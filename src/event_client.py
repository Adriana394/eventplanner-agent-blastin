from pathlib import Path
import sys
import re

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import json
from dotenv import load_dotenv
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from agents.mcp import MCPServerStdio

from openai import AsyncOpenAI

from agents import FunctionTool, Runner, Agent, OpenAIProvider, RunConfig, trace
from agents.exceptions import ModelBehaviorError

from mcp_servers.mcp_servers import get_server_config, bundle_servers
from src.schemas import (UserRequest, CoreResult, UIResult, MarkdownReport, ReporterResult, ValidationResult, ValidationIssue, Money,
                         UIEventTeaser, UISpotItem, UIDayOverview, UIItineraryStop, UIFoodDrinkSpot, ItineraryStop)
from src.reporting import append_missing_link_note_section, render_markdown, save_report_markdown

from src.instructions import SYSTEM_INSTRUCTIONS_PLANNER, SYSTEM_INSTRUCTIONS_REPORTER, SYSTEM_INSTRUCTIONS_VALIDATOR

from typing import Callable

ProgressCallback = Callable[[int, str], None]


def _get_progress_language(user_request: UserRequest) -> str:
    if user_request.delivery and user_request.delivery.language:
        return 'de' if user_request.delivery.language.value == 'Deutsch' else 'en'
    return 'en'


PROGRESS_MESSAGES = {
    'en': {
        'starting_servers': 'Starting MCP servers...',
        'searching': 'Searching for events and places...',
        'building_plan': 'Building the plan...',
        'validating': 'Validating and refining the plan...',
        'post_processing': 'Processing and verifying results...',
        'writing_report': 'Writing the report...',
        'saving_report': 'Saving report...',
        'revising_plan': 'Revising the current plan...',
    },
    'de': {
        'starting_servers': 'MCP-Server werden gestartet...',
        'searching': 'Events und Orte werden gesucht...',
        'building_plan': 'Plan wird erstellt...',
        'validating': 'Plan wird geprueft und verfeinert...',
        'post_processing': 'Ergebnisse werden verarbeitet und geprueft...',
        'writing_report': 'Bericht wird geschrieben...',
        'saving_report': 'Bericht wird gespeichert...',
        'revising_plan': 'Aktueller Plan wird ueberarbeitet...',
    },
}


def _progress(on_progress: ProgressCallback | None, percent: int, lang: str, key: str) -> None:
    if on_progress is not None:
        on_progress(percent, PROGRESS_MESSAGES[lang][key])


load_dotenv(override = True)

reports_dir = os.getenv('REPORTS_DIR', os.path.join(os.getcwd(), 'outputs', 'reports'))
os.makedirs(reports_dir, exist_ok = True)

CITY_SERVICE_BASE_URL = os.getenv('CITY_URL')
EVENT_SERVICE_BASE_URL = os.getenv('EVENT_URL')
OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
MODEL_PROVIDER_OPENAI = 'openai'
MODEL_PROVIDER_OPENROUTER = 'openrouter'

AVAILABLE_MODELS = [
    'deepseek/deepseek-v3.2',
    'google/gemini-2.5-flash',
    'anthropic/claude-haiku-4-5',
]
DEFAULT_MODEL = AVAILABLE_MODELS[0]
BERLIN_TZ = ZoneInfo('Europe/Berlin')
EVENT_PRICE_INFO_NOTE = (
    'Eventim prices are synced once per day and may vary slightly later. '
    'Use the ticket link for the latest live pricing.'
)
EVENTIM_HOSTS = {'eventim.de', 'www.eventim.de'}
PLANNER_SCHEMA_RETRY_NOTE = """
IMPORTANT OUTPUT FIX:
- recommendation.sentences must contain at most 5 items
- personal_feedback must stay concise
- return valid CoreResult JSON only
""".strip()
REPAIR_INSTRUCTIONS = """
REPAIR TASK:
- Revise the existing CoreResult using the validator findings below.
- Keep valid parts of the plan unchanged.
- Fix only the reported inconsistencies and constraint violations.
- Return a full valid CoreResult JSON object only.
""".strip()
GENERIC_ITINERARY_TITLES = {
    'free time',
    'freie zeit',
    'free time for discovery or rest',
    'freie zeit fuer entdeckung oder ausruhen',
    'freie zeit für entdeckung oder ausruhen',
    'time to explore',
    'time to rest',
    'relax',
    'rest',
    'entdeckung',
    'ausruhen',
    'explore the city',
    'stadt erkunden',
    'visit historic places',
    'dinner in a fine restaurant',
    'enjoy drinks at a bar',
}
GENERIC_ITINERARY_PATTERNS = [
    r'\bfree time\b',
    r'\bfreie zeit\b',
    r'\bexplore\b',
    r'\bentdeckung\b',
    r'\bausruhen\b',
    r'\brelax\b',
    r'\brest\b',
]


def normalize_model_provider(provider_name: str | None) -> str:
    provider = (provider_name or os.getenv('MODEL_PROVIDER') or MODEL_PROVIDER_OPENAI).strip().lower()
    if provider not in {MODEL_PROVIDER_OPENAI, MODEL_PROVIDER_OPENROUTER}:
        raise ValueError(f'Unsupported model provider: {provider_name}')
    return provider


def get_default_model_selection(provider_name: str | None = None) -> dict[str, str]:
    provider = normalize_model_provider(provider_name)

    if provider == MODEL_PROVIDER_OPENROUTER:
        planner_model = (
            os.getenv('OPENROUTER_PLANNER_MODEL')
            or os.getenv('PLANNER_MODEL')
            or 'openai/gpt-4.1'
        )
        reporter_model = (
            os.getenv('OPENROUTER_REPORTER_MODEL')
            or os.getenv('REPORTER_MODEL')
            or 'openai/gpt-4.1-mini'
        )
        validator_model = (
            os.getenv('OPENROUTER_VALIDATOR_MODEL')
            or os.getenv('VALIDATOR_MODEL')
            or 'openai/gpt-oss-120b:free'
        )
    else:
        planner_model = os.getenv('OPENAI_PLANNER_MODEL') or os.getenv('PLANNER_MODEL') or 'gpt-4.1'
        reporter_model = os.getenv('OPENAI_REPORTER_MODEL') or os.getenv('REPORTER_MODEL') or 'gpt-4.1-nano'
        validator_model = os.getenv('OPENAI_VALIDATOR_MODEL') or os.getenv('VALIDATOR_MODEL') or reporter_model

    return {
        'provider': provider,
        'planner_model': planner_model,
        'reporter_model': reporter_model,
        'validator_model': validator_model,
    }


def _build_model_provider(provider_name: str) -> OpenAIProvider:
    provider = normalize_model_provider(provider_name)

    if provider == MODEL_PROVIDER_OPENROUTER:
        openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        if not openrouter_api_key:
            raise ValueError('OPENROUTER_API_KEY is not set in .env.')

        headers = {'X-Title': os.getenv('OPENROUTER_APP_NAME', 'Dion Event Planner')}
        referer = os.getenv('OPENROUTER_SITE_URL')
        if referer:
            headers['HTTP-Referer'] = referer

        openrouter_client = AsyncOpenAI(
            api_key = openrouter_api_key,
            base_url = OPENROUTER_BASE_URL,
            default_headers = headers,
        )
        return OpenAIProvider(openai_client = openrouter_client, use_responses = False)

    openai_api_key = os.getenv('OPENAI_API_KEY')
    return OpenAIProvider(api_key = openai_api_key, use_responses = True)


def _normalize_report_path(saved_report_path: str, allowed_reports_dir: str) -> str:
    if not saved_report_path:
        raise ValueError('Reporter did not return a saved report path.')

    normalized_reports_dir = os.path.abspath(allowed_reports_dir)
    candidate_path = saved_report_path.strip()

    if not os.path.isabs(candidate_path):
        candidate_path = os.path.join(normalized_reports_dir, candidate_path)

    normalized_candidate = os.path.abspath(candidate_path)

    try:
        common_prefix = os.path.commonpath([normalized_reports_dir, normalized_candidate])
    except ValueError as exc:
        raise ValueError('Reporter returned an invalid saved report path.') from exc

    if common_prefix != normalized_reports_dir:
        raise ValueError('Reporter did not return a valid saved report path inside the allowed directory.')

    return normalized_candidate


async def _persist_report_to_expected_path(
    fs_server,
    markdown_report: MarkdownReport,
    reports_dir: str,
    filename_hint: str,
) -> str:
    markdown_content = render_markdown(markdown_report)
    saved_path = await save_report_markdown(
        fs_server = fs_server,
        reports_dir = reports_dir,
        filename = filename_hint,
        markdown = markdown_content,
    )
    return _normalize_report_path(saved_path, reports_dir)


async def _run_planner_with_schema_retry(
    planner_agent: Agent,
    planner_input_text: str,
    run_config: RunConfig,
    max_turns: int | None = None,
):
    try:
        if max_turns is None:
            return await Runner.run(planner_agent, planner_input_text, run_config = run_config)
        return await Runner.run(planner_agent, planner_input_text, max_turns = max_turns, run_config = run_config)
    except ModelBehaviorError as exc:
        error_text = str(exc)
        if 'Recommendation must contain at most 5 sentences' not in error_text:
            raise

        retry_input = f"{planner_input_text}\n\n{PLANNER_SCHEMA_RETRY_NOTE}"
        if max_turns is None:
            return await Runner.run(planner_agent, retry_input, run_config = run_config)
        return await Runner.run(planner_agent, retry_input, max_turns = max_turns, run_config = run_config)


def _parse_backend_iso(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None

    normalized = dt_str.strip()
    if normalized.endswith('Z'):
        normalized = normalized[:-1] + '+00:00'
    return datetime.fromisoformat(normalized)


def _to_utc_z(local_dt: datetime) -> str:
    if local_dt.tzinfo is None:
        local_dt = local_dt.replace(tzinfo = BERLIN_TZ)
    return local_dt.astimezone(ZoneInfo('UTC')).isoformat(timespec = 'milliseconds').replace('+00:00', 'Z')


def _to_berlin_iso(utc_dt_str: str | None) -> str | None:
    parsed = _parse_backend_iso(utc_dt_str)
    if parsed is None:
        return None
    return parsed.astimezone(BERLIN_TZ).isoformat(timespec = 'seconds')


def _format_price_display(amount: float | int | None) -> str | None:
    if amount is None:
        return None

    numeric_amount = float(amount)
    if numeric_amount == 0:
        return 'free'

    return f'from {numeric_amount:.2f} EUR'


def _normalize_public_url(url: str | None) -> str | None:
    normalized = (url or '').strip()
    if not normalized:
        return None

    if not re.match(r'^https?://', normalized, flags = re.IGNORECASE):
        return None

    if any(char.isspace() for char in normalized):
        return None

    normalized = normalized.replace('://eventim.de/', '://www.eventim.de/')
    normalized = re.sub(
        r'^(https?://www\.eventim\.de)/noapp/event/',
        r'\1/event/',
        normalized,
        flags = re.IGNORECASE,
    )
    return normalized


async def _is_public_place_url_reachable(url: str | None) -> bool:
    normalized_url = _normalize_public_url(url)
    if not normalized_url:
        return False

    # Eventim links are treated as trusted event links elsewhere.
    if any(host in normalized_url for host in EVENTIM_HOSTS):
        return True

    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; DionLinkChecker/1.0)',
        'Accept': 'text/html,application/xhtml+xml',
    }

    try:
        async with httpx.AsyncClient(timeout = 12.0, follow_redirects = True, headers = headers) as client:
            response = await client.get(normalized_url)
            if response.status_code >= 400:
                return False
            content_type = (response.headers.get('content-type') or '').casefold()
            return 'html' in content_type or 'text/' in content_type
    except Exception:
        return False


async def _http_get_json(url: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout = 30.0) as client:
        response = await client.get(url, params = params)
        response.raise_for_status()
        return response.json()


async def _resolve_city_key_from_backend(city_name_or_key: str) -> str | None:
    if not CITY_SERVICE_BASE_URL:
        return None

    raw_city = (city_name_or_key or '').strip()
    if not raw_city:
        return None

    if '--' in raw_city:
        return raw_city

    payload = await _http_get_json(f'{CITY_SERVICE_BASE_URL}/supported-cities-with-active-events')
    city_rows = payload.get('payload', [])

    lowered_raw_city = raw_city.casefold()
    for row in city_rows:
        city_name = (row.get('name') or '').strip()
        city_key = (row.get('clearNameCityOverloardKey3000') or '').strip()
        if city_name and city_name.casefold() == lowered_raw_city and city_key:
            return city_key

    return None


async def _fetch_authoritative_events_for_trip(user_request: UserRequest) -> dict[str, dict]:
    if not EVENT_SERVICE_BASE_URL:
        return {}

    city_key = await _resolve_city_key_from_backend(user_request.trip.city)
    if not city_key:
        return {}

    range_start_local = datetime.combine(user_request.trip.date_start, datetime.min.time())
    range_end_local = datetime.combine(user_request.trip.date_end, datetime.max.time().replace(microsecond = 0))

    response = await _http_get_json(
        f'{EVENT_SERVICE_BASE_URL}/events/for-city-key/{city_key}',
        params = {
            'eventsEndsAfterTimeUtc': _to_utc_z(range_start_local),
            'eventsStartsBeforeTimeUtc': _to_utc_z(range_end_local),
            'with_location': 'true',
            'limit': 250,
            'offset': 0,
        },
    )

    event_rows = response.get('payload', {}).get('data', []) or []
    authoritative_by_key: dict[str, dict] = {}

    for row in event_rows:
        event_id = (row.get('surrogate') or '').strip()
        ticket_url = (row.get('ticketShopUrl') or '').strip()
        name = (row.get('name') or '').strip()
        start_ts = (row.get('startTimestamp') or '').strip()

        if event_id:
            authoritative_by_key[event_id] = row
        if ticket_url:
            authoritative_by_key[ticket_url] = row
        if name and start_ts:
            authoritative_by_key[f'{name}::{start_ts}'] = row

    return authoritative_by_key


def _sync_core_result_events_with_authoritative_data(core_result: CoreResult, authoritative_events: dict[str, dict]) -> CoreResult:
    if not authoritative_events:
        return core_result

    for event in core_result.events:
        lookup_keys = [event.event_id]
        if event.ticket_url:
            lookup_keys.append(event.ticket_url)
        if event.start_datetime:
            backend_start = _parse_backend_iso(event.start_datetime)
            if backend_start is not None:
                lookup_keys.append(f'{event.name}::{backend_start.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")}')

        authoritative = next((authoritative_events.get(key) for key in lookup_keys if key), None)
        if not authoritative:
            continue

        location = authoritative.get('location') or {}
        lowest_price = authoritative.get('lowestPrice')
        address = (location.get('address') or '').strip()
        venue_name = (location.get('name') or '').strip()
        city_name = (location.get('cityName') or '').strip()

        event.name = authoritative.get('name') or event.name
        event.start_datetime = _to_berlin_iso(authoritative.get('startTimestamp')) or event.start_datetime
        event.end_datetime = _to_berlin_iso(authoritative.get('endTimestamp')) or event.end_datetime
        event.ticket_url = _normalize_public_url(authoritative.get('ticketShopUrl') or event.ticket_url)
        event.source_url = _normalize_public_url(authoritative.get('ticketShopUrl') or event.source_url) or event.source_url
        event.description = authoritative.get('description') or event.description
        event.event_id = authoritative.get('surrogate') or event.event_id

        if address and city_name:
            event.address_or_area = f'{address}, {city_name.title()}'
        elif address:
            event.address_or_area = address
        elif venue_name:
            event.address_or_area = venue_name

        if event.price is None:
            event.price = Money()

        event.price.amount_eur = lowest_price
        event.price.display = _format_price_display(lowest_price)

    return core_result


def _attach_event_price_info_warning(core_result: CoreResult) -> CoreResult:
    if core_result.events and EVENT_PRICE_INFO_NOTE not in core_result.warnings:
        core_result.warnings.append(EVENT_PRICE_INFO_NOTE)
    return core_result


def _sync_itinerary_stop_source_urls(core_result: CoreResult) -> CoreResult:
    event_lookup = {
        _normalize_name_key(event.name): event
        for event in core_result.events
        if _normalize_name_key(event.name)
    }
    sightseeing_lookup = {
        _normalize_name_key(spot.name): spot
        for spot in core_result.sightseeing_spots
        if _normalize_name_key(spot.name)
    }
    food_lookup = {
        _normalize_name_key(place.name): place
        for place in core_result.food_and_drink_spots
        if _normalize_name_key(place.name)
    }

    for day in core_result.itinerary:
        for stop in day.stops:
            linked_name_key = _normalize_name_key(stop.linked_item_name or stop.title)
            if not linked_name_key:
                continue

            if linked_name_key in event_lookup:
                stop.source_url = event_lookup[linked_name_key].source_url
            elif linked_name_key in sightseeing_lookup:
                stop.source_url = sightseeing_lookup[linked_name_key].source_url
            elif linked_name_key in food_lookup:
                stop.source_url = food_lookup[linked_name_key].source_url

    return core_result


def _normalize_generic_text(value: str | None) -> str:
    normalized = (value or '').strip().casefold()
    return normalized.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')


def _is_generic_itinerary_stop(stop) -> bool:
    if stop.linked_item_name or stop.source_url:
        return False

    normalized_title = _normalize_generic_text(stop.title)
    normalized_notes = _normalize_generic_text(stop.notes)
    combined_text = ' '.join(part for part in [normalized_title, normalized_notes] if part).strip()

    if not combined_text:
        return True

    if normalized_title in GENERIC_ITINERARY_TITLES:
        return True

    if stop.stop_type != 'other':
        return False

    return any(re.search(pattern, combined_text) for pattern in GENERIC_ITINERARY_PATTERNS)


def _deduplicate_food_stops_in_itinerary(core_result: CoreResult) -> CoreResult:
    """Remove food itinerary stops whose venue has already appeared earlier in the trip.

    If the same food/drink venue appears more than once across days (or twice within the same
    day), only the first occurrence is kept. A warning is added so the user knows the result
    had repeated venues.
    """
    seen: set[str] = set()
    duplicates_removed: list[str] = []

    for day in core_result.itinerary:
        kept: list = []
        for stop in day.stops:
            if stop.stop_type != 'food':
                kept.append(stop)
                continue

            key = _normalize_name_key(stop.linked_item_name or stop.title)
            if key and key in seen:
                duplicates_removed.append(stop.linked_item_name or stop.title)
            else:
                if key:
                    seen.add(key)
                kept.append(stop)
        day.stops = kept

    if duplicates_removed:
        unique_dups = list(dict.fromkeys(duplicates_removed))
        preview = ', '.join(unique_dups[:4])
        extra = f' (+{len(unique_dups) - 4} more)' if len(unique_dups) > 4 else ''
        core_result.warnings.append(
            f'Duplicate food/drink venue(s) removed from itinerary: {preview}{extra}. '
            'The agent reused the same venue on multiple days — consider varying meals manually.'
        )

    return core_result


def _sanitize_itinerary_placeholders(core_result: CoreResult) -> CoreResult:
    removed_stop_count = 0

    for day in core_result.itinerary:
        original_count = len(day.stops)
        day.stops = [stop for stop in day.stops if not _is_generic_itinerary_stop(stop)]
        removed_stop_count += original_count - len(day.stops)

    core_result.itinerary = [day for day in core_result.itinerary if day.stops]

    if removed_stop_count:
        core_result.warnings.append(
            f'Removed {removed_stop_count} generic itinerary placeholder stop(s) to keep the plan concrete.'
        )

    return core_result


def _sanitize_food_and_drink_source_urls(core_result: CoreResult) -> CoreResult:
    malformed_source_names: list[str] = []

    for place in core_result.food_and_drink_spots:
        raw_source_url = (place.source_url or '').strip()
        if not raw_source_url:
            place.source_url = None
            continue

        normalized_url = _normalize_public_url(raw_source_url)
        if normalized_url:
            place.source_url = normalized_url
            continue

        place.source_url = None
        malformed_source_names.append(place.name)

    if malformed_source_names:
        preview_names = ', '.join(malformed_source_names[:3])
        extra_count = len(malformed_source_names) - min(len(malformed_source_names), 3)
        suffix = f' (+{extra_count} more)' if extra_count > 0 else ''
        core_result.warnings.append(
            f'Some provided food/drink source URLs were malformed and were removed: {preview_names}{suffix}.'
        )

    return core_result


def _sanitize_event_source_urls(core_result: CoreResult) -> CoreResult:
    normalized_event_names: list[str] = []

    for event in core_result.events:
        original_source_url = event.source_url
        original_ticket_url = event.ticket_url

        event.source_url = _normalize_public_url(event.source_url) or event.source_url
        event.ticket_url = _normalize_public_url(event.ticket_url) or event.ticket_url

        if event.ticket_url and not event.source_url:
            event.source_url = event.ticket_url
        if event.source_url and not event.ticket_url:
            event.ticket_url = event.source_url

        if event.source_url != original_source_url or event.ticket_url != original_ticket_url:
            normalized_event_names.append(event.name)

    if normalized_event_names:
        preview_names = ', '.join(normalized_event_names[:3])
        extra_count = len(normalized_event_names) - min(len(normalized_event_names), 3)
        suffix = f' (+{extra_count} more)' if extra_count > 0 else ''
        core_result.warnings.append(
            f'Normalized public event links for: {preview_names}{suffix}.'
        )

    return core_result


def _sanitize_sightseeing_source_urls(core_result: CoreResult) -> CoreResult:
    malformed_source_names: list[str] = []

    for spot in core_result.sightseeing_spots:
        raw_source_url = (spot.source_url or '').strip()
        if not raw_source_url:
            spot.source_url = None
            continue

        normalized_url = _normalize_public_url(raw_source_url)
        if normalized_url:
            spot.source_url = normalized_url
            continue
        spot.source_url = None
        malformed_source_names.append(spot.name)

    if malformed_source_names:
        preview_names = ', '.join(malformed_source_names[:3])
        extra_count = len(malformed_source_names) - min(len(malformed_source_names), 3)
        suffix = f' (+{extra_count} more)' if extra_count > 0 else ''
        core_result.warnings.append(
            f'Some provided sightseeing source URLs were malformed and were removed: {preview_names}{suffix}.'
        )

    return core_result


async def _verify_place_source_urls(core_result: CoreResult) -> CoreResult:
    all_items = list(core_result.sightseeing_spots) + list(core_result.food_and_drink_spots)
    if not all_items:
        return core_result

    urls = [_normalize_public_url(item.source_url) for item in all_items]
    reachable = await asyncio.gather(*(
        _is_public_place_url_reachable(url) if url else _false()
        for url in urls
    ))

    removed_link_names: list[str] = []
    for item, url, is_ok in zip(all_items, urls, reachable):
        if url and is_ok:
            item.source_url = url
        else:
            item.source_url = None
            removed_link_names.append(item.name)

    if removed_link_names:
        unique_names = list(dict.fromkeys(removed_link_names))
        preview_names = ', '.join(unique_names[:4])
        extra_count = len(unique_names) - min(len(unique_names), 4)
        suffix = f' (+{extra_count} more)' if extra_count > 0 else ''
        core_result.warnings.append(
            f'No verified public link could be confirmed for: {preview_names}{suffix}. The place was kept, but its link was removed.'
        )

    return core_result


async def _false() -> bool:
    return False


def _time_to_minutes(value: str | None) -> int | None:
    key = _extract_time_sort_key(value)
    if key is None:
        return None
    return key[0] * 60 + key[1]


def _minutes_to_time(minutes: int) -> str:
    bounded = max(0, min(minutes, 23 * 60 + 59))
    hour, minute = divmod(bounded, 60)
    return f'{hour:02d}:{minute:02d}'


def _pick_food_spot(core_result: CoreResult, preferred_types: list[str], used_names: set[str]) -> object | None:
    normalized_preferred = [item.strip().casefold() for item in preferred_types]
    for venue_type in normalized_preferred:
        for place in core_result.food_and_drink_spots:
            if _normalize_name_key(place.name) in used_names:
                continue
            if place.venue_type.casefold() == venue_type:
                return place
    for place in core_result.food_and_drink_spots:
        if _normalize_name_key(place.name) not in used_names:
            return place
    return None


def _insert_default_food_structure(user_request: UserRequest, core_result: CoreResult) -> CoreResult:
    if not user_request.trip.food_drink_enabled or not core_result.food_and_drink_spots:
        return core_result

    for day in core_result.itinerary:
        if not day.stops:
            continue

        used_place_names = {
            _normalize_name_key(stop.linked_item_name)
            for stop in day.stops
            if stop.stop_type == 'food' and _normalize_name_key(stop.linked_item_name)
        }
        existing_food_minutes = [_time_to_minutes(stop.start_time) for stop in day.stops if stop.stop_type == 'food']
        existing_food_minutes = [minute for minute in existing_food_minutes if minute is not None]
        first_stop_minutes = [_time_to_minutes(stop.start_time) for stop in day.stops if _time_to_minutes(stop.start_time) is not None]
        earliest_stop_minute = min(first_stop_minutes) if first_stop_minutes else None
        has_breakfast = any(minute is not None and minute < 11 * 60 for minute in existing_food_minutes)
        has_lunch = any(minute is not None and 11 * 60 <= minute < 15 * 60 for minute in existing_food_minutes)
        has_dinner = any(minute is not None and minute >= 17 * 60 for minute in existing_food_minutes)
        has_event = any(stop.stop_type == 'event' for stop in day.stops)
        has_sightseeing = any(stop.stop_type == 'sightseeing' for stop in day.stops)
        new_stops: list[ItineraryStop] = []

        if not has_breakfast and (has_sightseeing or (earliest_stop_minute is not None and earliest_stop_minute >= 10 * 60)):
            breakfast_spot = _pick_food_spot(core_result, ['cafe', 'restaurant'], used_place_names)
            if breakfast_spot is not None:
                used_place_names.add(_normalize_name_key(breakfast_spot.name))
                target_minute = 9 * 60
                if earliest_stop_minute is not None:
                    target_minute = min(target_minute, max(8 * 60, earliest_stop_minute - 90))
                new_stops.append(
                    ItineraryStop(
                        stop_type = 'food',
                        title = f'Breakfast at {breakfast_spot.name}',
                        start_time = _minutes_to_time(target_minute),
                        notes = 'Start the day with a relaxed breakfast stop before sightseeing or other activities.',
                        linked_item_name = breakfast_spot.name,
                        source_url = breakfast_spot.source_url,
                    )
                )

        if not has_lunch and has_sightseeing:
            lunch_spot = _pick_food_spot(core_result, ['restaurant', 'cafe'], used_place_names)
            if lunch_spot is not None:
                used_place_names.add(_normalize_name_key(lunch_spot.name))
                new_stops.append(
                    ItineraryStop(
                        stop_type = 'food',
                        title = f'Lunch break at {lunch_spot.name}',
                        start_time = '13:00',
                        notes = 'Use midday for a flexible lunch or cafe stop before the next city highlight.',
                        linked_item_name = lunch_spot.name,
                        source_url = lunch_spot.source_url,
                    )
                )

        if not has_dinner and (has_event or has_sightseeing):
            dinner_spot = _pick_food_spot(core_result, ['restaurant', 'bar', 'other', 'cafe'], used_place_names)
            if dinner_spot is not None:
                used_place_names.add(_normalize_name_key(dinner_spot.name))
                event_start_minutes = min(
                    [_time_to_minutes(stop.start_time) for stop in day.stops if stop.stop_type == 'event' and _time_to_minutes(stop.start_time) is not None],
                    default = None,
                )
                dinner_minute = 18 * 60
                if event_start_minutes is not None:
                    dinner_minute = max(17 * 60, event_start_minutes - 120)
                new_stops.append(
                    ItineraryStop(
                        stop_type = 'food',
                        title = f'Dinner at {dinner_spot.name}',
                        start_time = _minutes_to_time(dinner_minute),
                        notes = 'Use this as the default evening meal stop before the main night program.',
                        linked_item_name = dinner_spot.name,
                        source_url = dinner_spot.source_url,
                    )
                )

        if new_stops:
            day.stops.extend(new_stops)
            day.stops.sort(key = lambda stop: (_time_to_minutes(stop.start_time) is None, _time_to_minutes(stop.start_time) or 24 * 60, stop.title))

    return core_result


def _normalize_issue_message(message: str) -> str:
    return ' '.join((message or '').split()).strip()


def _dedupe_core_warnings(core_result: CoreResult) -> CoreResult:
    seen: set[str] = set()
    unique_warnings: list[str] = []

    for warning in core_result.warnings:
        normalized_warning = _normalize_issue_message(warning).casefold()
        if not normalized_warning or normalized_warning in seen:
            continue
        seen.add(normalized_warning)
        unique_warnings.append(_normalize_issue_message(warning))

    core_result.warnings = unique_warnings
    return core_result


def _normalize_name_key(value: str | None) -> str:
    normalized = _normalize_generic_text(value)
    return re.sub(r'[^a-z0-9]+', ' ', normalized).strip()


def _extract_iso_date(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r'\d{4}-\d{2}-\d{2}', value)
    return match.group(0) if match else None


def _extract_time_sort_key(value: str | None) -> tuple[int, int] | None:
    if not value:
        return None
    match = re.search(r'(\d{1,2}):(\d{2})', value)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2))
    if hour > 23 or minute > 59:
        return None
    return hour, minute


def _build_event_lookup(core_result: CoreResult) -> dict[str, object]:
    lookup: dict[str, object] = {}
    for event in core_result.events:
        key = _normalize_name_key(event.name)
        if key:
            lookup[key] = event
    return lookup


def _parse_local_event_window(event) -> tuple[datetime | None, datetime | None]:
    start = _parse_backend_iso(event.start_datetime)
    end = _parse_backend_iso(event.end_datetime)
    if start is not None and end is not None and end < start:
        end = start
    return start, end


def _event_dates_by_name(core_result: CoreResult) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for event in core_result.events:
        key = _normalize_name_key(event.name)
        event_date = _extract_iso_date(event.start_datetime)
        if not key or not event_date:
            continue
        mapping.setdefault(key, set()).add(event_date)
    return mapping


def _build_item_name_sets(core_result: CoreResult) -> tuple[set[str], set[str], set[str]]:
    event_names = {_normalize_name_key(event.name) for event in core_result.events if _normalize_name_key(event.name)}
    sightseeing_names = {_normalize_name_key(spot.name) for spot in core_result.sightseeing_spots if _normalize_name_key(spot.name)}
    food_names = {_normalize_name_key(place.name) for place in core_result.food_and_drink_spots if _normalize_name_key(place.name)}
    return event_names, sightseeing_names, food_names


def _dedupe_validation_issues(issues: list[ValidationIssue]) -> list[ValidationIssue]:
    seen: set[tuple[str, str]] = set()
    unique_issues: list[ValidationIssue] = []

    for issue in issues:
        normalized_key = (issue.code.strip(), _normalize_issue_message(issue.message).casefold())
        if normalized_key in seen:
            continue
        seen.add(normalized_key)
        issue.message = _normalize_issue_message(issue.message)
        unique_issues.append(issue)

    return unique_issues


def _collect_deterministic_validation_issues(user_request: UserRequest, core_result: CoreResult) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    event_names, sightseeing_names, food_names = _build_item_name_sets(core_result)
    event_dates_by_name = _event_dates_by_name(core_result)
    event_lookup = _build_event_lookup(core_result)
    must_avoid_terms = [
        _normalize_name_key(term)
        for term in (user_request.itinerary.must_avoid or [])
        if _normalize_name_key(term)
    ]

    if not user_request.trip.events_enabled and core_result.events:
        issues.append(
            ValidationIssue(
                code = 'events_disabled_but_present',
                message = 'The request disables events, but the structured result still contains events.',
                severity = 'error',
            )
        )

    if not user_request.trip.sightseeing_enabled and core_result.sightseeing_spots:
        issues.append(
            ValidationIssue(
                code = 'sightseeing_disabled_but_present',
                message = 'The request disables sightseeing, but the structured result still contains sightseeing spots.',
                severity = 'error',
            )
        )

    if not user_request.trip.food_drink_enabled and core_result.food_and_drink_spots:
        issues.append(
            ValidationIssue(
                code = 'food_disabled_but_present',
                message = 'The request disables food and drinks, but the structured result still contains food or drink venues.',
                severity = 'error',
                )
            )

    if not user_request.trip.events_enabled:
        itinerary_event_stops = [
            stop.title
            for day in core_result.itinerary
            for stop in day.stops
            if stop.stop_type == 'event'
        ]
        if itinerary_event_stops:
            issues.append(
                ValidationIssue(
                    code = 'event_stops_present_while_events_disabled',
                    message = 'The request disables events, but the itinerary still contains event stops.',
                    severity = 'error',
                )
            )

    if not user_request.trip.sightseeing_enabled:
        itinerary_sightseeing_stops = [
            stop.title
            for day in core_result.itinerary
            for stop in day.stops
            if stop.stop_type == 'sightseeing'
        ]
        if itinerary_sightseeing_stops:
            issues.append(
                ValidationIssue(
                    code = 'sightseeing_stops_present_while_sightseeing_disabled',
                    message = 'The request disables sightseeing, but the itinerary still contains sightseeing stops.',
                    severity = 'error',
                )
            )

    if not user_request.trip.food_drink_enabled:
        itinerary_food_stops = [
            stop.title
            for day in core_result.itinerary
            for stop in day.stops
            if stop.stop_type == 'food'
        ]
        if itinerary_food_stops:
            issues.append(
                ValidationIssue(
                    code = 'food_stops_present_while_food_disabled',
                    message = 'The request disables food and drinks, but the itinerary still contains food stops.',
                    severity = 'error',
                )
            )

    if user_request.sightseeing and user_request.sightseeing.free_only:
        paid_sightseeing = [
            spot.name
            for spot in core_result.sightseeing_spots
            if spot.entry_fee and (spot.entry_fee.amount_eur or 0) > 0
        ]
        if paid_sightseeing:
            issues.append(
                ValidationIssue(
                    code = 'free_sightseeing_violation',
                    message = f"Sightseeing is marked as free-only, but these spots appear paid: {', '.join(paid_sightseeing[:3])}.",
                    severity = 'error',
                )
            )

    if user_request.events.free_only:
        paid_events = [
            event.name
            for event in core_result.events
            if event.price and (event.price.amount_eur or 0) > 0
        ]
        if paid_events:
            issues.append(
                ValidationIssue(
                    code = 'free_events_violation',
                    message = f"Events are marked as free-only, but these events appear paid: {', '.join(paid_events[:3])}.",
                    severity = 'error',
                )
            )

    if must_avoid_terms:
        blocked_matches: list[str] = []
        for event in core_result.events:
            haystack = ' '.join(
                part for part in [
                    event.name,
                    event.description,
                    ' '.join(event.category_tags or []),
                ] if part
            )
            normalized_haystack = _normalize_name_key(haystack)
            for term in must_avoid_terms:
                if term and term in normalized_haystack:
                    blocked_matches.append(event.name)
                    break

        for place in core_result.sightseeing_spots:
            haystack = ' '.join(part for part in [place.name, place.why_visit, place.address] if part)
            normalized_haystack = _normalize_name_key(haystack)
            for term in must_avoid_terms:
                if term and term in normalized_haystack:
                    blocked_matches.append(place.name)
                    break

        for place in core_result.food_and_drink_spots:
            haystack = ' '.join(part for part in [place.name, place.why_match, place.venue_type, place.address] if part)
            normalized_haystack = _normalize_name_key(haystack)
            for term in must_avoid_terms:
                if term and term in normalized_haystack:
                    blocked_matches.append(place.name)
                    break

        if blocked_matches:
            issues.append(
                ValidationIssue(
                    code = 'must_avoid_violation',
                    message = f"The result includes items that appear to match the avoid list: {', '.join(blocked_matches[:4])}.",
                    severity = 'error',
                )
            )

    expected_last_day = _normalize_generic_text(user_request.trip.date_end.isoformat())
    itinerary_dates_set = {
        _normalize_generic_text(_extract_iso_date(day.day_label))
        for day in core_result.itinerary
        if _extract_iso_date(day.day_label)
    }
    if user_request.trip.include_last_day and expected_last_day not in itinerary_dates_set:
        issues.append(
            ValidationIssue(
                code = 'last_day_missing',
                message = f"The itinerary should include the final trip day {user_request.trip.date_end.isoformat()}, but that day is missing.",
                severity = 'error',
            )
        )
    if not user_request.trip.include_last_day and expected_last_day in itinerary_dates_set:
        issues.append(
            ValidationIssue(
                code = 'last_day_unexpected',
                message = f"The itinerary includes the final trip day {user_request.trip.date_end.isoformat()} even though include_last_day is false.",
                severity = 'warning',
                )
            )

    if not core_result.itinerary:
        issues.append(
            ValidationIssue(
                code = 'itinerary_missing',
                message = 'The structured result does not contain any itinerary days.',
                severity = 'error',
            )
        )

    for day in core_result.itinerary:
        day_date = _extract_iso_date(day.day_label)
        if not day.stops:
            issues.append(
                ValidationIssue(
                    code = 'empty_itinerary_day',
                    message = f"The itinerary day '{day.day_label}' is empty.",
                    severity = 'warning',
                )
            )
            continue

        previous_time_key: tuple[int, int] | None = None
        earliest_time_key: tuple[int, int] | None = None
        day_event_windows: list[tuple[str, datetime | None, datetime | None]] = []
        for stop in day.stops:
            linked_name_key = _normalize_name_key(stop.linked_item_name or stop.title)

            if stop.stop_type == 'event' and linked_name_key and linked_name_key not in event_names:
                issues.append(
                    ValidationIssue(
                        code = 'event_stop_missing_reference',
                        message = f"The itinerary event stop '{stop.title}' does not match any selected event.",
                        severity = 'error',
                    )
                )

            if stop.stop_type == 'sightseeing' and linked_name_key and linked_name_key not in sightseeing_names:
                issues.append(
                    ValidationIssue(
                        code = 'sightseeing_stop_missing_reference',
                        message = f"The itinerary sightseeing stop '{stop.title}' does not match any selected sightseeing spot.",
                        severity = 'error',
                    )
                )

            if stop.stop_type == 'food' and linked_name_key and linked_name_key not in food_names:
                issues.append(
                    ValidationIssue(
                        code = 'food_stop_missing_reference',
                        message = f"The itinerary food stop '{stop.title}' does not match any selected food/drink venue.",
                        severity = 'error',
                    )
                )

            stop_time_key = _extract_time_sort_key(stop.start_time)
            if previous_time_key and stop_time_key and stop_time_key < previous_time_key:
                issues.append(
                    ValidationIssue(
                        code = 'itinerary_time_order_issue',
                        message = f"The stops on '{day.day_label}' are not ordered chronologically.",
                        severity = 'warning',
                    )
                )
                previous_time_key = stop_time_key
            elif stop_time_key:
                previous_time_key = stop_time_key
                if earliest_time_key is None or stop_time_key < earliest_time_key:
                    earliest_time_key = stop_time_key

            if stop.stop_type == 'event' and linked_name_key and day_date:
                event_dates = event_dates_by_name.get(linked_name_key)
                if event_dates and day_date not in event_dates:
                    issues.append(
                        ValidationIssue(
                            code = 'event_stop_wrong_day',
                            message = f"The event stop '{stop.title}' is placed on {day.day_label}, but the selected event date differs.",
                            severity = 'error',
                        )
                    )

                linked_event = event_lookup.get(linked_name_key)
                if linked_event:
                    event_start, event_end = _parse_local_event_window(linked_event)
                    day_event_windows.append((stop.title, event_start, event_end))

        for idx, (left_title, left_start, left_end) in enumerate(day_event_windows):
            if left_start is None:
                continue
            left_end_effective = left_end or left_start
            for right_title, right_start, right_end in day_event_windows[idx + 1:]:
                if right_start is None:
                    continue
                right_end_effective = right_end or right_start
                if left_start < right_end_effective and right_start < left_end_effective:
                    issues.append(
                        ValidationIssue(
                            code = 'overlapping_event_stops',
                            message = (
                                f"The itinerary day '{day.day_label}' contains overlapping event stops "
                                f"('{left_title}' and '{right_title}'). Competing events must not appear as one linear plan."
                            ),
                            severity = 'error',
                        )
                    )

        if (
            user_request.trip.planning_mode.value == 'full_trip'
            and day_date
            and day_date > user_request.trip.date_start.isoformat()
            and day_date < user_request.trip.date_end.isoformat()
            and (user_request.trip.sightseeing_enabled or user_request.trip.food_drink_enabled)
            and earliest_time_key is not None
            and earliest_time_key >= (15, 0)
        ):
            issues.append(
                ValidationIssue(
                    code = 'daytime_plan_missing',
                    message = (
                        f"The itinerary day '{day.day_label}' starts too late for a full-trip day. "
                        'Middle trip days should include a meaningful daytime plan before the evening.'
                    ),
                    severity = 'error',
                )
            )

    itinerary_dates = [
        _extract_iso_date(day.day_label)
        for day in core_result.itinerary
        if _extract_iso_date(day.day_label)
    ]
    if itinerary_dates:
        start_iso = user_request.trip.date_start.isoformat()
        end_iso = user_request.trip.date_end.isoformat()
        for itinerary_date in itinerary_dates:
            if itinerary_date < start_iso or itinerary_date > end_iso:
                issues.append(
                    ValidationIssue(
                        code = 'itinerary_date_out_of_range',
                        message = f"The itinerary contains the day {itinerary_date}, which is outside the requested trip range.",
                        severity = 'error',
                    )
                )

    recommendation_text = ' '.join(core_result.recommendation.sentences).casefold()
    if any(token in recommendation_text for token in ['kostenlos', 'free']):
        paid_sightseeing = [
            spot.name
            for spot in core_result.sightseeing_spots
            if spot.entry_fee and (spot.entry_fee.amount_eur or 0) > 0
        ]
        if paid_sightseeing:
            issues.append(
                ValidationIssue(
                    code = 'recommendation_free_mismatch',
                    message = f"The recommendation mentions free activities, but these sightseeing spots appear paid: {', '.join(paid_sightseeing[:3])}.",
                    severity = 'warning',
                )
            )

    if any(token in recommendation_text for token in ['bar', 'bars', 'cocktail', 'drinks']):
        has_bar = any(place.venue_type == 'bar' for place in core_result.food_and_drink_spots)
        if not has_bar:
            issues.append(
                ValidationIssue(
                    code = 'recommendation_bar_mismatch',
                    message = 'The recommendation emphasizes bar or drink options, but no bar venue appears in food_and_drink_spots.',
                    severity = 'warning',
                )
            )

    invalid_external_links: list[str] = []
    for spot in core_result.sightseeing_spots:
        if spot.source_url and not _normalize_public_url(spot.source_url):
            invalid_external_links.append(spot.name)
    for place in core_result.food_and_drink_spots:
        if place.source_url and not _normalize_public_url(place.source_url):
            invalid_external_links.append(place.name)

    if invalid_external_links:
        issues.append(
            ValidationIssue(
                code = 'invalid_external_links',
                message = (
                    'Some sightseeing or food/drink source URLs look malformed or unreliable: '
                    f"{', '.join(invalid_external_links[:4])}."
                ),
                severity = 'warning',
            )
        )

    return _dedupe_validation_issues(issues)


async def _run_validator(
    validator_agent: Agent,
    user_request: UserRequest,
    core_result: CoreResult,
    run_config: RunConfig,
) -> ValidationResult:
    deterministic_issues = _collect_deterministic_validation_issues(user_request, core_result)
    validator_input_text = build_validation_input_text(user_request, core_result, deterministic_issues)
    validator_run = await Runner.run(validator_agent, validator_input_text, run_config = run_config)
    validator_result = validator_run.final_output
    merged_issues = _dedupe_validation_issues([*deterministic_issues, *validator_result.issues])
    return ValidationResult(
        needs_revision = bool(merged_issues),
        issues = merged_issues,
    )


async def _repair_core_result_if_needed(
    planner_agent: Agent,
    validator_agent: Agent,
    user_request: UserRequest,
    core_result: CoreResult,
    run_config: RunConfig,
) -> tuple[CoreResult, ValidationResult]:
    validation_result = await _run_validator(
        validator_agent = validator_agent,
        user_request = user_request,
        core_result = core_result,
        run_config = run_config,
    )

    if not validation_result.needs_revision:
        return core_result, validation_result

    repair_input_text = build_repair_planner_input_text(user_request, core_result, validation_result)
    repair_run = await _run_planner_with_schema_retry(
        planner_agent,
        repair_input_text,
        max_turns = 20,
        run_config = run_config,
    )
    repaired_core_result = _sanitize_itinerary_placeholders(repair_run.final_output)
    repaired_core_result = _insert_default_food_structure(user_request, repaired_core_result)
    repaired_core_result = _sanitize_event_source_urls(repaired_core_result)
    repaired_core_result = _sanitize_sightseeing_source_urls(repaired_core_result)
    repaired_core_result = _sanitize_food_and_drink_source_urls(repaired_core_result)
    repaired_core_result = await _verify_place_source_urls(repaired_core_result)
    repaired_core_result = _sync_itinerary_stop_source_urls(repaired_core_result)
    final_validation_result = await _run_validator(
        validator_agent = validator_agent,
        user_request = user_request,
        core_result = repaired_core_result,
        run_config = run_config,
    )

    if final_validation_result.issues:
        repaired_core_result.warnings.extend(
            [f"Validation issue remains: {issue.message}" for issue in final_validation_result.issues]
        )

    return repaired_core_result, final_validation_result


async def _apply_post_processing_pipeline(
    user_request: UserRequest,
    core_result: CoreResult,
    authoritative_events: dict[str, dict],
) -> CoreResult:
    core_result = _sync_core_result_events_with_authoritative_data(core_result, authoritative_events)
    core_result = _sanitize_itinerary_placeholders(core_result)
    core_result = _deduplicate_food_stops_in_itinerary(core_result)
    core_result = _insert_default_food_structure(user_request, core_result)
    core_result = _sanitize_event_source_urls(core_result)
    core_result = _sanitize_sightseeing_source_urls(core_result)
    core_result = _sanitize_food_and_drink_source_urls(core_result)
    core_result = await _verify_place_source_urls(core_result)
    core_result = _sync_itinerary_stop_source_urls(core_result)
    return core_result


# Build input text for Agents
def build_planner_input_text(user_request: UserRequest) -> str:
    selected_language = (
        user_request.delivery.language.value
        if user_request.delivery and user_request.delivery.language
        else 'English'
    )
    return f"""
Plan a city-event trip for this request.
Return only the required structured output schema.
The required output language is: {selected_language}.

User request:
{json.dumps(user_request.model_dump(mode = 'json'), ensure_ascii = False, indent = 2)}
""".strip()


def build_followup_planner_input_text(
    original_request: UserRequest,
    current_plan: CoreResult,
    followup_message: str,
) -> str:
    selected_language = (
        original_request.delivery.language.value
        if original_request.delivery and original_request.delivery.language
        else 'English'
    )
    return f"""
A plan already exists.
Revise the existing plan based on the user's follow-up request.
Do not rebuild everything from scratch unless the user requests it.
Keep the revised structured output language in: {selected_language}.

Original user request:
{json.dumps(original_request.model_dump(mode = 'json'), ensure_ascii = False, indent = 2)}

Current plan:
{json.dumps(current_plan.model_dump(mode = 'json'), ensure_ascii = False, indent = 2)}

User follow-up request:
{followup_message.strip()}
""".strip()


def build_validation_input_text(
    user_request: UserRequest,
    core_result: CoreResult,
    deterministic_issues: list[ValidationIssue],
) -> str:
    return f"""
Validate the current trip plan against the user request.
Return only the required ValidationResult schema.

User request:
{json.dumps(user_request.model_dump(mode = 'json'), ensure_ascii = False, indent = 2)}

Current plan:
{json.dumps(core_result.model_dump(mode = 'json'), ensure_ascii = False, indent = 2)}

Deterministic validation findings already detected:
{json.dumps([issue.model_dump(mode = 'json') for issue in deterministic_issues], ensure_ascii = False, indent = 2)}
""".strip()


def build_repair_planner_input_text(
    original_request: UserRequest,
    current_plan: CoreResult,
    validation_result: ValidationResult,
) -> str:
    return f"""
{REPAIR_INSTRUCTIONS}

Original user request:
{json.dumps(original_request.model_dump(mode = 'json'), ensure_ascii = False, indent = 2)}

Current plan that needs repair:
{json.dumps(current_plan.model_dump(mode = 'json'), ensure_ascii = False, indent = 2)}

Validator findings to fix:
{json.dumps(validation_result.model_dump(mode = 'json'), ensure_ascii = False, indent = 2)}
""".strip()


def build_reporter_input_text(reporter_job: dict) -> str:
    selected_language = (
        reporter_job.get('selected_language')
        or reporter_job.get('user_request', {}).get('delivery', {}).get('language')
        or 'English'
    )
    return f"""
Create a MarkdownReport from the following planning result.

You must:
1. Build the MarkdownReport object from the provided data.
2. Return a ReporterResult containing the markdown_report.
3. Write the MarkdownReport content in this language: {selected_language}.
4. The report file will be saved automatically by the system.

Reporter job:
{json.dumps(reporter_job, ensure_ascii = False, indent = 2)}
""".strip()


# Results to UI 
def core_to_ui(core_result: CoreResult) -> UIResult:
    top_events = []
    for e in core_result.events[:3]:
        top_events.append(
            UIEventTeaser(
                name = e.name,
                start_datetime = e.start_datetime,
                venue_name = e.address_or_area,
                price_display = e.price.display if e.price and e.price.display else None,
                source_url = e.source_url,
                ticket_url = e.ticket_url,
            )
        )

    sightseeing_spots = []
    for s in core_result.sightseeing_spots:
        sightseeing_spots.append(
            UISpotItem(
                name = s.name,
                entry_fee_display = s.entry_fee.display if s.entry_fee and s.entry_fee.display else None,
                opening_hours = s.opening_hours,
                source_url = s.source_url,
            )
        )

    food_and_drink_spots = []
    for place in core_result.food_and_drink_spots[:4]:
        food_and_drink_spots.append(
            UIFoodDrinkSpot(
                name = place.name,
                venue_type = place.venue_type,
                price_hint = place.price_hint,
                opening_hours = place.opening_hours,
                source_url = place.source_url,
            )
        )

    itinerary_overview = []
    for day in core_result.itinerary:
        itinerary_overview.append(
            UIDayOverview(
                day_label = day.day_label,
                stops = [
                    UIItineraryStop(
                        title = stop.title,
                        start_time = stop.start_time,
                        notes = stop.notes,
                        stop_type = stop.stop_type,
                        linked_item_name = stop.linked_item_name,
                        source_url = stop.source_url,
                    )
                    for stop in day.stops
                ],
            )
        )

    return UIResult(
        recommendation = core_result.recommendation,
        top_events = top_events,
        sightseeing_spots = sightseeing_spots,
        food_and_drink_spots = food_and_drink_spots,
        itinerary_overview = itinerary_overview,
        warnings = core_result.warnings,
        personal_feedback = core_result.personal_feedback,
    )
    
    
# Agents 
async def run_full_planner_flow(
    user_request: UserRequest,
    model_provider_name: str | None = None,
    planner_model: str | None = None,
    reporter_model: str | None = None,
    validator_model: str | None = None,
    on_progress: ProgressCallback | None = None,
) -> dict:
    lang = _get_progress_language(user_request)
    configs = get_server_config(reports_dir)
    model_selection = get_default_model_selection(model_provider_name)
    resolved_provider = model_selection['provider']
    resolved_planner_model = (planner_model or model_selection['planner_model']).strip()
    resolved_reporter_model = (reporter_model or model_selection['reporter_model']).strip()
    resolved_validator_model = (validator_model or model_selection['validator_model']).strip()
    model_provider = _build_model_provider(resolved_provider)
    run_config = RunConfig(model_provider = model_provider)

    planner_input_text = build_planner_input_text(user_request)
    _progress(on_progress, 5, lang, 'starting_servers')

    async with bundle_servers(configs) as servers:
        pw = servers['playwright']
        fs = servers['filesystem']
        eventim = servers['eventim']
        dzt = servers['dzt']
        
        dion_planner = Agent(
            name = 'Dion_Planner', 
            instructions = SYSTEM_INSTRUCTIONS_PLANNER,
            model = resolved_planner_model,
            mcp_servers = [pw, fs, eventim, dzt],
            output_type = CoreResult
            )
        
        dion_reporter = Agent(
            name = 'Dion_Reporter',
            instructions = SYSTEM_INSTRUCTIONS_REPORTER,
            model = resolved_reporter_model,
            mcp_servers = [],
            output_type = ReporterResult
        )

        dion_validator = Agent(
            name = 'Dion_Validator',
            instructions = SYSTEM_INSTRUCTIONS_VALIDATOR,
            model = resolved_validator_model,
            output_type = ValidationResult,
        )
        
        _progress(on_progress, 15, lang, 'searching')

        with trace('dion_planner'):
            planner_run = await _run_planner_with_schema_retry(
                dion_planner,
                planner_input_text,
                max_turns = 20,
                run_config = run_config,
            )

        _progress(on_progress, 50, lang, 'building_plan')

        core_result = planner_run.final_output
        authoritative_events = await _fetch_authoritative_events_for_trip(user_request)
        core_result = await _apply_post_processing_pipeline(user_request, core_result, authoritative_events)

        _progress(on_progress, 65, lang, 'validating')

        core_result, _ = await _repair_core_result_if_needed(
            planner_agent = dion_planner,
            validator_agent = dion_validator,
            user_request = user_request,
            core_result = core_result,
            run_config = run_config,
        )
        core_result = await _apply_post_processing_pipeline(user_request, core_result, authoritative_events)
        core_result = _attach_event_price_info_warning(core_result)
        core_result = _dedupe_core_warnings(core_result)
        ui_result = core_to_ui(core_result = core_result)

        _progress(on_progress, 80, lang, 'writing_report')

        reporter_job = {
            'user_request': user_request.model_dump(mode = 'json'),
            'core_result': core_result.model_dump(mode = 'json'),
            'selected_language': user_request.delivery.language.value if user_request.delivery else 'English',
            'reports_dir': reports_dir,
            'now_iso': datetime.now().isoformat(timespec = 'seconds'),
            'filename_hint': f"report_{user_request.trip.city.strip().lower().replace(' ', '_')}_{user_request.trip.date_start.isoformat()}_to_{user_request.trip.date_end.isoformat()}.md"
        }

        reporter_input_text = build_reporter_input_text(reporter_job)

        with trace('dion_reporter'):
            reporter_run = await Runner.run(dion_reporter, reporter_input_text, run_config = run_config)

        reporter_result = reporter_run.final_output
        markdown_report = append_missing_link_note_section(
            reporter_result.markdown_report,
            core_result,
            user_request,
        )

        _progress(on_progress, 92, lang, 'saving_report')

        saved_report_path = await _persist_report_to_expected_path(
            fs_server = fs,
            markdown_report = markdown_report,
            reports_dir = reports_dir,
            filename_hint = reporter_job['filename_hint'],
        )

        return {
            'core_result': core_result,
            'ui_result': ui_result,
            'markdown_report': markdown_report,
            'saved_report_path': saved_report_path,
            'model_selection': {
                'provider': resolved_provider,
                'planner_model': resolved_planner_model,
                'reporter_model': resolved_reporter_model,
                'validator_model': resolved_validator_model,
            },
        }

async def run_followup_planner_flow(
    original_request: UserRequest,
    current_plan: CoreResult,
    followup_message: str,
    model_provider_name: str | None = None,
    planner_model: str | None = None,
    reporter_model: str | None = None,
    validator_model: str | None = None,
    on_progress: ProgressCallback | None = None,
) -> dict:
    lang = _get_progress_language(original_request)
    configs = get_server_config(reports_dir)
    model_selection = get_default_model_selection(model_provider_name)
    resolved_provider = model_selection['provider']
    resolved_planner_model = (planner_model or model_selection['planner_model']).strip()
    resolved_reporter_model = (reporter_model or model_selection['reporter_model']).strip()
    resolved_validator_model = (validator_model or model_selection['validator_model']).strip()
    model_provider = _build_model_provider(resolved_provider)
    run_config = RunConfig(model_provider = model_provider)

    planner_input_text = build_followup_planner_input_text(
        original_request = original_request,
        current_plan = current_plan,
        followup_message = followup_message,
    )
    _progress(on_progress, 5, lang, 'starting_servers')

    async with bundle_servers(configs) as servers:
        pw = servers['playwright']
        fs = servers['filesystem']
        eventim = servers['eventim']
        dzt = servers['dzt']
        
        
        dion_planner = Agent(
            name = 'Dion_Planner', 
            instructions = SYSTEM_INSTRUCTIONS_PLANNER,
            model = resolved_planner_model,
            mcp_servers = [pw, fs, eventim, dzt],
            output_type = CoreResult
        )
        
        dion_reporter = Agent(
            name = 'Dion_Reporter',
            instructions = SYSTEM_INSTRUCTIONS_REPORTER,
            model = resolved_reporter_model,
            mcp_servers = [],
            output_type = ReporterResult
        )

        dion_validator = Agent(
            name = 'Dion_Validator',
            instructions = SYSTEM_INSTRUCTIONS_VALIDATOR,
            model = resolved_validator_model,
            output_type = ValidationResult,
        )
        
        _progress(on_progress, 15, lang, 'revising_plan')

        with trace('dion_planner_followup'):
            planner_run = await _run_planner_with_schema_retry(
                dion_planner,
                planner_input_text,
                max_turns = 20,
                run_config = run_config,
            )

        _progress(on_progress, 50, lang, 'post_processing')

        core_result = planner_run.final_output
        authoritative_events = await _fetch_authoritative_events_for_trip(original_request)
        core_result = await _apply_post_processing_pipeline(original_request, core_result, authoritative_events)

        _progress(on_progress, 65, lang, 'validating')

        core_result, _ = await _repair_core_result_if_needed(
            planner_agent = dion_planner,
            validator_agent = dion_validator,
            user_request = original_request,
            core_result = core_result,
            run_config = run_config,
        )
        core_result = await _apply_post_processing_pipeline(original_request, core_result, authoritative_events)
        core_result = _attach_event_price_info_warning(core_result)
        core_result = _dedupe_core_warnings(core_result)
        ui_result = core_to_ui(core_result = core_result)

        _progress(on_progress, 80, lang, 'writing_report')

        reporter_job = {
            'user_request': original_request.model_dump(mode = 'json'),
            'core_result': core_result.model_dump(mode = 'json'),
            'selected_language': original_request.delivery.language.value if original_request.delivery else 'English',
            'reports_dir': reports_dir,
            'now_iso': datetime.now().isoformat(timespec = 'seconds'),
            'filename_hint': f"report_{original_request.trip.city.strip().lower().replace(' ', '_')}_{original_request.trip.date_start.isoformat()}_to_{original_request.trip.date_end.isoformat()}.md"
        }

        reporter_input_text = build_reporter_input_text(reporter_job)

        with trace('dion_reporter_followup'):
            reporter_run = await Runner.run(dion_reporter, reporter_input_text, run_config = run_config)

        reporter_result = reporter_run.final_output
        markdown_report = append_missing_link_note_section(
            reporter_result.markdown_report,
            core_result,
            original_request,
        )

        _progress(on_progress, 92, lang, 'saving_report')

        saved_report_path = await _persist_report_to_expected_path(
            fs_server = fs,
            markdown_report = markdown_report,
            reports_dir = reports_dir,
            filename_hint = reporter_job['filename_hint'],
        )

        return {
            'core_result': core_result,
            'ui_result': ui_result,
            'markdown_report': markdown_report,
            'saved_report_path': saved_report_path,
            'model_selection': {
                'provider': resolved_provider,
                'planner_model': resolved_planner_model,
                'reporter_model': resolved_reporter_model,
                'validator_model': resolved_validator_model,
            },
        }

async def main():
    user_request = UserRequest.model_validate(
        {
            'user': {
                'name': 'Adriana',
            },
            'trip': {
                'city': 'Berlin',
                'date_start': '2026-01-30',
                'date_end': '2026-02-01',
                'planning_mode': 'full_trip',
                'budget': {
                    'min_budget': 100,
                    'max_budget': 250,
                },
            },
            'events': {
                'vibe': 'techno',
                'categories': 'concert, club',
                'time_pref': 'night',
                'free_only': False,
            },
            'delivery': {
                'send_email': False,
                'language': 'English',
            },
        }
    )

    result = await run_full_planner_flow(user_request)

    print('UIResult created:')
    print(result['ui_result'].model_dump())

    print('\nMarkdownReport created:')
    print(result['markdown_report'].model_dump())


if __name__ == '__main__':
    asyncio.run(main())

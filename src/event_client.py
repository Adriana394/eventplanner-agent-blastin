from pathlib import Path
import sys

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

import mcp
from mcp import StdioServerParameters
from agents.mcp import MCPServerStdio

from openai import AsyncOpenAI

from agents import FunctionTool, Runner, Agent, OpenAIProvider, RunConfig, trace
from agents.exceptions import ModelBehaviorError

from IPython.display import display, Markdown

from mcp_servers.mcp_servers import get_server_config, bundle_servers
from src.schemas import (UserRequest, CoreResult, UIResult, MarkdownReport, ReporterResult, Money,
                         UIEventTeaser, UISpotItem, UIDayOverview, UIItineraryStop, UIFoodDrinkSpot)
from src.reporting import render_markdown, save_report_markdown

from src.instructions import SYSTEM_INSTRUCTIONS_PLANNER, SYSTEM_INSTRUCTIONS_REPORTER


load_dotenv(override = True)

reports_dir = os.getenv('REPORTS_DIR', os.path.join(os.getcwd(), 'outputs', 'reports'))
os.makedirs(reports_dir, exist_ok = True)

CITY_SERVICE_BASE_URL = os.getenv('CITY_URL')
EVENT_SERVICE_BASE_URL = os.getenv('EVENT_URL')
OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
MODEL_PROVIDER_OPENAI = 'openai'
MODEL_PROVIDER_OPENROUTER = 'openrouter'
BERLIN_TZ = ZoneInfo('Europe/Berlin')
EVENT_PRICE_INFO_NOTE = (
    'Eventim prices are synced once per day and may vary slightly later. '
    'Use the ticket link for the latest live pricing.'
)
PLANNER_SCHEMA_RETRY_NOTE = """
IMPORTANT OUTPUT FIX:
- recommendation.sentences must contain at most 5 items
- personal_feedback must stay concise
- return valid CoreResult JSON only
""".strip()


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
    else:
        planner_model = os.getenv('OPENAI_PLANNER_MODEL') or os.getenv('PLANNER_MODEL') or 'gpt-4.1'
        reporter_model = os.getenv('OPENAI_REPORTER_MODEL') or os.getenv('REPORTER_MODEL') or 'gpt-4.1-nano'

    return {
        'provider': provider,
        'planner_model': planner_model,
        'reporter_model': reporter_model,
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
        event.ticket_url = authoritative.get('ticketShopUrl') or event.ticket_url
        event.source_url = authoritative.get('ticketShopUrl') or event.source_url
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
2. Save the markdown report as a .md file in reports_dir using the Filesystem MCP.
3. Use filename_hint exactly as the filename.
4. Return a ReporterResult containing:
   - markdown_report
   - saved_report_path
5. Write the MarkdownReport content in this language: {selected_language}.

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
) -> dict:
    
    configs = get_server_config(reports_dir)
    model_selection = get_default_model_selection(model_provider_name)
    resolved_provider = model_selection['provider']
    resolved_planner_model = (planner_model or model_selection['planner_model']).strip()
    resolved_reporter_model = (reporter_model or model_selection['reporter_model']).strip()
    model_provider = _build_model_provider(resolved_provider)
    run_config = RunConfig(model_provider = model_provider)
    
    planner_input_text = build_planner_input_text(user_request)
    
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
            mcp_servers = [fs],
            output_type = ReporterResult
        )
        
        with trace('dion_planner'):
            planner_run = await _run_planner_with_schema_retry(
                dion_planner,
                planner_input_text,
                run_config = run_config,
            )
            
        core_result = planner_run.final_output
        authoritative_events = await _fetch_authoritative_events_for_trip(user_request)
        core_result = _sync_core_result_events_with_authoritative_data(core_result, authoritative_events)
        core_result = _attach_event_price_info_warning(core_result)
        ui_result = core_to_ui(core_result = core_result)
        
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
        markdown_report = reporter_result.markdown_report
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
            },
        }    

async def run_followup_planner_flow(
    original_request: UserRequest,
    current_plan: CoreResult,
    followup_message: str,
    model_provider_name: str | None = None,
    planner_model: str | None = None,
    reporter_model: str | None = None,
) -> dict:
    configs = get_server_config(reports_dir)
    model_selection = get_default_model_selection(model_provider_name)
    resolved_provider = model_selection['provider']
    resolved_planner_model = (planner_model or model_selection['planner_model']).strip()
    resolved_reporter_model = (reporter_model or model_selection['reporter_model']).strip()
    model_provider = _build_model_provider(resolved_provider)
    run_config = RunConfig(model_provider = model_provider)
    
    planner_input_text = build_followup_planner_input_text(
        original_request = original_request,
        current_plan = current_plan,
        followup_message = followup_message,
    )
    
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
            mcp_servers = [fs],
            output_type = ReporterResult
        )
        
        with trace('dion_planner_followup'):
            planner_run = await _run_planner_with_schema_retry(
                dion_planner,
                planner_input_text,
                max_turns = 20,
                run_config = run_config,
            )

        core_result = planner_run.final_output
        authoritative_events = await _fetch_authoritative_events_for_trip(original_request)
        core_result = _sync_core_result_events_with_authoritative_data(core_result, authoritative_events)
        core_result = _attach_event_price_info_warning(core_result)
        ui_result = core_to_ui(core_result = core_result)

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
        markdown_report = reporter_result.markdown_report
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

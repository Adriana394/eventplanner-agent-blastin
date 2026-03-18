import os

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, Callable
from zoneinfo import ZoneInfo

import httpx
from mcp.server.fastmcp import FastMCP

from dotenv import load_dotenv

load_dotenv(override = True)

EVENT_SERVICE_BASE_URL = os.getenv('EVENT_URL')
CITY_SERVICE_BASE_URL = os.getenv('CITY_URL')

BERLIN_TZ = ZoneInfo('Europe/Berlin')

mcp = FastMCP('eventim')

# Time helpers

def _parse_iso(dt_str: str) -> datetime:
    """
    Parse an ISO 8601 datetime string into a Python datetime.

    Supports UTC strings ending with 'Z' by converting them to '+00:00'
    because datetime.fromisoformat() does not accept 'Z' directly.
    """
    
    s = dt_str.strip()
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    return datetime.fromisoformat(s)


def _to_utc_z(dt: datetime) -> str:
    """
    Convert a datetime to an ISO 8601 UTC string ending with 'Z'.

    If the datetime is naive (no tzinfo), we assume it is in Europe/Berlin
    because user-facing inputs are expected to be local to Berlin.
    """
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo = BERLIN_TZ)
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.isoformat(timespec = 'milliseconds').replace('+00:00', 'Z')

def _to_dt_in_berlin(iso_utc: str) -> str:
    """
    Convert an ISO 8601 UTC datetime string from the backend into an ISO string in Europe/Berlin.

    This is helpful because the backend returns UTC timestamps (ending with 'Z'),
    while the user-facing plan should be in Europe/Berlin.
    """
    dt_utc = _parse_iso(iso_utc)
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo = timezone.utc)
    return dt_utc.astimezone(BERLIN_TZ).isoformat(timespec = 'seconds')

def _safe_bool(value: Any, default: bool = False) -> bool:
    """
    Normalize a vlue that might be a bool or a string into a bool.
    Some tool inputs may arrive as strings, this function make the server mire robust.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'y'}
    return bool(value)


# Cache types + helpers
    
@dataclass
class _CacheEntry:
    """
    Internal cache entry.
    valid_until_utc: backend-provided TTL boundary (validUntilUtc)
    data: cached payload for the tool call
    """
    valid_until_utc: datetime
    data: Any
    
# Internal caches (cleared when the process restarts)
_cities_cache: Optional[_CacheEntry] = None
_events_cache: Dict[Tuple[str, str, str, bool, int, int], _CacheEntry] = {}
_similar_cache: Dict[Tuple[str, bool, int, int], _CacheEntry] = {}
_popular_cache: Dict[Tuple[Optional[str], Optional[str], Optional[str], bool, int, int], _CacheEntry] = {}

# Internal indices to resolve city name/key quickly (rebuilt whenever cities payload refreshes)
_cities_by_key_lower: Dict[str, str] = {}
_cities_by_name_lower: Dict[str, str] = {}


def _cache_is_valid(entry: _CacheEntry) -> bool:
    """
    Return True if a cache entry is still valid according to its valid_until_utc TTL.
    """
    return datetime.now(timezone.utc) < entry.valid_until_utc


def _format_utc_z(dt: datetime) -> str:
    """
    Format a UTC datetime as an ISO string ending in Z (seconds precision).
    """
    return dt.isoformat(timespec = 'seconds').replace('+00:00', 'Z')


def _valid_until_from_response(payload: Dict[str, Any]) -> datetime:
    """
    Extract validUntilUtc from the backend response and return it as a UTC datetime.

    If validUntilUtc is missing, returns "now" (meaning: do not rely on cache).
    """
    valid_until_str = payload.get('validUntilUtc')
    if not valid_until_str:
        return datetime.now(timezone.utc)

    dt = _parse_iso(valid_until_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo = timezone.utc)

    return dt.astimezone(timezone.utc)


async def _http_get(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Perform an HTTP GET and return the parsed JSON response.

    Raises an exception for non-2xx responses (4xx/5xx) via raise_for_status().
    """
    async with httpx.AsyncClient(timeout = 30.0) as client:
        r = await client.get(url, params = params)
        r.raise_for_status()
        return r.json()


async def _cache_or_fetch_dict(
    cache: Dict[Any, _CacheEntry],
    key: Any,
    fetch_fn: Callable[[], Any],
) -> Tuple[bool, datetime, Any]:
    """
    Generic helper for dict-based caches.

    - Checks if cache[key] exists and is valid -> returns it
    - Otherwise calls fetch_fn() to get fresh data, stores it until validUntilUtc

    Returns:
    - cached (bool)
    - valid_until_utc (datetime)
    - payload (Any): backend "payload" field for this endpoint
    """
    entry = cache.get(key)
    if entry and _cache_is_valid(entry):
        return True, entry.valid_until_utc, entry.data

    data = await fetch_fn()
    valid_until = _valid_until_from_response(data)
    payload = data.get('payload', {})

    cache[key] = _CacheEntry(valid_until_utc = valid_until, data = payload)
    return False, valid_until, payload


def _rebuild_city_indices(payload: list[Dict[str, Any]]) -> None:
    """
    Build lookup dictionaries for city resolution.

    - _cities_by_key_lower maps cityKey(lower) -> cityKey
    - _cities_by_name_lower maps cityName(lower) -> cityKey
    """
    global _cities_by_key_lower, _cities_by_name_lower

    by_key: Dict[str, str] = {}
    by_name: Dict[str, str] = {}

    for c in payload:
        key = (c.get('clearNameCityOverloardKey3000') or '').strip()
        name = (c.get('name') or '').strip()

        if key:
            by_key[key.lower()] = key
        if name and key:
            by_name[name.lower()] = key

    _cities_by_key_lower = by_key
    _cities_by_name_lower = by_name 
    
    
@mcp.tool()
async def get_supported_cities_with_active_events() -> Dict[str, Any]:
    """
    Tool: Get Supported Cities (City Keys for Events)

    Calls:
      GET {CITY_SERVICE_BASE_URL}/supported-cities-with-active-events

    Returns:
      {
        "cached": bool,
        "validUntilUtc": "...Z",
        "payload": [ { city objects... } ]
      }

    Notes:
    - Uses backend "validUntilUtc" to cache results in memory until that time.
    - Also rebuilds internal lookup indices for city name/key resolution.
    """
    global _cities_cache

    if _cities_cache and _cache_is_valid(_cities_cache):
        if not _cities_by_key_lower or not _cities_by_name_lower:
            _rebuild_city_indices(payload = _cities_cache.data)

        return {
            'cached': True,
            'validUntilUtc': _format_utc_z(_cities_cache.valid_until_utc),
            'payload': _cities_cache.data,
        }

    url = f'{CITY_SERVICE_BASE_URL}/supported-cities-with-active-events'
    data = await _http_get(url)

    valid_until = _valid_until_from_response(data)
    payload = data.get('payload', [])

    _cities_cache = _CacheEntry(valid_until_utc = valid_until, data = payload)
    _rebuild_city_indices(payload = payload)

    return {
        'cached': False,
        'validUntilUtc': _format_utc_z(valid_until),
        'payload': payload,
    }


async def _resolve_city_key(city_name_or_key: str) -> str:
    """
    Internal helper: Resolve user input into a cityKey.

    The user may pass:
    - a cityKey directly (e.g. "berlin")
    - a city display name (e.g. "Berlin" / "München")
    """
    city_raw = city_name_or_key.strip()
    if not city_raw:
        raise ValueError('city_name_or_key must not be empty')

    await get_supported_cities_with_active_events()

    key_match = _cities_by_key_lower.get(city_raw.lower())
    if key_match:
        return key_match

    name_match = _cities_by_name_lower.get(city_raw.lower())
    if name_match:
        return name_match

    raise ValueError(f'City not found in supported cities list: {city_name_or_key}')


@mcp.tool()
async def get_events_for_city(
    city_name_or_key: str,
    events_ends_after_time_local: str,
    events_starts_before_time_local: str,
    with_location: bool = True,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Tool: Get Events (main endpoint)

    Calls:
      GET {EVENT_SERVICE_BASE_URL}/events/for-city-key/{cityKey}

    Inputs:
    - city_name_or_key:
        city name ("Berlin") OR cityKey ("berlin")
    - events_ends_after_time_local:
        ISO datetime string interpreted as Europe/Berlin (e.g. "2026-03-07T00:00:00")
    - events_starts_before_time_local:
        ISO datetime string interpreted as Europe/Berlin
    - with_location:
        include location object in each event when True
    - limit / offset:
        pagination

    Server behavior:
    - Converts local Berlin times -> UTC Z strings for the API query params
    - Caches the backend payload until validUntilUtc
    - Returns the backend payload plus:
        - resolved_city_key
        - request_params_utc (debug)
        - data_converted_times_berlin (convenience per event surrogate)
    """
    city_key = await _resolve_city_key(city_name_or_key)

    ends_after_dt = _parse_iso(events_ends_after_time_local)
    starts_before_dt = _parse_iso(events_starts_before_time_local)

    ends_after_utc = _to_utc_z(ends_after_dt)
    starts_before_utc = _to_utc_z(starts_before_dt)

    with_loc = _safe_bool(with_location, default = True)
    cache_key = (city_key, ends_after_utc, starts_before_utc, with_loc, int(limit), int(offset))

    async def _fetch() -> Dict[str, Any]:
        url = f'{EVENT_SERVICE_BASE_URL}/events/for-city-key/{city_key}'
        params = {
            'eventsEndsAfterTimeUtc': ends_after_utc,
            'eventsStartsBeforeTimeUtc': starts_before_utc,
            'with_location': with_loc,
            'limit': int(limit),
            'offset': int(offset),
        }
        return await _http_get(url, params = params)

    cached, valid_until, payload = await _cache_or_fetch_dict(
        cache = _events_cache,
        key = cache_key,
        fetch_fn = _fetch,
    )

    converted = []
    for e in payload.get('data', []) or []:
        start_utc = e.get('startTimestamp')
        end_utc = e.get('endTimestamp')
        converted.append({
            'surrogate': e.get('surrogate'),
            'start_datetime_berlin': _to_dt_in_berlin(start_utc) if start_utc else None,
            'end_datetime_berlin': _to_dt_in_berlin(end_utc) if end_utc else None,
        })

    return {
        'cached': cached,
        'validUntilUtc': _format_utc_z(valid_until),
        'payload': payload,
        'data_converted_times_berlin': converted,
        'resolved_city_key': city_key,
        'request_params_utc': {
            'eventsEndsAfterTimeUtc': ends_after_utc,
            'eventsStartsBeforeTimeUtc': starts_before_utc,
        }
    }


@mcp.tool()
async def get_similar_events(
    event_id: str,
    with_location: bool = True,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Tool: Get Similar Events

    Calls:
      GET {EVENT_SERVICE_BASE_URL}/events/{eventId}/similar

    Inputs:
    - event_id: surrogate id of the reference event (required)
    - with_location: include location object in each event when True
    - limit / offset: pagination

    Caching:
    - cached until validUntilUtc
    """
    if not event_id or not event_id.strip():
        raise ValueError('event_id must not be empty')

    with_loc = _safe_bool(with_location, default = True)
    cache_key = (event_id.strip(), with_loc, int(limit), int(offset))

    async def _fetch() -> Dict[str, Any]:
        url = f'{EVENT_SERVICE_BASE_URL}/events/{event_id.strip()}/similar'
        params = {
            'with_location': with_loc,
            'limit': int(limit),
            'offset': int(offset),
        }
        return await _http_get(url, params = params)

    cached, valid_until, payload = await _cache_or_fetch_dict(
        cache = _similar_cache,
        key = cache_key,
        fetch_fn = _fetch,
    )

    return {
        'cached': cached,
        'validUntilUtc': _format_utc_z(valid_until),
        'payload': payload,
    }


@mcp.tool()
async def get_popular_events(
    with_location: bool = True,
    events_ends_after_time_local: Optional[str] = None,
    events_starts_before_time_local: Optional[str] = None,
    city_key: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Tool: Get Popular Events

    Calls:
      GET {EVENT_SERVICE_BASE_URL}/events/popular-events

    Notes:
    - Backend currently may return random events (not truly popularity-ranked).

    Inputs:
    - with_location: include location object in each event when True
    - events_ends_after_time_local / events_starts_before_time_local:
        optional ISO strings interpreted as Europe/Berlin and converted to UTC for the API
    - city_key: optional filter (expects a cityKey, e.g. "berlin")
    - limit / offset: pagination

    Caching:
    - cached until validUntilUtc
    """
    with_loc = _safe_bool(with_location, default = True)

    ends_after_utc = None
    starts_before_utc = None

    if events_ends_after_time_local:
        ends_after_utc = _to_utc_z(_parse_iso(events_ends_after_time_local))

    if events_starts_before_time_local:
        starts_before_utc = _to_utc_z(_parse_iso(events_starts_before_time_local))

    cache_key = (city_key, ends_after_utc, starts_before_utc, with_loc, int(limit), int(offset))

    async def _fetch() -> Dict[str, Any]:
        url = f'{EVENT_SERVICE_BASE_URL}/events/popular-events'
        params: Dict[str, Any] = {
            'with_location': with_loc,
            'limit': int(limit),
            'offset': int(offset),
        }

        if city_key:
            params['city_key'] = city_key

        if ends_after_utc:
            params['eventsEndsAfterTimeUtc'] = ends_after_utc

        if starts_before_utc:
            params['eventsStartsBeforeTimeUtc'] = starts_before_utc

        return await _http_get(url, params = params)

    cached, valid_until, payload = await _cache_or_fetch_dict(
        cache = _popular_cache,
        key = cache_key,
        fetch_fn = _fetch,
    )

    return {
        'cached': cached,
        'validUntilUtc': _format_utc_z(valid_until),
        'payload': payload,
        'note': 'Backend currently may return random events (not true popularity ranking).',
    }


if __name__ == '__main__':
    """
    Entry point for running this MCP server as a separate process.
    """
    mcp.run('stdio')
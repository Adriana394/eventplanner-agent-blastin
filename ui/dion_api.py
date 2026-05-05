from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(override=True)

from agents.exceptions import ModelBehaviorError

from src.event_client import AVAILABLE_MODELS, DEFAULT_MODEL, run_followup_planner_flow, run_full_planner_flow
from src.schemas import CoreResult, UserRequest

UI_DIR = Path(__file__).parent
REPORTS_DIR = os.getenv('REPORTS_DIR', str(ROOT_DIR / 'outputs' / 'reports'))
os.makedirs(REPORTS_DIR, exist_ok=True)

TIME_PREF_MAP = {
    'No preference': 'no preferences',
    'Daytime': 'daytime',
    'Evening': 'evening',
    'Night': 'night',
}
PLANNING_MODE_MAP = {
    'Full Trip': 'full_trip',
    'Event or Day Trip': 'event_day_trip',
}
LANGUAGE_MAP = {'English': 'English', 'Deutsch': 'Deutsch'}

app = FastAPI(title='Dion API')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


class PlanRequest(BaseModel):
    user_name: str = ''
    city: str
    country: str = ''
    date_start: str
    date_end: str
    include_last_day: bool = True
    planning_mode: str = 'Full Trip'
    events_enabled: bool = True
    sightseeing_enabled: bool = True
    food_drink_enabled: bool = True
    group_size: int = 1
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    vibe: str = ''
    categories: str = ''
    time_pref: str = 'No preference'
    free_only: bool = False
    sightseeing_interests: str = ''
    sightseeing_mode: str = 'No preference'
    sightseeing_free_only: bool = False
    must_avoid: str = ''
    user_notes: str = ''
    language: str = 'English'
    model: str = DEFAULT_MODEL


class FollowupRequest(BaseModel):
    plan_request: PlanRequest
    core_result_json: dict
    followup_message: str


def _build_user_request(r: PlanRequest, for_followup: bool = False) -> UserRequest:
    payload: dict = {
        'user': {'name': r.user_name.strip() or None},
        'trip': {
            'city': r.city.strip(),
            'country': r.country.strip() or None,
            'date_start': r.date_start,
            'date_end': r.date_end,
            'include_last_day': r.include_last_day,
            'planning_mode': PLANNING_MODE_MAP.get(r.planning_mode, 'full_trip'),
            'events_enabled': r.events_enabled,
            'sightseeing_enabled': r.sightseeing_enabled,
            'food_drink_enabled': r.food_drink_enabled,
            'group_size': r.group_size,
        },
        'events': {
            'vibe': r.vibe.strip() or None,
            'categories': r.categories.strip() or None,
            'time_pref': TIME_PREF_MAP.get(r.time_pref, 'no preferences'),
            'free_only': r.free_only,
        },
        'itinerary': {
            'must_avoid': [x.strip() for x in r.must_avoid.split(',') if x.strip()] or None,
        },
        'delivery': {
            'send_email': False,
            'language': LANGUAGE_MAP.get(r.language, 'English'),
        },
    }

    if r.min_budget or r.max_budget:
        payload['trip']['budget'] = {'min_budget': r.min_budget, 'max_budget': r.max_budget}

    if r.sightseeing_enabled and (
        r.sightseeing_interests.strip()
        or r.sightseeing_mode != 'No preference'
        or r.sightseeing_free_only
    ):
        payload['sightseeing'] = {
            'interests': r.sightseeing_interests.strip() or None,
            'indoor_outdoor': None if r.sightseeing_mode == 'No preference' else r.sightseeing_mode.lower(),
            'free_only': r.sightseeing_free_only,
        }

    if not for_followup and r.user_notes.strip():
        existing_vibe = payload['events'].get('vibe')
        if existing_vibe:
            payload['events']['vibe'] = f'{existing_vibe} | Notes: {r.user_notes.strip()}'
        else:
            payload['events']['vibe'] = f'Notes: {r.user_notes.strip()}'

    return UserRequest.model_validate(payload)


def _serialize_result(user_request: UserRequest, result: dict) -> dict:
    ui = result['ui_result']
    saved_path = result.get('saved_report_path')

    size_kb = None
    if saved_path and Path(saved_path).exists():
        size_kb = round(Path(saved_path).stat().st_size / 1024, 1)

    return {
        'request': user_request.model_dump(mode='json'),
        'recommendation': {'sentences': list(ui.recommendation.sentences)},
        'top_events': [
            {
                'name': e.name,
                'start_datetime': e.start_datetime,
                'venue_name': e.venue_name,
                'price_display': e.price_display,
                'source_url': e.source_url,
            }
            for e in ui.top_events
        ],
        'sightseeing_spots': [
            {
                'name': s.name,
                'entry_fee_display': s.entry_fee_display,
                'opening_hours': s.opening_hours,
                'source_url': s.source_url,
            }
            for s in ui.sightseeing_spots
        ],
        'food_and_drink_spots': [
            {
                'name': f.name,
                'venue_type': str(f.venue_type or ''),
                'price_hint': f.price_hint,
                'opening_hours': f.opening_hours,
                'source_url': f.source_url,
            }
            for f in ui.food_and_drink_spots
        ],
        'itinerary_overview': [
            {
                'day_label': day.day_label,
                'stops': [
                    {
                        'stop_type': str(stop.stop_type or ''),
                        'start_time': stop.start_time,
                        'title': stop.title,
                        'notes': stop.notes,
                        'linked_item_name': stop.linked_item_name,
                    }
                    for stop in day.stops
                ],
            }
            for day in (ui.itinerary_overview or [])
        ],
        'warnings': list(ui.warnings or []),
        'personal_feedback': list(ui.personal_feedback or []),
        'saved_report_path': saved_path,
        'report_size_kb': size_kb,
    }


@app.get('/api/models')
def list_models():
    return {'models': AVAILABLE_MODELS, 'default': DEFAULT_MODEL}


def _handle_error(exc: Exception) -> None:
    msg = str(exc)
    if isinstance(exc, ModelBehaviorError):
        if 'Invalid JSON' in msg or 'invalid json' in msg.lower():
            raise HTTPException(
                status_code=422,
                detail='The selected model generated an invalid tool call. Please try a different model.',
            )
        raise HTTPException(status_code=422, detail=f'Model error: {msg}')
    if 'Provider returned error' in msg or 'is not supported' in msg:
        raise HTTPException(
            status_code=422,
            detail=f'The model provider returned an error — this model may not be compatible: {msg}',
        )
    raise HTTPException(status_code=500, detail=msg)


@app.post('/api/plan')
def run_plan(body: PlanRequest):
    try:
        user_request = _build_user_request(body)
        result = asyncio.run(
            run_full_planner_flow(user_request, planner_model=body.model or DEFAULT_MODEL)
        )
        return {
            'plan': _serialize_result(user_request, result),
            'core_result_json': result['core_result'].model_dump(mode='json'),
        }
    except HTTPException:
        raise
    except Exception as exc:
        _handle_error(exc)


@app.post('/api/followup')
def run_followup(body: FollowupRequest):
    try:
        user_request = _build_user_request(body.plan_request, for_followup=True)
        current_plan = CoreResult.model_validate(body.core_result_json)
        result = asyncio.run(
            run_followup_planner_flow(
                original_request=user_request,
                current_plan=current_plan,
                followup_message=body.followup_message,
                planner_model=body.plan_request.model or DEFAULT_MODEL,
            )
        )
        return {
            'plan': _serialize_result(user_request, result),
            'core_result_json': result['core_result'].model_dump(mode='json'),
        }
    except HTTPException:
        raise
    except Exception as exc:
        _handle_error(exc)


# Serve the HTML UI at /
@app.get('/', response_class=FileResponse)
def serve_ui():
    return FileResponse(UI_DIR / 'Dion UI.html')

# Serve JSX/asset files at their names
app.mount('/', StaticFiles(directory=str(UI_DIR)), name='static')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('ui.dion_api:app', host='0.0.0.0', port=7860, reload=False)

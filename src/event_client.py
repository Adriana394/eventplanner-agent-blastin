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

import mcp
from mcp import StdioServerParameters
from agents.mcp import MCPServerStdio

from openai import AsyncOpenAI

from agents import FunctionTool, Runner, Agent, OpenAIProvider, RunConfig, trace

from IPython.display import display, Markdown

from mcp_servers.mcp_servers import get_server_config, bundle_servers
from src.schemas import (UserRequest, CoreResult, UIResult, MarkdownReport, ReporterResult,
                         UIEventTeaser, UISpotItem, UIDayOverview, UIItineraryStop, UIFoodDrinkSpot)

from src.instructions import SYSTEM_INSTRUCTIONS_PLANNER, SYSTEM_INSTRUCTIONS_REPORTER


load_dotenv(override = True)

reports_dir = os.getenv('REPORTS_DIR', os.path.join(os.getcwd(), 'outputs', 'reports'))
os.makedirs(reports_dir, exist_ok = True)

OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
MODEL_PROVIDER_OPENAI = 'openai'
MODEL_PROVIDER_OPENROUTER = 'openrouter'


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
            planner_run = await Runner.run(dion_planner, planner_input_text, run_config = run_config)
            
        core_result = planner_run.final_output
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
        saved_report_path = reporter_result.saved_report_path
        
        if not saved_report_path or not saved_report_path.startswith(reports_dir):
            raise ValueError('Reporter did not return a valid saved report path inside the allowed directory.')
        
        
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
            planner_run = await Runner.run(dion_planner, planner_input_text, max_turns = 20, run_config = run_config)

        core_result = planner_run.final_output
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
        saved_report_path = reporter_result.saved_report_path

        if not saved_report_path or not saved_report_path.startswith(reports_dir):
            raise ValueError('Reporter did not return a valid saved report path inside the allowed directory.')

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

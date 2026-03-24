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

from agents import FunctionTool, Runner, Agent, trace

from IPython.display import display, Markdown

from mcp_servers.mcp_servers import get_server_config, bundle_servers
from src.schemas import (UserRequest, CoreResult, UIResult, MarkdownReport,
                         UIEventTeaser, UISpotItem, UIDayOverview, UIItineraryStop)

from src.instructions import SYSTEM_INSTRUCTIONS_PLANNER, SYSTEM_INSTRUCTIONS_REPORTER


load_dotenv(override = True)

reports_dir = os.getenv('REPORTS_DIR', os.path.join(os.getcwd(), 'outputs', 'reports'))
os.makedirs(reports_dir, exist_ok = True)


# Build input text for Agents
def build_planner_input_text(user_request: UserRequest) -> str:
    return f"""
Plan a city-event trip for this request.
Return only the required structured output schema.

User request:
{json.dumps(user_request.model_dump(mode = 'json'), ensure_ascii = False, indent = 2)}
""".strip()


def build_reporter_input_text(reporter_job: dict) -> str:
    return f"""
Create a MarkdownReport from the following planning result.
Return only the required MarkdownReport schema.

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

        itinerary_overview = []
    for day in core_result.itinerary:
        itinerary_overview.append(
            UIDayOverview(
                day_label = day.day_label,
                stops = [
                    UIItineraryStop(
                        title = stop.title,
                        start_time = stop.start_time,
                        duration_minutes = stop.duration_minutes,
                        notes = stop.notes,
                        stop_type = stop.stop_type,
                    )
                    for stop in day.stops
                ],
            )
        )

    return UIResult(
        recommendation = core_result.recommendation,
        top_events = top_events,
        sightseeing_spots = sightseeing_spots,
        itinerary_overview = itinerary_overview,
        warnings = core_result.warnings,
    )
    
# Agents 
async def run_full_planner_flow(user_request: UserRequest) -> dict:
    
    configs = get_server_config(reports_dir)
    
    planner_input_text = build_planner_input_text(user_request)
    
    async with bundle_servers(configs) as servers:
        pw = servers['playwright']
        fs = servers['filesystem']
        eventim = servers['eventim']
        dzt = servers['dzt']
        
        dion_planner = Agent(
            name = 'Dion_Planner', 
            instructions = SYSTEM_INSTRUCTIONS_PLANNER,
            model = 'gpt-4.1-nano',
            mcp_servers = [pw, fs, eventim, dzt],
            output_type = CoreResult
            )
        
        dion_reporter = Agent(
            name = 'Dion_Reporter',
            instructions = SYSTEM_INSTRUCTIONS_REPORTER,
            model = 'gpt-4.1-nano',
            mcp_servers = [fs],
            output_type = MarkdownReport
        )
        
        with trace('dion_planner'):
            planner_run = await Runner.run(dion_planner, planner_input_text)
            
        core_result = planner_run.final_output
        ui_result = core_to_ui(core_result = core_result)
        
        reporter_job = {
            'user_request': user_request.model_dump(mode = 'json'),
            'core_result': core_result.model_dump(mode = 'json'),
            'reports_dir': reports_dir,
            'now_iso': datetime.now().isoformat(timespec = 'seconds'),
            'filename_hint': f"report_{user_request.trip.city.strip().lower().replace(' ', '_')}_{user_request.trip.date_start.isoformat()}_to_{user_request.trip.date_end.isoformat()}.md"
        }
        
        reporter_input_text = build_reporter_input_text(reporter_job)
        
        with trace('dion_reporter'):
            reporter_run = await Runner.run(dion_reporter, reporter_input_text)
            
        markdown_report = reporter_run.final_output
        
        
        return {
            'core_result': core_result,
            'ui_result': ui_result,
            'markdown_report': markdown_report,
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
from pathlib import Path
import sys
import os
import traceback
import asyncio
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.schemas import UserRequest
from src.event_client import run_full_planner_flow


load_dotenv(override = True)

REPORTS_DIR = os.getenv('REPORTS_DIR', os.path.join(os.getcwd(), 'outputs', 'reports'))
os.makedirs(REPORTS_DIR, exist_ok = True)

st.set_page_config(
    page_title = 'BlastIn | Dion Event Planner',
    page_icon = '🎫',
    layout = 'wide',
    initial_sidebar_state = 'expanded',
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        h1 {
            font-size: 2.7rem !important;
            line-height: 1.1 !important;
            margin-bottom: 0.35rem !important;
        }
        h2 {
            font-size: 1.8rem !important;
            margin-top: 1rem !important;
            margin-bottom: 0.65rem !important;
        }
        h3 {
            font-size: 1.2rem !important;
            margin-bottom: 0.4rem !important;
        }
        p, label, div[data-testid='stMarkdownContainer'] p, div[data-testid='stCaptionContainer'] {
            font-size: 1.05rem !important;
        }
        div[data-testid='stForm'] {
            border: 1px solid rgba(250, 250, 250, 0.08);
            border-radius: 24px;
            padding: 1.25rem 1.1rem 0.9rem 1.1rem;
            background: rgba(255, 255, 255, 0.02);
        }
        .hero-card, .section-card {
            border: 1px solid rgba(250, 250, 250, 0.08);
            border-radius: 24px;
            padding: 1.2rem 1.1rem;
            background: rgba(255, 255, 255, 0.03);
            margin-bottom: 1rem;
        }
        .soft-label {
            font-size: 0.9rem !important;
            opacity: 0.78;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .big-intro {
            font-size: 1.14rem !important;
            line-height: 1.55 !important;
        }
        .pill {
            display: inline-block;
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            border: 1px solid rgba(250, 250, 250, 0.1);
            margin-right: 0.4rem;
            margin-bottom: 0.3rem;
            font-size: 0.95rem;
            opacity: 0.9;
        }
    </style>
    """,
    unsafe_allow_html = True,
)

TIME_PREF_OPTIONS = {
    'No preference': 'no preference',
    'Daytime': 'daytime',
    'Evening': 'evening',
    'Night': 'night',
}

LANGUAGE_OPTIONS = {
    'English': 'English',
    'Deutsch': 'Deutsch',
}

PLANNING_MODE_OPTIONS = {
    'Full Trip': 'full_trip',
    'Event or Day Trip': 'event_day_trip',
}

GROUP_SIZE_OPTIONS = list(range(1, 16))
SIGHTSEEING_MODE_OPTIONS = ['No preference', 'Indoor', 'Outdoor', 'Mixed']
MAX_FREE_TEXT_CHARS = 220


def init_session_state() -> None:
    defaults = {
        'last_user_request': None,
        'last_core_result': None,
        'last_ui_result': None,
        'last_markdown_report': None,
        'last_error': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar() -> None:
    st.sidebar.title('🎫 BlastIn')
    st.sidebar.caption('Dion helps users discover events and build a focused city plan.')

    st.sidebar.markdown('---')
    st.sidebar.markdown('### Inside this version')
    st.sidebar.markdown(
        '- guided input flow\n'
        '- optional sightseeing section\n'
        '- event-focused planning test\n'
        '- markdown report preview\n'
        '- structured debug output'
    )
    st.sidebar.markdown('---')
    st.sidebar.info('Best for testing real planner runs with clear user preferences.')


def render_intro() -> None:
    st.markdown(
        """
        <div class='hero-card'>
            <div class='soft-label'>Event planning assistant</div>
            <h1>🎫 BlastIn Event Planner</h1>
            <p class='big-intro'>
                Plan a city experience with Dion. This version is built for real testing:
                clear user questions, structured planner output, event results, optional sightseeing preferences,
                and a markdown report generated at the end.
            </p>
        </div>
        """,
        unsafe_allow_html = True,
    )

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown(
            """
            <div class='section-card'>
                <h3>🧳 Trip basics</h3>
                <p>Set the city, travel window, planning mode, group size, and budget.</p>
            </div>
            """,
            unsafe_allow_html = True,
        )

    with col_b:
        st.markdown(
            """
            <div class='section-card'>
                <h3>🎶 Event preferences</h3>
                <p>Define the vibe, categories, timing, and event-related wishes.</p>
            </div>
            """,
            unsafe_allow_html = True,
        )

    with col_c:
        st.markdown(
            """
            <div class='section-card'>
                <h3>📝 Final output</h3>
                <p>See the UI summary, warnings, itinerary overview, and generated markdown report.</p>
            </div>
            """,
            unsafe_allow_html = True,
        )


def build_user_request(
    user_name: str,
    city: str,
    country: str,
    date_start: date,
    date_end: date,
    planning_mode: str,
    group_size: int,
    min_budget: int | None,
    max_budget: int | None,
    vibe: str,
    categories: str,
    time_pref_label: str,
    free_only: bool,
    sightseeing_interests: str,
    sightseeing_mode: str,
    sightseeing_free_only: bool,
    must_avoid_raw: str,
    language_label: str,
    user_notes: str,
) -> UserRequest:
    payload = {
        'user': {
            'name': user_name.strip() or None,
        },
        'trip': {
            'city': city.strip(),
            'country': country.strip() or None,
            'date_start': str(date_start),
            'date_end': str(date_end),
            'planning_mode': planning_mode,
            'group_size': group_size,
            'budget': {
                'min_budget': min_budget,
                'max_budget': max_budget,
            },
        },
        'events': {
            'vibe': vibe.strip() or None,
            'categories': categories.strip() or None,
            'time_pref': TIME_PREF_OPTIONS[time_pref_label],
            'free_only': free_only,
        },
        'itinerary': {
            'must_avoid': [item.strip() for item in must_avoid_raw.split(',') if item.strip()] or None,
        },
        'delivery': {
            'send_email': False,
            'language': LANGUAGE_OPTIONS[language_label],
        },
    }

    if min_budget is None and max_budget is None:
        payload['trip'].pop('budget')

    if (
        sightseeing_interests.strip()
        or sightseeing_mode != 'No preference'
        or sightseeing_free_only
    ):
        payload['sightseeing'] = {
            'interests': sightseeing_interests.strip() or None,
            'indoor_outdoor': None if sightseeing_mode == 'No preference' else sightseeing_mode.lower(),
            'free_only': sightseeing_free_only,
        }

    if user_notes.strip():
        existing_vibe = payload['events'].get('vibe')
        if existing_vibe:
            payload['events']['vibe'] = f'{existing_vibe} | Notes: {user_notes.strip()}'
        else:
            payload['events']['vibe'] = f'Notes: {user_notes.strip()}'

    return UserRequest.model_validate(payload)


def validate_required_inputs(
    city: str,
    date_start: date,
    date_end: date,
    planning_mode: str | None,
    categories: str,
    min_budget: int | None,
    max_budget: int | None,
) -> list[str]:
    errors: list[str] = []

    if not city.strip():
        errors.append('Please enter a city.')

    if date_start is None:
        errors.append('Please select a start date.')

    if date_end is None:
        errors.append('Please select an end date.')

    if date_start is not None and date_end is not None and date_end < date_start:
        errors.append('End date must be on or after the start date.')

    if not planning_mode:
        errors.append('Please choose a planning mode.')

    if not categories.strip():
        errors.append('Please enter at least one event category or desired activity.')

    if min_budget is None and max_budget is None:
        errors.append('Please provide at least a minimum or maximum budget.')

    return errors


def render_form() -> UserRequest | None:
    st.markdown(
        """
        <div class='section-card'>
            <div class='soft-label'>Guided input</div>
            <h2>🧭 Tell Dion what kind of plan you want</h2>
            <p class='big-intro'>
                Use the sections below to keep the request focused and test the full planner flow.
                Sightseeing is optional for now. If left empty, Dion should not actively plan around it.
            </p>
        </div>
        """,
        unsafe_allow_html = True,
    )

    with st.form('planner_form', clear_on_submit = False):
        st.markdown('### 👤 About you')
        user_name = st.text_input(
            'What is your name? (optional)',
            placeholder = 'e.g. Adriana',
            max_chars = 40,
        )

        st.markdown('### 🏙️ Destination')
        col_trip_1, col_trip_2 = st.columns(2)
        with col_trip_1:
            city = st.text_input(
                'Which city do you want to visit?',
                placeholder = 'e.g. Berlin',
                max_chars = 40,
            )
        with col_trip_2:
            country = st.text_input(
                'Country (optional)',
                placeholder = 'e.g. Germany',
                max_chars = 40,
            )

        st.markdown('### 📅 Travel dates')
        col_date_1, col_date_2, col_date_3 = st.columns([1, 1, 1])
        with col_date_1:
            date_start = st.date_input(
                'Start date',
                value = date.today() + timedelta(days = 7),
                min_value = date.today(),
            )
        with col_date_2:
            date_end = st.date_input(
                'End date',
                value = date.today() + timedelta(days = 9),
                min_value = date.today(),
            )
        with col_date_3:
            group_size = st.selectbox(
                'How many people?',
                options = GROUP_SIZE_OPTIONS,
                index = 0,
            )

        st.markdown('### 🧭 Planning mode')
        planning_mode_label = st.selectbox(
            'What do you want Dion to plan?',
            options = list(PLANNING_MODE_OPTIONS.keys()),
            index = 0,
        )

        planning_mode = PLANNING_MODE_OPTIONS[planning_mode_label]

        if planning_mode == 'full_trip':
            budget_caption = 'This refers to the overall budget for the whole trip.'
            min_budget_label = 'Minimum trip budget (optional)'
            max_budget_label = 'Maximum trip budget (optional)'
        else:
            budget_caption = 'This refers to the budget for this day / event plan.'
            min_budget_label = 'Minimum day / event budget (optional)'
            max_budget_label = 'Maximum day / event budget (optional)'

        st.markdown('### 💸 Budget')
        st.caption(f'{budget_caption} Please provide at least a minimum or maximum budget')

        col_budget_1, col_budget_2 = st.columns(2)
        with col_budget_1:
            min_budget = st.number_input(
                min_budget_label,
                min_value = 0,
                value = 0,
                step = 10,
            )
        with col_budget_2:
            max_budget = st.number_input(
                max_budget_label,
                min_value = 0,
                value = 0,
                step = 10,
            )

        st.markdown('### 🎶 Event preferences')
        col_event_1, col_event_2 = st.columns(2)
        with col_event_1:
            vibe = st.text_input(
                'Which vibe do you want?',
                placeholder = 'e.g. techno, chill, latin, rnb',
                max_chars = 50,
            )
            time_pref_label = st.selectbox(
                'Preferred time',
                options = list(TIME_PREF_OPTIONS.keys()),
                index = 0,
            )
        with col_event_2:
            categories = st.text_input(
                'Which event categories or desired activities do you want?',
                placeholder = 'e.g. concert, festival, club, musical, museum, theatre',
                max_chars = 60,
            )
            free_only = st.selectbox(
                'Only free events?',
                options = ['No', 'Yes'],
                index = 0,
            ) == 'Yes'

        st.markdown('### 📍 Sightseeing preferences (optional)')
        st.caption('You can already fill this out, but if left empty Dion should focus on event planning.')
        col_sight_1, col_sight_2 = st.columns(2)
        with col_sight_1:
            sightseeing_interests = st.text_input(
                'What kind of sightseeing spots do you like?',
                placeholder = 'e.g. landmarks, viewpoints, historic places',
                max_chars = 60,
            )
            sightseeing_mode = st.selectbox(
                'Sightseeing style',
                options = SIGHTSEEING_MODE_OPTIONS,
                index = 0,
            )
        with col_sight_2:
            sightseeing_free_only = st.selectbox(
                'Only free sightseeing spots?',
                options = ['No', 'Yes'],
                index = 0,
            ) == 'Yes'

        st.markdown('### 🚫 Things to avoid')
        must_avoid_raw = st.text_input(
            'Avoid list (comma separated)',
            placeholder = 'e.g. museums, luxury restaurants, family events',
            max_chars = 90,
        )

        st.markdown('### 🌍 Output language')
        language_label = st.selectbox(
            'Output language',
            options = list(LANGUAGE_OPTIONS.keys()),
            index = 0,
        )

        st.markdown('### ✍️ One short extra note')
        user_notes = st.text_area(
            'Short free-text input',
            placeholder = 'e.g. We love rooftop bars and want one memorable highlight, but nothing too expensive.',
            max_chars = MAX_FREE_TEXT_CHARS,
            height = 110,
            help = 'Keep this short. This field is intentionally limited so the planner stays focused.',
        )
        st.caption(f'{len(user_notes)}/{MAX_FREE_TEXT_CHARS} characters used')

        submitted = st.form_submit_button('✨ Build my plan', use_container_width = True)

        if not submitted:
        return None

    min_budget_value = None if min_budget == 0 else int(min_budget)
    max_budget_value = None if max_budget == 0 else int(max_budget)

    validation_errors = validate_required_inputs(
        city = city,
        date_start = date_start,
        date_end = date_end,
        planning_mode = planning_mode,
        categories = categories,
        min_budget = min_budget_value,
        max_budget = max_budget_value,
    )

    if validation_errors:
        for error in validation_errors:
            st.error(error)
        return None

    try:
        user_request = build_user_request(
            user_name = user_name,
            city = city,
            country = country,
            date_start = date_start,
            date_end = date_end,
            planning_mode = planning_mode,
            group_size = int(group_size),
            min_budget = min_budget_value,
            max_budget = max_budget_value,
            vibe = vibe,
            categories = categories,
            time_pref_label = time_pref_label,
            free_only = free_only,
            sightseeing_interests = sightseeing_interests,
            sightseeing_mode = sightseeing_mode,
            sightseeing_free_only = sightseeing_free_only,
            must_avoid_raw = must_avoid_raw,
            language_label = language_label,
            user_notes = user_notes,
        )

    except Exception as exc:
        st.session_state['last_error'] = str(exc)
        return None

    return user_request


def render_status_and_run(user_request: UserRequest) -> None:
    st.markdown(
        """
        <div class='section-card'>
            <div class='soft-label'>Execution</div>
            <h2>⚙️ Planner run</h2>
            <p>The app validates the request, runs the planner, and generates the markdown report.</p>
        </div>
        """,
        unsafe_allow_html = True,
    )

    status_box = st.empty()
    progress_bar = st.progress(0)

    try:
        status_box.info('✅ City Keys geladen')
        progress_bar.progress(20)

        status_box.info('🔎 Events werden abgerufen…')
        progress_bar.progress(45)

        status_box.info('🧠 Plan wird gebaut…')
        progress_bar.progress(75)

        result = asyncio.run(run_full_planner_flow(user_request))

        status_box.info('📝 Report wird gespeichert…')
        progress_bar.progress(90)

        core_result = result['core_result']
        ui_result = result['ui_result']
        markdown_report = result['markdown_report']

        status_box.success('✨ Planung und Report erfolgreich erstellt')
        progress_bar.progress(100)

        st.session_state['last_user_request'] = user_request
        st.session_state['last_core_result'] = core_result
        st.session_state['last_ui_result'] = ui_result
        st.session_state['last_markdown_report'] = markdown_report
        st.session_state['last_error'] = None

    except Exception as exc:
        traceback.print_exc()
        status_box.error('The planner run failed. Please check the current project setup and MCP server configuration.')
        st.session_state['last_error'] = str(exc)


def render_results() -> None:
    ui_result = st.session_state['last_ui_result']
    user_request = st.session_state['last_user_request']
    markdown_report = st.session_state['last_markdown_report']

    if not ui_result or not user_request:
        st.info('No planner result yet. Fill in the form and run the planner.')
        return

    st.markdown(
        """
        <div class='section-card'>
            <div class='soft-label'>Generated output</div>
            <h2>✨ Result overview</h2>
            <p>Your request has been transformed into a compact city-event plan.</p>
        </div>
        """,
        unsafe_allow_html = True,
    )

    greeting_bits = [
        f'🏙️ {user_request.trip.city}',
        f'📅 {user_request.trip.date_start} → {user_request.trip.date_end}',
        f'👥 {user_request.trip.group_size} people',
    ]
    if user_request.user and user_request.user.name:
        greeting_bits.insert(0, f'👤 {user_request.user.name}')

    st.markdown(''.join([f"<span class='pill'>{item}</span>" for item in greeting_bits]), unsafe_allow_html = True)

    st.markdown('### 🌟 Recommendation')
    for sentence in ui_result.recommendation.sentences:
        st.write(f'- {sentence}')

    col_events, col_spots = st.columns(2)

    with col_events:
        st.markdown('### 🎫 Top events')
        if ui_result.top_events:
            for event in ui_result.top_events:
                with st.container(border = True):
                    st.markdown(f"**{event.name}**")
                    st.write(f"Time: {event.start_datetime or 'unknown'}")
                    st.write(f"Venue: {event.venue_name or 'unknown'}")
                    st.write(f"Price: {event.price_display or 'unknown'}")
                    if event.source_url:
                        st.link_button('Open source', event.source_url)
                    if getattr(event, 'ticket_url', None):
                        st.link_button('Open ticket page', event.ticket_url)
        else:
            st.write('No top events available.')

    with col_spots:
        st.markdown('### 📍 Sightseeing spots')
        if ui_result.sightseeing_spots:
            for spot in ui_result.sightseeing_spots:
                with st.container(border = True):
                    st.markdown(f"**{spot.name}**")
                    st.write(f"Entry: {spot.entry_fee_display or 'unknown'}")
                    st.write(f"Opening hours: {spot.opening_hours or 'unknown'}")
                    if spot.source_url:
                        st.link_button('Open source', spot.source_url)
        else:
            st.write('No sightseeing spots available.')

        st.markdown('### 🗺️ Itinerary overview')
    if ui_result.itinerary_overview:
        for day in ui_result.itinerary_overview:
            with st.expander(day.day_label, expanded = True):
                for idx, stop in enumerate(day.stops, start = 1):
                    time_label = stop.start_time or 'Time unknown'
                    duration_label = (
                        f'{stop.duration_minutes} min'
                        if stop.duration_minutes is not None
                        else 'duration unknown'
                    )
                    type_label = stop.stop_type or 'stop'

                    st.markdown(f"**{idx}. {time_label} — {stop.title}**")
                    st.caption(f'{type_label} • {duration_label}')

                    if stop.notes:
                        st.write(stop.notes)
    else:
        st.write('No itinerary overview available.')

    if ui_result.warnings:
        st.markdown('### ⚠️ Warnings')
        for warning in ui_result.warnings:
            st.warning(warning)

    if markdown_report:
        st.markdown('### 📝 Markdown report')
        st.markdown(f"**{markdown_report.title}**")

        rendered_report_parts = [f'# {markdown_report.title}\n']

        if markdown_report.recommendation and markdown_report.recommendation.sentences:
            st.markdown('#### Recommendation')
            rendered_report_parts.append('## Recommendation\n')
            for sentence in markdown_report.recommendation.sentences:
                st.write(f'- {sentence}')
                rendered_report_parts.append(f'- {sentence}\n')
            rendered_report_parts.append('\n')

        for section in markdown_report.sections:
            st.markdown(f'#### {section.heading}')
            st.markdown(section.body_markdown)
            rendered_report_parts.append(f'## {section.heading}\n\n{section.body_markdown}\n\n')

        if markdown_report.sources:
            st.markdown('#### Sources')
            rendered_report_parts.append('## Sources\n')
            for source in markdown_report.sources:
                label = source.label if source.label else source.url
                st.write(f'- {label}: {source.url}')
                rendered_report_parts.append(f'- {label}: {source.url}\n')

        rendered_report = ''.join(rendered_report_parts)

        st.download_button(
            label = '⬇️ Download markdown report',
            data = rendered_report,
            file_name = f"blastin_report_{user_request.trip.city.strip().lower().replace(' ', '_')}.md",
            mime = 'text/markdown',
            use_container_width = True,
        )

    with st.expander('Structured request preview'):
        st.json(st.session_state['last_user_request'].model_dump())

    with st.expander('Structured core result preview'):
        st.json(st.session_state['last_core_result'].model_dump())


def render_debug() -> None:
    if st.session_state['last_error']:
        st.markdown('## Debug info')
        st.error(st.session_state['last_error'])


def main() -> None:
    init_session_state()
    render_sidebar()
    render_intro()

    user_request = render_form()
    if user_request is not None:
        render_status_and_run(user_request)

    render_results()
    render_debug()


if __name__ == '__main__':
    main()


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
from src.event_client import run_full_planner_flow, run_followup_planner_flow


load_dotenv(override = True)

REPORTS_DIR = os.getenv('REPORTS_DIR', os.path.join(os.getcwd(), 'outputs', 'reports'))
os.makedirs(REPORTS_DIR, exist_ok = True)

st.set_page_config(
    page_title = 'Dion by BLASTIn',
    page_icon = '💜',
    layout = 'wide',
    initial_sidebar_state = 'collapsed',
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
            --blast-bg: #0e0a17;
            --blast-bg-2: #151022;
            --blast-surface: rgba(22, 17, 35, 0.84);
            --blast-surface-strong: rgba(30, 23, 48, 0.96);
            --blast-field: rgba(42, 28, 68, 0.72);
            --blast-field-strong: rgba(52, 34, 84, 0.84);
            --blast-border: rgba(203, 166, 247, 0.12);
            --blast-border-strong: rgba(203, 166, 247, 0.28);
            --blast-primary: #8b5cf6;
            --blast-primary-deep: #6d28d9;
            --blast-primary-soft: rgba(139, 92, 246, 0.12);
            --blast-accent: #c084fc;
            --blast-text: #f7f1ff;
            --blast-muted: #bdaed4;
            --blast-shadow: 0 26px 60px rgba(0, 0, 0, 0.34);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(192, 132, 252, 0.10), transparent 28%),
                radial-gradient(circle at top right, rgba(139, 92, 246, 0.18), transparent 32%),
                linear-gradient(180deg, #120d1d 0%, var(--blast-bg) 55%, #09070f 100%);
        }

        .block-container {
            max-width: 100%;
            padding-top: 1.5rem;
            padding-bottom: 2.4rem;
            padding-left: 2.4rem;
            padding-right: 2.4rem;
        }

        html, body, [class*="css"] {
            font-family: 'Manrope', sans-serif;
            color: var(--blast-text);
        }

        h1, h2, h3 {
            color: var(--blast-text);
            letter-spacing: -0.03em;
            font-family: 'Manrope', sans-serif !important;
        }

        h1 {
            font-size: 3.05rem !important;
            line-height: 1.02 !important;
            margin-bottom: 0.3rem !important;
            font-weight: 800 !important;
        }

        h2 {
            font-size: 1.35rem !important;
            margin-bottom: 0.35rem !important;
            font-weight: 750 !important;
        }

        h3 {
            font-size: 1.04rem !important;
            margin-bottom: 0.2rem !important;
        }

        p, label, div[data-testid='stMarkdownContainer'] p, div[data-testid='stCaptionContainer'] {
            color: var(--blast-text);
            font-size: 1rem !important;
            line-height: 1.55 !important;
        }

        div[data-testid="stMarkdownContainer"] li,
        div[data-testid="stCaptionContainer"],
        div[data-testid="stMetricLabel"] {
            color: var(--blast-muted) !important;
        }

        .dion-hero {
            background:
                linear-gradient(135deg, rgba(50, 29, 82, 0.96), rgba(109, 40, 217, 0.9) 58%, rgba(139, 92, 246, 0.84));
            border: 1px solid rgba(255, 255, 255, 0.10);
            box-shadow: 0 30px 85px rgba(107, 33, 168, 0.35);
            border-radius: 32px;
            padding: 2rem 1.8rem;
            color: white;
            overflow: hidden;
            position: relative;
            margin-bottom: 1.1rem;
        }

        .dion-hero::after {
            content: "";
            position: absolute;
            inset: -20% -10% auto auto;
            width: 260px;
            height: 260px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.12);
            filter: blur(10px);
        }

        .dion-kicker {
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.82rem;
            font-weight: 700;
            opacity: 0.86;
            margin-bottom: 0.7rem;
        }

        .dion-hero h1, .dion-hero p, .dion-hero div {
            color: white !important;
            position: relative;
            z-index: 1;
        }

        .dion-grid-card,
        .dion-panel,
        div[data-testid='stForm'] {
            background: var(--blast-surface);
            backdrop-filter: blur(14px);
            border: 1px solid var(--blast-border);
            border-radius: 26px;
            box-shadow: var(--blast-shadow);
        }

        .dion-grid-card {
            padding: 1rem 1rem;
            min-height: 120px;
        }

        .dion-panel {
            padding: 1.2rem 1.2rem;
            margin-bottom: 1.15rem;
        }

        div[data-testid='stForm'] {
            background:
                linear-gradient(180deg, rgba(28, 21, 44, 0.98), rgba(18, 14, 30, 0.96)) !important;
            border: 1px solid rgba(196, 181, 253, 0.12) !important;
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.34) !important;
            padding: 1.55rem 1.45rem 1.3rem 1.45rem;
        }

        .dion-soft-label {
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.8rem;
            color: var(--blast-muted);
            font-weight: 800;
            margin-bottom: 0.55rem;
        }

        .dion-brief {
            background: linear-gradient(180deg, rgba(139, 92, 246, 0.10), rgba(139, 92, 246, 0.04));
            border: 1px solid rgba(196, 181, 253, 0.12);
            border-radius: 20px;
            padding: 0.95rem 0.95rem 0.8rem 0.95rem;
            margin-bottom: 0.9rem;
        }

        .dion-pill {
            display: inline-block;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(216, 180, 254, 0.16);
            border-radius: 999px;
            padding: 0.33rem 0.68rem;
            margin-right: 0.4rem;
            margin-bottom: 0.45rem;
            font-size: 0.92rem;
            color: var(--blast-text);
        }

        .dion-scope-card {
            border-radius: 20px;
            padding: 0.95rem 0.95rem 0.8rem 0.95rem;
            background: linear-gradient(180deg, rgba(34, 25, 54, 0.98), rgba(21, 16, 34, 0.98));
            border: 1px solid rgba(196, 181, 253, 0.14);
            min-height: 128px;
            box-shadow: 0 16px 34px rgba(0, 0, 0, 0.26);
        }

        .dion-scope-card strong {
            display: block;
            font-size: 1.02rem;
            margin-bottom: 0.25rem;
            color: var(--blast-text);
        }

        .dion-metric-card {
            background: var(--blast-surface-strong);
            border: 1px solid rgba(196, 181, 253, 0.12);
            border-radius: 20px;
            padding: 0.85rem 0.95rem 0.8rem 0.95rem;
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.22);
        }

        .dion-section-space {
            margin-top: 0.2rem;
        }

        .dion-nav {
            display: flex;
            gap: 0.65rem;
            flex-wrap: wrap;
            margin: 1rem 0 0.2rem 0;
        }

        .dion-nav span {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: white;
            border-radius: 999px;
            padding: 0.38rem 0.75rem;
            font-size: 0.88rem;
        }

        div[data-baseweb="input"],
        div[data-baseweb="select"],
        div[data-baseweb="textarea"] {
            border-radius: 16px !important;
            background: transparent !important;
            box-shadow: none !important;
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div {
            background:
                linear-gradient(180deg, rgba(50, 33, 80, 0.9), rgba(35, 23, 58, 0.9)) !important;
            border: 1px solid rgba(216, 180, 254, 0.14) !important;
            border-radius: 16px !important;
            color: var(--blast-text) !important;
            min-height: 58px !important;
            box-shadow: none !important;
            overflow: visible !important;
            display: flex !important;
            align-items: center !important;
            margin: 0 !important;
        }

        div[data-baseweb="input"] > div:hover,
        div[data-baseweb="select"] > div:hover,
        div[data-baseweb="textarea"] > div:hover {
            background:
                linear-gradient(180deg, rgba(57, 37, 91, 0.94), rgba(40, 27, 67, 0.94)) !important;
            border-color: rgba(216, 180, 254, 0.2) !important;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div[data-testid="stDateInputField"],
        div[data-baseweb="input"] > div[data-testid="stNumberInputField"] {
            background:
                linear-gradient(180deg, rgba(50, 33, 80, 0.9), rgba(35, 23, 58, 0.9)) !important;
        }

        div[data-testid="stTextInput"] > div,
        div[data-testid="stNumberInput"] > div,
        div[data-testid="stDateInput"] > div,
        div[data-testid="stSelectbox"] > div,
        div[data-testid="stTextArea"] > div {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        div[data-testid="stDateInput"] [data-baseweb="input"],
        div[data-testid="stDateInput"] [data-baseweb="input"] > div,
        div[data-testid="stDateInput"] [data-baseweb="base-input"] {
            background:
                linear-gradient(180deg, rgba(50, 33, 80, 0.9), rgba(35, 23, 58, 0.9)) !important;
            border: 1px solid rgba(216, 180, 254, 0.14) !important;
            border-radius: 16px !important;
            box-shadow: none !important;
        }

        div[data-testid="stDateInput"] button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: var(--blast-muted) !important;
            padding-right: 0.55rem !important;
        }

        div[data-testid="stDateInput"] svg {
            fill: var(--blast-muted) !important;
        }

        div[data-baseweb="input"] > div::before,
        div[data-baseweb="input"] > div::after,
        div[data-baseweb="select"] > div::before,
        div[data-baseweb="select"] > div::after,
        div[data-baseweb="textarea"] > div::before,
        div[data-baseweb="textarea"] > div::after {
            display: none !important;
            border: none !important;
            box-shadow: none !important;
        }

        input,
        textarea,
        div[data-baseweb="select"] input {
            color: var(--blast-text) !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            line-height: 1 !important;
            padding-top: 0.76rem !important;
            padding-bottom: 0.76rem !important;
            margin: 0 !important;
        }

        div[data-testid="stNumberInput"] input {
            color: var(--blast-text) !important;
            background: transparent !important;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stDateInput"] input,
        div[data-testid="stSelectbox"] input {
            min-height: 1.35rem !important;
            transform: translateY(-3px);
        }

        div[data-testid="stTextArea"] textarea {
            background: transparent !important;
            min-height: 170px !important;
            padding-top: 0.8rem !important;
            padding-bottom: 0.8rem !important;
        }

        input::placeholder,
        textarea::placeholder {
            color: rgba(214, 196, 240, 0.8) !important;
            opacity: 1 !important;
        }

        div[data-testid="stSelectbox"] label,
        div[data-testid="stTextInput"] label,
        div[data-testid="stTextArea"] label,
        div[data-testid="stDateInput"] label,
        div[data-testid="stNumberInput"] label,
        div[data-testid="stCheckbox"] label {
            color: var(--blast-text) !important;
            font-weight: 600 !important;
        }

        button[kind="primary"] {
            background: linear-gradient(135deg, #7c3aed, #8b5cf6 55%, #6d28d9) !important;
            border: none !important;
            border-radius: 16px !important;
            color: white !important;
            font-weight: 800 !important;
            box-shadow: 0 16px 34px rgba(168, 85, 247, 0.28) !important;
        }

        button[kind="secondary"] {
            border-radius: 14px !important;
        }

        div[data-testid="stFormSubmitButton"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding-top: 0.4rem !important;
        }

        div[data-testid="stFormSubmitButton"] > div {
            background:
                linear-gradient(180deg, rgba(40, 27, 67, 0.72), rgba(24, 18, 40, 0.32)) !important;
            border: 1px solid rgba(196, 181, 253, 0.1) !important;
            border-radius: 20px !important;
            padding: 0.75rem !important;
            box-shadow: none !important;
        }

        div[data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(216, 180, 254, 0.12);
            border-radius: 18px;
        }

        .dion-form-section {
            margin-bottom: 1.5rem;
            padding-bottom: 1.35rem;
            border-bottom: 1px solid rgba(216, 180, 254, 0.10);
        }

        .dion-form-section:last-of-type {
            border-bottom: none;
            padding-bottom: 0;
        }

        .dion-form-section h3 {
            margin-bottom: 0.95rem !important;
        }

        .dion-form-subtle {
            color: var(--blast-muted);
            font-size: 0.98rem;
            margin-bottom: 1rem;
        }

        div[data-testid="stForm"] .stColumn {
            gap: 1.15rem;
        }

        .dion-output-shell {
            min-height: 780px;
        }

        .dion-output-empty {
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 440px;
        }

    </style>
    """,
    unsafe_allow_html = True,
)

TIME_PREF_OPTIONS = {
    'No preference': 'no preferences',
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
        'followup_text': '',
        'dion_scope_events': True,
        'dion_scope_sightseeing': True,
        'dion_scope_food': True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def build_user_request(
    user_name: str,
    city: str,
    country: str,
    date_start: date,
    date_end: date,
    planning_mode: str,
    events_enabled: bool,
    sightseeing_enabled: bool,
    food_drink_enabled: bool,
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
            'events_enabled': events_enabled,
            'sightseeing_enabled': sightseeing_enabled,
            'food_drink_enabled': food_drink_enabled,
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

    if sightseeing_enabled and (
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
    events_enabled: bool,
    categories: str,
    min_budget: int | None,
    max_budget: int | None,
) -> list[str]:
    errors: list[str] = []

    if not city.strip():
        errors.append('Please enter a city.')

    if date_start is not None and date_end is not None and date_end < date_start:
        errors.append('End date must be on or after the start date.')

    if not planning_mode:
        errors.append('Please choose a planning mode.')

    if events_enabled and not categories.strip():
        errors.append('Please enter at least one event category or desired activity.')

    if min_budget is None and max_budget is None:
        errors.append('Please provide at least a minimum or maximum budget.')

    return errors


def render_hero() -> None:
    st.markdown(
        """
        <div class='dion-hero'>
            <div class='dion-kicker'>Dion by BLASTIn</div>
            <h1>Curate a trip that feels intentional.</h1>
            <p>
                Dion acts like a planner, not a search box. Define the scope, shape the mood,
                and let BLASTIn turn the trip into a structured evening-forward city brief.
            </p>
            <div class='dion-nav'>
                <span>Dark mode interface</span>
                <span>Concrete venue planning</span>
                <span>Structured trip brief</span>
                <span>Follow-up revisions</span>
            </div>
        </div>
        """,
        unsafe_allow_html = True,
    )


def render_scope_controls() -> tuple[bool, bool, bool]:
    st.markdown(
        """
        <div class='dion-panel dion-section-space'>
            <div class='dion-soft-label'>Planning Scope</div>
            <h2>Choose what Dion should include</h2>
            <p>These controls update the request scope directly and are applied before the planning form is submitted.</p>
        </div>
        """,
        unsafe_allow_html = True,
    )

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        st.markdown(
            """
            <div class='dion-scope-card'>
                <strong>Events</strong>
                <p>Concerts, shows, nightlife events, and ticketed experiences.</p>
            </div>
            """,
            unsafe_allow_html = True,
        )
        events_enabled = st.checkbox(
            'Include events',
            key = 'dion_scope_events',
        )

    with col_2:
        st.markdown(
            """
            <div class='dion-scope-card'>
                <strong>Sightseeing</strong>
                <p>Landmarks, viewpoints, museums, and city highlights tailored to the trip.</p>
            </div>
            """,
            unsafe_allow_html = True,
        )
        sightseeing_enabled = st.checkbox(
            'Include sightseeing',
            key = 'dion_scope_sightseeing',
        )

    with col_3:
        st.markdown(
            """
            <div class='dion-scope-card'>
                <strong>Food & Drinks</strong>
                <p>Restaurants, bars, and places that support the mood of the trip.</p>
            </div>
            """,
            unsafe_allow_html = True,
        )
        food_drink_enabled = st.checkbox(
            'Include food & drinks',
            key = 'dion_scope_food',
        )

    return events_enabled, sightseeing_enabled, food_drink_enabled


def render_form(
    events_enabled: bool,
    sightseeing_enabled: bool,
    food_drink_enabled: bool,
) -> UserRequest | None:
    with st.form('dion_planner_form', clear_on_submit = False):
        st.markdown(
            """
            <div class='dion-soft-label'>Planning Input</div>
            <h2>Plan the trip</h2>
            <div class='dion-form-subtle'>Fill out only the parts that match the active planning scope.</div>
            """,
            unsafe_allow_html = True,
        )
        top_left, top_right = st.columns([1.06, 1.06], gap = 'large')

        with top_left:
            st.markdown("<div class='dion-form-section'>", unsafe_allow_html = True)
            st.markdown('### Traveler & Destination')
            user_name = st.text_input('Name', placeholder = 'e.g. Adriana', max_chars = 40)
            city = st.text_input('City', placeholder = 'e.g. Berlin', max_chars = 40)
            country = st.text_input('Country', placeholder = 'e.g. Germany', max_chars = 40)
            st.markdown("</div>", unsafe_allow_html = True)

            st.markdown("<div class='dion-form-section'>", unsafe_allow_html = True)
            st.markdown('### Trip Setup')
            col_date_1, col_date_2 = st.columns(2)
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

            col_setup_1, col_setup_2 = st.columns(2)
            with col_setup_1:
                group_size = st.selectbox('Group size', options = GROUP_SIZE_OPTIONS, index = 0)
            with col_setup_2:
                planning_mode_label = st.selectbox(
                    'Planning mode',
                    options = list(PLANNING_MODE_OPTIONS.keys()),
                    index = 0,
                )
            planning_mode = PLANNING_MODE_OPTIONS[planning_mode_label]
            st.markdown("</div>", unsafe_allow_html = True)

            st.markdown("<div class='dion-form-section'>", unsafe_allow_html = True)
            st.markdown('### Budget')
            col_budget_1, col_budget_2 = st.columns(2)
            with col_budget_1:
                min_budget = st.number_input('Minimum budget', min_value = 0, value = 0, step = 10)
            with col_budget_2:
                max_budget = st.number_input('Maximum budget', min_value = 0, value = 0, step = 10)
            st.markdown("</div>", unsafe_allow_html = True)

        with top_right:
            vibe = ''
            categories = ''
            time_pref_label = 'No preference'
            free_only = False
            if events_enabled:
                st.markdown("<div class='dion-form-section'>", unsafe_allow_html = True)
                st.markdown('### Event Direction')
                vibe = st.text_input(
                    'Desired vibe',
                    placeholder = 'e.g. elegant, energetic, underground, classical',
                    max_chars = 60,
                )
                col_event_1, col_event_2 = st.columns(2)
                with col_event_1:
                    time_pref_label = st.selectbox(
                        'Preferred event time',
                        options = list(TIME_PREF_OPTIONS.keys()),
                        index = 0,
                    )
                with col_event_2:
                    free_only = st.selectbox('Only free events?', options = ['No', 'Yes'], index = 0) == 'Yes'
                categories = st.text_input(
                    'Event categories',
                    placeholder = 'e.g. concert, show, club, theatre',
                    max_chars = 60,
                )
                st.markdown("</div>", unsafe_allow_html = True)

            sightseeing_interests = ''
            sightseeing_mode = 'No preference'
            sightseeing_free_only = False
            if sightseeing_enabled:
                st.markdown("<div class='dion-form-section'>", unsafe_allow_html = True)
                st.markdown('### City Direction')
                sightseeing_interests = st.text_input(
                    'Sightseeing interests',
                    placeholder = 'e.g. landmarks, viewpoints, art, history',
                    max_chars = 60,
                )
                col_sight_1, col_sight_2 = st.columns(2)
                with col_sight_1:
                    sightseeing_mode = st.selectbox(
                        'Sightseeing mode',
                        options = SIGHTSEEING_MODE_OPTIONS,
                        index = 0,
                    )
                with col_sight_2:
                    sightseeing_free_only = st.selectbox(
                        'Only free sightseeing?',
                        options = ['No', 'Yes'],
                        index = 0,
                    ) == 'Yes'
                st.markdown("</div>", unsafe_allow_html = True)

        st.markdown("<div class='dion-form-section'>", unsafe_allow_html = True)
        st.markdown('### Constraints')
        must_avoid_raw = st.text_input(
            'Avoid list',
            placeholder = 'e.g. family events, museums, luxury dining',
            max_chars = 90,
        )
        st.markdown("</div>", unsafe_allow_html = True)

        st.markdown("<div class='dion-form-section'>", unsafe_allow_html = True)
        st.markdown('### Output & Notes')
        language_label = st.selectbox('Output language', options = list(LANGUAGE_OPTIONS.keys()), index = 0)
        user_notes = st.text_area(
            'Short planning note',
            placeholder = 'e.g. We want one elegant highlight and one memorable late-night venue.',
            max_chars = MAX_FREE_TEXT_CHARS,
            height = 170,
        )
        st.caption(f'{len(user_notes)}/{MAX_FREE_TEXT_CHARS} characters used')
        st.markdown("</div>", unsafe_allow_html = True)

        submitted = st.form_submit_button('Build plan with Dion', use_container_width = True)
        if not submitted:
            return None

    min_budget_value = None if min_budget == 0 else int(min_budget)
    max_budget_value = None if max_budget == 0 else int(max_budget)

    validation_errors = validate_required_inputs(
        city = city,
        date_start = date_start,
        date_end = date_end,
        planning_mode = planning_mode,
        events_enabled = events_enabled,
        categories = categories,
        min_budget = min_budget_value,
        max_budget = max_budget_value,
    )

    if validation_errors:
        for error in validation_errors:
            st.error(error)
        return None

    try:
        return build_user_request(
            user_name = user_name,
            city = city,
            country = country,
            date_start = date_start,
            date_end = date_end,
            planning_mode = planning_mode,
            events_enabled = events_enabled,
            sightseeing_enabled = sightseeing_enabled,
            food_drink_enabled = food_drink_enabled,
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


def render_status_and_run(user_request: UserRequest) -> None:
    st.markdown(
        """
        <div class='dion-panel'>
            <div class='dion-soft-label'>Execution</div>
            <h2>Dion is building the plan</h2>
        </div>
        """,
        unsafe_allow_html = True,
    )

    st.session_state['last_core_result'] = None
    st.session_state['last_ui_result'] = None
    st.session_state['last_markdown_report'] = None
    st.session_state['last_error'] = None

    status_box = st.empty()
    progress_bar = st.progress(0)

    try:
        status_box.info('Preparing planner context...')
        progress_bar.progress(18)

        status_box.info('Collecting events and places...')
        progress_bar.progress(44)

        status_box.info('Composing the itinerary...')
        progress_bar.progress(76)

        result = asyncio.run(run_full_planner_flow(user_request))

        status_box.info('Saving report...')
        progress_bar.progress(92)

        st.session_state['last_user_request'] = user_request
        st.session_state['last_core_result'] = result['core_result']
        st.session_state['last_ui_result'] = result['ui_result']
        st.session_state['last_markdown_report'] = result['markdown_report']
        st.session_state['last_error'] = None

        progress_bar.progress(100)
        status_box.success('Plan and report created successfully.')
    except Exception as exc:
        traceback.print_exc()
        st.session_state['last_error'] = str(exc)
        status_box.error('The planner run failed. Review the current MCP and agent setup.')


def build_markdown_preview(markdown_report, max_sections: int = 3, max_chars: int = 1700) -> str:
    parts = [f"# {markdown_report.title}\n"]

    if markdown_report.recommendation and markdown_report.recommendation.sentences:
        parts.append("## Recommendation\n")
        for sentence in markdown_report.recommendation.sentences:
            parts.append(f"- {sentence}\n")
        parts.append("\n")

    for section in markdown_report.sections[:max_sections]:
        parts.append(f"## {section.heading}\n\n{section.body_markdown}\n\n")

    preview = ''.join(parts).strip()
    if len(preview) > max_chars:
        preview = preview[:max_chars].rstrip() + '\n\n...'
    return preview


def render_result_block(title: str, body_fn) -> None:
    st.markdown(
        f"""
        <div class='dion-panel'>
            <div class='dion-soft-label'>Result Block</div>
            <h2>{title}</h2>
        </div>
        """,
        unsafe_allow_html = True,
    )
    body_fn()


def render_results() -> None:
    ui_result = st.session_state['last_ui_result']
    user_request = st.session_state['last_user_request']
    markdown_report = st.session_state['last_markdown_report']

    if not ui_result or not user_request:
        st.markdown(
            """
            <div class='dion-panel dion-output-shell dion-output-empty'>
                <div class='dion-soft-label'>Awaiting Output</div>
                <h2>No plan generated yet</h2>
                <p>Define the trip, submit the planner form, and Dion will populate the result view here.</p>
            </div>
            """,
            unsafe_allow_html = True,
        )
        return

    greeting = []
    if user_request.user.name:
        greeting.append(f'Traveler: {user_request.user.name}')
    greeting.extend(
        [
            f'City: {user_request.trip.city}',
            f'Dates: {user_request.trip.date_start} → {user_request.trip.date_end}',
            f'Group: {user_request.trip.group_size}',
        ]
    )
    st.markdown(
        "<div class='dion-brief'>" + "".join([f"<span class='dion-pill'>{item}</span>" for item in greeting]) + "</div>",
        unsafe_allow_html = True,
    )

    metric_1, metric_2, metric_3 = st.columns(3)
    with metric_1:
        st.markdown("<div class='dion-metric-card'>", unsafe_allow_html = True)
        st.metric('Events', len(ui_result.top_events))
        st.markdown("</div>", unsafe_allow_html = True)
    with metric_2:
        st.markdown("<div class='dion-metric-card'>", unsafe_allow_html = True)
        st.metric('Sightseeing', len(ui_result.sightseeing_spots))
        st.markdown("</div>", unsafe_allow_html = True)
    with metric_3:
        st.markdown("<div class='dion-metric-card'>", unsafe_allow_html = True)
        st.metric('Food & Drinks', len(ui_result.food_and_drink_spots))
        st.markdown("</div>", unsafe_allow_html = True)

    render_result_block(
        'Dion’s Recommendation',
        lambda: [st.write(f'- {sentence}') for sentence in ui_result.recommendation.sentences],
    )

    top_left, top_right = st.columns(2)

    with top_left:
        if user_request.trip.events_enabled:
            render_result_block(
                'Selected Events',
                lambda: (
                    [st.info('No verified events were found.')]
                    if not ui_result.top_events
                    else [
                        _render_card(
                            event.name,
                            [
                                f"Time: {event.start_datetime or 'unknown'}",
                                f"Venue: {event.venue_name or 'unknown'}",
                                f"Price: {event.price_display or 'unknown'}",
                            ],
                            None,
                            getattr(event, 'ticket_url', None),
                        )
                        for event in ui_result.top_events
                    ]
                ),
            )

    with top_right:
        if user_request.trip.sightseeing_enabled:
            render_result_block(
                'City Highlights',
                lambda: (
                    [st.info('No verified sightseeing spots were found.')]
                    if not ui_result.sightseeing_spots
                    else [
                        _render_card(
                            spot.name,
                            [
                                f"Entry: {spot.entry_fee_display or 'unknown'}",
                                f"Opening hours: {spot.opening_hours or 'unknown'}",
                            ],
                            spot.source_url,
                        )
                        for spot in ui_result.sightseeing_spots
                    ]
                ),
            )

    if user_request.trip.food_drink_enabled:
        render_result_block(
            'Food & Drinks',
            lambda: (
                [st.info('No verified food & drink recommendations were found.')]
                if not ui_result.food_and_drink_spots
                else _render_food_grid(ui_result.food_and_drink_spots)
            ),
        )

    render_result_block(
        'Trip Flow',
        lambda: (
            [st.info('No itinerary overview available.')]
            if not ui_result.itinerary_overview
            else [
                _render_day_overview(day)
                for day in ui_result.itinerary_overview
            ]
        ),
    )

    if ui_result.warnings:
        render_result_block(
            'Warnings',
            lambda: [st.warning(warning) for warning in ui_result.warnings],
        )

    if ui_result.personal_feedback:
        render_result_block(
            "Dion's Personal Note",
            lambda: [st.write(f'- {line}') for line in ui_result.personal_feedback],
        )

    if markdown_report:
        render_result_block(
            'Report Preview',
            lambda: st.markdown(build_markdown_preview(markdown_report)),
        )

        with st.expander('Show structured report data'):
            st.json(markdown_report.model_dump())

    with st.expander('Show structured request'):
        st.json(st.session_state['last_user_request'].model_dump())

    with st.expander('Show structured core result'):
        st.json(st.session_state['last_core_result'].model_dump())


def _render_card(title: str, lines: list[str], source_url: str | None = None, secondary_url: str | None = None) -> None:
    with st.container(border = True):
        st.markdown(f"**{title}**")
        for line in lines:
            st.write(line)
        if source_url:
            st.link_button('Open source', source_url)
        if secondary_url:
            st.link_button('Open ticket page', secondary_url)


def _render_food_grid(food_items) -> None:
    cols = st.columns(2)
    for idx, place in enumerate(food_items):
        with cols[idx % 2]:
            with st.container(border = True):
                st.markdown(f"**{place.name}**")
                st.caption(place.venue_type.title())
                st.write(f"Price: {place.price_hint or 'unknown'}")
                st.write(f"Opening hours: {place.opening_hours or 'unknown'}")
                if place.source_url:
                    st.link_button('Open source', place.source_url)


def _render_day_overview(day) -> None:
    with st.expander(day.day_label, expanded = True):
        for idx, stop in enumerate(day.stops, start = 1):
            st.markdown(f"**{idx}. {stop.start_time or 'Time unknown'} — {stop.title}**")
            st.caption((stop.stop_type or 'stop').title())
            if stop.notes:
                st.write(stop.notes)
            if stop.linked_item_name:
                st.write(f"Reference: {stop.linked_item_name}")
            if stop.source_url:
                st.link_button('Open stop source', stop.source_url)


def render_followup_section() -> None:
    user_request = st.session_state['last_user_request']
    core_result = st.session_state['last_core_result']

    if not user_request or not core_result:
        return

    st.markdown(
        """
        <div class='dion-panel'>
            <div class='dion-soft-label'>Follow-up</div>
            <h2>Refine the plan</h2>
            <p>Ask Dion to revise the current plan instead of creating a new one from scratch.</p>
        </div>
        """,
        unsafe_allow_html = True,
    )

    followup_text = st.text_area(
        'What should Dion adjust?',
        value = st.session_state.get('followup_text', ''),
        placeholder = 'e.g. Make Friday more elegant, reduce sightseeing, and add a stronger bar recommendation.',
        max_chars = 320,
        height = 120,
    )

    if st.button('Update current plan', use_container_width = True):
        if not followup_text.strip():
            st.warning('Please enter a follow-up request first.')
            return

        status_box = st.empty()
        progress_bar = st.progress(0)

        try:
            status_box.info('Dion is revising the current plan...')
            progress_bar.progress(42)

            result = asyncio.run(
                run_followup_planner_flow(
                    original_request = user_request,
                    current_plan = core_result,
                    followup_message = followup_text,
                )
            )

            status_box.info('Saving updated report...')
            progress_bar.progress(86)

            st.session_state['last_core_result'] = result['core_result']
            st.session_state['last_ui_result'] = result['ui_result']
            st.session_state['last_markdown_report'] = result['markdown_report']
            st.session_state['last_error'] = None
            st.session_state['followup_text'] = ''

            progress_bar.progress(100)
            status_box.success('Plan updated successfully.')
            st.rerun()
        except Exception as exc:
            traceback.print_exc()
            st.session_state['last_error'] = str(exc)
            status_box.error('Updating the plan failed. Review the current setup.')


def render_debug() -> None:
    if st.session_state['last_error']:
        st.markdown(
            """
            <div class='dion-panel'>
                <div class='dion-soft-label'>Diagnostics</div>
                <h2>Latest error</h2>
            </div>
            """,
            unsafe_allow_html = True,
        )
        st.error(st.session_state['last_error'])


def main() -> None:
    init_session_state()
    render_hero()
    scope_events, scope_sightseeing, scope_food = render_scope_controls()

    left_col, right_col = st.columns([1.34, 0.96], gap = 'large')

    with left_col:
        user_request = render_form(scope_events, scope_sightseeing, scope_food)
        if user_request is not None:
            render_status_and_run(user_request)
        render_followup_section()

    with right_col:
        render_results()
        render_debug()


if __name__ == '__main__':
    main()

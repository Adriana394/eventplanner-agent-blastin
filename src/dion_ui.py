from pathlib import Path
import sys
import os
import traceback
import asyncio
from datetime import date, datetime, timedelta

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
UI_TEXT = {
    'en': {
        'execution': 'Execution',
        'building_plan': 'Dion is building the plan',
        'preparing_context': 'Preparing planner context...',
        'collecting_items': 'Collecting events and places...',
        'composing_itinerary': 'Composing the itinerary...',
        'saving_report': 'Saving report...',
        'plan_created': 'Plan and report created successfully.',
        'planner_failed': 'The planner run failed. Review the current MCP and agent setup.',
        'recommendation_heading': "Dion's Recommendation",
        'result_block': 'Result Block',
        'awaiting_output': 'Awaiting Output',
        'no_plan_title': 'No plan generated yet',
        'no_plan_body': 'Define the trip, submit the planner form, and Dion will populate the result view here.',
        'traveler': 'Traveler',
        'city': 'City',
        'dates': 'Dates',
        'group': 'Group',
        'events': 'Events',
        'sightseeing': 'Sightseeing',
        'food_drinks': 'Food & Drinks',
        'selected_events': 'Selected Events',
        'city_highlights': 'City Highlights',
        'trip_flow': 'Trip Flow',
        'warnings': 'Warnings',
        'personal_note': "Dion's Personal Note",
        'report_preview': 'Report Preview',
        'show_report_data': 'Show structured report data',
        'show_request_data': 'Show structured request',
        'show_core_result': 'Show structured core result',
        'no_events_found': 'No verified events were found.',
        'no_sightseeing_found': 'No verified sightseeing spots were found.',
        'no_food_found': 'No verified food & drink recommendations were found.',
        'no_itinerary': 'No itinerary overview available.',
        'time': 'Time',
        'venue': 'Venue',
        'price': 'Price',
        'entry': 'Entry',
        'opening_hours': 'Opening hours',
        'open_source': 'Open source',
        'open_ticket_page': 'Open ticket page',
        'open_stop_source': 'Open stop source',
        'reference': 'Reference',
        'time_unknown': 'Time unknown',
        'unknown_day': 'Unknown day',
        'followup': 'Follow-up',
        'refine_plan': 'Refine the plan',
        'followup_body': 'Ask Dion to revise the current plan instead of creating a new one from scratch.',
        'followup_prompt': 'What should Dion adjust?',
        'followup_placeholder': 'e.g. Make Friday more elegant, reduce sightseeing, and add a stronger bar recommendation.',
        'update_plan': 'Update current plan',
        'followup_required': 'Please enter a follow-up request first.',
        'followup_or_form_required': 'Please enter a follow-up request or change the planning selections first.',
        'revising_plan': 'Dion is revising the current plan...',
        'saving_updated_report': 'Saving updated report...',
        'plan_updated': 'Plan updated successfully.',
        'update_failed': 'Updating the plan failed. Review the current setup.',
        'new_planning_run': 'New Planning Run',
        'start_from_scratch': 'Start from scratch',
        'reset_body': 'Discard the current planning session and open a fresh planning form for a completely new trip brief.',
        'reset_button': 'Reset Dion and create a new plan',
        'recommendation_preview': 'Recommendation',
    },
    'de': {
        'execution': 'Ausführung',
        'building_plan': 'Dion erstellt gerade den Plan',
        'preparing_context': 'Planungskontext wird vorbereitet...',
        'collecting_items': 'Events und Orte werden gesammelt...',
        'composing_itinerary': 'Reiseplan wird zusammengestellt...',
        'saving_report': 'Bericht wird gespeichert...',
        'plan_created': 'Plan und Bericht wurden erfolgreich erstellt.',
        'planner_failed': 'Der Planungslauf ist fehlgeschlagen. Bitte prüfe die aktuelle MCP- und Agent-Konfiguration.',
        'recommendation_heading': 'Dions Empfehlung',
        'result_block': 'Ergebnis',
        'awaiting_output': 'Warten auf Ausgabe',
        'no_plan_title': 'Noch kein Plan erstellt',
        'no_plan_body': 'Lege die Reise fest und sende das Formular ab. Dion füllt dann hier die Ergebnisansicht.',
        'traveler': 'Reisende Person',
        'city': 'Stadt',
        'dates': 'Daten',
        'group': 'Gruppe',
        'events': 'Events',
        'sightseeing': 'Sightseeing',
        'food_drinks': 'Essen & Drinks',
        'selected_events': 'Ausgewählte Events',
        'city_highlights': 'Stadt-Highlights',
        'trip_flow': 'Reiseverlauf',
        'warnings': 'Hinweise',
        'personal_note': 'Dions persönliche Notiz',
        'report_preview': 'Berichtsvorschau',
        'show_report_data': 'Strukturierte Berichtsdaten anzeigen',
        'show_request_data': 'Strukturierte Anfrage anzeigen',
        'show_core_result': 'Strukturiertes Kernergebnis anzeigen',
        'no_events_found': 'Es wurden keine verifizierten Events gefunden.',
        'no_sightseeing_found': 'Es wurden keine verifizierten Sightseeing-Orte gefunden.',
        'no_food_found': 'Es wurden keine verifizierten Essen- und Drink-Empfehlungen gefunden.',
        'no_itinerary': 'Keine Itinerary-Übersicht verfügbar.',
        'time': 'Uhrzeit',
        'venue': 'Ort',
        'price': 'Preis',
        'entry': 'Eintritt',
        'opening_hours': 'Öffnungszeiten',
        'open_source': 'Quelle öffnen',
        'open_ticket_page': 'Ticketseite öffnen',
        'open_stop_source': 'Stopp-Quelle öffnen',
        'reference': 'Referenz',
        'time_unknown': 'Uhrzeit unbekannt',
        'unknown_day': 'Unbekannter Tag',
        'followup': 'Follow-up',
        'refine_plan': 'Plan anpassen',
        'followup_body': 'Bitte Dion, den aktuellen Plan gezielt zu überarbeiten statt einen komplett neuen zu erstellen.',
        'followup_prompt': 'Was soll Dion anpassen?',
        'followup_placeholder': 'z. B. Mach den Freitag eleganter, reduziere Sightseeing und ergänze eine stärkere Bar-Empfehlung.',
        'update_plan': 'Aktuellen Plan aktualisieren',
        'followup_required': 'Bitte gib zuerst einen Follow-up-Wunsch ein.',
        'followup_or_form_required': 'Bitte gib einen Follow-up-Wunsch ein oder ändere zuerst die Planungsauswahl.',
        'revising_plan': 'Dion überarbeitet gerade den aktuellen Plan...',
        'saving_updated_report': 'Aktualisierter Bericht wird gespeichert...',
        'plan_updated': 'Plan wurde erfolgreich aktualisiert.',
        'update_failed': 'Die Aktualisierung des Plans ist fehlgeschlagen. Bitte prüfe das aktuelle Setup.',
        'new_planning_run': 'Neuer Planlauf',
        'start_from_scratch': 'Komplett neu starten',
        'reset_body': 'Verwirf die aktuelle Planungssitzung und öffne ein frisches Formular für einen komplett neuen Plan.',
        'reset_button': 'Dion zurücksetzen und neuen Plan erstellen',
        'recommendation_preview': 'Empfehlung',
    },
}


def _format_trip_date(value: date | str | None) -> str:
    if value is None:
        return 'unknown'
    if isinstance(value, date):
        return value.strftime('%d.%m.%Y')

    parsed = _try_parse_datetime(value)
    if parsed is not None:
        return parsed.strftime('%d.%m.%Y')

    try:
        return date.fromisoformat(str(value)).strftime('%d.%m.%Y')
    except ValueError:
        return str(value)


def _try_parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.strip()
    if normalized.endswith('Z'):
        normalized = normalized[:-1] + '+00:00'

    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _format_event_datetime(value: str | None) -> str:
    parsed = _try_parse_datetime(value)
    if parsed is None:
        return value or 'unknown'
    return parsed.strftime('%a, %d.%m.%Y, %H:%M')


def _format_day_label(value: str | None) -> str:
    if not value:
        return 'Unknown day'

    parsed = _try_parse_datetime(value)
    if parsed is not None:
        return parsed.strftime('%A, %d.%m.%Y')

    try:
        return date.fromisoformat(value).strftime('%A, %d.%m.%Y')
    except ValueError:
        return value


def _get_ui_language(user_request: UserRequest | None = None) -> str:
    request = user_request or st.session_state.get('last_user_request')
    if request and request.delivery and getattr(request.delivery, 'language', None):
        return 'de' if request.delivery.language.value == 'Deutsch' else 'en'
    return 'en'


def _t(key: str, user_request: UserRequest | None = None) -> str:
    language = _get_ui_language(user_request)
    return UI_TEXT[language].get(key, UI_TEXT['en'][key])


def init_session_state() -> None:
    defaults = {
        'last_user_request': None,
        'last_core_result': None,
        'last_ui_result': None,
        'last_markdown_report': None,
        'last_error': None,
        'followup_text': '',
        'planner_form_version': 0,
        'dion_scope_events': True,
        'dion_scope_sightseeing': True,
        'dion_scope_food': True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_planner_state() -> None:
    st.session_state['last_user_request'] = None
    st.session_state['last_core_result'] = None
    st.session_state['last_ui_result'] = None
    st.session_state['last_markdown_report'] = None
    st.session_state['last_error'] = None
    st.session_state['followup_text'] = ''
    st.session_state['dion_scope_events'] = True
    st.session_state['dion_scope_sightseeing'] = True
    st.session_state['dion_scope_food'] = True
    st.session_state['planner_form_version'] += 1


def _build_form_change_followup_message() -> str:
    return (
        'Revise the existing plan to match the updated planning form selections and constraints. '
        'Treat the current form values as the new baseline request and update the plan accordingly.'
    )


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


def render_scope_controls(disabled: bool = False) -> tuple[bool, bool, bool]:
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
            disabled = disabled,
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
            disabled = disabled,
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
            disabled = disabled,
        )

    return events_enabled, sightseeing_enabled, food_drink_enabled


def render_form(
    events_enabled: bool,
    sightseeing_enabled: bool,
    food_drink_enabled: bool,
) -> UserRequest | None:
    existing_request = st.session_state.get('last_user_request')
    has_existing_plan = st.session_state.get('last_core_result') is not None

    user_name_value = existing_request.user.name if existing_request and existing_request.user else ''
    city_value = existing_request.trip.city if existing_request else ''
    country_value = existing_request.trip.country if existing_request and existing_request.trip.country else ''
    date_start_value = existing_request.trip.date_start if existing_request else date.today() + timedelta(days = 7)
    date_end_value = existing_request.trip.date_end if existing_request else date.today() + timedelta(days = 9)
    group_size_value = existing_request.trip.group_size if existing_request and existing_request.trip.group_size else GROUP_SIZE_OPTIONS[0]
    planning_mode_value = (
        existing_request.trip.planning_mode.value
        if existing_request and existing_request.trip.planning_mode
        else PLANNING_MODE_OPTIONS['Full Trip']
    )
    planning_mode_index = list(PLANNING_MODE_OPTIONS.values()).index(planning_mode_value)

    min_budget_default = 0
    max_budget_default = 0
    if existing_request and existing_request.trip.budget:
        min_budget_default = int(existing_request.trip.budget.min_budget or 0)
        max_budget_default = int(existing_request.trip.budget.max_budget or 0)

    vibe_value = existing_request.events.vibe if existing_request and existing_request.events and existing_request.events.vibe else ''
    categories_value = existing_request.events.categories if existing_request and existing_request.events and existing_request.events.categories else ''
    time_pref_value = (
        existing_request.events.time_pref.value
        if existing_request and existing_request.events and existing_request.events.time_pref
        else TIME_PREF_OPTIONS['No preference']
    )
    time_pref_index = list(TIME_PREF_OPTIONS.values()).index(time_pref_value)
    free_only_value = bool(existing_request.events.free_only) if existing_request and existing_request.events else False

    sightseeing_interests_value = (
        existing_request.sightseeing.interests
        if existing_request and existing_request.sightseeing and existing_request.sightseeing.interests
        else ''
    )
    sightseeing_mode_value = (
        existing_request.sightseeing.indoor_outdoor.title()
        if existing_request and existing_request.sightseeing and existing_request.sightseeing.indoor_outdoor
        else 'No preference'
    )
    sightseeing_mode_index = SIGHTSEEING_MODE_OPTIONS.index(sightseeing_mode_value)
    sightseeing_free_only_value = bool(existing_request.sightseeing.free_only) if existing_request and existing_request.sightseeing else False

    must_avoid_value = ', '.join(existing_request.itinerary.must_avoid) if existing_request and existing_request.itinerary and existing_request.itinerary.must_avoid else ''
    language_value = (
        existing_request.delivery.language.value
        if existing_request and existing_request.delivery and existing_request.delivery.language
        else LANGUAGE_OPTIONS['English']
    )
    language_index = list(LANGUAGE_OPTIONS.values()).index(language_value)

    with st.form(f"dion_planner_form_{st.session_state['planner_form_version']}", clear_on_submit = False):
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
            user_name = st.text_input('Name', value = user_name_value, placeholder = 'e.g. Adriana', max_chars = 40)
            city = st.text_input('City', value = city_value, placeholder = 'e.g. Berlin', max_chars = 40)
            country = st.text_input('Country', value = country_value, placeholder = 'e.g. Germany', max_chars = 40)
            st.markdown("</div>", unsafe_allow_html = True)

            st.markdown("<div class='dion-form-section'>", unsafe_allow_html = True)
            st.markdown('### Trip Setup')
            col_date_1, col_date_2 = st.columns(2)
            with col_date_1:
                date_start = st.date_input(
                    'Start date',
                    value = date_start_value,
                    min_value = date.today(),
                )
            with col_date_2:
                date_end = st.date_input(
                    'End date',
                    value = date_end_value,
                    min_value = date.today(),
                )

            col_setup_1, col_setup_2 = st.columns(2)
            with col_setup_1:
                group_size = st.selectbox(
                    'Group size',
                    options = GROUP_SIZE_OPTIONS,
                    index = GROUP_SIZE_OPTIONS.index(group_size_value),
                )
            with col_setup_2:
                planning_mode_label = st.selectbox(
                    'Planning mode',
                    options = list(PLANNING_MODE_OPTIONS.keys()),
                    index = planning_mode_index,
                )
            planning_mode = PLANNING_MODE_OPTIONS[planning_mode_label]
            st.markdown("</div>", unsafe_allow_html = True)

            st.markdown("<div class='dion-form-section'>", unsafe_allow_html = True)
            st.markdown('### Budget')
            col_budget_1, col_budget_2 = st.columns(2)
            with col_budget_1:
                min_budget = st.number_input('Minimum budget', min_value = 0, value = min_budget_default, step = 10)
            with col_budget_2:
                max_budget = st.number_input('Maximum budget', min_value = 0, value = max_budget_default, step = 10)
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
                    value = vibe_value,
                    placeholder = 'e.g. elegant, energetic, underground, classical',
                    max_chars = 60,
                )
                col_event_1, col_event_2 = st.columns(2)
                with col_event_1:
                    time_pref_label = st.selectbox(
                        'Preferred event time',
                        options = list(TIME_PREF_OPTIONS.keys()),
                        index = time_pref_index,
                    )
                with col_event_2:
                    free_only = st.selectbox(
                        'Only free events?',
                        options = ['No', 'Yes'],
                        index = 1 if free_only_value else 0,
                    ) == 'Yes'
                categories = st.text_input(
                    'Event categories',
                    value = categories_value,
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
                    value = sightseeing_interests_value,
                    placeholder = 'e.g. landmarks, viewpoints, art, history',
                    max_chars = 60,
                )
                col_sight_1, col_sight_2 = st.columns(2)
                with col_sight_1:
                    sightseeing_mode = st.selectbox(
                        'Sightseeing mode',
                        options = SIGHTSEEING_MODE_OPTIONS,
                        index = sightseeing_mode_index,
                    )
                with col_sight_2:
                    sightseeing_free_only = st.selectbox(
                        'Only free sightseeing?',
                        options = ['No', 'Yes'],
                        index = 1 if sightseeing_free_only_value else 0,
                    ) == 'Yes'
                st.markdown("</div>", unsafe_allow_html = True)

        st.markdown("<div class='dion-form-section'>", unsafe_allow_html = True)
        st.markdown('### Constraints')
        must_avoid_raw = st.text_input(
            'Avoid list',
            value = must_avoid_value,
            placeholder = 'e.g. family events, museums, luxury dining',
            max_chars = 90,
        )
        st.markdown("</div>", unsafe_allow_html = True)

        st.markdown("<div class='dion-form-section'>", unsafe_allow_html = True)
        if not has_existing_plan:
            st.markdown('### Output & Notes')
        else:
            st.markdown(f"### {_t('followup', existing_request)}")

        language_label = st.selectbox(
            'Output language',
            options = list(LANGUAGE_OPTIONS.keys()),
            index = language_index,
        )
        user_notes = ''
        followup_text = ''
        if not has_existing_plan:
            user_notes = st.text_area(
                'Short planning note',
                placeholder = 'e.g. We want one elegant highlight and one memorable late-night venue.',
                max_chars = MAX_FREE_TEXT_CHARS,
                height = 170,
            )
            st.caption(f'{len(user_notes)}/{MAX_FREE_TEXT_CHARS} characters used')
        else:
            st.markdown(_t('followup_body', existing_request))
            followup_text = st.text_area(
                _t('followup_prompt', existing_request),
                value = st.session_state.get('followup_text', ''),
                placeholder = _t('followup_placeholder', existing_request),
                max_chars = 320,
                height = 120,
            )
        st.markdown("</div>", unsafe_allow_html = True)

        submitted = st.form_submit_button(
            _t('update_plan', existing_request) if has_existing_plan else 'Build plan with Dion',
            use_container_width = True,
        )
        if not submitted:
            return None

    if has_existing_plan:
        min_budget_value = None if min_budget == 0 else int(min_budget)
        max_budget_value = None if max_budget == 0 else int(max_budget)

        updated_request = build_user_request(
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
            user_notes = '',
        )

        normalized_followup_text = followup_text.strip()
        request_changed = updated_request.model_dump(mode = 'json') != existing_request.model_dump(mode = 'json')

        if not normalized_followup_text and not request_changed:
            st.warning(_t('followup_or_form_required', existing_request))
            return None

        effective_followup_text = normalized_followup_text or _build_form_change_followup_message()
        run_followup_update(updated_request, st.session_state['last_core_result'], effective_followup_text)
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
        f"""
        <div class='dion-panel'>
            <div class='dion-soft-label'>{_t('execution', user_request)}</div>
            <h2>{_t('building_plan', user_request)}</h2>
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
        status_box.info(_t('preparing_context', user_request))
        progress_bar.progress(18)

        status_box.info(_t('collecting_items', user_request))
        progress_bar.progress(44)

        status_box.info(_t('composing_itinerary', user_request))
        progress_bar.progress(76)

        result = asyncio.run(run_full_planner_flow(user_request))

        status_box.info(_t('saving_report', user_request))
        progress_bar.progress(92)

        st.session_state['last_user_request'] = user_request
        st.session_state['last_core_result'] = result['core_result']
        st.session_state['last_ui_result'] = result['ui_result']
        st.session_state['last_markdown_report'] = result['markdown_report']
        st.session_state['last_error'] = None

        progress_bar.progress(100)
        status_box.success(_t('plan_created', user_request))
    except Exception as exc:
        traceback.print_exc()
        st.session_state['last_error'] = str(exc)
        status_box.error(_t('planner_failed', user_request))


def run_followup_update(user_request: UserRequest, core_result, followup_text: str) -> None:
    status_box = st.empty()
    progress_bar = st.progress(0)

    try:
        status_box.info(_t('revising_plan', user_request))
        progress_bar.progress(42)

        result = asyncio.run(
            run_followup_planner_flow(
                original_request = user_request,
                current_plan = core_result,
                followup_message = followup_text,
            )
        )

        status_box.info(_t('saving_updated_report', user_request))
        progress_bar.progress(86)

        st.session_state['last_core_result'] = result['core_result']
        st.session_state['last_ui_result'] = result['ui_result']
        st.session_state['last_markdown_report'] = result['markdown_report']
        st.session_state['last_user_request'] = user_request
        st.session_state['last_error'] = None
        st.session_state['followup_text'] = ''

        progress_bar.progress(100)
        status_box.success(_t('plan_updated', user_request))
        st.rerun()
    except Exception as exc:
        traceback.print_exc()
        st.session_state['last_error'] = str(exc)
        status_box.error(_t('update_failed', user_request))


def build_markdown_preview(markdown_report, max_sections: int = 3, max_chars: int = 1700) -> str:
    parts = [f"# {markdown_report.title}\n"]

    if markdown_report.recommendation and markdown_report.recommendation.sentences:
        parts.append(f"## {_t('recommendation_preview')}\n")
        for sentence in markdown_report.recommendation.sentences:
            parts.append(f"- {sentence}\n")
        parts.append("\n")

    for section in markdown_report.sections[:max_sections]:
        parts.append(f"## {section.heading}\n\n{section.body_markdown}\n\n")

    preview = ''.join(parts).strip()
    if len(preview) > max_chars:
        preview = preview[:max_chars].rstrip() + '\n\n...'
    return preview


def render_result_block(title: str, body_fn, user_request: UserRequest | None = None) -> None:
    st.markdown(
        f"""
        <div class='dion-panel'>
            <div class='dion-soft-label'>{_t('result_block', user_request)}</div>
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
        greeting.append(f"{_t('traveler', user_request)}: {user_request.user.name}")
    greeting.extend(
        [
            f"{_t('city', user_request)}: {user_request.trip.city}",
            f"{_t('dates', user_request)}: {_format_trip_date(user_request.trip.date_start)} → {_format_trip_date(user_request.trip.date_end)}",
            f"{_t('group', user_request)}: {user_request.trip.group_size}",
        ]
    )
    st.markdown(
        "<div class='dion-brief'>" + "".join([f"<span class='dion-pill'>{item}</span>" for item in greeting]) + "</div>",
        unsafe_allow_html = True,
    )

    metric_1, metric_2, metric_3 = st.columns(3)
    with metric_1:
        st.markdown("<div class='dion-metric-card'>", unsafe_allow_html = True)
        st.metric(_t('events', user_request), len(ui_result.top_events))
        st.markdown("</div>", unsafe_allow_html = True)
    with metric_2:
        st.markdown("<div class='dion-metric-card'>", unsafe_allow_html = True)
        st.metric(_t('sightseeing', user_request), len(ui_result.sightseeing_spots))
        st.markdown("</div>", unsafe_allow_html = True)
    with metric_3:
        st.markdown("<div class='dion-metric-card'>", unsafe_allow_html = True)
        st.metric(_t('food_drinks', user_request), len(ui_result.food_and_drink_spots))
        st.markdown("</div>", unsafe_allow_html = True)

    render_result_block(
        _t('recommendation_heading', user_request),
        lambda: [st.write(f'- {sentence}') for sentence in ui_result.recommendation.sentences],
        user_request,
    )

    top_left, top_right = st.columns(2)

    with top_left:
        if user_request.trip.events_enabled:
            render_result_block(
                _t('selected_events', user_request),
                lambda: (
                    [st.info(_t('no_events_found', user_request))]
                    if not ui_result.top_events
                    else [
                        _render_card(
                            event.name,
                            [
                                f"{_t('time', user_request)}: {_format_event_datetime(event.start_datetime)}",
                                f"{_t('venue', user_request)}: {event.venue_name or 'unknown'}",
                                f"{_t('price', user_request)}: {event.price_display or 'unknown'}",
                            ],
                            None,
                            getattr(event, 'ticket_url', None),
                            user_request,
                        )
                        for event in ui_result.top_events
                    ]
                ),
                user_request,
            )

    with top_right:
        if user_request.trip.sightseeing_enabled:
            render_result_block(
                _t('city_highlights', user_request),
                lambda: (
                    [st.info(_t('no_sightseeing_found', user_request))]
                    if not ui_result.sightseeing_spots
                    else [
                        _render_card(
                            spot.name,
                            [
                                f"{_t('entry', user_request)}: {spot.entry_fee_display or 'unknown'}",
                                f"{_t('opening_hours', user_request)}: {spot.opening_hours or 'unknown'}",
                            ],
                            spot.source_url,
                            user_request = user_request,
                        )
                        for spot in ui_result.sightseeing_spots
                    ]
                ),
                user_request,
            )

    if user_request.trip.food_drink_enabled:
        render_result_block(
            _t('food_drinks', user_request),
            lambda: (
                [st.info(_t('no_food_found', user_request))]
                if not ui_result.food_and_drink_spots
                else _render_food_grid(ui_result.food_and_drink_spots, user_request)
            ),
            user_request,
        )

    render_result_block(
        _t('trip_flow', user_request),
        lambda: (
            [st.info(_t('no_itinerary', user_request))]
            if not ui_result.itinerary_overview
            else [
                _render_day_overview(day, user_request)
                for day in ui_result.itinerary_overview
            ]
        ),
        user_request,
    )

    if ui_result.warnings:
        render_result_block(
            _t('warnings', user_request),
            lambda: [st.warning(warning) for warning in ui_result.warnings],
            user_request,
        )

    if ui_result.personal_feedback:
        render_result_block(
            _t('personal_note', user_request),
            lambda: [st.write(f'- {line}') for line in ui_result.personal_feedback],
            user_request,
        )

    if markdown_report:
        render_result_block(
            _t('report_preview', user_request),
            lambda: st.markdown(build_markdown_preview(markdown_report)),
            user_request,
        )

        with st.expander(_t('show_report_data', user_request)):
            st.json(markdown_report.model_dump())

    with st.expander(_t('show_request_data', user_request)):
        st.json(st.session_state['last_user_request'].model_dump())

    with st.expander(_t('show_core_result', user_request)):
        st.json(st.session_state['last_core_result'].model_dump())


def _render_card(title: str, lines: list[str], source_url: str | None = None, secondary_url: str | None = None, user_request: UserRequest | None = None) -> None:
    with st.container(border = True):
        st.markdown(f"**{title}**")
        for line in lines:
            st.write(line)
        if source_url:
            st.link_button(_t('open_source', user_request), source_url)
        if secondary_url:
            st.link_button(_t('open_ticket_page', user_request), secondary_url)


def _render_food_grid(food_items, user_request: UserRequest | None = None) -> None:
    cols = st.columns(2)
    for idx, place in enumerate(food_items):
        with cols[idx % 2]:
            with st.container(border = True):
                st.markdown(f"**{place.name}**")
                st.caption(place.venue_type.title())
                st.write(f"{_t('price', user_request)}: {place.price_hint or 'unknown'}")
                st.write(f"{_t('opening_hours', user_request)}: {place.opening_hours or 'unknown'}")
                if place.source_url:
                    st.link_button(_t('open_source', user_request), place.source_url)


def _render_day_overview(day, user_request: UserRequest | None = None) -> None:
    with st.expander(_format_day_label(day.day_label), expanded = True):
        for idx, stop in enumerate(day.stops, start = 1):
            st.markdown(f"**{idx}. {stop.start_time or _t('time_unknown', user_request)} — {stop.title}**")
            st.caption((stop.stop_type or 'stop').title())
            if stop.notes:
                st.write(stop.notes)
            if stop.linked_item_name:
                st.write(f"{_t('reference', user_request)}: {stop.linked_item_name}")
            if stop.source_url:
                st.link_button(_t('open_stop_source', user_request), stop.source_url)


def render_followup_section() -> None:
    return


def render_reset_section() -> None:
    user_request = st.session_state.get('last_user_request')
    if not st.session_state.get('last_core_result'):
        return

    st.markdown(
        f"""
        <div class='dion-panel'>
            <div class='dion-soft-label'>{_t('new_planning_run', user_request)}</div>
            <h2>{_t('start_from_scratch', user_request)}</h2>
            <p>{_t('reset_body', user_request)}</p>
        </div>
        """,
        unsafe_allow_html = True,
    )

    if st.button(_t('reset_button', user_request), use_container_width = True):
        reset_planner_state()
        st.rerun()


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
    has_existing_plan = st.session_state.get('last_core_result') is not None
    scope_events, scope_sightseeing, scope_food = render_scope_controls(disabled = has_existing_plan)

    left_col, right_col = st.columns([1.34, 0.96], gap = 'large')

    with left_col:
        user_request = render_form(scope_events, scope_sightseeing, scope_food)
        if user_request is not None:
            render_status_and_run(user_request)
        render_followup_section()
        render_reset_section()

    with right_col:
        render_results()
        render_debug()


if __name__ == '__main__':
    main()

from __future__ import annotations

import asyncio
import html
import os
import sys
import traceback
from datetime import date, datetime, timedelta
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.event_client import run_followup_planner_flow, run_full_planner_flow
from src.schemas import UserRequest


load_dotenv(override = True)

REPORTS_DIR = os.getenv('REPORTS_DIR', os.path.join(os.getcwd(), 'outputs', 'reports'))
os.makedirs(REPORTS_DIR, exist_ok = True)

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
        'revising_plan': 'Dion is revising the current plan...',
        'plan_created': 'Plan and report created successfully.',
        'plan_updated': 'Plan updated successfully.',
        'planner_failed': 'The planner run failed. Review the current MCP and agent setup.',
        'update_failed': 'Updating the plan failed. Review the current setup.',
        'recommendation_heading': "Dion's Recommendation",
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
        'reference': 'Reference',
        'time_unknown': 'Time unknown',
        'followup': 'Follow-up',
        'followup_body': 'Ask Dion to revise the current plan instead of creating a new one from scratch.',
        'followup_prompt': 'What should Dion adjust?',
        'followup_placeholder': 'e.g. Make Friday more elegant, reduce sightseeing, and add a stronger bar recommendation.',
        'update_plan': 'Update current plan',
        'followup_or_form_required': 'Please enter a follow-up request or change the planning selections first.',
        'new_planning_run': 'New Planning Run',
        'start_from_scratch': 'Start from scratch',
        'reset_body': 'Discard the current planning session and open a fresh planning form for a completely new trip brief.',
        'reset_button': 'Reset Dion and create a new plan',
        'recommendation_preview': 'Recommendation',
        'saved_report': 'Saved report',
    },
    'de': {
        'execution': 'Ausführung',
        'building_plan': 'Dion erstellt gerade den Plan',
        'revising_plan': 'Dion überarbeitet gerade den aktuellen Plan...',
        'plan_created': 'Plan und Bericht wurden erfolgreich erstellt.',
        'plan_updated': 'Plan wurde erfolgreich aktualisiert.',
        'planner_failed': 'Der Planungslauf ist fehlgeschlagen. Bitte prüfe die aktuelle MCP- und Agent-Konfiguration.',
        'update_failed': 'Die Aktualisierung des Plans ist fehlgeschlagen. Bitte prüfe das aktuelle Setup.',
        'recommendation_heading': 'Dions Empfehlung',
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
        'reference': 'Referenz',
        'time_unknown': 'Uhrzeit unbekannt',
        'followup': 'Follow-up',
        'followup_body': 'Bitte Dion, den aktuellen Plan gezielt zu überarbeiten statt einen komplett neuen zu erstellen.',
        'followup_prompt': 'Was soll Dion anpassen?',
        'followup_placeholder': 'z. B. Mach den Freitag eleganter, reduziere Sightseeing und ergänze eine stärkere Bar-Empfehlung.',
        'update_plan': 'Aktuellen Plan aktualisieren',
        'followup_or_form_required': 'Bitte gib einen Follow-up-Wunsch ein oder ändere zuerst die Planungsauswahl.',
        'new_planning_run': 'Neuer Planlauf',
        'start_from_scratch': 'Komplett neu starten',
        'reset_body': 'Verwirf die aktuelle Planungssitzung und öffne ein frisches Formular für einen komplett neuen Plan.',
        'reset_button': 'Dion zurücksetzen und neuen Plan erstellen',
        'recommendation_preview': 'Empfehlung',
        'saved_report': 'Gespeicherter Bericht',
    },
}

APP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --blast-bg: #0e0a17;
    --blast-bg-2: #151022;
    --blast-surface: rgba(22, 17, 35, 0.84);
    --blast-surface-strong: rgba(30, 23, 48, 0.96);
    --blast-border: rgba(203, 166, 247, 0.12);
    --blast-primary: #8b5cf6;
    --blast-primary-deep: #6d28d9;
    --blast-text: #f7f1ff;
    --blast-muted: #bdaed4;
    --blast-shadow: 0 26px 60px rgba(0, 0, 0, 0.34);
}

body, .gradio-container {
    font-family: 'Manrope', sans-serif !important;
    color: var(--blast-text) !important;
    background:
        radial-gradient(circle at top left, rgba(192, 132, 252, 0.10), transparent 28%),
        radial-gradient(circle at top right, rgba(139, 92, 246, 0.18), transparent 32%),
        linear-gradient(180deg, #120d1d 0%, var(--blast-bg) 55%, #09070f 100%) !important;
}

.gradio-container {
    max-width: 100% !important;
    padding: 28px 32px !important;
}

.dion-shell, .dion-shell * {
    color: var(--blast-text);
}

.dion-hero {
    background: linear-gradient(135deg, rgba(50, 29, 82, 0.96), rgba(109, 40, 217, 0.9) 58%, rgba(139, 92, 246, 0.84));
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

.dion-kicker, .dion-soft-label {
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 0.82rem;
    font-weight: 800;
    color: var(--blast-muted);
}

.dion-hero .dion-kicker,
.dion-hero h1,
.dion-hero p,
.dion-hero span {
    color: white !important;
    position: relative;
    z-index: 1;
}

.dion-hero h1 {
    font-size: 3rem;
    line-height: 1.02;
    margin: 0.3rem 0;
    letter-spacing: -0.03em;
}

.dion-nav {
    display: flex;
    gap: 0.65rem;
    flex-wrap: wrap;
    margin-top: 1rem;
}

.dion-nav span,
.dion-pill {
    display: inline-block;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    padding: 0.38rem 0.75rem;
    font-size: 0.88rem;
}

.dion-panel,
.dion-card,
.dion-scope-card,
.dion-metric-card,
.dion-brief,
.dion-empty {
    background: var(--blast-surface);
    backdrop-filter: blur(14px);
    border: 1px solid var(--blast-border);
    border-radius: 26px;
    box-shadow: var(--blast-shadow);
}

.dion-panel {
    padding: 1.2rem;
    margin-bottom: 1.1rem;
}

.dion-card {
    padding: 1rem;
    margin-bottom: 0.9rem;
    border-radius: 20px;
}

.dion-card-title {
    font-weight: 800;
    margin-bottom: 0.4rem;
}

.dion-card-line {
    color: var(--blast-muted);
    margin-bottom: 0.28rem;
}

.dion-links {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 0.7rem;
}

.dion-links a {
    color: white;
    text-decoration: none;
    background: linear-gradient(135deg, #7c3aed, #8b5cf6 55%, #6d28d9);
    border-radius: 999px;
    padding: 0.48rem 0.8rem;
    font-size: 0.88rem;
    font-weight: 700;
}

.dion-grid-2 {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
}

.dion-grid-3 {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
}

.dion-scope-card,
.dion-metric-card {
    padding: 1rem;
    border-radius: 20px;
}

.dion-brief {
    padding: 0.95rem;
    margin-bottom: 1rem;
}

.dion-pill {
    border-color: rgba(216, 180, 254, 0.16);
    margin-right: 0.45rem;
    margin-bottom: 0.45rem;
}

.dion-empty {
    min-height: 440px;
    padding: 1.2rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.dion-status {
    margin-bottom: 1rem;
    padding: 0.95rem 1rem;
    border-radius: 20px;
    background: linear-gradient(180deg, rgba(139, 92, 246, 0.12), rgba(139, 92, 246, 0.04));
    border: 1px solid rgba(196, 181, 253, 0.12);
}

.dion-status.error {
    background: rgba(127, 29, 29, 0.34);
    border-color: rgba(248, 113, 113, 0.35);
}

.dion-status.success {
    background: rgba(20, 83, 45, 0.34);
    border-color: rgba(74, 222, 128, 0.3);
}

.dion-days details {
    margin-bottom: 0.8rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(216, 180, 254, 0.12);
    border-radius: 18px;
    padding: 0.8rem 1rem;
}

.dion-days summary {
    cursor: pointer;
    font-weight: 800;
}

.dion-stop {
    padding: 0.75rem 0;
    border-top: 1px solid rgba(216, 180, 254, 0.08);
}

.dion-stop:first-of-type {
    border-top: none;
}

.dion-stop-meta {
    color: var(--blast-muted);
    font-size: 0.92rem;
    margin-bottom: 0.25rem;
}

.dion-json {
    border-radius: 18px !important;
}

#planner-column, #results-column, .dion-input-wrap {
    background: transparent !important;
}

#planner-column {
    padding-right: 0.9rem;
}

#results-column {
    padding-left: 0.2rem;
    max-width: 760px;
}

.dion-input-wrap {
    border: 1px solid rgba(196, 181, 253, 0.12);
    border-radius: 26px;
    padding: 1.45rem;
    background: linear-gradient(180deg, rgba(28, 21, 44, 0.98), rgba(18, 14, 30, 0.96)) !important;
    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.34);
}

.dion-input-wrap > .gradio-row {
    gap: 1.35rem !important;
}

.dion-input-wrap .gradio-row {
    margin-bottom: 0.7rem !important;
}

.dion-input-wrap .gradio-column {
    gap: 0.85rem !important;
}

.dion-input-wrap .gr-markdown,
.dion-input-wrap .gr-button,
.dion-input-wrap .gr-form,
.dion-input-wrap .gr-group {
    margin-bottom: 0.25rem !important;
}

.dion-input-wrap textarea,
.dion-input-wrap input,
.dion-input-wrap select {
    padding-top: 0.85rem !important;
    padding-bottom: 0.85rem !important;
}

.gradio-container .block,
.gradio-container input,
.gradio-container textarea,
.gradio-container select {
    font-family: 'Manrope', sans-serif !important;
}

.gradio-container .gr-button-primary,
.gradio-container button.primary {
    background: linear-gradient(135deg, #7c3aed, #8b5cf6 55%, #6d28d9) !important;
    border: none !important;
    color: white !important;
}

.gradio-container button:focus,
.gradio-container button:focus-visible,
.gradio-container input:focus,
.gradio-container input:focus-visible,
.gradio-container textarea:focus,
.gradio-container textarea:focus-visible,
.gradio-container select:focus,
.gradio-container select:focus-visible {
    outline: none !important;
    box-shadow: 0 0 0 1px rgba(196, 181, 253, 0.24) !important;
    border-color: rgba(196, 181, 253, 0.24) !important;
}

@media (max-width: 900px) {
    .dion-grid-2,
    .dion-grid-3 {
        grid-template-columns: 1fr;
    }

    #planner-column,
    #results-column {
        padding-left: 0;
        padding-right: 0;
        max-width: 100%;
    }
}
"""


def _default_state() -> dict:
    return {
        'last_user_request': None,
        'last_core_result': None,
        'last_ui_result': None,
        'last_markdown_report': None,
        'last_error': None,
        'saved_report_path': None,
    }


def _get_ui_language(user_request: UserRequest | None = None) -> str:
    if user_request and user_request.delivery and getattr(user_request.delivery, 'language', None):
        return 'de' if user_request.delivery.language.value == 'Deutsch' else 'en'
    return 'en'


def _t(key: str, user_request: UserRequest | None = None) -> str:
    language = _get_ui_language(user_request)
    return UI_TEXT[language].get(key, UI_TEXT['en'][key])


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


def _format_event_datetime(value: str | None) -> str:
    parsed = _try_parse_datetime(value)
    if parsed is None:
        return value or 'unknown'
    return parsed.strftime('%a, %d.%m.%Y, %H:%M')


def _normalize_date_input(value: str | datetime | date | None) -> str:
    if value is None:
        raise ValueError('Date value is required.')
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()

    raw = str(value).strip()
    if not raw:
        raise ValueError('Date value is required.')

    for candidate in (raw[:10], raw):
        try:
            return date.fromisoformat(candidate).isoformat()
        except ValueError:
            continue

    parsed = _try_parse_datetime(raw)
    if parsed is not None:
        return parsed.date().isoformat()

    raise ValueError('Please use a valid date.')


def _format_day_label(value: str | None, user_request: UserRequest | None = None) -> str:
    if not value:
        return 'Unknown day'

    parsed = _try_parse_datetime(value)
    if parsed is not None:
        return parsed.strftime('%A, %d.%m.%Y')

    try:
        return date.fromisoformat(value).strftime('%A, %d.%m.%Y')
    except ValueError:
        return value


def _link_button(url: str, label: str) -> str:
    return f'<a href="{html.escape(url, quote = True)}" target="_blank" rel="noopener noreferrer">{html.escape(label)}</a>'


def _render_status(message: str, tone: str = 'info') -> str:
    tone_class = '' if tone == 'info' else f' {tone}'
    return f"<div class='dion-status{tone_class}'>{html.escape(message)}</div>"


def _render_card(title: str, lines: list[str], source_url: str | None = None, secondary_url: str | None = None, user_request: UserRequest | None = None) -> str:
    links: list[str] = []
    if source_url:
        links.append(_link_button(source_url, _t('open_source', user_request) if 'open_source' in UI_TEXT[_get_ui_language(user_request)] else 'Open source'))
    if secondary_url:
        links.append(_link_button(secondary_url, _t('open_ticket_page', user_request) if 'open_ticket_page' in UI_TEXT[_get_ui_language(user_request)] else 'Open ticket page'))

    links_html = f"<div class='dion-links'>{''.join(links)}</div>" if links else ''
    lines_html = ''.join(f"<div class='dion-card-line'>{html.escape(line)}</div>" for line in lines)
    return (
        "<div class='dion-card'>"
        f"<div class='dion-card-title'>{html.escape(title)}</div>"
        f"{lines_html}"
        f"{links_html}"
        "</div>"
    )


def _render_food_grid(food_items, user_request: UserRequest | None = None) -> str:
    cards = []
    for place in food_items:
        cards.append(
            _render_card(
                place.name,
                [
                    place.venue_type.title(),
                    f"{_t('price', user_request)}: {place.price_hint or 'unknown'}",
                    f"{_t('opening_hours', user_request)}: {place.opening_hours or 'unknown'}",
                ],
                place.source_url,
                user_request = user_request,
            )
        )
    return f"<div class='dion-grid-2'>{''.join(cards)}</div>"


def _render_day_overview(day, user_request: UserRequest | None = None) -> str:
    stops_html: list[str] = []
    for idx, stop in enumerate(day.stops, start = 1):
        meta_parts = [
            f"{idx}. {stop.start_time or _t('time_unknown', user_request)}",
            (stop.stop_type or 'stop').title(),
        ]
        body_parts = [f"<div class='dion-stop-meta'>{html.escape(' • '.join(meta_parts))}</div>"]
        body_parts.append(f"<div><strong>{html.escape(stop.title)}</strong></div>")
        if stop.notes:
            body_parts.append(f"<div class='dion-card-line'>{html.escape(stop.notes)}</div>")
        if stop.linked_item_name:
            body_parts.append(f"<div class='dion-card-line'>{html.escape(_t('reference', user_request))}: {html.escape(stop.linked_item_name)}</div>")
        if stop.source_url:
            body_parts.append(f"<div class='dion-links'>{_link_button(stop.source_url, 'Open source')}</div>")
        stops_html.append(f"<div class='dion-stop'>{''.join(body_parts)}</div>")

    return (
        f"<details open>"
        f"<summary>{html.escape(_format_day_label(day.day_label, user_request))}</summary>"
        f"{''.join(stops_html)}"
        f"</details>"
    )


def build_markdown_preview(markdown_report, user_request: UserRequest | None = None, max_sections: int = 3, max_chars: int = 1700) -> str:
    parts = [f"# {markdown_report.title}\n"]

    if markdown_report.recommendation and markdown_report.recommendation.sentences:
        parts.append(f"## {_t('recommendation_preview', user_request)}\n")
        for sentence in markdown_report.recommendation.sentences:
            parts.append(f"- {sentence}\n")
        parts.append("\n")

    for section in markdown_report.sections[:max_sections]:
        parts.append(f"## {section.heading}\n\n{section.body_markdown}\n\n")

    preview = ''.join(parts).strip()
    if len(preview) > max_chars:
        preview = preview[:max_chars].rstrip() + '\n\n...'
    return preview


def build_user_request(
    user_name: str,
    city: str,
    country: str,
    date_start: str,
    date_end: str,
    include_last_day: bool,
    planning_mode_label: str,
    events_enabled: bool,
    sightseeing_enabled: bool,
    food_drink_enabled: bool,
    group_size: int,
    min_budget: float | None,
    max_budget: float | None,
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
    normalized_date_start = _normalize_date_input(date_start)
    normalized_date_end = _normalize_date_input(date_end)

    payload = {
        'user': {'name': user_name.strip() or None},
        'trip': {
            'city': city.strip(),
            'country': country.strip() or None,
            'date_start': normalized_date_start,
            'date_end': normalized_date_end,
            'include_last_day': include_last_day,
            'planning_mode': PLANNING_MODE_OPTIONS[planning_mode_label],
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
    date_start: str,
    date_end: str,
    planning_mode_label: str | None,
    events_enabled: bool,
    categories: str,
    min_budget: float | None,
    max_budget: float | None,
) -> list[str]:
    errors: list[str] = []

    if not city.strip():
        errors.append('Please enter a city.')

    try:
        start = date.fromisoformat(_normalize_date_input(date_start))
        end = date.fromisoformat(_normalize_date_input(date_end))
        if end < start:
            errors.append('End date must be on or after the start date.')
    except ValueError:
        errors.append('Please use valid ISO dates in YYYY-MM-DD format.')

    if not planning_mode_label:
        errors.append('Please choose a planning mode.')

    if events_enabled and not categories.strip():
        errors.append('Please enter at least one event category or desired activity.')

    if min_budget is None and max_budget is None:
        errors.append('Please provide at least a minimum or maximum budget.')

    return errors


def _build_form_change_followup_message() -> str:
    return (
        'Revise the existing plan to match the updated planning form selections and constraints. '
        'Treat the current form values as the new baseline request and update the plan accordingly.'
    )


def _empty_results_html() -> str:
    return (
        "<div class='dion-empty'>"
        "<div class='dion-soft-label'>Awaiting Output</div>"
        "<h2>No plan generated yet</h2>"
        "<p>Define the trip, submit the planner form, and Dion will populate the result view here.</p>"
        "</div>"
    )


def _render_results_html(state: dict) -> str:
    ui_result = state.get('last_ui_result')
    user_request = state.get('last_user_request')
    markdown_report = state.get('last_markdown_report')

    if not ui_result or not user_request:
        return _empty_results_html()

    greeting_items = []
    if user_request.user.name:
        greeting_items.append(f"{_t('traveler', user_request)}: {user_request.user.name}")
    greeting_items.extend(
        [
            f"{_t('city', user_request)}: {user_request.trip.city}",
            f"{_t('dates', user_request)}: {_format_trip_date(user_request.trip.date_start)} → {_format_trip_date(user_request.trip.date_end)}",
            f"{_t('group', user_request)}: {user_request.trip.group_size}",
        ]
    )

    sections: list[str] = [
        "<div class='dion-brief'>" + ''.join(f"<span class='dion-pill'>{html.escape(item)}</span>" for item in greeting_items) + "</div>",
        (
            "<div class='dion-grid-3'>"
            f"<div class='dion-metric-card'><div class='dion-soft-label'>{html.escape(_t('events', user_request))}</div><h2>{len(ui_result.top_events)}</h2></div>"
            f"<div class='dion-metric-card'><div class='dion-soft-label'>{html.escape(_t('sightseeing', user_request))}</div><h2>{len(ui_result.sightseeing_spots)}</h2></div>"
            f"<div class='dion-metric-card'><div class='dion-soft-label'>{html.escape(_t('food_drinks', user_request))}</div><h2>{len(ui_result.food_and_drink_spots)}</h2></div>"
            "</div>"
        ),
    ]

    recommendation_lines = ''.join(f"<div class='dion-card-line'>• {html.escape(sentence)}</div>" for sentence in ui_result.recommendation.sentences)
    sections.append(f"<div class='dion-panel'><div class='dion-soft-label'>Result Block</div><h2>{html.escape(_t('recommendation_heading', user_request))}</h2>{recommendation_lines}</div>")

    grid_blocks: list[str] = []
    if user_request.trip.events_enabled:
        if ui_result.top_events:
            body = ''.join(
                _render_card(
                    event.name,
                    [
                        f"{_t('time', user_request)}: {_format_event_datetime(event.start_datetime)}",
                        f"{_t('venue', user_request)}: {event.venue_name or 'unknown'}",
                        f"{_t('price', user_request)}: {event.price_display or 'unknown'}",
                    ],
                    event.source_url,
                    getattr(event, 'ticket_url', None),
                    user_request,
                )
                for event in ui_result.top_events
            )
        else:
            body = f"<div class='dion-card-line'>{html.escape(_t('no_events_found', user_request))}</div>"
        grid_blocks.append(f"<div class='dion-panel'><div class='dion-soft-label'>Result Block</div><h2>{html.escape(_t('selected_events', user_request))}</h2>{body}</div>")

    if user_request.trip.sightseeing_enabled:
        if ui_result.sightseeing_spots:
            body = ''.join(
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
            )
        else:
            body = f"<div class='dion-card-line'>{html.escape(_t('no_sightseeing_found', user_request))}</div>"
        grid_blocks.append(f"<div class='dion-panel'><div class='dion-soft-label'>Result Block</div><h2>{html.escape(_t('city_highlights', user_request))}</h2>{body}</div>")

    if grid_blocks:
        sections.append(f"<div class='dion-grid-2'>{''.join(grid_blocks)}</div>")

    if user_request.trip.food_drink_enabled:
        body = _render_food_grid(ui_result.food_and_drink_spots, user_request) if ui_result.food_and_drink_spots else f"<div class='dion-card-line'>{html.escape(_t('no_food_found', user_request))}</div>"
        sections.append(f"<div class='dion-panel'><div class='dion-soft-label'>Result Block</div><h2>{html.escape(_t('food_drinks', user_request))}</h2>{body}</div>")

    if ui_result.itinerary_overview:
        day_blocks = ''.join(_render_day_overview(day, user_request) for day in ui_result.itinerary_overview)
        sections.append(f"<div class='dion-panel dion-days'><div class='dion-soft-label'>Result Block</div><h2>{html.escape(_t('trip_flow', user_request))}</h2>{day_blocks}</div>")
    else:
        sections.append(f"<div class='dion-panel'><div class='dion-soft-label'>Result Block</div><h2>{html.escape(_t('trip_flow', user_request))}</h2><div class='dion-card-line'>{html.escape(_t('no_itinerary', user_request))}</div></div>")

    if ui_result.warnings:
        warnings_html = ''.join(f"<div class='dion-card-line'>• {html.escape(warning)}</div>" for warning in ui_result.warnings)
        sections.append(f"<div class='dion-panel'><div class='dion-soft-label'>Result Block</div><h2>{html.escape(_t('warnings', user_request))}</h2>{warnings_html}</div>")

    if ui_result.personal_feedback:
        notes_html = ''.join(f"<div class='dion-card-line'>• {html.escape(line)}</div>" for line in ui_result.personal_feedback)
        sections.append(f"<div class='dion-panel'><div class='dion-soft-label'>Result Block</div><h2>{html.escape(_t('personal_note', user_request))}</h2>{notes_html}</div>")

    if markdown_report:
        sections.append(
            f"<div class='dion-panel'><div class='dion-soft-label'>Result Block</div><h2>{html.escape(_t('saved_report', user_request))}</h2><div class='dion-card-line'>{html.escape(state.get('saved_report_path') or 'unknown')}</div></div>"
        )

    return ''.join(sections)


def _build_display_updates(state: dict, status_message: str = '', status_tone: str = 'info'):
    user_request = state.get('last_user_request')
    status_html = _render_status(status_message, status_tone) if status_message else ''
    results_html = _render_results_html(state)
    report_preview = build_markdown_preview(state['last_markdown_report'], user_request) if state.get('last_markdown_report') else ''
    request_json = state['last_user_request'].model_dump(mode = 'json') if state.get('last_user_request') else None
    core_json = state['last_core_result'].model_dump(mode = 'json') if state.get('last_core_result') else None
    report_json = state['last_markdown_report'].model_dump(mode = 'json') if state.get('last_markdown_report') else None
    error_html = _render_status(state['last_error'], 'error') if state.get('last_error') else ''
    has_plan = state.get('last_core_result') is not None

    followup_header = (
        f"### {_t('followup', user_request)}\n{_t('followup_body', user_request)}"
        if has_plan
        else '### Output & Notes'
    )

    return (
        state,
        status_html,
        results_html,
        report_preview,
        request_json,
        core_json,
        report_json,
        error_html,
        state.get('saved_report_path'),
        gr.update(visible = has_plan),
        gr.update(visible = not has_plan),
        gr.update(visible = has_plan),
        gr.update(value = followup_header),
        gr.update(interactive = not has_plan),
        gr.update(interactive = not has_plan),
        gr.update(interactive = not has_plan),
    )


def _normalize_budget(value: float | int | None) -> float | None:
    if value in (None, 0, 0.0):
        return None
    return float(value)


def _run_sync(coro):
    return asyncio.run(coro)


def submit_planner(
    current_state: dict,
    user_name: str,
    city: str,
    country: str,
    date_start: str,
    date_end: str,
    include_last_day: bool,
    planning_mode_label: str,
    events_enabled: bool,
    sightseeing_enabled: bool,
    food_drink_enabled: bool,
    group_size: int,
    min_budget: float | None,
    max_budget: float | None,
    vibe: str,
    categories: str,
    time_pref_label: str,
    free_only_text: str,
    sightseeing_interests: str,
    sightseeing_mode: str,
    sightseeing_free_only_text: str,
    must_avoid_raw: str,
    language_label: str,
    user_notes: str,
    followup_text: str,
):
    state = dict(current_state or _default_state())
    state['last_error'] = None

    has_existing_plan = state.get('last_core_result') is not None
    progress_text = _t('revising_plan', state.get('last_user_request')) if has_existing_plan else _t('building_plan')
    yield _build_display_updates(state, progress_text, 'info')

    min_budget_value = _normalize_budget(min_budget)
    max_budget_value = _normalize_budget(max_budget)
    free_only = free_only_text == 'Yes'
    sightseeing_free_only = sightseeing_free_only_text == 'Yes'

    if not has_existing_plan:
        errors = validate_required_inputs(
            city = city,
            date_start = date_start,
            date_end = date_end,
            planning_mode_label = planning_mode_label,
            events_enabled = events_enabled,
            categories = categories,
            min_budget = min_budget_value,
            max_budget = max_budget_value,
        )
        if errors:
            state['last_error'] = '\n'.join(errors)
            yield _build_display_updates(state, '', 'info')
            return

    try:
        user_request = build_user_request(
            user_name = user_name,
            city = city,
            country = country,
            date_start = date_start,
            date_end = date_end,
            include_last_day = include_last_day,
            planning_mode_label = planning_mode_label,
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
            user_notes = '' if has_existing_plan else user_notes,
        )

        if has_existing_plan:
            existing_request = state['last_user_request']
            normalized_followup = followup_text.strip()
            request_changed = user_request.model_dump(mode = 'json') != existing_request.model_dump(mode = 'json')
            if not normalized_followup and not request_changed:
                state['last_error'] = _t('followup_or_form_required', existing_request)
                yield _build_display_updates(state, '', 'info')
                return

            result = _run_sync(
                run_followup_planner_flow(
                    original_request = user_request,
                    current_plan = state['last_core_result'],
                    followup_message = normalized_followup or _build_form_change_followup_message(),
                )
            )
            success_message = _t('plan_updated', user_request)
        else:
            result = _run_sync(run_full_planner_flow(user_request))
            success_message = _t('plan_created', user_request)

        state['last_user_request'] = user_request
        state['last_core_result'] = result['core_result']
        state['last_ui_result'] = result['ui_result']
        state['last_markdown_report'] = result['markdown_report']
        state['saved_report_path'] = result.get('saved_report_path')
        state['last_error'] = None
        yield (
            *_build_display_updates(state, success_message, 'success'),
        )
    except Exception as exc:
        traceback.print_exc()
        state['last_error'] = str(exc)
        failure_message = _t('update_failed', state.get('last_user_request')) if has_existing_plan else _t('planner_failed')
        yield _build_display_updates(state, failure_message, 'error')


def reset_planner(*_args):
    state = _default_state()
    today = date.today()
    return (
        state,
        '',
        _empty_results_html(),
        '',
        None,
        None,
        None,
        '',
        None,
        gr.update(visible = False),
        gr.update(visible = True),
        gr.update(visible = False),
        gr.update(value = '### Output & Notes'),
        gr.update(value = True, interactive = True),
        gr.update(value = True, interactive = True),
        gr.update(value = True, interactive = True),
        '',
        '',
        '',
        str(today + timedelta(days = 7)),
        str(today + timedelta(days = 9)),
        True,
        'Full Trip',
        1,
        None,
        None,
        '',
        '',
        'No preference',
        'No',
        '',
        'No preference',
        'No',
        '',
        'English',
        '',
        '',
    )


def toggle_event_visibility(enabled: bool):
    return gr.update(visible = enabled)


def toggle_sightseeing_visibility(enabled: bool):
    return gr.update(visible = enabled)


def build_app() -> gr.Blocks:
    today = date.today()

    with gr.Blocks(css = APP_CSS, title = 'Dion by BLASTIn - Gradio') as demo:
        app_state = gr.State(_default_state())

        gr.HTML(
            """
            <div class='dion-shell'>
                <div class='dion-hero'>
                    <div class='dion-kicker'>Dion by BLASTIn</div>
                    <h1>Curate a trip that feels intentional.</h1>
                    <p>Dion acts like a planner, not a search box. Define the scope, shape the mood, and let BLASTIn turn the trip into a structured evening-forward city brief.</p>
                    <div class='dion-nav'>
                        <span>Dark mode interface</span>
                        <span>Concrete venue planning</span>
                        <span>Structured trip brief</span>
                        <span>Follow-up revisions</span>
                    </div>
                </div>
            </div>
            """
        )

        with gr.Row(equal_height = False):
            with gr.Column(scale = 16, min_width = 820, elem_id = 'planner-column'):
                gr.HTML(
                    """
                    <div class='dion-panel'>
                        <div class='dion-soft-label'>Planning Scope</div>
                        <h2>Choose what Dion should include</h2>
                        <p>These controls update the request scope directly and are applied before the planning form is submitted.</p>
                    </div>
                    """
                )
                with gr.Row():
                    with gr.Column():
                        gr.HTML("<div class='dion-scope-card'><strong>Events</strong><p>Concerts, shows, nightlife events, and ticketed experiences.</p></div>")
                        events_enabled = gr.Checkbox(label = 'Include events', value = True)
                    with gr.Column():
                        gr.HTML("<div class='dion-scope-card'><strong>Sightseeing</strong><p>Landmarks, viewpoints, museums, and city highlights tailored to the trip.</p></div>")
                        sightseeing_enabled = gr.Checkbox(label = 'Include sightseeing', value = True)
                    with gr.Column():
                        gr.HTML("<div class='dion-scope-card'><strong>Food & Drinks</strong><p>Restaurants, bars, and places that support the mood of the trip.</p></div>")
                        food_drink_enabled = gr.Checkbox(label = 'Include food & drinks', value = True)

                with gr.Column(elem_classes = ['dion-input-wrap']):
                    gr.Markdown("### Plan the trip\nFill out only the parts that match the active planning scope.")
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown('### Traveler & Destination')
                            user_name = gr.Textbox(label = 'Name', placeholder = 'e.g. Adriana', max_lines = 1)
                            city = gr.Textbox(label = 'City', placeholder = 'e.g. Berlin', max_lines = 1)
                            country = gr.Textbox(label = 'Country', placeholder = 'e.g. Germany', max_lines = 1)

                            gr.Markdown('### Trip Setup')
                            with gr.Row():
                                date_start = gr.DateTime(
                                    label = 'Start date',
                                    value = str(today + timedelta(days = 7)),
                                    include_time = False,
                                    type = 'string',
                                )
                                date_end = gr.DateTime(
                                    label = 'End date',
                                    value = str(today + timedelta(days = 9)),
                                    include_time = False,
                                    type = 'string',
                                )
                            include_last_day = gr.Checkbox(label = 'Include last trip day in itinerary', value = True)
                            with gr.Row():
                                group_size = gr.Dropdown(label = 'Group size', choices = GROUP_SIZE_OPTIONS, value = 1)
                                planning_mode = gr.Dropdown(label = 'Planning mode', choices = list(PLANNING_MODE_OPTIONS.keys()), value = 'Full Trip')

                            gr.Markdown('### Budget')
                            with gr.Row():
                                min_budget = gr.Number(label = 'Minimum budget', minimum = 0, step = 10)
                                max_budget = gr.Number(label = 'Maximum budget', minimum = 0, step = 10)

                        with gr.Column():
                            with gr.Column(visible = True) as events_section:
                                gr.Markdown('### Event Direction')
                                vibe = gr.Textbox(label = 'Desired vibe', placeholder = 'e.g. elegant, energetic, underground, classical')
                                with gr.Row():
                                    time_pref = gr.Dropdown(label = 'Preferred event time', choices = list(TIME_PREF_OPTIONS.keys()), value = 'No preference')
                                    free_only = gr.Dropdown(label = 'Only free events?', choices = ['No', 'Yes'], value = 'No')
                                categories = gr.Textbox(label = 'Event categories', placeholder = 'e.g. concert, show, club, theatre')

                            with gr.Column(visible = True) as sightseeing_section:
                                gr.Markdown('### City Direction')
                                sightseeing_interests = gr.Textbox(label = 'Sightseeing interests', placeholder = 'e.g. landmarks, viewpoints, art, history')
                                with gr.Row():
                                    sightseeing_mode = gr.Dropdown(label = 'Sightseeing mode', choices = SIGHTSEEING_MODE_OPTIONS, value = 'No preference')
                                    sightseeing_free_only = gr.Dropdown(label = 'Only free sightseeing?', choices = ['No', 'Yes'], value = 'No')

                    gr.Markdown('### Constraints')
                    must_avoid_raw = gr.Textbox(label = 'Avoid list', placeholder = 'e.g. family events, museums, luxury dining')

                    followup_header = gr.Markdown('### Output & Notes')
                    with gr.Column(visible = True) as user_notes_group:
                        user_notes = gr.Textbox(
                            label = 'Short planning note',
                            placeholder = 'e.g. We want one elegant highlight and one memorable late-night venue.',
                            lines = 6,
                            max_lines = 6,
                            max_length = MAX_FREE_TEXT_CHARS,
                        )
                    with gr.Column(visible = False) as followup_group:
                        followup_text = gr.Textbox(
                            label = 'What should Dion adjust?',
                            placeholder = UI_TEXT['en']['followup_placeholder'],
                            lines = 4,
                            max_lines = 5,
                            max_length = 320,
                        )
                    language = gr.Dropdown(label = 'Output language', choices = list(LANGUAGE_OPTIONS.keys()), value = 'English')
                    submit_button = gr.Button('Build plan with Dion', variant = 'primary')
                    reset_button = gr.Button(UI_TEXT['en']['reset_button'], visible = False)

            with gr.Column(scale = 8, min_width = 420, elem_id = 'results-column'):
                status_html = gr.HTML()
                results_html = gr.HTML(_empty_results_html())
                report_file = gr.File(label = 'Report file', visible = True)
                report_preview = gr.Markdown()
                with gr.Accordion('Structured report data', open = False):
                    report_json = gr.JSON(elem_classes = ['dion-json'])
                with gr.Accordion('Structured request', open = False):
                    request_json = gr.JSON(elem_classes = ['dion-json'])
                with gr.Accordion('Structured core result', open = False):
                    core_json = gr.JSON(elem_classes = ['dion-json'])
                error_html = gr.HTML()

        events_enabled.change(toggle_event_visibility, inputs = events_enabled, outputs = events_section)
        sightseeing_enabled.change(toggle_sightseeing_visibility, inputs = sightseeing_enabled, outputs = sightseeing_section)

        submit_inputs = [
            app_state,
            user_name,
            city,
            country,
            date_start,
            date_end,
            include_last_day,
            planning_mode,
            events_enabled,
            sightseeing_enabled,
            food_drink_enabled,
            group_size,
            min_budget,
            max_budget,
            vibe,
            categories,
            time_pref,
            free_only,
            sightseeing_interests,
            sightseeing_mode,
            sightseeing_free_only,
            must_avoid_raw,
            language,
            user_notes,
            followup_text,
        ]
        submit_outputs = [
            app_state,
            status_html,
            results_html,
            report_preview,
            request_json,
            core_json,
            report_json,
            error_html,
            report_file,
            reset_button,
            user_notes_group,
            followup_group,
            followup_header,
            events_enabled,
            sightseeing_enabled,
            food_drink_enabled,
        ]
        submit_button.click(submit_planner, inputs = submit_inputs, outputs = submit_outputs)

        reset_outputs = [
            app_state,
            status_html,
            results_html,
            report_preview,
            request_json,
            core_json,
            report_json,
            error_html,
            report_file,
            reset_button,
            user_notes_group,
            followup_group,
            followup_header,
            events_enabled,
            sightseeing_enabled,
            food_drink_enabled,
            user_name,
            city,
            country,
            date_start,
            date_end,
            include_last_day,
            planning_mode,
            group_size,
            min_budget,
            max_budget,
            vibe,
            categories,
            time_pref,
            free_only,
            sightseeing_interests,
            sightseeing_mode,
            sightseeing_free_only,
            must_avoid_raw,
            language,
            user_notes,
            followup_text,
        ]
        reset_button.click(reset_planner, outputs = reset_outputs)

    return demo


if __name__ == '__main__':
    build_app().launch()

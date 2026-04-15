import re
from datetime import datetime
from typing import Optional

from src.schemas import CoreResult, UserRequest, MarkdownReport, MarkdownSection


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-') or 'report'


def make_report_filename(user_request: UserRequest, created_at_iso: str) -> str:
    city = _slugify(user_request.trip.city)
    date_start = user_request.trip.date_start
    date_end = user_request.trip.date_end
    date_span = f'{date_start}_to_{date_end}'
    created_tag = created_at_iso.replace(':', '-')
    return f'report_{created_tag}_{city}_{date_span}.md'


def _append_url_suffix(url: str | None) -> str:
    return f' | {url}' if url else ''


def _is_german_report(user_request: UserRequest) -> bool:
    return bool(
        user_request.delivery
        and getattr(user_request.delivery, 'language', None)
        and user_request.delivery.language.value == 'Deutsch'
    )


def _fmt_text(value: str | None, fallback: str = 'unknown') -> str:
    cleaned = (value or '').strip()
    return cleaned or fallback


def _format_scope_summary(user_request: UserRequest, core_result: CoreResult) -> str:
    active_parts: list[str] = []
    if user_request.trip.events_enabled:
        active_parts.append(f"{len(core_result.events)} event(s)")
    if user_request.trip.sightseeing_enabled:
        active_parts.append(f"{len(core_result.sightseeing_spots)} sightseeing spot(s)")
    if user_request.trip.food_drink_enabled:
        active_parts.append(f"{len(core_result.food_and_drink_spots)} food/drink venue(s)")
    return ', '.join(active_parts) if active_parts else 'no active planning scope'


def _build_trip_summary_lines(core_result: CoreResult, user_request: UserRequest) -> list[str]:
    lines: list[str] = []
    lines.append(
        f"- {user_request.trip.city} from {user_request.trip.date_start} to {user_request.trip.date_end} for a group of "
        f"{user_request.trip.group_size or 'unknown'}."
    )
    lines.append(f'- Included scope: {_format_scope_summary(user_request, core_result)}.')

    if user_request.trip.budget and (
        user_request.trip.budget.min_budget is not None or user_request.trip.budget.max_budget is not None
    ):
        min_budget = user_request.trip.budget.min_budget
        max_budget = user_request.trip.budget.max_budget
        if min_budget is not None and max_budget is not None:
            lines.append(f'- Budget frame: {min_budget:.0f} EUR to {max_budget:.0f} EUR.')
        elif min_budget is not None:
            lines.append(f'- Budget frame: from {min_budget:.0f} EUR.')
        elif max_budget is not None:
            lines.append(f'- Budget frame: up to {max_budget:.0f} EUR.')

    rationale_parts: list[str] = []
    if user_request.events and user_request.events.vibe:
        rationale_parts.append(f"vibe '{user_request.events.vibe}'")
    if user_request.events and user_request.events.categories:
        rationale_parts.append(f"categories '{user_request.events.categories}'")
    if user_request.events and user_request.events.time_pref:
        rationale_parts.append(f"time preference '{user_request.events.time_pref.value}'")
    if rationale_parts:
        lines.append(f"- Planning direction anchored in {', '.join(rationale_parts)}.")

    return lines


def _build_event_section(core_result: CoreResult) -> MarkdownSection:
    if not core_result.events:
        return MarkdownSection(heading = 'Events', body_markdown = 'No events found for the selected city/time window.')

    event_lines = []
    for e in core_result.events:
        dt = _fmt_text(e.start_datetime)
        area = _fmt_text(e.address_or_area)
        price = e.price.display if e.price and e.price.display else 'unknown'
        why = _fmt_text(e.description, '')
        line = f'- **{e.name}** | {dt} | {area} | {price}{_append_url_suffix(e.source_url)}'
        if why:
            line += f'\n  Fit: {why}'
        event_lines.append(line)
    return MarkdownSection(heading = 'Events', body_markdown = '\n'.join(event_lines))


def _build_sightseeing_section(core_result: CoreResult) -> MarkdownSection | None:
    if not core_result.sightseeing_spots:
        return None

    spot_lines = []
    for s in core_result.sightseeing_spots:
        fee = s.entry_fee.display if s.entry_fee and s.entry_fee.display else 'unknown'
        hours = _fmt_text(s.opening_hours)
        line = f'- **{s.name}** | entry: {fee} | hours: {hours}{_append_url_suffix(s.source_url)}'
        line += f'\n  Why it fits: {_fmt_text(s.why_visit)}'
        spot_lines.append(line)
    return MarkdownSection(heading = 'Sightseeing / City Spots', body_markdown = '\n'.join(spot_lines))


def _build_food_section(core_result: CoreResult) -> MarkdownSection | None:
    if not core_result.food_and_drink_spots:
        return None

    venue_lines = []
    for place in core_result.food_and_drink_spots:
        area = _fmt_text(place.area_or_district)
        price = _fmt_text(place.price_hint)
        hours = _fmt_text(place.opening_hours)
        line = (
            f'- **{place.name}** ({place.venue_type}) | {area} | price: {price} | hours: {hours}'
            f'{_append_url_suffix(place.source_url)}'
        )
        line += f'\n  Why it fits: {_fmt_text(place.why_match)}'
        venue_lines.append(line)
    return MarkdownSection(heading = 'Food & Drinks', body_markdown = '\n'.join(venue_lines))


def _build_tradeoff_section(core_result: CoreResult, user_request: UserRequest) -> MarkdownSection | None:
    lines: list[str] = []

    if user_request.events and user_request.events.free_only:
        lines.append('- Event selection stayed within the free-only constraint.')
    if user_request.sightseeing and user_request.sightseeing.free_only:
        lines.append('- Sightseeing selection stayed within the free-only constraint.')
    if not core_result.events and user_request.trip.events_enabled:
        lines.append('- No strong event match was kept, which suggests the plan favored relevance over filler recommendations.')
    if core_result.warnings:
        lines.append('- Some details remained partially uncertain; see the warnings section for transparency on missing or unconfirmed information.')

    if not lines:
        return None

    return MarkdownSection(heading = 'Budget Fit & Tradeoffs', body_markdown = '\n'.join(lines))


def _build_itinerary_section(core_result: CoreResult) -> MarkdownSection | None:
    if not core_result.itinerary:
        return None

    day_blocks = []
    for day in core_result.itinerary:
        stop_types = [stop.stop_type for stop in day.stops]
        if 'event' in stop_types and 'food' in stop_types:
            flow = 'This day combines a concrete main event with a food/drink stop to give the schedule a clear evening arc.'
        elif 'event' in stop_types:
            flow = 'This day is built around a clear event anchor, with surrounding stops kept lighter.'
        elif 'sightseeing' in stop_types and 'food' in stop_types:
            flow = 'This day leans more city-focused, pairing sightseeing with a food/drink stop for a complete but lighter flow.'
        elif 'sightseeing' in stop_types:
            flow = 'This day stays mostly focused on city exploration.'
        else:
            flow = 'This day remains intentionally light and flexible.'

        day_blocks.append(f'### {day.day_label}')
        day_blocks.append(flow)
        day_blocks.append('')
        for stop in day.stops:
            t = stop.start_time or 'unknown'
            ref = f' | ref: {stop.linked_item_name}' if stop.linked_item_name else ''
            note = f' — {stop.notes}' if stop.notes else ''
            day_blocks.append(f'- **{t}** — {stop.title} ({stop.stop_type}){ref}{note}')
        day_blocks.append('')

    return MarkdownSection(
        heading = 'Itinerary (Day-by-Day)',
        body_markdown = '\n'.join(day_blocks).strip(),
    )


def _build_personal_note_section(core_result: CoreResult) -> MarkdownSection | None:
    if not core_result.personal_feedback:
        return None

    lines = [f'- {line}' for line in core_result.personal_feedback]
    return MarkdownSection(heading = "Dion's Personal Note", body_markdown = '\n'.join(lines))


def append_missing_link_note_section(
    markdown_report: MarkdownReport,
    core_result: CoreResult,
    user_request: UserRequest,
) -> MarkdownReport:
    missing_sightseeing = [spot.name for spot in core_result.sightseeing_spots if not spot.source_url]
    missing_food = [place.name for place in core_result.food_and_drink_spots if not place.source_url]

    if not missing_sightseeing and not missing_food:
        return markdown_report

    existing_headings = {section.heading.strip().casefold() for section in markdown_report.sections}
    german = _is_german_report(user_request)
    heading = 'Link-Hinweis' if german else 'Link Availability'
    if heading.casefold() in existing_headings:
        return markdown_report

    lines: list[str] = []
    if german:
        lines.append('- Einige Orte bleiben im Plan enthalten, auch wenn kein verifizierter öffentlicher Link bestätigt werden konnte.')
        if missing_sightseeing:
            lines.append(f"- Sightseeing ohne verifizierten Link: {', '.join(missing_sightseeing)}.")
        if missing_food:
            lines.append(f"- Essen & Drinks ohne verifizierten Link: {', '.join(missing_food)}.")
    else:
        lines.append('- Some places remain in the plan even though no verified public link could be confirmed.')
        if missing_sightseeing:
            lines.append(f"- Sightseeing without a verified link: {', '.join(missing_sightseeing)}.")
        if missing_food:
            lines.append(f"- Food/drink venues without a verified link: {', '.join(missing_food)}.")

    markdown_report.sections.append(
        MarkdownSection(
            heading = heading,
            body_markdown = '\n'.join(lines),
        )
    )
    return markdown_report


def core_result_to_markdown_report(
    core_result: CoreResult,
    user_request: UserRequest,
    created_at_iso: Optional[str] = None
) -> MarkdownReport:
    if created_at_iso is None:
        created_at_iso = datetime.now().isoformat(timespec = 'seconds')

    title = f"Dion's BlastIn Plan for {user_request.trip.city} ({user_request.trip.date_start} to {user_request.trip.date_end})"
    sections: list[MarkdownSection] = []

    rec_lines = [f'- {s}' for s in core_result.recommendation.sentences]
    sections.append(
        MarkdownSection(
            heading = "Dion's Recommendation",
            body_markdown = '\n'.join(rec_lines) if rec_lines else '- (no recommendation provided)'
        )
    )

    sections.append(
        MarkdownSection(
            heading = 'Trip Framing',
            body_markdown = '\n'.join(_build_trip_summary_lines(core_result, user_request)),
        )
    )

    sections.append(_build_event_section(core_result))

    sightseeing_section = _build_sightseeing_section(core_result)
    if sightseeing_section:
        sections.append(sightseeing_section)

    food_section = _build_food_section(core_result)
    if food_section:
        sections.append(food_section)

    tradeoff_section = _build_tradeoff_section(core_result, user_request)
    if tradeoff_section:
        sections.append(tradeoff_section)

    itinerary_section = _build_itinerary_section(core_result)
    if itinerary_section:
        sections.append(itinerary_section)

    if core_result.warnings:
        warn_lines = [f'- {w}' for w in core_result.warnings]
        sections.append(MarkdownSection(heading = 'Warnings / Missing Info', body_markdown = '\n'.join(warn_lines)))

    personal_note_section = _build_personal_note_section(core_result)
    if personal_note_section:
        sections.append(personal_note_section)

    return MarkdownReport(
        title = title,
        recommendation = core_result.recommendation,
        sections = sections,
        sources = core_result.sources,
        created_at = created_at_iso
    )


def render_markdown(report: MarkdownReport) -> str:
    lines = []
    lines.append(f'# {report.title}')
    if report.created_at:
        lines.append(f'*Created at:* `{report.created_at}`')
    lines.append('')

    for section in report.sections:
        lines.append(f'## {section.heading}')
        lines.append(section.body_markdown.strip())
        lines.append('')

    if report.sources:
        lines.append('## Sources')
        for src in report.sources:
            if not src.url:
                continue
            label = src.label or 'source'
            lines.append(f'- {label}: {src.url}')
        lines.append('')

    return '\n'.join(lines).strip()


async def save_report_markdown(
    fs_server,
    reports_dir: str,
    filename: str,
    markdown: str
) -> str:
    full_path = f'{reports_dir}/{filename}'.replace('\\', '/')

    await fs_server.call_tool(
        tool_name = 'write_file',
        arguments = {
            'path': full_path,
            'content': markdown
        }
    )

    return full_path

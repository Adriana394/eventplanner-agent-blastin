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

def core_result_to_markdown_report(
    core_result: CoreResult,
    user_request: UserRequest,
    created_at_iso: Optional[str] = None
) -> MarkdownReport:
    if created_at_iso is None:
        created_at_iso = datetime.now().isoformat(timespec = 'seconds')
        
    title = f"Dion's BlastIn Plan for {user_request.trip.city} ({user_request.trip.date_start} to {user_request.trip.date_end})"
    
    sections: list[MarkdownSection] = []
    
    # Recommendation
    rec_lines = [f'- {s}' for s in core_result.recommendation.sentences]
    sections.append(
        MarkdownSection(
            heading = "Dion's Recommendation",
            body_markdown = '\n'.join(rec_lines) if rec_lines else '- (no recommendation provided)'
        )
    )

    # Events (EventItem fields: name, start_datetime, address_or_area, price(Money), description, category_tags, source_url)
    if core_result.events:
        event_lines = []
        for e in core_result.events:
            dt = e.start_datetime or 'unknown'
            area = e.address_or_area or 'unknown'
            price = (e.price.display if e.price and e.price.display else 'unknown')
            url = e.source_url or 'unknown'
            event_lines.append(f'- **{e.name}** | {dt} | {area} | {price} | {url}')
        sections.append(MarkdownSection(heading = 'Events', body_markdown = '\n'.join(event_lines)))
    else:
        sections.append(MarkdownSection(heading = 'Events', body_markdown = 'No events found for the selected city/time window.'))

    # Sightseeing spots (SightseeingSpot fields: name, area_or_district, address, entry_fee(Money), opening_hours, why_visit, source_url)
    if core_result.sightseeing_spots:
        spot_lines = []
        for s in core_result.sightseeing_spots:
            fee = (s.entry_fee.display if s.entry_fee and s.entry_fee.display else 'unknown')
            hours = s.opening_hours or 'unknown'
            url = s.source_url or 'unknown'
            spot_lines.append(f'- **{s.name}** | entry: {fee} | hours: {hours} | {url}')
        sections.append(MarkdownSection(heading = 'Sightseeing / City Spots', body_markdown = '\n'.join(spot_lines)))

    if core_result.food_and_drink_spots:
        venue_lines = []
        for place in core_result.food_and_drink_spots:
            area = place.area_or_district or 'unknown'
            price = place.price_hint or 'unknown'
            hours = place.opening_hours or 'unknown'
            url = place.source_url or 'unknown'
            venue_lines.append(
                f'- **{place.name}** ({place.venue_type}) | {area} | price: {price} | hours: {hours} | {url}'
            )
        sections.append(MarkdownSection(heading = 'Food & Drinks', body_markdown = '\n'.join(venue_lines)))

    # Itinerary (ItineraryDay.stops, ItineraryStop fields: stop_type, title, start_time, duration_minutes, notes)
    if core_result.itinerary:
        day_blocks = []
        for day in core_result.itinerary:
            day_blocks.append(f'### {day.day_label}')
            for stop in day.stops:
                t = stop.start_time or 'unknown'
                note = f' — {stop.notes}' if stop.notes else ''
                ref = f' | ref: {stop.linked_item_name}' if stop.linked_item_name else ''
                day_blocks.append(f'- **{t}** — {stop.title} ({stop.stop_type}){ref}{note}')
            day_blocks.append('')
        sections.append(
            MarkdownSection(
                heading = 'Itinerary (Day-by-Day)',
                body_markdown = '\n'.join(day_blocks).strip()
            )
        )

    # Warnings
    if core_result.warnings:
        warn_lines = [f'- {w}' for w in core_result.warnings]
        sections.append(MarkdownSection(heading = 'Warnings / Missing Info', body_markdown = '\n'.join(warn_lines)))

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

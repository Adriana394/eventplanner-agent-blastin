# Current Status

This file replaces the older `NEXT_STEPS.md` and captures the current state of the project after the latest reliability and validation work.

## Project Summary

`eventplanner-agent` is an agent-driven city trip and event planner with three core stages:

1. `Dion_Planner` creates a structured `CoreResult`
2. `Dion_Validator` checks the result for consistency and sends repair findings back when needed
3. `Dion_Reporter` turns the validated result into a markdown report and saves it

The project now has two UI variants for comparison:

- Streamlit in [src/dion_ui.py](/home/adri/projects/eventplanner-agent/src/dion_ui.py:1)
- Gradio in [src/dion_gradio_ui.py](/home/adri/projects/eventplanner-agent/src/dion_gradio_ui.py:1)

The orchestration and business logic still live in [src/event_client.py](/home/adri/projects/eventplanner-agent/src/event_client.py:1).

## What Is Implemented

- OpenRouter integration is implemented in [src/event_client.py](/home/adri/projects/eventplanner-agent/src/event_client.py:1)
- Provider switching happens via `.env`, not the UI
- Separate planner, reporter, and validator model selection is supported
- Default OpenRouter validator model is `openai/gpt-oss-120b:free`
- A second Gradio UI was added without removing the Streamlit UI
- The Gradio UI now includes:
  - the same overall BLASTIn-style visual direction
  - follow-up and reset flows
  - calendar-based date inputs
  - more spacious form layout for side-by-side UI comparison
- The trip form now supports `include_last_day`
- The Streamlit date selection now uses a date-range picker for start/end selection
- The Streamlit flow now rerenders into follow-up mode immediately after a successful first run
- Follow-up UX now explains that current form filters remain active unless the user changes them
- Generic itinerary placeholders are filtered before UI/report output
- Sightseeing and food/drink places are no longer dropped only because their public URL cannot be confirmed
- UI cards and itinerary stops now show a short note instead of a broken link button when no verified public link is available
- Markdown reports now include a short link-availability note when places remain in the plan without a verified public link
- A validator-driven repair loop now checks:
  - disabled scopes
  - `free_only` constraints
  - `must_avoid`
  - itinerary references
  - itinerary date range and day handling
  - overlapping event stops in one itinerary day
  - weak middle-day planning that starts only late in the day
  - recommendation-vs-result mismatches
- Event links are now normalized to public-facing URLs when possible
- Itinerary stop URLs are now resynced against the final verified event/place URLs
- Internal warning output is now deduplicated and no longer treats intentionally cleared `source_url = null` values as malformed by default
- The markdown report is more presentation-oriented with trip framing, fit explanations, day flow, and tradeoff notes

## Current Quality Direction

The system is now much stronger on correctness and internal consistency than earlier iterations. The main architectural direction is:

- preserve the agentic workflow
- use deterministic checks for hard constraints
- use a validator agent for semantic inconsistencies
- repair through agent feedback instead of silently rewriting outputs

## Remaining Priority Areas

### Demo Readiness

- run the planned demo cases in [DEMO_CASES.md](/home/adri/projects/eventplanner-agent/DEMO_CASES.md:1)
- identify which scenarios are stable enough for a live presentation
- record concrete failures instead of generic impressions
- compare Streamlit vs. Gradio on the same demo cases before choosing a presentation UI
- verify that the remaining itinerary stop type edge case does not recur in additional demos

### Product Polish

- verify that the Streamlit UI feels presentation-ready under realistic runs
- test the follow-up flow more aggressively
- confirm that the improved report quality holds across multiple cities and request styles
- keep [issues.md](/home/adri/projects/eventplanner-agent/issues.md:1) limited to truly unresolved findings

### Future Product Work

- optional PDF export/download
- optional frontend migration later, only after the current system is stable
- broader model comparison through OpenRouter when useful

## Working Principle

- first correctness
- then consistency
- then presentation quality
- then product expansion

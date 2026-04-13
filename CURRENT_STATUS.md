# Current Status

This file replaces the older `NEXT_STEPS.md` and captures the current state of the project after the latest reliability and validation work.

## Project Summary

`eventplanner-agent` is an agent-driven city trip and event planner with three core stages:

1. `Dion_Planner` creates a structured `CoreResult`
2. `Dion_Validator` checks the result for consistency and sends repair findings back when needed
3. `Dion_Reporter` turns the validated result into a markdown report and saves it

The current UI remains Streamlit-based in [src/dion_ui.py](/home/adri/projects/eventplanner-agent/src/dion_ui.py:1), while orchestration and business logic live in [src/event_client.py](/home/adri/projects/eventplanner-agent/src/event_client.py:1).

## What Is Implemented

- OpenRouter integration is implemented in [src/event_client.py](/home/adri/projects/eventplanner-agent/src/event_client.py:1)
- Provider switching happens via `.env`, not the UI
- Separate planner, reporter, and validator model selection is supported
- Default OpenRouter validator model is `openai/gpt-oss-120b:free`
- The trip form now supports `include_last_day`
- Generic itinerary placeholders are filtered before UI/report output
- Food/drink venues are no longer dropped only because their URL cannot be confirmed
- A validator-driven repair loop now checks:
  - disabled scopes
  - `free_only` constraints
  - `must_avoid`
  - itinerary references
  - itinerary date range and day handling
  - recommendation-vs-result mismatches
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

### Product Polish

- verify that the Streamlit UI feels presentation-ready under realistic runs
- test the follow-up flow more aggressively
- confirm that the improved report quality holds across multiple cities and request styles

### Future Product Work

- optional PDF export/download
- optional frontend migration later, only after the current system is stable
- broader model comparison through OpenRouter when useful

## Working Principle

- first correctness
- then consistency
- then presentation quality
- then product expansion

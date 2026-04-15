# eventplanner-agent

`eventplanner-agent` is an agent-driven event and city-trip planner built around structured schemas, MCP tools, and a multi-step validation flow.

The project currently uses a Streamlit frontend in [src/dion_ui.py](/home/adri/projects/eventplanner-agent/src/dion_ui.py:1), while the core logic lives in Python orchestration code under [src/event_client.py](/home/adri/projects/eventplanner-agent/src/event_client.py:1).

## What It Does

The runtime flow is:

1. Build a structured `UserRequest`
2. Run `Dion_Planner` to create a `CoreResult`
3. Run deterministic validation plus `Dion_Validator`
4. Repair the plan through agent feedback when issues are found
5. Convert the validated result into UI output
6. Run `Dion_Reporter` to generate and save a markdown report

The planner can combine:

- events
- sightseeing
- food & drinks
- day-by-day itinerary planning
- follow-up revisions of an existing plan

## Key Features

- OpenAI and OpenRouter model provider support via `.env`
- separate planner, reporter, and validator model selection
- Eventim-backed event enrichment
- DZT-backed place discovery
- validator-driven repair loop instead of silent post-processing only
- final-day itinerary control through `include_last_day`
- browser-validated place-link handling that keeps places even when public links cannot be confirmed
- itinerary/source-url resync so final verified link state also propagates into itinerary stops
- follow-up revisions from the same planning form, with current filters kept as active constraints
- markdown report generation with trip framing, rationale, and tradeoff notes

## Main Files

- [src/dion_ui.py](/home/adri/projects/eventplanner-agent/src/dion_ui.py:1): current Streamlit UI
- [src/event_client.py](/home/adri/projects/eventplanner-agent/src/event_client.py:1): orchestration, validation loop, agent runs
- [src/schemas.py](/home/adri/projects/eventplanner-agent/src/schemas.py:1): shared request/result contracts
- [src/instructions.py](/home/adri/projects/eventplanner-agent/src/instructions.py:1): planner, validator, and reporter instructions
- [src/reporting.py](/home/adri/projects/eventplanner-agent/src/reporting.py:1): markdown report construction and persistence helpers
- [mcp_servers/mcp_servers.py](/home/adri/projects/eventplanner-agent/mcp_servers/mcp_servers.py:1): MCP server configuration and lifecycle
- [CURRENT_STATUS.md](/home/adri/projects/eventplanner-agent/CURRENT_STATUS.md:1): current implementation state
- [DEMO_CASES.md](/home/adri/projects/eventplanner-agent/DEMO_CASES.md:1): planned demo and regression scenarios

## Configuration

Model/provider selection is controlled through environment variables.

Current relevant keys include:

- `MODEL_PROVIDER`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENAI_PLANNER_MODEL`
- `OPENAI_REPORTER_MODEL`
- `OPENAI_VALIDATOR_MODEL`
- `OPENROUTER_PLANNER_MODEL`
- `OPENROUTER_REPORTER_MODEL`
- `OPENROUTER_VALIDATOR_MODEL`
- `CITY_URL`
- `EVENT_URL`
- `REPORTS_DIR`

For OpenRouter, the validator currently defaults to `openai/gpt-oss-120b:free` unless overridden.

## Running The App

The project is managed with `uv`.

Example local run:

```bash
uv run streamlit run src/dion_ui.py
```

The app is typically available at `http://localhost:8501`.

For the additional Gradio variant:

```bash
uv run python src/dion_gradio_ui.py
```

This launches a second UI implementation for side-by-side comparison without removing or replacing the Streamlit app.

## Current Focus

The current focus is demo readiness, not a frontend rewrite. The system has recently been improved around:

- itinerary correctness
- removal of generic filler stops
- recommendation/data consistency
- sightseeing and food/drink source handling
- follow-up usability in Streamlit
- markdown report messaging for places without verified public links
- validator-driven repair
- stronger report quality

The currently tracked open issue list lives in [issues.md](/home/adri/projects/eventplanner-agent/issues.md:1).

Use [CURRENT_STATUS.md](/home/adri/projects/eventplanner-agent/CURRENT_STATUS.md:1) for the latest status and [DEMO_CASES.md](/home/adri/projects/eventplanner-agent/DEMO_CASES.md:1) for the planned presentation scenarios.

# EventPlanner Agent Code Review

## Purpose

This document explains the current architecture of `eventplanner-agent` for someone who did not build it. It focuses on the runtime flow, the important files, and the contracts between UI, orchestration, validation, reporting, and MCP tools.

## High-Level Summary

The project is an agent-driven event and city-trip planner with a validation-and-repair loop.

At a high level it does six things:

1. accepts a structured planning request
2. runs a planner agent with MCP tools
3. validates the result with deterministic checks plus a validator agent
4. repairs the plan through targeted agent feedback when needed
5. converts the validated result into a UI-facing shape
6. produces and saves a markdown report

The architecture is centered around:

- Pydantic schemas in `src/schemas.py`
- orchestration in `src/event_client.py`
- behavior control in `src/instructions.py`
- report shaping in `src/reporting.py`
- MCP infrastructure in `mcp_servers/`

## Top-Level Structure

- `src/`
  Main application logic, UI, schemas, instructions, orchestration, and reporting.
- `mcp_servers/`
  MCP server configuration plus the custom Eventim and DZT-facing servers.
- `outputs/reports/`
  Default runtime output directory for markdown reports.
- `main.py`
  Placeholder entry point, not the main application runtime.
- `pyproject.toml`
  Project metadata and dependencies.
- `README.md`
  Current project overview and run instructions.
- `CURRENT_STATUS.md`
  Current implementation state.
- `DEMO_CASES.md`
  Planned demo and regression scenarios.

## End-to-End Runtime Flow

The main runtime path lives in `src/event_client.py`.

1. The UI builds a `UserRequest`.
2. `build_planner_input_text()` serializes that request for `Dion_Planner`.
3. MCP servers are started through `get_server_config()` and `bundle_servers()`.
4. `Dion_Planner` runs with Playwright, Filesystem, Eventim, and DZT access.
5. The planner returns a `CoreResult`.
6. Python applies post-processing:
   - authoritative Eventim enrichment
   - generic itinerary placeholder cleanup
   - event/place URL normalization
   - place-link verification with keep-the-place/remove-the-link behavior
   - itinerary stop link resync against the final verified item URLs
7. Deterministic validation runs for scope, constraints, itinerary references, date logic, and selected recommendation mismatches.
8. `Dion_Validator` adds semantic validation findings.
9. If issues exist, `Dion_Planner` receives a repair prompt containing the validation findings and returns a revised `CoreResult`.
10. The validated result is converted into `UIResult`.
11. `Dion_Reporter` turns the result into `MarkdownReport` and saves it through the Filesystem MCP.
12. The saved path is normalized and checked to remain inside the allowed reports directory.

This split is important:

- planning is agentic
- validation is both deterministic and agentic
- reporting is separated from planning

## Important Files In `src/`

### `src/schemas.py`

This is the shared contract layer.

It defines:

- request models such as `UserRequest`, `TripRequest`, `EventPreferences`, `SightseeingPreferences`
- result models such as `CoreResult`, `UIResult`, `MarkdownReport`, `ReporterResult`
- validator result models `ValidationIssue` and `ValidationResult`

Notable current points:

- `TripRequest` includes `include_last_day`
- `SightseeingSpot.source_url` is now optional
- `FoodDrinkSpot.source_url` is now optional
- `UISpotItem.source_url` is now optional
- result sizes are guarded through validators

Why it matters:

- all agent outputs are constrained through these schemas
- the UI, planner, validator, and reporter all depend on this file

### `src/event_client.py`

This is the application service layer and the most important runtime file.

Current responsibilities:

- model/provider selection for OpenAI and OpenRouter
- prompt construction for planner, validator, reporter, and repair runs
- MCP server startup and shutdown
- planner execution
- authoritative event syncing from backend services
- itinerary placeholder cleanup
- event/place source URL normalization and verification
- itinerary stop source URL resync after final verification
- deterministic validation
- validator-agent execution
- planner repair loop
- UI result shaping
- report generation and persistence

Important current concepts:

- OpenRouter validator default is `openai/gpt-oss-120b:free`
- the validator loop preserves the agentic workflow instead of silently rewriting everything in Python
- hard constraints are checked in code before and alongside semantic LLM validation

### `src/instructions.py`

This file contains the system instructions for:

- `Dion_Planner`
- `Dion_Reporter`
- `Dion_Validator`

Why it matters:

- much of the product behavior is controlled here, not only in Python
- it encodes source priorities, scope rules, date handling, URL handling, and report expectations

Recent important changes:

- explicit `include_last_day` handling
- non-Eventim sightseeing and food/drink links are validated, but places are kept even when their public link cannot be confirmed
- stronger report-quality rules
- validation-only instructions for the third agent

### `src/reporting.py`

This file shapes the markdown report from structured data.

Current responsibilities:

- trip framing summary
- events, sightseeing, and food/drink sections with fit explanations
- budget/tradeoff section when supported by available data
- more readable day-by-day narrative framing
- explicit markdown note when places remain in the plan without a verified public link
- markdown rendering and report persistence helpers

Architectural note:

The reporter agent still exists, but this file remains the code-level report representation and persistence helper.

### `src/dion_ui.py`

This is the current Streamlit frontend.

Main responsibilities:

- collects user input and scope settings
- builds `UserRequest`
- triggers full-plan and follow-up flows
- stores state in Streamlit session state
- renders recommendation, results, itinerary, warnings, and markdown preview

Important current UI detail:

- the form now includes `Include final trip day`
- travel dates are selected through a single date-range picker
- after a successful run, the same form rerenders into follow-up mode instead of requiring a reset
- items without verified place links show a small explanatory note instead of a broken link button

## Important Files In `mcp_servers/`

### `mcp_servers/mcp_servers.py`

This file centralizes MCP server configuration and lifecycle management.

Why it matters:

- it defines which MCP tools are available to the agents
- it passes the allowed reports directory into the Filesystem MCP
- it owns async startup and shutdown of the server bundle

### `mcp_servers/event_server.py`

This is the custom Eventim-facing MCP server.

Main responsibilities:

- resolve supported cities
- fetch events for a city/date range
- normalize time handling between UTC and Europe/Berlin
- cache backend responses

This is the main structured event source behind the planner.

### `mcp_servers/dzt_server.py`

This server provides structured place discovery for:

- sightseeing
- restaurants
- bars
- cafes
- other place-based recommendations

It is the main structured place source behind sightseeing and food/drink planning.

## Current Architectural Strengths

- clear schema contracts
- separation of planning, validation, and reporting
- explicit support for iterative follow-up changes
- better reliability through deterministic checks plus validator-agent review
- improved transparency through warnings instead of silent data loss
- clearer handling of missing public place links across UI, itinerary, and markdown report

## Current Risks Or Watch Areas

- final quality still depends on real-world model behavior and tool output quality
- demo readiness now depends on testing stable request scenarios, not only code quality
- the Streamlit UI is serviceable for demos, but not a deployable product frontend
- report quality is improved, but should still be checked on real cases before presentation
- one open issue remains: an itinerary stop can still receive the wrong `stop_type` from planner/repair output in edge cases

## Recommended Reading Order

If someone new joins the project, the best reading order is:

1. `README.md`
2. `CURRENT_STATUS.md`
3. `DEMO_CASES.md`
4. `src/schemas.py`
5. `src/event_client.py`
6. `src/instructions.py`
7. `src/dion_ui.py`
8. `mcp_servers/mcp_servers.py`

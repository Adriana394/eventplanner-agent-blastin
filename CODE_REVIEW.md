# EventPlanner Agent Code Review

## Purpose of This Document

This review is written for someone who did not build the project. It explains how the codebase is organized, how the main runtime flow works, which files matter most in `src/` and `mcp_servers/`, and which schemas act as the contract between the UI, the planner agent, the reporter agent, and the MCP tools.

`src/ui_app.py` is intentionally not covered here.

## High-Level Summary

This project is an agent-driven event and trip planner. At a high level it does four things:

1. Accepts a structured user request.
2. Uses MCP-backed tools to gather event and sightseeing data.
3. Produces a validated planning result as structured Pydantic output.
4. Produces and saves a Markdown report derived from that result.

The architecture is centered around three ideas:

- Pydantic schemas in `src/schemas.py` define the input and output contracts.
- `src/event_client.py` orchestrates the planner and reporter agents.
- `mcp_servers/` contains the tool servers the agents rely on for events, sightseeing, browser automation, and file output.

## Top-Level Project Structure

### Runtime-relevant files

- `main.py`
  - Minimal placeholder entry point. It currently does not drive the real application flow.
- `src/`
  - Main application logic, schemas, instructions, and reporting helpers.
- `mcp_servers/`
  - Custom MCP servers plus MCP server bootstrap/configuration utilities.
- `outputs/reports/`
  - Default report output directory created at runtime.
- `pyproject.toml`
  - Python project metadata and dependencies, including `openai-agents`, `mcp`, `httpx`, and `pydantic`.

## End-to-End Runtime Flow

The main runtime path lives in `src/event_client.py`.

1. A `UserRequest` object is created upstream and passed into the planner flow.
2. `build_planner_input_text()` converts that structured request into a prompt payload for the planning agent.
3. `get_server_config()` and `bundle_servers()` start all required MCP servers.
4. The planner agent runs with access to Playwright, Filesystem, Eventim, and DZT MCP servers.
5. The planner returns a validated `CoreResult`.
6. `core_to_ui()` transforms that detailed result into a smaller `UIResult`.
7. A reporter job is assembled from the original request and planner output.
8. A second agent turns that data into a `ReporterResult`, which includes a `MarkdownReport` and saved file path.
9. The saved path is validated to ensure it stays inside the allowed reports directory.

This separation is important: planning and reporting are treated as different responsibilities, with different instructions and different allowed tools.

## Important Files in `src/`

### `src/schemas.py`

This is the most important file in the project from a contract perspective. It defines both the structured input expected from the UI layer and the structured outputs expected from the agents.

Key responsibilities:

- Defines enums and input models for trip planning.
- Defines output models for events, sightseeing, itineraries, reports, and UI summaries.
- Uses Pydantic validators to enforce basic business rules and guardrails.

Important schema groups:

- Input/request schemas:
  - `PlanningMode`, `TimePreferences`, `Language`
  - `UserProfile`
  - `Budget`
  - `TripRequest`
  - `EventPreferences`
  - `SightseeingPreferences`
  - `ItineraryPreferences`
  - `DeliveryOption`
  - `UserRequest`

- Output/result schemas:
  - `Money`
  - `Source`
  - `EventItem`
  - `SightseeingSpot`
  - `ItineraryStop`
  - `ItineraryDay`
  - `Recommendation`
  - `CoreResult`
  - `MarkdownSection`
  - `MarkdownReport`
  - `ReporterResult`
  - `UIEventTeaser`
  - `UISpotItem`
  - `UIItineraryStop`
  - `UIDayOverview`
  - `UIResult`

Why it matters:

- The planner agent is constrained to return `CoreResult`.
- The reporter agent is constrained to return `ReporterResult`.
- The UI-facing layer depends on `UIResult`.
- The file acts as the shared language of the whole system.

Important validations:

- `Budget.validate_min_max()` ensures min budget does not exceed max budget.
- `TripRequest.validate_date()` ensures `date_end >= date_start`.
- `DeliveryOption.validate_email()` requires an email if `send_email` is true.
- `ItineraryDay.validate_max_5_sightseeing()` caps sightseeing stops per day at 5.
- `Recommendation.validate_max_5()` caps recommendation sentences at 5.
- `CoreResult.validate_max_5_events()` caps total recommended events at 5.
- `UIResult.validate_max_3_top_events()` caps UI teaser events at 3.

Best schema entry points for a new reader:

- `UserRequest` in `src/schemas.py:111`
- `CoreResult` in `src/schemas.py:193`
- `MarkdownReport` in `src/schemas.py:216`
- `UIResult` in `src/schemas.py:259`

### `src/event_client.py`

This is the orchestration layer of the application. It wires together schemas, agent instructions, MCP servers, and output conversion.

Main responsibilities:

- Builds planner and reporter prompts from structured inputs.
- Starts MCP servers using the shared server bundle.
- Creates and runs the planner and reporter agents.
- Converts full planner output into a smaller UI-friendly shape.
- Enforces the saved report path constraint.

Important functions:

- `build_planner_input_text()` in `src/event_client.py:36`
  - Serializes `UserRequest` into a prompt string for the planner agent.
- `build_followup_planner_input_text()` in `src/event_client.py:46`
  - Reuses the original request plus current plan for iterative revisions.
- `build_reporter_input_text()` in `src/event_client.py:67`
  - Builds the reporter job prompt and makes the file-save requirement explicit.
- `core_to_ui()` in `src/event_client.py:85`
  - Downsamples `CoreResult` into `UIResult`, especially by limiting events to the top 3.
- `run_full_planner_flow()` in `src/event_client.py:137`
  - Main end-to-end planner flow for a new request.
- `run_followup_planner_flow()` in `src/event_client.py:199`
  - Similar flow for plan revisions after a follow-up request.

Architectural note:

This file is effectively the application service layer. If someone wants to understand "what happens when a user submits a planning request," this is the first code file to read after `src/schemas.py`.

### `src/instructions.py`

This file stores the system prompts for the two agents.

Important contents:

- `SYSTEM_INSTRUCTIONS_PLANNER`
  - Defines the planner agent's role, allowed scope, tool rules, budget handling, safety behavior, date/time expectations, and output contract.
- `SYSTEM_INSTRUCTIONS_REPORTER`
  - Defines the reporter agent's narrower role: transform existing planning data into `MarkdownReport`, save it, and return `ReporterResult`.

Why it matters:

- This file is the behavioral control layer of the app.
- A large part of the product logic is prompt-defined, not only code-defined.
- It explains why the planner uses Eventim as the primary event source and DZT for sightseeing/outdoor data.

### `src/reporting.py`

This file contains a local Python implementation for report generation and persistence, independent of the reporter agent prompt.

Important functions:

- `_slugify()` in `src/reporting.py:8`
  - Converts city or text fragments into filename-safe slugs.
- `make_report_filename()` in `src/reporting.py:14`
  - Builds a deterministic report filename from request data and timestamp.
- `core_result_to_markdown_report()` in `src/reporting.py:22`
  - Converts `CoreResult` and `UserRequest` into a structured `MarkdownReport`.
- `render_markdown()` in `src/reporting.py:97`
  - Renders `MarkdownReport` into raw Markdown text.
- `save_report_markdown()` in `src/reporting.py:119`
  - Saves the rendered Markdown through the Filesystem MCP server.

Architectural note:

This file overlaps conceptually with the reporter agent. That is not necessarily wrong, but it does mean there are two reporting strategies in the repository:

- prompt-driven reporting via `Dion_Reporter` in `src/event_client.py`
- code-driven reporting helpers in `src/reporting.py`

That is worth keeping in mind when maintaining or extending the report flow.

### `src/__init__.py`

Package marker only. No logic.

## Important Files in `mcp_servers/`

### `mcp_servers/mcp_servers.py`

This file centralizes MCP server configuration and lifecycle management.

Important responsibilities:

- Defines `ServerConfig`, the immutable config object for each MCP server.
- Declares which servers are used by the app in `get_server_config()`.
- Starts and stops all configured servers through `MCPServerBundle`.

Important functions and classes:

- `ServerConfig` in `mcp_servers/mcp_servers.py:8`
  - Stores alias, subprocess command, arguments, and timeout.
- `get_server_config()` in `mcp_servers/mcp_servers.py:27`
  - Declares the active server list:
    - Playwright MCP via `npx`
    - Filesystem MCP via `npx`
    - local `event_server`
    - local `dzt_server`
- `MCPServerBundle.__aenter__()` in `mcp_servers/mcp_servers.py:95`
  - Starts each configured server and returns them by alias.
- `MCPServerBundle.__aexit__()` in `mcp_servers/mcp_servers.py:121`
  - Shuts all servers down in reverse order.
- `bundle_servers()` in `mcp_servers/mcp_servers.py:136`
  - Convenience wrapper returning an `MCPServerBundle`.

Why it matters:

- This is the infrastructure glue between the agents and the MCP tool ecosystem.
- It also enforces the allowed filesystem root by passing `reports_dir` into the Filesystem server.

### `mcp_servers/event_server.py`

This is the custom Eventim-facing MCP server. It wraps backend HTTP APIs and exposes them as MCP tools.

High-level responsibilities:

- Resolves city names into backend city keys.
- Converts local Berlin times into UTC API query parameters.
- Converts backend UTC timestamps back to Berlin time for convenience.
- Caches backend responses in memory using backend-provided TTLs.
- Exposes tool functions the planner can call.

Important internal helpers:

- `_parse_iso()` in `mcp_servers/event_server.py:24`
  - Parses ISO strings and normalizes trailing `Z`.
- `_to_utc_z()` in `mcp_servers/event_server.py:38`
  - Converts local datetimes into UTC `Z` strings for the backend.
- `_to_dt_in_berlin()` in `mcp_servers/event_server.py:51`
  - Converts backend UTC values into Berlin-local output timestamps.
- `_safe_bool()` in `mcp_servers/event_server.py:63`
  - Normalizes boolean-like inputs from MCP/tool calls.
- `_cache_is_valid()` in `mcp_servers/event_server.py:100`
  - Validity check for TTL-based cache entries.
- `_valid_until_from_response()` in `mcp_servers/event_server.py:114`
  - Reads the backend cache boundary from `validUntilUtc`.
- `_http_get()` in `mcp_servers/event_server.py:131`
  - Shared HTTP GET utility.
- `_cache_or_fetch_dict()` in `mcp_servers/event_server.py:143`
  - Generic "read cache or fetch fresh" helper.
- `_rebuild_city_indices()` in `mcp_servers/event_server.py:171`
  - Rebuilds city-name and city-key lookup maps.
- `_resolve_city_key()` in `mcp_servers/event_server.py:243`
  - Converts a city display name or raw city key into the backend city key.

Important exposed MCP tools:

- `get_supported_cities_with_active_events()` in `mcp_servers/event_server.py:196`
  - Fetches supported cities and refreshes the internal city lookup index.
- `get_events_for_city()` in `mcp_servers/event_server.py:268`
  - Main event query endpoint; converts input times, caches results, and returns Berlin-local convenience timestamps.
- `get_similar_events()` in `mcp_servers/event_server.py:354`
  - Fetches similar events for a known `event_id`.
- `get_popular_events()` in `mcp_servers/event_server.py:403`
  - Fetches "popular" events, with an explicit note that the backend may currently return random items rather than true ranking.

Why it matters:

- This server is the primary structured event data source for the planner.
- The time-conversion logic here is critical because the planner instructions assume Europe/Berlin semantics while the backend uses UTC.

### `mcp_servers/dzt_server.py`

This is the DZT-facing MCP server. It acts as a thin proxy over a remote JSON-RPC API.

High-level responsibilities:

- Adds the DZT API key and JSON-RPC envelope.
- Normalizes tool calls into a common request shape.
- Exposes focused sightseeing and trail search tools to the planner.

Important helpers:

- `_dzt_rpc_call()` in `mcp_servers/dzt_server.py:18`
  - Low-level POST request wrapper for the remote DZT endpoint.
- `_dzt_tool_call()` in `mcp_servers/dzt_server.py:42`
  - Common tool adapter that unwraps the DZT response and raises on `isError`.

Important exposed MCP tools:

- `get_pois_by_criteria()` in `mcp_servers/dzt_server.py:66`
  - Searches points of interest such as museums, landmarks, and restaurants.
- `get_trails_by_criteria()` in `mcp_servers/dzt_server.py:102`
  - Searches hiking and biking trails.
- `get_entity_details()` in `mcp_servers/dzt_server.py:139`
  - Fetches detailed information for a specific DZT entity URI.

Why it matters:

- This is the structured sightseeing data source.
- The server itself is intentionally thin; most of its job is request shaping rather than business logic.

### `mcp_servers/test_mcp_connectivity.py`

This is a local diagnostic script, not application runtime logic.

Purpose:

- Starts all configured MCP servers.
- Lists the available tools on each server.
- Verifies that the filesystem server can list the allowed directories and contents.

This is useful when MCP wiring breaks or when someone wants to confirm local setup before debugging the agent behavior.

### `mcp_servers/web_server_test_backup.py`

This appears to be an older or backup custom browser MCP server implementation using Playwright directly.

Important observations:

- It defines session management, navigation, interaction, extraction, and screenshot tools.
- The active app configuration does not use this file.
- `get_server_config()` currently launches `@playwright/mcp@latest` instead of this custom backup server.

For a new contributor, this should be treated as reference or legacy code unless the team plans to revive it.

### `mcp_servers/__init__.py`

Package marker only. No logic.

## Most Important Schemas

If a new engineer only reads a few models, these are the ones to start with.

### `UserRequest`

Location: `src/schemas.py:111`

Why it matters:

- This is the top-level input contract for the planner flow.
- It groups user identity, trip details, event preferences, sightseeing preferences, itinerary constraints, and delivery settings.

Key nested models:

- `UserProfile`
- `TripRequest`
- `EventPreferences`
- `SightseeingPreferences`
- `ItineraryPreferences`
- `DeliveryOption`

### `TripRequest`

Location: `src/schemas.py:58`

Why it matters:

- This carries the non-negotiable trip constraints: city, dates, planning mode, group size, and budget.
- Its date validator protects against invalid time ranges early.

### `CoreResult`

Location: `src/schemas.py:193`

Why it matters:

- This is the planner agent's primary output contract.
- It is the most important schema in the system after `UserRequest`.
- Everything downstream depends on it: UI conversion, reporting, and saved output.

Key fields:

- `recommendation`
- `events`
- `sightseeing_spots`
- `itinerary`
- `sources`
- `warnings`

Guardrails:

- Limits events to 5.
- Relies on nested validators to constrain recommendation length and itinerary density.

### `EventItem`

Location: `src/schemas.py:138`

Why it matters:

- Represents one planned event.
- Includes the fields that make event selection actionable: when, where, cost, what it is, and where the source/ticket links are.

Especially important fields:

- `name`
- `start_datetime`
- `address_or_area`
- `price`
- `source_url`
- `ticket_url`
- `event_id`

### `SightseeingSpot`

Location: `src/schemas.py:151`

Why it matters:

- Represents a sightseeing recommendation with enough detail to justify inclusion in an itinerary.

Especially important fields:

- `name`
- `address`
- `entry_fee`
- `opening_hours`
- `why_visit`
- `source_url`

### `ItineraryDay` and `ItineraryStop`

Locations:

- `src/schemas.py:161`
- `src/schemas.py:168`

Why they matter:

- These models turn a flat set of recommendations into a chronological plan.
- They are the bridge from data retrieval to an actual user-facing itinerary.

### `MarkdownReport` and `ReporterResult`

Locations:

- `src/schemas.py:216`
- `src/schemas.py:227`

Why they matter:

- `MarkdownReport` is the structured form of the final written report.
- `ReporterResult` proves both that the report was created and where it was saved.

### `UIResult`

Location: `src/schemas.py:259`

Why it matters:

- This is the reduced representation intended for UI display.
- It deliberately drops detail and caps the event list to keep the interface concise.

## Design Strengths

- Clear schema-first architecture. The system relies on explicit Pydantic contracts rather than loose dictionaries.
- Good separation of responsibilities between planning and reporting.
- MCP server configuration is centralized, which makes tool setup easier to understand.
- Event server includes practical cache and timezone handling, which are important in a planning app.
- The UI-facing result is intentionally separate from the full planning result.

## Maintenance Notes and Caveats

- `src/reporting.py` and the reporter agent overlap in responsibility. Future changes to reporting may need to be updated in both places or one path should be chosen as canonical.
- `main.py` is currently not representative of the real application entrypoint, so new contributors should not start there.
- `mcp_servers/web_server_test_backup.py` looks non-active and may confuse newcomers if not documented as legacy or backup code.
- A meaningful amount of application behavior is encoded in prompts in `src/instructions.py`, so code-only reading does not tell the full story.

## Recommended Reading Order for a New Contributor

1. `src/schemas.py`
2. `src/event_client.py`
3. `src/instructions.py`
4. `mcp_servers/mcp_servers.py`
5. `mcp_servers/event_server.py`
6. `mcp_servers/dzt_server.py`
7. `src/reporting.py`

This order gives the reader the contracts first, then the orchestration flow, then the tool layer, and finally the reporting helpers.

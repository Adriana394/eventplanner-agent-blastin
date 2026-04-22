# Code Documentation — eventplanner-agent

This document explains the architecture, files, and key concepts of `eventplanner-agent`
for team members who are new to the project. It answers: *what does each file do, why does
it exist, and how do the pieces fit together?*

---

## What Is This Project?

**Dion** is an AI-powered city trip and event planner built for BlastIn.

A user fills out a planning form (city, dates, vibe, budget, etc.) and Dion returns:
- a curated list of **events** (sourced from Eventim)
- **sightseeing spots** and **food & drink recommendations** (sourced from DZT)
- a **day-by-day itinerary** that fits everything together
- a **markdown report** the user can save or download

The system is built around three AI agents, a validation loop, and a set of structured data contracts (schemas) that control exactly what each agent can return.

---

## Key Concept: What Are Schemas?

`src/schemas.py` is the **shared data contract** for the entire project.

Think of it like a form with strict rules: every field has a name, a type, and sometimes a constraint. If an agent tries to return data that doesn't fit the schema, the run fails with a clear error instead of silently producing garbage.

### Input Schemas (what the UI sends to the agent)

| Schema | What it represents |
|--------|--------------------|
| `UserRequest` | The top-level object the UI builds and passes to Dion. Contains everything below. |
| `UserProfile` | Optional user name for personalization. |
| `TripRequest` | City, dates, planning mode, group size, budget, scope flags (events/sightseeing/food). |
| `EventPreferences` | Vibe, categories, time preference, free-only flag. |
| `SightseeingPreferences` | Interests, indoor/outdoor preference, free-only flag. |
| `ItineraryPreferences` | Must-avoid list. |
| `DeliveryOption` | Language selection, optional email delivery. |
| `Budget` | Min/max budget in EUR. Validated: min must be ≤ max. |
| `PlanningMode` | Either `full_trip` (multi-day) or `event_day_trip` (single day/event focus). |
| `TimePreferences` | `daytime` (10–17h), `evening` (17–22h), `night` (22h+), or `no preferences`. |
| `Language` | `English` or `Deutsch`. Controls all agent output language. |

### Output Schemas (what the agents return)

| Schema | What it represents |
|--------|--------------------|
| `CoreResult` | The full planning result from `Dion_Planner`. Contains events, sightseeing spots, food/drink spots, itinerary, recommendation, warnings, and personal feedback. |
| `EventItem` | A single event with start/end time, area/address, price info, `source_url`, optional `ticket_url`, and backend `event_id`. |
| `SightseeingSpot` | A sightseeing location (name, address, entry fee, opening hours, why it was selected). |
| `FoodDrinkSpot` | A restaurant, bar, or cafe (name, type, price hint, why it matches). |
| `ItineraryDay` | One day in the plan, containing an ordered list of `ItineraryStop` objects. Max 5 sightseeing stops per day. |
| `ItineraryStop` | A single stop in the itinerary: title, time, type (`sightseeing`, `event`, `food`, `other`), notes, `linked_item_name`, and optional `source_url`. |
| `Recommendation` | Max 5 sentences explaining why the plan fits the user's request. |
| `UIResult` | A slimmed-down version of `CoreResult` for the UI. Max 3 events shown, shorter stop info. |
| `ValidationResult` | Output from `Dion_Validator`: whether the plan needs revision and a list of concrete issues. |
| `ValidationIssue` | A single validation finding with a code, message, and severity (`info`, `warning`, `error`). |
| `MarkdownReport` | The full trip report: title, recommendation, ordered sections, sources, timestamp. |
| `ReporterResult` | Wrapper around `MarkdownReport` returned by `Dion_Reporter`, with an optional `saved_report_path`. |

---

## The Three Agents

The system uses three specialized AI agents. Each has a strict role and cannot do what the others do.

### 1. Dion_Planner
**What it does:** Plans the trip. Searches for events (via Eventim), sightseeing and food spots (via DZT), can use Playwright for URL discovery/validation, and returns a `CoreResult`.

**Tools available:** Eventim MCP, DZT MCP, Playwright, filesystem MCP

**System instructions:** `SYSTEM_INSTRUCTIONS_PLANNER` in `src/instructions.py`

**Key rules from the instructions:**
- Never invent events, venues, prices, or opening hours
- Event relevance is a hard requirement — no mismatched content
- Time preferences map to concrete time ranges (daytime 10–17h, evening 17–22h, night 22h+)
- No venue may be reused across multiple days for food/drink stops
- Must make at least 2 separate DZT calls for sightseeing on multi-day trips
- Scope flags (`events_enabled`, `sightseeing_enabled`, `food_drink_enabled`) are hard constraints

### 2. Dion_Validator
**What it does:** Reviews the `CoreResult` against the original `UserRequest` and returns a `ValidationResult` listing any concrete problems.

**Tools available:** None (read-only analysis)

**System instructions:** `SYSTEM_INSTRUCTIONS_VALIDATOR` in `src/instructions.py`

**Key rules from the instructions:**
- Only flag issues that are grounded in the actual data
- Overlapping itinerary stops are high-severity
- The validator prompt treats paid sightseeing spots labeled as "optional" as acceptable when free-only can't be fully met
- Final `needs_revision` is not taken from the validator alone; Python merges deterministic issues with the agent findings and derives the final decision from that combined list

**Important runtime note:** `src/event_client.py` currently still flags paid sightseeing spots in deterministic validation when `sightseeing.free_only = true`, so the real runtime behavior is stricter than the validator prompt alone.

### 3. Dion_Reporter
**What it does:** Takes the validated `CoreResult` and returns a `ReporterResult` containing a `MarkdownReport`. Does not search for new information.

**Tools available:** None (output-only)

**System instructions:** `SYSTEM_INSTRUCTIONS_REPORTER` in `src/instructions.py`

**Key rules from the instructions:**
- No new facts — only what's in the provided data
- Report language must match the user's language selection
- Day-by-day sections should read like a coherent story, not a data dump
- The system saves the report to disk automatically

---

## End-to-End Flow

```
User fills form
      │
      ▼
UI builds UserRequest (src/dion_ui.py)
      │
      ▼
run_full_planner_flow() (src/event_client.py)
      │
      ├─ 1. Start MCP servers (Playwright, filesystem, Eventim, DZT)
      │
      ├─ 2. Dion_Planner runs → returns CoreResult
      │
      ├─ 3. Post-processing pipeline (Python, deterministic):
      │      • sync authoritative Eventim event data
      │      • remove generic placeholder stops
      │      • remove duplicate food venues across days
      │      • normalize event / sightseeing / food URLs
      │      • verify place URLs in parallel (HTTP reachability)
      │      • resync verified URLs into itinerary stops
      │
      ├─ 4. Deterministic validation (Python):
      │      • scope flags respected?
      │      • free-only constraints met?
      │      • itinerary stops reference real items?
      │      • dates aligned with request?
      │      • malformed place URLs flagged?
      │
      ├─ 5. Dion_Validator runs with the deterministic findings as input
      │      • final ValidationResult merges Python checks + agent findings
      │
      ├─ 6. If needs_revision = true:
      │      └─ Dion_Planner receives repair prompt → revised CoreResult
      │         └─ Post-processing pipeline runs again
      │
      ├─ 7. CoreResult → UIResult (for display)
      │
      ├─ 8. Dion_Reporter runs → returns ReporterResult
      │
      └─ 9. Python appends final link notes if needed and saves report to outputs/reports/
```

**Follow-up flow** (`run_followup_planner_flow`) is similar but passes the existing `CoreResult` as context and asks the planner to revise only affected parts.

---

## File Reference

### `src/`

| File | Role |
|------|------|
| `event_client.py` | Core orchestration. Runs agents, manages MCP servers, post-processing, validation loop, report persistence. The most important file in the project. |
| `schemas.py` | All Pydantic data contracts (inputs + outputs). The shared language between UI, agents, and code. |
| `instructions.py` | System prompts for all three agents. Much of the product behavior lives here, not in Python. |
| `dion_ui.py` | Streamlit frontend. Collects user input, builds `UserRequest`, triggers flows, renders results. |
| `dion_styles.py` | CSS for the Streamlit UI (extracted to keep `dion_ui.py` focused on logic). |
| `dion_translations.py` | EN/DE UI text strings (extracted to keep translations centralized). |
| `dion_gradio_ui.py` | Alternative Gradio UI. Exists for side-by-side comparison during testing, not the primary frontend. |
| `reporting.py` | Helpers for building the markdown report from structured data and saving it to disk. |

### `mcp_servers/`

| File | Role |
|------|------|
| `mcp_servers.py` | MCP server configuration and lifecycle. Defines which servers are available, passes config (e.g. reports directory), handles startup/shutdown. |
| `event_server.py` | Custom Eventim-facing MCP server. Resolves cities, fetches events for a date range, normalizes UTC↔Europe/Berlin times, caches responses. |
| `dzt_server.py` | DZT-facing MCP server. Wraps DZT tool calls for POI search, trails, and entity details. |
| `test_mcp_connectivity.py` | Smoke-test script for MCP startup and basic tool access. Useful when a server fails before the planner runs. |
| `web_server_test_backup.py` | Older local Playwright MCP prototype kept as backup/reference. Not part of the main runtime path. |

### Root files

| File | Role |
|------|------|
| `README.md` | Project overview and setup instructions. Start here. |
| `DEMO_CASES.md` | All test/demo scenarios with inputs, expected outcomes, and checklists. |
| `EVENT_API_ENDPOINTS.md` | Reference notes for the Eventim-facing backend endpoints and expected request/response shape. |
| `IDEAS.md` | Future feature ideas parked for later (budget levels, mobility modes, etc.). |
| `main.py` | Minimal placeholder entrypoint. Not used for the planner app itself. |
| `pyproject.toml` | Project metadata and dependencies (managed with `uv`). |
| `.env` | Local environment variables (model keys, API endpoints). Not committed. |
| `outputs/reports/` | Where generated markdown reports are saved at runtime. |

---

## MCP Tools — What the Planner Can Use

MCP (Model Context Protocol) is the interface through which the AI agents call external tools. The runtime starts four MCP servers. The planner is attached to all four, although the filesystem server is mainly used by Python code for controlled report persistence.

**Eventim** (via `event_server.py`)
- `get_supported_cities_with_active_events` — resolves a city name to a backend city key
- `get_events_for_city` — fetches events for a city and date range
- `get_similar_events` — optional: finds related events
- `get_popular_events` — optional: returns popular events (may be random)

**DZT** (via `dzt_server.py`)
- `get_pois_by_criteria` — structured POI search for sightseeing, restaurants, bars, cafes, and similar place types
- `get_trails_by_criteria` — structured trail search
- `get_entity_details` — fetches full details for a specific DZT entity

**Playwright** (via external MCP server)
- Web browsing and content extraction
- Used to validate and discover correct URLs for non-Eventim places
- Can also extract content from event or venue pages when needed

**Filesystem** (via external MCP server)
- Scoped to `REPORTS_DIR`
- Used by the application to write the final markdown report into the allowed reports directory

---

## Post-Processing Pipeline

After the planner returns a `CoreResult`, Python applies a deterministic pipeline before anything reaches the UI or validator. This pipeline runs identically for both initial and follow-up planning runs.

```python
_sync_core_result_events_with_authoritative_data()   # enrich from Eventim backend
_sanitize_itinerary_placeholders()                   # remove generic filler stops
_deduplicate_food_stops_in_itinerary()               # remove repeated food venues
_insert_default_food_structure()                     # fill missing meal slots
_sanitize_event_source_urls()                        # normalize event links
_sanitize_sightseeing_source_urls()                  # normalize sightseeing links
_sanitize_food_and_drink_source_urls()               # normalize food/drink links
_verify_place_source_urls()                          # HTTP check all place links (parallel)
_sync_itinerary_stop_source_urls()                   # propagate verified URLs into stops
```

Key behaviors:
- **Places are never removed due to link issues.** If a link cannot be verified, the place is kept and the link is set to `null`. A warning is added.
- **Duplicate food venues are removed.** If the agent reuses the same restaurant on multiple days or twice in one day, the duplicates are stripped and a warning is shown.
- **Link verification is parallel** (`asyncio.gather`) — verifying 10+ links takes roughly the same time as verifying one.

---

## Progress Reporting

The planning flow reports real progress steps to the UI via a callback:

```python
ProgressCallback = Callable[[int, str], None]  # (percent, message)
```

Full planning flow (`run_full_planner_flow`) progress steps:
| % | Message (EN) |
|---|--------------|
| 5 | Starting MCP servers... |
| 15 | Searching for events and places... |
| 50 | Building the plan... |
| 65 | Validating and refining the plan... |
| 80 | Writing the report... |
| 92 | Saving report... |

Follow-up planning flow (`run_followup_planner_flow`) progress steps:
| % | Message (EN) |
|---|--------------|
| 5 | Starting MCP servers... |
| 15 | Revising the current plan... |
| 50 | Processing and verifying results... |
| 65 | Validating and refining the plan... |
| 80 | Writing the report... |
| 92 | Saving report... |

Messages are bilingual (EN/DE) and derived from the user's language selection — not hardcoded in the UI.

---

## Configuration

The runtime reads these values from environment variables, typically loaded from `.env`.

| Variable | Purpose |
|----------|---------|
| `MODEL_PROVIDER` | `openai` or `openrouter` |
| `OPENAI_API_KEY` | OpenAI key |
| `OPENROUTER_API_KEY` | OpenRouter key |
| `OPENROUTER_BASE_URL` | OpenRouter API base URL (defaults to `https://openrouter.ai/api/v1`) |
| `OPENROUTER_APP_NAME` | Optional OpenRouter app title header |
| `OPENROUTER_SITE_URL` | Optional OpenRouter referer header |
| `OPENAI_PLANNER_MODEL` | Model name for Dion_Planner (OpenAI) |
| `OPENAI_REPORTER_MODEL` | Model name for Dion_Reporter (OpenAI) |
| `OPENAI_VALIDATOR_MODEL` | Model name for Dion_Validator (OpenAI) |
| `OPENROUTER_PLANNER_MODEL` | Model name for Dion_Planner (OpenRouter) |
| `OPENROUTER_REPORTER_MODEL` | Model name for Dion_Reporter (OpenRouter) |
| `OPENROUTER_VALIDATOR_MODEL` | Model name for Dion_Validator (OpenRouter) |
| `PLANNER_MODEL` | Provider-agnostic fallback for the planner model |
| `REPORTER_MODEL` | Provider-agnostic fallback for the reporter model |
| `VALIDATOR_MODEL` | Provider-agnostic fallback for the validator model |
| `CITY_URL` | Eventim city lookup endpoint |
| `EVENT_URL` | Eventim event fetch endpoint |
| `DZT_URL` | DZT RPC endpoint |
| `DZT_API_KEY` | API key for DZT |
| `REPORTS_DIR` | Output path for saved reports (default: `outputs/reports/`) |

The MCP smoke-test script `mcp_servers/test_mcp_connectivity.py` additionally reads `MCP_SMOKE_INCLUDE`, `MCP_SMOKE_SKIP`, `MCP_SMOKE_STARTUP_TIMEOUT`, and `MCP_SMOKE_TOOL_TIMEOUT`.

---

## Recommended Reading Order

For someone new to the project:

1. `README.md` — setup and run instructions
2. `DEMO_CASES.md` — understand what the system is supposed to produce
3. `src/schemas.py` — learn the data contracts before touching any logic
4. `src/instructions.py` — understand how agent behavior is controlled
5. `src/event_client.py` — follow the runtime flow end to end
6. `src/dion_ui.py` — see how the UI builds requests and renders results
7. `mcp_servers/mcp_servers.py` + `event_server.py` + `dzt_server.py` — understand the tool layer

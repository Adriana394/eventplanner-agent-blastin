# Code Documentation — eventplanner-agent

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
- **Retry rules:** if Eventim returns 0 events with filters, retry without filter then with expanded date range; if DZT returns 0 results, retry with broad generic terms before giving up
- **Playwright fallback:** if DZT returns 0 after 2 retries, use Playwright to search the web for sightseeing spots or restaurants in the city

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
User fills form in browser (ui/Dion UI.html — React, no build step)
      │
      ▼
POST /api/plan  →  ui/dion_api.py  (FastAPI, sync endpoint, asyncio.run inside)
      │
      ▼  builds UserRequest from request body
run_full_planner_flow(user_request, planner_model=selected_model) (src/event_client.py)
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

**Follow-up flow** (`run_followup_planner_flow`) is similar but compresses the existing `CoreResult` to a slim dict (names, dates, and itinerary structure only — no descriptions) before passing it as context. This keeps the follow-up input small enough to avoid context overflow. The reporter still receives the full `CoreResult`.

---

## File Reference

### `src/`

| File | Role |
|------|------|
| `event_client.py` | Core orchestration. Runs agents, manages MCP servers, post-processing, validation loop, report persistence. The most important file in the project. Also defines `AVAILABLE_MODELS` and `DEFAULT_MODEL` for the UI model selector. |
| `schemas.py` | All Pydantic data contracts (inputs + outputs). The shared language between UI, agents, and code. |
| `instructions.py` | System prompts for all three agents. Much of the product behavior lives here, not in Python. |
| `reporting.py` | Helpers for building the markdown report from structured data and saving it to disk. |

### `ui/`

| File | Role |
|------|------|
| `dion_api.py` | FastAPI server. Exposes `POST /api/plan` and `POST /api/followup`, serializes `UIResult` to the JSON shape the frontend expects, and serves the static HTML/JSX files. Start with `uv run python ui/dion_api.py`. |
| `Dion UI.html` | React frontend entry point. Loads React and Babel from CDN, then imports the JSX modules. No build step needed — open via the FastAPI server at `http://localhost:7860`. |
| `dion-app.jsx` | Root `App` component. Owns all state (form, scope, plan, history), builds the API request body from form values, calls `/api/plan` and `/api/followup`, and renders the four-tab shell. |
| `dion-data.jsx` | Constants: `AVAILABLE_MODELS`, dropdown options, and `DEMO_PLAN` (Berlin demo data for the "Fill with demo data" button). |
| `dion-icons.jsx` | Lightweight SVG icon components used across the UI. |
| `dion-mark.jsx` | Animated Dion mascot (`DionMark`) and welcome speech bubble (`DionBubble`) rendered as a fixed floating widget at the bottom-right of the viewport. The bubble cycles through a German and an English message, then disappears. |
| `dion-output.jsx` | Output column components: `StatusBar`, `EventList`, `SpotList`, `Itinerary`, `FollowUpPanel`, `ReportFile`, and accordion JSON viewers. |
| `dion-tabs.jsx` | The three non-planner tab views: `VenueTab` (flat filterable inventory), `BriefTab` (JSON inspector), `IterationTab` (versioned plan history). |

### `mcp_servers/`

| File | Role |
|------|------|
| `mcp_servers.py` | MCP server configuration and lifecycle. Defines which servers are available, passes config (e.g. reports directory), handles startup/shutdown. |
| `event_server.py` | Custom Eventim-facing MCP server. Resolves cities, fetches events for a date range, normalizes UTC↔Europe/Berlin times, caches responses. |
| `dzt_server.py` | DZT-facing MCP server. Wraps DZT tool calls for POI search, local events, trails, and entity details. |

### Root files

| File | Role |
|------|------|
| `README.md` | Project overview and setup instructions. Start here. |
| `DEMO_CASES.md` | All test/demo scenarios with inputs, expected outcomes, and checklists. |
| `EVENT_API_ENDPOINTS.md` | Reference notes for the Eventim-facing backend endpoints and expected request/response shape. |
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
- `get_events_by_criteria` — structured search for local events (festivals, markets, city events) not covered by Eventim
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
_fix_event_stop_dates()                              # move event stops placed on wrong day
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

The FastAPI endpoints (`/api/plan`, `/api/followup`) are synchronous — they block until the agent finishes and then return the complete result as JSON. There is no server-sent streaming.

The React frontend simulates progress while waiting: a `setInterval` timer advances through the `PROGRESS_STEPS_I18N` object in `dion-app.jsx` every 18 seconds. The language (`en` or `de`) is derived from `form.language` at the start of each run. When the API response arrives, the timer is cleared and the real result is rendered immediately. If the API returns an error, the status bar shows a red dot with the error message.

The step labels adapt to the user's selected language:

| Step | English | Deutsch |
|------|---------|---------|
| 1 | Starting MCP servers… | MCP-Server werden gestartet… |
| 2 | Searching for events and places… | Events und Orte werden gesucht… |
| 3 | Building the plan… | Plan wird erstellt… |
| 4 | Validating and refining the plan… | Plan wird geprüft und verfeinert… |
| 5 | Writing the report… | Bericht wird geschrieben… |
| 6 | Plan and report created successfully. | Plan und Bericht erfolgreich erstellt. |

---

## UI Model Selector

The top-bar of the React UI exposes a dropdown that lets the user choose which AI model `Dion_Planner` should use for the current request. The list of options and the default are defined as constants in `src/event_client.py`:

```python
AVAILABLE_MODELS = [
    'google/gemini-2.5-flash',   # default — large context, reliable
    'z-ai/glm-4.7',              # top τ²-Bench score
    'moonshotai/kimi-k2.6',      # strong agentic benchmark results
]
DEFAULT_MODEL = AVAILABLE_MODELS[0]
```

**How it flows through the code:**

1. `ui/dion-data.jsx` imports `AVAILABLE_MODELS` and `DEFAULT_MODEL` as static constants (mirrored from the backend)
2. The selected value is included as `model` in the JSON body sent to `POST /api/plan` or `POST /api/followup`
3. `ui/dion_api.py` reads `body.model` and passes it as `planner_model=body.model` to both `run_full_planner_flow` and `run_followup_planner_flow`
4. Both flow functions accept an optional `planner_model` parameter — if provided it overrides the value from `.env`

`reporter_model` and `validator_model` are not affected and continue to use the `.env` configuration.

To add or remove models, update `AVAILABLE_MODELS` in `src/event_client.py` **and** mirror the change in `ui/dion-data.jsx` — the two lists are currently kept in sync manually.

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
| `OPENROUTER_PLANNER_MODEL` | Default model name for Dion_Planner (OpenRouter) — overridden per request when the user selects a model in the UI |
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

---

## Recommended Reading Order

For someone new to the project:

1. `README.md` — setup and run instructions
2. `DEMO_CASES.md` — understand what the system is supposed to produce
3. `src/schemas.py` — learn the data contracts before touching any logic
4. `src/instructions.py` — understand how agent behavior is controlled
5. `src/event_client.py` — follow the runtime flow end to end
6. `ui/dion_api.py` — see how the API layer builds `UserRequest`, calls the flows, and serializes results
7. `ui/dion-app.jsx` — see how the frontend sends requests and renders the response
8. `mcp_servers/mcp_servers.py` + `event_server.py` + `dzt_server.py` — understand the tool layer

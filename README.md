# Dion — AI Event & City Trip Planner

Dion is an AI-powered event and city trip planner built for BlastIn. Given a city, date range, and personal preferences, Dion finds real events, sightseeing spots, and food & drink recommendations, then builds a coherent day-by-day itinerary and a markdown trip report.

---

## Features

- **Event discovery** via Eventim (concerts, clubs, shows, festivals)
- **Sightseeing & food** via DZT (landmarks, restaurants, bars, cafes)
- **Day-by-day itinerary** that respects timing, budget, and personal vibe
- **Validation loop** — a second agent reviews the plan before it reaches the user
- **Follow-up revisions** — refine an existing plan without starting from scratch
- **Markdown report** generated and saved automatically
- **Bilingual** — full EN and DE support throughout the UI and reports
- **OpenAI and OpenRouter** model provider support
- **UI model selector** — choose the planner AI model directly in the interface

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)
- A `.env` file with the required API keys (see [Configuration](#configuration))

---

## Getting Started

**1. Clone the repository**

```bash
git clone <repo-url>
cd eventplanner-agent
```

**2. Install dependencies**

```bash
uv sync
```

**3. Configure environment variables**

Copy the example or create a `.env` file in the project root:

```bash
cp .env.example .env   # if an example exists, otherwise create manually
```

Minimum required variables:

```env
MODEL_PROVIDER=openai          # or openrouter
OPENAI_API_KEY=sk-...
CITY_URL=<eventim-city-endpoint>
EVENT_URL=<eventim-event-endpoint>
```

See [Configuration](#configuration) for the full variable list.

**4. Run the app**

```bash
uv run python ui/dion_gradio_ui.py
```

The app is available at `http://localhost:7860`.

---

## Configuration

All sensitive values and model selections are controlled via `.env`.

| Variable | Description |
|----------|-------------|
| `MODEL_PROVIDER` | `openai` or `openrouter` |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `OPENAI_PLANNER_MODEL` | Model for the planner agent (OpenAI) |
| `OPENAI_REPORTER_MODEL` | Model for the reporter agent (OpenAI) |
| `OPENAI_VALIDATOR_MODEL` | Model for the validator agent (OpenAI) |
| `OPENROUTER_PLANNER_MODEL` | Default planner model (OpenRouter) — can be overridden per request from the UI |
| `OPENROUTER_REPORTER_MODEL` | Model for the reporter agent (OpenRouter) |
| `OPENROUTER_VALIDATOR_MODEL` | Model for the validator agent (OpenRouter) |
| `CITY_URL` | Eventim city lookup endpoint |
| `EVENT_URL` | Eventim event fetch endpoint |
| `REPORTS_DIR` | Output path for saved reports (default: `outputs/reports/`) |

The UI exposes a model selector for the planner agent. Available choices and the default are defined in `AVAILABLE_MODELS` / `DEFAULT_MODEL` in `src/event_client.py`.

---

## Project Structure

```
eventplanner-agent/
├── src/
│   ├── event_client.py        # Core orchestration, validation loop, agent runs
│   ├── schemas.py             # All Pydantic data contracts (inputs + outputs)
│   ├── instructions.py        # System prompts for all three agents
│   └── reporting.py           # Markdown report construction and file persistence
├── ui/
│   ├── dion_gradio_ui.py      # Gradio frontend (primary UI)
│   ├── dion_styles.py         # UI CSS (extracted for readability)
│   └── dion_translations.py   # EN/DE UI text strings
├── mcp_servers/
│   ├── mcp_servers.py         # MCP server config and lifecycle management
│   ├── event_server.py        # Eventim-facing MCP server
│   └── dzt_server.py          # DZT-facing MCP server (places, sightseeing, food)
├── outputs/
│   └── reports/               # Generated markdown reports (runtime output)
├── CODE_DOKUMENTATION.md      # Detailed codebase guide for new team members
├── DEMO_CASES.md              # Test/demo scenarios with inputs and checklists
├── IDEAS.md                   # Future feature ideas
└── pyproject.toml             # Project metadata and dependencies
```

---

## How It Works

1. The user fills out the planning form in the UI
2. The UI builds a structured `UserRequest` (city, dates, vibe, budget, scope flags)
3. `Dion_Planner` searches for events (Eventim), sightseeing and food spots (DZT), and validates links (Playwright)
4. A deterministic post-processing pipeline cleans and verifies the result
5. `Dion_Validator` checks for constraint violations and inconsistencies
6. If the plan needs revision, `Dion_Planner` receives a targeted repair prompt
7. The final result is displayed in the UI and passed to `Dion_Reporter`
8. `Dion_Reporter` generates a markdown report, saved to `outputs/reports/`

For a deeper technical walkthrough, see [`CODE_DOKUMENTATION.md`](CODE_DOKUMENTATION.md).

---

## Testing

Use the scenarios in [`DEMO_CASES.md`](DEMO_CASES.md) for manual end-to-end testing.
Each case includes exact inputs, expected outcomes, and a checklist to verify.

Quick import checks:

```bash
uv run python -c "from src.event_client import run_full_planner_flow, AVAILABLE_MODELS; print('OK')"
uv run python -c "from src.schemas import UserRequest; print('OK')"
uv run python -c "import ui.dion_gradio_ui; print('OK')"
```

---

## Contributing

- `src/schemas.py` is the shared contract — coordinate with the team before changing it
- Agent behavior is controlled via `src/instructions.py`, not only Python code
- Available UI models are defined in `AVAILABLE_MODELS` in `src/event_client.py` — update there to add or remove choices
- New feature ideas go in `IDEAS.md` before being implemented
- Run through the relevant demo cases after any change to `event_client.py` or `instructions.py`

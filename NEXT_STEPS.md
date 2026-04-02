# Next Steps

This document captures the next implementation priorities for the `eventplanner-agent` project.
The order is intentionally structured so that data quality and planning reliability are addressed
before additional product and model-layer features are introduced.

## 0. Current Progress Snapshot

Status as of the latest working session:

- OpenRouter integration is now implemented in `src/event_client.py`
- provider switching is controlled via `.env`, not via the UI
- current provider logic supports:
  - `MODEL_PROVIDER=openai`
  - `MODEL_PROVIDER=openrouter`
- current model config supports:
  - `OPENAI_PLANNER_MODEL`
  - `OPENAI_REPORTER_MODEL`
  - `OPENROUTER_PLANNER_MODEL`
  - `OPENROUTER_REPORTER_MODEL`
- `OPENROUTER_API_KEY` is expected from `.env`
- OpenRouter is wired through the OpenAI-compatible client with base URL `https://openrouter.ai/api/v1`

Important current product decisions:

- Eventim links must remain in the output and should not be removed by generic link validation
- only sightseeing and food/drink external links should be actively checked
- model selection should stay in the backend/client configuration and not be exposed in the UI
- event relevance is currently handled primarily through stronger planner instructions and a stronger planner model, not through Python keyword heuristics

Current stopping point for the next session:

1. ~~OpenRouter is implemented and usable via `.env`; continue testing real planner/reporter model combinations only as needed~~
2. Continue Phase 1 reliability work, especially:
   - ~~link validation behavior for sightseeing and food/drink pages~~
   - itinerary date coverage
   - ~~follow-up report refresh verification~~
3. Improve consistency between recommendation text and structured result

Latest observed quality status:

- event relevance is clearly better than before
- no mismatched musicals/theater were inserted in the latest Hannover example
- report and structured output are now much more aligned
- remaining issue: recommendation text can still contradict structured facts
  - example: recommendation said "kostenlose Outdoor-Sightseeing-Möglichkeiten" while `Herrenhäuser Gärten` had an entry fee
- remaining issue: some food/drink source URLs are still empty, so report sections have thinner sourcing than sightseeing
- remaining issue: itinerary can still contain generic fallback blocks such as "Freie Zeit für Entdeckung oder Ausruhen"

## 1. Remaining Plan

### Phase 1: Reliability

- [ ] Fix consistency between recommendation text and structured facts
- [ ] Fix itinerary/date coverage so the final trip day is included correctly
- [ ] Reduce generic fallback itinerary blocks such as "Freie Zeit für Entdeckung oder Ausruhen"
- [ ] Improve sourcing completeness for food/drink recommendations when URLs are missing
- [ ] Keep testing real planner/reporter model combinations only when useful

### Phase 2: Validation Layer

- [ ] Add a controlled validation step before final UI/report output
- [ ] Check for mismatch between user request and selected events
- [ ] Check for mismatch between recommendation text and structured result
- [ ] Check itinerary consistency and date alignment
- [ ] Check constraint violations such as `free_only`
- [ ] Decide later whether this should become a dedicated third agent

### Phase 3: Report Quality

- [ ] Expand the report so it is more useful and informative
- [ ] Add clearer rationale for why selected items fit the user request
- [ ] Improve the day-by-day narrative
- [ ] Explain budget fit and tradeoffs more clearly
- [ ] Polish Dion's personal closing section

### Phase 4: Product Extensions

- [ ] Add PDF export/download for the report
- [ ] Compare more planner/reporter model options through OpenRouter when needed

## 2. Next Session Entry Point

- [ ] Review the latest baseline result
- [ ] Start with recommendation-text vs structured-facts consistency
- [ ] Then continue with itinerary final-day coverage and generic-stop quality
- [ ] After that, move into the validation layer

## 3. Working Principle

- [ ] First improve correctness
- [ ] Then improve consistency
- [ ] Then improve product polish
- [ ] Then expand flexibility and model experimentation

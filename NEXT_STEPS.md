# Next Steps

This document captures the next implementation priorities for the `eventplanner-agent` project.
The order is intentionally structured so that data quality and planning reliability are addressed
before additional product and model-layer features are introduced.

## 1. Goal

The immediate goal is to make Dion reliable enough for realistic testing:

- links should be valid before they appear in the UI or report
- planned events should actually match the user request
- the full trip date range should be reflected in the itinerary
- follow-up updates should consistently refresh the saved report

Once those foundations are stable, the system can be extended with a validation layer,
more detailed reporting, PDF export, and flexible model routing via OpenRouter.

## 2. Priority Order

### Phase 1: Core Reliability

1. Validate links before they enter the output or report
2. Improve event matching against the user request
3. Fix itinerary/date coverage so the final trip day is included correctly
4. Verify that the report is regenerated and saved after each follow-up update

### Phase 2: Quality Control

5. Add a validation step or third agent for consistency checks
6. Expand the report so it is more informative and useful to the user

### Phase 3: Product Extensions

7. Add PDF export/download for the report
8. Integrate OpenRouter to test different models more easily

## 3. Detailed Work Packages

### 3.1 Link Validation

#### Problem

Some `source_url` and `ticket_url` values appear in the UI and report even though the target page
is broken, unavailable, or no longer valid.

#### Objective

Only show links that have been validated as usable, or clearly mark them as unavailable.

#### Planned Implementation

- add a link validation step before final UI/report rendering
- validate:
  - event `source_url`
  - event `ticket_url`
  - sightseeing `source_url`
  - food/drink `source_url`
  - itinerary `source_url`
- if a link fails validation:
  - remove it from the rendered UI action buttons
  - exclude it from the report if necessary
  - add a warning if the missing link affects user usefulness

#### Notes

- This can initially be implemented as a lightweight validation helper in Python.
- Later, it can become part of a dedicated validation agent or post-processing step.

### 3.2 Event Matching Quality

#### Problem

The current planner sometimes recommends events that do not match the user’s stated vibe,
category, or time preference. Example: nightlife-oriented requests returning musicals.

#### Objective

Ensure that selected events are relevant to the requested vibe, category, and timing.

#### Planned Implementation

- strengthen planner instructions for event relevance
- require Dion to prefer no event over clearly mismatched events
- introduce fallback behavior:
  - if no strong event match exists, state that clearly
  - continue with sightseeing/food if appropriate
  - use `personal_feedback` for optional suggestions, not the actual plan
- add Python-side post-validation to catch obvious mismatches

#### Candidate Validation Rules

- if the request strongly implies nightlife/clubbing/electronic music:
  - reject musicals, theater, and unrelated family entertainment as top matches
- if the request prefers evening/night:
  - avoid primarily daytime event recommendations unless explicitly justified

### 3.3 Itinerary Date Coverage

#### Problem

The full requested date range is not always reflected in the itinerary. In particular,
the last day can be skipped or not planned correctly.

#### Objective

The itinerary should cover the requested range from `date_start` to `date_end`, inclusive,
unless the user explicitly asks for a narrower planning mode.

#### Planned Implementation

- inspect itinerary generation behavior for off-by-one issues
- verify whether the planner prompt or date conversion logic is dropping the final day
- add validation checks to confirm:
  - all requested trip days are represented
  - itinerary labels align with the requested dates
  - events are placed on the correct local day

#### Testing

- 1-day trip
- 2-day trip
- 3-day trip
- edge case with late-night events near midnight

### 3.4 Report Refresh After Follow-Up

#### Problem

It must be guaranteed that each follow-up actually produces an updated report and that the saved
report file reflects the current state of the plan.

#### Objective

After every follow-up revision:

- the updated plan is reflected in the UI
- the markdown report is regenerated
- the saved file is updated consistently

#### Planned Implementation

- verify follow-up flow in `event_client.py`
- confirm that:
  - updated `core_result` is passed to the reporter
  - the file save step is executed on follow-up
  - the stored `saved_report_path` remains valid
- define intended save behavior:
  - overwrite same file
  - or create versioned files

#### Recommendation

For now, keep the same file path for simplicity unless versioning becomes necessary.

## 4. Validation Layer

### 4.1 Purpose

Before introducing more product features, the system should gain a structured quality-control step.

### 4.2 Recommendation

Start with a controlled validation step instead of a completely free third agent.

The validator should check:

- broken or missing links
- mismatch between user request and selected events
- mismatch between recommendation text and structured result
- itinerary consistency
- constraint violations such as `free_only`

### 4.3 Later Extension

If the validation step proves useful, it can evolve into a dedicated third agent with a clearly
defined schema and responsibilities.

## 5. Report Improvements

### Problem

The current report is functional but still too thin in some scenarios.

### Objective

Make the report more useful and more explanatory without becoming verbose or repetitive.

### Planned Improvements

- clearer rationale for why selected items fit the user request
- stronger day-by-day narrative
- better explanation of budget fit
- clearer handling of tradeoffs and fallback decisions
- more polished personal closing section from Dion

## 6. PDF Export

### Objective

Allow users to download the generated report as PDF in addition to Markdown.

### Planned Implementation

- keep Markdown as the canonical report source
- generate PDF from the markdown output
- expose both download options in the UI:
  - `.md`
  - `.pdf`

### Notes

- This should come after report structure is stable.

## 7. OpenRouter Integration

### Objective

Allow easier experimentation with different models for:

- planner
- reporter
- future validator

### Planned Implementation

- centralize model configuration
- add provider/model settings that can be swapped without rewriting agent logic
- integrate OpenRouter API credentials/configuration
- make planner/reporter model selection configurable per environment or UI

### Expected Benefit

This will make it easier to compare:

- quality
- consistency
- cost
- latency

across different model choices.

## 8. Recommended Execution Sequence

The recommended order for implementation is:

1. Link validation
2. Event relevance and fallback logic
3. Final-day itinerary fix
4. Report refresh verification after follow-up
5. Validation step / third-agent design
6. Report expansion
7. PDF export
8. OpenRouter integration

## 9. Working Principle

For the next iterations, the guiding principle should be:

- first improve correctness
- then improve consistency
- then improve product polish
- then expand flexibility and model experimentation

This order reduces wasted effort and makes later model comparisons much more meaningful.

# Demo Cases

This file defines the planned demo and regression scenarios for `eventplanner-agent`.
Use these cases before internal reviews, live demos, or major model/config changes.

## How To Use

For each case:

- run the planner with the exact inputs
- review UI output, structured result, and markdown report
- mark the case as `ready`, `needs review`, or `blocked`
- note concrete issues instead of vague impressions

## Case 1: Elegant Weekend City Trip

- Goal: show balanced planning with events, food/drinks, and lighter sightseeing
- Status: `needs review`
- Inputs:
  - City: `Hannover`
  - Country: `Germany`
  - Dates: `Friday to Sunday`, 3 days
  - Include last trip day: `Yes`
  - Planning mode: `full_trip`
  - Group size: `2`
  - Events: `enabled`
  - Sightseeing: `enabled`
  - Food & drinks: `enabled`
  - Event vibe: `elegant, memorable, evening-forward`
  - Event categories: `concert, show, live performance`
  - Time preference: `evening`
  - Free events only: `No`
  - Sightseeing interests: `landmarks, architecture, city highlights`
  - Sightseeing mode: `No preference`
  - Free sightseeing only: `No`
  - Budget: `150-300 EUR`
  - Avoid list: `family events, generic theatre`
- Expected outcome:
  - strong weekend framing
  - no clearly mismatched musicals or family content
  - itinerary ends cleanly on the final day
  - report feels polished enough for presentation
- Checklist:
  - selected events match the intended upscale tone
  - recommendation does not overclaim free or outdoor activities
  - food/drink venues feel aligned with the evening tone
  - no generic placeholder itinerary stops remain

## Case 2: Berlin Nightlife Focus

- Goal: stress-test nightlife relevance and event selection quality
- Status: `needs review`
- Inputs:
  - City: `Berlin`
  - Country: `Germany`
  - Dates: `2 nights`
  - Include last trip day: `Yes`
  - Planning mode: `full_trip`
  - Group size: `2`
  - Events: `enabled`
  - Sightseeing: `enabled`
  - Food & drinks: `enabled`
  - Event vibe: `techno, underground, late-night`
  - Event categories: `club, concert`
  - Time preference: `night`
  - Free events only: `No`
  - Sightseeing interests: `viewpoints, neighborhoods`
  - Sightseeing mode: `Outdoor`
  - Free sightseeing only: `Yes`
  - Budget: `100-250 EUR`
  - Avoid list: `musicals, theatre, family events`
- Expected outcome:
  - event choices are nightlife-relevant
  - no daytime-heavy or obviously mismatched event filler
  - sightseeing stays compatible with `free_only`
- Checklist:
  - validator does not flag event mismatch
  - no paid sightseeing appears in the final result
  - recommendation matches the actual nightlife content
  - bar recommendations are concrete when mentioned

## Case 3: Food-Forward City Break

- Goal: test a trip that is lighter on events and stronger on city/food quality
- Status: `needs review`
- Inputs:
  - City: `Hamburg`
  - Country: `Germany`
  - Dates: `Saturday to Monday`
  - Include last trip day: `No`
  - Planning mode: `full_trip`
  - Group size: `2`
  - Events: `disabled`
  - Sightseeing: `enabled`
  - Food & drinks: `enabled`
  - Sightseeing interests: `waterfront, viewpoints, neighborhoods`
  - Sightseeing mode: `Outdoor`
  - Free sightseeing only: `No`
  - Budget: `120-260 EUR`
  - Avoid list: `museums`
- Expected outcome:
  - no events in structured result or itinerary
  - the omitted last day is respected
  - the plan still feels complete without an event anchor
- Checklist:
  - no event stops appear anywhere
  - itinerary remains coherent without the final day
  - food/drink venues still look concrete and useful
  - report explains the city-focused direction clearly

## Case 4: Free-Conscious Day Trip

- Goal: validate strict constraint handling
- Status: `needs review`
- Inputs:
  - City: `Leipzig`
  - Country: `Germany`
  - Dates: `single day`
  - Include last trip day: `Yes`
  - Planning mode: `event_day_trip`
  - Group size: `3`
  - Events: `enabled`
  - Sightseeing: `enabled`
  - Food & drinks: `disabled`
  - Event vibe: `casual, cultural`
  - Event categories: `free concert, local event`
  - Time preference: `daytime`
  - Free events only: `Yes`
  - Sightseeing interests: `historic center`
  - Sightseeing mode: `No preference`
  - Free sightseeing only: `Yes`
  - Budget: `0-60 EUR`
  - Avoid list: `nightlife`
- Expected outcome:
  - the plan stays strict on free-only constraints
  - no food/drink section or food stops appear
  - the result does not fake expensive highlights
- Checklist:
  - validator catches any paid content
  - recommendation language stays consistent with low-budget constraints
  - output remains useful even with tight filters

## Case 5: Follow-Up Revision

- Goal: prove that follow-up planning revises selectively instead of rebuilding everything
- Status: `needs review`
- Baseline:
  - Use a successful result from `Case 1` or `Case 2`
- Follow-up:
  - Example: `Make Saturday more elegant, reduce sightseeing, and add a stronger bar recommendation.`
- Expected outcome:
  - only affected parts change
  - unchanged good selections remain stable
  - report refresh stays aligned with the revised plan
- Checklist:
  - follow-up preserves unaffected days where possible
  - validator does not flag new inconsistencies after the revision
  - markdown report reflects the updated structure

## Readiness Scale

- `ready`: stable enough for a live demo
- `needs review`: promising, but must be rerun and checked
- `blocked`: currently unsuitable for presentation

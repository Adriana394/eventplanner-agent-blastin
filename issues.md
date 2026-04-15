# Open Issues

## 2026-04-15

### Itinerary stop type inconsistent with linked item
- Status: open
- Seen in: Demo Case 2
- Summary: An itinerary stop can reference a food/drink venue via `linked_item_name`, but still be labeled with `stop_type = "sightseeing"`.
- Example:
  - `title`: `Relax and brunch at Five Elephant in Kreuzberg`
  - `linked_item_name`: `Five Elephant`
  - `stop_type`: `sightseeing`
  - `Five Elephant` exists in `food_and_drink_spots`, not in `sightseeing_spots`
- Impact:
  - Visible user-facing inconsistency in the itinerary
  - Validator correctly flags it, but the repair loop did not resolve it in this case
- Likely source:
  - Planner or repair output
  - Not caused by `_insert_default_food_structure()`, which only creates `food` stops
- Possible fix later:
  - Add deterministic post-processing that aligns `itinerary.stop_type` with the referenced structured item when the mapping is unambiguous

# Step 4 — tag coverage of the 3 thin rules, v6 → v6b (2026-10-24)

`kb_gemini_curated_v6b` = `curated_data_v6` after round 4 and the manual untags A1/A2
(`data_pipeline/manual_untags_v6.json`), ingested 2026-10-24: 2,197 rows (v6: 1,845, untouched).
v6 = the files as ingested (`f6fdf0b`, trial + round 1 + round 2a). v6b adds round 3 (4 sources,
curated 2026-10-19, never ingested before) and round 4 (9 sources). Counts straight from the JSON
(`data_pipeline/tag_coverage.py` logic); "facts" = items after the gate's near-dup clustering
(token Jaccard ≥ 0.72), i.e. what can fill distinct quota slots.

## Coverage (items, facts in brackets)

| rule | kind | v6 | v6b | ≥5? | quota (MAX_PER_KIND) | quota fillable? |
|---|---|---|---|---|---|---|
| partial_pushup | mistake | 2 | **8** | ✓ | 3 | ✓ |
| partial_pushup | consequence | 1 | **4** | ✗ | 2 | ✓ |
| partial_pushup | principle | 5 | **13** | ✓ | 2 | ✓ |
| partial_pushup | finding | 2 | **4** | ✗ | 2 | ✓ |
| shallow_lunge | mistake | 3 | **7** | ✓ | 3 | ✓ |
| shallow_lunge | consequence | 1 | **2** | ✗ | 2 | ✓ (exactly) |
| shallow_lunge | principle | 9 (8) | **12** (11) | ✓ | 2 | ✓ |
| shallow_lunge | finding | 7 | **8** | ✓ | 2 | ✓ |
| straight_back_leg | mistake | 0 | **2** | ✗ | 3 | ✗ (2 of 3) |
| straight_back_leg | consequence | 0 | **2** | ✗ | 2 | ✓ (exactly) |
| straight_back_leg | principle | 4 | **8** | ✓ | 2 | ✓ |
| straight_back_leg | finding | 0 | **0** | ✗ | 2 | ✗ |

- Cells at ≥5: 3/12 → 7/12. Cells whose quota the tagged pool can fill: 6/12 → 10/12.
- "Fillable" is a ceiling: a tagged chunk still has to pass RELATIVE_MARGIN to reach the
  context (v6: 1 of 4 straight_back_leg principles did). Step 5 measures what actually arrives.
- Kinds that went from 0 to >0 (strict used to leave them empty): straight_back_leg mistake and
  consequence.
- **Still 0: straight_back_leg finding** → TAG_MODE strict keeps it empty on v6b as on v6
  (prefer would refill it with other rules' findings, as in LU-004).

## Tag review

Applied before ingest (user approved): A1 untag forward_trunk_lean from Riemann's "upright
trunk increases knee load" consequence (describes the correct form); A2 untag partial_pushup
from ATHLEAN-X's "full ROM and full lockout … ~60%" finding (lockout is outside the rule).
Kept on purpose: A3 ATHLEAN-X "~60%, 100 down to 40" finding (anecdotal number, partial_pushup);
A4 Gao 2022 "leaning forward increases knee shear" consequence (forward_trunk_lean, conflicts
with Riemann); the elitefts rear-foot cue (tied to the back-knee bend in the item text).

Checked, nothing to do: Gao's "be cautious about a long-step lunge" (citing Escamilla) was not
extracted as an item, and all 7 knee-past-toes items from Gao are untagged; Cathe's "half-way
down and hold" was not extracted; ATHLEAN-X's top-lockout mistake and principle are untagged.

Found in this pass (round 3, already in v6b):
- **B1** Patellofemoral (round 3), shallow_lunge principle: "Flex the front knee to approximately
  100 degrees during the lunge descent." A study protocol, worded as a cue, and shallower than
  the coached 90° (the rule fires above 105°). Not a contradiction of the rule, but not its fix.
  Left in v6b; if step 5 shows it in a shallow_lunge context, label it and untag the row.
- Round 3 straight_back_leg principle "Allow the trail knee to bend until it lightly makes
  contact with the ground": kept (light contact, not slamming; same call as BOXROX).

## Check of the file / document counts

ingest log: 52 JSON files. Split: 59 documents. 52 files = 44 single-document files + 4
`urls_curated_detailed.json` (15 pages) + 4 files of the general NSCA basics manual (1 document
routed into 3 exercise folders) → 60 source documents → 59 split units, because
`Lorenzetti2020_Correction` is grouped with `Lorenzetti2018` (`GROUPS` in `eval/make_split.py`).

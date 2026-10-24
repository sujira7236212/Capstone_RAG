# Step 2 — TAG_MODE strict on KB v6, offline (2026-10-24)

No API calls. Strict context derived from `compare_output/baseline_v14/compare_result_v14_<ex>.json`
(TAG_MODE prefer, kb_gemini_curated_v6, QUERIES profile) by
`eval/strict_offline_from_compare.py`. Output: `compare_output/strict_v6b/context_v6_strict_<ex>.json`
(baseline "v6 strict" for step 5; generated answers not carried over).

## Which (fault, kind) strict changes

Only pairs with a fault code and no chunk tagged for it (v14 metrics `tagged: false`):

| exercise | sessions | skipped (fault/kind) |
|---|---|---|
| lunge | LU-004, LU-005 | straight_back_leg / mistake, finding, consequence |
| push-up, squat, bicep-curl | — | none ("general principles" has no code → same as prefer) |

Correction (found in step 4): the coverage in the plan (straight_back_leg 0/0/6/0,
shallow_lunge 3/1/10/7, partial_pushup 3/1/7/2) includes curation round 3, which was
never ingested. Ingested v6 (`f6fdf0b`) = 0/0/4/0 · 3/1/9/7 · 2/1/5/2. The (fault, kind)
pairs with zero tags are the same either way, so the result below does not change.

## Control: byte-identical contexts

| exercise | sessions | identical (sha1) |
|---|---|---|
| lunge | LU-001, 002, 003, 006 | 4/4 |
| push-up | PU-001..004 | 4/4 |
| squat | SQ-001..006 | 6/6 |
| bicep-curl | BC-001..004 | 4/4 |

## Target: straight_back_leg blocks (labels proposed, pending review — `eval/labels_straight_back_leg_v6.json`)

| # | kind | chunk | in | proposed label | prefer | strict |
|---|---|---|---|---|---|---|
| 1 | principle | Lower the rear knee toward the ground during the descent | 004, 005 | **relevant** | ✓ | ✓ |
| 2 | mistake | spinal flexion or excessive spinal extension | 004, 005 | irrelevant | ✓ | — |
| 3 | mistake | front knee forward past the toes (NSCA basics) | 004, 005 | irrelevant (? EFKF, oq1) | ✓ | — |
| 4 | mistake | front knee translates in front of toes (Zellmer 2019) | 004 | irrelevant (? EFKF, oq1) | ✓ | — |
| 5 | mistake | excessive anterior knee translation (Loading Positions) | 005 | irrelevant (? EFKF, oq1) | ✓ | — |
| 6 | consequence | lead foot/knee turned inward → knee torque | 004, 005 | irrelevant | ✓ | — |
| 7 | finding | lunge joint kinematics (calcaneal eversion …) | 004, 005 | irrelevant | ✓ | — |
| 8 | consequence | back knee/foot rotated outward → knee torque | 004, 005 | wrong_fault (rotation) | ✓ | — |
| 9 | finding | forward trunk lean → more hamstrings | 004, 005 | wrong_fault (FTL) | ✓ | — |

## Metrics (straight_back_leg label only)

| session | arm | chunks | matching rule | not matching (wrong_fault / irrelevant) | precision |
|---|---|---|---|---|---|
| LU-004 | v6 prefer | 8 | 1 | 7 (2 / 5) | 0.13 |
| LU-004 | v6 strict | 1 | 1 | 0 | 1.00 |
| LU-005 | v6 prefer | 8 | 1 | 7 (2 / 5) | 0.13 |
| LU-005 | v6 strict | 1 | 1 | 0 | 1.00 |

Matching chunks 1 → 1 (recall not reduced). Per kind: mistake 3→0, finding 2→0,
consequence 2→0, principle 1→1. LU-005's other 25 blocks (3 faults) are identical.

Still thin: only 1 of the 4 principle items tagged straight_back_leg in v6 reaches the context
(the other 3 are outside RELATIVE_MARGIN of the best hit — by elimination: the principle quota of 2 is not
full and none of them is a near-dup, max Jaccard 0.23) — unchanged by A; a gap for steps 3–5.

## LU-005 is exact here, not an estimate

The general caveat holds (a fault's fallback can claim a chunk via the shared near-dup
list before a later fault sees it), but it does not bite in this session:
1. Faults are retrieved in sorted order; straight_back_leg sorts last of the 4, so its
   fallback chunks could not have been taken from the other faults.
2. Inside straight_back_leg, principle runs after the 3 skipped kinds; the max token
   Jaccard of its tagged principle candidates (4 in v6; checked all 6 incl. round 3) against
   the 7 removed blocks is 0.24
   (dup threshold 0.72), so none could have been dropped as a dup of them.

Remaining assumption: a live strict run re-embeds the same queries; Gemini embedding
drift would affect both arms equally.

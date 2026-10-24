# Step 5 — new data, context layer: v6 strict vs v6b strict (2026-10-24)

No LLM call. A = `compare_output/strict_v6b/context_v6_strict_<ex>.json` (step 2, offline from v14).
B = `compare_output/strict_v6b/context_v6b_strict_<ex>.json` (`test_rag_compare.py --context-only
--tag-mode strict --collection kb_gemini_curated_v6b`, live; only the query embeddings were paid).
Lunge and push-up only; squat and bicep-curl have the same chunk set in both collections.
Tools: `eval/diff_strict_contexts.py` (block diff), `eval/score_target_labels.py` (metrics),
labels `eval/labels_target_rules_v6b.json` (proposed, pending review).

v6b = v6 + curation round 3 (4 files, never ingested before) + round 4 (9 files), with the
manual untags A1, A2 applied.

## What is held constant

| check | result |
|---|---|
| the 1,845 v6 chunks inside v6b: vectors | identical (max cosine distance 0) |
| same chunks: fault_tags | identical (0 changed) |
| query embeddings | (fault, kind) pairs whose nearest chunk is old: `best` equal to 1e-9 in 18/18 |
| changed `best` | 30 pairs, every one smaller (a new chunk is now nearest) |

So every context change comes from the new chunks: they take quota slots, or they become
a query's nearest hit, which moves `rel = distance - that query's best` for every old chunk
of that query (QUERIES profile ranks by the smallest `rel` over the queries) and can
reorder old chunks among themselves.

## Target rules (labels proposed)

| session | rule | arm | blocks | matching | wrong_fault | irrelevant | contradicts | precision |
|---|---|---|---|---|---|---|---|---|
| LU-001 | shallow_lunge | A | 7 | 5 | 1 | 1 | 0 | 0.71 |
| | | B | 9 | 6 | 2 | 1 | 0 | 0.67 |
| LU-005 | shallow_lunge | A | 7 | 4 | 1 | 2 | 0 | 0.57 |
| | | B | 9 | 6 | 2 | 1 | 0 | 0.67 |
| LU-004 / 005 | straight_back_leg | A | 1 | 1 | 0 | 0 | 0 | 1.00 |
| | | B | 4 | 4 | 0 | 0 | 0 | 1.00 |
| PU-002 / 003 | partial_pushup | A | 6 | 4 | 0 | 2 | 0 | 0.67 |
| | | B | 9 | 9 | 0 | 0 | 0 | 1.00 |

Matching blocks per kind, A → B:

| rule (session) | mistake | consequence | principle | finding |
|---|---|---|---|---|
| shallow_lunge (LU-001) | 2 → 3 | 0 → 1 | **1 → 0** | 2 → 2 |
| shallow_lunge (LU-005) | 2 → 3 | 0 → 1 | 0 → 0 | 2 → 2 |
| straight_back_leg | 0 → 1 | 0 → 1 | 1 → 2 | 0 → 0 (strict skip) |
| partial_pushup | 0 → 3 | 1 → 2 | 2 → 2 | 1 → 2 |

### The label that decides criterion 3

#24 (BOXROX, new) "Proper lunge depth occurs when the back knee gently touches or comes very
close to the ground" and #27 (Trunk and Shank, in both arms) "descend until the trail knee is
just prior to touching the ground" define lunge depth by the rear knee. The shallow_lunge card
excludes "advice about the rear knee is a different rule", so both are proposed
`wrong_fault (straight_back_leg)`. Under that reading wrong_fault goes 1 → 2. If depth via the
rear knee is in scope, both are `relevant` and shallow_lunge becomes:

| session | A precision | B precision | wrong_fault |
|---|---|---|---|
| LU-001 | 0.86 | 0.89 | 0 → 0 |
| LU-005 | 0.71 | 0.89 | 0 → 0 |

LU-001's principle 1 → 0 is the same item: #24 displaced #25 (Bezerra, "front knee
about 90 to 100 degrees"), the only front-knee depth principle in that context.

## Pass criteria (set before the run)

| criterion | partial_pushup | shallow_lunge | straight_back_leg |
|---|---|---|---|
| matching up in ≥ 1 kind | pass (3 kinds) | pass (2 kinds) | pass (3 kinds) |
| precision drop ≤ 0.05 | pass (+0.33) | pass (LU-001 −0.05 → 0.048, LU-005 +0.10) | pass (=) |
| wrong_fault not up | pass (0 → 0) | **fail 1 → 2 as proposed; pass if #24/#27 relevant** | pass (0 → 0) |
| contradicts_rule = 0 | pass | pass | pass |

Control: see below. Every change is from the new chunks (vectors and query embeddings are
constant), so all of them can be explained.

## Control sessions (no target rule)

All five changed.

| session | change | from |
|---|---|---|
| LU-002 excessive_front_knee_flexion | 4 old blocks out, 4 new in | round 3 (fatigue, Patellofemoral) |
| LU-003 forward_trunk_lean | 9 out, 9 in (8 new + 1 old) | round 4 (BOXROX, Gao, Ladera Ranch, Riemann), round 3 (Patellofemoral, fatigue) |
| LU-006 clean (general principles) | 2 out, 2 in | BOXROX, Patellofemoral |
| PU-001 hip_sag_or_pike | 3 out, 3 in | BOXROX push-up, Biomechanical evaluation (r3), Cathe |
| PU-004 clean | 1 out, 1 in | Biomechanical evaluation (r3) |

The one old chunk that enters (LU-003/005: Bezerra "leaning the trunk forward increases
lumbar longissimus activation") is the `rel` reordering above, not a new chunk.

Two new control items to watch, neither labelled contradicts:
- LU-006, BOXROX: "Lunge only as far as allows secure footing and balance". In the source
  this is the fix for *steps too long* (step length), but the curated item lost that context
  and can be read as "go only as deep as balance allows".
- LU-002, fatigue paper: "Allowing the front knee to translate forward past the toes increases
  stress on the knee joint", not tied to over-bending (excessive_front_knee_flexion oq1).

## Gaps and caveats

- straight_back_leg finding still has 0 tagged chunks: strict still skips it in v6b.
- Experience Life's two straight_back_leg items (long stance → rear knee does not bend; more
  pressure on the back knee) are tagged but not in the context. Neither kind is full (mistake
  1/3, consequence 1/2), so by elimination they fall outside RELATIVE_MARGIN (a dup is unlikely);
  confirming needs a traced run (query embeddings again).
- 5 of the 31 labelled blocks come from test-split documents (#5, #9, #10 Cathe / BOXROX
  push-up, #22 Gao, #31 Patellofemoral). The numbers above use the whole v6b.
- #4 (ATHLEAN-X, A3, "full range reduces reps by ~60%") is labelled relevant but debatable:
  it explains why people shorten reps, and a generator could read it the other way.
- Labels are mine against the cards. 6 (session, rule) rows but only 4 distinct target-block
  sets (LU-004/005 straight_back_leg and PU-002/003 are identical pairs). No answer quality
  measured yet.

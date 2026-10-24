# Read-through of the Groq answers, three thin rules (2026-10-25)

Not a judged result: one reader (Claude), not blind to the arm, one sample per arm.
Answers: `compare_output/strict_v6b/groq_targets_qwen.json` (`eval/generate_groq.py`, qwen/qwen3.8-27b on
Groq free tier, temperature 0.7, the v14 prompt unchanged). Sessions:
`mock_data/mock_sessions_targets_{lunge,push-up}.json` (`mock_data/build_target_sessions.py`,
5 single-fault variants per rule: late / most / improving / early / every). Contexts reused from
compare_output/ (single-fault sessions retrieve exactly what LU-001/004 and PU-002 retrieved).

For shallow_lunge and partial_pushup, v6 prefer = v6 strict (same context), so one answer
covers both; strict only changes straight_back_leg.

## What went wrong, per arm (count of sessions out of 5)

| rule | problem | no-RAG | v6 prefer | v6 strict | v6b strict |
|---|---|---|---|---|---|
| straight_back_leg | knee torque / rotation in "why it matters" (the LU-004 failure) | 0 | **3** (108, 109, 110) | 0 | 0 |
| | wrong limb (explains a locked *front* knee) | 1 (110) | 0 | 0 | 0 |
| | "take a longer / wider step" (card: a long step is a cause) | 0 | 0 | 1 (109) | 1 (108, "step wider") |
| | cue "drive the back heel down" | 1 (106) | 0 | 1 (110) | 1 (110) |
| | mechanism matches the card (body pushed forward, load onto the front knee) | partly, generic | partly | partly, generic | **5/5**, EliteFTS wording |
| partial_pushup | explains a missed **top lockout** instead of depth (card excludes) | 1 (101) | **3** (101, 103, 104 partly) | = prefer | 0 |
| | "half-rep" drill | 1 (102) | 3 (101, 103, 104) | = prefer | 0 |
| shallow_lunge | "glutes not engaged → knee shear" (chunk #17, labelled irrelevant) | 0 | 1 (101) | = prefer | 1 (105) |
| | "lengthen the stride to go deeper" | 0 | 1 (103) | = prefer | 0 |
| any | model printed its own reasoning ("wait, 7 is lower than 8?") | 0 | 0 | 0 | 1 (LU-106) |

## Reading

- **Strict (A) on straight_back_leg:** the torque/rotation explanation appears only in v6
  prefer (3/5) and in no arm without the two rotation chunks (#6, #8 in
  `eval/labels_straight_back_leg_v6.json`). Strict removes it. With only one chunk left, v6
  strict answers look like no-RAG answers: generic, plausible, one wrong step-length tip.
- **partial_pushup in v6 is a labelling problem, not a strict one:** the two Schwartzkopf TSPU
  chunks ("only rising one to two inches from the floor", #6 and #11 in
  `eval/labels_target_rules_v6b.json`, proposed irrelevant) are tagged `partial_pushup`, so
  strict keeps them, and the model reads them as "did not push back up" → lockout advice and
  half-rep drills. v6b's new chunks push them out of the context; the lockout reading is gone
  (0/5). Untagging those two items would fix v6 as well.
- **New data (v6b):** the clearest gain is straight_back_leg (card mechanism in every answer)
  and partial_pushup (no wrong-fault reading). shallow_lunge: all three arms are similar;
  v6b adds the load and range-of-motion points from Riemann / BOXROX, and keeps the Jaeggi
  shear-force chunk in both arms.
- **no-RAG is not weak on these rules**: it got the wrong limb once and the lockout reading
  once; otherwise sound and generic.

## Limits

One unblinded reader, 1 sample per arm, 5 sessions per rule, a stand-in generator (qwen, not
Gemini 3.5 flash-lite). Counts above are patterns to check in the blind pairwise run, not
results.

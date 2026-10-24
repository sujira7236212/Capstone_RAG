# Retrieval golden-set evaluation

gates: CANDIDATE_K=12, MAX_PER_KIND={'mistake': 3, 'finding': 2, 'principle': 2}, ABS_DISTANCE_CAP={'mistake': 0.4, 'finding': 0.4, 'principle': 0.4}, RELATIVE_MARGIN=0.03, NEAR_DUP_JACCARD=0.72
golden: `eval/golden_chunks.json` · mock: `mock_data/mock_sessions.json`

`best` = closest chunk of that kind in the whole collection (before the gate). `good` = kept chunk matching a must_hit pattern, `bad` = matching a must_not_hit pattern (a different fault, labelled as this one), `neutral` = neither.

### kb_gemini_curated_v4 — mode: single

| exercise | fault | kind | best | kept | good | bad | neutral | must_hit found | missing must_hit |
|---|---|---|---|---|---|---|---|---|---|
| squat | butt wink | mistake | 0.019 | 2 | 2 | 0 | 0 | 2/4 | Tailbone tucking; neutral spine curvature to flex during a deep squat |
| squat | butt wink | finding | 0.099 | 2 | 1 | 0 | 1 | 1/1 |  |
| squat | butt wink | principle | 0.138 | 2 | 0 | 0 | 2 | 0/2 | neutral pelvic tilt; neutral, slightly lordotic spine |
| squat | knee valgus | mistake | 0.032 | 3 | 3 | 0 | 0 | 3/5 | knock-kneed; Knee valgus (knees caving inward) |
| squat | knee valgus | finding | 0.061 | 2 | 1 | 0 | 1 | 1/3 | control knee valgus and foot pronation; squats with medial knee displacement compared with a neutrally aligned squat |
| squat | knee valgus | principle | 0.088 | 2 | 2 | 0 | 0 | 2/3 | Keep knees in line with feet |
| squat | partial squat | mistake | 0.052 | 1 | 1 | 0 | 0 | 1/2 | insufficient squat depth |
| squat | partial squat | finding | 0.153 | 2 | 0 | 0 | 2 | 0/2 | Compressive forces in the knee may be higher in a partial squat; A deep squat is defined by a knee joint angle |
| squat | partial squat | principle | 0.143 | 2 | 1 | 0 | 1 | 1/1 |  |
| push-up | hip sag | mistake | 0.079 | 1 | 1 | 0 | 0 | 1/4 | hip sagging; sagging of the lower back; body in a straight line |
| push-up | hip sag | finding | 0.155 | 2 | 0 | 0 | 2 | 0/1 | Abdominal muscles dominate contributions to vertebral joint stiffness |
| push-up | hip sag | principle | 0.152 | 2 | 0 | 0 | 2 | 0/1 | Abdominal muscles are the primary contributors to maintaining vertebral joint stiffness |
| push-up | partial range of motion | mistake | 0.063 | 1 | 1 | 0 | 0 | 1/1 |  |
| push-up | partial range of motion | finding | 0.120 | 2 | 1 | 0 | 1 | 1/1 |  |
| push-up | partial range of motion | principle | 0.119 | 2 | 0 | 0 | 2 | 0/1 | depth of 90 degrees of elbow flexion |
| lunge | excessive forward trunk lean | mistake | 0.071 | 3 | 0 | 1 🔴 | 2 | 0/4 | marked trunk lean; Leaning the torso forward; Forward torso lean during the downward phase; gaze downward, which increases trunk flexion |
| lunge | excessive forward trunk lean | finding | 0.115 | 2 | 0 | 0 | 2 | 0/2 | upright trunk tends to create; downward direction of gaze increases trunk flexion |
| lunge | excessive forward trunk lean | principle | 0.110 | 2 | 0 | 0 | 2 | 0/3 | Maintain an upright trunk; Keep the upper body upright; forward trunk lean increases biceps femoris |
| lunge | shallow lunge | mistake | 0.076 | 3 | 1 | 0 | 2 | 1/2 | step is too short |
| lunge | shallow lunge | finding | 0.107 | 2 | 0 | 0 | 2 | 0/2 | length of the lunge is about 2x hip width; short step length results in joint forces almost two times higher |
| lunge | shallow lunge | principle | 0.117 | 2 | 1 | 0 | 1 | 1/2 | Step length |
| lunge | insufficient back knee flexion | mistake | 0.063 | 3 | 0 | 0 | 3 | 0/1 | preventing knee flexion to 90 degrees |
| lunge | insufficient back knee flexion | finding | 0.087 | 2 | 0 | 0 | 2 | 0/1 | back knee ending at approximately a 90-degree angle |
| lunge | insufficient back knee flexion | principle | 0.109 | 2 | 0 | 0 | 2 | 0/1 | until the back knee is just above the floor |
| bicep-curl | elbow flare | mistake | 0.037 | 2 | 2 | 0 | 0 | 2/4 | elbows to drift forward or away from the waist; elbows to pull forward |
| bicep-curl | elbow flare | finding | 0.187 | 2 | 0 | 0 | 2 | n/a |  |
| bicep-curl | elbow flare | principle | 0.126 | 2 | 2 | 0 | 0 | 2/3 | Keep the elbows close to the body |
| bicep-curl | partial range of motion | mistake | 0.068 | 3 | 2 | 1 🔴 | 0 | 2/6 | full range of motion at the elbow joint; fully extend the elbows at the bottom; limited range of motion; complete arm extension at the bottom |
| bicep-curl | partial range of motion | finding | 0.100 | 2 | 0 | 0 | 2 | n/a |  |
| bicep-curl | partial range of motion | principle | 0.129 | 2 | 1 | 0 | 1 | 1/4 | full range of motion from complete arm extension; Start the bicep curl with the elbow in full extension; Start the movement with the elbow joint in full extension |

### kb_gemini_curated_v4 — mode: session

| exercise | fault | kind | best | kept | good | bad | neutral | must_hit found | missing must_hit |
|---|---|---|---|---|---|---|---|---|---|
| squat | butt wink | mistake | 0.019 | 2 | 2 | 0 | 0 | 2/4 | Tailbone tucking; neutral spine curvature to flex during a deep squat |
| squat | butt wink | finding | 0.099 | 2 | 1 | 0 | 1 | 1/1 |  |
| squat | butt wink | principle | 0.138 | 2 | 0 | 0 | 2 | 0/2 | neutral pelvic tilt; neutral, slightly lordotic spine |
| squat | partial squat | mistake | 0.052 | 1 | 1 | 0 | 0 | 1/2 | insufficient squat depth |
| squat | partial squat | finding | 0.153 | 2 | 0 | 0 | 2 | 0/2 | Compressive forces in the knee may be higher in a partial squat; A deep squat is defined by a knee joint angle |
| squat | partial squat | principle | 0.143 | 2 | 1 | 0 | 1 | 1/1 |  |
| lunge | excessive forward trunk lean | mistake | 0.071 | 3 | 0 | 1 🔴 | 2 | 0/4 | marked trunk lean; Leaning the torso forward; Forward torso lean during the downward phase; gaze downward, which increases trunk flexion |
| lunge | excessive forward trunk lean | finding | 0.115 | 2 | 0 | 0 | 2 | 0/2 | upright trunk tends to create; downward direction of gaze increases trunk flexion |
| lunge | excessive forward trunk lean | principle | 0.110 | 2 | 0 | 0 | 2 | 0/3 | Maintain an upright trunk; Keep the upper body upright; forward trunk lean increases biceps femoris |
| lunge | insufficient back knee flexion | mistake | 0.063 | 3 | 0 | 3 🔴 | 0 | 0/1 | preventing knee flexion to 90 degrees |
| lunge | insufficient back knee flexion | finding | 0.087 | 2 | 0 | 0 | 2 | 0/1 | back knee ending at approximately a 90-degree angle |
| lunge | insufficient back knee flexion | principle | 0.109 | 2 | 0 | 0 | 2 | 0/1 | until the back knee is just above the floor |
| push-up | (no errors - principle path, not scored) | | | | | | | | |
| bicep-curl | elbow flare | mistake | 0.037 | 2 | 2 | 0 | 0 | 2/4 | elbows to drift forward or away from the waist; elbows to pull forward |
| bicep-curl | elbow flare | finding | 0.187 | 2 | 0 | 0 | 2 | n/a |  |
| bicep-curl | elbow flare | principle | 0.126 | 2 | 2 | 0 | 0 | 2/3 | Keep the elbows close to the body |
| bicep-curl | partial range of motion | mistake | 0.068 | 3 | 2 | 1 🔴 | 0 | 2/6 | full range of motion at the elbow joint; fully extend the elbows at the bottom; limited range of motion; complete arm extension at the bottom |
| bicep-curl | partial range of motion | finding | 0.100 | 2 | 0 | 0 | 2 | n/a |  |
| bicep-curl | partial range of motion | principle | 0.129 | 2 | 1 | 0 | 1 | 1/4 | full range of motion from complete arm extension; Start the bicep curl with the elbow in full extension; Start the movement with the elbow joint in full extension |

**single summary (kb_gemini_curated_v4)** — faults with ≥1 correct mistake chunk: **8/10** · context chunks: 62 = good 23 / bad **2** / neutral 37 · precision(good/kept) = 0.37
  bad chunks under: bicep-curl/partial range of motion, lunge/excessive forward trunk lean

**session summary (kb_gemini_curated_v4)** — faults with ≥1 correct mistake chunk: **4/6** · context chunks: 38 = good 12 / bad **5** / neutral 21 · precision(good/kept) = 0.32
  bad chunks under: bicep-curl/partial range of motion, lunge/excessive forward trunk lean, lunge/insufficient back knee flexion

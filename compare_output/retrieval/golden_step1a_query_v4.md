# Retrieval golden-set evaluation

gates: CANDIDATE_K=12, MAX_PER_KIND={'mistake': 3, 'finding': 2, 'principle': 3}, ABS_DISTANCE_CAP={'mistake': 0.55, 'finding': 0.4, 'principle': 0.45}, RELATIVE_MARGIN=0.2, NEAR_DUP_JACCARD=0.72
golden: `eval/golden_chunks.json` · mock: `mock_data/mock_sessions.json`

`best` = closest chunk of that kind in the whole collection (before the gate). `good` = kept chunk matching a must_hit pattern, `bad` = matching a must_not_hit pattern (a different fault, labelled as this one), `neutral` = neither.

### kb_local_curated_v4 — mode: single

| exercise | fault | kind | best | kept | good | bad | neutral | must_hit found | missing must_hit |
|---|---|---|---|---|---|---|---|---|---|
| squat | butt wink | mistake | 0.120 | 3 | 3 | 0 | 0 | 3/4 | neutral spine curvature to flex during a deep squat |
| squat | butt wink | finding | 0.329 | 2 | 1 | 1 🔴 | 0 | 1/1 |  |
| squat | knee valgus | mistake | 0.154 | 3 | 3 | 0 | 0 | 2/5 | Knee valgus (inward knee collapse); knock-kneed; Knee valgus (knees caving inward) |
| squat | knee valgus | finding | 0.307 | 2 | 1 | 1 🔴 | 0 | 1/3 | heel lift eliminated medial knee displacement; squats with medial knee displacement compared with a neutrally aligned squat |
| squat | partial squat | mistake | 0.258 | 3 | 1 | 1 🔴 | 1 | 1/2 | insufficient squat depth |
| squat | partial squat | finding | 0.370 | 1 | 1 | 0 | 0 | 1/2 | A deep squat is defined by a knee joint angle |
| push-up | hip sag | mistake | 0.133 | 2 | 2 | 0 | 0 | 2/4 | sagging of the lower back; body in a straight line |
| push-up | hip sag | finding | 0.357 | 1 | 1 | 0 | 0 | 1/1 |  |
| push-up | partial range of motion | mistake | 0.168 | 2 | 1 | 1 🔴 | 0 | 1/1 |  |
| push-up | partial range of motion | finding | 0.264 | 2 | 1 | 1 🔴 | 0 | 1/1 |  |
| lunge | excessive forward trunk lean | mistake | 0.256 | 3 | 2 | 0 | 1 | 2/4 | Forward torso lean during the downward phase; gaze downward, which increases trunk flexion |
| lunge | excessive forward trunk lean | finding | 0.338 | 1 | 1 | 0 | 0 | 1/2 | downward direction of gaze increases trunk flexion |
| lunge | shallow lunge | mistake | 0.304 | 3 | 1 | 1 🔴 | 1 | 1/2 | short step length |
| lunge | shallow lunge | finding | 0.306 | 2 | 0 | 0 | 2 | 0/2 | length of the lunge is about 2x hip width; short step length results in joint forces almost two times higher |
| lunge | insufficient back knee flexion | mistake | 0.256 | 3 | 0 | 2 🔴 | 1 | 0/1 | preventing knee flexion to 90 degrees |
| lunge | insufficient back knee flexion | finding | 0.305 | 2 | 0 | 2 🔴 | 0 | 0/1 | back knee ending at approximately a 90-degree angle |
| bicep-curl | elbow flare | mistake | 0.057 | 2 | 2 | 0 | 0 | 2/4 | elbows to drift forward or away from the waist; elbows to pull forward |
| bicep-curl | elbow flare | finding | 0.442 | 0 | 0 | 0 | 0 | n/a |  |
| bicep-curl | partial range of motion | mistake | 0.269 | 3 | 3 | 0 | 0 | 3/6 | full range of motion at the elbow joint; fully extend the elbows at the bottom; limited range of motion |
| bicep-curl | partial range of motion | finding | 0.407 | 0 | 0 | 0 | 0 | n/a |  |

    squat      butt wink                       mistake  GOOD  Lumbar flexion (butt wink) at the bottom of the squat.
    squat      butt wink                       mistake  GOOD  Posterior pelvic tilt ('Butt Wink') where the pelvis tucks under and the low back rounds at the bottom of the squat.
    squat      butt wink                       mistake  GOOD  Tailbone tucking or tilting backward (butt wink) at the bottom of the squat.
    squat      butt wink                       finding  GOOD  Flexing at the spine before 1208 (120 degrees) of hip flexion when squatting may indicate restriction in the posterior fibers of the iliotibial band or lack of lumbar control.
    squat      butt wink                       finding  BAD   Control squats were performed to 90 degrees of flexion.
    squat      knee valgus                     mistake  GOOD  Medial knee displacement (knee valgus) during double-legged squats.
    squat      knee valgus                     mistake  GOOD  Knees collapsing inward (valgus collapse) during the squat.
    squat      knee valgus                     mistake  GOOD  Excessive medial knee displacement (knee valgus) during single-leg squats or landings.
    squat      knee valgus                     finding  GOOD  A lack of strength in the medial gastrocnemius, tibialis anterior, and/or tibialis posterior decreases the athlete's ability to control knee valgus and foot pronation motions and may contribute to excessive medial knee displacement and dynamic valgus (1).
    squat      knee valgus                     finding  BAD   The knee joint displaced approximately 0.17 m anteriorly compared with neutral in the malaligned squat condition.
    squat      partial squat                   mistake  GOOD  Squatting too shallow, failing to bring the thighs at least parallel to the ground.
    squat      partial squat                   mistake  BAD   Medial knee displacement (knee-valgus collapse) during double-legged squats and single-leg squats.
    squat      partial squat                   mistake  neut  Utilizing shallow squat depths (0-30 degrees) when trying to target mid-range quadriceps activation.
    squat      partial squat                   finding  GOOD  Compressive forces in the knee may be higher in a partial squat than in a deep squat.
    push-up    hip sag                         mistake  GOOD  Allowing the hips to sag
    push-up    hip sag                         mistake  GOOD  Excessive hip sagging
    push-up    hip sag                         finding  GOOD  Abdominal muscles dominate contributions to vertebral joint stiffness during the push-up (Howarth, Beach, & Callaghan, 2008).
    push-up    partial range of motion         mistake  GOOD  Failing to achieve the correct depth of 90 degrees elbow flexion.
    push-up    partial range of motion         mistake  BAD   Performing a push-up with the forearm in 90 degrees of internal rotation, which increases posterior and varus elbow shear forces.
    push-up    partial range of motion         finding  GOOD  The correct depth for a push-up repetition was defined as 90 degrees (noted as 900 in text) of elbow flexion.
    push-up    partial range of motion         finding  BAD   Donkers et al. (7) reported axial elbow joint reaction forces of 37% and 38% BW in the up and down positions of the traditional push-up, respectively.
    lunge      excessive forward trunk lean    mistake  GOOD  Excessive trunk movement or marked trunk lean.
    lunge      excessive forward trunk lean    mistake  GOOD  Leaning the torso forward or backward.
    lunge      excessive forward trunk lean    mistake  neut  Spinal flexion (rounding the back) during the lunge.
    lunge      excessive forward trunk lean    finding  GOOD  An upright trunk tends to create what is often called a 90/90 lunge where both knees at the bottom of the move are 90° angles.
    lunge      shallow lunge                   mistake  GOOD  Lunge step is too short or too long.
    lunge      shallow lunge                   mistake  BAD   Allowing the rear knee to flex during the stride-stance lunge.
    lunge      shallow lunge                   mistake  neut  Lacking necessary mobility at the ankles and hips, or failing to maintain stability at the knees and trunk during the lunge.
    lunge      shallow lunge                   finding  neut  Partial lunge was performed to 50 degrees of knee flexion.
    lunge      shallow lunge                   finding  neut  In a traditional lunge, a moderate step results in the back knee ending at approximately a 90-degree angle.
    lunge      insufficient back knee flexion  mistake  BAD   Allowing the rear knee to flex during the stride-stance lunge.
    lunge      insufficient back knee flexion  mistake  BAD   Medial or lateral movement of the knees during the lunge.
    lunge      insufficient back knee flexion  mistake  neut  Allowing the trailing knee to impact the ground during a lunge.
    lunge      insufficient back knee flexion  finding  BAD   Rotating the back knee or foot outward during a forward lunge increases torque stress in the knee joint.
    lunge      insufficient back knee flexion  finding  BAD   Kinematic data showed a significantly greater knee angle in the forward lunge compared to the backward lunge.
    bicep-curl elbow flare                     mistake  GOOD  Allowing the elbows to flare outward during the curl.
    bicep-curl elbow flare                     mistake  GOOD  Allowing the elbows to drift away from the body during the curl.
    bicep-curl partial range of motion         mistake  GOOD  Failing to start the repetition with the elbow in full extension.
    bicep-curl partial range of motion         mistake  GOOD  Failing to achieve complete arm extension at the bottom of the movement.
    bicep-curl partial range of motion         mistake  GOOD  Failing to start the movement from full elbow extension.

### kb_local_curated_v4 — mode: session

| exercise | fault | kind | best | kept | good | bad | neutral | must_hit found | missing must_hit |
|---|---|---|---|---|---|---|---|---|---|
| squat | butt wink | mistake | 0.120 | 3 | 3 | 0 | 0 | 3/4 | neutral spine curvature to flex during a deep squat |
| squat | butt wink | finding | 0.329 | 2 | 1 | 1 🔴 | 0 | 1/1 |  |
| squat | partial squat | mistake | 0.258 | 3 | 1 | 1 🔴 | 1 | 1/2 | insufficient squat depth |
| squat | partial squat | finding | 0.370 | 1 | 1 | 0 | 0 | 1/2 | A deep squat is defined by a knee joint angle |
| lunge | excessive forward trunk lean | mistake | 0.256 | 3 | 2 | 0 | 1 | 2/4 | Forward torso lean during the downward phase; gaze downward, which increases trunk flexion |
| lunge | excessive forward trunk lean | finding | 0.338 | 1 | 1 | 0 | 0 | 1/2 | downward direction of gaze increases trunk flexion |
| lunge | insufficient back knee flexion | mistake | 0.256 | 3 | 0 | 2 🔴 | 1 | 0/1 | preventing knee flexion to 90 degrees |
| lunge | insufficient back knee flexion | finding | 0.305 | 2 | 0 | 2 🔴 | 0 | 0/1 | back knee ending at approximately a 90-degree angle |
| push-up | (no errors - principle path, not scored) | | | | | | | | |
| bicep-curl | elbow flare | mistake | 0.057 | 2 | 2 | 0 | 0 | 2/4 | elbows to drift forward or away from the waist; elbows to pull forward |
| bicep-curl | elbow flare | finding | 0.442 | 0 | 0 | 0 | 0 | n/a |  |
| bicep-curl | partial range of motion | mistake | 0.269 | 3 | 3 | 0 | 0 | 3/6 | full range of motion at the elbow joint; fully extend the elbows at the bottom; limited range of motion |
| bicep-curl | partial range of motion | finding | 0.407 | 0 | 0 | 0 | 0 | n/a |  |

    squat      butt wink                       mistake  GOOD  Lumbar flexion (butt wink) at the bottom of the squat.
    squat      butt wink                       mistake  GOOD  Posterior pelvic tilt ('Butt Wink') where the pelvis tucks under and the low back rounds at the bottom of the squat.
    squat      butt wink                       mistake  GOOD  Tailbone tucking or tilting backward (butt wink) at the bottom of the squat.
    squat      butt wink                       finding  GOOD  Flexing at the spine before 1208 (120 degrees) of hip flexion when squatting may indicate restriction in the posterior fibers of the iliotibial band or lack of lumbar control.
    squat      butt wink                       finding  BAD   Control squats were performed to 90 degrees of flexion.
    squat      partial squat                   mistake  GOOD  Squatting too shallow, failing to bring the thighs at least parallel to the ground.
    squat      partial squat                   mistake  BAD   Medial knee displacement (knee-valgus collapse) during double-legged squats and single-leg squats.
    squat      partial squat                   mistake  neut  Utilizing shallow squat depths (0-30 degrees) when trying to target mid-range quadriceps activation.
    squat      partial squat                   finding  GOOD  Compressive forces in the knee may be higher in a partial squat than in a deep squat.
    lunge      excessive forward trunk lean    mistake  GOOD  Excessive trunk movement or marked trunk lean.
    lunge      excessive forward trunk lean    mistake  GOOD  Leaning the torso forward or backward.
    lunge      excessive forward trunk lean    mistake  neut  Spinal flexion (rounding the back) during the lunge.
    lunge      excessive forward trunk lean    finding  GOOD  An upright trunk tends to create what is often called a 90/90 lunge where both knees at the bottom of the move are 90° angles.
    lunge      insufficient back knee flexion  mistake  BAD   Allowing the rear knee to flex during the stride-stance lunge.
    lunge      insufficient back knee flexion  mistake  BAD   Medial or lateral movement of the knees during the lunge.
    lunge      insufficient back knee flexion  mistake  neut  Allowing the trailing knee to impact the ground during a lunge.
    lunge      insufficient back knee flexion  finding  BAD   Rotating the back knee or foot outward during a forward lunge increases torque stress in the knee joint.
    lunge      insufficient back knee flexion  finding  BAD   Kinematic data showed a significantly greater knee angle in the forward lunge compared to the backward lunge.
    bicep-curl elbow flare                     mistake  GOOD  Allowing the elbows to flare outward during the curl.
    bicep-curl elbow flare                     mistake  GOOD  Allowing the elbows to drift away from the body during the curl.
    bicep-curl partial range of motion         mistake  GOOD  Failing to start the repetition with the elbow in full extension.
    bicep-curl partial range of motion         mistake  GOOD  Failing to achieve complete arm extension at the bottom of the movement.
    bicep-curl partial range of motion         mistake  GOOD  Failing to start the movement from full elbow extension.

**single summary (kb_local_curated_v4)** — faults with ≥1 correct mistake chunk: **9/10** · context chunks: 40 = good 24 / bad **10** / neutral 6 · precision(good/kept) = 0.60
  bad chunks under: lunge/insufficient back knee flexion, lunge/shallow lunge, push-up/partial range of motion, squat/butt wink, squat/knee valgus, squat/partial squat

**session summary (kb_local_curated_v4)** — faults with ≥1 correct mistake chunk: **5/6** · context chunks: 23 = good 14 / bad **6** / neutral 3 · precision(good/kept) = 0.61
  bad chunks under: lunge/insufficient back knee flexion, squat/butt wink, squat/partial squat

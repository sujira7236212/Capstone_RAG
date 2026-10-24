# Retrieval golden-set evaluation

gates: CANDIDATE_K=12, MAX_PER_KIND={'mistake': 3, 'finding': 2, 'principle': 2}, ABS_DISTANCE_CAP={'mistake': 0.4, 'finding': 0.4, 'principle': 0.4}, RELATIVE_MARGIN=0.06, NEAR_DUP_JACCARD=0.72
golden: `eval/golden_chunks.json` · mock: `mock_data/mock_sessions.json`

`best` = closest chunk of that kind in the whole collection (before the gate). `good` = kept chunk matching a must_hit pattern, `bad` = matching a must_not_hit pattern (a different fault, labelled as this one), `neutral` = neither.

### kb_local_curated_v4 — mode: single

| exercise | fault | kind | best | kept | good | bad | neutral | must_hit found | missing must_hit |
|---|---|---|---|---|---|---|---|---|---|
| squat | butt wink | mistake | 0.120 | 2 | 2 | 0 | 0 | 2/4 | Tailbone tucking; neutral spine curvature to flex during a deep squat |
| squat | butt wink | finding | 0.329 | 2 | 1 | 1 🔴 | 0 | 1/1 |  |
| squat | butt wink | principle | 0.296 | 2 | 2 | 0 | 0 | 2/2 |  |
| squat | knee valgus | mistake | 0.154 | 3 | 3 | 0 | 0 | 2/5 | Knee valgus (inward knee collapse); knock-kneed; Knee valgus (knees caving inward) |
| squat | knee valgus | finding | 0.307 | 2 | 1 | 1 🔴 | 0 | 1/3 | heel lift eliminated medial knee displacement; squats with medial knee displacement compared with a neutrally aligned squat |
| squat | knee valgus | principle | 0.316 | 2 | 1 | 0 | 1 | 1/3 | prevent knees from collapsing inward; knee alignment over the second and third toes |
| squat | partial squat | mistake | 0.258 | 1 | 1 | 0 | 0 | 1/2 | insufficient squat depth |
| squat | partial squat | finding | 0.370 | 1 | 1 | 0 | 0 | 1/2 | A deep squat is defined by a knee joint angle |
| squat | partial squat | principle | 0.331 | 2 | 1 | 0 | 1 | 1/1 |  |
| push-up | hip sag | mistake | 0.133 | 1 | 1 | 0 | 0 | 1/4 | hip sagging; sagging of the lower back; body in a straight line |
| push-up | hip sag | finding | 0.357 | 1 | 1 | 0 | 0 | 1/1 |  |
| push-up | hip sag | principle | 0.342 | 2 | 1 | 0 | 1 | 1/1 |  |
| push-up | partial range of motion | mistake | 0.168 | 1 | 1 | 0 | 0 | 1/1 |  |
| push-up | partial range of motion | finding | 0.264 | 1 | 1 | 0 | 0 | 1/1 |  |
| push-up | partial range of motion | principle | 0.327 | 2 | 1 | 1 🔴 | 0 | 1/1 |  |
| lunge | excessive forward trunk lean | mistake | 0.256 | 1 | 1 | 0 | 0 | 1/4 | Leaning the torso forward; Forward torso lean during the downward phase; gaze downward, which increases trunk flexion |
| lunge | excessive forward trunk lean | finding | 0.338 | 1 | 1 | 0 | 0 | 1/2 | downward direction of gaze increases trunk flexion |
| lunge | excessive forward trunk lean | principle | 0.307 | 2 | 2 | 0 | 0 | 2/3 | Keep the upper body upright |
| lunge | shallow lunge | mistake | 0.304 | 1 | 1 | 0 | 0 | 1/2 | short step length |
| lunge | shallow lunge | finding | 0.306 | 2 | 0 | 0 | 2 | 0/2 | length of the lunge is about 2x hip width; short step length results in joint forces almost two times higher |
| lunge | shallow lunge | principle | 0.310 | 2 | 1 | 1 🔴 | 0 | 1/2 | knee flexed to 90 degrees |
| lunge | insufficient back knee flexion | mistake | 0.256 | 1 | 0 | 1 🔴 | 0 | 0/1 | preventing knee flexion to 90 degrees |
| lunge | insufficient back knee flexion | finding | 0.305 | 2 | 0 | 2 🔴 | 0 | 0/1 | back knee ending at approximately a 90-degree angle |
| lunge | insufficient back knee flexion | principle | 0.275 | 2 | 0 | 2 🔴 | 0 | 0/1 | until the back knee is just above the floor |
| bicep-curl | elbow flare | mistake | 0.057 | 2 | 2 | 0 | 0 | 2/4 | elbows to drift forward or away from the waist; elbows to pull forward |
| bicep-curl | elbow flare | finding | 0.442 | 0 | 0 | 0 | 0 | n/a |  |
| bicep-curl | elbow flare | principle | 0.161 | 1 | 1 | 0 | 0 | 1/3 | Keep the elbows close to the body; Keep elbows fixed at the sides |
| bicep-curl | partial range of motion | mistake | 0.269 | 3 | 3 | 0 | 0 | 3/6 | full range of motion at the elbow joint; fully extend the elbows at the bottom; limited range of motion |
| bicep-curl | partial range of motion | finding | 0.407 | 0 | 0 | 0 | 0 | n/a |  |
| bicep-curl | partial range of motion | principle | 0.288 | 2 | 2 | 0 | 0 | 2/4 | Start the bicep curl with the elbow in full extension; Start the movement with the elbow joint in full extension |

    squat      butt wink                       mistake  GOOD  Lumbar flexion (butt wink) at the bottom of the squat.
    squat      butt wink                       mistake  GOOD  Posterior pelvic tilt ('Butt Wink') where the pelvis tucks under and the low back rounds at the bottom of the squat.
    squat      butt wink                       finding  GOOD  Flexing at the spine before 1208 (120 degrees) of hip flexion when squatting may indicate restriction in the posterior fibers of the iliotibial band or lack of lumbar control.
    squat      butt wink                       finding  BAD   Control squats were performed to 90 degrees of flexion.
    squat      butt wink                       principle GOOD  Maintain a neutral pelvic tilt during the squat to increase erector spinae and oblique muscle activity, providing optimal spinal support.
    squat      butt wink                       principle GOOD  Maintain a neutral, slightly lordotic spine posture throughout the squat to avoid excessive pressure on the lower back.
    squat      knee valgus                     mistake  GOOD  Medial knee displacement (knee valgus) during double-legged squats.
    squat      knee valgus                     mistake  GOOD  Knees collapsing inward (valgus collapse) during the squat.
    squat      knee valgus                     mistake  GOOD  Excessive medial knee displacement (knee valgus) during single-leg squats or landings.
    squat      knee valgus                     finding  GOOD  A lack of strength in the medial gastrocnemius, tibialis anterior, and/or tibialis posterior decreases the athlete's ability to control knee valgus and foot pronation motions and may contribute to excessive medial knee displacement and dynamic valgus (1).
    squat      knee valgus                     finding  BAD   The knee joint displaced approximately 0.17 m anteriorly compared with neutral in the malaligned squat condition.
    squat      knee valgus                     principle GOOD  Keep knees in line with feet to avoid knee valgus.
    squat      knee valgus                     principle neut  Knee position (valgus vs. varus) interacts with squat depth to alter the activation levels of both the VMO and VL muscles.
    squat      partial squat                   mistake  GOOD  Squatting too shallow, failing to bring the thighs at least parallel to the ground.
    squat      partial squat                   finding  GOOD  Compressive forces in the knee may be higher in a partial squat than in a deep squat.
    squat      partial squat                   principle GOOD  Achieve full depth with the tops of the thighs at least parallel to the ground.
    squat      partial squat                   principle neut  Perform squats to 90 degrees of flexion for standard depth.
    push-up    hip sag                         mistake  GOOD  Allowing the hips to sag
    push-up    hip sag                         finding  GOOD  Abdominal muscles dominate contributions to vertebral joint stiffness during the push-up (Howarth, Beach, & Callaghan, 2008).
    push-up    hip sag                         principle GOOD  Abdominal muscles are the primary contributors to maintaining vertebral joint stiffness during the push-up.
    push-up    hip sag                         principle neut  The push-up is an upper-extremity weight-bearing exercise that can improve joint stability and proprioception through joint compression forces.
    push-up    partial range of motion         mistake  GOOD  Failing to achieve the correct depth of 90 degrees elbow flexion.
    push-up    partial range of motion         finding  GOOD  The correct depth for a push-up repetition was defined as 90 degrees (noted as 900 in text) of elbow flexion.
    push-up    partial range of motion         principle GOOD  Achieve a depth of 90 degrees of elbow flexion during each repetition.
    push-up    partial range of motion         principle BAD   Forearm rotation during the push-up exercise influences the biomechanical load experienced by the elbow.
    lunge      excessive forward trunk lean    mistake  GOOD  Excessive trunk movement or marked trunk lean.
    lunge      excessive forward trunk lean    finding  GOOD  An upright trunk tends to create what is often called a 90/90 lunge where both knees at the bottom of the move are 90° angles.
    lunge      excessive forward trunk lean    principle GOOD  Performing a forward lunge with a forward trunk lean increases biceps femoris activity compared to an upright trunk.
    lunge      excessive forward trunk lean    principle GOOD  Maintain an upright trunk throughout the movement.
    lunge      shallow lunge                   mistake  GOOD  Lunge step is too short or too long.
    lunge      shallow lunge                   finding  neut  Partial lunge was performed to 50 degrees of knee flexion.
    lunge      shallow lunge                   finding  neut  In a traditional lunge, a moderate step results in the back knee ending at approximately a 90-degree angle.
    lunge      shallow lunge                   principle GOOD  Step length and height variations affect patellofemoral joint loading during the forward lunge.
    lunge      shallow lunge                   principle BAD   Perform a partial lunge by lowering the body to approximately 50 degrees of knee flexion, which is highly suitable for early-stage rehabilitation.
    lunge      insufficient back knee flexion  mistake  BAD   Allowing the rear knee to flex during the stride-stance lunge.
    lunge      insufficient back knee flexion  finding  BAD   Rotating the back knee or foot outward during a forward lunge increases torque stress in the knee joint.
    lunge      insufficient back knee flexion  finding  BAD   Kinematic data showed a significantly greater knee angle in the forward lunge compared to the backward lunge.
    lunge      insufficient back knee flexion  principle BAD   Do not allow the rear knee to contact the floor during the lunge.
    lunge      insufficient back knee flexion  principle BAD   Backward lunges can reduce anterior shearing forces and patellofemoral joint loading on the knee compared to forward lunges.
    bicep-curl elbow flare                     mistake  GOOD  Allowing the elbows to flare outward during the curl.
    bicep-curl elbow flare                     mistake  GOOD  Allowing the elbows to drift away from the body during the curl.
    bicep-curl elbow flare                     principle GOOD  Keep elbows tucked at the sides during the curl.
    bicep-curl partial range of motion         mistake  GOOD  Failing to start the repetition with the elbow in full extension.
    bicep-curl partial range of motion         mistake  GOOD  Failing to achieve complete arm extension at the bottom of the movement.
    bicep-curl partial range of motion         mistake  GOOD  Failing to start the movement from full elbow extension.
    bicep-curl partial range of motion         principle GOOD  Perform a full range of motion from complete arm extension at the bottom to near-maximal elbow flexion at the top.
    bicep-curl partial range of motion         principle GOOD  Utilize a full range of motion from full elbow extension to complete flexion.

### kb_local_curated_v4 — mode: session

| exercise | fault | kind | best | kept | good | bad | neutral | must_hit found | missing must_hit |
|---|---|---|---|---|---|---|---|---|---|
| squat | butt wink | mistake | 0.120 | 2 | 2 | 0 | 0 | 2/4 | Tailbone tucking; neutral spine curvature to flex during a deep squat |
| squat | butt wink | finding | 0.329 | 2 | 1 | 1 🔴 | 0 | 1/1 |  |
| squat | butt wink | principle | 0.296 | 2 | 2 | 0 | 0 | 2/2 |  |
| squat | partial squat | mistake | 0.258 | 1 | 1 | 0 | 0 | 1/2 | insufficient squat depth |
| squat | partial squat | finding | 0.370 | 1 | 1 | 0 | 0 | 1/2 | A deep squat is defined by a knee joint angle |
| squat | partial squat | principle | 0.331 | 2 | 1 | 0 | 1 | 1/1 |  |
| lunge | excessive forward trunk lean | mistake | 0.256 | 1 | 1 | 0 | 0 | 1/4 | Leaning the torso forward; Forward torso lean during the downward phase; gaze downward, which increases trunk flexion |
| lunge | excessive forward trunk lean | finding | 0.338 | 1 | 1 | 0 | 0 | 1/2 | downward direction of gaze increases trunk flexion |
| lunge | excessive forward trunk lean | principle | 0.307 | 2 | 2 | 0 | 0 | 2/3 | Keep the upper body upright |
| lunge | insufficient back knee flexion | mistake | 0.256 | 1 | 0 | 1 🔴 | 0 | 0/1 | preventing knee flexion to 90 degrees |
| lunge | insufficient back knee flexion | finding | 0.305 | 2 | 0 | 2 🔴 | 0 | 0/1 | back knee ending at approximately a 90-degree angle |
| lunge | insufficient back knee flexion | principle | 0.275 | 2 | 0 | 2 🔴 | 0 | 0/1 | until the back knee is just above the floor |
| push-up | (no errors - principle path, not scored) | | | | | | | | |
| bicep-curl | elbow flare | mistake | 0.057 | 2 | 2 | 0 | 0 | 2/4 | elbows to drift forward or away from the waist; elbows to pull forward |
| bicep-curl | elbow flare | finding | 0.442 | 0 | 0 | 0 | 0 | n/a |  |
| bicep-curl | elbow flare | principle | 0.161 | 1 | 1 | 0 | 0 | 1/3 | Keep the elbows close to the body; Keep elbows fixed at the sides |
| bicep-curl | partial range of motion | mistake | 0.269 | 3 | 3 | 0 | 0 | 3/6 | full range of motion at the elbow joint; fully extend the elbows at the bottom; limited range of motion |
| bicep-curl | partial range of motion | finding | 0.407 | 0 | 0 | 0 | 0 | n/a |  |
| bicep-curl | partial range of motion | principle | 0.288 | 2 | 2 | 0 | 0 | 2/4 | Start the bicep curl with the elbow in full extension; Start the movement with the elbow joint in full extension |

    squat      butt wink                       mistake  GOOD  Lumbar flexion (butt wink) at the bottom of the squat.
    squat      butt wink                       mistake  GOOD  Posterior pelvic tilt ('Butt Wink') where the pelvis tucks under and the low back rounds at the bottom of the squat.
    squat      butt wink                       finding  GOOD  Flexing at the spine before 1208 (120 degrees) of hip flexion when squatting may indicate restriction in the posterior fibers of the iliotibial band or lack of lumbar control.
    squat      butt wink                       finding  BAD   Control squats were performed to 90 degrees of flexion.
    squat      butt wink                       principle GOOD  Maintain a neutral pelvic tilt during the squat to increase erector spinae and oblique muscle activity, providing optimal spinal support.
    squat      butt wink                       principle GOOD  Maintain a neutral, slightly lordotic spine posture throughout the squat to avoid excessive pressure on the lower back.
    squat      partial squat                   mistake  GOOD  Squatting too shallow, failing to bring the thighs at least parallel to the ground.
    squat      partial squat                   finding  GOOD  Compressive forces in the knee may be higher in a partial squat than in a deep squat.
    squat      partial squat                   principle GOOD  Achieve full depth with the tops of the thighs at least parallel to the ground.
    squat      partial squat                   principle neut  Perform squats to 90 degrees of flexion for standard depth.
    lunge      excessive forward trunk lean    mistake  GOOD  Excessive trunk movement or marked trunk lean.
    lunge      excessive forward trunk lean    finding  GOOD  An upright trunk tends to create what is often called a 90/90 lunge where both knees at the bottom of the move are 90° angles.
    lunge      excessive forward trunk lean    principle GOOD  Performing a forward lunge with a forward trunk lean increases biceps femoris activity compared to an upright trunk.
    lunge      excessive forward trunk lean    principle GOOD  Maintain an upright trunk throughout the movement.
    lunge      insufficient back knee flexion  mistake  BAD   Allowing the rear knee to flex during the stride-stance lunge.
    lunge      insufficient back knee flexion  finding  BAD   Rotating the back knee or foot outward during a forward lunge increases torque stress in the knee joint.
    lunge      insufficient back knee flexion  finding  BAD   Kinematic data showed a significantly greater knee angle in the forward lunge compared to the backward lunge.
    lunge      insufficient back knee flexion  principle BAD   Do not allow the rear knee to contact the floor during the lunge.
    lunge      insufficient back knee flexion  principle BAD   Backward lunges can reduce anterior shearing forces and patellofemoral joint loading on the knee compared to forward lunges.
    bicep-curl elbow flare                     mistake  GOOD  Allowing the elbows to flare outward during the curl.
    bicep-curl elbow flare                     mistake  GOOD  Allowing the elbows to drift away from the body during the curl.
    bicep-curl elbow flare                     principle GOOD  Keep elbows tucked at the sides during the curl.
    bicep-curl partial range of motion         mistake  GOOD  Failing to start the repetition with the elbow in full extension.
    bicep-curl partial range of motion         mistake  GOOD  Failing to achieve complete arm extension at the bottom of the movement.
    bicep-curl partial range of motion         mistake  GOOD  Failing to start the movement from full elbow extension.
    bicep-curl partial range of motion         principle GOOD  Perform a full range of motion from complete arm extension at the bottom to near-maximal elbow flexion at the top.
    bicep-curl partial range of motion         principle GOOD  Utilize a full range of motion from full elbow extension to complete flexion.

**single summary (kb_local_curated_v4)** — faults with ≥1 correct mistake chunk: **9/10** · context chunks: 47 = good 33 / bad **9** / neutral 5 · precision(good/kept) = 0.70
  bad chunks under: lunge/insufficient back knee flexion, lunge/shallow lunge, push-up/partial range of motion, squat/butt wink, squat/knee valgus

**session summary (kb_local_curated_v4)** — faults with ≥1 correct mistake chunk: **5/6** · context chunks: 27 = good 20 / bad **6** / neutral 1 · precision(good/kept) = 0.74
  bad chunks under: lunge/insufficient back knee flexion, squat/butt wink

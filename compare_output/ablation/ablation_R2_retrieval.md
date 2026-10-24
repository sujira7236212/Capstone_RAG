# Retrieval golden-set evaluation

gates: CANDIDATE_K=12, MAX_PER_KIND={'mistake': 3, 'finding': 2, 'principle': 2, 'consequence': 2}, ABS_DISTANCE_CAP={'mistake': 0.4, 'finding': 0.4, 'principle': 0.4, 'consequence': 0.4}, RELATIVE_MARGIN=0.03, NEAR_DUP_JACCARD=0.72, TAG_MODE=prefer, KIND_POOL=single
golden: `eval/golden_chunks.json` · mock: `mock_data/mock_sessions.json`
relevance pool: `eval/relevance_pool.json` (judge gemini-3.8-flash, built 2026-09-25, collection kb_gemini_curated_v5)

`best` = closest chunk of that kind in the whole collection (before the gate). `good` = kept chunk matching a must_hit pattern, `bad` = matching a must_not_hit pattern (a different fault, labelled as this one), `neutral` = neither.

### kb_gemini_curated_v5 — mode: single

| exercise | fault | kind | best | kept | good | bad | neutral | must_hit found | missing must_hit |
|---|---|---|---|---|---|---|---|---|---|
| squat | butt wink | mistake | 0.032 | 2 | 2 | 0 | 0 | 2/5 | Lumbar flexion (butt wink); Tailbone tucking; neutral spine curvature to flex during a deep squat |
| squat | butt wink | finding | 0.156 | 0 | 0 | 0 | 0 | 0/2 | Flexing at the spine before; flexes at the spine before 120 degrees of hip flexion |
| squat | butt wink | principle | 0.116 | 0 | 0 | 0 | 0 | 0/4 | neutral pelvic tilt; neutral, slightly lordotic spine; maintain a slight lordotic posture; neutral, lordotic lumbar position |
| squat | butt wink | consequence | 0.111 | 0 | 0 | 0 | 0 | n/a |  |
| squat | knee valgus | mistake | 0.034 | 8 | 4 | 0 | 4 | 2/7 | Medial knee displacement (knee valgus); Knees collapsing inward (valgus collapse); Knee valgus (inward knee collapse); knock-kneed; Knee valgus (knees caving inward) |
| squat | knee valgus | finding | 0.045 | 1 | 1 | 0 | 0 | 1/4 | control knee valgus and foot pronation; heel lift eliminated medial knee displacement; squats with medial knee displacement compared with a neutrally aligned squat |
| squat | knee valgus | principle | 0.090 | 0 | 0 | 0 | 0 | 0/4 | Keep knees in line with feet; prevent knees from collapsing inward; knee alignment over the second and third toes; Avoiding medial knee displacement ensures |
| squat | knee valgus | consequence | 0.091 | 0 | 0 | 0 | 0 | n/a |  |
| squat | partial squat | mistake | 0.061 | 3 | 1 | 0 | 2 | 1/2 | insufficient squat depth |
| squat | partial squat | finding | 0.196 | 0 | 0 | 0 | 0 | 0/3 | Compressive forces in the knee may be higher in a partial squat; A deep squat is defined by a knee joint angle; decrease the compressive load on your knee joint |
| squat | partial squat | principle | 0.161 | 0 | 0 | 0 | 0 | 0/3 | at least parallel to the ground; femurs are slightly past parallel to the ground; at least parallel with the ground |
| squat | partial squat | consequence | 0.152 | 0 | 0 | 0 | 0 | n/a |  |
| push-up | hip sag | mistake | 0.048 | 1 | 1 | 0 | 0 | 1/5 | hips to sag; hip sagging; sagging of the lower back; body in a straight line |
| push-up | hip sag | finding | 0.180 | 0 | 0 | 0 | 0 | 0/1 | Abdominal muscles dominate contributions to vertebral joint stiffness |
| push-up | hip sag | principle | 0.143 | 0 | 0 | 0 | 0 | 0/2 | Abdominal muscles are the primary contributors to maintaining vertebral joint stiffness; Maintain a rigid spine and lower-extremity segments throughout the push-up |
| push-up | hip sag | consequence | 0.129 | 0 | 0 | 0 | 0 | n/a |  |
| push-up | partial range of motion | mistake | 0.079 | 1 | 1 | 0 | 0 | 1/2 | correct depth of 90 degrees elbow flexion |
| push-up | partial range of motion | finding | 0.186 | 0 | 0 | 0 | 0 | 0/3 | correct depth for a push-up repetition was defined as 90 degrees; correct depth of 90 degrees was not acquired; chest nearly touches the floor |
| push-up | partial range of motion | principle | 0.139 | 0 | 0 | 0 | 0 | 0/1 | depth of 90 degrees of elbow flexion |
| push-up | partial range of motion | consequence | 0.154 | 0 | 0 | 0 | 0 | n/a |  |
| lunge | excessive forward trunk lean | mistake | 0.072 | 4 | 2 | 0 | 2 | 2/5 | marked trunk lean; Forward torso lean during the downward phase; gaze downward, which increases trunk flexion |
| lunge | excessive forward trunk lean | finding | 0.142 | 0 | 0 | 0 | 0 | 0/2 | upright trunk tends to create; downward direction of gaze increases trunk flexion |
| lunge | excessive forward trunk lean | principle | 0.112 | 0 | 0 | 0 | 0 | 0/3 | Maintain an upright trunk; Keep the upper body upright; forward trunk lean increases biceps femoris |
| lunge | excessive forward trunk lean | consequence | 0.122 | 0 | 0 | 0 | 0 | n/a |  |
| lunge | shallow lunge | mistake | 0.059 | 5 | 1 | 0 | 4 | 1/3 | step is too short; short step length |
| lunge | shallow lunge | finding | 0.110 | 0 | 0 | 0 | 0 | 0/2 | length of the lunge is about 2x hip width; short step length results in joint forces almost two times higher |
| lunge | shallow lunge | principle | 0.127 | 0 | 0 | 0 | 0 | 0/3 | Step length; knee flexed to 90 degrees; front knee should be flexed to approximately 90 degrees |
| lunge | shallow lunge | consequence | 0.120 | 0 | 0 | 0 | 0 | n/a |  |
| lunge | insufficient back knee flexion | mistake | 0.060 | 1 | 1 | 0 | 0 | 1/2 | preventing knee flexion to 90 degrees |
| lunge | insufficient back knee flexion | finding | 0.108 | 0 | 0 | 0 | 0 | 0/2 | back knee ending at approximately a 90-degree angle; target depth for the trailing knee was defined as 2 to 3 cm short of contacting the ground |
| lunge | insufficient back knee flexion | principle | 0.106 | 0 | 0 | 0 | 0 | 0/2 | until the back knee is just above the floor; posterior legs should achieve a knee joint range of motion of 0 to 90 degrees |
| lunge | insufficient back knee flexion | consequence | 0.103 | 0 | 0 | 0 | 0 | n/a |  |
| bicep-curl | elbow flare | mistake | 0.046 | 2 | 2 | 0 | 0 | 2/5 | elbows to flare outward; elbows to drift away from the body; elbows to drift forward or away from the waist |
| bicep-curl | elbow flare | finding | 0.202 | 0 | 0 | 0 | 0 | n/a |  |
| bicep-curl | elbow flare | principle | 0.184 | 0 | 0 | 0 | 0 | 0/4 | Keep elbows tucked at the sides; Keep the elbows close to the body; Keep elbows fixed at the sides; elbows must be kept close to the body |
| bicep-curl | elbow flare | consequence | 0.149 | 0 | 0 | 0 | 0 | n/a |  |
| bicep-curl | partial range of motion | mistake | 0.045 | 3 | 3 | 0 | 0 | 3/8 | full elbow extension; full range of motion at the elbow joint; fully extend the elbows at the bottom; limited range of motion; elbow in full extension |
| bicep-curl | partial range of motion | finding | 0.168 | 0 | 0 | 0 | 0 | n/a |  |
| bicep-curl | partial range of motion | principle | 0.124 | 0 | 0 | 0 | 0 | 0/4 | full range of motion from complete arm extension; full range of motion from full elbow extension; Start the bicep curl with the elbow in full extension; Start the movement with the elbow joint in full extension |
| bicep-curl | partial range of motion | consequence | 0.120 | 0 | 0 | 0 | 0 | n/a |  |

**single summary (kb_gemini_curated_v5)** — faults with ≥1 correct mistake chunk: **10/10** · context chunks: 31 = good 19 / bad **0** / neutral 12 · precision(good/kept) = 0.61

### kb_gemini_curated_v5 — recall vs relevance pool (single mode)

`facts` = relevant chunks in the pool after near-dup clustering · `recall` = facts with a chunk (or near-dup) in the context · ctx columns = judge labels of the chunks actually kept.
`ceiling` = best recall possible at the current context budget (sum(MAX_PER_KIND) = 9 chunks per fault): min(facts, budget) / facts. Compare recall against it, and compare steps only at the same budget.

| exercise | fault | candidates | facts | covered | recall | ceiling | kept | ctx relevant | ctx wrong_fault | ctx irrelevant | ctx unlabeled | miss: tag_spelling | miss: tag_filter | miss: rank | miss: margin | miss: quota | miss: dup |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| squat | butt wink | 122 | 41 | 2 | 0.05 | 0.22 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 4 | 35 | 0 | 0 |
| squat | knee valgus | 189 | 116 | 8 | 0.07 | 0.08 | 9 | 8 | 0 | 1 | 0 | 0 | 1 | 74 | 0 | 33 | 0 |
| squat | partial squat | 149 | 52 | 3 | 0.06 | 0.17 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 15 | 34 | 0 | 0 |
| push-up | hip sag | 93 | 13 | 1 | 0.08 | 0.69 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 10 | 0 | 0 |
| push-up | partial range of motion | 97 | 13 | 1 | 0.08 | 0.69 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 | 0 |
| lunge | excessive forward trunk lean | 162 | 42 | 2 | 0.05 | 0.21 | 4 | 2 | 2 | 0 | 0 | 0 | 0 | 13 | 27 | 0 | 0 |
| lunge | shallow lunge | 160 | 56 | 5 | 0.09 | 0.16 | 5 | 5 | 0 | 0 | 0 | 0 | 3 | 20 | 28 | 0 | 0 |
| lunge | insufficient back knee flexion | 107 | 15 | 1 | 0.07 | 0.60 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 7 | 7 | 0 | 0 |
| bicep-curl | elbow flare | 73 | 5 | 2 | 0.40 | 1.00 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 |
| bicep-curl | partial range of motion | 104 | 58 | 3 | 0.05 | 0.16 | 3 | 3 | 0 | 0 | 0 | 0 | 6 | 11 | 38 | 0 | 0 |

**recall summary (kb_gemini_curated_v5)** — facts covered 28/411 · recall micro **0.07** (ceiling 0.21) / macro **0.10** · context 31 chunks: relevant 28 / wrong_fault **2** · pool-precision(relevant/kept) = 0.90
  missed facts by reason: tag_spelling 0, tag_filter 10, rank 146, margin 194, quota 33, dup 0
  context by kind: mistake 30, finding 1, principle 0, consequence 0 · faults missing a kind: mistake 0, finding 9, principle 10, consequence 10

    squat      butt wink                       margin       Exceeding the hip joint's anatomical limit (the theoretical glass ceiling on squat depth) forces compensation patterns, such as posterior pelvic tilt and spinal rounding.
    squat      butt wink                       margin       Squatting with a stance width or foot abduction angle that does not match the individual's anatomical capacity can lead to premature lumbar flexion.
    squat      butt wink                       margin       Forcing deep hip flexion without accommodating the necessary hip abduction and external rotation causes the pelvis to tilt posteriorly and the lumbar spine to flex.
    squat      butt wink                       margin       Allowing lumbar flexion during a squat is a biomechanical fault that must be avoided.
    squat      butt wink                       margin       The lumbar vertebrae should be maintained in a neutral alignment throughout the entire squat movement, which entails keeping a slight lordotic curve in the lumbar region while holding the abdomen upward and rigid.
    squat      butt wink                       margin       The individual must maintain a stiffened torso with a neutral, lordotic lumbar position as a safe and optimal squat strategy.
    squat      butt wink                       margin       Losing the neutral curvature of the lumbar spine during the squat is a common deficit.
    squat      butt wink                       margin       Losing the neutral curve of the lumbar spine causes the spine to lose its ability to bear load, preventing safe progression of the squat with load.
    squat      butt wink                       margin       The squat requires sufficient spinal mobility to assume and maintain a slight lordotic posture.
    squat      butt wink                       margin       The athlete must stiffen the back musculature to support the spine positioned in a neutral, slightly lordotic position.
    squat      butt wink                       margin       The athlete should maintain a slight lordotic curve in the lumbar spine and keep the trunk angle parallel with the tibial angles.
    squat      butt wink                       margin       Executing a squat to at least parallel with only a dowel as external resistance allows a coach to gauge when and if the athlete presents excessive anterior or posterior pelvic tilt.
    squat      butt wink                       margin       An athlete may flex at the spine before 120 degrees of hip flexion when squatting.
    squat      butt wink                       margin       If the athlete flexes at the spine before 120 degrees of hip flexion when squatting, they may have restriction in the posterior fibers of the iliotibial band or lack of lumbar control.
    squat      butt wink                       margin       Failing to stiffen the back musculature to support a neutral, slightly lordotic spine may result in increased and potentially harmful compressive and shear forces on the lumbar spine.
    squat      butt wink                       margin       Squatting with the spine in a flexed position increases the risk of disc herniation as a result of excessive stress placed on intervertebral discs.
    squat      butt wink                       margin       Maintaining a neutral pelvic tilt during the squat increases activity of the erector spinae and oblique muscles, helping to ensure optimal muscular support for the spine.
    squat      butt wink                       margin       The athlete should maintain the pelvis in a normal or neutral tilt, particularly during the descent phase and in the final part of the descent.
    squat      butt wink                       margin       Failing to maintain a neutral pelvic tilt reduces muscular support for the spine while handling loads, which increases the risk for low back injury.
    squat      butt wink                       margin       Use the pelvic rock test to identify the optimal width for the feet and knees to allow deep squatting without compromising back curvature.
    squat      butt wink                       margin       Allowing the neutral spine curvature to flex during a deep squat.
    squat      butt wink                       margin       The pelvic rock test starts with knees together, rocks the pelvis back toward the heels, and is repeated with knees spread apart a few inches to identify the point where neutral spine curvature begins to flex.
    squat      butt wink                       margin       Allowing the spine to flex during a squat compromises back curvature and can lead to eventual pain and suboptimal performance.
    squat      butt wink                       margin       The appropriate squat depth is the deepest position a client can achieve while maintaining a neutral spine, foot stability, proper joint alignment, and movement control.
    squat      butt wink                       rank         Forcing clients into an arbitrary squat depth standard rather than focusing on their individual anatomy, mobility, and ability to maintain a neutral spine.
    squat      butt wink                       margin       Proper cueing is the maintenance of a rigid spine that is either neutral or slightly flattened.
    squat      butt wink                       margin       Maintain a rigid spine by keeping constant contact with a dowel along the sacrum, thoracic spine, and back of the head throughout the movement.
    squat      butt wink                       margin       Maintain a neutral low back position with a slight lordosis throughout the squat movement.
    squat      butt wink                       margin       Intravertebral disc pressure increases as lumbar lordosis is lost, putting the lifter at risk for injury.
    squat      butt wink                       margin       Use a hip hinge drill holding a dowel along the length of the spine to cue and maintain a neutral spine position while descending.
    squat      butt wink                       margin       Failing to properly descend while pivoting at the hips and maintaining a correct lumbar position.
    squat      butt wink                       margin       Bending the spine and not keeping it straight and aligned with your pelvis.
    squat      butt wink                       rank         Your trunk and pelvis should stay neutral and aligned as you bend at your hips, with your pelvis remaining in a neutral position without tucking under or tilting backward.
    squat      butt wink                       margin       Limited range of motion in the hips, knees, ankles, or lumbar spine can cause your tailbone to tuck under at the bottom of the movement, a compensation commonly known as butt wink.
    squat      butt wink                       margin       Compensations such as tailbone tucking (butt wink), heels lifting, or incorrect knee tracking due to limited mobility can increase the risk of injury.
    squat      butt wink                       rank         Keep your spine straight and aligned with your pelvis, remaining relatively straight and parallel to your shins.
    squat      butt wink                       margin       If you lack the appropriate mobility at your hips, knees, or ankles to maintain proper alignment during a deep squat, perform a squat in which your hips do not go below your knees.
    squat      butt wink                       margin       Not keeping your spine straight and aligned with your pelvis increases the risk of strain and shear force in the spine.
    squat      butt wink                       rank         Failing to keep the spine straight and extended increases the risk of injury to the spine or intervertebral discs.
    squat      knee valgus                     rank         Elevating the heels during an overhead squat can help correct medial-knee displacement by increasing the tibial angle in the anterior direction.
    squat      knee valgus                     quota        Allowing medial knee displacement, which is a clinical observation of dynamic valgus collapse, during squatting tasks.
    squat      knee valgus                     rank         Participants who displayed medial-knee displacement during an overhead squat had approximately 20% less nonweight-bearing, passive ankle dorsiflexion than did those participants without medial-knee displacement.
    squat      knee valgus                     quota        The medial-knee displacement observed during the overhead squat was corrected when a 2-inch (5.08-cm) lift was placed under the heel.
    squat      knee valgus                     rank         Medial knee displacement combined with an anterior tibial shear force places the greatest load on the ACL, increasing the risk of ACL injury.
    squat      knee valgus                     quota        Allowing medial knee displacement, or knee-valgus collapse, during a double-legged squat is a common movement alteration associated with limited ankle mobility.
    squat      knee valgus                     rank         Previous research by Bell et al. reported decreased nonweight-bearing ankle dorsiflexion range of motion in individuals who displayed medial knee displacement during a double-legged squat compared with those who did not.
    squat      knee valgus                     quota        Limited ankle dorsiflexion range of motion can alter lower extremity movement patterns, which may manifest as medial knee displacement or knee-valgus collapse during squatting.
    squat      knee valgus                     rank         Elevating the heels with a 2-inch (5.08-cm) heel lift can eliminate medial knee displacement and decrease muscle activation of the gastrocnemius and tibialis anterior during the descent phase of a squat.
    squat      knee valgus                     rank         Greater ankle dorsiflexion range of motion during weight-bearing movements promotes knee-varus displacement, helping to prevent knee-valgus motion.
    squat      knee valgus                     rank         The medial-knee-displacement group displayed significantly greater muscle activation of the hip adductor, gastrocnemius, and tibialis anterior muscles in comparison with the control group.
    squat      knee valgus                     rank         Increased knee-valgus motion and loading are associated with a higher risk of ACL injury.
    squat      knee valgus                     rank         Limited ankle dorsiflexion contributes to excessive rearfoot pronation, calcaneal eversion, and talar-head adduction, which can cause internal rotation of the tibia and medial displacement at the knee.
    squat      knee valgus                     rank         Increasing ankle dorsiflexion range of motion facilitates increased knee flexion and knee varus displacement during squatting movements.
    squat      knee valgus                     rank         Sufficient ankle dorsiflexion range of motion helps minimize anterior shear force and knee-valgus-related ACL loading.
    squat      knee valgus                     quota        Performing squats with limited ankle dorsiflexion range of motion, which is associated with medial knee displacement.
    squat      knee valgus                     quota        Participants demonstrating medial knee displacement during an overhead squat have less ankle dorsiflexion range of motion assessed in non-weight-bearing with 30 degrees of knee flexion.
    squat      knee valgus                     rank         Limited ankle dorsiflexion range of motion leads to knee-valgus motion, which increases knee-valgus-related ACL loading and the risk of ACL injury.
    squat      knee valgus                     rank         Athlete comfort should dictate the combination of stance width and toe-out, provided that biomechanical faults like knees collapsing in, lumbar flexion, or heels elevating are avoided.
    squat      knee valgus                     rank         Allowing the knees to collapse inward during a squat is a biomechanical fault that must be avoided.
    squat      knee valgus                     quota        Allowing the knees to cave inward (valgus) increases stress on the knee joint.
    squat      knee valgus                     rank         Excessive foot pronation leads to compensatory internal rotation of the tibia or femur, which contributes to knee valgus.
    squat      knee valgus                     quota        The valgus angle of the knee can be reduced by increasing the base of support and placing the feet further apart.
    squat      knee valgus                     quota        Allowing excessive knee valgus (genu valgum or knock-knees) during standing or movement.
    squat      knee valgus                     rank         The normal frontal plane alignment of the knee is slightly valgus, ranging between 5 to 15 degrees.
    squat      knee valgus                     rank         An excessive valgus angle directly associates with an increasing lateral pulling force of the quadriceps muscle.
    squat      knee valgus                     rank         Training the posterior fibers of the gluteus medius can decrease hip internal rotation and the valgus force vector at the knee.
    squat      knee valgus                     rank         Keep your heels on the floor and your knees in line with your feet as you squat.
    squat      knee valgus                     quota        Allowing the hip to internally rotate and create a valgus force vector at the knee due to weak gluteus medius muscles.
    squat      knee valgus                     rank         The position of the hips should be neutral or slightly externally rotated during the squat to decrease the Q-angle and lateral forces acting on the patella.
    squat      knee valgus                     rank         Failing to maintain neutral or slightly externally rotated hips increases the Q-angle and lateral forces acting on the patella.
    squat      knee valgus                     rank         Activating the gluteus medius to control internal rotation of the femur during closed kinetic chain exercises helps maintain proper patellofemoral mechanics.
    squat      knee valgus                     quota        Failing to control internal rotation of the femur during closed kinetic chain exercises due to weakness or inactivity of the gluteus medius.
    squat      knee valgus                     rank         Inability of the gluteus medius to control internal rotation of the femur during closed kinetic chain exercises, combined with VMO inhibition, may lead to excessive lateral tracking of the patella.
    squat      knee valgus                     rank         Slightly externally rotate both hips during the squat setup.
    squat      knee valgus                     rank         Allowing the knees to align in a valgus position, where the feet cannot touch together when standing with the knees closed.
    squat      knee valgus                     quota        Slightly externally rotating both hips in the starting position is aimed to decrease the Q angle and lateral force acting on the patella.
    squat      knee valgus                     rank         Failing to slightly externally rotate the hips can increase the Q angle and lateral force acting on the patella.
    squat      knee valgus                     rank         Using inadequate resistance objects like a small towel roll, soft bolster, or weak elastic band causes excessive valgus posture of the knee.
    squat      knee valgus                     rank         Avoiding medial knee displacement prevents the need for adaptive muscle activation strategies to stabilize the lower extremity joints.
    squat      knee valgus                     quota        A poorly performed squat with increased knee valgus may expose the lower extremity joints to excessive torques.
    squat      knee valgus                     rank         Decreased vastus lateralis and increased gastrocnemius muscle activation have been reported during squats with medial knee displacement compared with a neutrally aligned squat.
    squat      knee valgus                     quota        Performing squats with the knees collapsing inward, representing mediolateral malalignment.
    squat      knee valgus                     rank         Push your knees out at the bottom of the squat to keep them aligned with your feet.
    squat      knee valgus                     rank         The medio-lateral malaligned squat resulted in significantly increased dorsiflexion, ankle inversion, knee flexion, knee abduction, and hip adduction during approximately 10% to 85% of the squat cycle compared with the control squat.
    squat      knee valgus                     quota        Medio-lateral malalignment of the knees during a squat causes increased ankle inversion, knee abduction, and hip adduction throughout 10% to 85% of the squat movement.
    squat      knee valgus                     quota        Maintain proper medio-lateral alignment of the knees and hips throughout the squat cycle to avoid altered muscle activation patterns.
    squat      knee valgus                     quota        Allowing medio-lateral malalignment during the squat, which alters the activation of the quadriceps, hamstrings, and gastrocnemius muscles.
    squat      knee valgus                     rank         A medio-laterally malaligned squat results in significantly decreased hip flexion during 14–71% of the squat cycle compared with a control squat.
    squat      knee valgus                     rank         Vastus lateralis activation decreases during the final ascent (96–99%) of the squat cycle in a medio-laterally malaligned squat compared to a control squat, with a very large effect size of 26.21.
    squat      knee valgus                     rank         Vastus medialis activation decreases during the final phase of ascent (92–98%) of the squat cycle in a medio-laterally malaligned squat, with a very large effect size of 23.78.
    squat      knee valgus                     rank         Rectus femoris activation decreases during the initial (15–18%) and final phase of descent (28–48%), as well as the final phase of ascent (85–99%) of the squat cycle in a medio-laterally malaligned squat.
    squat      knee valgus                     rank         Biceps femoris activation increases during the initial phase of descent (11–21%) and the beginning of the final phase of descent (25–28%) during a medio-laterally malaligned squat, with effect sizes ranging from 4.71 to 13.14.
    squat      knee valgus                     rank         The lateral head of the gastrocnemius is more active during a medio-laterally malaligned squat in the initial (51–69%) and final phases of ascent (71–82%, 85–90%, 96–99%), with effect sizes ranging from 3.90 to 11.53.
    squat      knee valgus                     rank         The medial head of the gastrocnemius is less active during the initial (1–7%) phase of the squat cycle in a medio-laterally malaligned squat.
    squat      knee valgus                     rank         Medio-lateral malalignment during a squat reduces the activation of key knee extensors, including the vastus lateralis, vastus medialis, and rectus femoris, during critical phases of descent and ascent.
    squat      knee valgus                     rank         Medio-lateral malalignment increases the activation of the biceps femoris and lateral gastrocnemius, potentially leading to muscle imbalances or compensatory movement patterns.
    squat      knee valgus                     rank         During the ascending phases of the squat cycle, the medial gastrocnemius was more active in the ML malaligned squat (65–69%, 75–78%, and 85–94%) compared with the control squat.
    squat      knee valgus                     quota        Maintaining proper sagittal and frontal plane alignment during a squat is essential to target and strengthen the quadriceps muscle group effectively.
    squat      knee valgus                     quota        Avoiding medial knee displacement ensures that the rectus femoris remains active during the descent into peak knee flexion.
    squat      knee valgus                     rank         Allowing frontal plane malalignment, such as medial knee displacement, alters the muscle activation strategy and decreases quadriceps activation.
    squat      knee valgus                     rank         Frontal plane malalignment decreased rectus femoris activation during descent into peak knee flexion and increased activation in the knee flexors.
    squat      knee valgus                     quota        Medial knee displacement during squats changes the nature of the exercise by decreasing quadriceps activation and increasing hamstring and gastrocnemii activity.
    squat      knee valgus                     rank         Increased coactivation of the gastrocnemii during malaligned squats indicates an unstable knee joint position with increased anterior and medial knee displacement.
    squat      knee valgus                     quota        Medial knee displacement (medio-lateral malalignment) is a common error during a bodyweight bilateral squat.
    squat      knee valgus                     rank         Both the medio-lateral and antero-posterior malaligned squats increased anterior knee displacement by approximately 0.07 and 0.15 m, respectively.
    squat      knee valgus                     rank         Malaligned squats in the frontal and sagittal plane significantly alter muscle activation patterns in the lower extremity, increasing activation in hamstring and gastrocnemius muscles compared with a control squat.
    squat      knee valgus                     rank         Increased cocontraction of the knee flexors and gastrocnemii during malaligned squats may be in an effort to stabilize the ankle, knee, and hip during flexed knee stance, indicating that malaligned knee positions may be potentially injurious.
    squat      knee valgus                     rank         Medial and anterior knee displacement increases activation of the hamstrings and gastrocnemii, which can lead to tightness and pain in the hamstring or gastrocnemii.
    squat      knee valgus                     rank         Frontal and sagittal plane knee excursion significantly alters quadriceps activation patterns during squatting, changing the demands of the task on the knee musculature.
    squat      knee valgus                     rank         Altering knee position to varus or valgus did not significantly affect the VMO:VL EMG ratio (p = 0.44) in semi-squat exercises.
    squat      knee valgus                     rank         For a neutral squat alignment, position the feet 30 cm apart at the heel with a 7° external rotation, ensuring the knees track directly over the big toe.
    squat      knee valgus                     rank         Keep the knees aligned in a neutral path over the toes rather than caving inward or pushing excessively outward.
    squat      knee valgus                     quota        Allowing the knees to cave inward (valgus or 'knees in') during the descent or ascent of the squat.
    squat      knee valgus                     quota        Allowing the knees to cave inward (valgus) alters the relative activation of the vastus medialis obliques (VMO) and vastus lateralis (VL), which act antagonistically on patellar tracking.
    squat      knee valgus                     rank         Allowing the knees to cave into a valgus position alters the muscle activation patterns of the vastus medialis oblique (VMO) and vastus lateralis (VL).
    squat      knee valgus                     quota        Allowing the knees to cave inward (valgus position) or push outward (varus position) during a squat alters the knee movement path from the recommended neutral alignment.
    squat      knee valgus                     rank         The hip abductors, including the gluteus medius and minimus, must stabilize the femurs during the squat to prevent the knees and hips from rotating inward during descent.
    squat      knee valgus                     quota        Internal rotation of the femurs during descent, which may be caused by tight hip adductors.
    squat      knee valgus                     quota        The knees should track over the toes throughout the squat motion, maintaining a neutral frontal plane knee position where the foot creates an in-line hinge with knee motion.
    squat      knee valgus                     rank         To maintain proper knee alignment, the lateral aspect of the knee should not cross the vertical plane of the medial malleolus.
    squat      knee valgus                     quota        Experiencing knee valgus, where the knees cave inward and the medial aspect of either knee passes the medial malleolus.
    squat      knee valgus                     rank         A lack of strength in the medial gastrocnemius, tibialis anterior, and/or tibialis posterior decreases the athlete's ability to control knee valgus and foot pronation motions.
    squat      knee valgus                     rank         The gluteus medius plays a critical role in controlling femoral and knee alignment in the frontal plane.
    squat      knee valgus                     quota        Allowing knee valgus (knees caving inward) during the squat, which is commonly associated with overactive adductors and tensor fasciae latae (TFL) along with underactive gluteal musculature.
    squat      knee valgus                     rank         Keep the knees aligned over the second and third toes during the movement.
    squat      knee valgus                     quota        Lacking ankle mobility in the talocrural joint, which forces the talocalcaneal joint to pronate and evert, driving the knees inward.
    squat      knee valgus                     quota        Allowing limitations in adductor extensibility to cause valgus knee collapse during the deep phase of the squat.
    squat      knee valgus                     rank         Lacking ankle mobility causes the talocalcaneal joint to pronate and evert, which drives the knees inward and increases stress lines along the ACL.
    squat      knee valgus                     rank         Maintain knee and foot alignment, ensure proper hinging and timing of forward knee translation, and facilitate adequate ankle mobility.
    squat      knee valgus                     quota        Allowing the knees to cave inward so that the outside of the knee crosses the medial malleolus.
    squat      knee valgus                     rank         ACL injuries occur at a four to six fold greater incidence in females than males and have been associated with increased knee valgus angles.
    squat      knee valgus                     rank         Increased knee valgus angles are associated with a significantly higher risk of ACL injuries.
    squat      knee valgus                     rank         Knee valgus movement dysfunction may be caused by hip muscular weakness, ankle dorsiflexion limitations, or over-pronation.
    squat      knee valgus                     rank         At the bottom position, arms should stay straight, there should be no excessive forward lean, feet should stay pointing straight, heels should stay on the ground, and knees should stay in line with the feet.
    squat      knee valgus                     quota        Knee valgus during a squat may be the result of an overpronation problem.
    squat      knee valgus                     rank         Perform the clamshell exercise with a resistance band to strengthen weak hip external rotators and mitigate valgus collapse.
    squat      knee valgus                     quota        Allowing knee valgus (knees caving inward) to occur during the movement.
    squat      knee valgus                     rank         Knee valgus has been shown as a contributing factor to nearly 40,000 ACL injuries per year.
    squat      knee valgus                     rank         Paterno and colleagues found that weak hip external rotators, which can cause valgus collapse of the knee, lead to an eight times greater risk of sustaining a second ACL injury.
    squat      knee valgus                     rank         Knee valgus (valgus collapse) acts as a contributing factor to ACL injuries.
    squat      knee valgus                     rank         Weak hip external rotators leading to valgus collapse of the knee results in an eight times greater risk of sustaining a second ACL injury.
    squat      knee valgus                     rank         Your knees must stay in alignment with your feet when viewed from the front.
    squat      knee valgus                     rank         Inadequate hip stability can cause your knees to track incorrectly and move toward the midline of your body.
    squat      knee valgus                     rank         Allowing your knees to move toward the midline of your body (caving inward) increases torque on the knee joint.
    squat      knee valgus                     rank         Letting your knees bow inward toward each other as you ascend or descend, which may result from poor gluteal and hip rotator strength.
    squat      knee valgus                     rank         When your knees come out of alignment and bow inward, there is torque at your knee, which can lead to injury.
    squat      knee valgus                     tag_filter   Maintain proper mediolateral and anteroposterior alignment during the squat to ensure balanced muscle activation and joint kinematics.
    squat      partial squat                   margin       Attempting to squat with limited weight-bearing ankle dorsiflexion range of motion, which restricts the depth of the squat.
    squat      partial squat                   margin       Limited weight-bearing ankle dorsiflexion range of motion alters lower extremity kinematics, specifically reducing peak knee flexion and ankle dorsiflexion displacement, which prevents the lifter from reaching full squat depth.
    squat      partial squat                   margin       Limited ankle dorsiflexion range of motion restricts knee-flexion displacement, which directly limits squat depth and can result in a shallower squat.
    squat      partial squat                   margin       Ensure adequate ankle dorsiflexion range of motion to allow for optimal knee flexion and squat depth.
    squat      partial squat                   margin       Squatting with limited ankle dorsiflexion restricts knee forward travel and knee flexion, leading to a shallower squat.
    squat      partial squat                   margin       Limited ankle dorsiflexion restricts knee flexion displacement, which directly prevents the lifter from reaching full squat depth.
    squat      partial squat                   rank         Maintaining adequate weight-bearing ankle dorsiflexion range of motion is essential for achieving proper knee-flexion displacement and sagittal-plane depth during squatting tasks.
    squat      partial squat                   margin       Squatting with limited ankle dorsiflexion range of motion, which restricts knee and ankle sagittal-plane displacement and results in smaller peak knee-flexion angles.
    squat      partial squat                   rank         Individuals with limited weight-bearing lunge ankle dorsiflexion range of motion displayed less sagittal-plane displacement at the knee and ankle during squatting, with effect sizes ranging from 1.31 to 1.86.
    squat      partial squat                   margin       Decreased knee flexion (shallower squat depth) results in a larger patellar tendon-tibial shaft angle, producing greater anterior tibial shear force during quadriceps contraction.
    squat      partial squat                   rank         Decreased knee flexion reduces the ability of the hamstrings to offset anterior tibial shear forces and reduce ACL loading.
    squat      partial squat                   rank         Test degrees of hip flexion, external rotation, and abduction synergistically to find the maximum pain-free hip flexion angle, which represents the anatomical limit for squat depth.
    squat      partial squat                   margin       Ignoring individual anatomical variations in femoral version and acetabular orientation when prescribing squat stance and depth.
    squat      partial squat                   margin       Squat stance width and toe-out angle should be customized based on the individual's hip anatomy to maximize comfort, depth, and proper execution.
    squat      partial squat                   margin       Adjust stance width and toe-out angles to find the combination that allows the athlete to achieve the best squatting depth with the least compensations.
    squat      partial squat                   rank         The contact area of the patella increases and moves proximally as the knee flexes to 90 degrees, which helps distribute and compensate for the larger patellofemoral joint reaction forces.
    squat      partial squat                   rank         Maintaining quadriceps flexibility is necessary to avoid limitations in knee flexion.
    squat      partial squat                   rank         Experiencing limited knee flexion during lower body movements due to tightness of the quadriceps muscle.
    squat      partial squat                   margin       Performing shallow squats at only 20 degrees of knee flexion, which limits the relative activation of the vastus medialis obliquus.
    squat      partial squat                   rank         Squatting to deeper angles, such as 50 degrees and 80 degrees of knee flexion, increases the VMO:VL muscle activation ratio compared to shallow 20-degree squats.
    squat      partial squat                   margin       Performing shallow squats at 20 degrees of knee flexion limits the activation of the vastus medialis oblique (VMO) relative to the vastus lateralis (VL).
    squat      partial squat                   margin       Increasing squat depth from 20° to 50° or 80° of knee flexion significantly increases the VMO:VL muscle activation ratio.
    squat      partial squat                   margin       Squatting to a shallow depth of only 20° of knee flexion limits the activation ratio of the vastus medialis obliquus relative to the vastus lateralis.
    squat      partial squat                   rank         Both 50° and 80° squat depths showed significant increases in VMO:VL ratio compared with the 20° squat depth.
    squat      partial squat                   margin       Descend until the top of the thigh is at least parallel with the ground and the hip joint is at least level with or slightly below the knee joint.
    squat      partial squat                   margin       The athlete should squat down until the top of the thighs are at least parallel to the ground.
    squat      partial squat                   margin       The athlete should achieve full depth with the tops of the thighs at least parallel to the ground without any disjointed deviations noted at the knee, ankle, or hips.
    squat      partial squat                   margin       At the proper depth, the femurs are slightly past parallel to the ground, hips are back, tibias are positioned vertical, and feet are entirely on the ground.
    squat      partial squat                   margin       Without squatting to the proper depth, the hamstrings and gluteus muscular complex may not be adequately challenged.
    squat      partial squat                   rank         Training at shallower knee flexion can influence quadriceps-dominant sport skill performance, which can limit performance and increase injury risk.
    squat      partial squat                   margin       Failing to train at deeper depths prevents the reduction of quadriceps dominance strategies that are purported to increase injury risk.
    squat      partial squat                   margin       The appropriate squat depth is the deepest position a client can achieve while maintaining a neutral spine, foot stability, proper joint alignment, and movement control.
    squat      partial squat                   margin       Increase squat depth past 90 degrees if the training intent is to increase hip extensor strength.
    squat      partial squat                   rank         Perform hamstring foam rolling and seated hamstring stretches to address overactive and tight posterior chain muscles if you experience difficulty descending properly during a squat.
    squat      partial squat                   rank         Experiencing difficulty descending properly due to overactive and tight hamstring and hip muscles.
    squat      partial squat                   margin       In a standard squat, you only bend down until your thighs are parallel with the ground, with knees bent at around a 90-degree angle.
    squat      partial squat                   margin       At deep squat depths, the backs of your thighs come into contact with the backs of your calves, which has been shown to decrease the compressive load on your knee joint.
    squat      partial squat                   rank         Some researchers believe compressive forces in the knee may be higher in a partial squat than in a deep squat.
    squat      partial squat                   margin       Failing to reach deep squat depth prevents the backs of your thighs from contacting the backs of your calves, which increases the compressive load on your knee joint and may raise the risk of injury.
    squat      partial squat                   margin       Performing shallow squats with heavier weight instead of deep squats with lighter weight.
    squat      partial squat                   margin       Limited ankle dorsiflexion range of motion reduces peak knee flexion and displacement during squatting, which prevents achieving full squat depth.
    squat      partial squat                   margin       Training with deep squats elicits more favorable adaptations on knee extensor muscle size and function compared with training with shallow squats.
    squat      partial squat                   margin       Performing shallow squats instead of deep squats, which limits adaptations in knee extensor muscle size and function.
    squat      partial squat                   margin       Training with shallow squats results in inferior adaptations on knee extensor muscle size and function compared to deep squats.
    squat      partial squat                   margin       Perform squats to a mid-range depth of 40 to 90 degrees of knee flexion to increase levels of VMO activation relative to the VL, compared to a shallow depth of 0 to 30 degrees.
    squat      partial squat                   margin       Squatting deeper increases the overall magnitude of muscle contraction and loading, resulting in greater training effects through the overload principle compared to shallower squats.
    squat      partial squat                   margin       Performing shallow squats (0 to 30 degrees of knee flexion) limits VMO activation relative to the VL and reduces the overall magnitude of muscle contraction.
    squat      partial squat                   rank         VMO has increased levels of activation, relative to VL, when semi-squat exercises are performed to a mid-range (40-90 degrees) of knee flexion, as opposed to an early range (0-30 degrees) depth.
    squat      partial squat                   rank         Training with exercises that result in a VMO:VL ratio lower than 1:1 (such as shallow squats) will result in greater strength gains in the VL muscle, potentially increasing the lateral force acting on the patella and thus increasing patellofemoral symptoms.
    push-up    hip sag                         margin       The standard push-up requires a general stiffening of the knee joints, hip joints, pelvis, and spine to keep the body in a straight line from head to feet.
    push-up    hip sag                         margin       Maintain a rigid spine and lower-extremity segments throughout the push-up movement.
    push-up    hip sag                         rank         Maintain an angle of approximately 180 degrees between the upper and lower body during the exercise.
    push-up    hip sag                         margin       Allowing excessive hip sagging during the movement.
    push-up    hip sag                         rank         Brace the core to maintain a neutral spine throughout the movement.
    push-up    hip sag                         margin       Maintain a straight line from the head to the heels.
    push-up    hip sag                         margin       Allowing the trunk to collapse during the movement.
    push-up    hip sag                         margin       Losing core engagement, sagging the hips, elevating the hips, or adopting a forward-head posture reduces exercise effectiveness and reinforces poor movement patterns.
    push-up    hip sag                         margin       Allowing the hips to sag during the movement.
    push-up    hip sag                         margin       Allowing the hips to sag indicates core disengagement and reduces exercise effectiveness.
    push-up    hip sag                         margin       Ideal alignment during a push-up requires that the kinetic chain checkpoints—ears, shoulders, hips, knees, and ankles—all remain in one straight line during both the descent and ascent.
    push-up    hip sag                         margin       Allowing the low back to arch or sag during a push-up decreases engagement of the deeper core stabilizers, increases involvement of the lumbar erectors, and increases stress on the vertebral discs.
    push-up    partial range of motion         margin       Ensure the correct depth of 90 degrees of elbow flexion is acquired during each repetition.
    push-up    partial range of motion         margin       A standard push-up involves flexing the elbows until the chest approaches the floor, followed by extending the elbows back to the initial position.
    push-up    partial range of motion         margin       Achieving deeper elbow flexion during push-ups increases the mechanical load and muscular demand on the triceps.
    push-up    partial range of motion         margin       Failing to reach deep elbow flexion reduces the mechanical load and contractile demand placed on the triceps muscle.
    push-up    partial range of motion         margin       Failing to lower completely to the down position reduces the peak resistance and muscular demand of the exercise.
    push-up    partial range of motion         margin       Not reaching the full down position prevents the whole-body center of mass from moving further from the point of contact, which reduces the torque and subsequent force required by the upper body musculature.
    push-up    partial range of motion         margin       It may be necessary to temporarily modify the range of motion of the push-up to accommodate strength limitations at the bottom of the movement, progressively increasing the depth as strength improves.
    push-up    partial range of motion         margin       Lower the body with control until the chest approaches the floor.
    push-up    partial range of motion         margin       Descend until your chest nearly touches the floor or your elbows bend to approximately 90 degrees, whichever comes first based on mobility.
    push-up    partial range of motion         margin       Not achieving adequate range of motion.
    push-up    partial range of motion         margin       Descend until your chest nearly touches the floor or your elbows bend to approximately 90 degrees.
    push-up    partial range of motion         margin       Not achieving adequate range of motion limits chest stretch and development.
    lunge      excessive forward trunk lean    margin       Leaning the torso forward instead of maintaining an upright position.
    lunge      excessive forward trunk lean    margin       Keep the upper body perpendicular to the ground during the lunge.
    lunge      excessive forward trunk lean    margin       Keep the upper body upright during the lunge to maintain proper alignment.
    lunge      excessive forward trunk lean    margin       Maintain an upright trunk during the lunge to avoid excessive forward or lateral trunk movement.
    lunge      excessive forward trunk lean    margin       Allowing the trunk movement to exceed approximately 10 degrees of deviation from an upright posture.
    lunge      excessive forward trunk lean    margin       Allowing excessive compensatory movements such as marked trunk lean or pelvic rotation.
    lunge      excessive forward trunk lean    margin       Maintain the upper body upright and facing forward during the lunge to control movement of the upper torso.
    lunge      excessive forward trunk lean    margin       Allowing excessive forward movement of the upper body and trunk segment as the knee flexion angle increases.
    lunge      excessive forward trunk lean    margin       Excessive forward movement of the upper body and trunk segment generates a large reaction force on the ground surface contacted by the front foot.
    lunge      excessive forward trunk lean    margin       Avoid excessive anterior movement of the upper torso and lower leg to control the load exerted on the front knee joint.
    lunge      excessive forward trunk lean    rank         Anterior movement of the upper torso and lower leg significantly increases the load exerted on the knee joint of the front leg.
    lunge      excessive forward trunk lean    margin       Anterior movement of the upper torso and lower leg increases the load exerted on the knee joint of the front leg, which may elevate knee joint compression forces and impact ACL injury risk.
    lunge      excessive forward trunk lean    rank         Higher activation in the erector spinae is observed when the trunk is inclined.
    lunge      excessive forward trunk lean    rank         Excessive forward trunk lean increases the activation of the erector spinae.
    lunge      excessive forward trunk lean    margin       Inclining the trunk forward during a lunge shifts the load, resulting in higher activation of the erector spinae.
    lunge      excessive forward trunk lean    margin       During the lowest position of the forward lunge, the trunk should be maintained in a reasonably upright posture.
    lunge      excessive forward trunk lean    rank         The thoracic spine should remain straight and vertical, with the shoulders positioned directly above the hips.
    lunge      excessive forward trunk lean    rank         The trunk should remain vertical with the lumbar spine in a neutral position.
    lunge      excessive forward trunk lean    rank         Directing the head position and direction of gaze downward increases trunk flexion.
    lunge      excessive forward trunk lean    margin       Maintain an upright torso position throughout the lunge movement.
    lunge      excessive forward trunk lean    margin       Failing to maintain an upright torso alters muscle activation patterns during the lunge.
    lunge      excessive forward trunk lean    rank         The torso should be straight and the abdominals should be tight.
    lunge      excessive forward trunk lean    rank         Beginners tend to lean too far forward during the eccentric phase of the exercise.
    lunge      excessive forward trunk lean    margin       To compensate for balance and strength challenges, the torso can lean forward during the downward phase.
    lunge      excessive forward trunk lean    margin       Leaning too far forward during the eccentric phase can increase the shear force at the knee joint, increasing the risk of injury or pain.
    lunge      excessive forward trunk lean    margin       Leaning the trunk forward during a lunge shifts the muscular demand, increasing the load on the hip extensors and ankle plantar flexors while reducing the load on the knee extensors.
    lunge      excessive forward trunk lean    margin       Maintain a vertical and upright position of the trunk during a normal forward lunge.
    lunge      excessive forward trunk lean    margin       Leaning the trunk forward during a lunge increases hip flexion, hip extensor impulse, and ankle plantar flexor impulse.
    lunge      excessive forward trunk lean    margin       Keeping the trunk erect or extended during a lunge increases peak ankle dorsiflexion, peak knee flexion, and knee extensor impulse.
    lunge      excessive forward trunk lean    margin       Leaning the trunk forward excessively reduces the knee extensor impulse and peak knee flexion, shifting the training load away from the quadriceps.
    lunge      excessive forward trunk lean    rank         Leaning the trunk forward (LTF) shifts the mechanical demand (joint impulse) away from the knee joint and increases the loading on the hip extensors (gluteus maximus and biceps femoris) and ankle plantar flexors.
    lunge      excessive forward trunk lean    rank         Keeping the trunk erect or extended (LTE) increases the mechanical demand (joint impulse) on the knee extensors and increases peak knee flexion and ankle dorsiflexion, which may increase stress on the knee joint.
    lunge      excessive forward trunk lean    margin       Leaning the trunk forward during a lunge increases the vertical ground reaction force on the lead leg by 27%, which increases the loading impulse on all joints of the lead lower extremity.
    lunge      excessive forward trunk lean    rank         Leaning the trunk forward shifts the body's center of mass forward relative to the base of support, causing a 47% increase in plantar flexor impulse.
    lunge      excessive forward trunk lean    margin       Performing a forward lunge with the trunk forward increases the recruitment of the hip extensors.
    lunge      excessive forward trunk lean    margin       Performing a forward lunge with the trunk forward (LTF) is characterized by an increase in hip extensor impulse and a concomitant increase in the muscular actions of the hip extensors when compared to a normal lunge (NL).
    lunge      excessive forward trunk lean    margin       Leaning the trunk forward during a lunge increases the range of hip and trunk flexion, which shifts the body's center of mass forward and increases weight bearing on the lead lower extremity.
    lunge      excessive forward trunk lean    rank         Keep your body straight at all times, avoiding leaning forward or backward when standing or stepping.
    lunge      excessive forward trunk lean    rank         Leaning the torso forward or backward.
    lunge      excessive forward trunk lean    margin       If the lunge step is too long, you may have to lean forward to step.
    lunge      shallow lunge                   margin       Take a big step forward and slowly bend both knees until the back knee is just above the floor.
    lunge      shallow lunge                   margin       Perform the forward lunge by taking one step forward, placing the foot down, and flexing the front knee to approximately 90 degrees.
    lunge      shallow lunge                   margin       The holding phase of a forward lunge requires maintaining the body position at approximately 90 degrees of front knee flexion.
    lunge      shallow lunge                   margin       During the descending phase of the lunge, the front knee should be flexed to approximately 90 degrees.
    lunge      shallow lunge                   rank         The smallest vertical reaction force in both upward and downward phases was found at a targeted knee flexion angle of 100°.
    lunge      shallow lunge                   rank         In a study of eight subjects (aged 22.23±1.51 years), the 80° targeted knee flexion condition showed greater anterior and vertical knee joint movements, reaction force, and extensor moment at maximum knee flexion than both the 90° and 100° conditions (p<.05).
    lunge      shallow lunge                   rank         The 80° knee flexed angle condition resulted in greater peak joint reaction force and extensor moment compared with both 90° and 100° conditions between the upward and downward phases of the forward lunge.
    lunge      shallow lunge                   rank         A shallower front knee flexion angle of 80° increases the peak joint reaction forces and extensor moments on the knee joint compared to deeper angles of 90° and 100°.
    lunge      shallow lunge                   margin       Achieving a knee flexion angle of 90 degrees or greater (such as 100 degrees) on the front leg during a forward lunge reduces the knee extensor moment compared to a shallower 80-degree angle.
    lunge      shallow lunge                   rank         A deeper knee flexion angle of 100 degrees reduces lateral and vertical joint reaction forces compared to shallower angles of 80 and 90 degrees.
    lunge      shallow lunge                   rank         The knee extensor moment is significantly higher at an 80-degree knee flexion angle (0.980 ± 0.14 Nm/BW) compared to 90 degrees (0.717 ± 0.22 Nm/BW) and 100 degrees (0.362 ± 0.27 Nm/BW).
    lunge      shallow lunge                   rank         Under the 80-degree knee flexion condition, the knee joint displacement showed significantly larger anterior (40.984 ± 4.58 cm) and vertical (-6.641 ± 0.79 cm) movements than under the 90-degree and 100-degree conditions.
    lunge      shallow lunge                   rank         At 100 degrees of knee flexion, the vertical joint reaction force is significantly lower (-5.640 ± 3.08 N/BW) compared to 90 degrees (-7.725 ± 0.84 N/BW) and 80 degrees (-8.956 ± 0.79 N/BW).
    lunge      shallow lunge                   margin       Allowing the front knee to remain in a shallow 80-degree angle increases the knee extensor moment and vertical joint reaction forces, placing greater mechanical demand on the knee extensors and joint structures.
    lunge      shallow lunge                   margin       Performing a forward lunge with a smaller knee flexion angle of 80 degrees increases the knee extension moment compared to larger angles of 90 and 100 degrees.
    lunge      shallow lunge                   rank         Under the 80 degree knee flexion angle, the knee extension moment was statistically highest at 1.039 Nm/BW in the downward phase and 1.096 Nm/BW in the upward phase, compared to 0.810 Nm/BW and 0.978 Nm/BW at 90 degrees, and 0.532 Nm/BW and 0.731 Nm/BW at 100 degrees.
    lunge      shallow lunge                   margin       A shallower lunge of 80 degrees of knee flexion generates a higher knee extension moment, which increases the mechanical demand on the knee extensor musculature.
    lunge      shallow lunge                   margin       Aim for a deeper knee flexion angle, such as 100 degrees, during the forward lunge to minimize peak vertical, medial, and anterior reaction forces in the knee joint.
    lunge      shallow lunge                   margin       Performing a shallow lunge with a knee flexion angle of only 80 degrees increases the peak knee extension moment during both the downward and upward phases.
    lunge      shallow lunge                   margin       Allowing insufficient front knee flexion during a lunge increases peak medial and anterior reaction forces in the knee joint.
    lunge      shallow lunge                   rank         Peak knee extension moment showed a statistically higher value in downward and upward phases at a targeted knee flexion angle of 80° than at 90° and 100°.
    lunge      shallow lunge                   rank         The peak medial and anterior reaction forces in both upward and downward phases decreased as the knee flexion angle increased from 80° to 100°.
    lunge      shallow lunge                   rank         Gluteus medius activity is significantly higher with a larger step-length.
    lunge      shallow lunge                   margin       Performing a shallow lunge with a shorter step-length reduces gluteus medius activation.
    lunge      shallow lunge                   margin       Using a shorter step length (shallow lunge) limits the recruitment and activation of the gluteus medius muscle.
    lunge      shallow lunge                   margin       Maintain a consistent movement rhythm and full range of motion throughout the lunge, avoiding compensatory strategies like excessive pelvic displacement or lateral trunk flexion.
    lunge      shallow lunge                   margin       During a forward lunge, the peak knee flexion angle of the leading leg reaches 112.73 ± 7.85° in pre-fatigue and 113.86 ± 6.17° in post-fatigue conditions.
    lunge      shallow lunge                   rank         The knee joint range of motion during a forward lunge is 87.88 ± 5.86° in pre-fatigue and increases to 92.58 ± 8.83° in post-fatigue conditions.
    lunge      shallow lunge                   margin       Standardizing the forward lunge step length to match individual leg length increases gluteus medius activation and the muscular effort required to maintain movement control.
    lunge      shallow lunge                   rank         Allowing an unstandardized or self-selected step length that is shorter than individual leg length can lead to lower gluteus medius activation.
    lunge      shallow lunge                   rank         Using a shorter, self-selected step length reduces the demand on the gluteus medius, which decreases the muscular effort available to maintain movement control and execution consistency.
    lunge      shallow lunge                   margin       Executing the forward lunge with a deeper position involves increasing peak ankle and knee joint angles.
    lunge      shallow lunge                   margin       When observing the forward lunge from the side, the athlete should step out far enough so that the lead knee is directly over the lead foot and the heel remains in contact with the ground as the center of mass moves toward the ground.
    lunge      shallow lunge                   margin       Both the anterior and posterior legs should achieve a knee joint range of motion of 0 to 90 degrees during the lunge.
    lunge      shallow lunge                   margin       The traditional lunge is characterized by taking a moderately large step forward so that the thigh of the lead leg is parallel to the ground.
    lunge      shallow lunge                   margin       Using a longer step length during a lunge helps minimize anterior tibial translation over the toes and reduces joint forces.
    lunge      shallow lunge                   margin       A lunge with a shorter step length results in joint forces almost two times higher than a lunge with a longer step.
    lunge      shallow lunge                   margin       A short step length causes anterior tibial translation over the toes, which increases joint forces in the knee.
    lunge      shallow lunge                   rank         A smaller knee angle reduces quadriceps muscle activity during the movement.
    lunge      shallow lunge                   rank         Ensure the distance between the front foot and back foot is a length that is greater than a walking stride.
    lunge      shallow lunge                   rank         While keeping the torso straight and abdominals tight, lower the hips until both knees are bent at about a 90-degree angle, if possible.
    lunge      shallow lunge                   margin       Quite often, the lunge is plagued from the start due to a stride length that is too short.
    lunge      shallow lunge                   rank         If the feet are too close together, the downward movement results in an increased amount of stress on the knee joint, specifically the patellar tendon.
    lunge      shallow lunge                   margin       Making the lunge step too short or too long.
    lunge      shallow lunge                   margin       Lower the trailing knee until it is approximately 2 to 3 cm short of contacting the ground.
    lunge      shallow lunge                   margin       An upright trunk tends to create a 90/90 lunge where both knees are at 90-degree angles at the bottom of the movement.
    lunge      shallow lunge                   rank         The length of the lunge should be about two times your hip width.
    lunge      shallow lunge                   margin       If the lunge step is too short, the front heel may come off the ground.
    lunge      shallow lunge                   tag_filter   Perform the forward lunge by taking an elongated forward step, flexing the lead hip and knee, and dorsiflexing the lead ankle while lowering the body toward the floor.
    lunge      shallow lunge                   tag_filter   Control the descent during a lunge so that you stop just before the trailing knee contacts the ground.
    lunge      shallow lunge                   tag_filter   The forward lunge should be executed by stepping anteriorly while the back foot remains in contact with the starting surface, descending until the rear knee is approximately at ankle height.
    lunge      insufficient back knee flexion  rank         Take a big step forward and slowly bend both knees until the back knee is just above the floor.
    lunge      insufficient back knee flexion  margin       The forward lunge should be executed by stepping anteriorly while the back foot remains in contact with the starting surface, descending until the rear knee is approximately at ankle height.
    lunge      insufficient back knee flexion  margin       The back knee should be flexed during the lunge.
    lunge      insufficient back knee flexion  margin       Both the anterior and posterior legs should achieve a knee joint range of motion of 0 to 90 degrees during the lunge.
    lunge      insufficient back knee flexion  rank         The knee joint range of motion is similar in both the anterior and posterior leg positions, spanning 0 to 90 degrees.
    lunge      insufficient back knee flexion  margin       Control the descent during a lunge so that you stop just before the trailing knee contacts the ground.
    lunge      insufficient back knee flexion  margin       A traditional lunge utilizes a moderate step that results in the back knee ending at approximately a 90-degree angle.
    lunge      insufficient back knee flexion  rank         While keeping the torso straight and abdominals tight, lower the hips until both knees are bent at about a 90-degree angle, if possible.
    lunge      insufficient back knee flexion  rank         At the lowest point of the downward movement, the hip, knee, and ankle joints should be no less than 90 degrees.
    lunge      insufficient back knee flexion  rank         Lower the body by flexing the lead and trailing knees simultaneously during the descent.
    lunge      insufficient back knee flexion  rank         Lower the trailing knee until it is approximately 2 to 3 cm short of contacting the ground.
    lunge      insufficient back knee flexion  margin       The target depth for the trailing knee was defined as 2 to 3 cm short of contacting the ground.
    lunge      insufficient back knee flexion  margin       An upright trunk tends to create a 90/90 lunge where both knees are at 90-degree angles at the bottom of the movement.
    lunge      insufficient back knee flexion  rank         As the front foot hits the floor, lower the back knee towards the floor.
    bicep-curl elbow flare                     margin       The elbows must be kept close to the body during the movement.
    bicep-curl elbow flare                     margin       Because the biceps brachii is a biarticular muscle responsible for both elbow flexion and shoulder stabilization, it can cause the elbows to pull forward during curls.
    bicep-curl elbow flare                     margin       Tuck your elbows so that they are flush against your body and near the waist, keeping them in the same position during the entire range of motion.
    bicep-curl partial range of motion         margin       The movement should start with the elbow joint in full extension, flexing the forearm until the dumbbells reach the top of the shoulders, and then returning to the starting position.
    bicep-curl partial range of motion         margin       Use an elbow stabilizing plate or maintain strict elbow positioning to ensure that the full range of motion of the elbow joint is achieved and to prevent swinging the elbows.
    bicep-curl partial range of motion         margin       Exercising muscles at a longer length by completing a full range of motion of the elbow joint produces more muscle damage.
    bicep-curl partial range of motion         margin       A systematic review by Kassiano et al. [26] found that a partial range of motion at long muscle lengths is sufficient to promote optimal muscle growth for the biceps brachii.
    bicep-curl partial range of motion         margin       Employ a range of motion that allows the target muscle to be fully stretched.
    bicep-curl partial range of motion         margin       Performing partial repetitions at shorter muscle lengths rather than longer muscle lengths.
    bicep-curl partial range of motion         margin       Partial repetitions at shorter-muscle lengths are not as hypertrophic as partial repetitions at longer-muscle lengths.
    bicep-curl partial range of motion         rank         To maximize muscle growth, training should emphasize a full range of motion, specifically focusing on training at long muscle lengths.
    bicep-curl partial range of motion         margin       Start the bicep curl with the elbow in full extension and the forearm supinated.
    bicep-curl partial range of motion         margin       Failing to start the movement with the elbow in full extension.
    bicep-curl partial range of motion         margin       Training at longer muscle lengths elicits more favorable muscle growth compared to training at shorter muscle lengths.
    bicep-curl partial range of motion         margin       Select exercises and ranges of motion that impose a relevant external torque when the muscle is in a lengthened position to optimize muscle hypertrophy.
    bicep-curl partial range of motion         margin       Using a restricted range of motion that avoids training the muscle at longer, fully stretched lengths.
    bicep-curl partial range of motion         margin       Failing to train at longer muscle lengths or select ranges of motion with relevant external torque in the lengthened position limits the potential for optimal muscle hypertrophy.
    bicep-curl partial range of motion         margin       Training through a full range of motion or focusing on the initial range of motion where the muscle is at longer lengths optimizes muscle hypertrophy compared to training only at short muscle lengths.
    bicep-curl partial range of motion         rank         Contractions performed at moderate to longer muscle lengths are associated with more favorable sarcomere overlap and passive elastic contributions, which can improve active force-generating capacity.
    bicep-curl partial range of motion         margin       Failing to reach full extension at the bottom of a curl and training exclusively in the final, shortened range of motion limits muscle growth.
    bicep-curl partial range of motion         rank         Studies show that both full range of motion (ROM) and initial ROM training (contracting exclusively at longer muscle lengths) are superior to training at the final ROM (contracting exclusively at shorter muscle lengths) for inducing muscle hypertrophy.
    bicep-curl partial range of motion         margin       Performing contractions exclusively at shorter muscle-tendon unit lengths (more flexed joint positions) reduces cross-bridge formation and force output due to suboptimal sarcomere overlap.
    bicep-curl partial range of motion         margin       Restricting movement to the final range of motion (short muscle lengths) results in suboptimal muscle hypertrophy compared to utilizing the initial range of motion where the muscle is fully stretched.
    bicep-curl partial range of motion         margin       Training at longer muscle lengths or medium muscle lengths enhances the physiological responses and hypertrophic stimulus compared to training at short muscle lengths.
    bicep-curl partial range of motion         margin       Performing contractions in a range of motion where the muscle is stretched increases passive tension, which contributes to triggering hypertrophic signaling cascades.
    bicep-curl partial range of motion         rank         Force production and Akt activation were found to be higher when muscles contracted at medium lengths (ML) and long lengths (LL) compared to short lengths (SL), where activation was similar to unstimulated conditions.
    bicep-curl partial range of motion         rank         Phosphorylation levels of mechano-responsive kinases, specifically Akt and p70S6K, are contingent upon muscle length, with contractions at long lengths (LL) and medium lengths (ML) enhancing this response.
    bicep-curl partial range of motion         margin       Failing to train at longer muscle lengths reduces the mechanical tension and passive tension generated by elements like titin, which diminishes the overall hypertrophic stimulus.
    bicep-curl partial range of motion         rank         Concentric contractions that excessively shorten the muscle fiber increase the radial distance between actin and myosin filaments, which may decrease calcium interaction with troponin and diminish the muscle's capacity to generate active force.
    bicep-curl partial range of motion         margin       Training the bicep curl at longer muscle lengths, which corresponds to the initial range of motion starting from full elbow extension (0º), optimizes muscle hypertrophy.
    bicep-curl partial range of motion         margin       Ensuring the movement includes the bottom portion of the curl (initial ROM) is critical for targeting the distal region of the biceps brachii.
    bicep-curl partial range of motion         margin       Training the biceps at longer muscle lengths, such as the initial range of motion or full range of motion, promotes greater distal muscle hypertrophy.
    bicep-curl partial range of motion         margin       The range of motion variable serves as a means of training the muscle at lengthened positions with relevant torque in that position to maximize hypertrophy.
    bicep-curl partial range of motion         margin       Using mechanical stops or visual marks to control range of motion prevents self-regulating repetitions outside the desired range, which can negatively impact the muscle length-tension curve.
    bicep-curl partial range of motion         margin       Restricting the bicep curl to the top half of the movement (final ROM) reduces the hypertrophic stimulus at longer muscle lengths, resulting in significantly less muscle growth in the distal portion of the biceps brachii.
    bicep-curl partial range of motion         rank         Training muscles at longer muscle lengths promotes structural adaptations such as increased fascicle length and sarcomerogenesis.
    bicep-curl partial range of motion         margin       Avoiding training at longer muscle lengths, which limits the potential for length-dependent muscle adaptations.
    bicep-curl partial range of motion         rank         Structural adaptations (e.g., increased fascicle length, sarcomerogenesis) occur in the muscle after training at longer muscle lengths, theoretically attenuating the contribution of passive structures to force production in future training sessions.
    bicep-curl partial range of motion         rank         Failing to train at longer muscle lengths may prevent structural adaptations like increased fascicle length and sarcomerogenesis, which theoretically attenuates the contribution of passive structures to force production in future training sessions.
    bicep-curl partial range of motion         margin       Training at moderate to longer muscle lengths combined with meaningful external torque in that position is critical for maximizing hypertrophic adaptations.
    bicep-curl partial range of motion         margin       Utilizing a full range of motion or the initial range of motion combines training at longer muscle lengths with high external torque to induce greater muscle growth.
    bicep-curl partial range of motion         margin       Training only at shorter muscle lengths, such as the final range of motion, fails to optimize muscle growth.
    bicep-curl partial range of motion         margin       Failing to train at longer muscle lengths by restricting movement to shorter muscle lengths (final ROM) fails to optimize muscle hypertrophy.
    bicep-curl partial range of motion         margin       Training muscles at moderate to longer muscle lengths induces more favorable hypertrophy compared to training at shorter muscle lengths.
    bicep-curl partial range of motion         margin       Range of motion configurations should be used as a strategy to train muscles at longer lengths under relevant external torque to optimize muscular hypertrophy.
    bicep-curl partial range of motion         margin       Performing training or isometric contractions exclusively at shorter muscle lengths limits the hypertrophic response.
    bicep-curl partial range of motion         margin       Perform the exercise in a standing position with an emphasis on maintaining a controlled and consistent range of motion throughout the entire movement.
    bicep-curl partial range of motion         margin       Failing to flex the elbow past 90 degrees up to 135 degrees prevents the biceps brachii from experiencing the highest joint moments and muscle forces.
    bicep-curl partial range of motion         margin       Perform exercises through a full range of motion rather than rushing through partial repetitions.
    bicep-curl partial range of motion         margin       Rushing through repetitions and performing partial range of motion reps.
    bicep-curl partial range of motion         rank         A tempo utilizing controlled eccentrics of 2 to 3 seconds is recommended to maximize hypertrophy compared to rushed partial reps.
    bicep-curl partial range of motion         rank         Bring the implement as far up as you are able to, maximizing the range of motion.
    bicep-curl partial range of motion         tag_filter   Performing preacher curls with an intermediate range of motion that omits the initial portion of the movement from 0 degrees to 49 degrees of elbow flexion.
    bicep-curl partial range of motion         tag_filter   Dumbbell supinating curls and Bayesian curls can be performed using either the initial range of motion (approximately 50% of full ROM) or a full range of motion to achieve similar hypertrophy in the elbow flexors.
    bicep-curl partial range of motion         tag_filter   Performing preacher curls only in the final range of motion (shortened position) limits muscle growth compared to training in the initial range of motion (lengthened position).
    bicep-curl partial range of motion         tag_filter   Utilizing a partial range of motion at long muscle lengths can be sufficient to promote optimal muscle growth for the biceps brachii.
    bicep-curl partial range of motion         tag_filter   Training the biceps preacher curl only in the final range of motion (shortened position) results in lower hypertrophy responses at the distal site of the biceps brachii and elbow flexors.
    bicep-curl partial range of motion         tag_filter   In a study by Pedrosa et al. on seated preacher curls, training the initial ROM (0º–68º) induced greater increases in biceps brachii cross-sectional area at the distal site (24.0%) compared to the final ROM of 68º–135º (13.1%), while proximal site gains were similar (20.0% vs 21.1%).

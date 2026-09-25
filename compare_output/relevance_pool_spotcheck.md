# Relevance pool spot-check

Read the disagreements first: they are where the LLM judge and the hand-made golden set
(eval/golden_chunks.json) disagree. Then the random sample per fault. Mark anything wrong
by editing `label` in eval/relevance_pool.json and set `"checked": true` on it.

## squat / butt wink — 122 candidates · relevant 41 · wrong_fault 61 · irrelevant 20

**Random sample**
- `irrelevant` [mistake] Using compensatory movement strategies during the squat due to improper mechanics.  
  _judge:_ Too vague; does not name or describe butt wink or its mechanics.
- `relevant` [principle] Your trunk and pelvis should stay neutral and aligned as you bend at your hips, with your pelvis remaining in a neutral position without tucking under or tilting backward.  
  _judge:_ Directly describes maintaining a neutral pelvis without tucking under or tilting backward.
- `wrong_fault` [mistake] Allowing the chest to drop or failing to retract the scapulae during the squat is a common deficit.  
  _judge:_ Describes chest drop and scapular retraction failure, a different fault.
- `irrelevant` [principle] Sufficient weight-bearing ankle dorsiflexion range of motion is required to allow proper ankle dorsiflexion and knee flexion displacement during a squat.  
  _judge:_ General statement on ankle dorsiflexion without linking to butt wink.
- `relevant` [principle] If you lack the appropriate mobility at your hips, knees, or ankles to maintain proper alignment during a deep squat, perform a squat in which your hips do not go below your knees.  
  _judge:_ Recommends limiting squat depth to prevent alignment breakdown and butt wink.

## squat / knee valgus — 189 candidates · relevant 118 · wrong_fault 38 · irrelevant 33

**Random sample**
- `relevant` [consequence] Limited ankle dorsiflexion range of motion can alter lower extremity movement patterns, which may manifest as medial knee displacement or knee-valgus collapse during squatting.  
  _judge:_ Describes how limited ankle dorsiflexion causes medial knee displacement during squats.
- `relevant` [finding] The medio-lateral malaligned squat resulted in significantly increased dorsiflexion, ankle inversion, knee flexion, knee abduction, and hip adduction during approximately 10% to 85% of the squat cycle compared with the control squat.  
  _judge:_ Reports kinematic consequences of mediolateral knee malalignment during squats.
- `irrelevant` [principle] Perform the lateral monster walk in a squat position rather than an upright straight leg position to generate greater gluteus maximus and medius muscle activity.  
  _judge:_ Details how to perform lateral monster walks without linking to knee valgus.
- `relevant` [mistake] Allowing the knees to cave inward so that the outside of the knee crosses the medial malleolus.  
  _judge:_ Defines what knees caving inward looks like with a specific threshold.
- `irrelevant` [principle] Squats are commonly taught with a 'knees over toes' neutral position, with the foot in a slightly externally rotated position.  
  _judge:_ General squat teaching information not directly tied to preventing or fixing knee valgus.

## squat / partial squat — 149 candidates · relevant 52 · wrong_fault 57 · irrelevant 40

**Random sample**
- `wrong_fault` [finding] A deep squat is defined as a squat in which your hips are below the height of your knees, meaning the angle of your knee joint is greater than 100 degrees at the lowest point.  
  _judge:_ Defines a different exercise variant, the deep squat.
- `irrelevant` [consequence] Squatting with deeper knee flexion increases patellofemoral joint compressive forces.  
  _judge:_ General biomechanical information about knee flexion depth and joint compressive forces.
- `wrong_fault` [mistake] Allowing the knees to cave inward medially during the squat.  
  _judge:_ Addresses knee valgus, a different squat fault.
- `relevant` [principle] Squatting deeper increases the overall magnitude of muscle contraction and loading, resulting in greater training effects through the overload principle compared to shallower squats.  
  _judge:_ Explains the overload principle advantage of deeper squats over shallow squats.
- `wrong_fault` [consequence] Overly restricted tibial translation during the squat increases anterior lean of the torso, which increases hip torque and lumbar shear forces.  
  _judge:_ About overly restricted tibial translation and trunk lean, different faults.

## push-up / hip sag — 93 candidates · relevant 13 · wrong_fault 17 · irrelevant 63

**Random sample**
- `relevant` [mistake] Allowing the low back to arch or sag during the push-up as fatigue sets in.  
  _judge:_ Low back arching or sagging is an alternate wording for hip sag.
- `irrelevant` [principle] Lower the body with control until the chest approaches the floor.  
  _judge:_ General execution cue for push-up descent.
- `relevant` [consequence] Losing core engagement, sagging the hips, elevating the hips, or adopting a forward-head posture reduces exercise effectiveness and reinforces poor movement patterns.  
  _judge:_ Explicitly addresses sagging hips and states the negative consequences of the fault.
- `irrelevant` [principle] Performing push-ups on an unstable suspension system forces the extremity musculature to play a greater role in joint stability and strains synergistic and stabilizing muscles.  
  _judge:_ Discusses joint stability demands on suspension push-ups generally.
- `wrong_fault` [mistake] Adopting a forward-head posture during the movement.  
  _judge:_ About forward-head posture, a different fault.

## push-up / partial range of motion — 97 candidates · relevant 13 · wrong_fault 18 · irrelevant 66

**Disagreements with golden set**
- `irrelevant` [finding] The study protocol monitored body form and required repetitions to be repeated if the correct depth of 90 degrees was not acquired.  
  _judge:_ Study protocol methodology regarding repetition repetition criteria.

**Random sample**
- `irrelevant` [consequence] Performing a push-up with the forearm in 90 degrees of internal rotation results in the greatest posterior and varus elbow shear forces.  
  _judge:_ Discusses elbow shear forces resulting from forearm rotation, not depth.
- `irrelevant` [principle] Narrow-width push-ups target the triceps more effectively by increasing triceps muscle activation and requiring a deeper range of elbow movement.  
  _judge:_ Explains triceps targeting in narrow push-ups; does not address the partial ROM fault.
- `irrelevant` [finding] Clapping push-ups outperform standard, slow eccentric, 1 hand on medicine ball, staggered hands, hands on 2 balls, 2 hands on 1 ball, rapid countermovement, 1 arm, and alternating plyometric push-up variations in pectoralis major and triceps brachii activity.  
  _judge:_ Compares muscle activity across numerous push-up variations.
- `irrelevant` [finding] During upper-extremity pressing motions, the lowest force is exerted at the bottom of the lift in shoulder horizontal abduction and elbow flexion, while the highest force is exerted near full elbow extension at an angle of approximately 120 degrees.  
  _judge:_ General biomechanical information about pressing strength curves.
- `wrong_fault` [mistake] Flaring the elbows too wide.  
  _judge:_ Refers to elbow flaring, which is a different fault.

## lunge / excessive forward trunk lean — 162 candidates · relevant 43 · wrong_fault 53 · irrelevant 66

**Random sample**
- `relevant` [principle] During the lowest position of the forward lunge, the trunk should be maintained in a reasonably upright posture.  
  _judge:_ Directly provides the correct upright trunk posture cue.
- `relevant` [finding] Anterior movement of the upper torso and lower leg significantly increases the load exerted on the knee joint of the front leg.  
  _judge:_ Explains how anterior torso movement increases front knee joint loading.
- `relevant` [consequence] Leaning the trunk forward shifts the body's center of mass forward relative to the base of support, causing a 47% increase in plantar flexor impulse.  
  _judge:_ Describes how forward trunk lean alters center of mass and plantar impulse.
- `wrong_fault` [consequence] Knee valgus and excessive side-to-side knee movement during the lunge raise concern regarding the potential increased risk of a knee injury.  
  _judge:_ Discusses knee valgus and mediolateral movement, not trunk lean.
- `irrelevant` [finding] An increase in targeted knee flexion angle during a forward lunge causes an increase in anterior-posterior (AP) and vertical movement in the front knee at the point of maximum knee flexion, as well as vertical reaction force and extension moment.  
  _judge:_ Discusses the effects of knee flexion angles on knee kinetics.

## lunge / shallow lunge — 160 candidates · relevant 58 · wrong_fault 48 · irrelevant 54

**Disagreements with golden set**
- `irrelevant` [finding] Mean gluteus medius (GMED) activation during the forward lunge was 19.83  8.30 %MVIC when step length and rhythm were standardized, compared to 11.3  8.3 %MVIC in unstandardized trials.  
  _judge:_ Specific experimental trial data comparing standardized and unstandardized conditions.
- `irrelevant` [mistake] Lunging with a short step length alters the demands on the knee joint.  
  _judge:_ Too vague to be helpful; does not state how demands are altered.
- `irrelevant` [principle] Variations in step length and torso angle can influence joint angles and muscle activity levels during a lunge.  
  _judge:_ General statement about variations in step length without addressing this fault.
- `irrelevant` [finding] The standardized step length for the lunge was set equal to the distance from the subject's greater trochanter to the floor.  
  _judge:_ Describes a study protocol measurement rather than exercise instruction.

**Random sample**
- `relevant` [principle] Performing a forward lunge with a smaller knee flexion angle of 80 degrees increases the knee extension moment compared to larger angles of 90 and 100 degrees.  
  _judge:_ States smaller 80-degree knee angle increases knee extension moment.
- `wrong_fault` [mistake] Allowing the front knee to collapse inward during the lunge.  
  _judge:_ Addresses knee valgus rather than shallow lunge depth.
- `wrong_fault` [principle] During the lunge, the forward knee should maintain a neutral alignment over the second metatarsal.  
  _judge:_ Addresses knee alignment in the frontal plane, a different fault.
- `relevant` [principle] Lower the trailing knee until it is approximately 2 to 3 cm short of contacting the ground.  
  _judge:_ Defines the correct depth of descent to prevent a shallow lunge.
- `irrelevant` [principle] Familiarizing oneself with the bottom position of the lunge can help mitigate instability during the movement.  
  _judge:_ Discusses mitigating instability rather than correcting shallow lunge depth.

## lunge / insufficient back knee flexion — 107 candidates · relevant 16 · wrong_fault 52 · irrelevant 39

**Random sample**
- `wrong_fault` [finding] A lunge with a shorter step length results in joint forces almost two times higher than a lunge with a longer step.  
  _judge:_ Focuses on step length rather than back knee flexion.
- `wrong_fault` [mistake] Allowing the knee to collapse into valgus (inward caving) during the single-leg lunge.  
  _judge:_ Addresses knee valgus collapse, which is a different fault.
- `irrelevant` [principle] The forward lunge results in higher patellofemoral joint loading compared to the backward lunge.  
  _judge:_ Compares patellofemoral joint loading across lunge variants.
- `irrelevant` [principle] Using a longer step length during a lunge helps minimize anterior tibial translation over the toes and reduces joint forces.  
  _judge:_ Discusses step length and anterior tibial translation, not back knee flexion.
- `irrelevant` [consequence] Incorrect lunge technique can promote poor posture.  
  _judge:_ Too general regarding incorrect technique promoting poor posture.

## bicep-curl / elbow flare — 73 candidates · relevant 5 · wrong_fault 31 · irrelevant 37

**Random sample**
- `irrelevant` [finding] In a simulation comparing dumbbell curls with 6 kg and 10.7 kg, the rate of increase of elbow peak moment was 57.7% and the rate of increase of peak muscle force was 38.3%.  
  _judge:_ Simulation study data on loading and peak moment.
- `irrelevant` [principle] Utilize a supinated forearm position to maximize the power of the biceps brachii as an elbow flexor.  
  _judge:_ Advice on forearm supination, not elbow stability or flaring.
- `relevant` [consequence] Because the biceps brachii is a biarticular muscle responsible for both elbow flexion and shoulder stabilization, it can cause the elbows to pull forward during curls.  
  _judge:_ Explains anatomical mechanism causing elbows to pull forward during curls.
- `wrong_fault` [finding] In the preacher curl, the peak of torque and greatest external moment arm occur at approximately 45 degrees to 50 degrees of elbow flexion.  
  _judge:_ Describes biomechanics of a different exercise variant (preacher curl).
- `wrong_fault` [principle] Use an elbow stabilizing plate or maintain strict elbow positioning to ensure that the full range of motion of the elbow joint is achieved and to prevent swinging the elbows.  
  _judge:_ Focuses on preventing elbow swinging momentum and achieving full range of motion.

## bicep-curl / partial range of motion — 104 candidates · relevant 58 · wrong_fault 16 · irrelevant 30

**Disagreements with golden set**
- `relevant` [principle] Use an elbow stabilizing plate or maintain strict elbow positioning to ensure that the full range of motion of the elbow joint is achieved and to prevent swinging the elbows.  
  _judge:_ Prescribes form to ensure full range of motion of the elbow joint.
- `relevant` [mistake] Performing preacher curls with an intermediate range of motion that omits the initial portion of the movement from 0 degrees to 49 degrees of elbow flexion.  
  _judge:_ Describes partial range of motion omitting full elbow extension at the bottom.
- `relevant` [principle] Dumbbell supinating curls and Bayesian curls can be performed using either the initial range of motion (approximately 50% of full ROM) or a full range of motion to achieve similar hypertrophy in the elbow flexors.  
  _judge:_ Discusses partial versus full range of motion in elbow flexor curls.
- `relevant` [mistake] Performing preacher curls only in the final range of motion (shortened position) limits muscle growth compared to training in the initial range of motion (lengthened position).  
  _judge:_ Explains the hypertrophy consequence of curling only through a partial range of motion.
- `relevant` [principle] Utilizing a partial range of motion at long muscle lengths can be sufficient to promote optimal muscle growth for the biceps brachii.  
  _judge:_ Discusses hypertrophy outcomes of utilizing partial range of motion for the biceps.
- `relevant` [consequence] Training the biceps preacher curl only in the final range of motion (shortened position) results in lower hypertrophy responses at the distal site of the biceps brachii and elbow flexors.  
  _judge:_ Explains the negative hypertrophy consequence of training curls only in partial shortened ROM.
- `relevant` [finding] In a study by Pedrosa et al. on seated preacher curls, training the initial ROM (0º–68º) induced greater increases in biceps brachii cross-sectional area at the distal site (24.0%) compared to the final ROM of 68º–135º (13.1%), while proximal site gains were similar (20.0% vs 21.1%).  
  _judge:_ Quantifies hypertrophy consequence of partial final ROM versus initial ROM in curls.

**Random sample**
- `relevant` [principle] Start the bicep curl with the elbow in full extension and the forearm supinated.  
  _judge:_ Specifies starting in full extension to avoid partial range of motion.
- `irrelevant` [finding] An 8-week study by Wolf et al. on trained men performing dumbbell supinating curls and Bayesian curls found that initial ROM (~50% of full ROM) and full ROM resulted in similar elbow flexor hypertrophy (~5% growth for both at 55% of humeral length, and ~4% for initial ROM vs ~3% for full ROM at 45% of humeral length).  
  _judge:_ Study protocol, sample details, and findings comparing initial versus full ROM.
- `relevant` [principle] Range of motion configurations should be used as a strategy to train muscles at longer lengths under relevant external torque to optimize muscular hypertrophy.  
  _judge:_ Discusses range of motion configuration to optimize muscle hypertrophy.
- `irrelevant` [finding] A 10-week study by Pinto et al. on untrained men performing barbell preacher curls showed similar elbow flexor muscle thickness increases between full ROM (0º–130º) at 7.2% and intermediate ROM (50º–100º) at 7.8%.  
  _judge:_ Study protocol, sample details, and results comparing full versus intermediate ROM.
- `irrelevant` [finding] Bicep curls should be programmed for hypertrophy using a moderate weight that allows for 8-12 reps.  
  _judge:_ General programming advice about repetition ranges and weight selection.


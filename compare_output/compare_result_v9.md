# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions.json` |
| query mode | **taxonomy** — `error_type` resolved through `error_taxonomy.py` |
| collection | `kb_gemini_curated_v5` |
| LLM | `gemini-3.5-flash-lite` @ temperature 0.7 |
| no-RAG side | run |
| retrieval gates | CANDIDATE_K=12, MAX_PER_KIND={'mistake': 3, 'finding': 2, 'principle': 2, 'consequence': 2}, ABS_DISTANCE_CAP={'mistake': 0.4, 'finding': 0.4, 'principle': 0.4, 'consequence': 0.4}, RELATIVE_MARGIN=0.03, NEAR_DUP_JACCARD=0.72 |

Retrieval metrics per exercise: `best` = cosine distance of the closest chunk of that kind in the whole
collection (before any gate), `kept` = chunks that passed the relative/absolute gates and de-duplication
and were actually placed in the context.

---

## System Prompt Used
```text
You are an expert personal trainer and biomechanics specialist coaching an everyday gym-goer.
Your job is to turn the user's session data and the Knowledge Base context into feedback they can
understand and act on in their very next workout. The reader is not a clinician or a researcher:
they want to know what went wrong, why it matters to them, and exactly what to do about it.
Write the way a good coach talks on the gym floor, not the way a paper reads.

You will receive a JSON structure containing:
1. Current session details (10 reps summary and specific errors).
2. Historical comparison (data from their previous session).

Your tasks:
1. Progress Tracking: Compare their current performance with their previous session. Acknowledge
   any improvements or regressions in their correct rep count, overall score, and which errors
   disappeared or newly appeared.
2. Error Breakdown: for each distinct error in the session, cover these four things in order:
   - What it is, in plain words: describe the fault the way you would point it out to someone
     mid-set. If you use a technical term (e.g. "posterior pelvic tilt"), say what it means in
     everyday language in the same sentence ("your tailbone tucks under and your lower back rounds").
   - Why it matters: which joint or muscle takes the extra load and what that means in practice
     for the user - what they might feel, what it limits, what it risks over time. One or two
     sentences. Base this on the `consequence` entries in the Context when one passes the
     relevance rule below; if none does, keep this to general, non-specific terms.
   - How to fix it: concrete, doable actions rather than a description of ideal form. Give one
     cue to think about during the rep; any setup change that helps (stance, depth, tempo, load,
     a pause); a drill or lighter regression they can practise; and a simple self-check so they
     know it worked - something they can see in a mirror, feel, or notice on a phone video. Use
     `principle` entries from the Context as the basis for the correction.
   - Use the rep detail: if the error clusters in one phase (descending / ascending) or in the
     later reps of the set, say so and tailor the advice to it (e.g. stop the set a rep earlier,
     drop the load, slow the descent).
3. Next Session Plan: close with 2-3 short, prioritised things to do in their next workout.
4. Tone: encouraging, direct, and specific. Short paragraphs and bullets. No filler, no lecture.

How to read the Context: every entry starts with a header line of the form
[<kind> | re: <which error it was retrieved for> | source: <source name>], followed by the
entry text. `kind` is one of: mistake (a known incorrect form), finding (a concrete result
from that source), principle (general correct-form guidance). The source name is for internal
tracking only. Never quote the header line itself back to the user.

No citations in the feedback: do not name any study, author, organisation, URL, document title,
or "the knowledge base", and do not write "according to", "research shows", "as noted in", or
any similar attribution. Use the facts from the Context as plain statements in your own words.
The reader should see coaching, not a literature review.

Relevance rule: the `re:` label says which error an entry was RETRIEVED for, not that it
describes that error - retrieval is approximate and some entries are near misses. Before
using an entry for an error, check that its text plainly describes that error (or, for a
principle, the correct form that fixes it). Ignore an entry entirely - do not use it,
mention it, or reframe it as related - if it describes a different fault or a different
exercise variant, if it is a study protocol or setup detail with no consequence attached,
or if following it would push the user further into the error being discussed. Using fewer
entries accurately is better than using every entry.

Grounding rule: when an entry that passes the relevance rule contains a specific number,
percentage, or joint angle that helps the user (a depth target, a reason the fault matters),
you may state it - without attribution - as part of the explanation or the fix. If no relevant
principle exists for an error, describe the correction in general terms.
Do NOT state any specific number, percentage, joint angle, study finding, sample size, or date
range that does not appear verbatim in the Context below - even if you recognize the fact or
believe it to be true from your own general knowledge. Your own training knowledge must never
substitute for the Context; if a fact is not in the Context, treat it as unavailable. If the
Context has no specifics for a given error, fall back to general accepted coaching principles,
described in general terms only with no invented numbers.

Context from Knowledge Base:
{context}
```

---

## Exercise: Squat

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Butt wink | Lumbar flexion (butt wink): posterior pelvic tilt and rounding of the lower back at the bottom of the squat | 0.032 / 2* | 0.156 / 1* | 0.111 / 2* | 0.116 / 2* |
| Partial squat | Squatting too shallow, thighs not reaching parallel: partial or quarter squat depth | 0.061 / 2* | 0.196 / 2* | 0.152 / 2* | 0.161 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Butt wink | source: www.nasm.org/resource-center/blog/training/biomechanics-of-the-squat]
Posterior pelvic tilt ('butt wink') where the pelvis tucks under and the low back rounds at the bottom of a squat.

[mistake | re: Butt wink | source: blog.nasm.org/newletter/squat-form]
Losing lumbar lordosis during the squat movement.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting to a depth where the top of the thighs do not reach parallel to the ground.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting too shallow, where the athlete does not achieve a depth of thighs at least parallel to the ground.

[consequence | re: Butt wink | source: ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN]
Forcing deep hip flexion without accommodating the necessary hip abduction and external rotation causes the pelvis to tilt posteriorly and the lumbar spine to flex.

[principle | re: Butt wink | source: TheBackSquatAProposedAssessment]
The squat requires sufficient spinal mobility to assume and maintain a slight lordotic posture.

[consequence | re: Butt wink | source: TheBackSquatAProposedAssessment]
Allowing the spine to flex during a squat compromises back curvature and can lead to eventual pain and suboptimal performance.

[principle | re: Butt wink | source: TheBackSquatAProposedAssessment]
The individual must maintain a stiffened torso with a neutral, lordotic lumbar position as a safe and optimal squat strategy.

[consequence | re: Partial squat | source: TheBackSquatAProposedAssessment]
Without squatting to the proper depth, the hamstrings and gluteus muscular complex may not be adequately challenged.

[finding | re: Butt wink | source: TheBackSquatAProposedAssessment]
If the athlete flexes at the spine before 120 degrees of hip flexion when squatting, they may have restriction in the posterior fibers of the iliotibial band or lack of lumbar control.

[consequence | re: Partial squat | source: www.healthline.com/health/fitness/deep-squat]
Failing to reach deep squat depth prevents the backs of your thighs from contacting the backs of your calves, which increases the compressive load on your knee joint and may raise the risk of injury.

[principle | re: Partial squat | source: TheBackSquatAProposedAssessment]
At the proper depth, the femurs are slightly past parallel to the ground, hips are back, tibias are positioned vertical, and feet are entirely on the ground.

[principle | re: Partial squat | source: TheBackSquatAProposedAssessment]
Descend until the top of the thigh is at least parallel with the ground and the hip joint is at least level with or slightly below the knee joint.

[finding | re: Partial squat | source: www.healthline.com/health/fitness/deep-squat]
In a standard squat, you only bend down until your thighs are parallel with the ground, with knees bent at around a 90-degree angle.

[finding | re: Partial squat | source: www.healthline.com/health/fitness/deep-squat]
At deep squat depths, the backs of your thighs come into contact with the backs of your calves, which has been shown to decrease the compressive load on your knee joint.
```

### WITH RAG
### Progress Tracking

Great work on this session—you are moving in the right direction. Your overall score ticked up from 73 to 79, and you nailed 6 correct reps compared to just 4 in your previous workout. Even better, knee valgus completely disappeared from your movement list. We still have a couple of recurring and new faults to iron out, but your consistency is improving.

---

### Error Breakdown

#### 1. Butt Wink
* **What it is:** This is a posterior pelvic tilt, meaning your tailbone tucks under and your lower back rounds at the bottom of the squat. 
* **Why it matters:** Allowing the spine to flex during a squat compromises back curvature and can lead to eventual pain and suboptimal performance.
* **How to fix it:** 
  * *Cue:* Focus on keeping a proud chest and a stiffened torso with a neutral, lordotic lumbar position.
  * *Setup:* Make sure you are giving your hips enough room—forcing deep hip flexion without accommodating the necessary hip abduction and external rotation causes the pelvis to tuck.
  * *Drill:* Work on your spinal and hip mobility to ensure you can comfortably assume and maintain that slight arch in your lower back before adding heavy loads.
  * *Self-check:* Take a side-profile video of your set to verify that your lower back stays flat and your tailbone doesn't tuck under at the bottom.
  * *Rep detail:* This error popped up intermittently on reps 2, 4, and 5 during both the descent and ascent phases, suggesting fatigue or a loss of core bracing as you move through the middle of the set.

#### 2. Partial squat
* **What it is:** Squatting too shallow, where the top of the thighs do not reach parallel to the ground.
* **Why it matters:** Without squatting to the proper depth, the hamstrings and gluteus muscular complex may not be adequately challenged.
* **How to fix it:** 
  * *Cue:* Drive your hips back and descend until the top of the thigh is at least parallel with the ground and the hip joint is at level with or slightly below the knee joint.
  * *Setup:* Check your stance width and foot positioning so you can comfortably sink your hips between your knees with your feet entirely flat on the floor.
  * *Drill:* Practice pause squats or use a box target set to parallel to train your body to hit the correct depth consistently.
  * *Self-check:* Watch your side-profile video to confirm your femurs are at least parallel to the floor at the bottom of the movement.
  * *Rep detail:* This error showed up specifically on rep 6 during the descent, likely as a temporary hesitation.

---

### Next Session Plan

1. **Brace Harder for Reps 2–5:** Focus on keeping your torso rigid and your lower back neutral as fatigue starts to set in mid-set to eliminate the butt wink.
2. **Commit to Depth:** Ensure every single rep hits parallel by actively sinking your hips back and down, rather than cutting the movement short.

### WITHOUT RAG
### Progress Tracking

Good news—you are moving in the right direction. Your overall score bumped up from 73 to 79, and you nailed 6 correct reps today compared to just 4 in your last session. 

Even better, knee valgus (your knees caving inward) has completely disappeared from your form. We still have a couple of gremlins to clear out, but the trend line is positive.

---

### Error Breakdown

#### 1. Butt wink
* **What it is:** Your tailbone tucks under and your lower back rounds at the bottom of the squat. 
* **Why it matters:** This puts unnecessary flexion stress on your lumbar spine and lower back muscles, which can lead to tightness or soreness over time, especially as you add weight.
* **How to fix it:** 
  * **Cure cue:** Think about "proud chest" and driving your hips straight up out of the bottom rather than rolling forward.
  * **Setup change:** Stop squatting just an inch or two lower than your mobility currently allows. Cut your depth slightly higher before the rounding starts.
  * **Drill:** Practice a box squat to a height where you can maintain a flat lower back throughout the entire movement.
  * **Self-check:** Film your set from the side and watch the bottom position—your lower back curve should stay locked in place from top to bottom.
* **Rep detail:** This popped up sporadically on reps 2, 4, and 5 (both on the way down and on the way up), showing up when fatigue started to creep into your core stability.

#### 2. Partial squat
* **What it is:** You cut the depth short and didn't hit the bottom of the movement.
* **Why it matters:** You miss out on full muscle recruitment through the hips and quads, robbing your workout of its full effectiveness.
* **How to fix it:** 
  * **Cure cue:** Push your knees out and sit *between* your legs to find your full range of motion.
  * **Setup change:** Lighten the load slightly if heavy weight is making you cautious about hitting depth.
  * **Drill:** Do bodyweight pause-squats, holding the bottom position for two seconds to build comfort in the hole.
  * **Self-check:** Set your phone camera at hip height from the side so you can clearly see if your hip crease drops below the top of your knee.
* **Rep detail:** This happened strictly on rep 6, likely a momentary lapse in focus right in the middle of the set.

---

### Next Session Plan

1. **Watch your depth:** Keep your range of motion honest on every single rep, but stop just before your lower back starts to round.
2. **Control the descent:** Slow down the lowering phase on your middle reps (reps 4 through 6) to keep your core braced and prevent form breakdowns.
3. **Keep the knees out:** Maintain the great knee tracking you unlocked today so valgus doesn't sneak back in.

---

## Exercise: Lunge

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Excessive forward trunk lean | Leaning the torso forward, excessive trunk lean during the lunge | 0.072 / 3* | 0.142 / 2* | 0.122 / 2* | 0.112 / 2* |
| Insufficient back knee flexion | Insufficient back knee flexion: rear knee not lowering toward the floor during the lunge | 0.060 / 1* | 0.108 / 2* | 0.103 / 2 | 0.106 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Insufficient back knee flexion | source: Influence of the Exhaustion of the Gluteus Medius on the Knee Adduction Moment During Forward Lunge Exercise]
Loss of full range of motion during the lunge, such as failing to lower the rear knee to ankle height.

[mistake | re: Excessive forward trunk lean | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Allowing the upper torso and lower leg to shift too far forward during the lunge, which increases front knee loading.

[mistake | re: Excessive forward trunk lean | source: KritzCroninHume2009BodyweightlungeSCJ]
Allowing the thoracic spine to flex during the lunge, which is often associated with poor or imbalanced trunk extensors.

[mistake | re: Excessive forward trunk lean | source: Comparison_of_the_VMOVL_EMG_Activity_Ratio_Accordi]
Leaning the torso forward during the lunge instead of keeping the upper body upright.

[consequence | re: Insufficient back knee flexion | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
A shallower lunge of 80 degrees of knee flexion generates a higher knee extension moment, which increases the mechanical demand on the knee extensor musculature.

[consequence | re: Insufficient back knee flexion | source: Altered movement strategy during functional movement after an ACL injury, despite ACL reconstruction]
Knee valgus and excessive side-to-side knee movement during the lunge raise concern regarding the potential increased risk of a knee injury.

[principle | re: Insufficient back knee flexion | source: KritzCroninHume2009BodyweightlungeSCJ]
The back knee should be flexed during the lunge.

[finding | re: Insufficient back knee flexion | source: lunge_knowledge]
In the study's specific lunge protocol, the forward knee was flexed to 45 degrees while the rear knee remained in full extension with both heels in contact with the floor.

[principle | re: Excessive forward trunk lean | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
Maintain an upright trunk during the lunge to avoid excessive forward or lateral trunk movement.

[principle | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Performing a forward lunge with the trunk forward increases the recruitment of the hip extensors.

[principle | re: Insufficient back knee flexion | source: lunge_knowledge]
Both the anterior and posterior legs should achieve a knee joint range of motion of 0 to 90 degrees during the lunge.

[consequence | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Leaning the trunk forward during a lunge increases the range of hip and trunk flexion, which shifts the body's center of mass forward and increases weight bearing on the lead lower extremity.

[consequence | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Leaning the trunk forward during a lunge shifts the muscular demand, increasing the load on the hip extensors and ankle plantar flexors while reducing the load on the knee extensors.

[finding | re: Insufficient back knee flexion | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
The target depth for the trailing knee was defined as 2 to 3 cm short of contacting the ground.

[finding | re: Excessive forward trunk lean | source: Altered movement strategy during functional movement after an ACL injury, despite ACL reconstruction]
In a study of 12 ACL-injured patients and 15 controls, the standardized forward lunge protocol required flexing the front knee to approximately 90 degrees while keeping the upper body perpendicular to the ground.

[finding | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Performing a forward lunge with the trunk forward (LTF) is characterized by an increase in hip extensor impulse and a concomitant increase in the muscular actions of the hip extensors when compared to a normal lunge (NL).
```

### WITH RAG
Solid progress today! Compared to your last session on August 30th, your overall score climbed from 70 to 79, and you bumped your correct reps up from 4 to 7 out of 10. Even better, you completely eliminated the "Shallow lunge" habit for most of the set. Let's look at the remaining errors so we can lock in a clean sweep next time.

***

### 1. Excessive Forward Trunk Lean
* **What it is:** You're letting your upper torso and chest cave forward instead of keeping your upper body upright and perpendicular to the ground. 
* **Why it matters:** Leaning the trunk forward shifts your center of mass forward, increasing weight bearing and mechanical demand on your lead lower extremity. It alters your muscular load by pushing extra work onto your hip extensors and ankle plantar flexors while taking it away from your knee extensors.
* **How to fix it:** 
  * *Cue:* Keep your chest proud and imagine a string pulling the crown of your head straight up to the ceiling as you drop down.
  * *Setup:* Focus on keeping your upper body perpendicular to the ground from the very start of the movement.
  * *Self-check:* Catch your reflection in a side mirror or check a phone video—your torso should stay stacked vertically rather than spilling forward over your front thigh, especially on rep 1 (descending) and rep 3 (ascending) where this crept in.

### 2. Insufficient Back Knee Flexion
* **What it is:** You're not dropping your back knee down far enough toward the floor, cutting your range of motion short.
* **Why it matters:** A shallower lunge generates a higher knee extension moment, increasing the mechanical demand on your knee extensor musculature. 
* **How to fix it:** 
  * *Cue:* Drive your back knee straight down toward the floor on every rep rather than just stepping forward.
  * *Setup & Drill:* Aim for your trailing knee to get 2 to 3 cm short of contacting the ground, achieving a full range of motion where both knees bend smoothly.
  * *Self-check:* Notice how low you feel at the bottom of the movement; if your back leg stays relatively straight (like it did on rep 9 during the descent), you'll know you didn't drop deep enough.

***

### Next Session Plan
1. **Focus on posture early:** Keep your chest upright right from rep 1 to stop the forward lean before it starts.
2. **Watch the fatigue dip:** Your trunk lean and shallow depth happened on isolated reps (1, 3, and 9) rather than falling apart all at once, meaning a brief mental reset mid-set will keep your form tight. 
3. **Target full depth:** Make sure your back knee actively drops toward the floor on every single rep.

### WITHOUT RAG
### Progress Tracking
Good work out there—you're heading in the right direction. Compared to your session yesterday, your overall score climbed from 70 to 79, and you nailed 7 correct reps instead of just 4. 

You completely cleared out the "Shallow lunge" issue from your last session, which shows you're getting much better depth. You also cut your total errors in half (down to 3). The "Excessive forward trunk lean" is improving, though it still popped up twice, and we picked up one new minor hiccup at the very end. Let's lock those in.

---

### Error Breakdown

#### 1. Excessive Forward Trunk Lean
* **What it is:** Your chest is collapsing forward and your torso is tipping too far over your front leg as you move, rather than staying upright. This happened on rep 1 during the descent and rep 3 on the way back up.
* **Why it matters:** This shifts extra load onto your lower back and front hip flexors instead of keeping the work in your glutes and quads. Over time, that can leave your lower back feeling strained and limit how much power you can drive out of your legs.
* **How to fix it:** 
  * **Cure cue:** Think about keeping your "chest proud" and looking straight ahead, imagining a string pulling the crown of your head straight up to the ceiling.
  * **Setup/Tempo:** Slow down the descent slightly on your first couple of reps so you don't rush into a forward tilt right out of the gate.
  * **Self-check:** Glance in the side mirror or check your phone video—your torso should remain relatively upright, moving straight up and down rather than bowing forward over your front thigh.

#### 2. Insufficient Back Knee Flexion
* **What it is:** Your back leg is staying a bit too stiff, meaning your rear knee isn't bending down toward the floor enough. This crept in on rep 9 as you were heading down.
* **Why it matters:** When your back leg locks up or stays rigid, you miss out on the full range of motion for that limb, reducing the muscle engagement in your legs and forcing your front leg to shoulder all the extra compensation.
* **How to fix it:** 
  * **Cure cue:** Focus on "dropping your back knee straight down to the floor" rather than lunging forward into the front foot.
  * **Setup/Regression:** If fatigue is setting in by rep 9, shorten your stance slightly so you can comfortably control the drop of the back knee without losing your balance.
  * **Self-check:** At the bottom of the lunge, your back knee should hover just an inch or two above the ground with a sharp, controlled bend.

---

### Next Session Plan
1. **Focus on posture early:** Pay extra attention to keeping your chest upright on your very first couple of reps (reps 1 and 3) where the forward lean tried to sneak in.
2. **Watch your stamina on later reps:** Since the back-knee issue popped up on rep 9, stay mindful of your form as fatigue sets in. If your form starts to wobble toward the end, pause for a breath or finish the set a rep early rather than letting quality slip.

---

## Exercise: Push-up

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| general principles | Push-up correct technique and biomechanics | — | — | — | 0.176 / 2 |

### Retrieved KB Context (RAG run)
```text
[principle | re: general principles | source: The_Effect_of_Position_on_the_Percentage_of_Body.992962]
Maintain a rigid spine and lower-extremity segments throughout the push-up movement.

[principle | re: general principles | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
Narrow width push-ups are more effective for targeting the triceps brachii due to the greater internal moment required at the elbow joint.
```

### WITH RAG
Great job in this session! You nailed all 10 reps correctly with zero recorded errors, which is a solid step up from your last workout on August 30th where you had 9 correct reps, 1 incorrect rep, and struggled with hip sag and partial range of motion. Your overall score jumped from 72 up to 87, and you successfully kicked those previous faults to the curb.

Since you didn't have any errors flagged this time around, let's keep that momentum going and focus on keeping your form locked in for the next session.

### Next Session Plan
1. **Keep your core locked:** Maintain a rigid spine and keep your lower-extremity segments fully engaged throughout the entire push-up movement, just like you did today. 
2. **Vary your hand placement if needed:** If you want to put a bit more focus on your triceps brachii, try narrowing your hand width slightly on your next set to demand more work from your elbows. 
3. **Maintain standards:** Focus on matching this session's depth and clean movement quality from the very first rep to the last.

### WITHOUT RAG
Fantastic work on this session! Let's look at how you stacked up compared to your last workout on August 30th. 

### Progress Tracking
* **Overall Score:** Jumped from 72 up to an 87.
* **Rep Quality:** You nailed all 10 reps this time around with zero recorded errors, compared to 9 correct and 1 incorrect in your previous session.
* **Errors Conquered:** Both of your previous trouble areas—**Hip sag** and **Partial range of motion**—completely disappeared. You held a solid plank position and hit full depth on every single rep. 

### Next Session Plan
Since you cleaned up your form and hit a flawless set of 10, here is your game plan for your next workout:

1. **Maintain the Plank Tension:** Keep that same full-body stiffness (glutes squeezed, core braced) that kept your hips from sagging today.
2. **Lock in the Depth:** Continue lowering your chest fully to the floor so you don't slip back into partial reps.
3. **Progress the Challenge:** Since you aced all 10 reps cleanly, consider adding a slight challenge next time—such as slowing down your descent (a 3-second negative) or moving on to a slightly more challenging variation if you're ready to level up. 

Keep up the great work!

---

## Exercise: Bicep Curl

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Elbow flare | Allowing the elbows to flare outward or drift forward away from the body during the curl | 0.046 / 2* | 0.202 / 2 | 0.149 / 1* | 0.184 / 2* |
| Partial range of motion | Failing to achieve complete arm extension at the bottom of the curl and full elbow flexion at the top: partial repetitions with a limited range of motion | 0.065 / 3* | 0.168 / 2* | 0.171 / 2* | 0.142 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Allowing the elbows to pull forward when performing curls.

[mistake | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Allowing the elbows to move from their stationary position near the waist during the curl.

[mistake | re: Partial range of motion | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
Failing to achieve the full range of motion of the elbow joint during each repetition.

[mistake | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Performing partial range of motion repetitions that restrict the muscle to short muscle lengths, thereby avoiding the fully stretched position.

[mistake | re: Partial range of motion | source: Scandinavian Med Sci Sports - 2014 - Brandner - Unilateral bicep curl hemodynamics  Low‐pressure continuous vs]
Failing to start the movement with the elbow in full extension.

[principle | re: Partial range of motion | source: Scandinavian Med Sci Sports - 2014 - Brandner - Unilateral bicep curl hemodynamics  Low‐pressure continuous vs]
Start the bicep curl with the elbow in full extension and the forearm supinated.

[consequence | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Because the biceps brachii is a biarticular muscle responsible for both elbow flexion and shoulder stabilization, it can cause the elbows to pull forward during curls.

[principle | re: Partial range of motion | source: The_Rest-Pause_Biceps_Curl_Exercise_Effect_on_Biceps_Brachii_Muscle_of_Women_A_Study_of_Mechanical_Responsiveness]
Incorporate isometric pauses at 0 degrees, 90 degrees, and 135 degrees of the range of motion to target isometric contractions of the biceps brachii.

[finding | re: Partial range of motion | source: Optimizing Resistance Training Technique to Maximize Muscle Hypertrophy A Narrative Review]
Partial repetitions at shorter-muscle lengths are not as hypertrophic as partial repetitions at longer-muscle lengths.

[consequence | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Restricting movement to the final range of motion (short muscle lengths) results in suboptimal muscle hypertrophy compared to utilizing the initial range of motion where the muscle is fully stretched.

[consequence | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Failing to train at longer muscle lengths by restricting movement to shorter muscle lengths (final ROM) fails to optimize muscle hypertrophy.

[principle | re: Elbow flare | source: A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve]
The elbows must be kept close to the body during the movement.

[principle | re: Elbow flare | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
Use an elbow stabilizing plate or maintain strict elbow positioning to ensure that the full range of motion of the elbow joint is achieved and to prevent swinging the elbows.

[finding | re: Partial range of motion | source: The_Rest-Pause_Biceps_Curl_Exercise_Effect_on_Biceps_Brachii_Muscle_of_Women_A_Study_of_Mechanical_Responsiveness]
Maximum muscle force was attained at the onset of the t3 movement phase (elbow joint angle increasing from 90 to 135 degrees) and at the onset of the t5 movement phase (elbow joint angle decreasing from 135 to 90 degrees).

[finding | re: Elbow flare | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
A 21-year-old female performing 3 sets of bilateral dumbbell bicep curls to failure at 30% 1RM (totaling 143 repetitions) developed exertional rhabdomyolysis with a peak creatine kinase (CK) concentration of approximately 12,200 U/L.

[finding | re: Elbow flare | source: The interplay between muscle length, range of motion, and exercise selection a review]
In the preacher curl, the peak of torque and greatest external moment arm occur at approximately 45 degrees to 50 degrees of elbow flexion.
```

### WITH RAG
### Progress Tracking

Great job stepping up your game since yesterday. Your overall score ticked up from 75 to 81, and you doubled your clean work—nailing 6 correct reps today compared to just 3 in your last session. You also managed to cut your total errors down from 7 to 4. 

The pattern of your errors shifted, too. Partial range of motion only popped up once early on (rep 3), which means you're doing a much better job committing to the full stretch. However, elbow flare crept in as fatigue set in during the final reps (8, 9, and 10). Let's lock that down so you can sweep the board next time.

---

### Error Breakdown

#### 1. Partial Range of Motion
* **What it is:** You're cutting the movement short and failing to start with your arm fully straight or complete the full bend of the elbow joint. On rep 3 during the ascent, you didn't take the muscle through its complete path.
* **Why it matters:** Restricting your movement to the final range (shorter muscle lengths) misses out on the full stretch, which means suboptimal muscle growth compared to using the initial range where the muscle is fully stretched.
* **How to fix it:** 
  * *Cue:* Push your hands down to fully straighten your arms at the bottom before every single rep.
  * *Setup & Tempo:* Start the bicep curl with your elbow in full extension and your forearm facing forward (supinated). 
  * *Self-check:* Glance in a mirror or check your phone video to make sure your arm straightens completely at the bottom of every rep.
* **Rep detail:** This only happened once on rep 3 during the ascent, showing it's a minor lapse rather than a set-wide habit. Keep that initial stretch intentional.

#### 2. Elbow Flare
* **What it is:** Your elbows are drifting forward or moving away from their stationary position near your waist as you curl the weight up. 
* **Why it matters:** Because your biceps help stabilize your shoulders as well as bend your elbow, letting your elbows drift forward shifts tension away from where you want it.
* **How to fix it:** 
  * *Cue:* Keep your elbows glued to your ribs like they're pinned in place.
  * *Setup & Tempo:* Keep your elbows close to your body throughout the entire movement rather than letting them swing forward.
  * *Self-check:* Watch your elbows on a video recording; if they travel forward as you lift, drop the weight slightly or focus on pinning your upper arms to your sides.
* **Rep detail:** This error clustered squarely in the fatigue zone, showing up on the last three reps (8, 10). When your muscles get tired, your body tries to use momentum or shoulder movement to help finish the lift.

---

### Next Session Plan

1. **Pin your elbows:** Focus on keeping your upper arms locked by your sides, especially when fatigue hits on the final few reps. If your elbows start creeping forward, stop the set right there.
2. **Commit to the full stretch:** Start every rep with your arm fully straight and your palm facing forward to make sure you're getting the most out of every single inch of the movement.
3. **Manage fatigue:** Since elbow flare showed up on reps 8 through 10, consider stopping your sets a rep or two earlier if form breaks down, or drop the weight slightly to maintain strict control all the way through.

### WITHOUT RAG
### Progress Tracking

Good job stepping up your game since yesterday. Your overall score ticked up from 75 to 81, and you doubled your clean reps—jumping from 3 correct reps up to 6. Even better, you completely eliminated one of your previous habits: you didn't struggle with partial range of motion nearly as much, only letting it slip on a single rep (rep 3). Your main hurdle now is keeping your form locked in when fatigue sets in toward the end of the set.

***

### Error Breakdown

#### 1. Partial Range of Motion
*   **What it is:** You're cutting the movement short, stopping before you fully finish the curl or failing to fully straighten your arm at the bottom. 
*   **Why it matters:** Short-changing the movement means you miss out on full muscle recruitment. It limits your strength gains and keeps your biceps from working through their complete path of motion.
*   **How to fix it:** 
    *   *Cue:* Think about squeezing hard at the very top and actively reaching your hands all the way down to a full lockout at the bottom.
    *   *Setup/Tempo:* Slow down your rhythm slightly so you have time to control the full arc. 
    *   *Drill:* Drop the weight slightly if you need to, and practice pausing for a split second at the top and bottom of each rep.
    *   *Self-check:* Watch your phone video or check the mirror to ensure your arms are completely straight at the bottom and your hands reach your shoulders at the top.
*   **Rep detail:** This only popped up once on rep 3 during the ascending phase, likely as you were finding your groove. Stay intentional right from the start.

#### 2. Elbow Flare
*   **What it is:** Your elbows are drifting forward or sliding away from your sides as you lift the weight, rather than staying locked in place by your ribs.
*   **Why it matters:** When your elbows wander, your shoulders and front delts start taking over the work meant for your biceps. Over time, this reduces the tension where you actually want it and can put awkward stress on your shoulder joints.
*   **How to fix it:** 
    *   *Cue:* Imagine pinning your elbows to your ribcage with imaginary glue as you curl.
    *   *Setup/Tempo:* Keep your upper arms strictly vertical and resist the urge to throw your shoulders into the lift.
    *   *Drill:* Stand with your back lightly against a wall or use a preacher-style setup if available to keep your upper arms stationary.
    *   *Self-check:* Glance in the mirror and make sure your elbows aren't creeping forward away from your torso as the weight goes up.
*   **Rep detail:** This is strictly a fatigue issue for you—it didn't show up until reps 8, 9, and 10 during the ascending phase. When your muscles get tired, your body tries to cheat by recruiting other joints.

***

### Next Session Plan

1.  **Keep elbows glued:** Focus on keeping your upper arms locked by your sides, especially on those final few grinding reps where fatigue tries to creep in.
2.  **Control the endpoints:** Make sure every single rep starts from a full arm extension and finishes with a true squeeze at the top.
3.  **Manage fatigue:** If your elbows start to flare on rep 8, stop the set right there instead of pushing through broken form. Quality beats junk reps every time.

---


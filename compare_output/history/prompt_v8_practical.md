# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions.json` |
| query mode | **taxonomy** — `error_type` resolved through `error_taxonomy.py` |
| collection | `kb_local_curated_v4` |
| LLM | `gemini-3.5-flash-lite` @ temperature 0.7 |
| no-RAG side | skipped |
| retrieval gates | CANDIDATE_K=12, MAX_PER_KIND={'mistake': 3, 'finding': 2, 'principle': 2}, ABS_DISTANCE_CAP={'mistake': 0.4, 'finding': 0.4, 'principle': 0.4}, RELATIVE_MARGIN=0.06, NEAR_DUP_JACCARD=0.72 |

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
     for the user - what they might feel, what it limits, what it risks over time. One or two sentences.
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
| error_type | query sent | mistake best / kept | finding best / kept | principle best / kept |
|---|---|---|---|---|
| Butt wink | Lumbar flexion (butt wink): posterior pelvic tilt and rounding of the lower back at the bottom of the squat | 0.120 / 2 | 0.327 / 2 | 0.296 / 2 |
| Partial squat | Squatting too shallow, thighs not reaching parallel: partial or quarter squat depth | 0.258 / 1 | 0.370 / 1 | 0.331 / 2 |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Butt wink | source: ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN]
Lumbar flexion (butt wink) at the bottom of the squat.

[mistake | re: Butt wink | source: www.nasm.org/resource-center/blog/training/biomechanics-of-the-squat]
Posterior pelvic tilt ('Butt Wink') where the pelvis tucks under and the low back rounds at the bottom of the squat.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting too shallow, failing to bring the thighs at least parallel to the ground.

[principle | re: Butt wink | source: TheBackSquatAProposedAssessment]
Maintain a neutral pelvic tilt during the squat to increase erector spinae and oblique muscle activity, providing optimal spinal support.

[principle | re: Butt wink | source: TheBackSquatAProposedAssessment]
Maintain a neutral, slightly lordotic spine posture throughout the squat to avoid excessive pressure on the lower back.

[finding | re: Butt wink | source: TheBackSquatAProposedAssessment]
Flexing at the spine before 120 degrees of hip flexion when squatting may indicate restriction in the posterior fibers of the iliotibial band or lack of lumbar control.

[principle | re: Partial squat | source: TheBackSquatAProposedAssessment]
Achieve full depth with the tops of the thighs at least parallel to the ground.

[finding | re: Butt wink | source: Muscle Activation Patterns During Different Squat Techniques]
Control squats were performed to 90 degrees of flexion.

[principle | re: Partial squat | source: Muscle Activation Patterns During Different Squat Techniques]
Perform squats to 90 degrees of flexion for standard depth.

[finding | re: Partial squat | source: www.healthline.com/health/fitness/deep-squat]
Compressive forces in the knee may be higher in a partial squat than in a deep squat.
```

### WITH RAG
### Progress Tracking

Great job putting in the work today. You’ve moved your overall score up from 73 to 79, and your correct rep count jumped from 4 out of 10 up to 6 out of 10. Even better, you completely wiped out knee valgus (your knees caving inward), which was showing up in your last session. 

We still have a couple of recurring and new bugs to squash—specifically, a bit of lower back rounding at the bottom and cutting depth short on a rep—but the trend is heading in the right direction. Let's look at what happened and how to clean it up.

---

### Error Breakdown

#### 1. Butt wink
* **What it is:** This is a posterior pelvic tilt, where your tailbone tucks under and your lower back rounds at the bottom of the squat. 
* **Why it matters:** Flexing at the spine creates excessive pressure on your lower back and deprives you of optimal spinal support from your erector spinae and oblique muscles. 
* **How to fix it:** 
  * *Cue:* Think about keeping a neutral, slightly lordotic spine posture (a proud chest with a slight natural arch in your lower back) throughout the entire movement. 
  * *Setup & Tempo:* Watch your depth—flexing at the spine before 120 degrees of hip flexion can happen if you push past your current mobility limits or lack lumbar control. 
  * *Self-check:* Take a side-profile video of your set and check if your lower back stays flat or if your tailbone scoops forward at the very bottom.

#### 2. Partial squat
* **What it is:** Squatting too shallow, failing to bring your thighs at least parallel to the ground.
* **Why it matters:** Compressive forces in the knee may actually be higher in a partial squat than in a deep squat, while also cheating you out of full muscle engagement. 
* **How to fix it:** 
  * *Cue:* Commit to achieving full depth with the tops of your thighs at least parallel to the ground. 
  * *Setup & Tempo:* Standard depth requires performing squats to 90 degrees of flexion. Slow down your descent slightly so you can control the movement into that bottom position.
  * *Self-check:* Look in the side mirror or watch your phone footage to confirm your hip crease drops below or right in line with the top of your knee cap before you stand back up. (This error only popped up once on rep 6, likely as you fatigued, so staying mindful of depth will clear it right up.)

---

### Next Session Plan

1. **Focus on spinal control:** Prioritize keeping your lower back slightly arched and neutral at the bottom of every rep to protect your spine.
2. **Commit to full depth:** Don't shortchange your range of motion; make sure your thighs hit parallel on every single rep, especially as you get deeper into the set.
3. **Maintain knee tracking:** Keep up the great work from today by keeping your knees tracking properly over your toes with zero inward caving.

---

## Exercise: Lunge

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | principle best / kept |
|---|---|---|---|---|
| Excessive forward trunk lean | Leaning the torso forward, excessive trunk lean during the lunge | 0.256 / 1 | 0.338 / 1 | 0.307 / 2 |
| Insufficient back knee flexion | Insufficient back knee flexion: rear knee not lowering toward the floor during the lunge | 0.256 / 1 | 0.305 / 2 | 0.275 / 2 |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Excessive forward trunk lean | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
Excessive trunk movement or marked trunk lean.

[mistake | re: Insufficient back knee flexion | source: lunge_knowledge]
Allowing the rear knee to flex during the stride-stance lunge.

[principle | re: Insufficient back knee flexion | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
Do not allow the rear knee to contact the floor during the lunge.

[finding | re: Insufficient back knee flexion | source: ptq-4.4.9-the-undervalued-lunge]
Rotating the back knee or foot outward during a forward lunge increases torque stress in the knee joint.

[principle | re: Excessive forward trunk lean | source: mxn167Sp24]
Performing a forward lunge with a forward trunk lean increases biceps femoris activity compared to an upright trunk.

[principle | re: Insufficient back knee flexion | source: mxn167Sp24]
Backward lunges can reduce anterior shearing forces and patellofemoral joint loading on the knee compared to forward lunges.

[finding | re: Insufficient back knee flexion | source: mxn167Sp24]
Kinematic data showed a significantly greater knee angle in the forward lunge compared to the backward lunge.

[finding | re: Excessive forward trunk lean | source: blog.nasm.org/training-benefits/lunge-effective-lower-body-training-exercise]
An upright trunk tends to create what is often called a 90/90 lunge where both knees at the bottom of the move are 90° angles.

[principle | re: Excessive forward trunk lean | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
Maintain an upright trunk throughout the movement.
```

### WITH RAG
### Progress Tracking

Good improvements across the board since yesterday. You bumped your overall score up from 70 to 79 and nailed 7 clean reps instead of just 4. Even better, you completely eliminated the "Shallow lunge" issue that tripped you up last time. You're moving better, but we still have a couple of specific form leaks to clean up.

---

### Error Breakdown

#### 1. Excessive Forward Trunk Lean
- **What it is:** Your torso is tipping forward from the hips as you move, instead of staying tall and stacked over your hips. This happened on the way down on rep 1 and on the way back up on rep 3.
- **Why it matters:** Leaning your chest forward places extra load onto your hamstrings (the biceps femoris muscles) rather than distributing the work evenly through your legs. 
- **How to fix it:** 
  - **Cue:** Think about keeping your chest proud and "shining your shirt logo" straight ahead against the wall in front of you.
  - **Setup / Tempo:** Aim for a classic 90/90 position at the bottom, where both of your knees form 90-degree angles and your torso remains upright.
  - **Drill:** Practice a few bodyweight reps standing in front of a mirror, focusing entirely on keeping your shoulders stacked directly above your hips.
  - **Self-Check:** Catch yourself on a phone video—if your shoulders drift past your front knee on the descent, you're leaning too far forward.

#### 2. Insufficient Back Knee Flexion
- **What it is:** You aren't bending your back leg enough as you step into the lunge. This popped up on the way down during rep 9 as fatigue started to creep in.
- **Why it matters:** Shortchanging the back knee bend means you aren't dropping deep enough into your lower body, which robs the exercise of its full muscle-building benefits.
- **How to fix it:**
  - **Cue:** Drop straight down toward the floor with your back knee rather than lunging forward.
  - **Setup / Tempo:** Make sure your rear knee dips down nicely toward the ground without actually touching the floor. 
  - **Drill:** If forward lunges continue to give you trouble late in the set, try switching to backward lunges; stepping backward naturally helps keep your trunk upright and takes unnecessary stress off the front of the knee.
  - **Self-Check:** Feel for an even distribution of weight across both legs at the bottom of the movement, with your back knee hovering just an inch or two above the floor.

---

### Next Session Plan

1. **Keep your chest tall:** Focus on that upright torso from the very first rep so trunk lean doesn't sneak in early like it did on rep 1.
2. **Watch the finish:** Pay extra attention to your back knee bend on your later reps (like rep 9) when fatigue tries to shorten your range of motion.

---

## Exercise: Push-up

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | principle best / kept |
|---|---|---|---|---|
| general principles | Push-up correct technique and biomechanics | — | — | 0.250 / 2 |

### Retrieved KB Context (RAG run)
```text
[principle | re: general principles | source: blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement]
Regress the push-up by placing hands on a bench or knees on the floor to maintain movement integrity and posture.

[principle | re: general principles | source: www.nasm.org/resource-center/blog/training/proper-push-up-form-and-technique-a-complete-guide]
Utilize the push-up as a movement assessment to evaluate upper-body strength, core stability, and the ability to maintain alignment under load.
```

### WITH RAG
### Progress Tracking

Great job on this session. You pulled off a clean sweep: all 10 reps were marked correct, bumping your overall score up from 72 to 87 compared to your last workout on August 30th. Most importantly, those previous issues—hip sag and cutting your range of motion short—completely disappeared this time around. You maintained solid posture from start to finish.

### Error Breakdown

Since you didn't flag any errors this session, there are no specific faults to break down. You successfully treated this set as a true test of your core stability and upper-body strength, keeping your alignment locked in under load rather than letting your form break down. 

### Next Session Plan

Keep the momentum rolling into your next workout with these two priorities:

1. **Maintain the standard:** Treat your next push-up session as a movement assessment, focusing entirely on holding that same rigid core stability and full range of motion.
2. **Control the regression if needed:** If fatigue starts creeping in toward the end of your sets and your hips or posture begin to slip, regress the movement by placing your hands on a bench or your knees on the floor. This lets you keep your movement integrity and posture intact instead of forcing sloppy reps.

---

## Exercise: Bicep Curl

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | principle best / kept |
|---|---|---|---|---|
| Elbow flare | Allowing the elbows to flare outward or drift forward away from the body during the curl | 0.057 / 2 | 0.442 / 0 | 0.161 / 1 |
| Partial range of motion | Failing to achieve complete arm extension at the bottom of the curl and full elbow flexion at the top: partial repetitions with a limited range of motion | 0.269 / 3 | 0.407 / 0 | 0.288 / 2 |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Elbow flare | source: grokipedia.com/page/Bicep_curl]
Allowing the elbows to flare outward during the curl.

[mistake | re: Elbow flare | source: A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve]
Allowing the elbows to drift away from the body during the curl.

[principle | re: Elbow flare | source: grokipedia.com/page/Bicep_curl]
Keep elbows tucked at the sides during the curl.

[mistake | re: Partial range of motion | source: Scandinavian Med Sci Sports - 2014 - Brandner - Unilateral bicep curl hemodynamics  Low‐pressure continuous vs]
Failing to start the repetition with the elbow in full extension.

[mistake | re: Partial range of motion | source: grokipedia.com/page/Bicep_curl]
Failing to achieve complete arm extension at the bottom of the movement.

[principle | re: Partial range of motion | source: grokipedia.com/page/Bicep_curl]
Perform a full range of motion from complete arm extension at the bottom to near-maximal elbow flexion at the top.

[principle | re: Partial range of motion | source: grokipedia.com/page/Bicep_curl]
Utilize a full range of motion from full elbow extension to complete flexion.

[mistake | re: Partial range of motion | source: A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve]
Failing to start the movement from full elbow extension.
```

### WITH RAG
### Progress Tracking

Great work on this session—you're heading in the right direction! Your overall score bumped up from 75 to 81, and you doubled your clean reps, nailing 6 correct reps compared to just 3 in your previous workout. You also managed to cut your total errors down from 7 to 4. 

The breakdown shows a clear pattern: your early reps look sharp, but as fatigue sets in on the later reps (specifically reps 8 through 10), your form starts to break down. Let's look at the two specific faults that popped up so we can lock them down for your next session.

---

### Error Breakdown

#### 1. Partial Range of Motion
* **What it is:** You're cutting the movement short instead of starting the repetition with your elbow in full extension, failing to achieve complete arm extension at the bottom of the movement.
* **Why it matters:** Stopping short cheats your muscles out of the fully lengthened position, which limits the overall muscle-building stimulus for your biceps.
* **How to fix it:** 
  * *Cue:* Focus on consciously straightening your arm all the way at the bottom before starting the next curl.
  * *Setup & Tempo:* Take a deliberate pause at the bottom of every single rep to ensure your arm is completely straight.
  * *Self-Check:* Watch your phone video and check that your arm forms a straight line from shoulder to wrist at the bottom of each rep.
* **Rep Detail:** This only happened once (on rep 3), which suggests it was just a momentary lapse rather than a severe fatigue issue. Stay mindful of it right from the first rep.

#### 2. Elbow Flare
* **What it is:** Allowing your elbows to drift away from your body and flare outward during the curl.
* **Why it matters:** When your elbows drift forward or flare out, other muscles have to take over the work, reducing the direct load on your biceps.
* **How to fix it:** 
  * *Cue:* Keep your elbows pinned to your sides like they are glued to your ribs.
  * *Setup & Tempo:* Lighten the load slightly if needed so you don't need body English or elbow movement to get the weight up.
  * *Self-Check:* Notice how your upper arms feel against your torso—if you feel your elbows sliding forward or out to the sides, you are losing your anchor point.
* **Rep Detail:** This error clustered heavily at the end of your set, hitting on reps 8, 9, and 10 as fatigue kicked in. When you feel your form slipping, it's time to call the set.

---

### Next Session Plan

1. **Keep elbows pinned:** Focus entirely on keeping your elbows locked at your sides during the lift, especially as the set gets harder.
2. **Lock out the bottom:** Pause briefly at full arm extension on every single rep to guarantee a full range of motion.
3. **Stop the set earlier:** Since your elbow flare happens on the final three reps due to fatigue, cut your set 1 to 2 reps short of failure to keep your form pristine.

---


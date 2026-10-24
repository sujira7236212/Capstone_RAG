# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions.json` |
| query mode | **taxonomy** — `error_type` resolved through `error_taxonomy.py` |
| collection | `kb_local_curated_v4` |
| LLM | `gemini-3.5-flash-lite` @ temperature 0.7 |
| no-RAG side | run |
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
Good work getting back under the bar. Let’s look at how this session stacked up against your last one, and exactly what we need to clean up for the next workout.

### Progress Tracking
You're moving in the right direction. Your overall score ticked up from 73 to 79, and you nailed 6 correct reps today compared to just 4 in your previous session. Even better, knee valgus (your knees caving in) completely disappeared from your list of errors. We still have a couple of recurring and new faults to iron out, but the foundation is improving.

---

### Error Breakdown

#### 1. Butt Wink
* **What it is:** This is a posterior pelvic tilt where your tailbone tucks under and your lower back rounds at the bottom of the squat. 
* **Why it matters:** Rounding your lower back places excessive pressure on the spine and reduces the support you get from your erector spinae and oblique muscles. 
* **How to fix it:** 
  * *Cue:* Think about keeping a neutral, slightly lordotic spine posture throughout the entire squat, keeping your chest proud.
  * *Setup/Depth:* This error tended to pop up during the descent and ascent of reps 2, 4, and 5. Watch your depth—if you sink too low before your hips are ready, your lower back will round. 
  * *Self-check:* Take a video from the side and watch your lower back at the very bottom of the movement; your spine should maintain its natural slight arch without your tailbone tucking under.

#### 2. Partial squat
* **What it is:** Squatting too shallow, failing to bring your thighs at least parallel to the ground.
* **Why it matters:** Cutting your depth short robs you of the full movement pattern and can actually increase compressive forces in the knee compared to a full squat.
* **How to fix it:**
  * *Cue:* Commit to standard depth by aiming to bring the tops of your thighs at least parallel to the ground, matching the 90-degree flexion mark.
  * *Setup/Depth:* This cropped up on rep 6 as fatigue set in and you cut the descent short. Don't shortchange your range of motion just because the set is getting hard.
  * *Self-check:* Look at your phone video or use a side mirror to confirm your hip crease drops below or meets the top of your kneecap on every rep.

---

### Next Session Plan
1. **Focus on spine control:** Actively maintain a neutral, slightly arched lower back throughout your descent to eliminate the butt wink.
2. **Commit to depth:** Push past any temptation to cut reps short, ensuring your thighs hit parallel on every single rep.
3. **Pace your set:** Since errors like the butt wink crept in mid-set (reps 4 and 5) and partial depth hit later on rep 6, focus on pristine form over speed. If your form starts to break down, rack the bar a rep early rather than grinding out sloppy reps.

### WITHOUT RAG
Good work getting under the bar again. Let's look at how this session stacked up against your last one.

### Progress Tracking
You're moving in the right direction! Your overall score bumped up from 73 to 79, and you nailed 6 correct reps today compared to just 4 in your previous session. Even better, knee valgus (your knees caving in) completely disappeared from your report. We still saw some butt wink pop up a few times, plus a new one with depth on rep 6, but overall your movement quality is improving.

---

### Error Breakdown

#### 1. Butt Wink
- **What it is:** At the bottom of your squat, your tailbone tucks under and your lower back rounds instead of staying flat. This happened mid-set on reps 2, 4, and 5 during both the descent and the ascent.
- **Why it matters:** This rounding shifts extra load onto your lumbar spine and discs, which can leave your lower back feeling stiff or achy and limits how much stable power you can drive out of the bottom.
- **How to fix it:** 
  - *Cue:* Think about keeping your chest proud and spreading your floor apart with your feet as you drop down.
  - *Setup/Tempo:* Cut your depth slightly short of absolute rock-bottom if you notice your hips tucking under, and control the descent rather than dropping in too fast.
  - *Regression:* Practise goblet squats to a box set just above parallel to help you feel where your lower back starts to round.
  - *Self-check:* Watch a side-angle video of your set—your lower back curve should stay locked in from top to bottom.

#### 2. Partial Squat
- **What it is:** On rep 6, during the descent, you cut the movement short and didn't hit full depth.
- **Why it matters:** Halting your descent early robs your quadriceps and glutes of the full range of motion they need to grow stronger and more resilient.
- **How to fix it:** 
  - *Cue:* Pick a fixed target point straight ahead and commit to hitting your full depth before reversing direction.
  - *Setup/Tempo:* Pause for a split second at the bottom of each rep to establish control before driving back up.
  - *Drill:* Use a target like a med ball or box to lightly touch on every rep so you know you're hitting the exact same depth every time.
  - *Self-check:* On your phone video, your hip crease should clearly drop below the top of your knee cap.

---

### Next Session Plan
1. **Control your depth and range:** Focus on hitting your full depth consistently while keeping your lower back locked in, using rep 6 as a reminder not to shortchange your movement.
2. **Watch the bottom position:** If you feel your tailbone tucking under on reps 2 through 5, stop your descent a fraction of an inch higher where your spine stays neutral.

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

Good job getting to work. Compared to your last session on August 30th, you’ve made some solid progress:
- Your overall score ticked up from 70 to 79.
- You nailed 7 correct reps today, up from just 4 in the previous session. 
- You completely dropped "Shallow lunge" from your errors list, which means you're getting a much better range of motion. 
- The old issue of excessive forward trunk lean dropped from a set-wide habit down to just a couple of isolated reps (reps 1 and 3), and one new minor issue cropped up on rep 9 (insufficient back knee flexion). 

Let's clean up those few remaining leaks so you can lock in a fully dialed-in set next time.

---

### Error Breakdown

#### 1. Excessive Forward Trunk Lean
- **What it is:** Instead of keeping your torso tall and stacked over your hips as you drop down, your chest caves forward toward your front knee. 
- **Why it matters:** Leaning your trunk too far forward shifts extra load onto your hamstrings (specifically the biceps femoris) rather than keeping the work balanced across your legs. Over time, it makes it harder to keep your balance and robs the target leg muscles of optimal work.
- **How to fix it:** 
  - *Cues & Setup:* Keep an upright trunk throughout the movement. Aim for a position where both knees form 90-degree angles at the bottom of the move, with your torso tall.
  - *Action:* On reps 1 and 3, this happened during the descent and ascent phases as fatigue or momentum tried to pull you forward. Focus on lifting your chest proudly before you even step out.
  - *Self-check:* Glance in a mirror or check your phone video to ensure your shoulders stay stacked directly over your hips rather than drifting past your front knee.

#### 2. Insufficient Back Knee Flexion
- **What it is:** On rep 9, your back leg stayed a bit too stiff, meaning your rear knee didn't bend enough as you dropped into the lunge.
- **Why it matters:** Failing to bend your back knee properly alters your mechanics and throws off the balance of the exercise.
- **How to fix it:** 
  - *Cues & Setup:* Drop your back knee straight down toward the floor on every rep. Just make sure it doesn't actually crash into the ground. 
  - *Action:* This popped up on the descending phase of rep 9, likely as you started getting tired toward the end of the set. Treat every rep like it's the first one—don't cut the back leg's job short.
  - *Self-check:* Feel for an equal distribution of weight between your front and back legs at the bottom of the movement, and check that your back knee is hovering just above the floor.

---

### Next Session Plan

1. **Prioritise torso height:** Start every rep with a tall chest, keeping your trunk upright to avoid leaning forward (especially as you start feeling fatigued on reps 1 and 3).
2. **Mind the back leg:** Ensure your back knee bends properly on every descent so you maintain that balanced 90/90 position at the bottom.
3. **Pace the set:** Take a brief, deliberate breath between reps to reset your posture, ensuring mistakes like the one on rep 9 don't sneak in as you tire out.

### WITHOUT RAG
### Progress Tracking

Great job on this session—you’re definitely moving in the right direction! Your overall score ticked up from 70 to 79, and you nailed 7 correct reps compared to just 4 in your previous workout. 

Even better, you completely eliminated the "Shallow lunge" error that plagued your last session. While a couple of new faults popped up, your control improved significantly for the bulk of the set. Let's look at the two errors from today and clean them up for your next go.

---

### Error Breakdown

#### 1. Excessive Forward Trunk Lean
* **What it is:** Instead of keeping your torso upright, your chest collapses forward and caves toward the floor as you move. This happened on rep 1 during the descent and rep 3 during the ascent.
* **Why it matters:** This shifts the work away from your glutes and quads, dumping extra load onto your lower back. Over time, that can leave your lower back feeling fried and limit how much power you can drive out of your legs.
* **How to fix it:** 
  * **Cue:** Think about "chest proud" or "zipping up your jacket" as you lower yourself. 
  * **Setup/Tempo:** Slow down the descent slightly so you aren't rushing into the bottom of the movement.
  * **Drill:** Practice bodyweight split squats with your hands placed across your chest or behind your head to force your upper back to stay tall.
  * **Self-check:** Glance in a mirror sideways—your torso should stay roughly parallel to your shin angle, rather than tipping forward toward your front knee.

#### 2. Insufficient Back Knee Flexion
* **What it is:** Your back leg stays a bit too stiff, meaning your rear knee isn't bending deeply enough toward the floor. This showed up late in the set on rep 9 during the descent.
* **Why it matters:** When your back leg locks up, you miss out on the full range of motion needed to properly load your front leg's glutes and quads. It turns a deep, effective lunge into a shallow, less impactful step.
* **How to fix it:** 
  * **Cue:** Focus on "dropping straight down" toward the floor with your back knee rather than lunging forward.
  * **Setup/Tempo:** Take a slightly shorter stride if you feel stretched out, and pause for a split second at the bottom to ensure the back knee actually kisses or hovers just above the floor.
  * **Drill:** Drop the weight and practice stationary reverse lunges, focusing entirely on a vertical drop of the back knee.
  * **Self-check:** On a phone video, you should see your back shin approaching a vertical line and your back knee pointing straight down toward the ground at the bottom.

---

### Next Session Plan

1. **Keep the chest tall early:** Pay extra attention to your posture on the very first few reps (reps 1–3) to prevent your torso from collapsing forward.
2. **Control the back leg:** Focus on dropping straight down rather than reaching forward, ensuring your back knee bends fully on every single rep.
3. **Pace yourself:** Since fatigue caused that slip-up on rep 9, don't rush the end of your set—take an extra breath between reps if your form starts to blur.

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

Great job on this session. You pulled off a clean sweep with **10 out of 10 correct reps** and bumped your overall score up to **87** (compared to 72 last time). Most importantly, both of your previous issues—hip sag and partial range of motion—completely disappeared. You proved you can maintain strict alignment and core stability under load from the first rep to the last.

Since you had zero recorded errors this time around, we don't need to fix any specific faults. Instead, let's look at how to lock in these gains and keep challenging your upper body safely.

---

### Next Session Plan

1. **Keep the standard high:** Treat your next push-up session as a movement assessment to check your core stability. Focus on holding that rigid plank position from head to toe on every single rep.
2. **Progress with control:** If 10 unbroken reps are feeling locked-in and solid, avoid rushing into sloppy fatigue. Keep your movement integrity sharp, and only scale up the difficulty or volume once you can repeat this clean performance effortlessly.
3. **Use regressions if fatigue hits:** If your form ever starts to slip late in a set, don't force ugly reps. Regress the push-up by placing your hands on a sturdy bench or dropping your knees to the floor to maintain proper posture all the way through.

### WITHOUT RAG
### Progress Tracking

Great work on this session! You made a fantastic jump from your last workout on August 30th. 

* **Overall Score:** Up from 72 to an 87.
* **Correct Reps:** You nailed all 10 reps this time, compared to 9 correct reps and 1 mistake last session.
* **Errors:** Both of your previous issues—hip sag and partial range of motion—completely disappeared. Every single rep was completed successfully. 

### Error Breakdown

You didn't log any errors during this session, meaning your form stayed solid from the first rep to the last. Keep that core braced and keep hitting full depth!

### Next Session Plan

1. **Lock in Your Setup:** Start your next session with the exact same tight core and glute squeeze you used today to maintain a straight line from head to heels.
2. **Maintain Full Range of Motion:** Keep bringing your chest down smoothly on every rep without cutting the bottom short.
3. **Progress the Challenge:** Since you cleared all 10 reps cleanly, focus on maintaining this pristine form for your next progression—whether that means adding a few more reps or slowing down the tempo for an extra challenge.

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

Solid improvements today. Your overall score ticked up from 75 to 81, and you doubled your correct reps, jumping from 3 clean reps in your last session up to 6 today. Both of your old habits—partial range of motion and elbow flare—showed up again, but you cut your total errors down from 7 to 4. 

The breakdown tells an encouraging story: your range-of-motion issues are happening early (just rep 3), while the elbow flare is sneaking in exclusively during the final few reps (reps 8 through 10) as fatigue sets in. 

---

### Error Breakdown

#### 1. Partial Range of Motion
* **What it is:** You're cutting the movement short, failing to start the repetition with the elbow in full extension or achieve complete arm extension at the bottom. 
* **Why it matters:** Stopping short cheats your muscles out of the full stretch and contraction loop, limiting the overall development of the bicep.
* **How to fix it:** 
  * *Cue:* Focus on actively straightening your arms all the way before you start curling.
  * *Setup/Drill:* Perform a full range of motion from complete arm extension at the bottom to near-maximal elbow flexion at the top.
  * *Self-check:* Watch your phone video or check the mirror to ensure your arms hang completely straight at the bottom of every single rep.
* **Rep Detail:** This only happened on rep 3 today, meaning you drifted into it briefly during the early middle of your set before locking your focus back in.

#### 2. Elbow Flare
* **What it is:** Allowing your elbows to drift away from your body or flare outward during the curl.
* **Why it matters:** When your elbows wander, your shoulders and front delts start taking over the work that your biceps are supposed to be doing.
* **How to fix it:** 
  * *Cue:* Keep your elbows pinned to your sides like they're glued in place.
  * *Setup/Drill:* Pin your upper arms by your ribcage throughout the entire lift.
  * *Self-check:* Look in the mirror and make sure your elbows stay locked to your torso rather than creeping forward or winging out to the sides.
* **Rep Detail:** This is entirely a fatigue issue. It only popped up on reps 8, 9, and 10 as your muscles started getting tired toward the end of the set.

---

### Next Session Plan

1. **Lock your elbows in:** For your next workout, consciously pin your upper arms to your sides from the very first rep, and if you feel them starting to drift on reps 8-10, fight to keep them tucked.
2. **Commit to full extension:** Make a mental note on every single rep—especially early in the set like rep 3—to let your arms straighten completely at the bottom before initiating the curl.
3. **Manage fatigue:** Since elbow flare only hit at the tail end of your set, consider dropping the weight slightly or stopping the set one rep earlier if your form starts to break down.

### WITHOUT RAG
### Progress Tracking

Great job on this session—you’re moving in the right direction. Your overall score ticked up to 81 (from 75), and you doubled your clean reps, hitting 6 correct out of 10 compared to just 3 in your last workout. 

While "Partial range of motion" is still popping up occasionally, you've cut those instances down significantly. The main culprit holding you back now is "Elbow flare," which started creeping in toward the end of the set as fatigue set in.

---

### Error Breakdown

#### 1. Partial Range of Motion
* **What it is:** You're cutting the movement short before fully completing the lift, specifically happening on the way up during rep 3. 
* **Why it matters:** Stopping short cheats your biceps out of the full contraction they need to grow stronger and adapt, meaning you aren't getting the full benefit of the exercise.
* **How to fix it:** 
  * **Cue:** Think about driving your knuckles all the way up to your shoulders before you reverse direction.
  * **Setup/Tempo:** Take a brief, one-second pause at the very top of the curl to ensure you've squeezed the bicep completely before lowering the weight.
  * **Drill:** Drop the weight slightly if you need to, and practice performing slow, deliberate reps where you consciously touch the top position.
  * **Self-check:** Glance in the mirror or check your video to confirm your forearm touches or comes tight against your bicep at the top of every single rep.

#### 2. Elbow Flare
* **What it is:** Your elbows are drifting forward or flaring out away from your sides as you lift the weight, rather than staying locked by your ribs. This clustered heavily in your final reps (8 through 10) as you started getting tired.
* **Why it matters:** When your elbows wander, your shoulders and front delts start taking over the work, robbing your biceps of the tension they need and altering the lift.
* **How to fix it:** 
  * **Cue:** Imagine your elbows are pinned to your ribs by imaginary hinges, forcing the weight to move around them.
  * **Setup/Tempo:** Because this happened on reps 8, 9, and 10, your muscles simply fatigued. Stop your set a rep or two earlier when your form starts to break down, or drop the load slightly so you can maintain strict control through the end.
  * **Drill:** Stand with your back and upper arms lightly touching a wall or keep a rolled-up towel tucked under each armpit to feel if they start to slip forward.
  * **Self-check:** Watch your side-profile video to see if your upper arms stay glued to your torso or if they swing forward as the weight gets heavy.

---

### Next Session Plan

1. **Protect your elbow position:** Keep your upper arms pinned to your sides from the very first rep to the last, using a lighter weight if your elbows start to drift.
2. **Watch the fatigue threshold:** Since elbow flare and partial reps showed up late in the set, stop your set one rep *before* your form starts to degrade.
3. **Commit to the top squeeze:** Make sure every single rep reaches full range by pausing briefly at the top with a hard bicep squeeze.

---


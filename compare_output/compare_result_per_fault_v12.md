# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions_per_fault.json` |
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
2. Error Breakdown: for each distinct error in the session, write these five as five separate
   top-level bullets, in this order. Do not nest one inside another.
   - What it is, in plain words: describe the fault the way you would point it out to someone
     mid-set.
   - Why it matters: which joint or muscle takes the extra load, and then - always - what that
     means for this person. Finish the thought: what will they feel, where, and when; what does
     it cost them in strength, in muscle actually worked, or in reps they can trust; what does
     it risk as the load goes up. A statement of mechanics on its own is not an answer to "why
     does this matter to me". One or two sentences. Base it on the `consequence` entries in the
     Context when one passes the relevance rule below; if none does, keep it to general,
     non-specific terms.
   - How to fix it: a `principle` entry tells you what correct looks like - it is not itself
     the fix, and restating it does not count as giving one. Write four distinct items:
     (a) one cue to think about during the rep; (b) a setup change that names a variable they
     can actually turn - stance width, depth, tempo, load, a pause, a range limit - repeating
     the cue in other words is not a setup change; (c) a drill or lighter regression they can
     practise, and if there honestly isn't one for this fault, say so rather than padding;
     (d) a simple self-check so they know it worked - something they can see in a mirror, feel,
     or notice on a phone video.
   - Use the rep detail: if the error clusters in one phase (descending / ascending) or in the
     later reps of the set, say so and tailor the advice to it (e.g. stop the set a rep earlier,
     drop the load, slow the descent).
3. Next Session Plan: close with 2-3 short, prioritised things to do in their next workout.
4. Tone: encouraging, direct, and specific. Short paragraphs and bullets. No filler, no lecture.

Sessions with no errors: if the session records no errors, write the Progress Tracking section
and a Next Session Plan about holding the standard they just hit. Do not go looking through the
Context for something else to change, and do not suggest a different version of the exercise
(a narrower grip, a different stance) as a way to have something to say. A clean session is the
result, not a gap to fill.

Stick to their numbers: rep numbers, rep counts, scores and error names come from the session
JSON and nothing else. They must match it exactly. If you say "the last three reps", list three.
Keep the two sessions apart. The previous session's error list is history: if a name appears
there but in none of this session's reps, that fault is GONE - credit them for clearing it, and
never attach it to a rep they did today. Faults with similar names are still different faults
(a wrist that folds back and a grip that is too wide are not the same error) - when you name the
fault on a given rep, use the name that rep actually carries in this session's data.

How to read the Context: every entry starts with a header line of the form
[<kind> | re: <which error it was retrieved for> | source: <source name>], followed by the
entry text. `kind` is one of: mistake (a known incorrect form), finding (a concrete result
from that source), principle (general correct-form guidance). The source name is for internal
tracking only. Never quote the header line itself back to the user.

No citations in the feedback: do not name any study, author, organisation, URL, document title,
or "the knowledge base", and do not write "according to", "research shows", "as noted in", or
any similar attribution. Use the facts from the Context as plain statements in your own words.
The reader should see coaching, not a literature review.

Translation rule - applies to every word you write, not just the "What it is" bullet. The
Context is written by and for researchers; it is what you reason FROM, not a phrasebook to
quote. The reader never sees it. Whenever an anatomical or biomechanical term appears in your
answer - in "Why it matters" and "How to fix it" just as much as anywhere else - give its
everyday meaning in the same sentence, or use the everyday meaning instead. Terms that need
this treatment include: posterior pelvic tilt, lordotic / lumbar lordosis, lumbar flexion,
knee extension moment, knee extensor musculature, hip extensors, plantar flexors, lead lower
extremity, lower-extremity segments, biarticular, hypertrophy, brachii, muscular complex,
kinematic, medial knee displacement, supinated, and anything else you would not say out loud
to someone between sets. Examples of the move - these are worked in a movement you are NOT being
asked about, on purpose: the point is the move, not the answer: "ulnar deviation" -> "your wrist
bends over toward your little-finger side"; "maintain a neutral cervical position" -> "keep your
head in line with your spine instead of craning it up"; "a higher wrist extension moment" ->
"the back of your wrist and your forearm soak up more of the work, so the wrist starts aching
before the muscle you are actually training is anywhere near done"; "plantar flexors" ->
"calves"; "suboptimal hypertrophy" -> "less muscle growth for the same effort". You may use these bare, no explanation needed: quads, hamstrings, glutes, core, lats,
biceps, triceps, calves, knee, hip, shoulder, lower back.

Write it yourself: never reuse a sentence, a clause, or a distinctive phrase from the Context.
Every fact you take from it has to be re-expressed in your own words before it reaches the
reader. Copying a Context sentence because it is already accurate is the single most common way
this feedback goes wrong - accuracy is not the standard, being useful to this reader is.
  Wrong: "Permitting excessive wrist extension during the pressing phase increases load on the
  radiocarpal joint and may produce discomfort that limits performance."
  Right: "When your wrist folds back under the weight, the joint takes the load instead of your
  palm stacking over your forearm - that's the ache that turns up a few sets in, and it caps
  what you can lift long before the muscle you came to train is done."

Relevance rule: the `re:` label says which error an entry was RETRIEVED for, not that it
describes that error - retrieval is approximate and some entries are near misses. Before
using an entry for an error, check that its text plainly describes that error (or, for a
principle, the correct form that fixes it). Ignore an entry entirely - do not use it,
mention it, or reframe it as related - if it describes a different fault or a different
exercise variant, if it is a study protocol or setup detail with no consequence attached,
or if following it would push the user further into the error being discussed. Using fewer
entries accurately is better than using every entry.

Grounding rule, part 1 - the facts are fixed. When an entry that passes the relevance rule
contains a specific number, percentage, or joint angle that helps the user (a depth target, a
reason the fault matters), state it - without attribution - as part of the explanation or the
fix; those specifics are the most valuable thing you have. Do NOT state any specific number,
percentage, joint angle, study finding, sample size, or date range that does not appear
verbatim in the Context below - even if you recognize the fact or believe it to be true from
your own general knowledge. Your own training knowledge must never substitute for the Context;
if a fact is not in the Context, treat it as unavailable. If the Context has no specifics for
a given error, fall back to general accepted coaching principles, described in general terms
only with no invented numbers.

Grounding rule, part 2 - the wording is never fixed. "Verbatim" above governs numbers and
facts only. It says nothing about phrasing, and it is not permission to quote: reproducing a
Context sentence in order to stay safe is itself a violation of the Translation rule. Keep the
number exactly as given; build the sentence around it yourself. A "120-second inter-set recovery
period" stays 120 seconds, but it reaches the reader as "give yourself a full two minutes between
sets before you go again". Note that this example is deliberately not about any fault you are
likely to be shown: do not carry its number, its wording, or its subject into your answer.

Context from Knowledge Base:
{context}
```

---

## Exercise: Squat — Butt wink

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Butt wink | Lumbar flexion (butt wink): posterior pelvic tilt and rounding of the lower back at the bottom of the squat | 0.032 / 2* | 0.156 / 1* | 0.111 / 2* | 0.116 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Butt wink | source: www.nasm.org/resource-center/blog/training/biomechanics-of-the-squat]
Posterior pelvic tilt ('butt wink') where the pelvis tucks under and the low back rounds at the bottom of a squat.

[mistake | re: Butt wink | source: blog.nasm.org/newletter/squat-form]
Losing lumbar lordosis during the squat movement.

[consequence | re: Butt wink | source: ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN]
Forcing deep hip flexion without accommodating the necessary hip abduction and external rotation causes the pelvis to tilt posteriorly and the lumbar spine to flex.

[principle | re: Butt wink | source: TheBackSquatAProposedAssessment]
The squat requires sufficient spinal mobility to assume and maintain a slight lordotic posture.

[consequence | re: Butt wink | source: TheBackSquatAProposedAssessment]
Allowing the spine to flex during a squat compromises back curvature and can lead to eventual pain and suboptimal performance.

[principle | re: Butt wink | source: TheBackSquatAProposedAssessment]
The individual must maintain a stiffened torso with a neutral, lordotic lumbar position as a safe and optimal squat strategy.

[finding | re: Butt wink | source: TheBackSquatAProposedAssessment]
If the athlete flexes at the spine before 120 degrees of hip flexion when squatting, they may have restriction in the posterior fibers of the iliotibial band or lack of lumbar control.
```

### WITH RAG
### Progress Tracking

Solid step forward compared to your September 20 session. Your overall score ticked up from 71 to 76, and you nailed 6 correct reps today compared to just 4 last time. Even better, knee valgus has completely vanished from your list of faults. You've got one lingering issue to clean up—"butt wink" popped up on reps 4, 6, 8, and 9 during the descent—but the direction of travel is entirely positive. Let's lock that remaining piece in.

***

### Error Breakdown: Butt wink

*   **What it is:** As you drop down into the bottom of the squat, your tailbone tucks underneath you and your lower back rounds instead of staying locked in its natural slight arch.
*   **Why it matters:** When your lower spine flexes under the load, it compromises your back curvature, which can lead to eventual pain and less-than-best performance as you try to drive back up.
*   **How to fix it:** 
    *   (a) Cue to think about: Push your knees out wide and keep your chest proud as you lower yourself down.
    *   (b) Setup change: Take a slightly wider stance and turn your toes out just a fraction more to give your hips the room they need before you initiate the descent.
    *   (c) Drill or regression: Try a box squat stopping just above parallel to groove the descent without letting your hips roll under at the very bottom.
    *   (d) Self-check: Set your phone up to record a side-view video and check if your lower back stays flat and extended all the way through the bottom of the movement, or if it folds at the end.

***

### Next Session Plan

1. **Warm up the hips wider:** Spend a few extra minutes opening up your hips with bodyweight squats focusing on that wider stance before touching the bar.
2. **Watch the descent on video:** Film your working sets from the side, paying close attention to reps 4 and onward where fatigue tends to make that lower back round creep back in.

### WITHOUT RAG
### Progress Tracking

Good movement on the numbers today. You bumped your overall score up to 76 (from 71 last time) and hit 6 correct reps instead of 4. Even better, you completely cleared knee valgus out of your squat—that old fault is gone. You still had some lower back rounding pop up on reps 4, 6, 8, and 9 during the descent, but overall you're moving in the right direction. 

***

### Error Breakdown: Butt wink

* **What it is, in plain words:** As you sink down into the bottom of the squat, your tailbone tucks under and your lower back rounds out instead of staying flat and braced. 
* **Why it matters:** This shifts the stress away from your glutes and core, dumping it directly onto your lower spine. You'll feel a dull ache in your lower back during or right after your sets, it robs you of your power out of the bottom, and it puts your spine at risk as you add heavier weight to the bar.
* **How to fix it:** 
  * (a) Think about proud chest and spreading your sits bones apart as you go down.
  * (b) Cut your depth slightly higher on each rep, stopping just before your lower back starts to round.
  * (c) Practice box squats to a height that keeps your lower back locked in.
  * (d) Glance in a side mirror or check your phone video to make sure your lower back stays arched from top to bottom.
  * **Use the rep detail:** Notice how this only happens on reps 4, 6, 8, and 9—it's creeping in as fatigue sets in mid-set. Stay extra tight on those later reps or cut your set short when your form starts slipping.

***

### Next Session Plan

1. **Keep your core locked on fatigue:** Since your lower back rounding showed up on the later reps (4, 6, 8, and 9), be ready for it when fatigue hits. Take an extra breath before those middle reps to reset your brace.
2. **Control your depth:** Stop your descent an inch higher if you need to, making sure your lower back stays flat before you drive back up.
3. **Build on your win:** Celebrate clearing out the knee wobble from your last session, and focus entirely on keeping that lower back stable today.

---

## Exercise: Squat — Knee valgus

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Knee valgus | Knee valgus: knees caving inward (medial knee displacement) during the squat | 0.034 / 3* | 0.045 / 1* | 0.091 / 2* | 0.090 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Knee valgus | source: Altered_Knee_and_Ankle_Kinemat]
Allowing the knees to cave inward (medial knee displacement) during the squat.

[mistake | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
Allowing the knees to collapse inward, also known as medial knee displacement, during the squat.

[mistake | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
Allowing the knees to cave inward medially during the squat.

[finding | re: Knee valgus | source: TheBackSquatAProposedAssessment]
Knee valgus is identified when the medial aspect of either knee passes the medial malleolus from the anterior perspective during any phase of the squat.

[principle | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
Avoiding medial knee displacement ensures that the rectus femoris remains active during the descent into peak knee flexion.

[consequence | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
A poorly performed squat with increased knee valgus may expose the lower extremity joints to excessive torques.

[principle | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
Maintain neutral lower extremity alignment during the squat to properly attenuate patellofemoral forces and stabilize the knee joint.

[consequence | re: Knee valgus | source: Effect of hip adductor (Squat)]
Allowing the knees to cave inward (valgus) increases stress on the knee joint.
```

### WITH RAG
### Progress Tracking

Your overall score dipped slightly to 78 compared to 82 in your previous session on 2026-09-20. You landed 6 correct reps today, which is down from 8 last time, leaving you with 4 incorrect reps instead of 2. The familiar issue of your knees caving inward followed you from the last workout, showing up on reps 3, 5, 8, and 10. The good news is your clean reps still look solid—let's look at what's happening when fatigue sets in.

### Error Breakdown

*   **What it is, in plain words:** Your knees are caving inward toward each other as you push yourself back up out of the bottom of the squat—specifically on reps 3, 5, 8, and 10 as fatigue sets in.
*   **Why it matters:** This puts a lot of extra twisting stress on your knee joints and surrounding leg bones. Over time, that adds up to unnecessary wear and tear on your knees and keeps you from getting the full muscle-building benefit out of your quads.
*   **How to fix it:** 
    (a) **Cue:** Think about actively pushing your knees outward to track directly over your toes on the way up. 
    (b) **Setup change:** Take a slightly narrower stance or slow down your tempo on the push-up phase so you can consciously control your knee tracking. 
    (c) **Drill:** Practice a lighter set with a mini-band placed just above your knees to give your legs constant feedback to push outward. 
    (d) **Self-check:** Glance in the mirror or record a side-on video to confirm your knees stay wide and don't pinch inward as you stand up.

### Next Session Plan

1. **Watch the fatigue factor:** Notice how your knees started collapsing on later reps (3, 5, 8, 10). On your next workout, if your form starts slipping around rep 7 or 8, rack the weight rather than grinding out sloppy reps.
2. **Focus on the push-up:** Spend your warm-up sets actively driving your knees wide during the ascent so the pattern becomes second nature before you touch your working weight.

### WITHOUT RAG
### Progress Tracking
Let’s look at how today stacked up against your last session on September 20th. Your overall score dipped slightly from 82 to 78, and your correct reps dropped from 8 down to 6, leaving you with 4 incorrect reps today instead of just 2. On the bright side, the specific error we tracked last time—knee valgus—is still the only issue showing up, meaning your movement pattern remains consistent; we just need to shore up your control as fatigue sets in.

### Error Breakdown

*   **What it is, in plain words:** On reps 3, 5, 8, and 10, your knees caved inward toward each other as you pushed yourself back up out of the bottom of the squat.
*   **Why it matters:** When your knees collapse inward, your hips and knees lose their stable alignment, forcing your inner thighs and joints to absorb forces they aren't meant to handle under a load. You will likely feel this as an awkward strain around your inner knees or a loss of power halfway up, which robs your glutes of the work they should be doing and leaves you vulnerable to nagging joint aches as you add more weight to the bar.
*   **How to fix it:** 
    *   (a) Cue: Think about actively spreading the floor apart with your feet as you stand up.
    *   (b) Setup: Bring your stance in slightly or point your toes out a fraction more to find a position where your knees naturally track right over your toes.
    *   (c) Drill: Loop a light resistance band just around your knees during your warm-up bodyweight squats to force your outer hips to stay awake.
    *   (d) Self-check: Watch your knees in the mirror or on a phone video to ensure they stay wide and track in line with your second and third toes the entire way up.
*   **Use the rep detail:** Notice that your first two reps were clean, and the inward cave only crept in on reps 3, 5, 8, and 10—specifically as you pushed through the ascent. This tells us it is a fatigue issue: your outer hips are getting tired and giving up toward the end of the movement. 

### Next Session Plan
1. **Manage fatigue:** When you feel your knees start to drift inward on the way up, treat that as your cue to rack the bar rather than grinding out sloppy reps.
2. **Warm up with bands:** Spend a few minutes doing banded squats before your working sets to prime the muscles on the outside of your hips that keep your knees tracking straight.
3. **Focus on the push:** Keep your mind locked on driving your knees outward the exact second you start pushing up from the bottom of every rep.

---

## Exercise: Squat — Partial squat

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Partial squat | Squatting too shallow, thighs not reaching parallel: partial or quarter squat depth | 0.061 / 2* | 0.196 / 2* | 0.152 / 2* | 0.161 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting to a depth where the top of the thighs do not reach parallel to the ground.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting too shallow, where the athlete does not achieve a depth of thighs at least parallel to the ground.

[consequence | re: Partial squat | source: TheBackSquatAProposedAssessment]
Without squatting to the proper depth, the hamstrings and gluteus muscular complex may not be adequately challenged.

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
Good job today—you pushed your overall score up to 80 (from 74 last session) and landed 6 correct reps instead of 5. Even better, you completely cleared "Butt wink" off the board since yesterday. The main thing holding you back now is depth control, which started slipping on the last four reps of the set. 

### Error Breakdown

* What it is, in plain words: You are cutting your depth short on the way down, finishing up with your thighs sitting above parallel instead of getting down to the proper depth where the tops of your thighs are at least parallel to the floor and your hip joint drops level with or slightly below your knees.
* Why it matters: When you stop short, your glutes and the backs of your thighs don't get fully challenged, and you miss out on that touch point where the backs of your thighs connect with your calves—a contact point that actually helps ease the compressive load on your knee joints. If you keep cutting reps high, you cheat yourself out of complete muscle development in your lower body and leave extra stress sitting right on your knees as the weight gets heavier.
* How to fix it: 
  (a) Think about sitting your hips back and down to actively chase that lower depth rather than stopping yourself halfway.
  (b) Widen your stance slightly or adjust your foot position during setup so you feel comfortable opening your hips up for a deeper descent.
  (c) Practice bodyweight box squats using a target set at the correct parallel height so you can feel the exact bottom position before adding load back on.
  (d) Check your phone video from the side to verify that your hip crease clears below the top of your knee at the bottom of the movement.
  (e) Notice how the error clusters on reps 7 through 10 as fatigue sets in—combat this by either ending your set a rep earlier when form breaks down, or taking a slightly longer breather before your final working sets to keep your depth honest.

### Next Session Plan
* Lock in your depth on every single rep: make sure those hips drop at least level with your knees right from rep one, and use a lower box or target if you need a physical reminder.
* Watch out for fatigue creep: once you hit rep 7 and your legs start getting heavy, focus extra hard on staying tight on the way down so you don't start shortening your range of motion.
* Celebrate the win on your hip mobility: since you successfully shook off the butt wink from last time, keep using that same solid core bracing as you push the depth lower.

### WITHOUT RAG
### Progress Tracking

Good work today—you moved the needle in the right direction. Your overall score ticked up from 74 to 80, and you banked 6 correct reps compared to 5 in your last session. Even better, you completely cleared "Butt wink" from your movement pattern, which is a massive win for your lower back. 

The main thing holding you back now is fatigue kicking in late: your form was dialed in for the first 6 reps, but "Partial squat" crept in on reps 7 through 10 as you headed down. Let's look at that final remaining error.

---

### Error Breakdown

#### Partial squat
* **What it is, in plain words:** You're cutting your depth short on the way down, turning a full squat into a half-rep before you even reach the bottom.
* **Why it matters:** When you cut the depth, your quads and glutes miss out on the full stretch and workload they need for maximum growth and strength gains. You end up burning energy without taking the muscles through their complete path, meaning fewer productive reps for your effort.
* **How to fix it:** 
  * (a) Think about sitting your hips down between your heels rather than just dropping your knees forward.
  * (b) Widen your stance slightly or point your toes out a fraction more to give your hips room to drop fully.
  * (c) Practice with a box or a target set at the correct depth so you have a physical cue to touch before coming back up.
  * (d) Set your phone up from the side and check that the crease of your hip drops below the top of your knee on every single rep.

---

### Next Session Plan

1. **Protect the early reps:** Keep the sharp focus you had on reps 1 through 6, making sure every single descent hits full depth right from the start.
2. **Manage fatigue:** When you hit rep 7, actively cue yourself to fight for depth instead of letting tiredness rush your descent. If your depth starts failing by rep 7 again, rack the bar and call it a set rather than grinding out shallow reps.

---

## Exercise: Push-up — Hip sag

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Hip sag | Allowing the hips to sag during the push-up | 0.048 / 1* | 0.180 / 2 | 0.129 / 2* | 0.143 / 1* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Hip sag | source: blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement]
Allowing the low back to arch or sag during the push-up as fatigue sets in.

[consequence | re: Hip sag | source: blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement]
Allowing the low back to arch or sag during a push-up decreases engagement of the deeper core stabilizers, increases involvement of the lumbar erectors, and increases stress on the vertebral discs.

[consequence | re: Hip sag | source: www.nasm.org/resource-center/exercise-library/push-up]
Allowing the hips to sag indicates core disengagement and reduces exercise effectiveness.

[principle | re: Hip sag | source: The_Effect_of_Position_on_the_Percentage_of_Body.992962]
Maintain a rigid spine and lower-extremity segments throughout the push-up movement.

[finding | re: Hip sag | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
The push-up cycle was standardized using a metronome to fix the repetition rate at 2 seconds, starting from the top position.

[finding | re: Hip sag | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
During shoulder-width push-ups, the elbow extension angle was 164.99 ± 3.09 degrees and the flexion angle was 96.91 ± 6.20 degrees.
```

### WITH RAG
### Progress Tracking

Good movement on this session—you brought your overall score up to 77 from 72 yesterday, and you hit 6 clean reps compared to 5 in your last workout. Even better, you completely cleared out partial range of motion, which is a big win for your working capacity. You still have one lingering habit to clean up, though: hip sag showed up on reps 6, 7, 9, and 10, creeping in as fatigue started to build in the second half of the set. 

***

### Error Breakdown

* **What it is, in plain words:** As you fatigue in the later reps—specifically on the way down for reps 6, 7, and 10, and on the way back up for rep 9—your hips drop and your lower back dips toward the floor instead of your whole body moving as a single rigid plank.
* **Why it matters:** When your midsection gives out, your deep core stabilizers turn off, dumping extra stress onto your lower back muscles and vertebral discs while making the exercise far less effective. That means you miss out on the full muscle-building stimulus you came for, and you invite dull lower-back aching that lingers long after you finish your set.
* **How to fix it:** 
  *(a) Cue:* Think about squeezing your glutes and bracing your stomach as if someone is about to poke you in the gut, holding that tension locked in from top to bottom.
  *(b) Setup change:* Shorten your working sets by stopping one rep before your hips usually start to drop—take 5 solid reps instead of pushing into messy ones, or drop to your knees to finish the set cleanly if you want to accumulate more volume.
  *(c) Drill:* Practice a strict plank hold on the floor for 20 to 30 seconds at a time to build the endurance needed to keep your spine locked during the push-up.
  *(d) Self-check:* Glance at a mirror sideways or set your phone up to record a side-profile video; if your hips dip below the straight line of your shoulders and heels on the way down, you'll see it instantly.

***

### Next Session Plan

1. **Protect your form first:** Cap your sets at the exact rep count right before your hips start to sag (aim for sets of 5 clean reps) rather than forcing ugly repetitions at the end.
2. **Lock your midline:** Focus intensely on squeezing your glutes and bracing your core on every single rep to keep your spine rigidly straight from head to heels.

### WITHOUT RAG
### Progress Tracking
Good job today—you are moving in the right direction. Your overall score ticked up to 77 from 72 in your previous session on 2026-09-20, and you nailed 6 correct reps compared to just 5 last time. Even better, you completely cleared the partial range of motion issue from your last workout. You still have one recurring hurdle to clear, so let's lock that in for the next session.

### Error Breakdown

* **What it is, in plain words:** Your hips drop toward the floor instead of your whole body moving as a single rigid plank, particularly as you start lowering yourself down or pushing back up on reps 6, 7, 9, and 10.
* **Why it matters:** When your midsection gives way, your lower back takes the stress instead of your core bracing the movement. That costs you strength and leaves your lower back feeling stiff or achy by the end of your set, robbing the chest and triceps of the clean work they should be doing.
* **How to fix it:** 
  (a) Think about squeezing your glutes and bracing your stomach as hard as you can, as if someone is about to poke you in the gut.
  (b) Set your feet slightly wider apart to give your lower body a more stable base of support before you start your set.
  (c) Try performing incline push-ups with your hands elevated on a sturdy bench or box to build up core endurance at a lighter angle.
  (d) Glance at a mirror sideways or prop your phone up to record a video—your shoulders, hips, and ankles should move together in a straight line with zero dip in the middle.

### Next Session Plan
1. **Focus on your core early:** Keep your glutes squeezed and stomach braced from rep one so you don't let your hips start sagging as fatigue sets in.
2. **Take a wider stance:** Widen your foot position slightly during setup to create a more stable platform and protect your lower back.
3. **Cut the set short if form breaks:** If your hips start dipping on later reps like they did today, stop the set right there rather than grinding through sloppy reps.

---

## Exercise: Push-up — Partial range of motion

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Partial range of motion | Not lowering deep enough: incomplete elbow flexion, failing to reach 90 degrees during the push-up | 0.079 / 1* | 0.186 / 2* | 0.154 / 2* | 0.139 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Partial range of motion | source: 10-week suspension and traditional push-up training]
Failing to acquire the correct depth of 90 degrees of elbow flexion.

[principle | re: Partial range of motion | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
Achieving deeper elbow flexion during push-ups increases the mechanical load and muscular demand on the triceps.

[principle | re: Partial range of motion | source: 10-week suspension and traditional push-up training]
Ensure the correct depth of 90 degrees of elbow flexion is acquired during each repetition.

[consequence | re: Partial range of motion | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
Restricting the range of motion during narrow-width push-ups develops and concentrates the load on the elbow joint.

[consequence | re: Partial range of motion | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
Failing to reach deep elbow flexion reduces the mechanical load and contractile demand placed on the triceps muscle.

[finding | re: Partial range of motion | source: 10-week suspension and traditional push-up training]
The study protocol monitored body form and required repetitions to be repeated if the correct depth of 90 degrees was not acquired.

[finding | re: Partial range of motion | source: www.nasm.org/resource-center/exercise-library/push-up]
Descend until your chest nearly touches the floor or your elbows bend to approximately 90 degrees.
```

### WITH RAG
### Progress Tracking
Let's look at how today stacked up against your last session on September 20. Your overall score dipped slightly from 80 to 78, and your correct reps dropped from 7 down to 6, leaving you with 4 incorrect reps today instead of 3. The same issue—partial range of motion—followed you over from last time and popped up on reps 2, 5, 8, and 10, particularly on the way down as fatigue started creeping in.

---

### Error Breakdown

*   **What it is, in plain words:** You are cutting your push-ups short on the descent instead of lowering yourself all the way down until your elbows bend to about 90 degrees or your chest gets close to the floor.
*   **Why it matters:** Stopping halfway means your elbow joints take the brunt of the stress while your triceps miss out on the mechanical load and muscle-building demand they need. That means fewer actual gains for your effort, and you're leaving muscle growth on the table.
*   **How to fix it:** 
    *   (a) *Cue:* Think about actively pulling your chest down to meet the floor rather than just waiting for gravity to stop you.
    *   (b) *Setup change:* Slow your tempo on the way down, taking a deliberate two-count to control the descent so you don't stall out early.
    *   (c) *Drill or regression:* If you find you can't hit depth without collapsing, drop your knees to the floor or elevate your hands on a sturdy bench to groove the full range of motion safely.
    *   (d) *Self-check:* Set up your phone from the side and check your video to confirm your elbows hit that roughly 90-degree bend before you press back up.

---

### Next Session Plan
1. **Slow down the descent:** Take an extra second on the way down for every single rep, especially when fatigue sets in on the later reps, to ensure you consistently hit your depth target.
2. **Cut the set short if form slips:** If you hit rep 5 or 8 and feel your range of motion cutting short again, rack or pause rather than grinding out shallow reps. Protect the quality of the movement.

### WITHOUT RAG
### Progress Tracking

Let's look at how today's push-up session compared to your last workout on September 20th. Your overall score dipped slightly from 80 to 78, and you landed 6 correct reps today compared to 7 last time, meaning incorrect reps ticked up from 3 to 4 (reps 2, 5, 8, and 10). The good news is that your core form remains solid for the majority of the set, but that recurring issue with partial range of motion is still hanging around. Let's get that ironed out so you can squeeze every ounce of muscle growth and strength out of your sets.

***

### Error Breakdown

*   **What it is, in plain words:** You are cutting your push-ups short on the way down, stopping well before your chest gets close to the floor on reps 2, 5, 8, and 10—notice how these errors creep in as fatigue sets in later in the set.
*   **Why it matters:** When you shorten the drop, your chest and arms do a fraction of the work they are supposed to, robbing you of full muscle engagement and leaving strength gains on the table. If you keep practicing abbreviated reps, you'll find it harder to build complete upper-body power as you try to push heavier loads.
*   **How to fix it:** 
    *   (a) *Cue:* Think about actively pulling your chest down toward the floor on every single descent, treating the bottom position like a solid checkpoint.
    *   (b) *Setup change:* Slow down the tempo of your descent, taking a full two seconds to lower yourself so you don't subconsciously brake early.
    *   (c) *Drill:* Drop your knees to the floor for a few light practice reps to get used to the feel of your chest touching the ground without having to fight full bodyweight fatigue.
    *   (d) *Self-check:* Watch yourself on a phone video or use a target object right under your chest (like a small rolled towel) to confirm you are actually hitting the bottom depth every time.

***

### Next Session Plan

1. **Slow down the first half:** Take a controlled, deliberate two-second descent on every rep, especially as you get tired in the later stages of the set, to prevent you from cutting the range of motion short.
2. **Use a depth marker:** Place a small object right beneath your chest so you have a physical target to brush against on reps 2, 5, 8, and 10, keeping your depth honest.
3. **Cut the set short if needed:** If fatigue causes your depth to collapse on rep 8, rack or rest rather than grinding out shallow reps that practice the wrong movement pattern.

---

## Exercise: Lunge — Excessive forward trunk lean

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Excessive forward trunk lean | Leaning the torso forward, excessive trunk lean during the lunge | 0.072 / 3* | 0.142 / 2* | 0.122 / 2* | 0.112 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Excessive forward trunk lean | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Allowing the upper torso and lower leg to shift too far forward during the lunge, which increases front knee loading.

[mistake | re: Excessive forward trunk lean | source: KritzCroninHume2009BodyweightlungeSCJ]
Allowing the thoracic spine to flex during the lunge, which is often associated with poor or imbalanced trunk extensors.

[mistake | re: Excessive forward trunk lean | source: Comparison_of_the_VMOVL_EMG_Activity_Ratio_Accordi]
Leaning the torso forward during the lunge instead of keeping the upper body upright.

[principle | re: Excessive forward trunk lean | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
Maintain an upright trunk during the lunge to avoid excessive forward or lateral trunk movement.

[principle | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Performing a forward lunge with the trunk forward increases the recruitment of the hip extensors.

[consequence | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Leaning the trunk forward during a lunge increases the range of hip and trunk flexion, which shifts the body's center of mass forward and increases weight bearing on the lead lower extremity.

[consequence | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Leaning the trunk forward during a lunge shifts the muscular demand, increasing the load on the hip extensors and ankle plantar flexors while reducing the load on the knee extensors.

[finding | re: Excessive forward trunk lean | source: Altered movement strategy during functional movement after an ACL injury, despite ACL reconstruction]
In a study of 12 ACL-injured patients and 15 controls, the standardized forward lunge protocol required flexing the front knee to approximately 90 degrees while keeping the upper body perpendicular to the ground.

[finding | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Performing a forward lunge with the trunk forward (LTF) is characterized by an increase in hip extensor impulse and a concomitant increase in the muscular actions of the hip extensors when compared to a normal lunge (NL).
```

### WITH RAG
### Progress Tracking

Good movement on this session. You brought your correct reps up from 4 to 6, pushed your overall score from 70 to 78, and cut your bad reps down from 6 to 4. Even better, you completely cleared the shallow lunge fault from your previous workout. You only have one remaining error to tidy up, and you kept it out of your last three reps completely.

***

### Error Breakdown

*   **What it is, in plain words:** You are letting your upper body tip and collapse forward toward your front knee as you move, instead of keeping your torso tall and stacked over your hips. This popped up mostly on your way down (reps 1, 3, and 7), plus once on the way back up on rep 5.
*   **Why it matters:** When your chest caves forward, your center of mass shifts out of position, throwing extra weight onto your front leg and dumping more work onto your hips and calves while taking the load off your quads. That means you are missing out on the quad development you came for, and as you add weight to the bar, that extra forward tilt places unneeded strain on your lower back.
*   **How to fix it:** 
    *   *(a) Cue:* Think about keeping your chest proud and shining your logo straight at the wall ahead of you on every single step.
    *   *(b) Setup change:* Slow your tempo down on the way into the front foot plant so you have time to catch your balance before you drop, and cut your depth slightly if you feel your chest starting to pull you down.
    *   *(c) Drill:* Try a bodyweight pause lunge where you step out, hold the bottom for a solid two-second count with your torso upright, and then drive back up.
    *   *(d) Self-check:* Glance in the side mirror or record your set on your phone—your shoulders should stay stacked directly over your hips from the top of the movement all the way to the bottom.
*   **Use the rep detail:** Notice how your trunk lean happened early and mid-set (reps 1, 3, 5, and 7) but vanished on reps 8, 9, and 10 as you settled in. That tells you your form gets cleaner once you find your rhythm, so make your warm-up sets extra deliberate to dial that posture in right from rep one.

***

### Next Session Plan

1. **Prioritise posture on warm-ups:** Spend your first few bodyweight reps focusing entirely on keeping your chest up and your torso vertical so that habit carries over into your working sets.
2. **Control the descent:** Slow down the step-out phase of every rep to prevent your upper body from tipping forward before you even reach the bottom.
3. **Finish strong:** Use your clean finish from today (reps 8 through 10) as your baseline standard—if your chest starts to drop as you fatigue, call the set there.

### WITHOUT RAG
### Progress Tracking

Solid improvements today compared to your last session on September 20. Your overall score ticked up from 70 to 78, and you landed 6 correct reps instead of just 4. Even better news: the shallow lunge error you struggled with last time is completely gone. You've only got one fault left to clean up—excessive forward trunk lean—which cropped up on reps 1, 3, 5, and 7.

---

### Error Breakdown

*   **What it is, in plain words:** Your chest is collapsing forward and your torso is tipping out over your front knee as you move, instead of staying tall and stacked over your hips.
*   **Why it matters:** When your upper body pitches forward, the load shifts away from your glutes and quads and piles extra stress onto your lower back. That costs you strength and steals the muscle-building stimulus from the legs you're trying to work, leaving your lower back fatigued and aching instead.
*   **How to fix it:** 
    *   (a) *Cue:* Think about painting a wall straight up and down with your spine as you drop into the lunge.
    *   (b) *Setup:* Slow down your tempo on the way down, pausing for a split second at the bottom to catch your balance before you push back up.
    *   (c) *Drill:* Drop the weight entirely and practice bodyweight reverse lunges, where stepping backward naturally makes it easier to keep your torso upright.
    *   (d) *Self-check:* Glance in a mirror sideways or set your phone up—your chest should stay open and proud rather than caved over your front thigh.
    *   *Note on rep detail:* Notice this leaned-over habit happened early and mid-set (reps 1, 3, 5, 7), but you totally fixed it on the final three reps (8, 9, 10) once you found your groove. Bring that focus to the very first rep next time.

---

### Next Session Plan

1. **Lead with upright posture:** Focus on keeping your chest tall right from rep 1 so you don't waste energy correcting your form midway through the set.
2. **Keep the tempo controlled:** Use a deliberate, slow descent on every single rep to stay balanced and prevent your torso from tipping forward.
3. **Carry over the depth:** Your depth was great today—hold onto that standard while locking in that vertical torso.

---

## Exercise: Lunge — Shallow lunge

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Shallow lunge | Shallow lunge: step too short, insufficient front knee flexion, front knee not reaching 90 degrees | 0.059 / 3* | 0.110 / 2* | 0.120 / 2* | 0.127 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Shallow lunge | source: mxn167Sp24]
Using an insufficient step length during the lunge.

[mistake | re: Shallow lunge | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Performing a shallow lunge where the front knee flexion angle only reaches 80 degrees, which increases knee joint displacement and extensor moments.

[mistake | re: Shallow lunge | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Performing a shallow lunge with only 80 degrees of knee flexion, which increases the knee extensor moment compared to deeper lunges.

[finding | re: Shallow lunge | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
The holding phase of a forward lunge requires participants to maintain body position at approximately 90 degrees of front knee flexion.

[consequence | re: Shallow lunge | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
A shallower lunge of 80 degrees of knee flexion generates a higher knee extension moment, which increases the mechanical demand on the knee extensor musculature.

[consequence | re: Shallow lunge | source: Influence of the Exhaustion of the Gluteus Medius on the Knee Adduction Moment During Forward Lunge Exercise]
Using a shorter step length (shallow lunge) limits the recruitment and activation of the gluteus medius muscle.

[principle | re: Shallow lunge | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
During the descending phase of the lunge, the front knee should be flexed to approximately 90 degrees.

[principle | re: Shallow lunge | source: mxn167Sp24]
Using a longer step length during a lunge helps minimize anterior tibial translation over the toes and reduces joint forces.

[finding | re: Shallow lunge | source: lunge_knowledge]
In the study's specific lunge protocol, the forward knee was flexed to 45 degrees while the rear knee remained in full extension with both heels in contact with the floor.
```

### WITH RAG
### Progress Tracking
Great job stepping it up since yesterday. Your overall score ticked up from 75 to 77, and you nailed 6 correct reps today compared to 5 in your last session, dropping your mistakes down from 5 to 4. Even better news: "Insufficient back knee flexion" is completely gone from your error list. You only have one fault left to iron out, so let's get it sorted.

### Error Breakdown

*   **What it is, in plain words:** You are cutting your step short on the way down, leaving your front knee bending to roughly 80 degrees instead of getting all the way down into a full lunge. This fault pops up during the descending phase as fatigue starts to creep in.
*   **Why it matters:** Stopping short piles extra mechanical demand onto your quads while failing to properly recruit your gluteus medius on the side of your hip. That means your quads take a beating and tire out faster, but you miss out on the balanced muscle activation you are working for, leaving your hips undercooked.
*   **How to fix it:**
    *   *(a) Cue to think about:* Focus on dropping your back knee straight down toward the floor on every step.
    *   *(b) Setup change:* Take a slightly longer step forward when you initiate the movement to give your body room to sink into that bottom position.
    *   *(c) Drill or lighter regression:* Slow down your tempo on the way down, taking a full two seconds to ease into the bottom position so you stop cutting the depth short.
    *   *(d) Self-check:* Glance in a side mirror or check your phone video to confirm your front knee hits roughly 90 degrees at the bottom before you push back up.

### Next Session Plan
1. **Take a longer stride:** Step out just a few inches further on every rep to naturally force your front knee into a deeper bend.
2. **Slow your descent:** Count two full seconds on the way down for all 10 reps to keep your depth honest right up to the end of the set.
3. **Watch the fatigue:** Since your shallow reps tend to happen later in the set, stay hyper-focused on your depth on reps 6 through 10.

### WITHOUT RAG
### Progress Tracking
Good work today—you bumped your overall score up to 77 (from 75 yesterday) and hit 6 correct reps instead of 5. Even better, you completely cleared out the "Insufficient back knee flexion" issue from your last session. The one lingering habit is the shallow depth, which popped up on reps 2, 4, 6, and 9. Let's lock that down so you can nail the full set next time.

***

* **What it is, in plain words:** On your way down, you're cutting the movement short before your legs hit the right depth.
* **Why it matters:** Stopping early cheats your quads and glutes out of the full stretch and workload they need to grow stronger, meaning you get less muscle building for the exact same effort.
* **How to fix it:** 
  (a) Cue: Think about gently kissing your back knee to the floor on every descent. 
  (b) Setup change: Take a slightly longer stride forward so your legs have the room to drop properly without your front knee drifting too far past your toes.
  (c) Drill: Practice a few bodyweight paused lunges, holding the bottom position for a full two seconds to build comfort in the deep part of the movement.
  (d) Self-check: Glance in the side mirror or record your set—your front thigh should roughly parallel the floor at the bottom.

***

### Next Session Plan
1. **Pace your descent:** Take an extra half-second on the way down for reps 2, 4, 6, and 9 (where you tend to rush and cut the depth short).
2. **Commit to the stride:** Measure out your starting stance so you have plenty of room to sink your hips straight down rather than pitching forward.

---

## Exercise: Lunge — Insufficient back knee flexion

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Insufficient back knee flexion | Insufficient back knee flexion: rear knee not lowering toward the floor during the lunge | 0.060 / 1* | 0.108 / 2* | 0.103 / 2 | 0.106 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Insufficient back knee flexion | source: Influence of the Exhaustion of the Gluteus Medius on the Knee Adduction Moment During Forward Lunge Exercise]
Loss of full range of motion during the lunge, such as failing to lower the rear knee to ankle height.

[consequence | re: Insufficient back knee flexion | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
A shallower lunge of 80 degrees of knee flexion generates a higher knee extension moment, which increases the mechanical demand on the knee extensor musculature.

[consequence | re: Insufficient back knee flexion | source: Altered movement strategy during functional movement after an ACL injury, despite ACL reconstruction]
Knee valgus and excessive side-to-side knee movement during the lunge raise concern regarding the potential increased risk of a knee injury.

[principle | re: Insufficient back knee flexion | source: KritzCroninHume2009BodyweightlungeSCJ]
The back knee should be flexed during the lunge.

[finding | re: Insufficient back knee flexion | source: lunge_knowledge]
In the study's specific lunge protocol, the forward knee was flexed to 45 degrees while the rear knee remained in full extension with both heels in contact with the floor.

[principle | re: Insufficient back knee flexion | source: lunge_knowledge]
Both the anterior and posterior legs should achieve a knee joint range of motion of 0 to 90 degrees during the lunge.

[finding | re: Insufficient back knee flexion | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
The target depth for the trailing knee was defined as 2 to 3 cm short of contacting the ground.
```

### WITH RAG
### Progress Tracking
You landed 6 clean reps out of 10 today, giving you an overall score of 78. Compared to your last session on September 20—where you hit 7 correct reps and scored an 81—your numbers slipped just a fraction. The same exact issue, insufficient back knee flexion, followed you over from last time, showing up on reps 5, 7, 8, and 10 as you headed down into the lunge. You are still holding onto a solid baseline in the first half of your set, but fatigue is catching up and cutting your range of motion short as you tire out.

### Error Breakdown

* **What it is, in plain words:** You are stopping your back leg from bending all the way, leaving your rear knee floating high instead of dropping down toward the floor as you step forward.
* **Why it matters:** Cutting the drop short forces your front thigh to soak up extra strain because it has to handle the mechanical load of an incomplete range of motion. For you, that means your quads are going to burn out faster and carry a heavier brunt of the work on those shallower reps, leaving you with less muscle growth for the same effort and burning through your energy quicker than you should.
* **How to fix it:** 
  - (a) Cue: Focus on driving your back knee straight down toward the ground rather than lunging forward into the front leg.
  - (b) Setup: Take a slightly more deliberate tempo on your way down, making sure you control the descent so you have time to drop the back hip fully.
  - (c) Drill: Practice bodyweight split squats where you place a small target or pad two to three centimeters above the floor for your back knee to lightly graze, so you train the exact depth you need.
  - (d) Self-check: Watch your side-profile video and check that your back knee gets low enough to nearly brush the floor on every single repetition.
* **Use the rep detail:** This fault is entirely a fatigue problem, appearing exclusively on the descending phase of the later reps (5, 7, 8, and 10). Because it creeps in as you tire, your best tool here is to catch it before it starts—either stop your set one rep earlier when your depth begins to fail, or take an extra breath between those later reps to keep your form sharp.

### Next Session Plan
1. Prioritize depth from the very first rep by aiming your back knee straight down toward the floor, using your self-check video to confirm you are hitting the target.
2. Cut your set short at the exact moment fatigue causes your back knee to stay high—stopping at 8 clean reps is better than grinding out 10 sloppy ones.

### WITHOUT RAG
### Progress Tracking
Let's look at how today compares to your previous session on September 20th. Your overall score dipped slightly from 81 to 78, and your correct reps dropped from 7 down to 6 (with 4 incorrect reps today compared to 3 previously). The good news is that the error we saw last time—**Insufficient back knee flexion**—is still your main technical hurdle, popping up on reps 5, 7, 8, and particularly as fatigue sets in toward the end of the set. Let's iron that out so you can hold your form all the way through.

---

### Error Breakdown: Insufficient back knee flexion

*   **What it is, in plain words:** As you step down into the lunge, your back knee stays too straight instead of dropping down smoothly toward the floor.
*   **Why it matters:** Your front leg ends up doing almost all the heavy lifting while your back leg just tags along, which cheats your glutes and quads out of the work they should be doing. You'll feel this as an uneven burn—your front thigh will fry much faster while your back leg coasts—and it cuts down the muscle growth you are earning for the effort you put in.
*   **How to fix it:** 
    *   (a) *Cue:* Think about dropping your back knee straight down to kiss the floor on every rep, rather than lunging forward.
    *   (b) *Setup change:* Shorten your stride slightly if your back leg feels too far out of reach to bend comfortably.
    *   (c) *Drill:* Try bodyweight reverse lunges on a slight deficit or just pause at the bottom for a one-second count to force that back knee to bend fully.
    *   (d) *Self-check:* Watch yourself in a side-profile mirror and check that your back shin gets close to parallel with the floor at the bottom of the dip.
*   **Use the rep detail:** Notice how this error only shows up on the descending phase of reps 5, 7, 8, and 10—right when your legs start getting tired. When you feel your form slipping halfway through the set, take a quick extra breath before starting the next rep to keep your depth honest.

---

### Next Session Plan
1. **Prioritise back leg depth early:** Focus heavily on bending that back knee from rep one so the habit sticks when fatigue hits.
2. **Watch the fatigue window:** On reps 5 through 10, slow your descent down by one second to stay in control and stop that back leg from locking up early.

---

## Exercise: Bicep Curl — Elbow flare

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Elbow flare | Allowing the elbows to flare outward or drift forward away from the body during the curl | 0.046 / 2* | 0.202 / 2 | 0.149 / 1* | 0.184 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Allowing the elbows to pull forward when performing curls.

[mistake | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Allowing the elbows to move from their stationary position near the waist during the curl.

[consequence | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Because the biceps brachii is a biarticular muscle responsible for both elbow flexion and shoulder stabilization, it can cause the elbows to pull forward during curls.

[principle | re: Elbow flare | source: A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve]
The elbows must be kept close to the body during the movement.

[principle | re: Elbow flare | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
Use an elbow stabilizing plate or maintain strict elbow positioning to ensure that the full range of motion of the elbow joint is achieved and to prevent swinging the elbows.

[finding | re: Elbow flare | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
A 21-year-old female performing 3 sets of bilateral dumbbell bicep curls to failure at 30% 1RM (totaling 143 repetitions) developed exertional rhabdomyolysis with a peak creatine kinase (CK) concentration of approximately 12,200 U/L.

[finding | re: Elbow flare | source: The interplay between muscle length, range of motion, and exercise selection a review]
In the preacher curl, the peak of torque and greatest external moment arm occur at approximately 45 degrees to 50 degrees of elbow flexion.
```

### WITH RAG
### Progress Tracking
Solid work today. You brought your overall score up from 73 to 79 and bumped your clean reps from 4 up to 6. Even better, you completely cleared out "Partial range of motion" from your previous session—that error is gone. You still hit some bumps with elbow movement on the back half of the set, but you showed you can hold strict form for a solid majority of the reps.

---

### Error Breakdown

- **What it is, in plain words:** Your elbows are drifting forward and straying from their fixed position by your sides as you lift the weight up on reps 6, 8, 9, and 10.
- **Why it matters:** Because your biceps cross both your elbow and your shoulder joint, they naturally try to help steady your shoulder when they get tired, which pulls your elbows out of place. This means your front shoulders and upper back end up taking over part of the load meant for your biceps, so you get less direct muscle growth for your effort and lose strict tension on the target muscle right when it matters most.
- **How to fix it:** 
  - (a) Cue to think about: Pretend there is a wall right behind your elbows, and keep them pinned back against it as you lift.
  - (b) Setup change: Lighten the weight slightly so you aren't forced to use momentum or recruit your shoulders to finish the curl.
  - (c) Drill or regression: Try doing your curls seated against a bench backrest or with your upper arms resting against an upright pad to physically block your elbows from creeping forward.
  - (d) Self-check: Watch your side profile in the mirror or on video—if your elbows travel forward away from your torso as the weight goes up, the rep doesn't count.
- **Use the rep detail:** Notice how this fault only shows up on the last four reps (6, 8, 9, and 10) during the lifting phase. That tells you fatigue is creeping in and breaking your form; next time, either drop the weight slightly or cut the set off a rep or two earlier before your elbows start to wander.

---

### Next Session Plan
1. **Pin your elbows:** Start your next set with a slightly lighter weight and focus entirely on locking your upper arms by your sides from the very first rep to the last.
2. **Cut the set short:** The moment you feel your elbows start to slide forward, rack the weight or stop—don't grind out sloppy reps that practice the wrong movement pattern.

### WITHOUT RAG
### Progress Tracking

Solid effort today. You hit 6 correct reps out of 10, bringing your overall score up to 79—an improvement over yesterday's score of 73 and your previous 4 correct reps. Even better, you completely cleared "Partial range of motion" off the board. The only fault showing up now is "Elbow flare," which cropped up exclusively on your way up during the final four reps (reps 6, 8, 9, and 10) as fatigue started to creep in. Let's lock that down so you can carry a clean set all the way through next time.

***

### Error Breakdown

*   **What it is, in plain words:** Your elbows are drifting forward and away from your sides as you curl the weight up, rather than staying pinned by your ribs.
*   **Why it matters:** When your elbows drift forward, your front shoulders and upper back end up taking over the work that your biceps are supposed to be doing. That means less muscle growth for the exact effort you're putting in, and as the weight gets heavier, it places awkward strain on the front of your shoulder joint.
*   **How to fix it:** 
    *   (a) *Cue:* Think about keeping your elbows glued to your ribs like they're pinned in place by imaginary clamps.
    *   (b) *Setup:* Drop the weight slightly so you aren't forced to use momentum or shift your upper body to finish the curl.
    *   (c) *Drill:* Practice with your back lightly touching a wall to physically block your elbows from creeping forward.
    *   (d) *Self-check:* Watch yourself in the side-profile mirror; if your upper arm moves forward at all during the lift, you'll see the gap open up between your elbow and your torso.

***

### Next Session Plan

*   **Drop the weight slightly:** Start your next session with a load that lets you control all 10 reps without needing to heave or let your elbows drift.
*   **Watch the back half:** Since your elbow flare only showed up on reps 6 through 10, stay extra disciplined with your form as soon as fatigue kicks in during the second half of the set.
*   **Use the wall check:** Spend a quick warm-up set with your back against a wall to reset the feel of keeping your elbows locked strictly by your sides.

---

## Exercise: Bicep Curl — Partial range of motion

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Partial range of motion | Failing to achieve complete arm extension at the bottom of the curl and full elbow flexion at the top: partial repetitions with a limited range of motion | 0.065 / 3* | 0.168 / 2* | 0.171 / 2* | 0.142 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Partial range of motion | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
Failing to achieve the full range of motion of the elbow joint during each repetition.

[mistake | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Performing partial range of motion repetitions that restrict the muscle to short muscle lengths, thereby avoiding the fully stretched position.

[mistake | re: Partial range of motion | source: Scandinavian Med Sci Sports - 2014 - Brandner - Unilateral bicep curl hemodynamics  Low‐pressure continuous vs]
Failing to start the movement with the elbow in full extension.

[principle | re: Partial range of motion | source: Scandinavian Med Sci Sports - 2014 - Brandner - Unilateral bicep curl hemodynamics  Low‐pressure continuous vs]
Start the bicep curl with the elbow in full extension and the forearm supinated.

[principle | re: Partial range of motion | source: The_Rest-Pause_Biceps_Curl_Exercise_Effect_on_Biceps_Brachii_Muscle_of_Women_A_Study_of_Mechanical_Responsiveness]
Incorporate isometric pauses at 0 degrees, 90 degrees, and 135 degrees of the range of motion to target isometric contractions of the biceps brachii.

[finding | re: Partial range of motion | source: Optimizing Resistance Training Technique to Maximize Muscle Hypertrophy A Narrative Review]
Partial repetitions at shorter-muscle lengths are not as hypertrophic as partial repetitions at longer-muscle lengths.

[consequence | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Restricting movement to the final range of motion (short muscle lengths) results in suboptimal muscle hypertrophy compared to utilizing the initial range of motion where the muscle is fully stretched.

[consequence | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Failing to train at longer muscle lengths by restricting movement to shorter muscle lengths (final ROM) fails to optimize muscle hypertrophy.

[finding | re: Partial range of motion | source: The_Rest-Pause_Biceps_Curl_Exercise_Effect_on_Biceps_Brachii_Muscle_of_Women_A_Study_of_Mechanical_Responsiveness]
Maximum muscle force was attained at the onset of the t3 movement phase (elbow joint angle increasing from 90 to 135 degrees) and at the onset of the t5 movement phase (elbow joint angle decreasing from 135 to 90 degrees).
```

### WITH RAG
### Progress Tracking
Good work today. You hit 6 correct reps out of 10, bringing your overall score up to 79 compared to 77 in your last session yesterday. You also picked up one more clean rep, moving from 5 to 6. More importantly, you completely cleared elbow flare off your list—that error is gone. You only have one fault left to clean up: partial range of motion, which popped up on reps 3, 4, 7, and 10. 

### Error Breakdown: Partial range of motion

*   **What it is, in plain words:** You are cutting your reps short instead of going all the way down to a fully straight arm, especially on the way down or halfway through the lift.
*   **Why it matters:** Stopping short keeps the muscle locked in a cramped position and skips the fully stretched bottom half where the magic happens. That means less muscle growth for the exact same amount of sweat and effort.
*   **How to fix it:** 
    (a) *Cue:* Think about driving your knuckles all the way down to the floor at the bottom of every single rep. 
    (b) *Setup change:* If the weight feels too heavy to lock your arms out fully without cheating, drop the load slightly so you can handle the complete stretch. 
    (c) *Drill:* Practice a few bodyweight or very light reps where you pause for a full second at the bottom with your arms completely straight before curling back up. 
    (d) *Self-check:* Watch yourself in the mirror and make sure your elbow straightens out completely before you start pulling the weight back up.

### Next Session Plan
*   Drop your working weight slightly if you need to, making sure every single rep starts with your arms fully straight and ends with a full squeeze.
*   Keep that tight elbow position locked in—you completely cleared the elbow flare from last time, so make sure it stays gone.

### WITHOUT RAG
### Progress Tracking
Good work today. You bumped your overall score up slightly from 77 to 79 and knocked out 6 clean reps compared to 5 in your previous session on 2026-09-20. Even better, you completely cleared elbow flare out of your set—that error is gone. You still ran into trouble with partial range of motion on reps 3, 4, 7, and 10, but overall you are heading in the right direction. 

***

### Error Breakdown: Partial range of motion

*   **What it is, in plain words:** You are cutting your reps short instead of finishing the full movement—stopping before your arms are fully locked out at the bottom or before you have curled all the way up to the top.
*   **Why it matters:** When you cut your reps short, your biceps miss out on the full stretch and contraction they are built for, meaning less muscle growth for the exact same amount of effort. You also leave strength gains on the table because you are only working part of the path.
*   **How to fix it:** 
    *   (a) *Cue:* Focus on squeezing your biceps hard at the very top and fully straightening your arms at the very bottom on every single rep.
    *   (b) *Setup change:* Drop the weight slightly so you can handle the full movement without needing to cut corners when fatigue sets in.
    *   (c) *Drill:* Try a two-second pause at the bottom and a one-second pause at the top of each rep to force yourself into the full range.
    *   (d) *Self-check:* Watch yourself in the mirror and make sure your elbow reaches a straight line at the bottom and a tight squeeze at the top before you turn the rep around.
*   **Use the rep detail:** This error popped up intermittently on reps 3, 4, 7, and 10—both on the way down and on the way up—showing up as fatigue started creeping in. Don't rush these transitions; take a deliberate second to reset your posture if you feel yourself cutting the next rep short.

***

### Next Session Plan
*   **Drop the weight slightly:** Give yourself room to hit a full, clean range of motion on all 10 reps without cutting corners on the way up or down.
*   **Pause at the ends:** Add a deliberate pause at full extension and full contraction to lock in the proper path.
*   **Target a clean set:** Aim to beat your 6 clean reps and push that number closer to a full set of 10.

---

## Exercise: Push-up — clean session

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
### Progress Tracking
Huge step up today! You nailed a clean sweep with 10 out of 10 correct reps, pushing your overall score up to 91 compared to 84 in your previous session on September 20. Even better, both of the old issues—hip sag and partial range of motion—completely vanished from your set. You kept your midsection locked and worked through the full range from top to bottom on every single rep. 

---

### Next Session Plan
1. **Hold the standard:** Your core tension and depth were spot-on today. Treat the start of your next push-up session exactly the same way—lock your spine and lower body rigid from rep one.
2. **Keep the rhythm:** Maintain the same steady, deliberate pace you used today rather than rushing through the later reps, ensuring every single push-up matches the quality of your best ones.

### WITHOUT RAG
### Progress Tracking
Huge step up from yesterday. You went from 8 correct reps up to a clean sweep of 10 out of 10, bumping your overall score from 84 to 91. More importantly, those old issues you were dealing with—hip sag and cutting your range of motion short—are completely gone. You locked in your form and executed the whole set cleanly. 

### Next Session Plan
1. **Hold the standard:** Your next workout's main job is simply replicating this exact form. Do not chase extra reps or speed if it means your hips start dropping or your chest stops touching the floor.
2. **Keep the rhythm steady:** Take a controlled descent on every single rep, just like you did today, to make sure you earn every inch of that full range of motion.

---


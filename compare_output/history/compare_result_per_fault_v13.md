# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions_per_fault.json` |
| query mode | **taxonomy** — `error_type` resolved through `error_taxonomy.py` |
| collection | `kb_gemini_curated_v5` |
| LLM | `gemini-3.5-flash-lite` @ temperature 0.7 |
| no-RAG side | run |
| samples per session | 1 |
| retrieval gates | CANDIDATE_K=12, MAX_PER_KIND={'mistake': 3, 'finding': 2, 'principle': 2, 'consequence': 2}, ABS_DISTANCE_CAP={'mistake': 0.4, 'finding': 0.4, 'principle': 0.4, 'consequence': 0.4}, RELATIVE_MARGIN=0.03, NEAR_DUP_JACCARD=0.72, TAG_MODE=prefer, KIND_POOL=split, QUERIES=profile, HYBRID=False, RERANK=False |

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
| Butt wink | Lumbar flexion (butt wink): posterior pelvic tilt and rounding of the lower back at the bottom of the squat (+why/fix) | 0.032 / 3* | 0.156 / 1* | 0.111 / 2* | 0.116 / 2* |

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

[mistake | re: Butt wink | source: TheBackSquatAProposedAssessment]
Losing the neutral curvature of the lumbar spine during the squat is a common deficit.

[consequence | re: Butt wink | source: TheBackSquatAProposedAssessment]
Squatting with the spine in a flexed position increases the risk of disc herniation as a result of excessive stress placed on intervertebral discs.

[finding | re: Butt wink | source: TheBackSquatAProposedAssessment]
If the athlete flexes at the spine before 120 degrees of hip flexion when squatting, they may have restriction in the posterior fibers of the iliotibial band or lack of lumbar control.

[principle | re: Butt wink | source: blog.nasm.org/newletter/squat-form]
Maintain a neutral low back position with a slight lordosis throughout the squat movement.
```

### WITH RAG
Good session today. Let's look at how you stacked up against your last workout.

### Progress Tracking
You pushed your overall score up to 76 (from 71) and nailed 6 clean reps out of 10, beating your previous count of 4. Even better, you completely cleared knee valgus from your movement pattern compared to last time. You've only got one fault left to iron out, and it's showing up specifically on the way down as fatigue creeps in.

### Error Breakdown

*   **What it is, in plain words:** As you drop into the bottom of reps 4, 6, 8, and 9, your tailbone tucks under and your lower back rounds instead of staying locked in its natural slight arch.
*   **Why it matters:** Forcing your hips down too deep without letting your knees track outward and opening your stance enough forces your pelvis to roll under and rounds your spine. That puts excessive stress on your intervertebral discs, spiking your risk of a disc herniation as the weight gets heavier.
*   **How to fix it:** 
    *   (a) Keep your chest proud and actively think about maintaining the natural curve in your lower back from the second you start your descent.
    *   (b) Turn your stance out slightly wider and let your knees push further apart as you descend to give your hips the room they need.
    *   (c) Practice bodyweight box squats to a height just above where your pelvis typically tucks, so you learn to reverse the movement before your lower back rounds.
    *   (d) Watch your side-profile video on your phone to check that your lower back maintains its slight inward curve all the way through the bottom of the movement.

### Next Session Plan
1. **Clear the last fault:** Focus entirely on stopping your descent the moment you feel your tailbone tuck under, even if it means cutting depth slightly short on those later reps.
2. **Watch the fatigue window:** Reps 4, 6, 8, and 9 all caught you slipping as you got tired—try taking an extra 30 seconds of rest between sets to keep your form dialed in from start to finish.

### WITHOUT RAG
### Progress Tracking
Great movement on your squats today! Your overall score bumped up from 71 to 76, and you nailed 6 correct reps compared to just 4 in your previous session. You also completely cleared knee valgus (your knees caving inward) off your list—that's a huge win. The only fault showing up now is a lower back tuck on the way down, which happened on reps 4, 6, 8, and 9. Let's lock that down so you can pull a clean set next time.

***

### Error Breakdown: Butt wink

* **What it is, in plain words:** As you sink down into the bottom of the squat, your lower back rounds under and your tailbone tucks forward underneath you.
* **Why it matters:** Your lower back and hips take the brunt of the shift instead of your glutes and quads carrying the load evenly. That means you lose your tight brace just when you need it most, draining power out of the bottom of the lift and leaving your lower back aching and fatigued by the end of your set.
* **How to fix it:** 
  (a) Think about proudly showing off the logo on your shirt to the wall in front of you as you descend.
  (b) Cut your depth just an inch or two short of rock-bottom where your pelvis starts to tuck.
  (c) Practice box squats to a height that lets you hit the target while keeping your lower back locked in its natural arch.
  (d) Set your phone up side-on and watch to see if your belt line stays level at the bottom or if it drops and rolls under.
  *Note on rep detail:* Notice how this only popped up on the later half of the set (reps 4, 6, 8, and 9) right as fatigue set in. Keep a close eye on your form as you get tired, and don't fight for a rep if your lower back starts folding.

***

### Next Session Plan
1. **Mind the fatigue:** When you hit reps 4 and up, actively focus on keeping your chest up and your lower back arched before you even start the descent.
2. **Watch the depth:** Stop your descent an inch higher if you feel your tailbone start to tuck under. Build strength at that safe depth first before chasing a deeper squat.
3. **Film a mid-set check:** Prop your phone up for a side-angle video on your working sets to see if you can keep all 10 reps looking as clean as your first three.

---

## Exercise: Squat — Knee valgus

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Knee valgus | Knee valgus: knees caving inward (medial knee displacement) during the squat (+why/fix) | 0.034 / 3* | 0.045 / 2* | 0.091 / 2* | 0.090 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Knee valgus | source: Altered_Knee_and_Ankle_Kinemat]
Allowing the knees to cave inward (medial knee displacement) during the squat.

[finding | re: Knee valgus | source: TheBackSquatAProposedAssessment]
Knee valgus is identified when the medial aspect of either knee passes the medial malleolus from the anterior perspective during any phase of the squat.

[principle | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
Avoiding medial knee displacement ensures that the rectus femoris remains active during the descent into peak knee flexion.

[consequence | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
A poorly performed squat with increased knee valgus may expose the lower extremity joints to excessive torques.

[mistake | re: Knee valgus | source: Physiotherapy Res Intl - 2015 - Jaberzadeh - The Effect of Altering Knee Position and Squat Depth on VMO   VL EMG Ratio]
Allowing the knees to cave inward into a valgus position during the squat.

[mistake | re: Knee valgus | source: www.nasm.org/resource-center/blog/training/biomechanics-of-the-squat]
Knees caving in (knee valgus) during the squat, which is commonly associated with overactive adductors, overactive tensor fasciae latae (TFL), and underactive gluteus medius and gluteus maximus.

[principle | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
Maintain proper medio-lateral alignment of the knees and hips throughout the squat cycle to avoid altered muscle activation patterns.

[consequence | re: Knee valgus | source: blog.nasm.org/newletter/diving-deeper-squat-common-misconceptions]
Limitations in adductor extensibility during the deep phase of a squat cause valgus knee collapse.

[finding | re: Knee valgus | source: Altered_Knee_and_Ankle_Kinemat]
The medial-knee displacement observed during the overhead squat was corrected when a 2-inch (5.08-cm) lift was placed under the heel.
```

### WITH RAG
### Progress Tracking
Let's look at how today's squat session stacked up against yesterday's. Your overall score dipped slightly from 82 down to 78, and your correct rep count dropped from 8 clean reps out of 10 yesterday to 6 clean reps today. The same persistent issue—Knee valgus—is still showing up, meaning your knees are caving inward. While you started strong with clean movement on reps 1 and 2, this fault crept in during the second half of the set, specifically hitting on reps 3, 5, 8, and 10. 

### Error Breakdown: Knee valgus

*   **What it is, in plain words:** Your knees are dropping and caving inward toward each other instead of tracking straight out over your toes as you push back up. 
*   **Why it matters:** When your knees collapse inward, your lower-body joints have to absorb extra twisting and turning forces they aren't meant to handle. For you, this means you miss out on getting full work out of your main thigh muscle (the rectus femoris), and it exposes your hips and knees to excessive stress that builds up into joint aches or pain over time.
*   **How to fix it:** 
    *   (a) *Cue:* Think about actively driving your knees wide apart as you push yourself back up to standing.
    *   (b) *Setup:* Try placing a 2-inch (5.08-cm) lift under your heels before you start your next set to help keep your knees tracking properly.
    *   (c) *Drill:* Practice lighter bodyweight squats focusing entirely on keeping your knees glued in line with your toes on the way up.
    *   (d) *Self-check:* Watch yourself in the mirror or record a side-front angle video to confirm your knees stay tracking directly over your middle toes as you stand up.
*   **Use the rep detail:** Notice how this fault only showed up on the ascending (pushing up) phase of reps 3, 5, 8, and 10—right when fatigue started settling into the set. Fight to keep your knees pushed out even harder as you drive out of the bottom.

### Next Session Plan
1. **Focus on knee tracking early:** Keep your mental cue locked on pushing your knees outward from the very first rep so you don't let fatigue dictate your form later in the set.
2. **Use the heel lift:** Set up with a 2-inch (5.08-cm) lift under your heels for your working sets to help iron out the knee collapse.
3. **Cut the set short if needed:** If your form starts breaking down with caving knees on the later reps just like it did on reps 8 and 10, rack the bar a rep early to protect the quality of your movement.

### WITHOUT RAG
### Progress Tracking
Let’s look at how today stacked up against your session on September 20th. Your overall score dipped slightly from an 82 down to 78, and your correct reps dropped from 8 out of 10 to 6 out of 10. The good news is that "Knee valgus" is still your only recurring issue—you didn't pick up any new form errors. However, that knee caving in is creeping up on you as fatigue sets in, appearing on reps 3, 5, 8, and 10, specifically on the way back up. 

***

### Error Breakdown

- **What it is, in plain words:** Your knees are caving inward toward each other instead of tracking straight out in line with your toes, particularly on the push back up out of the bottom of the squat.
- **Why it matters:** When your knees drop inward, extra stress gets dumped into your knee joints and inner thighs while your glutes check out of the movement. You will feel this as a wobbly, unstable ascent and an achy sensation around the inside or front of your knees, which eats away at your lifting power and risks joint strain as you add more weight to the bar.
- **How to fix it:** 
  - (a) Cue: Think about actively screwing your feet into the floor and driving your knees wide as you stand up.
  - (b) Setup change: Take a slightly narrower stance or point your toes out a degree or two more to give your hips better leverage.
  - (c) Drill: Loop a light resistance band just around your knees during your warm-up bodyweight squats to force your outer hips to stay active.
  - (d) Self-check: Watch your phone video from the side and front to see if your kneecaps track directly over your second toe from bottom to top without wobbling inward.

***

### Next Session Plan
1. **Pace your reps:** Don't rush out of the bottom. Take a deliberate, controlled pause at the lowest point of the squat to lock in your knee position before you drive up.
2. **Watch the fatigue curve:** Since your knees started buckling on reps 3, 5, 8, and 10, cut your working sets slightly short if you feel your form slipping, or drop the weight by 5-10% to keep every single rep clean.

---

## Exercise: Squat — Partial squat

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Partial squat | Squatting too shallow, thighs not reaching parallel: partial or quarter squat depth (+why/fix) | 0.061 / 3* | 0.169 / 2* | 0.124 / 2* | 0.161 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting to a depth where the top of the thighs do not reach parallel to the ground.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Failing to reach parallel squat depth.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting too shallow, where the athlete does not achieve a depth of thighs at least parallel to the ground.

[consequence | re: Partial squat | source: www.healthline.com/health/fitness/deep-squat]
Failing to reach deep squat depth prevents the backs of your thighs from contacting the backs of your calves, which increases the compressive load on your knee joint and may raise the risk of injury.

[consequence | re: Partial squat | source: TheBackSquatAProposedAssessment]
Without squatting to the proper depth, the hamstrings and gluteus muscular complex may not be adequately challenged.

[principle | re: Partial squat | source: TheBackSquatAProposedAssessment]
At the proper depth, the femurs are slightly past parallel to the ground, hips are back, tibias are positioned vertical, and feet are entirely on the ground.

[principle | re: Partial squat | source: ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN]
Adjust stance width and toe-out angles to find the combination that allows the athlete to achieve the best squatting depth with the least compensations.

[finding | re: Partial squat | source: TheBackSquatAProposedAssessment]
There is no scientific evidence indicating that squatting below parallel increases the potential for injury to the cruciate and collateral ligaments or menisci in the knee during extreme flexion.

[finding | re: Partial squat | source: www.healthline.com/health/fitness/deep-squat]
In a standard squat, you only bend down until your thighs are parallel with the ground, with knees bent at around a 90-degree angle.
```

### WITH RAG
### Progress Tracking
Great job stepping it up since yesterday. Your overall score ticked up from 74 to 80, and you nailed 6 correct reps compared to just 5 in your previous session. Even better, you completely wiped out the butt wink issue from last time. The only thing holding you back today is depth on the back half of your set.

### Error Breakdown

*   **What it is, in plain words:** You are cutting your depth short on reps 7 through 10—stalling out on the way down instead of dropping your thighs until they are parallel to the floor.
*   **Why it matters:** When you don't hit proper depth, your glutes and hamstrings don't pull their weight, leaving those muscles underworked while cranking up the compressive load on your knees. That means you miss out on full muscle growth, and as the weight creeps up, it starts putting your knee joints under avoidable stress.
*   **How to fix it:** 
    *   (a) Cue: Think about sending your hips back and down to open up your range of motion before you reverse direction.
    *   (b) Setup: Play with your stance width and the angle of your toes so you can settle into the bottom of the squat comfortably without compensations.
    *   (c) Drill: Practice bodyweight box squats to a low target to teach your hips what hitting parallel actually feels like.
    *   (d) Self-check: Set your phone up for a side-profile video to verify that your thighs are dropping parallel to the floor before you drive back up.

### Next Session Plan
*   Keep the clean movement from your first six reps locked in, and pay extra attention to depth as fatigue sets in on the back half of the set.
*   If you notice your depth starting to shallow out around rep 7, cut the set short there rather than grinding through incomplete reps.

### WITHOUT RAG
### Progress Tracking
Good work today—you moved your overall score up from 74 to 80, and banked 6 correct reps compared to 5 in your previous session. Even better, you completely cleared "Butt wink" off your error list from last time. The main issue now is that fatigue is creeping in late, causing your depth to cut short on the last four reps (reps 7 through 10). Let's clean that up so you can finish strong.

---

### Error Breakdown

*   **What it is, in plain words:** You are cutting your depth short instead of sinking all the way down into the bottom of the squat, and this is happening specifically on the way down during reps 7, 8, 9, and 10 as you get tired.
*   **Why it matters:** When you stop high, your quads and glutes don't get taken through their full range of motion, which means you miss out on the muscle growth you're working for. It also robs you of the bounce out of the bottom hole, costing you strength and leaving you with reps you can't fully trust as the weight goes up.
*   **How to fix it:** 
    *   (a) Cue: Think about actively pulling yourself down into the bottom position rather than just waiting for gravity to stop you.
    *   (b) Setup change: Set a box or a safety pin at the correct height so you have a physical target to touch every single rep.
    *   (c) Drill: Drop the load down by about 10-15% and pause for a full two seconds at the very bottom of every rep to kill any momentum and build strength where you're currently falling short.
    *   (d) Self-check: Set your phone up to record from the side so you can verify on video that your hip crease drops below the top of your kneecap before you start back up.

---

### Next Session Plan
1. **Drop the weight slightly:** Take 10% off the bar so you have enough in the tank to hit full depth on all 10 reps without fatigue making you stall early.
2. **Add a pause:** Incorporate a 2-second pause at the bottom of your first two work sets to lock in your depth perception.
3. **Film your working sets:** Review your video between sets to ensure reps 7 through 10 look just as deep as reps 1 through 3.

---

## Exercise: Push-up — Hip sag

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Hip sag | Allowing the hips to sag during the push-up (+why/fix) | 0.048 / 2* | 0.179 / 2 | 0.129 / 2* | 0.143 / 1* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Hip sag | source: blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement]
Allowing the low back to arch or sag during the push-up as fatigue sets in.

[consequence | re: Hip sag | source: blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement]
Allowing the low back to arch or sag during a push-up decreases engagement of the deeper core stabilizers, increases involvement of the lumbar erectors, and increases stress on the vertebral discs.

[principle | re: Hip sag | source: The_Effect_of_Position_on_the_Percentage_of_Body.992962]
Maintain a rigid spine and lower-extremity segments throughout the push-up movement.

[mistake | re: Hip sag | source: www.nasm.org/resource-center/exercise-library/push-up]
Allowing the hips to sag during the movement.

[finding | re: Hip sag | source: The_Biomechanics_of_the_Push_up]
Compressive spinal loading on the L4/L5 joint reaches 1,838 N during a standard push-up.

[finding | re: Hip sag | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
The push-up cycle was standardized using a metronome to fix the repetition rate at 2 seconds, starting from the top position.

[consequence | re: Hip sag | source: www.nasm.org/resource-center/exercise-library/push-up]
Allowing the hips to sag indicates core disengagement and reduces exercise effectiveness.
```

### WITH RAG
### Progress Tracking
You pushed your overall score up from 72 to 77 and landed 6 clean reps today compared to 5 in your previous session on 2026-09-20. Even better, you completely kicked one of your old habits: "Partial range of motion" didn't show up once. The only fault hanging around is "Hip sag," and looking at the breakdown, it's strictly a fatigue issue creeping in on reps 6, 7, 9, and 10 as you started getting tired on the way down and back up.

***

### Error Breakdown

*   **What it is, in plain words:** On reps 6, 7, 9, and 10, your hips and lower back started dropping toward the floor instead of your whole body moving as a single solid plank—this happened right as you were lowering yourself or pushing back up.
*   **Why it matters:** When your midsection gives out, your deep core muscles switch off, leaving your lower back to overwork and dumping 1,838 N of compressive force onto your L4/L5 spinal joints. That translates to a dull, nagging ache in your lower back right after your set, cheapens the exercise so your chest and arms do less actual work, and sets you up for injury when fatigue settles in.
*   **How to fix it:** 
    *   (a) *Cue:* Squeeze your glutes hard and brace your stomach like someone is about to poke you in the ribs before you even start bending your elbows.
    *   (b) *Setup change:* Drop your knees to the floor for your sets once your form starts to break, rather than grinding out ugly reps with sagging hips.
    *   (c) *Drill:* Practice the plank hold on your elbows for 30 seconds to recalibrate what a straight line from your shoulders to your heels actually feels like.
    *   (d) *Self-check:* If you glance in a mirror or watch your phone video and notice a dip in your lower back as you bend your arms, your core has checked out.
*   **Use the rep detail:** Notice how your first five reps were totally clean and the sagging only started on rep 6. That's your fatigue window right there—your muscles are failing you in the second half of the set.

***

### Next Session Plan
1. **Cap your clean sets:** Stop your working sets one rep *before* your hips start to sag—on today's evidence, that means cutting the set at 5 reps to protect your form.
2. **Kneel when tired:** If you want to push past 5 reps, transition to a knee push-up variation immediately when fatigue hits, keeping your spine locked in place.
3. **Rest longer between sets:** Give your core stabilizers a full, proper recovery break so they don't fatigue prematurely on your next round.

### WITHOUT RAG
### Progress Tracking
Good job today—you moved your overall score up from 72 to 77, and you banked 6 clean reps compared to just 5 in your previous session. Even better, you completely wiped out "Partial range of motion" from your last workout, proving you can hit full depth when you focus. The main thing holding you back now is "Hip sag," which crept in on 4 reps (specifically reps 6, 7, 9, and 10). Notice how it didn't show up until the second half of your set as fatigue set in. Let's look at why that happens and how to lock it down.

***

### Error Breakdown

*   **What it is, in plain words:** Your hips and lower back started dropping toward the floor while your upper body kept moving, making your body look like a sagging hammock instead of a rigid plank.
*   **Why it matters:** When your midsection gives out, your lower back takes the extra strain instead of your core holding everything stable. That means you'll start feeling a dull ache in your lower back during or right after your sets, you lose the power transfer from your legs and torso, and you risk straining your spine as you try to grind through fatigue.
*   **How to fix it:** 
    *   (a) Think about squeezing your glutes hard and pulling your belly button in toward your spine like someone is about to poke you in the stomach.
    *   (b) Set your feet slightly wider apart to create a more stable base of support before you even start the first rep.
    *   (c) Practice plank holds on your elbows to build the core endurance needed to keep your torso rigid under load.
    *   (d) Glance at a mirror sideways or prop your phone up to record a side-view video—if your belt buckle drops lower than your shoulders on the way down, you'll see it instantly.
    *   (Use the rep detail): Since this fatigue-driven error only hit you on reps 6, 7, 9, and 10, cut your sets off one rep *before* your hips start dropping so you only practice perfect form.

***

### Next Session Plan
1. **Stop the set early:** Cut your sets off the moment your form starts to slip—don't grind out ugly reps that train your lower back to sag.
2. **Brace harder:** Actively squeeze your glutes and brace your abs from the very first rep of every set to keep your torso locked like a solid plank.
3. **Check your video:** Record one of your working sets from the side to make sure your hips stay up through the final reps.

---

## Exercise: Push-up — Partial range of motion

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Partial range of motion | Not lowering deep enough: incomplete elbow flexion, failing to reach 90 degrees during the push-up (+why/fix) | 0.079 / 2* | 0.186 / 2* | 0.154 / 2* | 0.139 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Partial range of motion | source: 10-week suspension and traditional push-up training]
Failing to acquire the correct depth of 90 degrees of elbow flexion.

[principle | re: Partial range of motion | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
Achieving deeper elbow flexion during push-ups increases the mechanical load and muscular demand on the triceps.

[consequence | re: Partial range of motion | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
Restricting the range of motion during narrow-width push-ups develops and concentrates the load on the elbow joint.

[principle | re: Partial range of motion | source: 10-week suspension and traditional push-up training]
Ensure the correct depth of 90 degrees of elbow flexion is acquired during each repetition.

[mistake | re: Partial range of motion | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
Using a narrow-width hand position can restrict the elbow joint's range of motion during the push-up.

[finding | re: Partial range of motion | source: 10-week suspension and traditional push-up training]
The study protocol monitored body form and required repetitions to be repeated if the correct depth of 90 degrees was not acquired.

[consequence | re: Partial range of motion | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
Failing to reach deep elbow flexion reduces the mechanical load and contractile demand placed on the triceps muscle.

[finding | re: Partial range of motion | source: www.nasm.org/resource-center/exercise-library/push-up]
Descend until your chest nearly touches the floor or your elbows bend to approximately 90 degrees.
```

### WITH RAG
### Progress Tracking

Compared to your last session on September 20th, your correct rep count dipped slightly from 7 down to 6, and your overall score moved from 80 to 78. You are still dealing with the exact same issue we talked about last time—partial range of motion—which showed up on reps 2, 5, 8, and 10 on the way down. The good news is your clean reps (1, 3, 4, 6, 7, and 9) looked sharp, meaning you definitely have the strength to do these right; you just need to hold that standard for every single rep instead of cutting the bottom short when fatigue creeps in.

### Error Breakdown

*   **What it is, in plain words:** You are cutting your descent short on the way down instead of lowering yourself all the way until your elbows hit a 90-degree bend.
*   **Why it matters:** When you don't bend your elbows deep enough, your triceps don't have to work nearly as hard, cheating you out of the actual muscle growth you came for. That means you are doing the hard work of moving your bodyweight but getting less payoff for your triceps at the bottom of the movement.
*   **How to fix it:** 
    *   (a) *Cue:* Tell yourself "chest to the floor" as you start heading down.
    *   (b) *Setup change:* Make sure your hands aren't jammed too close together, as a narrow grip can naturally choke off how far you're able to bend your elbows. 
    *   (c) *Drill:* Drop your knees to the floor for your warm-up sets to groove that full depth without straining.
    *   (d) *Self-check:* Glance at your phone video or a mirror to confirm your upper arms dip low enough to form a right angle at the elbow before you push back up.

### Next Session Plan

1. **Slow down the descent:** Take an extra half-second on the way down for reps 8 through 10 so fatigue doesn't trick you into cutting the depth short.
2. **Set a depth standard:** Treat any rep where your elbows don't hit a 90-degree bend as a practice rep that doesn't count toward your working set.

### WITHOUT RAG
### Progress Tracking
Let's look at how you stacked up against your last session on September 20th. Your overall score dipped slightly from 80 to 78, and your correct reps went from 7 down to 6 out of 10. The good news is that the old error you brought over—partial range of motion—is still the only thing holding you back. It showed up on reps 2, 5, 8, and 10, meaning fatigue in the latter half of the set is causing you to cut your reps short on the way down. Let's fix that dip and get those numbers back up next time.

### Error Breakdown: Partial range of motion

* What it is, in plain words: You aren't lowering your chest far enough toward the floor on reps 2, 5, 8, and 10, cutting the movement short just as you start descending.
* Why it matters: Shortchanging your depth means your chest and triceps miss out on the full stretch and workload they need to grow stronger, leaving gains on the table for the exact same amount of effort.
* How to fix it: 
  (a) Think about bringing your chest all the way down to a fixed target point on every single rep.
  (b) Move your hands slightly wider or narrow your stance to give yourself a more stable platform before you start pressing.
  (c) Practice incline push-ups with your hands elevated on a sturdy bench to groove the full movement pattern without straining.
  (d) Check your phone video to make sure your chest clearly touches or nears the floor on every descent.

### Next Session Plan
1. Keep a close eye on your descent depth, especially as you get tired in the later reps of your set (reps 8 through 10).
2. Take a slightly longer rest—around 60 to 90 seconds—between your sets so fatigue doesn't force you to cut your range of motion short early.

---

## Exercise: Lunge — Excessive forward trunk lean

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Excessive forward trunk lean | Leaning the torso forward, excessive trunk lean during the lunge (+why/fix) | 0.072 / 3* | 0.142 / 2* | 0.122 / 2* | 0.112 / 2* |

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

[consequence | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Leaning the trunk forward during a lunge increases the range of hip and trunk flexion, which shifts the body's center of mass forward and increases weight bearing on the lead lower extremity.

[consequence | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Leaning the trunk forward during a lunge shifts the muscular demand, increasing the load on the hip extensors and ankle plantar flexors while reducing the load on the knee extensors.

[principle | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Performing a forward lunge with the trunk leaned forward increases the hip extensor impulse and the recruitment of the hip extensors, specifically the gluteus maximus and biceps femoris.

[finding | re: Excessive forward trunk lean | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Anterior movement of the upper torso and lower leg significantly increases the load exerted on the knee joint of the front leg.

[finding | re: Excessive forward trunk lean | source: Altered movement strategy during functional movement after an ACL injury, despite ACL reconstruction]
In a study of 12 ACL-injured patients and 15 controls, the standardized forward lunge protocol required flexing the front knee to approximately 90 degrees while keeping the upper body perpendicular to the ground.
```

### WITH RAG
### Progress Tracking
Good work today—you're moving in the right direction. Your overall score ticked up from 70 to 78, and you nailed 6 correct reps compared to just 4 in your previous session. Even better, you completely cleared the "Shallow lunge" fault from last time. You've only got one error left to clean up.

### Error Breakdown: Excessive forward trunk lean

*   **What it is, in plain words:** You're letting your upper body pitch forward toward your front knee as you move, rather than keeping your chest tall and your torso stacked vertically over your hips.
*   **Why it matters:** This leans your center of mass forward, which dumps extra loading onto your front knee and shifts how the work gets distributed across your lower body. As you keep doing this, you'll feel more of the stress pooling into the front knee joint and your calves, which robs your quads of the work they're supposed to be doing and can leave your knees aching by the end of a heavier session.
*   **How to fix it:** 
    *   (a) *Cue:* Think about keeping your chest proudly open and staring straight ahead on every rep, imagining a string pulling the crown of your head straight up to the ceiling.
    *   (b) *Setup change:* Slow down the tempo on your way down, taking a full two seconds to descend so you have time to catch your balance before your torso starts tipping.
    *   (c) *Drill:* Drop the weight entirely and practice bodyweight lunges with your hands crossed over your opposite shoulders to force your upper back to stay locked in.
    *   (d) *Self-check:* Glance sideways in a mirror or prop your phone up—if your shoulders finish ahead of your hips at the bottom, your chest has dropped too far.
*   **Use the rep detail:** This error popped up on reps 1, 3, 5, and 7. Notice how it hits early and mid-set during both the descending and ascending phases as you settle into the movement, meaning you need to stay dialed in on your posture right from step one rather than letting your form slip as you get moving.

### Next Session Plan
1.  **Lead with posture:** Spend your warm-up reps focusing exclusively on keeping your chest tall before you add any weight back to the bar or dumbbells.
2.  **Control the descent:** Use a slower, two-second drop on every single rep to stop your torso from taking over the movement.
3.  **Hold the standard:** Keep that newfound depth you found today locked in, and focus entirely on stacking your ribs over your hips to wipe out that last lingering lean.

### WITHOUT RAG
Error occurred during generation: [WinError 10060] A connection attempt failed because the connected party did not properly respond after a period of time, or established connection failed because connected host has failed to respond

---

## Exercise: Lunge — Shallow lunge

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Shallow lunge | Shallow lunge: step too short, insufficient front knee flexion, front knee not reaching 90 degrees (+why/fix) | 0.059 / 3* | 0.110 / 2* | 0.120 / 2* | 0.127 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Shallow lunge | source: mxn167Sp24]
Using an insufficient step length during the lunge.

[mistake | re: Shallow lunge | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Performing a shallow lunge where the front knee flexion angle only reaches 80 degrees, which increases knee joint displacement and extensor moments.

[finding | re: Shallow lunge | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
The holding phase of a forward lunge requires participants to maintain body position at approximately 90 degrees of front knee flexion.

[mistake | re: Shallow lunge | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Performing a shallow lunge where the front knee only reaches an 80-degree flexion angle rather than 90 or 100 degrees.

[consequence | re: Shallow lunge | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
A shallower lunge of 80 degrees of knee flexion generates a higher knee extension moment, which increases the mechanical demand on the knee extensor musculature.

[principle | re: Shallow lunge | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
During the descending phase of the lunge, the front knee should be flexed to approximately 90 degrees.

[principle | re: Shallow lunge | source: mxn167Sp24]
Using a longer step length during a lunge helps minimize anterior tibial translation over the toes and reduces joint forces.

[finding | re: Shallow lunge | source: mxn167Sp24]
A lunge with a shorter step length results in joint forces almost two times higher than a lunge with a longer step.

[consequence | re: Shallow lunge | source: Influence of the Exhaustion of the Gluteus Medius on the Knee Adduction Moment During Forward Lunge Exercise]
Using a shorter step length (shallow lunge) limits the recruitment and activation of the gluteus medius muscle.
```

### WITH RAG
### Progress Tracking
You pushed your score up from 75 to 77 and nailed 6 correct reps today compared to 5 in your last session, dropping your mistakes down from 5 to 4. Even better, you completely cleared "Insufficient back knee flexion"—that fault is gone from your list. The remaining issue, "Shallow lunge," popped up on the way down during reps 2, 4, 6, and 9. Let's lock that in so you can clean the slate next time.

***

### Error Breakdown: Shallow lunge

* **What it is, in plain words:** You are cutting your step short and failing to sink deep enough into the bottom of the movement, stopping around an 80-degree bend in your front knee instead of hitting your full range.
* **Why it matters:** Sinking only partway ramps up the physical demands on your quads while failing to fully recruit your glutes, leading to joint forces almost two times higher than a full-depth stride. That extra stress can catch up to your knees as you add more weight to your sets.
* **How to fix it:** 
  (a) Think about reaching out further and driving your hips straight down as you descend.
  (b) Take a slightly longer step forward when you set up your stance.
  (c) Practise a bodyweight pause lunge, holding the bottom position for a two-count to get used to the depth without heavy loads.
  (d) Check your phone video to confirm your front thigh is parallel to the floor at the bottom of the rep.

***

### Next Session Plan
1. **Take a bigger initial stride:** Focus on stepping out further on every single rep to open up your range of motion right from the start.
2. **Pause at the bottom:** Add a one-second pause on your reps to build comfort at the correct depth and break the habit of cutting the descent short.
3. **Drop the error count:** Target zero shallow reps by keeping your front knee bent to roughly 90 degrees on every drop.

### WITHOUT RAG
### Progress Tracking
Good work today. You pulled your overall score up slightly from 75 to 77, and you bumped your clean reps from 5 up to 6 out of 10. Even better, you completely cleared out the "Insufficient back knee flexion" fault that showed up in your last session. That means you are bending your back leg properly now. You still have one lingering issue to clean up, so let's dial that in.

***

### Error Breakdown: Shallow lunge

* **What it is, in plain words:** You are cutting your depth short on the way down, stopping well before your back knee gets close to the floor. This happened on reps 2, 4, 6, and 9 during the descending phase.
* **Why it matters:** When you don't drop your hips fully, your front quad and glute miss out on the deep stretch and heavy load they need to grow stronger. That translates to wasted effort and fewer solid, trustworthy reps for your lower body.
* **How to fix it:** 
  * (a) Think about kissing your back knee softly to the floor on every single rep.
  * (b) Shorten your stride slightly if your stance feels too wide to control, or slow down your descent so you don't bail out early.
  * (c) Try bodyweight lunges with a soft pad or yoga block placed directly under your back knee so you have a physical target to touch.
  * (d) Glance sideways in the mirror or film a side-profile video to check that your back knee actually hovers just an inch above the floor at the bottom.

***

### Next Session Plan
1. **Target the bottom:** Keep a mental note on every single rep to drop your hips all the way down instead of cutting the descent short.
2. **Control the pace:** Slow down the lowering phase of your reps—especially on the later reps like 6 and 9—so you don't rush and lose your depth.
3. **Use a target:** Place a small rolled-up mat or towel under your back knee for your warm-up sets to guarantee you hit full range of motion.

---

## Exercise: Lunge — Insufficient back knee flexion

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Insufficient back knee flexion | Insufficient back knee flexion: rear knee not lowering toward the floor during the lunge (+why/fix) | 0.060 / 1* | 0.108 / 2* | 0.103 / 2 | 0.106 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Insufficient back knee flexion | source: Influence of the Exhaustion of the Gluteus Medius on the Knee Adduction Moment During Forward Lunge Exercise]
Loss of full range of motion during the lunge, such as failing to lower the rear knee to ankle height.

[consequence | re: Insufficient back knee flexion | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
A shallower lunge of 80 degrees of knee flexion generates a higher knee extension moment, which increases the mechanical demand on the knee extensor musculature.

[principle | re: Insufficient back knee flexion | source: KritzCroninHume2009BodyweightlungeSCJ]
The back knee should be flexed during the lunge.

[finding | re: Insufficient back knee flexion | source: lunge_knowledge]
In the study's specific lunge protocol, the forward knee was flexed to 45 degrees while the rear knee remained in full extension with both heels in contact with the floor.

[consequence | re: Insufficient back knee flexion | source: ptq-4.4.9-the-undervalued-lunge]
Lunges performed without optimal technique can create unnecessary joint stress that can limit performance, exacerbate pre-existing injuries, and potentially cause pain.

[principle | re: Insufficient back knee flexion | source: lunge_knowledge]
Both the anterior and posterior legs should achieve a knee joint range of motion of 0 to 90 degrees during the lunge.

[finding | re: Insufficient back knee flexion | source: blog.nasm.org/training-benefits/lunge-effective-lower-body-training-exercise]
An upright trunk tends to create what is often called a 90/90 lunge where both knees at the bottom of the move are 90° angles.
```

### WITH RAG
### Progress Tracking
You landed 6 correct reps out of 10 today, giving you an overall score of 78. Compared to your last session on 2026-09-20, where you hit 7 correct reps and scored an 81, you slipped back slightly by one correct rep and 3 points on the score. That old familiar fault—Insufficient back knee flexion—is still hanging around, showing up on reps 5, 7, 8, and 10, specifically as you step down into the bottom of the movement.

---

### Error Breakdown

* What it is, in plain words: You are cutting your step short on the way down, leaving your back leg too straight instead of dropping that rear knee toward the floor.
* Why it matters: Stopping short of an 80-degree bend in your back knee piles extra mechanical demand straight onto your quads, forcing them to handle a higher load than they should. Over the set, that extra stress creates unnecessary joint strain, leaves you feeling gassed prematurely, and can lead to nagging aches that cut your workout short.
* How to fix it: 
  (a) Cue: Think about dropping your back knee straight down toward the ground rather than lunging forward.
  (b) Setup: Slow down your descent on every rep, taking a full two seconds to lower yourself into a position where both knees hit a clear 90-degree angle at the bottom.
  (c) Drill: Drop the added load completely and practice bodyweight split squats, pausing for a full second at the bottom to build awareness of the proper depth.
  (d) Self-check: Glance in the mirror as you step down—your back knee should hover just above the floor, and both legs should form matching 90-degree right angles.

---

### Next Session Plan
1. **Pace the set:** Since this fault creeps in during the second half of your set (hitting you on reps 5, 7, 8, and 10), focus intensely on keeping your tempo controlled as fatigue sets in.
2. **Prioritize depth over speed:** Drop the weight slightly if you need to, and make sure every single rep reaches that full 90/90 position before you push back up.

### WITHOUT RAG
### Progress Tracking
Let's look at how today stacked up against your last session on September 20th. You landed 6 correct reps out of 10 today, giving you an overall score of 78. That's a slight dip from your previous session, where you hit 7 correct reps and scored an 81. The good news? You didn't pick up any brand-new faults today. Your old nemesis—Insufficient back knee flexion—showed up again on reps 5, 7, 8, and 10, creeping in specifically as you step down into the bottom of the movement. 

***

### Error Breakdown

*   **What it is, in plain words:** As you lower yourself down into the lunge, your back leg stays a bit too stiff and straight instead of bending to let your knee drop cleanly toward the floor.
*   **Why it matters:** When your back knee doesn't bend enough on the way down, your front leg has to shoulder almost all the work while your back leg and glutes coast. That means you are cutting your lower-body muscle activation short and fatiguing your front quad way too early, while robbing yourself of the full strength and stability you could be building across both legs.
*   **How to fix it:** 
    *   (a) *Cue:* Think about dropping your back knee straight down toward the floor like you are trying to kiss it to the ground, rather than lunging forward.
    *   (b) *Setup:* Take a slightly shorter stride if you find yourself feeling stretched out, which naturally gives your back leg the room it needs to fold properly.
    *   (c) *Drill:* Practice bodyweight split squats with your back foot elevated on a low bench or step to force that back knee to bend right from the start of the descent.
    *   (d) *Self-check:* Glance in a mirror sideways or catch your set on video—your back shin should be nearly vertical and your back knee should hover just an inch or two above the floor at the bottom.
*   **Use the rep detail:** Notice how this error only appeared in the second half of your set (reps 5, 7, 8, and 10). That tells us fatigue is setting in and your form is leaking as your legs get tired. Next time, either cut the set off at 4 reps before form breaks down, or take an extra breath of rest before starting your sets to keep that back leg honest all the way through.

***

### Next Session Plan
1. **Prioritize the back leg:** Focus on driving that back knee straight down to the floor on every single rep, treating the bottom of the lunge as a drop rather than a slide forward.
2. **Manage your set length:** Stop your sets a rep or two earlier when you feel fatigue creeping in—don't let sloppy reps like 8 and 10 sneak into your working sets.
3. **Check your depth on video:** Film one set from the side so you can verify whether your back knee is actually bending fully before you push back up.

---

## Exercise: Bicep Curl — Elbow flare

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Elbow flare | Allowing the elbows to flare outward or drift forward away from the body during the curl (+why/fix) | 0.046 / 2* | 0.202 / 2 | 0.149 / 1* | 0.184 / 2* |

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

[finding | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Bicep curls should be programmed for hypertrophy using a moderate weight that allows for 8-12 reps.
```

### WITH RAG
### Progress Tracking
Great work today—you bumped your overall score up from 73 to 79 and nailed 6 clean reps compared to just 4 in your last session. Even better, you completely cleared out "Partial range of motion" from your previous session's error list. You only had one issue pop up today, and it didn't even show up until the back half of your set.

---

### Error Breakdown

* **What it is, in plain words:** On reps 6, 8, 9, and 10, your elbows drifted forward and drifted away from your waist as you lifted the weight up.
* **Why it matters:** Because your biceps help stabilize your shoulder joint in addition to bending your elbow, fatigue in that shoulder-stabilizing role makes your elbows sneak forward as you lift. When that happens, your front shoulders and upper back step in to take over the work, stealing tension away from your biceps and cutting down on the muscle-building stimulus you're after.
* **How to fix it:** 
  (a) **Cue:** Keep your upper arms pinned to your sides like they're glued to your ribs as you curl.
  (b) **Setup change:** Lighten the load slightly so you aren't forced to recruit your shoulders to finish the movement.
  (c) **Drill:** Practice your curls standing with your back against a wall, or tuck your elbows against your ribs to block any forward travel.
  (d) **Self-check:** Glance in the mirror to make sure your elbows stay locked by your hips through the entire lift instead of creeping up toward your chest.
* **Use the rep detail:** Notice how this fault only crept in on reps 6, 8, 9, and 10—right as fatigue set in. That tells you your form breaks down as soon as you get tired, so don't push past the point where your elbows start to wander.

---

### Next Session Plan
1. **Drop the weight slightly:** Give yourself enough headroom to keep your elbows locked tight to your ribs for all 8 to 12 reps without needing momentum.
2. **Watch the back half of the set:** Pay extra attention when you hit reps 6 and beyond—that's where your form started leaking today, so lock your focus in early.
3. **Stop before form breaks:** The moment your elbows start drifting forward, end the set rather than grinding out ugly reps.

### WITHOUT RAG
### Progress Tracking

Great work on this session—you are definitely moving in the right direction. Your overall score ticked up to 79 (compared to 73 last time), and you nailed 6 correct reps instead of just 4. Even better, you completely cleared out the partial range of motion issue from your previous workout. You only had one error showing up today: elbow flare, which popped up exclusively on the ascending phase of your later reps (reps 6, 8, 9, and 10) as fatigue started to set in. 

***

### Error Breakdown

* **What it is, in plain words:** As you curled the weight up on reps 6, 8, 9, and 10, your elbows drifted forward and away from your sides instead of staying pinned right at your ribs.
* **Why it matters:** When your elbows wander forward, your shoulders and front delts step in to help lift the weight, taking the load off your biceps. That means less actual muscle growth for the exact same effort, and it leaves your shoulders feeling overworked instead of your arms.
* **How to fix it:** 
  * (a) Think about dragging the weight straight up your torso as if your elbows are glued inside deep pockets.
  * (b) Narrow your grip slightly or drop the weight just a fraction so you aren't fighting to keep your upper arms locked in place.
  * (c) Try doing your curls with your back against a wall to physically block your elbows from creeping forward.
  * (d) Glance in the mirror to check that your upper arms stay completely vertical from the floor to the top of the curl.

***

### Next Session Plan

* **Pin your elbows:** Start your next session by focusing entirely on keeping those upper arms locked to your sides from the very first rep to the last.
* **Call it early when form slips:** Since elbow flare only hit on your final four reps as you got tired, stop your set one rep *before* your form breaks down instead of grinding out messy reps.
* **Drop the weight if needed:** If your elbows start drifting forward anyway, back off the weight slightly so you can finish every rep with strict form.

---

## Exercise: Bicep Curl — Partial range of motion

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Partial range of motion | Failing to achieve complete arm extension at the bottom of the curl and full elbow flexion at the top: partial repetitions with a limited range of motion (+why/fix) | 0.045 / 3* | 0.168 / 2* | 0.120 / 1* | 0.124 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Failing to achieve complete arm extension at the bottom of the curl and instead performing partial repetitions only in the top portion of the range of motion (final ROM, such as 68º–135º or 80º–130º).

[consequence | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Restricting the bicep curl to the top half of the movement (final ROM) reduces the hypertrophic stimulus at longer muscle lengths, resulting in significantly less muscle growth in the distal portion of the biceps brachii.

[mistake | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Failing to reach full extension at the bottom of a curl and training exclusively in the final, shortened range of motion limits muscle growth.

[mistake | re: Partial range of motion | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
Failing to achieve the full range of motion of the elbow joint during each repetition.

[principle | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Ensuring the movement includes the bottom portion of the curl (initial ROM) is critical for targeting the distal region of the biceps brachii.

[principle | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Training the bicep curl at longer muscle lengths, which corresponds to the initial range of motion starting from full elbow extension (0º), optimizes muscle hypertrophy.

[finding | re: Partial range of motion | source: Optimizing Resistance Training Technique to Maximize Muscle Hypertrophy A Narrative Review]
Partial repetitions at shorter-muscle lengths are not as hypertrophic as partial repetitions at longer-muscle lengths.

[finding | re: Partial range of motion | source: Optimizing Resistance Training Technique to Maximize Muscle Hypertrophy A Narrative Review]
A systematic review by Kassiano et al. [26] found that a partial range of motion at long muscle lengths is sufficient to promote optimal muscle growth for the biceps brachii.
```

### WITH RAG
### Progress Tracking
You pushed your overall score up to 79 from 77, and your clean reps climbed from 5 to 6 compared to your last session. Even better, you completely cleared "Elbow flare" off the board—that fault is gone. The one thing holding you back from a fully locked-in set is a shrinking range of motion, which popped up on reps 3, 4, 7, and 10.

### Error Breakdown

* What it is, in plain words: You are cutting your reps short instead of letting your arms straighten out completely at the bottom, or you're failing to get the full movement in as you curl.
* Why it matters: Restricting the movement to the top half of the curl cuts out the stretch at the bottom, which robs you of the muscle growth you should be getting in the lower part of your biceps. You miss out on the best stimulus for size and leave gains on the table for the same amount of effort.
* How to fix it: 
  (a) Focus on actively reaching your hands all the way down to full arm extension before you start pulling back up.
  (b) Take a slightly lighter weight if you need to, which lets you control the full length of the stroke without cutting corners when fatigue sets in.
  (c) Try doing slow, controlled negative reps where you spend three full seconds lowering the weight to a dead straight arm every time.
  (d) Glance in a mirror from the side and check that your elbow completely straightens out at the bottom of every single rep.

### Next Session Plan
* Keep your elbows locked by your sides just like you did to beat that flare fault, holding onto that great setup habit.
* Drop the weight slightly if needed so you can hit a full, complete range of motion on every single rep from one to ten without cutting the bottom short.
* Watch your form on the later reps (like reps 7 and 10) where fatigue usually creeps in and makes you chop the movement down.

### WITHOUT RAG
### Progress Tracking
Good work today. Your overall score ticked up slightly from 77 to 79, and you banked 6 correct reps compared to 5 in your previous session on September 20. Even better, you completely cleared elbow flare out of your movement—that fault is gone. You're left with just one issue to clean up: partial range of motion showed up on 4 reps (reps 3, 4, 7, and 10), hitting you on both the way down and the way up. 

---

### Error Breakdown: Partial range of motion

* What it is, in plain words: You're cutting the movement short instead of fully straightening your arm at the bottom or curling all the way up to squeeze the muscle at the top. 
* Why it matters: When you cut the rep short, your biceps miss out on the full stretch and peak contraction, meaning less muscle growth for the exact same amount of effort. You also end up trusting reps that aren't actually finishing the job, which leaves gains on the table.
* How to fix it: 
  * (a) Cue to think about: "Reach long at the bottom, squeeze hard at the chin."
  * (b) Setup change: Slow down your lifting tempo and drop the weight slightly if you need to so you can control the entire path of the motion without rushing.
  * (c) Drill or lighter regression: Practice dead-stop curls from a seated position, letting the weight come to a complete, dead stop at full arm extension at the bottom of every single rep before you pull again.
  * (d) Self-check: Watch yourself in the mirror and make sure your arm locks out straight like a plank at the bottom before every curl starts.

---

### Next Session Plan
1. **Focus on the full length:** Take two seconds on the way down for every single rep today, making sure your arm is completely straight before you start the next curl.
2. **Drop the weight if needed:** If you find yourself cutting reps short again by rep 7 or 10, drop the load slightly so you can finish the full range of motion cleanly.
3. **Keep the elbows pinned:** Since you successfully beat elbow flare this session, keep that same locked-in elbow position as your baseline for the next workout.

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

Great work out there today! You completely cleared out both errors from your last session—"Hip sag" and "Partial range of motion" are entirely gone. You hit a clean sweep with 10 out of 10 correct reps today, pushing your overall score up to 91 (compared to 84 in your previous session on 2026-09-20). You stayed locked in from the first rep to the last.

### Next Session Plan

1. **Hold the standard:** Keep your body completely rigid and lock out your full range of motion right from your warm-up sets. 
2. **Lock in your setup:** Set up with your core braced and your hips high so you match the airtight form you just produced today.

### WITHOUT RAG
### Progress Tracking

Great work on this session! You put up a clean sheet with 10 out of 10 correct reps, pushing your overall score up to 91 (compared to 84 in your previous session on September 20th). Even better, you completely cleared out the hip sag and partial range of motion issues that showed up last time. Zero errors recorded today—you nailed the standard.

### Next Session Plan

* **Hold the line:** Keep the exact same form, full depth, and rigid midsection you just used. 
* **Lock in your setup:** Take a second before your first rep to brace your core and glutes so you start strong, exactly like you did today.

---


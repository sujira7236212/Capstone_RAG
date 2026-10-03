# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `C:/Users/HP/AppData/Local/Temp/claude/c--Users-HP-Documents-RAG-SYSTEM/ff00b949-2a72-429a-a1a7-392ed8b6748d/scratchpad/mock_smoke_v14.json` |
| query mode | **taxonomy** — `error_type` resolved through `error_taxonomy.py` |
| collection | `kb_gemini_curated_v6` |
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
1. Current session details (a summary of the set, and every attempt in it with its errors).
2. Historical comparison (data from their previous session).

How to read the session data:
- `error_type` is the system's internal key for a fault (lowercase words joined by
  underscores). It identifies the fault: use it to tell which attempt has which fault, and to
  compare with `previous_common_errors`, which uses the same keys. Never write a key to the
  user - name the fault in plain words instead. When an attempt lists more than one error,
  they are in the system's priority order: the first one is the most important.
- `status`: "completed" is a counted rep. "abort" is an attempt that started the movement but
  came back before reaching the point the system counts as a rep, so the system did not count
  it. The summary still includes it: `total_reps` counts every entry, completed or aborted,
  and an aborted attempt with a fault counts in `incorrect_reps`. Call an aborted entry an
  attempt (e.g. "attempt 5"), not a rep, and if any entry aborted, do not tell the user they
  completed all of them. When the fault on an aborted attempt is about range of motion (not
  going deep enough, not going far enough), the abort is that fault itself: the attempt was
  cut short.
- `state_occurred` is a phase label from the system's rep counter. The labels follow the main
  joint as it bends and then straightens again, always in this order: CONCENTRIC (first half
  of the attempt), INFLECTION (the turnaround), ECCENTRIC (second half). Which way the body
  moves in each half depends on the exercise:
    Squat, Lunge:  CONCENTRIC = going DOWN              INFLECTION = at the bottom
                   ECCENTRIC  = standing back UP
    Push-up:       CONCENTRIC = lowering the chest DOWN INFLECTION = at the bottom
                   ECCENTRIC  = pressing back UP
    Bicep curl:    CONCENTRIC = curling the weight UP   INFLECTION = at the top of the curl
                   ECCENTRIC  = lowering the weight back DOWN
  In squat, lunge and push-up this is the reverse of the textbook meaning of the words:
  CONCENTRIC there is always the way DOWN, never the way up. Read the labels only through
  this table. Never write CONCENTRIC, INFLECTION or ECCENTRIC to the user, and do not use the
  words "concentric", "eccentric" or "inflection" anywhere, not even in brackets - say the
  plain phase from the table.
  What the label tells you depends on the fault:
    - rounded_back, hip_sag_or_pike, forward_trunk_lean and elbow_flare are watched during
      the movement: `state_occurred` is the phase in which the fault happened.
    - Every other fault is judged once, when the attempt ends, from the attempt as a whole
      (how deep or how far it went, where the knees were). Its `state_occurred` only says
      where the attempt ended - ECCENTRIC on a completed rep, CONCENTRIC on an aborted one -
      not when the fault happened. Do not tie these faults to a phase of the movement.

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
   - Use the rep detail: if the error clusters in one phase of the movement (read from
     `state_occurred` through the table above), in the aborted attempts, or in the later
     attempts of the set, say so and tailor the advice to it (e.g. stop the set a rep earlier,
     drop the load, slow the descent).
3. Next Session Plan: close with 2-3 short, prioritised things to do in their next workout.
4. Tone: encouraging, direct, and specific. Short paragraphs and bullets. No filler, no lecture.

Sessions with no errors: if the session records no errors, write the Progress Tracking section
and a Next Session Plan about holding the standard they just hit. Do not go looking through the
Context for something else to change, and do not suggest a different version of the exercise
(a narrower grip, a different stance) as a way to have something to say. A clean session is the
result, not a gap to fill.

Stick to their numbers: rep numbers, rep counts, scores and which fault each attempt carries come
from the session JSON and nothing else. They must match it exactly. If you say "the last three
reps", list three.
Keep the two sessions apart. The previous session's error list is history: if a name appears
there but in none of this session's reps, that fault is GONE - credit them for clearing it, and
never attach it to a rep they did today. Faults with similar names are still different faults
(a wrist that folds back and a grip that is too wide are not the same error) - when you name the
fault on a given rep, describe the fault whose key that rep actually carries in this session's data.

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

## Exercise: Squat — mixed

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| knee_valgus | Knees caving in as the lifter squats: one or both knees collapsing inside the feet while lowering or rising (dynamic knee valgus, medial knee displacement) (+why/fix) | 0.045 / 3* | 0.130 / 2* | 0.115 / 2* | 0.095 / 2* |
| partial_squat | Squatting too shallow: stopping the descent early in a half or quarter squat, so the thighs stay well above parallel and the knees never reach a 90-degree bend (+why/fix) | 0.062 / 2* | 0.185 / 2* | 0.160 / 2* | 0.174 / 2* |
| rounded_back | Losing a straight back during the squat: the upper back hunching, the lower back rounding as the pelvis tucks under at the bottom (butt wink), the lower back over-arching, or the torso tipping too far forward (+why/fix) | 0.049 / 3* | 0.119 / 2* | 0.109 / 2* | 0.101 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: knee_valgus | source: Bell2013_KneeValgusReducedAfterExercise_Squat_JAthlTrain]
Allowing the knees to cave inward (medial knee displacement or knee valgus) during a squat.

[mistake | re: rounded_back | source: blog.nasm.org/newletter/squat-form]
Losing lumbar lordosis or failing to maintain a neutral low back position during the squat.

[mistake | re: partial_squat | source: TheBackSquatAProposedAssessment]
Squatting too shallow, where the athlete does not achieve a depth where the tops of the thighs are at least parallel to the ground.

[mistake | re: knee_valgus | source: Bell2013_KneeValgusReducedAfterExercise_Squat_JAthlTrain]
Allowing the knees to cave inward, known as dynamic knee valgus or medial knee displacement, during the descent or ascent of a squat.

[principle | re: knee_valgus | source: TheBackSquatAProposedAssessment]
During the squat, the lateral aspect of the knee should not cross the vertical plane of the medial malleolus to avoid medial displacement.

[mistake | re: knee_valgus | source: Bell2013_KneeValgusReducedAfterExercise_Squat_JAthlTrain]
Allowing the knees to cave inward (medial knee displacement or dynamic knee valgus) during squatting movements.

[principle | re: rounded_back | source: blog.nasm.org/newletter/squat-form]
Maintaining an upright chest and thoracic position with the scapula retracted is important to attain a correct lumbo-pelvic position during the squat.

[consequence | re: rounded_back | source: TheBackSquatAProposedAssessment]
Allowing the hips to rise too quickly and increasing trunk flexion during the ascent represents an incorrect back squat that can be a dangerous strategy to the lower back during squatting with progressive external resistance.

[consequence | re: knee_valgus | source: basics_of_strength_and_conditioning_manual]
Allowing the knees to come together (valgus knee position) increases the strain on the ligaments and muscles surrounding the knee.

[finding | re: rounded_back | source: TheBackSquatAProposedAssessment]
Flexing at the spine before 120 degrees of hip flexion when squatting may indicate restriction in the posterior fibers of the iliotibial band or a lack of lumbar control.

[consequence | re: rounded_back | source: Kim2015_HipAnkleROM_SquatDepth_JHumKinet]
Failing to maintain correct positioning during the squat can increase joint strain and potential injury to the low back and knees.

[finding | re: rounded_back | source: Papadakis2024_BackSquatErrors_NeutralSpineKneeAlignment_JFMK]
A flat lumbar spine during squats is associated with a thinner anterior vertebral wedge, long paraspinal muscles, and/or a long iliopsoas.

[finding | re: knee_valgus | source: Bell2013_KneeValgusReducedAfterExercise_Squat_JAthlTrain]
Visual knee valgus is clinically defined during a double-legged squat screening when the midpoint of the patella passes medial to the great toe in 3 out of 5 trials.

[principle | re: knee_valgus | source: Papadakis2024_BackSquatErrors_NeutralSpineKneeAlignment_JFMK]
Proper coaching cues, such as 'knees out', and the use of resistance bands can assist in reinforcing correct knee alignment.

[consequence | re: knee_valgus | source: blog.nasm.org/newletter/squat-form]
Over-pronation of the foot can lead to dynamic knee valgus during the squat.

[finding | re: knee_valgus | source: Papadakis2024_BackSquatErrors_NeutralSpineKneeAlignment_JFMK]
Knee joint genu valgus during squats is associated with reduced height of the lateral meniscus, decreased hip abductor performance (gluteus maximus and medius), increased femoral anteversion, internal rotation of the tibia, and decreased ankle inversion muscles (tibialis anterior and posterior).

[mistake | re: partial_squat | source: Kim2015_HipAnkleROM_SquatDepth_JHumKinet]
Limiting squat depth (stopping early in a partial squat) due to restricted ankle dorsiflexion or hip mobility.

[mistake | re: rounded_back | source: Papadakis2024_BackSquatErrors_NeutralSpineKneeAlignment_JFMK]
Allowing excessive lumbar lordosis (hyperextension) or excessive lumbar flexion during the squat.

[mistake | re: rounded_back | source: Papadakis2024_BackSquatErrors_NeutralSpineKneeAlignment_JFMK]
Rounding the back, bending forward, raising the heels, or looking down during the ascent phase are common errors that compromise squat effectiveness.

[consequence | re: partial_squat | source: TheBackSquatAProposedAssessment]
Without squatting to the proper depth, the hamstrings and gluteus muscular complex may not be adequately challenged.

[principle | re: rounded_back | source: basics_of_strength_and_conditioning_manual]
Never flex the spine or round forward during a squat.

[principle | re: partial_squat | source: TheBackSquatAProposedAssessment]
The descent phase of the squat begins as the hips, knees, and ankles flex, and should continue until the top of the thigh is at least parallel with the ground and the hip joint is at least level with or slightly below the knee joint.

[finding | re: partial_squat | source: www.healthline.com/health/fitness/deep-squat]
In a standard squat, the knees are bent at around a 90-degree angle with thighs parallel to the ground.

[principle | re: partial_squat | source: www.nasm.org/resource-center/blog/training/biomechanics-of-the-squat]
The appropriate squat depth is the deepest position a client can achieve while maintaining a neutral spine, foot stability, proper joint alignment, and movement control.

[consequence | re: partial_squat | source: www.healthline.com/health/fitness/deep-squat]
Performing a partial squat instead of a deep squat may subject the knee joint to higher compressive forces.

[finding | re: partial_squat | source: www.healthline.com/health/fitness/deep-squat]
Scientific research does not substantiate any increased risk of knee injury from performing deep squats.
```

### WITH RAG
### Progress Tracking
You finished today's session with 4 correct reps out of 10 total attempts (including 1 aborted attempt), landing on an overall score of 67. Compared to your previous session on October 2, your correct rep count stayed steady at 4, but your overall score dipped slightly from 70 to 67, and your incorrect reps rose from 4 to 6. Both of your old hurdles—knees caving in and rounding your lower back—showed up again today, and a new habit of cutting your depth short crept into your reps and your final aborted attempt. 

***

### Error Breakdown

* **Knee Valgus**
  * **What it is:** Your knees collapse inward toward each other instead of tracking straight out over your toes. This happened on reps 2, 6, and 10 as you pushed back up to stand.
  * **Why it matters:** When your knees drift inward, it cranks up the strain on the ligaments and muscles hugging the knee joint. Over time, that translates into achy, unhappy knees that start talking to you halfway through a workout and put a hard ceiling on how much weight you can safely load.
  * **How to fix it:** 
    (a) Cue yourself to "push the floor apart" and drive your knees wide as you stand. 
    (b) Loop a light resistance band just above your knees during your warm-up sets to force your outer hips to turn on. 
    (c) Practice bodyweight box squats where you deliberately touch your outer knees to a pair of wide target posts on the way down. 
    (d) Glance down in the mirror as you press up; if your kneecaps dip inside your big toes, you'll see it immediately.

* **Rounded Back**
  * **What it is:** Your spine loses its neutral arch and slumps forward. This crept in on rep 4 (while standing back up), reps 6 and 10 (at the very bottom of the squat), and on your aborted attempt 9 (on the way down).
  * **Why it matters:** Letting your spine round under a heavy barbell shifts the load away from your legs and directly onto your lower back, especially as your hips rise too quickly out of the bottom. That sets you up for a nagging, deep-seated lower-back ache the next day and increases your injury risk as the weight goes up.
  * **How to fix it:** 
    (a) Think about pulling your chest up proudly and squeezing your shoulder blades together before you even unrack the bar. 
    (b) Slow down your tempo on the way down and pause for a solid second at the bottom to lock in your back angle before you reverse direction. 
    (c) Drop the load and practice light goblet squats, keeping your torso upright and your chest glued to an imaginary wall in front of you. 
    (d) Check your phone video from the side: your upper and lower back should stay locked in the exact same shape from start to finish.

* **Partial Squat**
  * **What it is:** You're cutting the movement short and failing to drop deep enough. This hit on rep 4, rep 8, and forced you to abort attempt 9 on the way down before you even reached the bottom.
  * **Why it matters:** If you shortchange your depth, your glutes and hamstrings don't get fully stretched or challenged, meaning you miss out on the muscle growth and strength you came for, while your knee joints soak up higher compressive forces for zero extra reward.
  * **How to fix it:** 
    (a) Focus on sinking your hips down and back until your hip joint sits at least level with or slightly below your knee. 
    (b) Set a sturdy box or bench at that exact parallel height so you have a physical target to touch every single rep. 
    (c) Practice unweighted bodyweight squats with a 3-second pause at the bottom to build comfort and mobility in the deep position. 
    (d) Have someone film you from the side; look for the crease of your hip dropping below the top of your kneecap at the bottom.

***

### Next Session Plan
1. **Lighten the load and chase depth:** Drop the weight slightly for your next session so you can consistently hit parallel depth without rounding your lower back or cutting your reps short.
2. **Add a band for knee tracking:** Warm up with banded bodyweight squats to hardwire that "knees out" habit before you put any heavy plates on your back.
3. **Control the bottom transition:** Take an intentional one-second pause at the bottom of every rep to eliminate rushing and keep your spine flat as you drive back up.

### WITHOUT RAG
### Progress Tracking
Let’s look at how today stacked up against your last session on October 2nd. Your correct rep count held steady at 4, but your overall score dipped slightly from 70 to 67, and you picked up 6 incorrect reps instead of clearing them out. On the bright side, you kept a solid baseline of clean reps mixed in, but old habits are still creeping in as you fatigue.

### Error Breakdown

* **Knee Valgus (Knocking Knees Inward)**
  * **What it is:** On reps 2, 6, and 10, your knees caved inward toward each other instead of tracking straight out over your toes, especially on the way back up to standing.
  * **Why it matters:** This puts a lot of shearing stress right through your knee joints and hip sockets, and it shuts off your glutes. You'll feel it as a strange pinch or ache around the front and sides of your knees after the set, and it robs you of your power out of the bottom of the squat.
  * **How to fix it:** 
    * (a) Cue: "Spread the floor apart with your feet" as you stand up.
    * (b) Setup change: Loop a light resistance band just above your knees to give your hips tactile feedback to push outward.
    * (c) Drill: Practice bodyweight pauses at the bottom of the squat while actively driving your knees wide against an imaginary band.
    * (d) Self-check: Watch your phone video—your kneecaps should point in the exact same direction as your second and third toes the entire time.

* **Rounded Back (Loss of Spine Neutrality)**
  * **What it is:** On reps 4, 6, 9 (an aborted attempt), and 10, your lower back lost its flat, braced position and rounded outward, particularly at the very bottom of the squat or during the ascent.
  * **Why it matters:** Your lower back and spinal discs soak up the load instead of your core and hips. That means you'll feel a nagging lower back pump or soreness that lingers long after you leave the gym, and it heavily caps how much weight you can safely lift as you get stronger.
  * **How to fix it:**
    * (a) Cue: "Big chest, proud sternum, and brace your abs like someone is about to punch your stomach."
    * (b) Setup change: Reduce the load slightly so you can maintain spinal tension without your hips shooting up early.
    * (c) Drill: Perform lighter goblet squats while focusing entirely on keeping a vertical-ish torso and a locked-in lower back.
    * (d) Self-check: Check a side-view mirror or video—your belt line should maintain the same arch from start to finish without any tucking under at the bottom.

* **Partial Squat (Short Range of Motion)**
  * **What it is:** On reps 4, 8, and 9 (which aborted early on the way down), you cut the depth short and didn't reach the bottom of the squat.
  * **Why it matters:** You're cheating your quads and glutes out of the full stretch and contraction they need to grow and get stronger. You'll finish the set feeling like you worked hard, but you're leaving a massive chunk of muscle-building work on the table.
  * **How to fix it:**
    * (a) Cue: "Pull your hips down between your ankles until your thighs break parallel to the floor."
    * (b) Setup change: Set a box or a target height just below parallel so you have a physical marker to touch on every single rep.
    * (c) Drill: Box squats with a lighter weight to train your brain to hit full depth consistently.
    * (d) Self-check: Glance at your side-profile video to verify your hip crease drops clearly below the top of your knee cap before you reverse direction.

### Next Session Plan
1. **Drop the weight by 10%:** Give yourself room to fix your depth and back angle without fighting for your life on every rep.
2. **Use a box or bench target:** This solves the depth issue instantly and forces you to hit the same bottom position every time.
3. **Rest longer between sets:** Give yourself a full two minutes to recover so fatigue doesn't cause your knees to cave and your back to round by rep 6.

---

## Exercise: Push-up — mixed

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| hip_sag_or_pike | Failing to hold a straight plank line in the push-up: the hips sagging toward the floor with the lower back arching, or the hips piking up toward the ceiling (+why/fix) | 0.074 / 3* | 0.238 / 2* | 0.114 / 2* | 0.137 / 2* |
| partial_pushup | Push-ups that stop too high: lowering only partway, so the chest stays far from the floor (+why/fix) | 0.122 / 1* | 0.219 / 2* | 0.200 / 1* | 0.189 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: hip_sag_or_pike | source: www.acefitness.org/resources/pros/expert-articles/7265/perfecting-the-push-up-for-all-levels]
Failing to activate the deep core muscles required to stabilize the spine and pelvis during the push-up.

[consequence | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Failing to maintain a neutral lumbar spine position during a push-up results in anterior pelvic tilt and trunk lag, indicating impaired trunk stability.

[mistake | re: partial_pushup | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Failing to complete the push-up by only rising one to two inches from the floor due to insufficient upper body strength.

[principle | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Maintaining a neutral lumbar spine position and control is necessary to prevent anterior pelvic tilt and trunk lag during the push-up.

[consequence | re: hip_sag_or_pike | source: blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement]
Allowing the lower back to sag or arch during a push-up increases mechanical stress on the vertebral discs.

[mistake | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Anterior pelvic tilt and trunk lag are common errors where the trunk fails to lift as a single unit during the push-up.

[mistake | re: hip_sag_or_pike | source: blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement]
As fatigue sets in during a push-up, the lower back may arch or sag, causing the kinetic chain checkpoints to migrate out of alignment.

[principle | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Improving awareness of lumbar spine position and thoracic spine mobility can help improve trunk stability during a push-up.

[principle | re: partial_pushup | source: www.nasm.org/resource-center/blog/training/proper-push-up-form-and-technique-a-complete-guide]
Lower the body with control until the chest approaches the floor.

[consequence | re: partial_pushup | source: www.nasm.org/resource-center/exercise-library/push-up]
Not achieving adequate range of motion limits chest stretch and development.

[finding | re: partial_pushup | source: The_Effect_of_Position_on_the_Percentage_of_Body.992962]
The increased force in the down position of a push-up is due to the whole-body center of mass being located further from the point of contact with the floor, which results in greater torque.

[principle | re: partial_pushup | source: www.nasm.org/resource-center/exercise-library/push-up]
Descend until your chest nearly touches the floor or your elbows bend to approximately 90 degrees, whichever comes first based on mobility.

[finding | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
More than 60% (n=65/108) of active females failed the Trunk Stability Push Up (TSPU) compared to less than 10% (n=10/101) of active males.

[finding | re: partial_pushup | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
In a study of active females, 45% of participants passed the Trunk Stability Push-Up (TSPU) post-intervention, with many of those who failed only able to rise one to two inches from the floor.

[finding | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
In a pilot study of active females, a six-week multiplanar trunk stability intervention resulted in 9 of 20 participants (45%) improving their Trunk Stability Push Up (TSPU) score to ≥2.
```

### WITH RAG
### Progress Tracking
You landed 4 clean reps today out of 10 total entries (which includes 3 aborted attempts where you had to cut the movement short). Your overall score dipped slightly to 65 compared to 71 yesterday, and your correct rep count dropped from 5 down to 4. Both of your old consistency bumps—letting your hips sag and cutting the depth short—showed up again today, so those remain your primary targets.

---

### Error Breakdown

* **What it is:** Your lower back arches and your hips drop toward the floor instead of your whole body moving as a single rigid plank. This showed up both at the bottom turnaround on reps 3 and 9, and as you were lowering yourself down on attempts 5, 6, and 10.
* **Why it matters:** When your midsection gives out, your lower back takes the mechanical stress instead of your core bracing the load. That adds wear and tear to your vertebral discs, and it's usually the first sign that fatigue is pulling your form apart.
* **How to fix it:** 
  * (a) Cue: Think about squeezing your glutes hard and bracing your stomach like you are about to take a punch before you even start moving.
  * (b) Setup: Drop down to incline push-ups on a sturdy bench or box to take some load off until your core can keep up with your upper body.
  * (c) Drill: Practice standard planks on your elbows to build endurance in the exact muscles needed to keep your hips level.
  * (d) Self-check: Watch a video of your set from the side—your shoulders, hips, and ankles should move together as one straight line with zero dip in the middle.

* **What it is:** You're cutting the descent short and failing to press back up through a full range of motion. This caught you on attempts 5, 8, and 10, where you aborted the movement early or barely managed to push yourself an inch or two off the floor.
* **Why it matters:** Stopping short cheats your chest muscles out of a full stretch and development, and it leaves you weak at the bottom where the leverage is hardest.
* **How to fix it:** 
  * (a) Cue: Aim to bring your chest down until it nearly brushes the floor or your elbows form a 90-degree angle.
  * (b) Setup: Shorten your target depth temporarily or use an elevated surface so you can hit the bottom position cleanly on every single rep without failing.
  * (c) Drill: Eccentric-only push-ups—lower yourself all the way to the floor with control over three seconds, drop to your knees, and press back up.
  * (d) Self-check: Feel for a deep stretch across your chest at the bottom of each rep before you press back up.

---

### Next Session Plan
1. **Reduce the volume or elevate your hands:** Drop the reps per set or use a slightly elevated surface so you can finish every rep without form breaking down or stalling out at the bottom.
2. **Prioritize core tension:** Squeeze your glutes and brace your abs before every single rep to keep your hips from sagging as you fatigue.

### WITHOUT RAG
### Progress Tracking
Let’s look at how today compares to your session on October 2nd. Your overall score dipped slightly from 71 to 65, and your clean rep count dropped from 5 down to 4, with 6 more attempts running into trouble (including 3 aborted attempts where you cut the movement short). 

The good news? You didn't pick up any brand-new faults today—the issues showing up are the exact same ones from last time (`hip_sag_or_pike` and `partial_pushup`). That means we know the exact targets to fix. Let's clean them up so you can trust every single rep you push out.

### Error Breakdown

#### Sagging or Piking Hips
* **What it is:** Your hips are either dropping toward the floor or hiking up toward the ceiling instead of keeping your whole body locked in a straight plank. This crept in during the bottom turnaround (the inflection phase) and as you began pressing back up, especially on reps 3, 5, 6, 9, and 10.
* **Why it matters:** When your midsection gives way, your lower back and core lose their bracing, which forces your spine to soak up stress it shouldn't be handling. This steals power from your chest and arms, saps your strength mid-set, and sets you up for a dull ache in your lower back rather than a solid chest pump.
* **How to fix it:** 
  (a) Cue: Squeeze your glutes hard and brace your stomach as if someone is about to poke you in the ribs before you even start moving.
  (b) Setup change: Take a slightly wider foot stance to give your lower body a more stable base of support.
  (c) Drill: Drop to your knees for a few controlled sets to lock in core tension without the full bodyload, then return to your toes once you feel the difference.
  (d) Self-check: Have someone film your side profile—your shoulders, hips, and ankles should move as one single rigid board from top to bottom.

#### Partial Push-up
* **What it is:** You cut the movement short before your chest got low enough, leading to shallow, incomplete attempts. This showed up right at the start of the lowering phase on attempts 5, 8, and 10, causing you to abort those tries early.
* **Why it matters:** Shortchanging your range of motion means you miss out on stretching and working the chest muscles through their full path, leaving you with less muscle growth and strength gains for the exact same amount of effort.
* **How to fix it:** 
  (a) Cue: Think about actively pulling your chest down to a specific target rather than just dropping your upper body.
  (b) Setup change: Slow down your tempo on the way down so you control the descent instead of rushing the turnaround.
  (c) Drill: Elevate your hands on a sturdy bench or box to make the full depth manageable, ensuring your chest makes light contact with the target every single time.
  (d) Self-check: Notice whether your upper arms reach at least parallel to the floor at the bottom of the dip before you press back up.

### Next Session Plan
1. **Prioritize core tightness first:** Spend an extra second before rep one locking your glutes and abs, and if your hips start sagging by rep 6, stop the set right there rather than fighting through broken form.
2. **Commit to full depth:** Scale the height of your hands if needed so you can comfortably hit the bottom position on every single rep without having to abort early.

---

## Exercise: Lunge — shallow_lunge

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| shallow_lunge | Lunging too shallow: dipping only slightly, so the front knee stays far from a 90-degree bend and the front thigh stays well above parallel (+why/fix) | 0.135 / 2* | 0.226 / 2* | 0.316 / 1* | 0.185 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: shallow_lunge | source: basics_of_strength_and_conditioning_manual]
Failing to lower the hips until the front thigh is parallel to the floor.

[principle | re: shallow_lunge | source: Trunk and Shank Position Influences Patellofemoral Joint Stress in the Lead and Trail Limbs During the Forward Lunge Exercise]
To achieve proper depth during a lunge, descend until the trail knee is just prior to touching the ground.

[mistake | re: shallow_lunge | source: Effects of Loading Positions on Lower Limb Biomechanics During Lunge Squat in Men with Different Training Experience]
Novice lifters may perform backward lunges with shallower knee flexion compared to experienced lifters.

[principle | re: shallow_lunge | source: Bezerra2021_TrunkPosition_LungeActivation_IJES]
During the lunge, the front knee should be flexed to approximately 90 to 100 degrees as the rear knee is lowered toward the ground.

[finding | re: shallow_lunge | source: Effects of Loading Positions on Lower Limb Biomechanics During Lunge Squat in Men with Different Training Experience]
During backward barbell lunges, novices achieved a shallower peak knee flexion with a minimal sagittal angle of -99.01 ± 10.02 degrees compared to -108.44 ± 8.33 degrees in experienced lifters.

[finding | re: shallow_lunge | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
During a forward lunge, a shallower front knee flexion angle of 80° results in a statistically significantly higher knee extensor moment (0.980 Nm/BW) compared to 90° (0.717 Nm/BW) and 100° (0.362 Nm/BW).

[consequence | re: shallow_lunge | source: Jaeggi2024_SplitSquat_RearLegMuscleForces_JFMK]
Failing to sufficiently activate the m. gluteus maximus reduces the generation of posterior shear forces at the tibia, which otherwise potentially contribute to a reduced likelihood of knee injuries.
```

### WITH RAG
### Progress Tracking
You finished today's session with an overall score of 71, a slight uptick from your 70 in the previous workout. You successfully completed 6 clean reps out of 10 total attempts, matching your previous count of 6 correct reps. Your old nemesis, the shallow lunge, showed up again on your four aborted attempts (attempts 3, 5, 7, and 9), meaning that old habit is still hanging around. 

***

### Error Breakdown: Shallow Lunge

* **What it is:** You're cutting the movement short on your way down instead of dropping your hips until your front thigh sits parallel to the floor and your front knee reaches roughly 90 to 100 degrees of bend. 
* **Why it matters:** Cutting the depth short forces your quads to absorb a disproportionately higher joint moment (up to 0.980 Nm/BW at 80 degrees compared to 0.717 at 90 degrees), which overloads the front of your knee. At the same time, it robs your glutes of the work they need to do, costing you strength development and leaving you more vulnerable to knee strain down the road.
* **How to fix it:** 
  *(a) Cue to think about:* Think about lowering your back knee straight down toward the floor on the way down, rather than sliding forward.
  *(b) Setup change:* Slow your tempo down on the descent to a deliberate three-second count so you have time to settle into the bottom position before pushing back up.
  *(c) Drill or regression:* Drop the weight entirely and practice bodyweight split squats, pausing for a full two seconds at the bottom where your back knee hovers just above the floor.
  *(d) Self-check:* Set your phone up for a side-profile video and check that your front shin stays roughly vertical and your front thigh is parallel to the floor at the bottom of each rep.
* **Phase detail:** This error specifically caused you to bail out early during the going down phase on attempts 3, 5, 7, and 9—notice how it cropped up later in the set as fatigue set in.

***

### Next Session Plan
1. **Pace your reps:** Slow down the lowering phase on every single rep to guarantee you hit full depth before you press back up, especially as you get tired near the end of the set.
2. **Use a depth target:** Hover your back knee just shy of touching the floor on every rep so you have a physical benchmark to keep your range of motion honest.

### WITHOUT RAG
### Progress Tracking
You finished today's session with 6 correct reps out of 10 total attempts, earning an overall score of 71. That puts you right on par with your last workout on October 2, where you also hit 6 correct reps and scored a 70. 

Your old nemesis, the shallow lunge, carried over from last time and showed up on all 4 of your missed attempts (reps 3, 5, 7, and 9). The good news? You didn't add any new errors to the mix, and your solid reps looked great. Let's fix that depth so you can clear the rest of those attempts.

---

### Error Breakdown

*   **What it is, in plain words:** You're cutting your stride short on the way down. Instead of lowering your hips until your back knee hovers just above the floor, you're stopping halfway and pushing back up.
*   **Why it matters:** When you don't drop your hips all the way down, your front leg and glutes miss out on the full stretch and workload you came for. That cuts down the muscle-building return on your effort, leaving you with a half-finished rep that doesn't challenge your lower body the way it should.
*   **How to fix it:** 
    *   (a) Cue: Think about dropping straight down toward the floor, not lunging forward.
    *   (b) Setup: Take a slightly longer stride forward when you step out so your back knee has the room it needs to descend cleanly.
    *   (c) Drill: Practice bodyweight split squats with your rear foot elevated on a low bench to get used to the feeling of a full, deep descent without worrying about balance.
    *   (d) Self-check: Glance in the mirror sideways or film a set on your phone—your back knee should gently graze or hover just above the floor at the bottom of every rep.

---

### Next Session Plan

1. **Slow down the descent:** Take a full two seconds to lower yourself on every single rep. Rushing the way down is usually why depth gets cut short.
2. **Commit to the bottom:** Treat every rep like it needs to reach full depth before you even think about pressing back up. If an attempt starts feeling short, abort it cleanly rather than muscling through a half-rep.
3. **Target 8 clean reps:** Keep your weight and setup identical to today, but focus on turning at least two of those previous aborted attempts into fully completed, deep lunges.

---

## Exercise: Bicep Curl — partial_curl

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| partial_curl | Curling through only part of the range: not straightening the arm at the bottom, or not bringing the weight all the way up at the top (half repetitions) (+why/fix) | 0.132 / 3* | 0.207 / 2* | 0.183 / 2* | 0.146 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: partial_curl | source: Optimizing Resistance Training Technique to Maximize Muscle Hypertrophy A Narrative Review]
Performing partial repetitions at shorter muscle lengths rather than allowing the muscle to fully stretch.

[principle | re: partial_curl | source: The Effect of Varying Weightload Intensities on Biceps Curl Techn]
A complete repetition of a bicep curl requires moving the weight from a position of full elbow extension to a position of full flexion, and returning back to the initial position of full extension.

[mistake | re: partial_curl | source: Oliveira2009_ShoulderPosition_BicepsEMG_JSSM]
Lifters frequently start the bicep curl from a slightly flexed elbow position of around 20 degrees instead of starting from full elbow extension.

[principle | re: partial_curl | source: Oliveira2009_ShoulderPosition_BicepsEMG_JSSM]
The bicep curl should ideally begin from a position of full elbow extension to ensure a complete range of motion.

[consequence | re: partial_curl | source: The Effect of Varying Weightload Intensities on Biceps Curl Techn]
Failing to pause at full extension and full flexion increases the risk of sustaining an injury.

[mistake | re: partial_curl | source: The interplay between muscle length, range of motion, and exercise selection a review]
Training exclusively at the final range of motion, where the muscle contracts only at short muscle lengths and avoids the initial stretched position.

[finding | re: partial_curl | source: Optimizing Resistance Training Technique to Maximize Muscle Hypertrophy A Narrative Review]
Partial repetitions at shorter-muscle lengths are not as hypertrophic as partial repetitions at longer-muscle lengths.

[consequence | re: partial_curl | source: The interplay between muscle length, range of motion, and exercise selection a review]
Training exclusively at the final range of motion results in inferior muscle hypertrophy compared to training with a full range of motion or at longer muscle lengths.

[finding | re: partial_curl | source: Oliveira2009_ShoulderPosition_BicepsEMG_JSSM]
Previous studies have reported a strategy of starting the bicep curl movement with an elbow joint angle ranging from 15 degrees to 48 degrees.
```

### WITH RAG
### Progress Tracking

Great to see your overall score tick up from 73 to 76, and you matched your previous count of 6 clean, correct reps. That said, the exact same issue—cutting your reps short—showed up again today just like it did in your last session, appearing across reps 4, 6, 8, and the aborted attempt 9. You are still dealing with the exact same habit, so let's get it sorted for good.

### Error Breakdown

* **What it is, in plain words:** You are cutting your reps short instead of going all the way. On reps 4, 6, and 8, you shorten the lowering phase, and on attempt 9, you abort early without finishing the curl.
* **Why it matters:** Skipping the fully stretched starting position means your biceps miss out on the deep stretch they need for maximum muscle growth, leaving you with inferior muscle gains for the same amount of effort. Plus, failing to control the full range of motion ramps up your risk of sustaining an injury.
* **How to fix it:** 
  - (a) **Cue:** Think "reach the bottom completely" before every single rep.
  - (b) **Setup change:** Deliberately start every rep from a position of fully straight arms with your elbows locked out, rather than kicking off with a slightly bent elbow. 
  - (c) **Drill or regression:** Pause briefly at the very bottom and the very top of each rep to force your arms into a complete range of motion.
  - (d) **Self-check:** Glance in the mirror to confirm your arms are completely straight at the bottom before you start curling back up.

### Next Session Plan

1. **Lock out the bottom:** Spend your next session actively checking that your arms are fully straight at the start of every rep, instead of rushing straight into the next lift with a bend in your elbow.
2. **Slow down the drop:** Focus on taking an extra second to lower the weight all the way down, particularly as you get tired near the end of the set where these partial reps tend to sneak in.

### WITHOUT RAG
### Progress Tracking

Good movement on the score sheet today—your overall score ticked up to 76 from 73 in your last session, and you matched your count of 6 clean, fully-completed reps. Your old habit of cutting reps short (partial_curl) is still hanging around, showing up on 4 occasions (reps 4, 6, 8, and an aborted attempt on rep 9). The good news is that those slips are entirely isolated to the second half of the movement as you lower the weight back down, meaning your curls on the way up are locked in. Let's clean up the tail end of those reps so you get full value from every single one.

***

### Error Breakdown

*   **What it is, in plain words:** As you lower the weight back down in the second half of the movement (the lowering phase), you're cutting the descent short and dropping the bar prematurely instead of controlling it all the way to a straight arm.
*   **Why it matters:** When you shortcut the lowering phase, your biceps miss out on the tension they need during the stretch. That costs you muscle growth for the exact same effort, and it leaves strength on the table because you're bypassing the hardest part of the lift.
*   **How to fix it:** 
    *   *(a) Cue:* Think about actively reaching your hands toward the floor at the bottom of every rep.
    *   *(b) Setup:* Lighten the load slightly or slow your tempo down to a 3-second descent on those final reps where fatigue starts creeping in.
    *   *(c) Drill:* Try a slow-eccentric-only set with a lighter weight, taking a full 4 seconds just to lower the weight from top to bottom.
    *   *(d) Self-check:* Watch your arms in the mirror; your elbows should lock out completely straight at the bottom of every single rep before you start the next curl.
*   **Use the rep detail:** Notice how these short reps (4, 6, 8, and the aborted rep 9) only happen when fatigue sets in toward the later part of your set. When you feel your form start to clip the bottom range, don't force another sloppy rep—drop the weight or finish the set there.

***

### Next Session Plan

1. **Prioritize Full Extension:** Dedicate your first two working sets to hitting a complete, straight-arm lockout at the bottom of every single rep, even if you have to drop the weight by a few pounds to pull it off.
2. **Slow the Descent:** Consciously slow down the lowering phase of your curl, especially on reps 4 through 10, to break the habit of dropping the weight prematurely.

---


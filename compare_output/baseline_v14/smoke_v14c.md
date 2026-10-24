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
   - Use the rep detail: if the error clusters in the aborted attempts or in the later
     attempts of the set, say so and tailor the advice to it (e.g. stop the set a rep earlier,
     drop the load, slow the descent). The data does not say in which part of the movement a
     fault happened, so do not claim one.
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

Compared to your last session yesterday, your numbers stayed pretty steady: you landed 4 correct reps again, and your overall score dipped slightly from 70 down to 67 out of 100. Out of your 10 total entries today, 6 had errors—including attempt 9, which was cut short before you could finish it. The good news is you are keeping a solid baseline, but the same old habits are creeping back in as you fatigue. 

***

### Knees caving inward

* **What it is:** Letting your knees slump or drift toward each other instead of tracking straight over your feet as you push up and down.
* **Why it matters:** Putting your knees in this sideways-collapsed position cranks up the strain on the ligaments and muscles holding the joint together. When you load this up over time, you'll feel it as a nagging ache around your knees, and it robs you of the stable power base you need to drive heavy weight upward.
* **How to fix it:** 
  * (a) Think about actively driving your knees wide apart as you push out of the bottom.
  * (b) Widen your stance slightly or slip a mini resistance band just above your knees to give your hips a physical reminder to push outward.
  * (c) Try band-resisted bodyweight squats where you fight the band pulling your knees inward on every single rep.
  * (d) Glance down or check a side-angle phone video to see if your knees stay in line with your big toes throughout the lift.
* **Rep detail:** This popped up on reps 2, 6, and 10, showing up consistently in the second half of your set as your legs started getting tired.

### Rounding your lower back

* **What it is:** Letting your spine slump forward and lose its flat, braced position instead of keeping your torso rigid.
* **Why it matters:** When your lower back rounds under a load, your spine takes the brunt of the force instead of your glutes and core doing the heavy lifting. That translates to a dull, nagging lower-back tightness after your workout, burns up energy that should be moving the barbell, and ramps up your injury risk as you add weight.
* **How to fix it:** 
  * (a) Keep your chest proud and your shoulder blades pinned back to lock your spine into place.
  * (b) Take a huge breath into your belly and brace your abs hard before you even begin the descent.
  * (c) Practice the movement with a lighter weight or just bodyweight, pausing for two seconds at the bottom to ensure your torso isn't collapsing.
  * (d) Record a video from the side to see if your lower back stays flat or starts curling under when you hit the bottom.
* **Rep detail:** This crept in alongside other faults on reps 4, 6, 9 (the aborted attempt), and 10, heavily clustering in the fatigued final stretch of your set.

### Stopping too shallow

* **What it is:** Cutting your descent short and heading back up before your thighs drop parallel to the floor.
* **Why it matters:** If you shortchange your depth, your glutes and hamstrings don't get fully stretched or challenged, meaning you leave muscle growth on the table for the effort you're putting in. On top of that, stopping high can actually place higher compressive forces right onto the front of your knee joint.
* **How to fix it:** 
  * (a) Focus on sinking your hips down and back until your hip crease drops at least level with your knees.
  * (b) Adjust your setup by placing a low box or bench right at your target depth so you have a physical target to touch before coming back up.
  * (c) Regress to lighter goblet squats or bodyweight squats to rebuild comfort in the bottom position.
  * (d) Watch yourself in a side mirror or review a video to verify that your thighs genuinely break parallel to the floor.
* **Rep detail:** This showed up on reps 4, 8, and the aborted attempt 9, where you cut the movement short entirely because you ran out of steam or control.

***

### Next Session Plan

1. **Drop the load slightly:** Take 10% off your working weight next time so you can control your depth and posture without grinding through ugly reps.
2. **Watch the fatigue cliff:** Your form started falling apart around rep 6 today. Stop your working sets one rep *before* your form breaks down to build better movement patterns.

### WITHOUT RAG
### Progress Tracking
Let's look at how today's squat session stacked up against yesterday. You matched your correct rep count at 4 clean reps, but your overall score dipped slightly from 70 to 67, and your incorrect reps stayed high at 6 out of 10 attempts (which includes one aborted attempt on rep 9). On the bright side, your form is staying solid on alternating reps—your odd-numbered reps (1, 3, 5, 7) were all clean. However, the same old habits are creeping back in as fatigue sets in. You managed to keep knee caving off your clean reps, but it still popped up on reps 2, 6, and 10.

***

### Error Breakdown

*   **Knees collapsing inward**
    *   What it is, in plain words: As you push up out of the bottom of the squat, your knees drift toward each other instead of tracking straight out over your toes. This showed up on reps 2, 6, and 10—mostly as you started getting tired later in the set.
    *   Why it matters: Your knees and hips take a lot of twisting stress when they cave inward, leaking the power you need to drive the weight up. That means your quads and glutes have to work harder from a compromised position, leaving your knees aching and cutting your strength short as the barbell gets heavier.
    *   How to fix it: 
        (a) Cue: Think about "spreading the floor apart" with your feet as you stand up. 
        (b) Setup change: Narrow your stance slightly or point your toes out another couple of degrees to give your hips better leverage. 
        (c) Drill: Place a light resistance band just around your knees during your warm-up bodyweight squats to force your outer hips to stay active. 
        (d) Self-check: Watch your phone video from the front and make sure your kneecaps track directly over the middle of your feet on every single rep.

*   **Rounding your lower back**
    *   What it is, in plain words: Your spine loses its neutral arch and your lower back slumps forward under the load. This happened on reps 4, 6, 9, and 10, including your aborted attempt on rep 9 where you cut the movement short.
    *   Why it matters: Your spine takes the brunt of the load instead of your core and glutes locking your torso in place. That shifts the work away from the muscles you want to train and puts shearing stress on your lower back, leaving you with a dull ache after lifting and risking a serious strain as you add more weight to the bar.
    *   How to fix it: 
        (a) Cue: Take a deep breath into your belly and brace your abs hard like someone is about to punch you before you even unlock the bar. 
        (b) Setup change: Bring the weight down slightly so you can maintain a proud chest and a flat back throughout the whole range of motion. 
        (c) Drill: Practice goblet squats with a lighter weight on a slow 3-second tempo down, pausing at the bottom to check that your chest stays up and your lower back stays flat. 
        (d) Self-check: Check your side-profile video to ensure the natural curve of your lower back stays locked in from top to bottom.

*   **Cutting the depth short**
    *   What it is, in plain words: You are turning around and heading back up before hitting full depth, meaning your hips don't drop low enough. This hit on reps 4, 8, and your aborted attempt on rep 9 where you cut the movement short.
    *   Why it matters: You are cheating yourself out of full muscle engagement, meaning your glutes and quads aren't getting the full stretch and contraction they need for strength and growth. It also makes your rep counts unreliable because you aren't finishing the movement you started.
    *   How to fix it: 
        (a) Cue: Push your hips back and down until you feel your hamstrings load up like a spring at the bottom. 
        (b) Setup change: Set a box or a target height just below parallel so you have a physical marker to touch on every rep. 
        (c) Drill: Do pause squats with a lighter load, holding for two full seconds at the bottom before driving up to build comfort in the deep position. 
        (d) Self-check: Film your sets from the side to verify your hip crease genuinely drops below the top of your knee cap before you ascend.

***

### Next Session Plan
1. **Drop the load slightly:** Take 5–10% off the bar for your next session so you can focus entirely on hitting full depth with a flat back.
2. **Cut the reps short if form slips:** Your clean reps (1, 3, 5, 7) looked great because you were fresh. Next time, if your knees start caving or your back rounds by rep 6, end the set right there rather than grinding through sloppy reps.

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

Your overall score dipped slightly from 71 to 65, and your correct reps dropped from 5 down to 4 out of your 10 total attempts (which included 3 aborted tries). Both of your previous faults—sagging hips and cutting your depth short—showed up again today. The good news is that you nailed the first two reps cleanly, proving you have the strength for the movement when you are fresh. 

---

### Hips Sagging or Piking

* **What it is:** Your midsection gives way and your lower back arches downward toward the floor, causing your hips to drop instead of your whole body moving as a single, rigid plank. This crept up starting on rep 3 and showed up again on reps 5, 6, 9, and 10 as fatigue set in.
* **Why it matters:** When your trunk sags, the extra mechanical stress lands directly on your spinal discs instead of being absorbed by your core muscles. That is what leads to that nagging lower-back ache halfway through a set, and it robs you of the stable platform you need to push heavy weight.
* **How to fix it:**
  * **Cue:** Actively squeeze your glutes and brace your stomach like you are about to take a punch right before you start moving.
  * **Setup change:** Elevate your hands on a sturdy bench or box for your next session to lighten the load on your midsection until your core endurance catches up.
  * **Drill:** Practice a front plank hold on your elbows, focusing on tucking your tailbone slightly under to lock your spine in a flat, neutral line.
  * **Self-check:** Glance at a mirror sideways or record your set on your phone to verify your hips and shoulders rise and fall together without your belly button leading the way.

---

### Partial Range of Motion

* **What it is:** You cut the movement short, only pushing yourself up an inch or two from the bottom (seen on aborted attempts 5, 8, and 10) rather than pressing through a full range.
* **Why it matters:** Stopping short cheats your chest out of the stretch and tension it needs to grow. You miss out on the peak challenge of the exercise, costing you real muscle development for the same amount of effort.
* **How to fix it:**
  * **Cue:** Think about driving your chest away from the floor until your elbows lock out completely at the top.
  * **Setup change:** Reduce the volume of your working sets or take a slightly wider stance to give your upper body a more stable base so you can hit depth on every single rep.
  * **Drill:** Drop to your knees for a set of push-ups to groove the full bottom-to-top path without form breaking down under your full body weight.
  * **Self-check:** Notice if your arms finish fully straight at the top and your chest gets close to the floor on every completed attempt.

---

### Next Session Plan

1. **Prioritize quality over rep count:** Cut your sets shorter (aim for sets of 3 clean reps) to prevent fatigue from dragging your hips down.
2. **Use an incline regression:** Elevate your hands on a stable surface for your warm-up and first working set to guarantee full depth and a flat back before dropping back to the floor.

### WITHOUT RAG
### Progress Tracking

Your overall score dipped slightly from 71 down to 65 this session. Out of 10 total attempts, you completed 4 clean reps and had 6 incorrect ones (including 3 aborted attempts that were cut short). Compared to last time, both of your previous common faults—letting your hips sag or pike and cutting your range of motion short—showed up again. The fatigue really crept in as the set wore on, with form breaking down notably in the second half. Let's lock those hips in and get your depth consistent.

***

### Error Breakdown

*   **What it is, in plain words:** Letting your hips sag toward the floor or pike up toward the ceiling instead of keeping your whole body locked in a straight line from your head to your heels. This happened on reps 3, 5, 6, 9, and 10, clustering heavily as you got tired toward the end of the set.
*   **Why it matters:** Your lower back and midsection take the extra stress instead of your chest and shoulders doing the heavy lifting. That means you'll feel it as a dull ache in your lower back rather than a good chest pump, it robs you of your power output, and it places your spine in a compromised position as the weight and fatigue increase.
*   **How to fix it:** 
    *   *(a) Cue:* Squeeze your glutes hard and brace your abs like someone is about to poke you in the stomach.
    *   *(b) Setup:* Drop your knees to the floor for a quick reset if you feel your hips starting to sag, or slow down your tempo to maintain full-body tension before you initiate the descent.
    *   *(c) Drill:* Practice plank holds on the floor to build the core endurance needed to keep your hips from dropping.
    *   *(d) Self-check:* Glance at a mirror sideways or set your phone up to record—if your hips drop below the line of your shoulders and ankles, you've lost the tension.

*   **What it is, in plain words:** Not pushing deep enough or cutting your reps short before your chest gets close to the floor. This cropped up on aborted attempts 5, 8, and 10, where you couldn't finish the movement.
*   **Why it matters:** You miss out on the full stretch and contraction of the chest and triceps, meaning less muscle growth and strength gains for the exact same amount of effort. Over time, it creates a habit of half-reps that won't hold up under heavier training demands.
*   **How to fix it:** 
    *   *(a) Cue:* Think about actively driving the floor away from you and aiming your chest right between your hands at the bottom.
    *   *(b) Setup:* Elevate your hands on a sturdy bench or box if you find yourself unable to hit full depth cleanly on the floor.
    *   *(c) Drill:* Perform slow, controlled eccentric push-ups—lowering yourself to the floor over 3 full seconds, then dropping your knees to push back up.
    *   *(d) Self-check:* Notice if your upper arms break parallel to the floor at the bottom; if your elbows stay high and the drop is shallow, you're cutting it short.

***

### Next Session Plan

1. **Prioritize quality over volume:** Stop your set one or two reps *before* your form starts to break down and your hips start sagging. 
2. **Control your depth:** Treat every single rep as a full range-of-motion movement, and use an elevated surface for your hands if you feel yourself cutting them short due to fatigue.
3. **Rest more between sets:** Give yourself a solid 90 seconds to 2 minutes of recovery so you can approach each set with fresh strength rather than carrying fatigue over and letting your core give out.

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

Your overall score held steady at 71 (up just one point from 70), and your correct rep count matched your previous session at 6. The same persistent issue—short-changing your depth—showed up again today, accounting for all 4 of your incorrect attempts. Notably, every single one of those mistakes came from aborted attempts (reps 3, 5, 7, and 9) where you cut the movement short instead of finishing the descent. 

***

### Error Breakdown: Shallow Lunge

* **What it is:** You're cutting the movement short and turning back up before your hips drop far enough, leaving your front thigh well short of parallel to the floor.
* **Why it matters:** When you don't drop deep enough, your glutes don't fully engage to help stabilize your knee joint. That leaves your quads to soak up a massive spike in force—a shallow front knee bend of 80 degrees forces your quads and knees to shoulder a much harsher workload than the smoother 90 to 100-degree range. That extra stress can catch up to you as nagging knee discomfort and cheats you out of the complete muscle development you're after.
* **How to fix it:**
  * **(a) Cue:** Think about driving your back knee straight down toward the floor rather than lunging forward.
  * **(b) Setup change:** Slow down your descent and pause for a deliberate one-count at the bottom when your back knee is just an inch or two off the ground.
  * **(c) Drill:** Drop the load entirely and practice bodyweight split squats with your rear foot elevated on a low bench to get used to dropping straight down into the deep position.
  * **(d) Self-check:** Glance in the mirror or check your phone video to make sure your front knee hits roughly a 90 to 100-degree bend and your back knee nearly brushes the floor on every working rep.

***

### Next Session Plan

1. **Lower the weight slightly:** Take a small step back in load so you can build the confidence to hit full depth without cutting your attempts short.
2. **Prioritize the pause:** Commit to a clear, controlled bottom position on every single rep—no rushing the turnaround, especially as fatigue sets in later in the set.

### WITHOUT RAG
### Progress Tracking
Let's look at how today stacked up against your last session. Your overall score ticked up slightly from 70 to 71, and you matched your previous count of 6 correct reps. However, you still ran into 4 incorrect reps—specifically, attempts 3, 5, 7, and 8 (wait, let's look at the data: attempts 3, 5, 7, and 9) were all aborted short. The good news is you're holding steady on your clean reps, but that lingering depth issue is still holding you back from a fully green session.

### Error Breakdown

* **What it is, in plain words:** You are cutting your lunges short before your back knee gets close enough to the floor, causing those attempts to abort entirely (seen on attempts 3, 5, 7, and 9). 
* **Why it matters:** When you don't drop down fully into the lunge, your front leg and glutes don't get taken through their full range of motion. That means you miss out on the muscle growth and strength gains you're actually showing up for, while leaving your hips undercooked for the effort you're putting in.
* **How to fix it:** 
  (a) Think about kissing your back knee gently to the floor on every descent.
  (b) Shorten your stride slightly or reduce the weight so you have the control to drop your hips straight down instead of drifting forward.
  (c) Practice bodyweight split squats with a soft pad or mat under your back knee so you have a physical target to touch every single time.
  (d) Glance at a side-profile mirror or check your phone video to confirm your back knee is hovering just an inch above the ground at the bottom of the movement.
  *Note on rep detail:* Notice how all your aborted attempts happened in the second half of the set (attempts 3, 5, 7, and 9)? That tells us fatigue is setting in and robbing you of your depth. 

### Next Session Plan
1. **Stop the set a rep or two earlier:** Since your depth starts failing on odd-numbered attempts as fatigue builds, cut your set off right before your form starts breaking down instead of grinding out sloppy, shallow attempts.
2. **Use a depth target:** Place a small yoga block or folded mat where your back knee should touch to keep yourself honest on every single repetition.
3. **Pace your breathing:** Take a deliberate breath and brace your core before you step back or forward, ensuring you have the stability to control the full descent to the bottom.

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

Good work staying consistent—your overall score ticked up from 73 to 76 today, and you locked in 6 clean reps just like last time. The same issue, short-changing your range of motion, popped up again on reps 4, 6, and 8, and cut your final attempt (rep 9) short before you even reached the top. You are holding your baseline, but the fatigue in the back half of the set is making you cut your reps short. 

### Error Breakdown

*   **What it is:** You are cutting your reps short by stopping the bottom of the movement early instead of fully straightening your arms, and freezing up before you get the weight all the way up to your shoulders. 
*   **Why it matters:** Skipping the bottom stretch means your biceps miss out on the tension they need to grow, leaving you with less muscle growth for the exact same amount of effort. Plus, failing to control the full range of motion bumps up your risk of picking up an injury over time.
*   **How to fix it:** 
    *   *Cue:* Touch all the way down to a dead straight arm at the bottom, and squeeze hard at the top before you head back down.
    *   *Setup change:* Drop the weight slightly on your next session so you aren't forced to truncate the movement just to finish the set.
    *   *Drill:* Practise lighter single-arm dumbbell curls in front of a mirror, pausing for a full second at both the very bottom (arm completely straight) and the very top.
    *   *Self-check:* Watch a quick video of your set—if your elbows are still bent when you start curling back up, you are starting too high.
*   **Rep detail note:** This error clustered entirely in the second half of your set—reps 4, 6, 8, and the aborted rep 9 all suffered from this. As fatigue sets in, you are rushing the bottom of the rep.

### Next Session Plan

1. **Lighten the load slightly:** Drop the weight by a small increment for your next bicep session so you can handle a full stretch and squeeze on every single rep without cutting corners.
2. **Watch the fatigue zone:** When you hit rep 4 and beyond, mentally check your bottom position—make sure your arms straighten out completely before you start the next pull.

### WITHOUT RAG
### Progress Tracking
Nice work pushing through this session—your overall score ticked up to 76 (compared to 73 last time), and you locked in 6 clean, solid reps just like you did yesterday. You held onto the exact same number of correct reps, but that persistent partial curl issue from your last session showed up again, landing on reps 4, 6, 8, and cutting attempt 9 short before it even counted. Let's get that range of motion locked in so every single rep counts.

---

### Error Breakdown

* **What it is, in plain words:** You're cutting the top of the movement short instead of curling the weight all the way up to your shoulders.
* **Why it matters:** When you cut the range of motion short, your biceps miss out on the peak contraction where they actually do their hardest work. That means you are shortchanging your muscle growth for the exact same amount of effort, leaving gains on the table and letting momentum take over.
* **How to fix it:**
  * (a) **Cue:** Think about driving your pinkies toward your shoulders at the very top of each rep.
  * (b) **Setup change:** Drop the weight slightly so you aren't fighting a load that forces you to cheat the top half of the movement.
  * (c) **Drill:** Practice lighter dumbbell curls seated on a bench to lock your torso in place and force a full squeeze at the top.
  * (d) **Self-check:** Watch your phone video and make sure your forearms get past parallel to the floor—and close to vertical—before you start the way back down.
  * *Note on rep detail:* This fault crept in as fatigue set in during the later half of the set (reps 4, 6, 8) and finally caused attempt 9 to abort entirely. Drop the weight or stop your set a rep earlier before form breaks down.

---

### Next Session Plan

1. **Drop the weight slightly:** Take a small step down on your load so you can hit a full range of motion on every single rep without cutting the top short.
2. **Watch the fatigue wall:** Pay attention to when your form starts slipping—around rep 4 or 5—and focus intensely on squeezing hard at the top rather than just moving the weight.
3. **Film a quick set:** Set your phone up to check your top position, making sure your forearms are coming all the way up on every rep.

---


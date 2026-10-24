# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions_squat.json` |
| query mode | **taxonomy** — `error_type` resolved through `error_taxonomy.py` |
| collection | `kb_gemini_curated_v6` |
| LLM | `gemini-3.5-flash-lite` @ temperature 0.7 |
| no-RAG side | run |
| samples per session | 3 |
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

## Exercise: Squat — partial_squat

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| partial_squat | Squatting too shallow: stopping the descent early in a half or quarter squat, so the thighs stay well above parallel and the knees never reach a 90-degree bend (+why/fix) | 0.062 / 2* | 0.185 / 2* | 0.160 / 2* | 0.174 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: partial_squat | source: TheBackSquatAProposedAssessment]
Squatting too shallow, where the athlete does not achieve a depth where the tops of the thighs are at least parallel to the ground.

[mistake | re: partial_squat | source: Kim2015_HipAnkleROM_SquatDepth_JHumKinet]
Limiting squat depth (stopping early in a partial squat) due to restricted ankle dorsiflexion or hip mobility.

[consequence | re: partial_squat | source: TheBackSquatAProposedAssessment]
Without squatting to the proper depth, the hamstrings and gluteus muscular complex may not be adequately challenged.

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

### WITH RAG (sample 1/3)
### Progress Tracking
You matched your previous overall score of 72 and kept your correct rep count at 5 out of 10. The good news is you completely cleared rounded back from your last session—that error is gone. However, you are still running into the exact same depth issue, which showed up on reps 3, 6, 8, 10, and caused your attempt on rep 9 to cut short and abort before finishing.

### Error Breakdown

*   **What it is:** You are cutting your squats short instead of sinking down until the tops of your thighs drop to at least parallel with the floor, often happening because tight ankles or hips put the brakes on your descent.
*   **Why it matters:** When you stay high, your glutes and hamstrings don't get fully challenged, meaning you miss out on the muscle growth you came for. At the same time, stopping short can put higher compressive forces directly on your knee joints, leaving you with extra stress on your knees and less muscle built for your effort.
*   **How to fix it:** 
    *   *Cue:* Think about driving your hips down and back between your knees until your hip joint drops level with or slightly below your knees.
    *   *Setup change:* Take a slightly wider stance or slow down your descent so you have time to settle into the bottom position.
    *   *Drill:* Practice bodyweight box squats to a parallel target so you can feel the correct depth before loading up the bar again.
    *   *Self-check:* Set your phone up to record a side-view video and check whether the crease of your hip dips below the top of your knee at the bottom.

### Next Session Plan
*   **Fix your depth early:** Drop the weight slightly for your warm-up sets to focus purely on hitting that parallel depth on every single rep without cutting corners as fatigue sets in.
*   **Manage your fatigue:** Since your depth started failing in the second half of the set (reps 6, 8, 10, and the aborted rep 9), stop your working sets a rep or two earlier to keep your form locked in.

### WITH RAG (sample 2/3)
### Progress Tracking
Let's look at how you did compared to yesterday. Your overall score held steady at 72, and you matched your previous count with 5 correct reps and 5 incorrect reps out of 10 total attempts. The great news is that you completely cleared the rounded back error from your previous session—that's a huge win for your spine stability. However, your old habit of cutting your depth short (partial squat) is still hanging around, popping up on reps 3, 6, 8, 10, and causing attempt 9 to abort entirely as you cut the descent short. 

### Error Breakdown

*   **What it is, in plain words:** You are cutting your squats short and turning back up before your thighs reach parallel to the floor—your knees are only bending to about a 90-degree angle instead of sinking into the full depth of the movement.
*   **Why it matters:** When you don't drop your hips all the way down, your glutes and hamstrings don't get fully challenged, meaning you miss out on real muscle growth and strength gains in the back of your legs. Plus, stopping high puts extra compressive force straight into your knee joints.
*   **How to fix it:** 
    *   *Cue:* Think about opening your hips and sinking your glutes down between your heels as you reach the bottom.
    *   *Setup change:* Widen your stance slightly or spend an extra 5 minutes opening up your ankles and hips before you touch a barbell.
    *   *Drill:* Drop the weight completely and use a box or a bench set at parallel to pause on for two seconds at the bottom of each rep.
    *   *Self-check:* Set up your phone to record your profile—at the bottom of your rep, your hip crease should drop level with or slightly below the top of your knee.

### Next Session Plan
1. **Target depth first:** Keep the weight moderate for your next workout so you can focus entirely on hitting full depth on every single rep without fighting for survival.
2. **Watch the fatigue:** Notice how your depth started slipping on reps 6, 8, 10, and aborted on 9? Fatigue is making you cut corners. Stop your working sets one rep *before* your form starts to break down.

### WITH RAG (sample 3/3)
### Progress Tracking
You matched your previous outing overall: your score stayed locked at 72, with 5 clean reps and 5 incorrect reps. The good news is you completely cleared rounded back off your list—that error didn't show up once today. Your main hurdle now is depth, which carried over from last time and popped up on reps 3, 6, 8, and 10, plus your aborted attempt on rep 9. 

### Error Breakdown

* **What it is:** You are cutting your squats short instead of sinking down until the tops of your thighs sit at least parallel to the floor, often driven by tight ankles or hips.
* **Why it matters:** When you don't drop down far enough, your glutes and hamstrings don't get properly challenged, meaning you miss out on real muscle growth for your backside. At the same time, stopping high places extra compressive pressure on your knees.
* **How to fix it:** 
  * (a) **Cue:** Think about driving your hips back and down between your heels as you descend, aiming to drop your hip crease level with or slightly below your knee.
  * (b) **Setup:** Take a slightly wider stance or elevate your heels on small plates to compensate for ankle mobility limits so you can get down cleanly.
  * (c) **Drill:** Practice bodyweight box squats to a low target that forces you to hit proper depth before standing back up.
  * (d) **Self-check:** Set up your phone from the side and look for the 90-degree bend in your knees where your thighs run parallel to the ground.

### Next Session Plan
* **Drop the load slightly:** Take 5-10% off the bar for your next session so you can focus entirely on hitting full depth without grinding.
* **Watch the fatigue:** Your depth issues started creeping in on the second half of the set (reps 6, 8, 9, and 10), so focus on keeping your form tight as fatigue sets in, or cut the set a rep earlier before your form breaks down.

### WITHOUT RAG (sample 1/3)
### Progress Tracking

Your overall score came in at 72, which matches your last session exactly. You locked in 5 correct reps today, just like last time, but you still ran into trouble with 5 incorrect reps. The good news: your rounded back from the previous workout is completely gone, which means your torso stayed strong and supported. The challenge today was depth—your only remaining issue is cutting your reps short before hitting the bottom.

***

### Error Breakdown: Partial Squat

*   **What it is:** You are turning back up before your hips drop below the level of your knees, meaning you are cutting the bottom of the movement short. Notice how this crept in as fatigue set in—it hit you on reps 3, 6, 8, and 10, and completely cut your movement short on attempt 9.
*   **Why it matters:** When you cut the depth short, your quads and glutes miss out on the full stretch and workload they are supposed to handle. That costs you muscle growth and strength gains for the exact same amount of effort, and it leaves you practicing an incomplete movement pattern.
*   **How to fix it:** 
    *   (a) Cue: Think about "spreading the floor" with your feet and sinking your hips straight down between your heels as you descend.
    *   (b) Setup change: Drop the weight slightly on your next session so you can control the descent all the way to the bottom without rushing the turnaround.
    *   (c) Drill: Practice a box squat to a parallel box, pausing for one full second on the box to build comfort in the bottom position before standing back up.
    *   (d) Self-check: Set your phone up to record a side-view video and check that the crease of your hip drops clearly below the top of your knee cap before you start your ascent.

***

### Next Session Plan

1. **Drop the load slightly:** Take about 5-10% off the bar for your next squat session so you can hit full depth cleanly without fighting for every inch.
2. **Focus on fatigue management:** Since your depth errors started showing up later in the set (reps 6, 8, and 10) and led to an aborted attempt on 9, consider cutting your working sets one rep short of failure next time to keep your form pristine.

### WITHOUT RAG (sample 2/3)
### Progress Tracking

Your overall score held steady at 72, matching your previous session, and you successfully nailed 5 clean reps. Good news on the upper body front: you completely cleared out the rounded back issue from last time. The main hurdle today is depth, which showed up as partial squats on reps 3, 6, 8, and 10, plus an aborted attempt on rep 9 where you cut the descent short. 

***

### Error Breakdown

*   **What it is, in plain words:** You're cutting your squats short and turning back up before your hips drop below the level of your knees.
*   **Why it matters:** When you don't hit full depth, your quads and glutes miss out on the deep stretch that drives real muscle growth, meaning you're working hard without getting the full payoff for your effort.
*   **How to fix it:** 
    *   *(a) Cue to think about:* Think about sitting down and back between your heels until your thighs break parallel with the floor.
    *   *(b) Setup change:* Set a box or a height-adjustable bench just below parallel behind you to serve as a physical target for your hips to lightly touch on every rep.
    *   *(c) Drill or regression:* Drop the weight by twenty percent and practise pause squats, holding the bottom position for a full two seconds before standing back up.
    *   *(d) Self-check:* Set your phone up side-on and watch the playback to confirm your hip crease clearly drops below the top of your knee cap before you drive up.
*   **Rep detail note:** This depth drop-off crept in during the second half of the set (reps 3, 6, 8, 10, and the aborted rep 9). That's a classic sign of fatigue setting in, so your legs are getting tired and calling it quits early.

***

### Next Session Plan

1. Drop the working weight slightly next time so you have enough in the tank to hit proper depth on every single rep without grinding.
2. Keep your focus on that bottom position—use a box or bench target on your warm-up sets to lock in the correct depth before you load the bar.
3. If fatigue starts making your depth shallow in the back half of your sets like it did today, cut the set short a rep or two early rather than cutting the depth short.

### WITHOUT RAG (sample 3/3)
### Progress Tracking

Your overall score came in at 72, which matches your previous session exactly. You locked in 5 correct reps today, just like last time, but you still ran into trouble with 5 incorrect attempts. The good news is that you completely cleared the rounded back issue from your last workout—that error is gone. However, cutting your depth short continues to hold you back, appearing on reps 3, 6, 8, 9, and 10, with attempt 9 cutting short enough that it aborted entirely.

---

### Error Breakdown: Partial Squat

*   **What it is:** You are cutting the movement short and heading back up before your hips drop below the level of your knees.
*   **Why it matters:** Your quads and glutes miss out on the full stretch and workload they need to grow, meaning you're doing hard work for a diminished return in muscle development. As you start loading heavier weights, this habit makes it harder to build consistent power out of the bottom hole, and you'll feel like you're stalling out prematurely.
*   **How to fix it:** 
    *   (a) Cue: Think about actively pulling your hips down between your ankles before you reverse direction.
    *   (b) Setup change: Widen your stance just a fraction or slightly turn your toes out to open up the hip room needed for full depth.
    *   (c) Drill: Set up a box or a target bench just below parallel behind you and lightly touch it on every rep to confirm your depth before driving back up.
    *   (d) Self-check: Record your set from the side and watch to see if the crease of your hip clearly drops past the top of your kneecap at the bottom.
*   **Rep detail note:** Notice how this fault only creeps in later in the set (reps 3, 6, 8, 9, and 10, with rep 9 aborting completely). As fatigue sets in, you're losing your patience at the bottom.

---

### Next Session Plan

1.  **Drop the fatigue threshold:** Stop your sets one rep *before* your depth starts breaking down so you practice successful movement patterns instead of grinding out shallow reps.
2.  **Use a depth target:** Place a box or bench behind you for your working sets to guarantee you hit the correct depth every single rep.
3.  **Control the descent:** Slow down your lowering phase slightly on the later reps of your set to keep your positions locked in when fatigue hits.

---

## Exercise: Squat — knee_valgus

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| knee_valgus | Knees caving in as the lifter squats: one or both knees collapsing inside the feet while lowering or rising (dynamic knee valgus, medial knee displacement) (+why/fix) | 0.045 / 3* | 0.130 / 2* | 0.115 / 2* | 0.095 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: knee_valgus | source: Bell2013_KneeValgusReducedAfterExercise_Squat_JAthlTrain]
Allowing the knees to cave inward (medial knee displacement or knee valgus) during a squat.

[mistake | re: knee_valgus | source: Bell2013_KneeValgusReducedAfterExercise_Squat_JAthlTrain]
Allowing the knees to cave inward, known as dynamic knee valgus or medial knee displacement, during the descent or ascent of a squat.

[principle | re: knee_valgus | source: TheBackSquatAProposedAssessment]
During the squat, the lateral aspect of the knee should not cross the vertical plane of the medial malleolus to avoid medial displacement.

[mistake | re: knee_valgus | source: Bell2013_KneeValgusReducedAfterExercise_Squat_JAthlTrain]
Allowing the knees to cave inward (medial knee displacement or dynamic knee valgus) during squatting movements.

[consequence | re: knee_valgus | source: basics_of_strength_and_conditioning_manual]
Allowing the knees to come together (valgus knee position) increases the strain on the ligaments and muscles surrounding the knee.

[finding | re: knee_valgus | source: Bell2013_KneeValgusReducedAfterExercise_Squat_JAthlTrain]
Visual knee valgus is clinically defined during a double-legged squat screening when the midpoint of the patella passes medial to the great toe in 3 out of 5 trials.

[principle | re: knee_valgus | source: Papadakis2024_BackSquatErrors_NeutralSpineKneeAlignment_JFMK]
Proper coaching cues, such as 'knees out', and the use of resistance bands can assist in reinforcing correct knee alignment.

[consequence | re: knee_valgus | source: blog.nasm.org/newletter/squat-form]
Over-pronation of the foot can lead to dynamic knee valgus during the squat.

[finding | re: knee_valgus | source: Papadakis2024_BackSquatErrors_NeutralSpineKneeAlignment_JFMK]
Knee joint genu valgus during squats is associated with reduced height of the lateral meniscus, decreased hip abductor performance (gluteus maximus and medius), increased femoral anteversion, internal rotation of the tibia, and decreased ankle inversion muscles (tibialis anterior and posterior).
```

### WITH RAG (sample 1/3)
### Progress Tracking
Good effort out there today. Your overall score ticked up slightly from 74 to 76, and you matched your previous performance with 6 fully clean reps out of 10. The same persistent issue—knees caving inward—showed up again in this session, appearing on reps 4, 6, 8, and 10. Notice how this fault only crept in during the second half of the set as fatigue set in, while your early reps stayed solid.

---

### Error Breakdown

*   **What it is, in plain words:** As you push through the middle and bottom of the squat, your knees drift inward toward each other instead of tracking straight out over your toes. 
*   **Why it matters:** This puts extra stress on the ligaments and muscles around the knee joint while dampening the power coming from your outer hip muscles. Over time, you'll feel this as nagging knee discomfort or tightness around the joint caps, and it robs you of leg drive when you try to stand back up with heavy weight.
*   **How to fix it:** 
    *   (a) *Cue:* Think "knees out" and actively push your knees wide to match your toe angle on every descent.
    *   (b) *Setup:* Place a light resistance band just above your knees during your warm-up sets to force your outer hips to turn on.
    *   (c) *Drill:* Do a few sets of bodyweight box squats with a band around your knees, pausing for a two-second count at the bottom to build positional strength.
    *   (d) *Self-check:* Watch yourself in the side-front mirror and make sure your kneecaps stay directly in line with your big toes from top to bottom.

---

### Next Session Plan
1.  **Wrap a band for warm-ups:** Put a mini resistance band around your knees for your first two warm-up sets to wake up your glutes and anchor your knee tracking early.
2.  **Cut the set short if form slips:** Since your knees held strong for the first three reps before caving on rep 4, cap your working sets at 3 clean reps today. Build your endurance gradually rather than grinding out sloppy reps under fatigue.
3.  **Check your foot stance:** Make sure your feet aren't rolling inward on the floor, as a collapsing arch often triggers the knees to dive inward. Keep your whole foot planted flat.

### WITH RAG (sample 2/3)
### Progress Tracking

Good to see some upward movement since yesterday. Your overall score ticked up from 74 to 76, and your clean rep count held steady at 6 out of 10. The same old issue—your knees caving in—showed up again, carrying over from your previous session on reps 4, 6, 8, and . Notice how those faults cluster in the second half of the set (reps 4 through 10)? That tells us fatigue is creeping in and your form is starting to leak as you get tired.

***

### Error Breakdown

*   **What it is:** Your knees are caving inward toward each other instead of tracking straight out over your toes as you squat down and push back up.
*   **Why it matters:** When your knees drift inward, it piles extra strain onto the ligaments and muscles around the knee joint. Over time, that reduces how well your outer hip muscles (the glutes) can fire and chips away at your power output, leaving your knees vulnerable to aches and strains as the weight goes up.
*   **How to fix it:**
    *   (a) *Cue:* Think "knees out" or drive your feet apart against the floor on every single rep.
    *   (b) *Setup change:* Loop a light resistance band just above your knees during your warm-up sets to force those outer hips to wake up and keep your knees tracking properly.
    *   (c) *Drill:* Drop the load and pause for two seconds at the bottom of a lighter set to anchor your knee position before standing back up.
    *   (d) *Self-check:* Watch yourself in the mirror and make sure your knees stay directly in line with your big toes throughout the whole movement, without drifting inside that line.

***

### Next Session Plan

1.  **Lead with a band warm-up:** Spend a few minutes doing bodyweight squats with a resistance band around your knees to hardwire that outward tracking before you load the bar.
2.  **Cut the set short if form slips:** Since your knee cave only happens in the back half of the set (reps 4, 6, 8, and 10), drop the total reps per set or lower the weight slightly so you can finish every single rep with clean form.

### WITH RAG (sample 3/3)
### Progress Tracking
Good effort out there today. Your overall score ticked up slightly from 74 to 76, and you matched your previous performance by hitting 6 clean, solid reps. You are still dealing with the same issue from your last session—knees caving inward—and it popped up on 4 of your reps (reps 4, 6, 8, and 10). Notice how they didn't show up right away? The breakdown is happening exclusively in the second half of the set as fatigue sets in. 

---

### Error Breakdown

* **What it is, in plain words:** As you push up or lower down, your knees drop and pinch inward toward each other instead of tracking directly over your feet.
* **Why it matters:** This puts extra stress on the ligaments and muscles around the knee joint while also cutting into the power of your glutes and hip strength. When your knees cave under heavy weight, you leak force, meaning you miss out on muscle growth and leave yourself vulnerable to joint discomfort as the loads go up.
* **How to fix it:** 
  * (a) **Cue:** Think "knees wide" or drive your feet outward into the floor as you stand.
  * (b) **Setup change:** Loop a light resistance band just above your knees during your warm-up sets to force your outer hips to wake up.
  * (c) **Drill:** Practice bodyweight squats with that band on, pausing for a two-second hold at the bottom to actively keep your knees pushed out against the tension.
  * (d) **Self-check:** Film your set from the front—your knees should stay in line with your toes the whole time, and the midpoint of your kneecap should never drift inside your big toe.

---

### Next Session Plan
1. **Cut the set short before form breaks:** Since your knees only started collapsing on the later reps (4, 6, 8, and 10), stop your working sets a rep or two before fatigue makes your technique sloppy. Quality over junk volume.
2. **Use the band warm-up:** Spend five minutes before your first working set doing banded squats to prime your outer glutes and lock in the right knee tracking early.

### WITHOUT RAG (sample 1/3)
### Progress Tracking

Great to see your overall score tick up slightly from 74 to 76 today, and you matched your previous count of 6 clean, correct reps out of 10. You also managed to clear out any other errors that might have lingered, leaving just one recurring habit to clean up. Your knees caved inward on reps 4, 6, 8, and 10—noticing how that pops up in the second half of the set tells us fatigue is starting to compromise your form as you get deeper into the work.

---

### Error Breakdown

*   **What it is:** Your knees are collapsing inward toward each other instead of tracking out in line with your toes as you drive up out of the bottom of the squat.
*   **Why it matters:** This forces your knees and hips to absorb the load at an awkward angle, throwing extra stress onto the inside of your knee joints. That means you are leaking power right when you need it most to stand back up, and as the weight on the bar gets heavier, it sharply increases the risk of nagging joint discomfort.
*   **How to fix it:** 
    *   (a) Cue: Think about actively spreading the floor apart with your feet as you push up.
    *   (b) Setup: Bring your stance in slightly or adjust your toe angle outward by a few degrees to find a more stable base.
    *   (c) Drill: Loop a light resistance band just around your knees during your warm-up bodyweight squats to force your outer glutes to wake up and keep your knees tracking straight.
    *   (d) Self-check: Watch your phone video and look for your knees staying wide and tracking directly over your second toe from the bottom all the way to lockout.

---

### Next Session Plan

1. **Beat the fatigue fade:** Since your knees started caving inward on the later reps (4, 6, 8, and 10), focus extra hard on keeping your knees pushed out when you start getting tired in the second half of your working sets. 
2. **Use warm-up bands:** Spend a few minutes doing bodyweight squats with a mini-band around your knees before you touch a barbell to lock in that outward-pushing habit early.
3. **Rest adequately:** Take a full two minutes between your working sets to make sure your legs are fresh enough to hold your form together from the first rep to the last.

### WITHOUT RAG (sample 2/3)
### Progress Tracking
Let’s look at how today stacked up against your last session on October 2nd. Your overall score ticked up slightly from 74 to 76, and you matched your previous count of 6 correct reps out of 10 total attempts. More importantly, check out the error list: last time, multiple issues held you back, but today you've completely cleared everything except for one stubborn habit: knees collapsing inward. That is real progress on cleaning up your movement—now we just need to lock down that last piece.

***

### Error Breakdown

* **What it is, in plain words:** Your knees are caving inward toward each other instead of tracking straight out over your toes, especially showing up as fatigue sets in on reps 4, 6, 8, and 10.
* **Why it matters:** When your knees drop inward, extra stress gets dumped right onto your knee joints rather than letting your quads and glutes handle the load. That means you miss out on full muscle growth, and as the weight gets heavier, it sets you up for sharp joint aches right around the kneecap. 
* **How to fix it:** 
  * (a) Think about actively spreading the floor apart with your feet as you push back up.
  * (b) Narrow your stance by just an inch or turn your toes out slightly to find a more stable base.
  * (c) Loop a light resistance band just above your knees during your warm-up sets to force your outer hips to turn on.
  * (d) Glance in the mirror and make sure your kneecaps track directly over the middle of your feet on every single rep.

***

### Next Session Plan
1. **Focus on the finish:** Since your knee collapse showed up on the later reps (4, 6, 8, and 10), watch your form closely as you tire, and don't be afraid to cut the set short before your form breaks down.
2. **Warm up with bands:** Spend a few minutes doing bodyweight squats with a mini-band around your knees to wake up your glutes before touching any heavy weight.

### WITHOUT RAG (sample 3/3)
### Progress Tracking
Let’s look at the numbers from yesterday to today: your overall score nudged up slightly from 74 to 76, and you matched your previous count of 6 correct reps out of 10. The good news is you kept the total error count at 4, but that lingering knee caving issue we saw last session showed up again on reps 4, 6, 8, and 10—so fatigue is likely setting in late in the set and pulling your knees inward as you push back up.

### Error Breakdown

*   **What it is, in plain words:** Your knees are caving inward toward each other instead of tracking straight out in line with your toes, particularly when you start driving back up from the bottom of the squat.
*   **Why it matters:** When your knees buckle inward, your inner thighs and knees take a beating to compensate for your glutes checking out, which costs you raw power out of the hole and leaves your joints vulnerable to twisting forces as the weight gets heavier.
*   **How to fix it:** 
    (a) Cue: Think about "screwing your feet into the floor" and actively pushing your knees outward against an imaginary band throughout the entire lift. 
    (b) Setup change: Narrow your stance slightly or point your toes out a couple of degrees more to give your hips a more natural track. 
    (c) Drill: Loop a light resistance band just above your knees during your warm-up sets to force your glutes to stay switched on and push outward against the pull. 
    (d) Self-check: Keep a phone camera angled slightly from the front so you can watch whether your kneecaps stay tracking directly over your second toe on every single rep.

### Next Session Plan
1. **Manage your fatigue:** Since your knees started collapsing on the later reps (4, 6, 8, and 10), cut your working sets a rep or two short of breakdown today to groove clean movement.
2. **Band your warm-ups:** Spend two minutes doing bodyweight squats with a mini-band around your knees before touching the barbell to wake up the outer glutes.
3. **Check the video:** Film your heaviest set from the front and verify your knees stay stable as you drive out of the bottom position.

---

## Exercise: Squat — knee_varus

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| knee_varus | Knees splaying outward during the squat: driving the knees apart until they track outside the little toes in a V shape, often with the toes turned out too much (+why/fix) | 0.058 / 3* | 0.153 / 2* | 0.145 / 2* | 0.089 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: knee_varus | source: Kim2015_HipAnkleROM_SquatDepth_JHumKinet]
Allowing the knees to align outside the hips (knee varus) during the squat.

[principle | re: knee_varus | source: Lorenzetti2018_HowToSquat_StanceFootAngle_BMCSSMR]
The knees should track over the toes throughout the squat motion without knee displacement either medially or laterally.

[mistake | re: knee_varus | source: Lorenzetti2018_HowToSquat_StanceFootAngle_BMCSSMR]
Excessive mediolateral movement of the knees (medial or lateral knee displacement) is a common deficit during the squat.

[mistake | re: knee_varus | source: Lorenzetti2018_HowToSquat_StanceFootAngle_BMCSSMR]
Allowing the knees to displace medially or laterally during the squat motion.

[consequence | re: knee_varus | source: Kim2015_HipAnkleROM_SquatDepth_JHumKinet]
Faulty alignment patterns, such as mediolateral rotation of the hip and knee alignment inside or outside the hip during the squat, induce increases in the compressive and shear forces at the ankle, knee, and hip joints.

[finding | re: knee_varus | source: Lorenzetti2018_HowToSquat_StanceFootAngle_BMCSSMR]
Novice squatters showed a higher knee deviation (ΔD*) compared to experienced squatters, who performed squats in all positions with a ΔD* closer to 0 except in the wide stance with 0° foot angle (WS-0°) position.

[consequence | re: knee_varus | source: Lorenzetti2018_HowToSquat_StanceFootAngle_BMCSSMR]
A tendency towards varus limb alignment during the squat causes greater stretching of the lateral collateral ligament (LCL) than the medial collateral ligament (MCL).

[principle | re: knee_varus | source: TheBackSquatAProposedAssessment]
The knees should track over the toes throughout the squat motion, maintaining a neutral frontal plane knee position without medial or lateral displacement.

[finding | re: knee_varus | source: Lorenzetti2018_HowToSquat_StanceFootAngle_BMCSSMR]
Novice squatters without additional weight tend towards a more varus alignment, while experienced squatters showed a lower mediolateral movement.
```

### WITH RAG (sample 1/3)
### Progress Tracking

You held steady on your clean reps with 6 correct today, matching your output from yesterday, and your overall score ticked up slightly from 75 to 77. That stubborn knee wobble from your last session is still hanging around, showing up on reps 2, 5, 8, and 10. The good news is you are completely cleaning it up on the alternate reps, so we just need to stitch that consistency together for the whole set.

### Error Breakdown

*   **What it is:** Your knees are bowing outward away from your toes instead of tracking straight ahead as you squat.
*   **Why it matters:** This weird alignment forces extra compressive and shear stress right through your ankle, knee, and hip joints, while throwing a heavy stretch across the outside ligament of your knee. If you keep letting your knees flare out sideways under heavier weights, those joints will start aching post-workout, and you are leaking power that should be driving you straight back up.
*   **How it is fixed:** 
    *   (a) *Cue:* Think about actively driving your knees directly in line with your toes on the way up and down.
    *   (b) *Setup change:* Try narrowing your stance slightly or adjusting your toe angle by a couple of degrees so your knees naturally track forward without drifting.
    *   (c) *Drill:* Loop a light resistance band around your thighs just above your knees during a bodyweight warmup squat to force those muscles to keep your legs tracking straight.
    *   (d) *Self-check:* Set your phone up to record a front-view video and watch whether your knees stay locked over your toes or push outward as you stand.

### Next Session Plan

*   Keep your working weight right where it is, but pause for a full one-second hold at the bottom of reps 2, 5, 8, and 10 to check your knee alignment before driving back up.
*   Drop your total rep count per set down to 8 clean reps if form starts breaking down on those later attempts like it did today.

### WITH RAG (sample 2/3)
### Progress Tracking
You finished today's session with an overall score of 77, a slight step up from your 75 last time. You landed 6 correct reps, matching your previous count, and kept your incorrect rep count steady at 4. The same old habit—allowing your knees to drift outward away from your toes—showed up again on reps 2, 5, 8, and 10. While your clean reps look solid, that recurring drift on the later reps is what's holding your score back.

### Error Breakdown

*   **What it is:** Your knees are flaring or pushing outward outside of your hip and toe alignment as you squat down and drive back up, rather than tracking straight over your feet.
*   **Why it matters:** This misalignment spikes the compressive and shear forces hitting your ankle, knee, and hip joints while throwing extra stretch onto the outer ligaments of your knee. Over time, that translates to nagging joint friction and soreness around your hips and knees after a heavy session, draining power out of your drive and wearing down your joints instead of building the muscle.
*   **How to fix it:**
    *   *(a) Cue to think about:* Drive your knees directly in line with your second toe on every single inch of the way down and up.
    *   *(b) Setup change:* Narrow your stance slightly or adjust your foot angle so your knees naturally track straight ahead without needing to force them wide.
    *   *(c) Drill or regression:* Pause for a full two seconds at the bottom of a lighter bodyweight squat to lock your knee alignment in place before standing.
    *   *(d) Self-check:* Glance at a mirror or record a video from the front to see if your knees stay glued on top of your toes or wander outward as you fatigue. Notice how this tended to happen on your later reps (8 and 10), so stay extra sharp on your breathing and bracing as you get tired.

### Next Session Plan
1. **Prioritize mid-set focus:** Since your knee drift tends to creep in during the later reps (like reps 8 and 10), treat every rep in the second half of the set with the same strict focus as your very first one.
2. **Use a tempo pause:** Add a deliberate two-second pause at the bottom of your warm-up sets to build the habit of keeping your knees tracking properly over your toes.

### WITH RAG (sample 3/3)
### Progress Tracking
You finished today's session with an overall score of 77, a slight step up from 75 last time. You landed 6 correct reps, matching your total from your previous session, but your incorrect reps stayed stubbornly at 4. The same old issue—letting your knees bow outward instead of tracking properly—popped up on reps 2, 5, 8, and 10. You are holding your ground on your clean reps, but that consistency slips as fatigue settles into the later stretches of your set.

### Error Breakdown

*   **What it is, in plain words:** On reps 2, 5, 8, and 10, your knees flared outward away from your toes instead of tracking in line with them as you moved.
*   **Why it matters:** This misalignment jacks up the compressive and shear forces hitting your ankle, knee, and hip joints while putting extra stretch on your outer collateral ligament compared to the inner one. As the weight goes up, that uneven stress means your joints take a pounding they aren't built for, leaving your knees aching and grinding by the time you walk out of the gym.
*   **How to fix it:** 
    *   (a) *Cue:* Think about actively driving your knees forward directly over your toes on every inch of the descent and ascent.
    *   (b) *Setup:* Take a slightly closer stance or adjust your foot angle so your toes point naturally where your knees want to travel.
    *   (c) *Drill:* Loop a light resistance band just above your knees during a bodyweight warm-up set; fighting the band's pull forces your legs to track straight.
    *   (d) *Self-check:* Set your phone up to record a head-on video and watch whether your knees drift outward from your toe line as you hit the bottom of the squat.

### Next Session Plan
*   **Pace your breathing and stance:** Take an extra breath between reps 1 and 6 so you don't rush into the later part of the set where your knee alignment tends to fall apart.
*   **Drop the load for a working buffer:** Knock 10% off your working weight for your first two sets to lock in perfect knee tracking across all 10 reps before adding the heavy plates back on.
*   **Film the back half:** Record your final set specifically to check if reps 8 through 10 are where your form breaks down, and kill the set the second your knees start bowing out.

### WITHOUT RAG (sample 1/3)
### Progress Tracking
Good effort out there. You finished 6 clean reps out of 10 total, bringing your overall score to 77—a slight bump up from 75 in your last session. Your correct rep count stayed steady at 6, and you completely cleared out any other lingering issues from last time except for one stubborn habit that kept showing up.

***

### Error Breakdown

* **What it is:** Your knees caved inward toward each other as you drove up out of the bottom of reps 2, 5, 8, and 10. Notice how this mistake only popped up in the second half of your set as fatigue started to settle in.
* **Why it matters:** When your knees cave inward, your joints and connective tissue take on stress they aren't meant to handle, robbing your quads and glutes of the work. That means you get less muscle growth for the effort, and as the weight on the bar goes up, you risk knee pain or injury.
* **How to fix it:** 
  (a) Cue to think about: Drive your knees out wide toward your pinky toes the entire time you are pushing up.
  (b) Setup change: Take a fraction of a second to pause at the very bottom of each rep to kill any momentum before you drive back up, and consider dropping the weight slightly if your knees still buckle.
  (c) Drill or regression: Loop a light resistance band around your thighs just above your kneecaps during your warm-up sets; pushing out against the band will wake up the exact muscles needed to keep your knees tracking properly.
  (d) Self-check: Watch your phone video and check if your knees stay in line with your toes from top to bottom, or glance in the mirror and make sure they never drift inside that imaginary line.

***

### Next Session Plan
1. **Pace your reps:** Because your knee collapse only happened on the later reps (2, 5, 8, and 10), make sure you aren't rushing. Take a deliberate breath between reps to keep your form tight.
2. **Band warm-ups:** Spend two minutes doing bodyweight squats with a resistance band around your thighs before loading up the barbell to groove the correct knee tracking.
3. **Keep the focus:** Hang onto the 6 clean reps you nailed today, and use your setup to actively lock your knee path in place so those later reps stay just as sharp.

### WITHOUT RAG (sample 2/3)
### Progress Tracking

Good effort today. You matched your previous score on correct reps, landing 6 clean ones just like last time, and nudged your overall score up slightly from 75 to 77. The good news is you completely cleared any other issues from your history, leaving just one recurring habit to clean up.

### Error Breakdown

*   **What it is:** Your knees are caving inward toward each other instead of tracking out in line with your toes, which happened specifically on reps 2, 5, 8, and 10 as fatigue started to settle in toward the middle and end of your set.
*   **Why it matters:** This forces your knees and ankles to soak up rotational stress they aren't built to handle easily, robbing your glutes of the power they should be contributing. That means you are leaking strength out of the bottom of the lift, missing out on full muscle growth in your legs, and inviting joint discomfort as the weight gets heavier.
*   **How to fix it:**
    *   (a) Think about actively spreading the floor apart with your feet as you push back up.
    *   (b) Turn your toes out just a fraction more in your setup and keep your stance width consistent.
    *   (c) Loop a light resistance band just above your knees during your warm-up bodyweight squats to force your outer hips to turn on.
    *   (d) Watch your knees in the mirror or on your phone video to make sure they track directly over your middle toes from the bottom all the way to the top.

### Next Session Plan

*   **Spot the fatigue:** Since your knees started buckling on the later reps (2, 5, 8, and 10), cut your working sets a rep or two short before form starts to break down.
*   **Band warm-ups:** Spend two minutes doing banded bodyweight squats before touching a loaded barbell to wake up your outer glutes.
*   **Keep the tempo honest:** Slow your descent slightly on every rep so you have time to consciously keep your knees tracking outward under control.

### WITHOUT RAG (sample 3/3)
### Progress Tracking

Good to see you back on the bar. You matched your previous session's score of 6 clean reps, but your overall score ticked up slightly from 75 to 77. The good news is you completely cleared any other faults from last time, leaving just one recurring habit to clean up. 

***

### Error Breakdown

* **What it is:** Your knees are caving inward toward each other—specifically showing up on reps 2, 5, 8, and 10. As you get deeper into the set and fatigue sets in, your knees drop out of alignment with your toes.
* **Why it matters:** This puts a lot of twisting stress right on the inside of your knee joints instead of letting your quads and glutes share the workload evenly. If you let this slide, it robs you of your driving power out of the bottom and creates a nagging ache around your kneecaps as the weight goes up.
* **How to fix it:** 
  * (a) Think about driving your knees out wide to the sides, as if you are trying to split the floor apart with your feet.
  * (b) Narrow your stance slightly or point your toes out a couple of degrees more to give your hips a better angle to track from.
  * (c) Loop a light resistance band just above your knees during your warm-up sets and perform bodyweight squats, forcing your knees to actively fight the band the whole way.
  * (d) Watch your knees in the mirror as you come up—if they pinch together at any point, that rep didn't count.

***

### Next Session Plan

* **Spread the floor:** Focus on pushing your knees outward from the very first rep, especially as fatigue starts creeping into the later half of your sets on reps 8 through 10.
* **Warm up with bands:** Spend two minutes doing banded squats before you touch a loaded bar to wake up the outer glutes that keep your knees tracking straight.

---

## Exercise: Squat — rounded_back

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| rounded_back | Losing a straight back during the squat: the upper back hunching, the lower back rounding as the pelvis tucks under at the bottom (butt wink), the lower back over-arching, or the torso tipping too far forward (+why/fix) | 0.049 / 3* | 0.119 / 2* | 0.109 / 2* | 0.101 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: rounded_back | source: blog.nasm.org/newletter/squat-form]
Losing lumbar lordosis or failing to maintain a neutral low back position during the squat.

[principle | re: rounded_back | source: blog.nasm.org/newletter/squat-form]
Maintaining an upright chest and thoracic position with the scapula retracted is important to attain a correct lumbo-pelvic position during the squat.

[consequence | re: rounded_back | source: TheBackSquatAProposedAssessment]
Allowing the hips to rise too quickly and increasing trunk flexion during the ascent represents an incorrect back squat that can be a dangerous strategy to the lower back during squatting with progressive external resistance.

[finding | re: rounded_back | source: TheBackSquatAProposedAssessment]
Flexing at the spine before 120 degrees of hip flexion when squatting may indicate restriction in the posterior fibers of the iliotibial band or a lack of lumbar control.

[consequence | re: rounded_back | source: Kim2015_HipAnkleROM_SquatDepth_JHumKinet]
Failing to maintain correct positioning during the squat can increase joint strain and potential injury to the low back and knees.

[finding | re: rounded_back | source: Papadakis2024_BackSquatErrors_NeutralSpineKneeAlignment_JFMK]
A flat lumbar spine during squats is associated with a thinner anterior vertebral wedge, long paraspinal muscles, and/or a long iliopsoas.

[mistake | re: rounded_back | source: Papadakis2024_BackSquatErrors_NeutralSpineKneeAlignment_JFMK]
Allowing excessive lumbar lordosis (hyperextension) or excessive lumbar flexion during the squat.

[mistake | re: rounded_back | source: Papadakis2024_BackSquatErrors_NeutralSpineKneeAlignment_JFMK]
Rounding the back, bending forward, raising the heels, or looking down during the ascent phase are common errors that compromise squat effectiveness.

[principle | re: rounded_back | source: basics_of_strength_and_conditioning_manual]
Never flex the spine or round forward during a squat.
```

### WITH RAG (sample 1/3)
### Progress Tracking
Good work on the score bump—you moved up from 73 to 76 overall. Your clean reps stayed steady at 6 out of 10, exactly where you were last time. Even better, you completely kicked one of your old habits: partial squats didn't show up at all today. You're still letting your lower back round out, though, which carried over from your last session. Let's get that nailed down so you can trust every single rep.

### Error Breakdown

*   **What it is, in plain words:** Letting your lower back curve forward and slouch as you move, instead of keeping a tight, neutral spine.
*   **Why it matters:** This puts unnecessary strain on your lower back and knees, and as you add heavier weights, it turns into a risky position that can lead to injury. You'll feel it tugging in your lower back instead of working your legs, and it costs you a strong, stable base to drive out of the bottom of the squat.
*   **How to fix it:** 
    (a) Cue: Think about lifting your chest proudly and keeping your shoulder blades squeezed together as you move. 
    (b) Setup change: Pause for a full second at the top to reset your breath and brace your core before you start your next descent. 
    (c) Drill: Drop the weight down to just the bar and practice slow-tempo squats, focusing entirely on keeping your spine rigid before adding load back on. 
    (d) Self-check: Glance at a side-profile mirror or check your phone video to make sure your lower back stays flat and doesn't tuck under at any point during the lift.

### Next Session Plan
1. **Pace your breathing:** Take a deliberate pause at the top of every single rep to set your upper back and brace your core before you descend.
2. **Watch the fatigue factor:** Notice that your back rounding popped up on reps 3, 6, 8, and 10—likely as fatigue set in. If your form starts to slip halfway through a set, rack the bar and finish with shorter sets rather than grinding out sloppy reps.

### WITH RAG (sample 2/3)
### Progress Tracking
Good work stepping up to the bar again. Your overall score ticked up slightly from 73 to 76, and you matched your previous count of 6 correct reps. More importantly, you completely cleared partial squats from your session—every single rep went the full distance today. You still had 4 incorrect reps, but you dropped one of your old errors entirely, leaving just one fault to iron out.

### Error Breakdown

* **What it is, in plain words:** Your lower spine is curling forward and rounding out instead of staying locked flat as you squat.
* **Why it matters:** Rounding your lower back shifts the strain directly onto your spine and joints instead of letting your muscles carry the load. As you add heavier weights to the bar, this turns into a dangerous loading pattern that invites low back strain and knee stress, leaving you sore in the wrong places and risking injury.
* **How to fix it:** 
  *(a) Cue to think about:* Keep your chest proud and drive your shoulder blades together like you are trying to squeeze a tennis ball between them.
  *(b) Setup change:* Lift your chest and upper back tall before you even unrack the bar, and set your depth so you maintain that proud-chest posture without letting your hips shoot up faster than your shoulders on the way back up.
  *(c) Drill or regression:* Practice bodyweight box squats where you focus entirely on keeping your spine rigid before adding weight back to the bar.
  *(d) Self-check:* Notice that this fault showed up exclusively on the later reps (reps 3, 6, 8, and 10), which tells us your form starts to slip as fatigue sets in; watch your phone video to see if your torso starts tipping forward halfway through your set.

### Next Session Plan
* **Hold your depth:** You completely wiped out the partial squat issue today—keep that exact same range of motion on every rep next time.
* **Watch late-set fatigue:** Since rounding your lower back only crept in on the later reps (3, 6, 8, and 10), cut your sets a rep or two short once your form starts to blur, or take a few extra seconds of rest before those final reps.
* **Anchor your chest:** Focus on keeping your upper back tight and your chest lifted from the very first rep to the last so your spine stays locked in place.

### WITH RAG (sample 3/3)
### Progress Tracking
Good work stepping back under the bar. Your overall score ticked up to 76 (from 73), and you matched your previous count of 6 correct reps. More importantly, you completely cleared one of your previous issues—partial squats are gone entirely, meaning you are hitting your depth on every single rep. You still had 4 incorrect reps today due to your back rounding, which is the exact same number of miscues you had last time, so cleaning that up is the final puzzle piece to lock in a completely clean set.

### Error Breakdown

* **What it is, in plain words:** Your lower spine is curling forward instead of staying flat and braced as you move, which usually happens when your hips shoot up too fast or you start bending forward during the hardest part of the lift. This cropped up on reps 3, 6, 8, and 10—notice how it only happened in the second half of your set as fatigue started to creep in.
* **Why it matters:** When your spine rounds under a load, your lower back takes the stress that your legs and core should be handling. As the weight on the bar goes up, that puts dangerous strain on your lower back joints, costing you power and leaving you with a sore lower back instead of stronger quads and glutes.
* **How to fix it:** 
  (a) *Cue:* Think about lifting your chest proudly to the wall in front of you and locking your ribs down tight before you even unrack the bar. 
  (b) *Setup change:* Slow your descent down and keep your tempo under control, especially on those later reps where fatigue makes your hips want to shoot up first. 
  (c) *Drill:* Drop the weight down to a light plate or just the bar and practice pausing for a full two seconds at the bottom of the squat to build that lower-back control. 
  (d) *Self-check:* Glance at your phone recording—if your lower back caves or your hips rise ahead of your chest on the way up, you'll see the curve immediately.

### Next Session Plan
1. **Manage fatigue:** Since your back rounding only showed up on the later reps (3, 6, 8, and 10), consider cutting your sets a rep or two short once your form starts to wobble, rather than grinding through sloppy reps.
2. **Focus on chest position:** Make "proud chest" your primary mental cue on every single rep from the very first one.

### WITHOUT RAG (sample 1/3)
### Progress Tracking
Good effort out there today. You hit 6 clean reps out of your 10 total completed reps, bumping your overall score up slightly to 76 compared to 73 in your last session. More importantly, you completely cleared out the partial squat issue that was dragging you down last time, which is a great win for your depth. You still have one lingering habit to iron out, though: rounding your lower back showed up again on reps 3, 6, 8, and 10 as fatigue started to creep into the later stages of the set. 

***

### Error Breakdown

* **What it is, in plain words:** Your lower back is curling forward and losing its flat, supported arch, especially as you start getting tired in the second half of the set.
* **Why it matters:** When your spine rounds under a load, the stress shifts away from your glutes and thighs and dumps straight onto the passive structures of your lower back. That is the exact ache you feel the next morning, and it costs you leg power while risking your spine as you add heavier plates to the bar.
* **How to fix it:** 
  * (a) Think about lifting your chest proudly to the wall in front of you the moment you start your descent.
  * (b) Narrow your stance slightly or adjust your foot angle so you can drop comfortably between your legs without your hips tucking under at the bottom.
  * (c) Practice bodyweight box squats where you focus entirely on keeping your torso rigid and your lower back locked flat before adding weight back on.
  * (d) Check your phone video to see if your hips are tucking under at the bottom of the movement—if they are, cut your depth just an inch higher where you can keep your spine solid.

***

### Next Session Plan
1. **Manage your fatigue:** Since your back rounded on reps 3, 6, 8, and 10, cut your working sets a rep or two short of breakdown today, or drop the weight slightly to keep every single rep crisp.
2. **Brace hard first:** Spend an extra two seconds before un-racking the bar to take a deep breath into your stomach and lock your core tight, treating your torso like a solid cylinder.

### WITHOUT RAG (sample 2/3)
### Progress Tracking
Good effort out there today. You hit 6 clean reps out of your 10 total completed reps, bumping your overall score up slightly to 76 compared to 73 in your previous session. Even better, you completely cleared the partial squat issue that was showing up last time. You had 4 incorrect reps today, and all of them came down to the exact same issue: a rounded back, which cropped up on reps 3, 6, 8, and . Let's get that locked in so you can string together a fully clean set next time.

***

### Error Breakdown: Rounded Back

* **What it is, in plain words:** As you got deeper into the set—specifically on reps 3, 6, 8, and 10—your lower back started to slump forward instead of staying flat and braced under the load. 
* **Why it matters:** When your lower spine rounds out like that, the load shifts away from your quads, glutes, and core and dumps straight onto the passive structures of your lower back. That is what leaves your lower back aching after leg day instead of your legs, and as the weight gets heavier, it sharply increases the risk of a strain or tweak right when you are trying to push.
* **How to fix it:**
  * *(a) Cue:* Think about proudly chesting up and pulling your ribs down toward your hips before you even unrack the bar.
  * *(b) Setup:* Take a slightly wider stance or slow down your descent so you have more control over your torso angle as you drop into the bottom position.
  * *(c) Drill:* Drop the weight down to just the bar or a light plate and practice paused squats, holding for a full two seconds at the bottom while aggressively checking that your lower back stays flat.
  * *(d) Self-check:* Watch a side-angle video of your set; you want to see your torso angle remain steady and your lower back flat from the start of the descent all the way back to standing.

***

### Next Session Plan
1. **Focus on the brace early:** Set your core and keep your chest proud before every single rep, treating rep 10 with the exact same postural strictness as rep 1.
2. **Watch the fatigue window:** Notice how your back rounded on the later reps (3, 6, 8, and 10)? If your form starts to break down toward the end of a set, cut the set a couple of reps short rather than grinding out ugly reps.

### WITHOUT RAG (sample 3/3)
### Progress Tracking
Good effort out there today. You hit 6 clean reps out of 10 total completed reps, bumping your overall score up to 76 compared to 73 in your last session. Even better, you completely cleared partial squats off the board—that depth issue from last time is gone. Your main hurdle today was letting your lower back round on the second half of the set, specifically showing up on reps 3, 6, 8, and 10. Let's lock that in so you can string together a completely clean set next time.

### Error Breakdown

*   **What it is:** Your lower back is curling forward and losing its flat, stable arch as you push up out of the bottom of the squat, usually creeping in as you start getting tired later in the set.
*   **Why it matters:** When your spine rounds under a load, your lower back muscles and spinal joints take the strain instead of your quads, glutes, and core sharing the work. That means you'll feel a dull ache or tightness in your lower back during or after your workout, you lose power out of the hole, and you risk straining your lower back as the weight gets heavier.
*   **How to fix it:** 
    *   (a) *Cue:* Think about pulling your chest proud and driving your upper back hard into the bar from the moment you unrack.
    *   (b) *Setup change:* Take an extra second to brace your abs hard like you're about to take a punch before you even begin descending, and slow down your tempo on the way down to keep control.
    *   (c) *Drill:* Drop the weight down by 10-15% and pause for a solid two seconds at the bottom of each rep to practice holding your torso rigid before driving back up.
    *   (d) *Self-check:* Watch a side-angle video of your set—your torso angle should stay steady on the way up instead of your hips shooting up first while your chest caves forward.

### Next Session Plan
1. **Pace your fatigue:** Since your back rounding kicked in on the later reps (3, 6, 8, and 10), focus on maintaining absolute tightness as you tire, or cut the set short right before form breaks down rather than grinding out ugly reps.
2. **Prioritize the brace:** Spend an extra breath getting tight before every single rep next workout to make sure your spine stays locked in from start to finish.

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

### WITH RAG (sample 1/3)
### Progress Tracking
You finished today's session with 4 correct reps out of 10 total attempts, and your overall score dipped slightly to 67 compared to 70 in your previous workout. Your correct rep count held steady at 4, but your incorrect reps jumped up to 6, including one attempt (attempt 9) that you had to cut short and abort altogether. 

On the bright side, you stayed strong on your clean reps—rep 1, 3, 5, and 7 were solid. The main issue today is that fatigue crept in during the second half of the set, causing old habits like knee caving and rounding your lower back to sneak back in alongside a few shallow reps.

---

### Error Breakdown

*   **Knee caving inward**
    *   What it is, in plain words: Letting your knees buckle toward each other instead of tracking straight out over your toes as you push up or lower down.
    *   Why it matters: This places extra stress on the ligaments and muscles surrounding your knee joint. For you, that translates to nagging joint discomfort and less stable, weaker lifts when the weight on the bar starts climbing.
    *   How to fix it: 
        *   (a) Cue: Think about actively pushing your knees outward as you drive up.
        *   (b) Setup: Place a mini resistance band just above your knees during your warm-up sets to force your outer hips to turn on.
        *   (c) Drill: Perform a few lighter sets with a mini band or focus on a slightly wider stance if your feet tend to drift.
        *   (d) Self-check: Watch your phone video to make sure your kneecaps stay in line with your second toe from top to bottom.
    *   Note on your set: This error showed up on reps 2, 6, and 10, meaning it tends to pop up later in the set as your legs start getting tired.

*   **Rounding your lower back**
    *   What it is, in plain words: Losing the flat, neutral arch in your lower back and letting your spine slump forward as you move.
    *   Why it matters: This shifts the load away from your legs and directly onto your lower back, dramatically increasing joint strain. If you push heavier loads with a rounded spine, you risk a dull, nagging lower back ache that lingers long after you leave the gym.
    *   How to fix it: 
        *   (a) Cue: Keep your chest proud and your shoulder blades pinned back to lock your torso in place.
        *   (b) Setup: Take a deep breath into your belly and brace your core hard before you even begin the descent.
        *   (c) Drill: Practice bodyweight pauses at the bottom of the squat, focusing entirely on holding a flat lower back before standing up.
        *   (d) Self-check: Glance in the side mirror or check your video to verify your torso stays upright and your lower back doesn't tuck under at the bottom.
    *   Note on your set: This fault crept into rep 4, rep 6, the aborted attempt 9, and rep 10, signaling a breakdown in core endurance as fatigue set in.

*   **Stopping too shallow**
    *   What it is, in plain words: Cutting your depth short and not dropping down far enough before heading back up.
    *   Why it matters: When you cut your depth short, your glutes and hamstrings don't get fully challenged, leaving muscle growth on the table. It also subjects your knee joints to higher compressive forces without giving you the full-range benefits of a proper squat.
    *   How to fix it: 
        *   (a) Cue: Wait until the top of your thighs are at least parallel to the floor before reversing direction.
        *   (b) Setup: Use a box or a target set at the correct height so you have a physical marker for your target depth.
        *   (c) Drill: Drop the weight and practice slow, controlled goblet squats to a full-depth pause.
        *   (d) Self-check: Have a training partner film your side profile to see if your hip joint drops at least level with your knees.
    *   Note on your set: This issue hit on rep 4, rep 8, and forced you to abort attempt 9 early. It's a clear sign that your legs were tiring out near the end.

---

### Next Session Plan

1.  **Drop the weight slightly:** Take 10% off your working weight for your next session. This lets you chase crisp, full-depth reps without form breakdown.
2.  **Add a mid-set pause:** Stop at rep 5 and take a full 10-second breath before finishing your set, or cap your sets at 5 clean reps to beat the fatigue that brings on knee caving and back rounding.
3.  **Use a band warm-up:** Spend five minutes doing bodyweight squats with a mini band around your knees to prime your hips and keep your knees tracking correctly from rep one.

### WITH RAG (sample 2/3)
### Progress Tracking
You finished today's session with 4 correct reps out of 10 total attempts, earning an overall score of 67. Compared to your previous session on October 2, your correct rep count stayed locked at 4, and your overall score dipped slightly from 70 to 67, while your incorrect reps remained at 6. Both of your old habits—knees caving in and your lower back rounding—came back with you today. On top of that, cutting your depth short showed up as a brand-new issue in the second half of your set, appearing on reps 8, 9, and 10 (with attempt 9 cutting so short it aborted completely). Let's clean these up so your numbers actually start climbing.

---

### Error Breakdown

*   **Knees caving inward**
    *   What it is, in plain words: Your knees are collapsing toward each other instead of tracking straight out over your toes as you push up and down.
    *   Why it matters: When your knees drop inward, the ligaments and muscles surrounding the knee joint take on extra strain. As the weight on your back creeps up, that stress turns into joint irritation and knee pain that can sideline you.
    *   How to fix it: 
        (a) Cue yourself to "push your knees out wide" the second you start bending your legs. 
        (b) Loop a small resistance band around your thighs just above your knees during your warm-up sets to force your outer hip muscles to wake up. 
        (c) Drop the load slightly for your working sets so you can control your knee path without shaking. 
        (d) Watch your knees in the mirror or on a phone video to make sure the middle of your kneecap stays pointed right over your big toe.
    *   Use the rep detail: This fault popped up on reps 2, 6, and 10—showing up every few reps as fatigue set in. Stay extra disciplined with your knee drive on your later reps.

*   **Rounding your lower back**
    *   What it is, in plain words: Your spine is flexing forward and losing its flat, stable arch as you move.
    *   Why it matters: Letting your lower back round shifts excessive strain onto your spine and the discs in your lower back. Under heavy loads, this increases your risk of a sudden tweak or deep lower back ache that ruins your training week.
    *   How to fix it: 
        (a) Think about lifting your chest proud and keeping your shoulder blades squeezed together. 
        (b) Take a deep breath into your stomach and brace your core hard before you even unrack the bar. 
        (c) Practice bodyweight box squats where you focus entirely on keeping your spine rigid from top to bottom. 
        (d) Glance at your side-profile video to check that your torso angle stays consistent and your lower back doesn't tuck under at the bottom.
    *   Use the rep detail: This error clustered heavily in the back half of your workout, showing up on rep 4, rep 6, the aborted attempt 9, and rep 10. When fatigue hits, your torso is folding forward early—recognize when your form starts slipping and wrap up the set before your spine gives way.

*   **Stopping too shallow**
    *   What it is, in plain words: You are cutting your depth short and turning your squats into half-reps instead of dropping all the way down.
    *   Why it matters: If you don't drop down until the top of your thighs are at least parallel to the floor, your glutes and hamstrings don't get fully challenged, meaning you miss out on muscle growth for the exact effort you're putting in. Plus, partial squats can actually place higher compressive forces on your knee joints.
    *   How to fix it: 
        (a) Cue yourself to "sit down between your heels" rather than just bending your knees forward. 
        (b) Set a box or a bench at parallel height behind you so you have a physical target to lightly touch on every rep. 
        (c) Spend a few extra minutes before your session working on ankle and hip stretches so your joints actually have the range of motion to reach depth comfortably. 
        (d) Check your phone video to verify your hip crease drops at least level with or slightly below your kneecap.
    *   Use the rep detail: Depth started failing exclusively in the later stages, hitting on rep 8, cutting attempt 9 short into an abort, and showing up alongside your back rounding on the final stretch. Stop the set a rep or two earlier when you notice yourself cutting corners to avoid hitting a wall.

---

### Next Session Plan
1. **Band your warm-ups:** Wrap a light resistance band around your knees for two warm-up sets to actively build knee and hip awareness before you touch heavy weight.
2. **Add a depth target:** Place a box or bench at parallel height behind you so you eliminate the guesswork on how low to go.
3. **Cut the set short when form breaks:** If your lower back rounds or your knees cave on rep 6, rack the weight right there. Protecting your spine matters more than grinding out sloppy reps.

### WITH RAG (sample 3/3)
### Progress Tracking

Compared to your last session yesterday, your numbers stayed pretty steady: you hit 4 correct reps again, but your overall score dipped slightly from 70 to 67, and your incorrect reps rose to 6 (including one aborted attempt). 

The good news is you completely cleared out the knee caving issue on half of your work, but it still crept in later in the set. You also picked up a new battle with depth—stopping short on a few reps—while rounding your lower back remains a stubborn habit that followed you over from yesterday.

***

### Error Breakdown

*   **Knee caving inward**
    *   *What it is:* Letting your knees drift toward each other instead of tracking straight out over your toes during the descent and ascent.
    *   *Why it matters:* This puts extra stress on the ligaments and muscles holding your knee joint together. When you load this up over time, you will feel a nagging ache around your kneecap or on the inside of the joint, and it robs you of the stable power transfer you need to drive the weight up safely.
    *   *How to fix it:* 
        *   (a) Think about actively pushing your knees outward as you lower yourself.
        *   (b) Take a slightly wider stance or loop a light resistance band just above your knees to give your legs something to fight against.
        *   (c) Try banded bodyweight squats as a warm-up drill to wake up your hip muscles.
        *   (d) Set up your phone to record from the front and check that your kneecaps track directly over your big toes on every single rep.
    *   *Note on your set:* This error showed up on reps 2, 6, and 10—appearing specifically as fatigue set in during the later stages of your workout.

*   **Rounding your lower back**
    *   *What it is:* Losing your neutral, flat lower-back position and letting your spine hunch forward as you move.
    *   *Why it matters:* This shifts a heavy shear load straight onto your lower back instead of letting your glutes and quads do the heavy lifting. That translates to lower-back stiffness or a dull ache right after your set, and it sharply increases your injury risk as you add heavier weights to the bar.
    *   *How to fix it:* 
        *   (a) Keep your chest proud and your upper back tight throughout the whole movement.
        *   (b) Reduce your descent depth slightly if you notice your hips tucking under at the bottom.
        *   (c) Practice the cat-cow stretch on the floor to get a better feel for moving your pelvis independently of your spine.
        *   (d) Watch your side-profile video to ensure your spine maintains the exact same shape from top to bottom.
    *   *Note on your set:* This crept in on reps 4, 6, 9 (the aborted attempt), and 10, clustering heavily in the second half when your core started getting tired.

*   **Stopping too shallow**
    *   *What it is:* Cutting your squat short before your thighs reach parallel to the floor.
    *   *Why it matters:* Short-changing your depth means your glutes and hamstrings never get fully stretched or challenged, so you miss out on real muscle growth. Plus, stopping halfway can actually put higher compressive forces on the front of your knees.
    *   *How to fix it:* 
        *   (a) Pick a fixed target on the wall in front of you and commit to hitting depth before you reverse direction.
        *   (b) Adjust your stance slightly or work on ankle mobility so you can comfortably sink lower without your heels lifting.
        *   (c) Use a box or a bench set to parallel height behind you to give yourself a physical target to touch on every rep.
        *   (d) Film from the side and verify that your hip crease drops at least level with or slightly below the top of your knee.
    *   *Note on your set:* This happened on reps 4, 8, and rep 9—which was cut short entirely as an aborted attempt because the depth and form broke down simultaneously.

***

### Next Session Plan

1.  **Drop the load slightly:** Take 5-10% off the bar for your next session so you can focus entirely on hitting proper depth without your lower back rounding or your knees caving.
2.  **Use a target box:** Place a box or bench at parallel height behind you to eliminate depth guesswork and ensure every rep hits the right standard.
3.  **Cut the set short when form cracks:** Since your errors heavily cluster in the second half of the set, stop your sets two reps *before* your form starts to fall apart. Bank clean reps instead of grinding out messy ones.

### WITHOUT RAG (sample 1/3)
### Progress Tracking
Let's look at how today stacked up against your last session on October 2nd. Your correct rep count stayed locked at 4, but your overall score dipped slightly from 70 to 67, and you pushed through 6 incorrect attempts today compared to 6 last time (though note that attempt 9 was an aborted effort rather than a finished rep). 

The good news is you are fighting familiar battles: knee valgus and rounded back showed up again, but you also introduced a new issue with depth (partial squats) on reps 4, 8, 9, and 10. Let's iron these out so you can trust every single rep you log.

***

### Error Breakdown

* **Knee Valgus (Caving knees)**
  * **What it is:** Your knees are collapsing inward toward each other instead of tracking directly over your toes as you push up from the bottom.
  * **Why it matters:** This puts a lot of twisting stress right on the inside of your knee joints and robs your glutes of the leverage they need to help you stand up. When the weight gets heavier, this is where nagging joint aches start creeping into your knees, and it drains your power output before your legs get a true workout.
  * **How to fix it:** 
    (a) Cue: Think about actively spreading the floor apart with your feet as you drive up. 
    (b) Setup: Bring your stance in slightly or adjust your toe angle so your knees naturally track outward over your second and third toes. 
    (c) Drill: Loop a light mini-band around your thighs just above your knees during a bodyweight warmup set to give your nervous system instant feedback to push outward. 
    (d) Self-check: Watch your phone video and check if your knees stay wide or pinch together when you hit the bottom of the squat.

* **Rounded Back (Loss of spinal neutrality)**
  * **What it is:** Your lower or mid-back is flexing forward, causing your chest to cave as you move. This popped up on reps 4, 6, 9 (your abort), and 10—mostly as fatigue set in during the back half of your set.
  * **Why it matters:** Your spine has to soak up loads it isn't built to carry, shifting the work away from your core and hips and dumping sheer stress straight onto your lower back disks. You'll feel this as a dull ache or tightness in your lower back right after your set, and it severely limits how much safe strength you can build.
  * **How to fix it:** 
    (a) Cue: Pull your shoulder blades down and back, and brace your stomach like someone is about to punch your gut before you even unrack the bar. 
    (b) Setup: Take a slightly narrower grip on the bar to help lock your upper back tight, and slow down your descent so you don't lose your posture at the bottom. 
    (c) Drill: Practice lightweight pause squats, holding a 2-second pause at the bottom while aggressively maintaining a proud, upright chest. 
    (d) Self-check: Glance at a side-profile mirror or video to ensure the angle of your torso matches the angle of your lower shin throughout the entire movement.

* **Partial Squat (Short range of motion)**
  * **What it is:** You are cutting the movement short before hitting proper depth—this happened on reps 4, 8, the aborted attempt 9, and rep 10. Notice how this cluster hits right when you are getting tired.
  * **Why it matters:** You're cheating your quads and glutes out of the bottom stretch where the most muscle growth actually happens, meaning you're doing hard work for less return. Over time, it creates major strength gaps in your legs and leaves you unable to trust your depth when you test heavier weights.
  * **How to fix it:** 
    (a) Cue: Wait until your hip crease clearly drops below the top of your knee before you reverse direction. 
    (b) Setup: Set a sturdy box or bench just at your proper parallel depth height so you have a physical target to touch gently before standing back up. 
    (c) Drill: Drop the weight by 20% and force yourself to pause for a full second at the bottom of every rep to build strength out of the hole. 
    (d) Self-check: Have a gym buddy film your side profile to verify your hip crease clears your knee before you drive upward.

***

### Next Session Plan
1. **Drop the load slightly:** Take 10% off the bar for your next session so you can own the depth and keep your back completely flat without form breaking down by rep 6.
2. **Prioritize mid-set rest:** If form starts crumbling in the back half of the set (like reps 6 through 10 did today), stop the set two reps early rather than grinding through ugly, partial-rep territory.

### WITHOUT RAG (sample 2/3)
### Progress Tracking

Let's look at how today's squat session stacked up against yesterday. You matched your correct rep count at 4 clean reps, but your overall score dipped slightly from 70 to 67, and your incorrect reps stayed high at 6 (including 9 total attempts, with one aborted rep). 

The good news: you are fighting hard and keeping that solid execution on your best reps. However, old habits are sneaking back in. While you kept knee caving out of a few sets, it returned on reps 2, 6, and 10, and rounding your lower back showed up on reps 4, 6, 9 (your aborted attempt), and 10. You also cut depth short on reps 4, 8, and 9. Let's clean these up so your hard work actually goes toward building strength.

***

### Error Breakdown

* **Knee caving inward**
  * *What it is:* Your knees are collapsing toward each other instead of tracking directly over your toes as you push up. This popped up on reps 2, 6, and 10 as you started fatiguing.
  * *Why it matters:* Your knees and hips take the brunt of the twisting force instead of your quads and glutes driving the weight straight up. That means your joints soak up stress they aren't meant to handle, leaving your legs feeling gassed early and putting your knees at risk as the weight gets heavier.
  * *How to fix it:* 
    * (a) **Cue:** Actively push your knees out wide to the sides, as if you are trying to tear the floor apart with your feet.
    * (b) **Setup:** Take a slightly narrower stance or point your toes out a degree or two more if it gives your hips a better angle to track open.
    * (c) **Drill:** Loop a light resistance band just around your knees during your warm-up bodyweight squats to force your outer hip muscles to switch on.
    * (d) **Self-check:** Glance in the mirror on your next set—your kneecaps should point in the exact same direction as your second and third toes the entire way down and up.

* **Rounding your lower back**
  * *What it is:* Your spine is flexing forward under the load instead of staying flat and braced, which happened on reps 4, 6, 9, and 10.
  * *Why it matters:* Your lower spine has to carry the load your core and glutes should be handling, which places heavy shear stress on your spinal discs. You'll feel a dull ache in your lower back during or after your workout, you lose the rigid trunk strength needed to push heavy weight, and you run a serious risk of injury as you load up the bar.
  * *How to fix it:*
    * (a) **Cue:** Take a massive breath into your belly—not your chest—and brace your abs hard like someone is about to punch your stomach, keeping that tightness until you lock out at the top.
    * (b) **Setup:** Lift your chest proudly and squeeze your shoulder blades together before you even unrack the bar to lock your upper back into a tight shelf.
    * (c) **Drill:** Practice a set of bodyweight or very light pause squats, holding the bottom for two seconds while actively thinking about keeping your chest up and your lower back flat.
    * (d) **Self-check:** Have a training partner film your side profile; your lower back should maintain its natural slight arch from the unrack to the top, with zero rounding at the bottom.

* **Cutting depth short**
  * *What it is:* You are turning around before your hips drop below parallel to your knees, which caused reps 4, 8, and the aborted rep 9 to fall short.
  * *Why it matters:* You miss out on full muscle recruitment in your glutes and hamstrings, cheating yourself out of the exact leg growth and strength gains you came to the gym for. Over time, you build partial strength in a partial range of motion, leaving you weak and stuck when you try to lift heavier.
  * *How to fix it:*
    * (a) **Cue:** Wait for your hips to break the plane of your knees before you reverse direction—think "down and back" rather than just "down."
    * (b) **Setup:** Drop the weight slightly for your next session so you aren't fighting a load that scares you out of hitting depth.
    * (c) **Drill:** Set a low box or bench just beneath parallel behind you and lightly touch your hips to it on every rep to give yourself a physical target for depth.
    * (d) **Self-check:** Watch your side-profile video to confirm your hip crease clearly drops below the top of your kneecap before you drive back up.

***

### Next Session Plan

1. **Drop the weight by 10%:** Give yourself some breathing room to fix your form. Earning clean reps at a slightly lighter load will do more for your strength than grinding out ugly reps with heavy weight.
2. **Prioritise the first 5 reps:** Your errors heavily cluster in the later reps (reps 6 through 10) as fatigue sets in. On your next workout, if your form starts breaking down on rep 6, rack the bar right there rather than forcing sloppy reps.
3. **Film your working sets:** Set your phone up to record from the side and slightly behind so you can check your lower back rounding, knee position, and depth in real time between sets.

### WITHOUT RAG (sample 3/3)
### Progress Tracking

Let's look at how today stacked up against your last session on October 2nd. Your correct rep count stayed locked at 4 out of 10, and your overall score dipped slightly from 70 to 67. 

The good news is that you are holding onto clean, solid reps right alongside the messy ones (reps 1, 3, 5, and 7 were great). However, the old faults are still hanging around: your knees collapsing inward (`knee_valgus`) and your lower back rounding (`rounded_back`) both carried over from last time. On top of that, depth became an issue today, leading to a few short-changed attempts and an aborted attempt at rep 9. 

---

### Error Breakdown

*   **Knees collapsing inward**
    *   *What it is:* As you push back up out of the bottom of the squat, your knees cave toward each other instead of tracking straight out over your toes. This showed up on reps 2, 6, and 10 as fatigue started to settle in.
    *   *Why it matters:* Your knees and hips take the strain sideways instead of working smoothly in a straight line, which robs your glutes and quads of the heavy lifting. You will feel this as a wobbly ascent and nagging joint stress around your kneecaps, capping your strength long before your legs are actually tired.
    *   *How to fix it:* 
        (a) Cue: Think about actively spreading the floor apart with your feet as you drive up. 
        (b) Setup: Bring your stance in slightly or adjust your toe angle outward just a couple of degrees so your knees have a natural path to follow. 
        (c) Drill: Loop a light resistance band around your thighs just above your knees during your warm-up sets to force your outer hips to turn on. 
        (d) Self-check: Watch your phone video and check that your kneecaps stay locked in line with your second toe from the bottom all the way to the top.

*   **Lower back rounding**
    *   *What it is:* Your spine loses its proud, flat shape and curves forward as you descend or push up. This popped up on reps 4, 6, 9, and 10—mostly clustered in the second half of the set when your core started to tire.
    *   *Why it matters:* Your lower back vertebrae and spinal ligaments soak up the load instead of your core and glutes doing the bracing. That translates into a nagging dull ache in your lower back by the time you walk away from the rack, and it puts your spine at risk as you add more weight.
    *   *How to fix it:* 
        (a) Cue: Take a deep breath into your belly and brace your abs hard like someone is about to punch you, keeping that armor tight throughout the whole rep. 
        (b) Setup: Lift your chest slightly and pull your shoulder blades down into your back pockets before you even unrack the bar. 
        (c) Drill: Drop the weight and pause for a solid two seconds at the very bottom of a lighter set to practice holding a flat, rigid spine where it matters most. 
        (d) Self-check: Look in the side mirror and make sure the natural arch in your lower back stays identical from the moment you start descending to when you lock out.

*   **Cutting the depth short**
    *   *What it is:* You aren't descending far enough to hit the standard squat depth, turning full reps into half-reps. This happened on rep 4 and rep 8, and it's the exact reason rep 9 aborted early before you even made it back up.
    *   *Why it matters:* Your glutes and hamstrings miss out on the deep stretch that builds real lower-body strength and muscle. You end up lifting with your ego instead of your legs, trading actual growth for numbers on a bar that only went halfway down.
    *   *How to fix it:* 
        (a) Cue: Wait for your hip crease to drop clearly below the top of your kneecap before you reverse direction. 
        (b) Setup: Set a box or a target height just below parallel behind you so you have a physical marker to lightly touch on every single rep. 
        (c) Drill: Perform lighter goblet squats holding a dumbbell at your chest, focusing entirely on sinking into a deep, paused bottom position without losing your balance. 
        (d) Self-check: Set your phone up strictly at hip height from the side to verify that your hips are genuinely dropping past parallel on every working rep.

---

### Next Session Plan

1.  **Drop the load slightly:** Take 10% off the bar for your next session. Getting your reps clean and hitting full depth consistently is worth far more right now than grinding out ugly reps with heavy weight.
2.  **Cut your sets short:** Since your form (especially your back and knees) started falling apart around rep 6, cap your working sets at 5 clean reps for now. Step away before the fatigue forces you into bad habits.
3.  **Add a pause:** Introduce a strict 1-second pause at the bottom of every rep on your warm-up and first working set to force yourself to own the depth and keep your core braced.

---

## Exercise: Squat — clean

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| general principles | Squat correct technique and biomechanics | — | — | — | 0.153 / 2 |

### Retrieved KB Context (RAG run)
```text
[principle | re: general principles | source: TheBackSquatAProposedAssessment]
During the squat, the lateral aspect of the knee should not cross the vertical plane of the medial malleolus to avoid medial displacement.

[principle | re: general principles | source: blog.nasm.org/newletter/squat-form]
Maintaining an upright chest and thoracic position with the scapula retracted is important to attain a correct lumbo-pelvic position during the squat.
```

### WITH RAG (sample 1/3)
### Progress Tracking

Great work on this session—you completely turned things around since yesterday. Your overall score jumped from 76 to 89, and you nailed all 10 reps cleanly without a single error. Even better, you completely cleared both faults from your last workout: you hit full depth on every single rep, leaving behind the partial reps, and you kept your knees tracking strong and steady, kicking the knee cave to the curb. 

---

### Next Session Plan

* **Lock in this standard:** Take a quick phone video from the front and side during your warm-up sets to make sure your depth and knee alignment look just like they did today.
* **Keep the weight steady:** Since your form was spotless across all 10 reps, stick with this exact load for your next session before adding any weight.

### WITH RAG (sample 2/3)
### Progress Tracking

Massive improvement since yesterday. You bumped your overall score from 76 up to 89, and you nailed all 10 reps cleanly with zero errors flagged. Even better, you completely cleared out the partial depth and knee collapse issues that were dragging down your previous session. That is a textbook turnaround—you kept your standards high from the first rep to the last.

### Next Session Plan

1. **Hold the standard:** Your form looked solid across all 10 reps today. Do not try to change your stance or speed next time out; just lock in the exact same rhythm and depth you used today.
2. **Watch the fatigue factor:** Your scores dipped slightly by rep 10 (down to 86 from 92 on rep 1). Keep an eye on your focus as you get tired so your form stays just as sharp on the final rep as it is on the first.

### WITH RAG (sample 3/3)
### Progress Tracking

Massive turnaround since yesterday. You bumped your overall score up from 76 to 89 and went from hitting 6 correct reps out of 10 down to a clean sweep: all 10 reps completed successfully with zero errors recorded. Even better, you completely cleared out the partial depth and knee cave issues that were dragging down your previous session. 

---

### Next Session Plan

* **Hold the standard:** You proved today you can lock in your form for a full set of 10. Keep your setup and focus exactly where they were for this session.
* **Keep the weight steady:** Don't rush to jump up in load just yet. Give yourself one more session at this weight to prove today wasn't a fluke before you add plates.
* **Trust your depth:** Since you completely shook off the habit of cutting reps short, focus on hitting that same solid bottom position from rep one to rep ten next time out.

### WITHOUT RAG (sample 1/3)
Great work on this session. You hit 10 completed reps with zero errors, bringing your overall score up to 89 compared to 76 in your last workout. Even better, you completely cleared out the partial depth and knee cave issues that showed up in your previous session. Every single rep was clean, and you locked in a solid standard. 

Here is your plan for your next workout to hold that ground:

* **Lock in your setup:** Keep the exact same stance width and depth target you used today so your body stays familiar with this clean movement pattern.
* **Maintain your pace:** Don't rush your descent on the next session—keep the same controlled tempo that helped you keep your knees and depth in check across all 10 reps.

### WITHOUT RAG (sample 2/3)
### Progress Tracking

Great job on this session! You made a massive jump across the board compared to yesterday. Your overall score climbed from 76 to 89, and you nailed all 10 reps cleanly with zero errors. Even better, you completely wiped out the partial depth and knee cave issues that tripped you up in your last workout. 

---

### Next Session Plan

* **Lock in this standard:** Your movement quality was rock solid today. Keep your setup, stance, and depth exactly where they were for this session.
* **Maintain your focus:** Since you cleared all previous faults, your main goal next time is simply to repeat this clean performance under the same weight before you even think about adding more load.

### WITHOUT RAG (sample 3/3)
### Progress Tracking

Great job on this session! You made a massive jump across the board compared to your last workout on October 2nd. Your overall score climbed from 76 to 89, and you completed all 10 reps cleanly with zero errors—a huge improvement from the 4 incorrect reps you logged last time. Even better, you completely wiped out the partial depth and knee cave issues that were holding you back previously. That is real progress.

### Next Session Plan

1. **Hold the standard:** Keep your focus on the same depth and knee tracking that just earned you a clean 10-rep set. 
2. **Lock in your setup:** Take the exact same time to brace your core and set your stance before you unrack the bar next workout.

---


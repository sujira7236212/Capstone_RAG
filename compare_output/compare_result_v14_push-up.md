# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions_push-up.json` |
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

## Exercise: Push-up — hip_sag_or_pike

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| hip_sag_or_pike | Failing to hold a straight plank line in the push-up: the hips sagging toward the floor with the lower back arching, or the hips piking up toward the ceiling (+why/fix) | 0.074 / 3* | 0.238 / 2* | 0.114 / 2* | 0.137 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: hip_sag_or_pike | source: www.acefitness.org/resources/pros/expert-articles/7265/perfecting-the-push-up-for-all-levels]
Failing to activate the deep core muscles required to stabilize the spine and pelvis during the push-up.

[consequence | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Failing to maintain a neutral lumbar spine position during a push-up results in anterior pelvic tilt and trunk lag, indicating impaired trunk stability.

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

[finding | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
More than 60% (n=65/108) of active females failed the Trunk Stability Push Up (TSPU) compared to less than 10% (n=10/101) of active males.

[finding | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
In a pilot study of active females, a six-week multiplanar trunk stability intervention resulted in 9 of 20 participants (45%) improving their Trunk Stability Push Up (TSPU) score to ≥2.
```

### WITH RAG (sample 1/3)
### Progress Tracking
Good effort today. Your overall score ticked up slightly from 73 to 76, and you matched your previous count with 6 clean, solid reps out of 10. That said, your old habit—letting your hips sag—is still hanging around, appearing on reps 4, 6, 8, and 10. Notice how it only shows up in the second half of the set? That tells us your core is giving out as fatigue sets in, causing your trunk to lag behind your upper body instead of lifting as one solid piece.

***

### Error Breakdown

* **What it is, in plain words:** Your lower back arches and your hips drop toward the floor mid-rep, breaking the straight line from your shoulders to your ankles.
* **Why it matters:** When your midsection gives out, the stress shifts straight onto the discs in your lower back instead of staying locked into your core and upper body. That means you'll start feeling a dull ache or pinch in your lower back as the set drags on, and it robs you of the stable platform you need to push heavy and build real chest and arm strength.
* **How to fix it:** 
  *(a) Cue to think about:* Squeeze your glutes hard and brace your stomach like someone's about to poke you in the gut right before you start moving.
  *(b) Setup change:* Drop your knees to the floor for your sets once you feel your form starting to slip, or cut your set short by a rep or two before the breakdown happens.
  *(c) Drill or regression:* Try practicing plank holds on your toes to build the trunk stability you need to keep your hips locked in place.
  *(d) Self-check:* Glance at a mirror sideways or set your phone up to record—if your hips hit the floor a split second before your chest does, you know your core let go.

***

### Next Session Plan
1. **Stop the slide:** Cut your sets off one rep *before* your form breaks down. If reps 4, 6, 8, and 10 are where your hips sag, stop at 3 clean reps per set today and build quality up from there.
2. **Prioritize the brace:** Spend an extra five seconds setting your core and squeezing your glutes before you even unlock your arms on every single rep.

### WITH RAG (sample 2/3)
### Progress Tracking
Good effort out there today. Your overall score ticked up slightly from 73 to 76, and you matched your previous performance by banking 6 clean, solid reps. That said, your incorrect rep count stayed locked at 4. The same issue from yesterday—letting your hips sag or hike up—is still showing up, meaning we haven't quite stamped it out yet, but you're keeping your core braced for a bit longer before fatigue sets in.

### Error Breakdown

* **What it is, in plain words:** Your lower back starts to arch and your hips dip toward the floor as you press, meaning your midsection caves in and your torso stops moving as a single rigid block. 
* **Why it matters:** When your trunk fails to stay locked, extra mechanical stress goes straight onto your spinal discs. That translates to a dull, nagging ache in your lower back during or after your set, robbing your chest and arms of a stable platform to push from and risking your long-term joint health as you add weight or volume.
* **How to fix it:** 
  *(a) Cue:* Think about tucking your tailbone under and pulling your belt buckle toward your belly button to lock your midsection in place.
  *(b) Setup:* Elevate your hands on a sturdy bench or box for your next session to reduce the load on your core, making it easier to keep your body straight from your head to your heels.
  *(c) Drill:* Practice the plank hold on your elbows or hands, focusing hard on squeezing your glutes and bracing your abs so your hips never drop.
  *(d) Self-check:* Notice that this fault only crops up on your later reps (reps 4, 6, 8, and 10)—as fatigue builds, your hips give out. 
* **Use the rep detail:** Notice that your form stays clean on the first three reps and only starts to break down on the later attempts (reps 4, 6, 8, and 10) when fatigue creeps in.

### Next Session Plan
1. **Cut the sets short:** Stop your sets one rep *before* your hips start to sag—quality over junk volume.
2. **Use an incline regression:** If you're hitting fatigue and letting your lower back arch by rep 4, drop the floor and elevate your hands on a higher surface so you can finish every rep with a flat back.
3. **Rest longer:** Give yourself a bit more recovery time between sets to let your core completely reset so you aren't carrying residual fatigue into your next push.

### WITH RAG (sample 3/3)
### Progress Tracking
Good work stepping back under the bar today—your overall score ticked up to 76 from 73 last session, and you matched your clean rep count with 6 solid reps completed. That said, your old habit is still hanging around: your lower back sagging or hips piking showed up on reps 4, 6, 8, and 10. Notice how it only happens in the back half of the set? That tells us your core endurance is giving out as you fatigue, causing your midsection to lose tension right when you need it most.

### Error Breakdown

* **What it is:** Your hips and lower back are sagging toward the floor or piking up instead of your whole body moving as a single, rigid plank.
* **Why it matters:** When your midsection gives out, your lower back takes on extra mechanical stress, dumping load straight onto your spinal discs. That costs you core stability and sets you up for a dull, nagging ache in your lower back by the time you finish your set.
* **How to fix it:** 
  - (a) Cue yourself to squeeze your glutes hard and brace your stomach as if someone is about to poke you in the gut before you even start descending.
  - (b) Set up with your hands directly under your shoulders and actively push the floor away to lock your upper back in place before initiating the rep.
  - (c) Try an incline push-up with your hands elevated on a sturdy bench or box to build your core strength without letting your hips sag under horizontal body weight.
  - (d) Record a quick video from the side and check if your hips and shoulders rise and fall together at the exact same time, or if your hips drop first.

### Next Session Plan
1. **Cut the set short when form slips:** Since your lower back starts sagging on the later reps (4, 6, 8, and 10), end your sets a rep or two before that breakdown happens so you only practice good movement.
2. **Prioritize mid-set rest:** Give yourself a full, honest rest between sets to let your core recover fully, ensuring you don't carry accumulated fatigue into your next round.

### WITHOUT RAG (sample 1/3)
### Progress Tracking
Great effort today! Your overall score ticked up slightly from 73 to 76, and you matched your previous count of 6 correct reps. The recurring issue from yesterday—letting your hips sag or pike—showed up again, appearing on reps 4, 6, 8, and 10. Notice how it didn't plague your entire set? It crept in exclusively during the second half of your workout as fatigue set in. Let's look at how to lock that down so you can carry your strong form all the way through to the final rep.

### Error Breakdown

*   **What it is, in plain words:** Your hips are dropping toward the floor or hiking up toward the ceiling instead of keeping your body in a straight, rigid line from your head to your heels.
*   **Why it matters:** When your midsection gives way, your lower back takes the brunt of the load instead of your core and chest sharing the work. That means you'll start feeling a dull ache in your lower back by the end of your set, costing you the abdominal engagement you're after and risking strain as you push heavier or higher-rep sets.
*   **How to fix it:** 
    *   (a) *Cue:* Imagine pulling your belt buckle toward your chin and squeezing your glutes hard like you're holding a coin between your cheeks.
    *   (b) *Setup change:* Move your feet slightly wider apart to create a more stable base of support before you start your set.
    *   (c) *Drill:* Drop your knees to the floor for a few strict sets to retrain your core tension, or elevate your hands on a sturdy bench to reduce the load on your midsection until you can hold the plank position cleanly.
    *   (d) *Self-check:* Glance at a mirror sideways or set your phone up to record—if your hips dip below your shoulder-to-heel line at any point, you'll see it instantly.

### Next Session Plan
1. **Watch the fatigue cliff:** Since your hip form broke down only on the even-numbered reps in the second half (4, 6, 8, and 10), cut your sets short just before your form starts to fray. Quality beats junk volume every time.
2. **Prioritise core tension:** Spend an extra 30 seconds setting up your plank position before you even bend your elbows on rep one. Squeeze your glutes and brace your abs before you make a move.

### WITHOUT RAG (sample 2/3)
### Progress Tracking
Great job showing upward momentum since yesterday! Your overall score ticked up from 73 to 76, and you matched your previous count of 6 correct reps. The good news is that old bugbear—letting your hips sag or pike—is still showing up, but notice *when* it happens: it didn’t touch your first three reps at all. It only crept in on reps 4, 6, 8, and 10 as fatigue set in later in the set. That tells us your strength is there, but your core stamina is fading toward the finish line. 

***

### Error Breakdown

*   **What it is, in plain words:** Your hips are dropping toward the floor or lifting up into the air like a tent, breaking the straight line from your shoulders to your heels.
*   **Why it matters:** When your midsection gives out, your lower back takes the brunt of the load instead of your core bracing the movement. That costs you strength and leaves your lower back feeling stiff or achy by the time you finish, while robbing your chest and arms of the stable platform they need to do the actual work.
*   **How to fix it:** 
    *   *(a) Cue:* Imagine balancing a full cup of water on your lower back, or squeeze your glutes hard as if you are trying to crack a walnut between your cheeks.
    *   *(b) Setup:* Shorten your sets. Since this only happened on the even-numbered reps in the second half of your set, stop at 3 clean reps today and build back up once your core endurance catches up.
    *   *(c) Drill:* Drop to an incline push-up with your hands on a sturdy bench or box to take some load off your midsection while you master keeping your body rigid.
    *   *(d) Self-check:* Glance at a mirror sideways or set your phone up to record; your shoulders, hips, and ankles should move together as one solid plank.

***

### Next Session Plan
1. **Cap your reps early:** Cut your sets off at 3 clean reps before fatigue ruins your form, taking a solid two-minute break between sets to let your core fully recover.
2. **Prioritize the plank:** Squeeze your glutes and brace your abs hard on every single rep, treating the push-up as a moving plank rather than just an arm exercise.

### WITHOUT RAG (sample 3/3)
### Progress Tracking
Good work on consistency today. Your overall score ticked up to 76 (from 73 in your last session), and you matched your previous count of 6 correct reps. That recurring issue with your hips dropping or piking is still hanging around—it popped up in your previous session and showed up again today—so it remains our primary target. The good news is you still powered through 6 clean reps before fatigue started pulling your form out of alignment. 

***

### Error Breakdown

* **What it is:** Your hips are sagging toward the floor or piking up toward the ceiling as you push, breaking the straight line from your shoulders to your ankles. This cluster of errors showed up exclusively in the second half of your set (reps 4, 6, 8, and 10), right as fatigue started to set in.
* **Why it matters:** When your midsection gives out, your lower back takes the brunt of the load instead of your core bracing the movement. You'll feel this as a dull ache in your lower back by the time you finish your set, and it robs your upper body and core of the stable platform they need to drive out maximum strength and muscle growth.
* **How to fix it:** 
  * *(a) Cue:* Think about pulling your belt buckle up toward your ribs and squeezing your glutes hard to lock your torso in place.
  * *(b) Setup change:* Drop your rep count on each set and stop one rep *before* your form breaks down—cut your working sets to 3 clean reps if that's where form holds, rather than grinding out ugly reps.
  * *(c) Drill:* Practice plank holds on your toes for 20 to 30 seconds to build the endurance your midsection needs to stay rigid during the push-up.
  * *(d) Self-check:* Glance at a mirror sideways or prop your phone up to record a set; if your hips drift lower or higher than your shoulders mid-rep, you'll see it instantly.

***

### Next Session Plan
1. **Prioritize quality over volume:** Keep your sets short and crisp. The moment your hips start to sag or pike—just like they did on reps 4, 6, 8, and 10 today—shut the set down immediately.
2. **Lock in the core:** Spend a minute practicing a tight plank before you start your push-ups to wake up the exact muscles you need to keep your hips level.

---

## Exercise: Push-up — partial_pushup

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| partial_pushup | Push-ups that stop too high: lowering only partway, so the chest stays far from the floor (+why/fix) | 0.122 / 1* | 0.219 / 2* | 0.200 / 1* | 0.189 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: partial_pushup | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Failing to complete the push-up by only rising one to two inches from the floor due to insufficient upper body strength.

[principle | re: partial_pushup | source: www.nasm.org/resource-center/blog/training/proper-push-up-form-and-technique-a-complete-guide]
Lower the body with control until the chest approaches the floor.

[consequence | re: partial_pushup | source: www.nasm.org/resource-center/exercise-library/push-up]
Not achieving adequate range of motion limits chest stretch and development.

[finding | re: partial_pushup | source: The_Effect_of_Position_on_the_Percentage_of_Body.992962]
The increased force in the down position of a push-up is due to the whole-body center of mass being located further from the point of contact with the floor, which results in greater torque.

[principle | re: partial_pushup | source: www.nasm.org/resource-center/exercise-library/push-up]
Descend until your chest nearly touches the floor or your elbows bend to approximately 90 degrees, whichever comes first based on mobility.

[finding | re: partial_pushup | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
In a study of active females, 45% of participants passed the Trunk Stability Push-Up (TSPU) post-intervention, with many of those who failed only able to rise one to two inches from the floor.
```

### WITH RAG (sample 1/3)
### Progress Tracking

Great to see a step forward since yesterday! Your overall score ticked up slightly from 74 to 75, and you matched your count of 7 solid, completed reps. The same stubborn issue—cutting your range of motion short—is still hanging around, appearing on your aborted attempts (reps 5, 7, and 9) where fatigue set in and you could only push an inch or two off the floor. You're fighting through the set, but those mid-set dips are where the form breaks down. Let's fix that so every rep counts.

### Error Breakdown

*   **What it is:** Stopping short and cutting the movement off early, getting stuck just an inch or two above the floor on attempts 5, 7, and 9 instead of finishing the press.
*   **Why it matters:** When you cut the depth and range of movement short, your chest misses out on the proper stretch and development it needs for growth. Because the bottom position of a push-up demands the most force—since your whole-body center of mass is furthest from your hands—short-changing that bottom part cheats your muscles out of the hard work that builds real strength.
*   **How to fix it:** 
    *   *(a) Cue:* Think about actively pushing the floor away from you while keeping your chest proud all the way to the bottom.
    *   *(b) Setup change:* Shorten your working sets by a rep or two, or switch to incline push-ups on a sturdy bench to keep your upper body strong enough to finish every single rep cleanly.
    *   *(c) Drill:* Practice kneeling push-ups or reduce your volume so you never hit the point of muscular failure where you get pinned an inch off the ground.
    *   *(d) Self-check:* Glance at your phone video or check the mirror to ensure your elbows bend to about a 90-degree angle and your chest gets close to the floor on every single try.

### Next Session Plan

*   **Drop the volume slightly:** Cut your working set down to 6 clean reps to avoid hitting that wall where attempts 5, 7, and 9 stalled out. Quality over grinding out half-reps.
*   **Elevate if needed:** If fatigue catches up to you again, elevate your hands on a stable surface for the final few reps so you can maintain a full range of motion without getting stuck.

### WITH RAG (sample 2/3)
### Progress Tracking

Solid effort today. You hit 7 correct reps out of 10 total attempts, nudging your overall score up slightly to 75 compared to 74 in your last session. That old issue with cutting your depth short—which tripped you up last time—showed up again today, but specifically when fatigue set in, causing you to stall out and abort attempts 5, 7, and 9 right near the bottom. 

***

### Error Breakdown

*   **What it is, in plain words:** You are cutting your reps short near the bottom, stalling out after pushing just an inch or two off the floor instead of pressing all the way back up to the top.
*   **Why it matters:** When you don't take your chest toward the floor, your chest muscles miss out on the deep stretch they need for maximum growth and development. If you skim on that range of motion, you get less muscle building for the exact same amount of effort.
*   **How to fix it:** 
    (a) **Cue:** Think about driving the floor away hard as soon as your elbows hit roughly a 90-degree bend or your chest gets close to the deck. 
    (b) **Setup:** Lower the load by shifting to an incline push-up on a sturdy bench or elevated bar so you can comfortably hit the full depth without stalling. 
    (c) **Drill:** Practice a set of knees-down push-ups focusing strictly on getting your chest all the way down and locked out at the top. 
    (d) **Self-check:** Glance in a mirror or set your phone up from the side to verify that your elbows reach about a 90-degree bend before you press back up.
*   **Rep detail note:** This wasn't an issue at the start of your set—reps 1 through 4 were clean. The breakdowns happened exclusively on your aborted attempts (5, 7, and 9) when upper-body fatigue caught up to you. Recognizing this pattern means you can pull the plug before form degrades.

***

### Next Session Plan

*   **Drop the volume slightly before failure:** Since your depth started failing on the middle-to-late attempts, stop your sets one or two reps *before* your form breaks down so every rep you log is high quality.
*   **Regulate your depth:** Use an elevated surface like a box or bench for your sets today if needed, ensuring you can hit full range of motion on every single rep without stalling near the floor.

### WITH RAG (sample 3/3)
### Progress Tracking

Great job showing up again. Compared to your last session on October 2nd, your overall score ticked up slightly from 74 to 75, and you matched your count with 7 fully completed reps. That said, your old habit—shortchanging your range of motion—is still hanging around, showing up as aborted attempts on reps 5, 7, and 9 where you couldn't press all the way back up. 

***

### Error Breakdown

*   **What it is, in plain words:** You are cutting your reps short—specifically on attempts 5, 7, and 9, where fatigue sets in and you stall out after rising just an inch or two off the floor, failing to finish the push.
*   **Why it matters:** When you don't push through a full range of motion, your chest muscles miss out on the deep stretch they need to trigger maximum muscle growth and development. Stopping short robs you of the full muscular benefit you're working for, leaving potential strength gains on the table.
*   **How to fix it:** 
    (a) **Cue:** Think about driving the floor away from you and pressing straight up until your elbows lock out completely on every single rep.
    (b) **Setup change:** If your upper body runs out of gas near the bottom of the movement, elevate your hands on a sturdy bench or plyo box to shorten the distance while still letting you hit full elbow extension.
    (c) **Drill:** Practice knee push-ups or eccentric-only push-ups (lowering yourself to the floor slowly over three seconds, then dropping to your knees to reset) to build up the upper-body strength required to clear the bottom portion of the lift.
    (d) **Self-check:** Keep an eye on your phone video or a mirror and watch your elbows: make sure they bend to roughly a 90-degree angle at the bottom and straighten fully at the top before you call the rep done.

***

### Next Session Plan

*   **Drop the elevation if needed:** If you start stalling out on your regular floor push-ups like you did on attempts 5, 7, and 9, elevate your hands slightly right away so you can maintain a clean, complete range of motion without aborting reps.
*   **Cap your sets:** Stop your working sets one rep *before* your form breaks down and you find yourself stuck near the floor, keeping the quality high.

### WITHOUT RAG (sample 1/3)
### Progress Tracking
Good effort out there today. Your overall score ticked up slightly from 74 to 75, and you matched your previous performance by nailing 7 correct reps. You still carried over one familiar issue from yesterday—partial reps—which popped up on your three aborted attempts (reps 5, 7, and 9). The good news is that your clean reps are solid; now we just need to keep that range of motion honest when fatigue sets in.

---

### Error Breakdown: Partial Reps

*   **What it is:** You're cutting the movement short and pushing back up before your chest gets close enough to the floor, specifically happening on those aborted attempts later in the set when fatigue starts creeping in.
*   **Why it matters:** When you shorten the range of motion, your chest and triceps don't go through a full stretch and contraction, meaning you miss out on the muscle-building stimulus you're working for. It rops you of a trustworthy rep count and lets you bypass the hardest part of the lift, which holds back your pushing strength as the weight gets more challenging.
*   **How to fix it:** 
    *   (a) *Cue:* Think about actively pulling your chest down to the floor, driving your entire torso down as a single solid unit before pressing away.
    *   (b) *Setup:* Slow down your tempo on the descent—take an extra second to lower yourself so you control the depth instead of rushing the turnaround.
    *   (c) *Drill:* Drop to an incline push-up on a sturdy bench or box for your final sets if you find your chest stalling out halfway down, which lets you hit full depth without your form breaking completely.
    *   (d) *Self-check:* Set your phone up side-on to record a set and watch whether your chest clearly reaches the bottom position on every single rep, or notice if your elbows are staying high and rigid early.

---

### Next Session Plan
1. **Pace your descent:** Don't let your speed increase as you get tired; control the way down on every rep to ensure you hit full depth.
2. **Cut the set when form drops:** On your next workout, if you feel yourself cutting reps short like you did on attempts 5, 7, and 9, stop the set right there rather than fighting through incomplete movement.

### WITHOUT RAG (sample 2/3)
### Progress Tracking

Solid effort today. You landed an overall score of 75, a slight tick up from 74 in your last session on October 2nd. Your correct rep count held steady at 7, and you kept the exact same number of incorrect reps (3). The familiar issue of cutting your depth short showed up again on attempts 5, 7, and 9, causing those three to abort before you finished the movement. You kept the core clean, though—no new errors crept in, and you punched out all 7 completed reps with solid execution. 

***

### Error Breakdown: Partial Push-up

* **What it is, in plain words:** You are cutting your descent short on the later half of the set instead of taking your chest all the way down to the floor. 
* **Why it matters:** When you shorten your range of motion, your chest and triceps miss out on the full stretch and workload they need to grow stronger. It leaves reps on the table that you can't truly trust, and it usually means fatigue is starting to take over your technique as you get deeper into the set.
* **How to fix it:**
  * (a) Cue: Think about actively pulling your chest down to an imaginary target an inch off the floor on every single descent.
  * (b) Setup change: Take a brief, one-second pause at the top of each rep to reset your tension before you drop back down.
  * (c) Drill: Drop to your knees for the final few reps when fatigue hits, letting you finish out the full range of motion without cutting corners.
  * (d) Self-check: Have a training partner watch your side profile or prop your phone up to check that your chest consistently hits the bottom marker on every rep, especially when you start getting tired.

***

### Next Session Plan

1. **Protect your depth early:** Focus on hitting that full bottom position right from rep 1 so it sets the standard for the whole set.
2. **Cut the set short before form breaks:** Since your depth started failing on attempts 5, 7, and 9, try stopping your working sets one rep before fatigue forces you to cut the range short. 
3. **Use a pause:** Keep that intentional pause at the top of your push-ups to stay tight and organized throughout the workout.

### WITHOUT RAG (sample 3/3)
### Progress Tracking
Good effort today. You hit 7 clean, completed reps and scored a 75 overall, a slight nudge up from 74 in your last session. You also kept the exact same number of correct reps (7) as yesterday. The catch is that your error count stayed locked at 3—specifically on attempts 5, 7, and 9, where you cut the movement short and aborted before finishing the rep. That old habit of incomplete depth ("partial_pushup") is sticking around, so let's clear it out.

### Error Breakdown

* **What it is, in plain words:** You are cutting your depth short on attempts 5, 7, and 9, pushing back up before your chest gets down to the floor.
* **Why it matters:** Short-changing your range of motion means your chest, triceps, and shoulders don't go through a full stretch and contraction, leaving you with less muscle growth and strength gains for the same amount of effort. Worse, it tends to creep in as fatigue sets in during the later part of your set, meaning you're bailing out early just when the muscle is supposed to be doing the hardest work.
* **How to fix it:**
  - (a) Cue: Think about actively pulling your chest down to lightly touch the floor on every single descent.
  - (b) Setup change: Narrow your focus to tempo—slow down the way down so you actually hit the bottom position before reversing.
  - (c) Drill: Drop to an incline push-up on a sturdy bench or box for your next session to groove the full range of motion without failing halfway down.
  - (d) Self-check: Have a partner watch your side profile or film your set on your phone to confirm your chest actually reaches the bottom position before you push back up.

### Next Session Plan
1. **Pace your reps:** Don't rush the descent, especially on the back half of the set where you started cutting them short today.
2. **Use a depth target:** If hitting the floor is too tough by rep 5, place a small, soft target (like an ab mat or yoga block) under your chest so you have a physical marker to aim for every time. 
3. **Cut the set earlier if needed:** If fatigue causes you to abort or cut depth by rep 5 again, finish the set cleanly there instead of grinding out half-reps.

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

### WITH RAG (sample 1/3)
### Progress Tracking
You landed 4 correct reps out of 10 total entries today, giving you an overall score of 65. Compared to your last session on October 2nd, your correct rep count dropped by one (from 5 to 4), your incorrect count ticked up (from 5 to 6), and your overall score dipped slightly from 71. The good news: both of your recurring faults—letting your hips sag or pike and cutting your range of motion short—showed up again, meaning you haven't cleared them yet, but your first two reps today were clean, solid movement. 

---

### Lower back sagging or hips piking
- **What it is:** Your hips and lower back give way, causing your midsection to dip toward the floor or pike upward instead of your entire upper and lower body moving as a single, rigid plank.
- **Why it matters:** When your midsection sags, your lower back soaks up extra mechanical stress on the vertebral discs. That's the nagging ache in your spine that creeps up mid-set, and it strips away the core stability you need to press heavy loads safely.
- **How to fix it:** 
  - (a) **Cue:** Squeeze your glutes hard and brace your stomach as if someone is about to poke you in the ribs before you even start descending.
  - (b) **Setup change:** Elevate your hands on a sturdy bench or box to lessen the load on your core until you can hold a flat plank for the entire set.
  - (c) **Drill:** Practice a standard floor plank holding your body totally rigid for 20 to 30 seconds to build the deep core bracing you are losing as fatigue sets in.
  - (d) **Self-check:** Set your phone up to record from the side—your shoulders, hips, and ankles should move together in a straight line without your hips lagging behind.

---

### Partial push-up (not going deep enough)
- **What it is:** You cut the bottom of the movement short—seen clearly in your aborted attempts 5, 8, and 10, where you only managed to push an inch or two off the bottom or failed to press back up at all.
- **Why it matters:** Stopping short robs your chest of the deep stretch it needs for optimal muscle development. You miss out on the full range of motion, meaning less muscle growth for the exact same effort.
- **How to fix it:** 
  - (a) **Cue:** Imagine pulling your chest down actively toward the floor until your elbows hit roughly a 90-degree bend or your chest nearly touches.
  - (b) **Setup change:** Slow down your descent and pause for a split second just above the floor before pressing back up to eliminate momentum.
  - (c) **Drill:** Drop to your knees for a lighter regression to ensure you can hit the bottom position cleanly without stalling out.
  - (d) **Self-check:** Watch for your elbows to bend to about 90 degrees on every single rep before you reverse direction.

---

### Next Session Plan
1. **Drop the volume slightly or scale early:** Since your faults and aborted attempts clustered heavily in the back half of the set as fatigue set in, stop your working sets a rep or two *before* your form breaks down.
2. **Prioritize core bracing:** Spend two minutes practicing a static plank before you start your push-ups to wake up the deep core muscles that kept letting your lower back sag today.

### WITH RAG (sample 2/3)
### Progress Tracking

Your overall score slipped a bit from 71 to 65, and your correct rep count dropped from 5 down to 4 out of 10 total attempts (which included 3 aborted tries). Both of the errors from your last session—letting your hips sag and cutting your depth short—are still following you, and they showed up heavily as fatigue settled in toward the second half of your set. 

***

### Hips Sagging or Piking

*   **What it is:** Your midsection gives way and your lower back arches or sags toward the floor instead of your whole body moving as a single, rigid plank.
*   **Why it matters:** When your core switches off and your lower back dips, extra mechanical stress dumps directly into your vertebral discs. That’s the dull ache in your lower back that lingers after a set, and it costs you the solid body tension needed to press heavy loads safely.
*   **How to fix it:** 
    *   *Cue:* Squeeze your glutes hard and brace your stomach as if someone is about to poke you in the ribs before you even start moving.
    *   *Setup:* Keep your spine neutral and focus on moving your chest and hips up at the exact same time so your trunk never lags behind.
    *   *Drill:* Drop your knees to the floor for a regressed push-up to rebuild your midsection strength, or pause for a second in a high plank to check your alignment before lowering.
    *   *Self-check:* Record your set on your phone and look to see if your hips drop first when you start getting tired.
*   **Rep Detail:** This fault started creeping in on rep 3, showed up on aborted attempt 5, and returned on reps 6, 9, and 10 as fatigue took over.

***

### Partial Push-Up Range of Motion

*   **What it is:** You are cutting the movement short, pushing back up before your chest gets close to the floor.
*   **Why it matters:** If you don't lower yourself fully, you miss out on the deep stretch across your chest. That means less muscle growth for the exact same amount of effort, and it leaves your strength incomplete at the hardest part of the lift.
*   **How to fix it:** 
    *   *Cue:* Lower yourself under control until your chest nearly touches the floor or your elbows hit about a 90-degree bend.
    *   *Setup:* Slow down your descent so you aren't rushing the bottom portion where the hardest leverage lives.
    *   *Drill:* Practice incline push-ups with your hands on a sturdy elevated surface like a bench to make full depth manageable.
    *   *Self-check:* Have a gym partner watch from the side to confirm your chest gets close to the floor on every single rep.
*   **Rep Detail:** This error clustered entirely in your aborted attempts (attempts 5, 8, and 10), where you couldn't drive yourself back up out of the bottom.

***

### Next Session Plan

1. **Cut the set short before form breaks:** When you feel your lower back start to arch or your hips begin to sag—typically around rep 3 or 6 based on today—stop the set immediately rather than grinding out sloppy reps.
2. **Elevate your hands if needed:** If you find yourself cutting your depth short on attempts 8 through 10, elevate your hands on an incline to ensure you can hit full depth with a rigid core.

### WITH RAG (sample 3/3)
### Progress Tracking

Your overall score dipped slightly to 65 today compared to 71 in your last session, and your correct rep count dropped from 5 down to 4 out of your 10 total attempts (which included 3 aborted tries where you had to cut the movement short). Both of your familiar form faults—letting your hips sag and cutting your range of motion short—showed up again today, meaning neither of them has cleared out just yet. 

---

### Hips Sagging or Piking

* **What it is:** Your midsection gives way and your lower back arches or sags toward the floor as you push, meaning your hips and chest stop moving as a single solid piece. This crept in mostly during your later reps and aborted attempts as fatigue set in.
* **Why it matters:** When your trunk lags and your lower back dips, it piles extra mechanical stress directly onto your vertebral discs. That sets you up for a dull ache or sharp pinch in your lower back right in the middle of a set, robbing your core of the stability it needs to keep your power output high.
* **How to fix it:**
  * **Cue:** Think about bracing your stomach as if someone is about to poke you in the gut, and tuck your tailbone slightly under to lock your pelvis in place.
  * **Setup:** Drop your knees to the floor for your sets if your hips start sagging toward the end of your workout, keeping that plank line unbroken from knees to shoulders.
  * **Drill:** Practice holding a standard front elbow plank on the floor for 20 to 30 seconds at a time to build up the deep core endurance required to keep your spine flat.
  * **Self-check:** Set your phone up to record a video from the side—your shoulders, hips, and ankles should move up and down together as one rigid board.

---

### Partial Range of Motion

* **What it is:** You are cutting the push-up short by failing to lower your body all the way down, or in the case of your aborted attempts (like reps 5, 8, and 10), stalling out just an inch or two above the floor when your upper body strength gives out.
* **Why it matters:** If you skip the bottom portion of the movement, you cheat your chest out of the deep stretch it needs to trigger maximum muscle development. You end up doing all the hard work at the top where leverage is easier, leaving your growth and strength gains sitting on the table.
* **How to fix it:**
  * **Cue:** Imagine actively pulling your chest down toward the floor on the way down, aiming to bend your elbows to about a 90-degree angle.
  * **Setup:** Elevate your hands on a sturdy bench or box if you find yourself stalling out an inch or two off the floor on later reps—a higher starting point lets you hit full depth cleanly.
  * **Drill:** Drop into an incline push-up against a wall or counter height where you can comfortably control the entire descent until your chest nearly touches.
  * **Self-check:** Glance in a mirror or check your side-view video to confirm your elbows hit that 90-degree bend before you press back up.

---

### Next Session Plan

1. **Prioritize quality over volume:** Stop your sets one or two reps *before* your hips start sagging and your form breaks down. It is far better to finish a clean set of 3 than grind out ugly reps 5 through 10.
2. **Elevate your hands if needed:** If you start stalling out just an inch off the floor like you did on reps 5, 8, and 10, shift your hands to an elevated surface immediately to protect your range of motion.
3. **Build your core baseline:** Add two rounds of 30-second front planks at the end of your workout to specifically target the trunk stability that let you down on your later reps today.

### WITHOUT RAG (sample 1/3)
### Progress Tracking

Your overall score dipped slightly from 71 to 65, and you landed 4 clean reps out of 10 total attempts today, compared to 5 out of 10 in your last session. The good news is you are still battling the exact same two faults—sagging or piking your hips and cutting your depth short—which means your movement patterns are predictable and entirely fixable. Let's clean them up so your numbers go back up next time.

---

### Error Breakdown

*   **What it is, in plain words:** Your hips are sagging down toward the floor or piking up toward the ceiling as you push, instead of keeping your whole body locked in a straight line from head to heels.
*   **Why it matters:** Your lower back and midsection take the strain instead of your chest and shoulders sharing the load evenly. That translates to an aching lower back by the time you hit the middle of your set, and it drains your core strength so you cannot press as many clean reps.
*   **How to fix it:**
    *   (a) Cue to think about: Squeeze your glutes and brace your stomach as if someone is about to poke you in the gut.
    *   (b) Setup change: Narrow your stance slightly or squeeze your thighs together to lock your lower half in place before you even start moving.
    *   (c) Drill or lighter regression: Drop your knees to the floor for a few sets to rebuild core tension without your hips giving out.
    *   (d) Self-check: Glance at a mirror sideways or set your phone up to record—if your belt line drops before your chest does, you've spotted the sag.

*   **What it is, in plain words:** You are cutting the movement short and pushing back up before your chest gets close enough to the floor.
*   **Why it matters:** Your chest and triceps never go through their full range of motion, meaning you get less muscle growth for the exact same amount of effort and build a false sense of how strong your push-ups actually are.
*   **How to fix it:**
    *   (a) Cue to think about: Pull your chest down to an imaginary target an inch off the floor on every single descent.
    *   (b) Setup change: Slow your tempo down on the way down so you actually hit the bottom position before reversing direction.
    *   (c) Drill or lighter regression: Elevate your hands on a sturdy bench or box so you can hit full depth comfortably without failing halfway.
    *   (d) Self-check: Notice whether your elbows break past a 90-degree bend at the bottom—if they stay flared high and wide, you haven't gone deep enough.

---

### Next Session Plan

1.  **Prioritise clean reps over total volume:** Aim for sets of 3 to 4 reps where your hips do not sag and your chest touches down, rather than grinding out sloppy attempts.
2.  **Rest longer between sets:** Give yourself a full 90 seconds to catch your breath so your core fatigue doesn't cause your hips to cave in early.
3.  **Film your second set:** Check the video before your third set to see if your depth is shrinking or your hips are lifting.

### WITHOUT RAG (sample 2/3)
### Progress Tracking
Let's look at how today stacked up against your last session. Your overall score slipped slightly from 71 to 65, and your clean rep count dropped from 5 down to 4 out of 10 total attempts (which included 3 aborted attempts). 

The good news? You are dealing with the exact same two faults as last time—`hip_sag_or_pike` and `partial_pushup`—meaning we know the exact targets to hit. Fatigue clearly caught up with you in the second half of the set, as all of your errors clustered in reps 3 through 10. Let's lock those down so your next session looks much sharper.

---

### Error Breakdown

*   **What it is, in plain words:** Your hips are dipping toward the floor or hiking up toward the ceiling (which shows up on reps 3, 5, 6, 9, and 10), turning your straight body line into a banana shape.
*   **Why it matters:** Your lower back and midsection take the strain instead of your core bracing the weight, which costs you total-body tension and invites a dull ache in your lower back right when you need your strength most.
*   **How to fix it:** 
    *   (a) Cue: Think about squeezing your glutes hard and pulling your belly button toward your spine as one solid unit before you even start moving.
    *   (b) Setup change: Narrow your stance slightly or drop your working volume so you aren't trying to grind out reps with a tired core.
    *   (c) Drill: Drop to an incline push-up with your hands on a sturdy bench to take the pressure off your midsection while you rebuild your plank strength.
    *   (d) Self-check: If you glance at your phone video or a mirror, your shoulders, hips, and ankles should move together like a plank of wood without any sag in the middle.

*   **What it is, in plain words:** You're cutting the movement short (seen on aborted attempts 5, 8, and 10, plus rep 5), meaning your chest doesn't get close enough to the floor before you push back up.
*   **Why it matters:** You cheat your chest and triceps out of the full range of motion they need to grow stronger, leaving you with easy reps that don't build the actual muscle you're after.
*   **How to fix it:**
    *   (a) Cue: Pick a target spot on the floor right between your thumbs and aim your chest directly at it.
    *   (b) Setup change: Slow down your descent—take a full two seconds to lower yourself so you control the bottom position rather than rushing back up.
    *   (c) Drill: Pause for a full one-second dead-stop at the bottom with your chest hovering just above the floor before pressing up.
    *   (d) Self-check: Feel for your chest touching or nearly brushing the floor on every single descent before you reverse direction.

---

### Next Session Plan

1. **Cut the set short before form breaks:** You started leaking form around rep 3 today. Next time, stop your set one rep *before* your hips start sagging or your depth gets shallow—quality over junk volume.
2. **Prioritize a rigid plank:** Spend an extra five seconds setting up your core and squeezing your glutes before your very first rep to establish that straight-line tension.
3. **Slow down the tempo:** Count a clear two-second descent on every rep to ensure you hit full depth without having to bail out early.

### WITHOUT RAG (sample 3/3)
### Progress Tracking

Your overall score dipped slightly to 65 today compared to 71 in your last session, and you landed 4 correct reps out of 10 total attempts (which includes 3 aborted tries). That is a slight step back from your 5 correct reps last time. The good news is you are still fighting through the set, but fatigue in the later half is clearly catching up to you—especially on attempts 8 through 10, where form broke down early and forced you to bail. 

---

### Error Breakdown

*   **What it is, in plain words:** Your hips are sagging toward the floor or hiking up toward the ceiling instead of keeping your whole body locked in a straight line. This showed up on rep 3, rep 6, rep 9, and mixed in with your aborted attempts on rep 5 and rep 10.
*   **Why it matters:** When your midsection gives way, your lower back has to absorb the stress instead of your core holding everything stable. That costs you strength and leaves your lower back feeling strained and cranky by the end of a set, while robbing your chest and arms of the solid platform they need to push effectively.
*   **How to fix it:** 
    *   (a) *Cue:* Think about squeezing your glutes hard and pulling your belly button in toward your spine as if you are bracing for a punch.
    *   (b) *Setup:* Narrow your stance slightly if your feet are too wide, or shorten your set length—stop at 6 reps before fatigue breaks your form.
    *   (c) *Drill:* Practice the plank hold on the floor or with your hands elevated on a bench to build the core endurance you need to lock your hips in place.
    *   (d) *Self-check:* Look at a side-profile video of your set to see if your hips drop or pike the moment you start pushing back up.

*   **What it is, in plain words:** You are cutting your range of motion short and pushing back up before your chest gets close to the floor. This happened on attempt 8, and also showed up alongside your hip sagging on aborted attempts 5 and 10 as fatigue set in.
*   **Why it matters:** Halting your descent halfway means your chest and triceps never go through their full working range, which gives you less muscle growth for the effort and leaves you with reps you cannot genuinely trust.
*   **How to fix it:** 
    *   (a) *Cue:* Pick a target spot on the floor right between your hands and aim to tap your chest or chin to that exact level on every single rep.
    *   (b) *Setup:* Elevate your hands slightly on a sturdy box or bench for your working sets to make the full range of motion achievable without your form collapsing.
    *   (c) *Drill:* Drop to an incline push-up on a higher surface where you can comfortably touch your chest to the target every time without cutting corners.
    *   (d) *Self-check:* Feel for your chest making light contact with the floor—or a marker you set below you—before you press back up.

---

### Next Session Plan

1. **Cut the reps short:** Next time, stop your sets a rep or two *before* your hips start sagging and your depth starts shrinking (aim for clean sets of 3 or 4 high-quality reps rather than grinding out ugly ones).
2. **Elevate if needed:** If full floor push-ups cause your form to break down past rep 4, use an elevated surface for your hands so you can own the full depth and keep your core rock-solid from start to finish.

---

## Exercise: Push-up — clean

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| general principles | Push-up correct technique and biomechanics | — | — | — | 0.187 / 2 |

### Retrieved KB Context (RAG run)
```text
[principle | re: general principles | source: The_Effect_of_Position_on_the_Percentage_of_Body.992962]
The difference in resistance patterns between push-up variations is influenced by differing moment arms between the support surface contact point (knees or feet) and the hands.

[principle | re: general principles | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Maintaining a neutral lumbar spine position and control is necessary to prevent anterior pelvic tilt and trunk lag during the push-up.
```

### WITH RAG (sample 1/3)
### Progress Tracking

Fantastic session today! You completely turned things around since yesterday. Your overall score jumped from 75 up to 88, and you nailed all 10 reps cleanly with zero errors. Even better, you successfully cleared both of the recurring issues from your last workout—your hips stayed locked in place and you hit full depth on every single rep. That is the kind of consistency we love to see.

### Next Session Plan

* **Hold the standard:** Keep your core just as tight and your movement just as full next time you step up to the floor. Do not let fatigue rush your reps.
* **Lock in your setup:** Take a deliberate breath and brace your midsection before you even start rep one, making sure your plank position looks solid right out of the gate.

### WITH RAG (sample 2/3)
### Progress Tracking

Fantastic session today. You nailed all 10 reps cleanly with zero errors, bumping your overall score up to 88 compared to 75 yesterday. Even better, you completely cleared both faults from your last workout—the hips staying solid means your midsection control is locking in, and every single rep went through the full range of motion. 

### Next Session Plan

1. **Hold the standard:** Keep your setup identical next time—same body tension, same full-depth press.
2. **Lock in the win:** Let this clean session be your new baseline. When the weight or reps go up next time, do not let your form slip to chase extra numbers.

### WITH RAG (sample 3/3)
### Progress Tracking
Huge step forward today! You completely wiped out the hip sag and partial range issues that held you back in your last session on October 2nd. Your overall score jumped from 75 up to 88, and you nailed all 10 reps cleanly with zero errors flagged. 

### Next Session Plan
1. **Hold the line:** You just hit a completely clean set. Lock in the feeling of keeping your body completely rigid from head to toe for your next workout.
2. **Keep the same load and setup:** Don't change a thing about your hand placement or stance—just replicate the exact execution you brought to the floor today.

### WITHOUT RAG (sample 1/3)
### Progress Tracking

Massive improvements since yesterday! You bumped your overall score up from 75 to 88, and more importantly, you nailed all 10 reps cleanly with zero errors. That means you completely wiped out both major issues from your last session—your hips stayed locked in place and you hit full depth on every single rep instead of cutting them short. That is a huge win.

### Next Session Plan

1. **Lock in the standard:** Hold this exact same form and pacing for your next session. Do not rush to add reps or speed up until locking out all 10 clean reps feels automatic.
2. **Focus on quality over volume:** If you decide to push for more reps next time, stop the exact moment your hips start to drop or your elbows flare wide. Keep your standards high.

### WITHOUT RAG (sample 2/3)
### Progress Tracking

Great work on this session—you completely turned things around since yesterday. Your overall score jumped from 75 to 88, and you nailed all 10 reps cleanly without a single error. Most importantly, you completely wiped out the hip sagging and partial depth issues that were dragging down your score in your previous session. 

### Next Session Plan

1. **Hold the standard:** Keep your body locked in a tight, straight line from your shoulders to your ankles on every single rep, exactly as you did today.
2. **Lock in your depth:** Maintain the full chest-to-floor range of motion that earned you all 10 clean reps this time around. 
3. **Maintain your setup:** Take the exact same strong, stable stance at the start of your next workout to keep those old form leaks from creeping back in.

### WITHOUT RAG (sample 3/3)
### Progress Tracking

Great work on this session—you completely turned things around since yesterday. You brought your overall score up from 75 to 88, and hit 10 clean, completed reps without a single incorrect rep or aborted attempt dragging you down. Even better, you completely cleared out both previous issues: your hips stayed locked in place (no more sagging or piking), and you hit full depth on every single rep instead of cutting them short. 

### Next Session Plan

1. **Lock in the standard:** Your form was rock solid today, so your primary goal for the next workout is simply to repeat this exact performance without letting your standards slip as fatigue sets in.
2. **Keep the same pacing:** Whatever tempo and setup you used today worked—don't rush your reps or try to muscle through changes. Keep your core braced and your movement identical next time out.

---


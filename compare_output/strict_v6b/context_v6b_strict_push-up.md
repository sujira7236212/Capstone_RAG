# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions_push-up.json` |
| query mode | **taxonomy** — `error_type` resolved through `error_taxonomy.py` |
| collection | `kb_gemini_curated_v6b` |
| LLM | `gemini-3.5-flash-lite` @ temperature 0.7 |
| no-RAG side | skipped |
| generation | **off** — `--context-only`: context and metrics only, no LLM call |
| samples per session | 0 |
| retrieval gates | CANDIDATE_K=12, MAX_PER_KIND={'mistake': 3, 'finding': 2, 'principle': 2, 'consequence': 2}, ABS_DISTANCE_CAP={'mistake': 0.4, 'finding': 0.4, 'principle': 0.4, 'consequence': 0.4}, RELATIVE_MARGIN=0.03, NEAR_DUP_JACCARD=0.72, TAG_MODE=strict, KIND_POOL=split, QUERIES=profile, HYBRID=False, RERANK=False |

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
| hip_sag_or_pike | Failing to hold a straight plank line in the push-up: the hips sagging toward the floor with the lower back arching, or the hips piking up toward the ceiling (+why/fix) | 0.074 / 3* | 0.238 / 2* | 0.093 / 2* | 0.137 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: hip_sag_or_pike | source: www.acefitness.org/resources/pros/expert-articles/7265/perfecting-the-push-up-for-all-levels]
Failing to activate the deep core muscles required to stabilize the spine and pelvis during the push-up.

[consequence | re: hip_sag_or_pike | source: BOXROX_PushUpBenchmarks]
Failing to brace the abdominals and glutes during push-ups allows the lower back to extend into excessive arching.

[mistake | re: hip_sag_or_pike | source: Biomechanical evaluation of the push-up exercise of the upper extremities from various starting points]
Allowing incorrect and damaging inclinations of the torso during the push-up.

[principle | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Maintaining a neutral lumbar spine position and control is necessary to prevent anterior pelvic tilt and trunk lag during the push-up.

[mistake | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Anterior pelvic tilt and trunk lag are common errors where the trunk fails to lift as a single unit during the push-up.

[consequence | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Failing to maintain a neutral lumbar spine position during a push-up results in anterior pelvic tilt and trunk lag, indicating impaired trunk stability.

[principle | re: hip_sag_or_pike | source: Cathe_PushUpMistakes]
Perform planks on a regular basis to build the core stability required to hold proper alignment during push-ups.

[finding | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
More than 60% (n=65/108) of active females failed the Trunk Stability Push Up (TSPU) compared to less than 10% (n=10/101) of active males.

[finding | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
In a pilot study of active females, a six-week multiplanar trunk stability intervention resulted in 9 of 20 participants (45%) improving their Trunk Stability Push Up (TSPU) score to ≥2.
```

---

## Exercise: Push-up — partial_pushup

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| partial_pushup | Push-ups that stop too high: lowering only partway, so the chest stays far from the floor (+why/fix) | 0.100 / 3* | 0.184 / 2* | 0.111 / 2* | 0.187 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: partial_pushup | source: Cathe_PushUpMistakes]
Performing a short-range push-up by lowering down only far enough to partially bend the elbows.

[consequence | re: partial_pushup | source: Attika_PushUpErrors]
Stopping far above the ground in a partial push-up prevents the chest muscles from working to their full potential.

[mistake | re: partial_pushup | source: BOXROX_PushUpBenchmarks]
Performing partial repetitions where the chest does not lower close to the floor.

[consequence | re: partial_pushup | source: AthleanX_PushUpRangeOfMotion]
Failing to lower the chest completely to the floor reduces the total work required of the upper body, limiting potential strength and muscle development.

[mistake | re: partial_pushup | source: Attika_PushUpErrors]
Performing partial reps by only bending the elbows slightly and stopping far above the ground.

[finding | re: partial_pushup | source: Cathe_PushUpMistakes]
Full range of motion in a push-up requires descending until the elbows reach an angle of 90 degrees or less.

[principle | re: partial_pushup | source: Biomechanical evaluation of the push-up exercise of the upper extremities from various starting points]
Lower the body toward the floor until achieving 90 degrees of elbow flexion, bringing the chest as close to the ground as possible before pushing up.

[principle | re: partial_pushup | source: Attika_PushUpErrors]
Perform a full range of motion by lowering until the chest nearly touches the floor, ensuring the chest leads the way down rather than the belly or chin.

[finding | re: partial_pushup | source: AthleanX_PushUpRangeOfMotion]
Switching to a full range of motion where the chest reaches the ground can reduce push-up repetition performance by approximately 60%, dropping rep output from 100 down to 40.
```

---

## Exercise: Push-up — mixed

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| hip_sag_or_pike | Failing to hold a straight plank line in the push-up: the hips sagging toward the floor with the lower back arching, or the hips piking up toward the ceiling (+why/fix) | 0.074 / 3* | 0.238 / 2* | 0.093 / 2* | 0.137 / 2* |
| partial_pushup | Push-ups that stop too high: lowering only partway, so the chest stays far from the floor (+why/fix) | 0.100 / 3* | 0.184 / 2* | 0.111 / 2* | 0.187 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: hip_sag_or_pike | source: www.acefitness.org/resources/pros/expert-articles/7265/perfecting-the-push-up-for-all-levels]
Failing to activate the deep core muscles required to stabilize the spine and pelvis during the push-up.

[consequence | re: hip_sag_or_pike | source: BOXROX_PushUpBenchmarks]
Failing to brace the abdominals and glutes during push-ups allows the lower back to extend into excessive arching.

[mistake | re: partial_pushup | source: Cathe_PushUpMistakes]
Performing a short-range push-up by lowering down only far enough to partially bend the elbows.

[consequence | re: partial_pushup | source: Attika_PushUpErrors]
Stopping far above the ground in a partial push-up prevents the chest muscles from working to their full potential.

[mistake | re: hip_sag_or_pike | source: Biomechanical evaluation of the push-up exercise of the upper extremities from various starting points]
Allowing incorrect and damaging inclinations of the torso during the push-up.

[principle | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Maintaining a neutral lumbar spine position and control is necessary to prevent anterior pelvic tilt and trunk lag during the push-up.

[mistake | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Anterior pelvic tilt and trunk lag are common errors where the trunk fails to lift as a single unit during the push-up.

[consequence | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
Failing to maintain a neutral lumbar spine position during a push-up results in anterior pelvic tilt and trunk lag, indicating impaired trunk stability.

[principle | re: hip_sag_or_pike | source: Cathe_PushUpMistakes]
Perform planks on a regular basis to build the core stability required to hold proper alignment during push-ups.

[mistake | re: partial_pushup | source: BOXROX_PushUpBenchmarks]
Performing partial repetitions where the chest does not lower close to the floor.

[consequence | re: partial_pushup | source: AthleanX_PushUpRangeOfMotion]
Failing to lower the chest completely to the floor reduces the total work required of the upper body, limiting potential strength and muscle development.

[mistake | re: partial_pushup | source: Attika_PushUpErrors]
Performing partial reps by only bending the elbows slightly and stopping far above the ground.

[finding | re: partial_pushup | source: Cathe_PushUpMistakes]
Full range of motion in a push-up requires descending until the elbows reach an angle of 90 degrees or less.

[principle | re: partial_pushup | source: Biomechanical evaluation of the push-up exercise of the upper extremities from various starting points]
Lower the body toward the floor until achieving 90 degrees of elbow flexion, bringing the chest as close to the ground as possible before pushing up.

[principle | re: partial_pushup | source: Attika_PushUpErrors]
Perform a full range of motion by lowering until the chest nearly touches the floor, ensuring the chest leads the way down rather than the belly or chin.

[finding | re: partial_pushup | source: AthleanX_PushUpRangeOfMotion]
Switching to a full range of motion where the chest reaches the ground can reduce push-up repetition performance by approximately 60%, dropping rep output from 100 down to 40.

[finding | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
More than 60% (n=65/108) of active females failed the Trunk Stability Push Up (TSPU) compared to less than 10% (n=10/101) of active males.

[finding | re: hip_sag_or_pike | source: SchwartzkopfPhifer2021_TrunkStabilityPushUp_IJSPT]
In a pilot study of active females, a six-week multiplanar trunk stability intervention resulted in 9 of 20 participants (45%) improving their Trunk Stability Push Up (TSPU) score to ≥2.
```

---

## Exercise: Push-up — clean

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| general principles | Push-up correct technique and biomechanics | — | — | — | 0.187 / 2 |

### Retrieved KB Context (RAG run)
```text
[principle | re: general principles | source: Biomechanical evaluation of the push-up exercise of the upper extremities from various starting points]
Maintain straight alignment between the shoulder, ischium, and lateral malleolus throughout the push-up.

[principle | re: general principles | source: The_Effect_of_Position_on_the_Percentage_of_Body.992962]
The difference in resistance patterns between push-up variations is influenced by differing moment arms between the support surface contact point (knees or feet) and the hands.
```

---


# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions_lunge.json` |
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

## Exercise: Lunge — shallow_lunge

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| shallow_lunge | Lunging too shallow: dipping only slightly, so the front knee stays far from a 90-degree bend and the front thigh stays well above parallel (+why/fix) | 0.135 / 3* | 0.226 / 2* | 0.265 / 2* | 0.157 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: shallow_lunge | source: basics_of_strength_and_conditioning_manual]
Failing to lower the hips until the front thigh is parallel to the floor.

[principle | re: shallow_lunge | source: Trunk and Shank Position Influences Patellofemoral Joint Stress in the Lead and Trail Limbs During the Forward Lunge Exercise]
To achieve proper depth during a lunge, descend until the trail knee is just prior to touching the ground.

[mistake | re: shallow_lunge | source: Biomechanical Analysis of the Anterior Lunge During 4 External-Load Conditions]
Lifters tend to cut lunge depth short when handling heavier external loads, failing to lower their center of mass to full depth.

[mistake | re: shallow_lunge | source: Influence of Different Load Conditions on Lower Extremity Biomechanics during the Lunge Squat in Novice Men]
Exhibiting small knee flexion during a lunge indicates underlying issues such as quadriceps weakness or a limited ankle dorsiflexion range.

[principle | re: shallow_lunge | source: BOXROX_WalkingLungeMistakes]
Proper lunge depth occurs when the back knee gently touches or comes very close to the ground under control.

[finding | re: shallow_lunge | source: Effects of Loading Positions on Lower Limb Biomechanics During Lunge Squat in Men with Different Training Experience]
During backward barbell lunges, novices achieved a shallower peak knee flexion with a minimal sagittal angle of -99.01 ± 10.02 degrees compared to -108.44 ± 8.33 degrees in experienced lifters.

[finding | re: shallow_lunge | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
During a forward lunge, a shallower front knee flexion angle of 80° results in a statistically significantly higher knee extensor moment (0.980 Nm/BW) compared to 90° (0.717 Nm/BW) and 100° (0.362 Nm/BW).

[consequence | re: shallow_lunge | source: BOXROX_WalkingLungeMistakes]
Cutting depth reduces muscle growth and motor unit recruitment because muscles grow more when stretched through a full range of motion.

[consequence | re: shallow_lunge | source: Jaeggi2024_SplitSquat_RearLegMuscleForces_JFMK]
Failing to sufficiently activate the m. gluteus maximus reduces the generation of posterior shear forces at the tibia, which otherwise potentially contribute to a reduced likelihood of knee injuries.
```

---

## Exercise: Lunge — excessive_front_knee_flexion

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| excessive_front_knee_flexion | Sinking too deep in the lunge: the hips dropping below the level of the front knee, so the front knee folds far past 90 degrees and takes extra load (+why/fix) | 0.088 / 3* | 0.126 / 2* | 0.148 / 2* | 0.125 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: excessive_front_knee_flexion | source: Zellmer2019_KneePastToes_PatellarTendon_Lunge_JSHS]
Allowing the front knee to translate forward in front of the toes during the descending phase of a forward step lunge.

[principle | re: excessive_front_knee_flexion | source: Bezerra2021_TrunkPosition_LungeActivation_IJES]
During the lunge, the front knee should be flexed to approximately 90 to 100 degrees as the rear knee is lowered toward the ground.

[mistake | re: excessive_front_knee_flexion | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Allowing excessive knee flexion (sinking too deep) during the lunge increases the joint reaction forces and extensor moments on the front knee.

[mistake | re: excessive_front_knee_flexion | source: Biomechanical effects of exercise fatigue on the lower limbs of men during the forward lunge]
Allowing the front knee to translate forward past the toes during the lunge increases stress on the knee joint.

[finding | re: excessive_front_knee_flexion | source: Biomechanical effects of exercise fatigue on the lower limbs of men during the forward lunge]
Keeping the front knee behind the toes reduces stretching force on the patellar tendon during a lunge.

[consequence | re: excessive_front_knee_flexion | source: Zellmer2019_KneePastToes_PatellarTendon_Lunge_JSHS]
Increased knee flexion angle during the lunge increases quadriceps force, which is a main contributing factor to greater patellar tendon stress.

[consequence | re: excessive_front_knee_flexion | source: Patellofemoral Joint Loading in Forward Lunge With Step Length and Height Variations]
Deep knee flexion during a lunge increases compressive force and stress acting on the patellofemoral joint.

[principle | re: excessive_front_knee_flexion | source: Zellmer2019_KneePastToes_PatellarTendon_Lunge_JSHS]
Keeping the front knee behind the toes during a lunge limits knee flexion to a safer range of approximately 110 degrees compared to letting it translate forward.

[finding | re: excessive_front_knee_flexion | source: Biomechanical effects of exercise fatigue on the lower limbs of men during the forward lunge]
Peak knee joint stress, quadriceps force, knee moment, and knee flexion are significantly higher when the knee is brought in front of the toes during the lunge.
```

---

## Exercise: Lunge — forward_trunk_lean

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| forward_trunk_lean | Leaning the upper body forward during the lunge: bending at the hips so the chest drops toward the front thigh instead of the torso staying upright (+why/fix) | 0.052 / 3* | 0.173 / 2* | 0.141 / 2* | 0.138 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: forward_trunk_lean | source: BOXROX_WalkingLungeMistakes]
Tilting the upper body forward at the bottom of the lunge.

[mistake | re: forward_trunk_lean | source: Influence of Different Load Conditions on Lower Extremity Biomechanics during the Lunge Squat in Novice Men]
Leaning the torso forward during the lunge, which commonly occurs in novice lifters due to muscle imbalance and poor body coordination.

[mistake | re: forward_trunk_lean | source: Common Mistakes to Avoid When Performing a Lunge in Ladera Ranch]
Leaning the torso too far forward while lowering into a lunge.

[principle | re: forward_trunk_lean | source: Biomechanical Analysis of the Anterior Lunge During 4 External-Load Conditions]
Maintain an upright, vertical trunk position during the anterior lunge to avoid shifting the total body center of mass forward and altering joint loading.

[consequence | re: forward_trunk_lean | source: Influence of Different Load Conditions on Lower Extremity Biomechanics during the Lunge Squat in Novice Men]
Leaning forward during the lunge increases the shear force at the knee joint, raising the risk of joint injury.

[principle | re: forward_trunk_lean | source: Patellofemoral Joint Loading in Forward Lunge With Step Length and Height Variations]
Maintain between 0° and 20° of forward trunk tilt relative to vertical at the lowest position of the lunge descent.

[consequence | re: forward_trunk_lean | source: Bezerra2021_TrunkPosition_LungeActivation_IJES]
Leaning the trunk forward during a lunge increases lumbar longissimus activation, which can cause unnecessary pain and discomfort for individuals with chronic or acute low back pain.

[finding | re: forward_trunk_lean | source: Biomechanical effects of exercise fatigue on the lower limbs of men during the forward lunge]
An increase in moment at the hip joint during a lunge is directly linked to an increased hip flexion angle brought on by forward body lean.

[finding | re: forward_trunk_lean | source: Patellofemoral Joint Loading in Forward Lunge With Step Length and Height Variations]
Most individuals skilled in lunge exercises achieve between 0° and 20° of forward trunk tilt relative to vertical at the lowest position of the lunge descent.
```

---

## Exercise: Lunge — straight_back_leg

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| straight_back_leg | Keeping the rear leg too straight in the lunge: the back knee failing to bend and drop toward the floor at the bottom, with the body pushed forward onto the front leg (+why/fix) | 0.100 / 1* | strict — | 0.115 / 1* | 0.110 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: straight_back_leg | source: EliteFTS_EasyLungeRegression]
Keeping the back leg straight while attempting to lower the body during a lunge pushes the body forward.

[principle | re: straight_back_leg | source: Bezerra2021_TrunkPosition_LungeActivation_IJES]
Lower the rear knee toward the ground during the descent of the lunge.

[consequence | re: straight_back_leg | source: EliteFTS_EasyLungeRegression]
Projecting the body forward during a lunge due to a straight rear leg increases force on the knee joint and causes knee pain.

[principle | re: straight_back_leg | source: Patellofemoral Joint Loading in Forward Lunge With Step Length and Height Variations]
Allow the trail knee to bend until it lightly makes contact with the ground at the bottom of the lunge.
```

---

## Exercise: Lunge — mixed

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| excessive_front_knee_flexion | Sinking too deep in the lunge: the hips dropping below the level of the front knee, so the front knee folds far past 90 degrees and takes extra load (+why/fix) | 0.088 / 3* | 0.126 / 2* | 0.148 / 2* | 0.125 / 2* |
| forward_trunk_lean | Leaning the upper body forward during the lunge: bending at the hips so the chest drops toward the front thigh instead of the torso staying upright (+why/fix) | 0.052 / 3* | 0.173 / 2* | 0.141 / 2* | 0.138 / 2* |
| shallow_lunge | Lunging too shallow: dipping only slightly, so the front knee stays far from a 90-degree bend and the front thigh stays well above parallel (+why/fix) | 0.135 / 3* | 0.226 / 2* | 0.265 / 2* | 0.157 / 2* |
| straight_back_leg | Keeping the rear leg too straight in the lunge: the back knee failing to bend and drop toward the floor at the bottom, with the body pushed forward onto the front leg (+why/fix) | 0.100 / 1* | strict — | 0.115 / 1* | 0.110 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: forward_trunk_lean | source: BOXROX_WalkingLungeMistakes]
Tilting the upper body forward at the bottom of the lunge.

[mistake | re: excessive_front_knee_flexion | source: Zellmer2019_KneePastToes_PatellarTendon_Lunge_JSHS]
Allowing the front knee to translate forward in front of the toes during the descending phase of a forward step lunge.

[mistake | re: straight_back_leg | source: EliteFTS_EasyLungeRegression]
Keeping the back leg straight while attempting to lower the body during a lunge pushes the body forward.

[mistake | re: forward_trunk_lean | source: Influence of Different Load Conditions on Lower Extremity Biomechanics during the Lunge Squat in Novice Men]
Leaning the torso forward during the lunge, which commonly occurs in novice lifters due to muscle imbalance and poor body coordination.

[principle | re: straight_back_leg | source: Bezerra2021_TrunkPosition_LungeActivation_IJES]
Lower the rear knee toward the ground during the descent of the lunge.

[mistake | re: forward_trunk_lean | source: Common Mistakes to Avoid When Performing a Lunge in Ladera Ranch]
Leaning the torso too far forward while lowering into a lunge.

[consequence | re: straight_back_leg | source: EliteFTS_EasyLungeRegression]
Projecting the body forward during a lunge due to a straight rear leg increases force on the knee joint and causes knee pain.

[principle | re: excessive_front_knee_flexion | source: Bezerra2021_TrunkPosition_LungeActivation_IJES]
During the lunge, the front knee should be flexed to approximately 90 to 100 degrees as the rear knee is lowered toward the ground.

[mistake | re: excessive_front_knee_flexion | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Allowing excessive knee flexion (sinking too deep) during the lunge increases the joint reaction forces and extensor moments on the front knee.

[mistake | re: excessive_front_knee_flexion | source: Biomechanical effects of exercise fatigue on the lower limbs of men during the forward lunge]
Allowing the front knee to translate forward past the toes during the lunge increases stress on the knee joint.

[finding | re: excessive_front_knee_flexion | source: Biomechanical effects of exercise fatigue on the lower limbs of men during the forward lunge]
Keeping the front knee behind the toes reduces stretching force on the patellar tendon during a lunge.

[mistake | re: shallow_lunge | source: basics_of_strength_and_conditioning_manual]
Failing to lower the hips until the front thigh is parallel to the floor.

[principle | re: forward_trunk_lean | source: Biomechanical Analysis of the Anterior Lunge During 4 External-Load Conditions]
Maintain an upright, vertical trunk position during the anterior lunge to avoid shifting the total body center of mass forward and altering joint loading.

[consequence | re: forward_trunk_lean | source: Influence of Different Load Conditions on Lower Extremity Biomechanics during the Lunge Squat in Novice Men]
Leaning forward during the lunge increases the shear force at the knee joint, raising the risk of joint injury.

[principle | re: forward_trunk_lean | source: Patellofemoral Joint Loading in Forward Lunge With Step Length and Height Variations]
Maintain between 0° and 20° of forward trunk tilt relative to vertical at the lowest position of the lunge descent.

[consequence | re: excessive_front_knee_flexion | source: Zellmer2019_KneePastToes_PatellarTendon_Lunge_JSHS]
Increased knee flexion angle during the lunge increases quadriceps force, which is a main contributing factor to greater patellar tendon stress.

[consequence | re: forward_trunk_lean | source: Bezerra2021_TrunkPosition_LungeActivation_IJES]
Leaning the trunk forward during a lunge increases lumbar longissimus activation, which can cause unnecessary pain and discomfort for individuals with chronic or acute low back pain.

[principle | re: shallow_lunge | source: Trunk and Shank Position Influences Patellofemoral Joint Stress in the Lead and Trail Limbs During the Forward Lunge Exercise]
To achieve proper depth during a lunge, descend until the trail knee is just prior to touching the ground.

[mistake | re: shallow_lunge | source: Biomechanical Analysis of the Anterior Lunge During 4 External-Load Conditions]
Lifters tend to cut lunge depth short when handling heavier external loads, failing to lower their center of mass to full depth.

[mistake | re: shallow_lunge | source: Influence of Different Load Conditions on Lower Extremity Biomechanics during the Lunge Squat in Novice Men]
Exhibiting small knee flexion during a lunge indicates underlying issues such as quadriceps weakness or a limited ankle dorsiflexion range.

[consequence | re: excessive_front_knee_flexion | source: Patellofemoral Joint Loading in Forward Lunge With Step Length and Height Variations]
Deep knee flexion during a lunge increases compressive force and stress acting on the patellofemoral joint.

[principle | re: shallow_lunge | source: BOXROX_WalkingLungeMistakes]
Proper lunge depth occurs when the back knee gently touches or comes very close to the ground under control.

[finding | re: forward_trunk_lean | source: Biomechanical effects of exercise fatigue on the lower limbs of men during the forward lunge]
An increase in moment at the hip joint during a lunge is directly linked to an increased hip flexion angle brought on by forward body lean.

[principle | re: excessive_front_knee_flexion | source: Zellmer2019_KneePastToes_PatellarTendon_Lunge_JSHS]
Keeping the front knee behind the toes during a lunge limits knee flexion to a safer range of approximately 110 degrees compared to letting it translate forward.

[finding | re: excessive_front_knee_flexion | source: Biomechanical effects of exercise fatigue on the lower limbs of men during the forward lunge]
Peak knee joint stress, quadriceps force, knee moment, and knee flexion are significantly higher when the knee is brought in front of the toes during the lunge.

[finding | re: forward_trunk_lean | source: Patellofemoral Joint Loading in Forward Lunge With Step Length and Height Variations]
Most individuals skilled in lunge exercises achieve between 0° and 20° of forward trunk tilt relative to vertical at the lowest position of the lunge descent.

[principle | re: straight_back_leg | source: Patellofemoral Joint Loading in Forward Lunge With Step Length and Height Variations]
Allow the trail knee to bend until it lightly makes contact with the ground at the bottom of the lunge.

[finding | re: shallow_lunge | source: Effects of Loading Positions on Lower Limb Biomechanics During Lunge Squat in Men with Different Training Experience]
During backward barbell lunges, novices achieved a shallower peak knee flexion with a minimal sagittal angle of -99.01 ± 10.02 degrees compared to -108.44 ± 8.33 degrees in experienced lifters.

[finding | re: shallow_lunge | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
During a forward lunge, a shallower front knee flexion angle of 80° results in a statistically significantly higher knee extensor moment (0.980 Nm/BW) compared to 90° (0.717 Nm/BW) and 100° (0.362 Nm/BW).

[consequence | re: shallow_lunge | source: BOXROX_WalkingLungeMistakes]
Cutting depth reduces muscle growth and motor unit recruitment because muscles grow more when stretched through a full range of motion.

[consequence | re: shallow_lunge | source: Jaeggi2024_SplitSquat_RearLegMuscleForces_JFMK]
Failing to sufficiently activate the m. gluteus maximus reduces the generation of posterior shear forces at the tibia, which otherwise potentially contribute to a reduced likelihood of knee injuries.
```

---

## Exercise: Lunge — clean

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| general principles | Lunge correct technique and biomechanics | — | — | — | 0.145 / 2 |

### Retrieved KB Context (RAG run)
```text
[principle | re: general principles | source: BOXROX_WalkingLungeMistakes]
Lunge only as far as allows secure footing and balance so force production is not compromised.

[principle | re: general principles | source: Patellofemoral Joint Loading in Forward Lunge With Step Length and Height Variations]
Flex the front knee to approximately 100 degrees during the lunge descent.
```

---


# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions.json` |
| query mode | **raw** — `error_type` embedded verbatim, taxonomy bypassed |
| collection | `kb_local_curated_v4` |
| LLM | `gemini-3.5-flash-lite` @ temperature 0.7 |
| no-RAG side | skipped |
| retrieval gates | CANDIDATE_K=12, MAX_PER_KIND={'mistake': 3, 'finding': 2, 'principle': 3}, ABS_DISTANCE_CAP={'mistake': 0.55, 'finding': 0.4, 'principle': 0.45}, RELATIVE_MARGIN=0.2, NEAR_DUP_JACCARD=0.72 |

Retrieval metrics per exercise: `best` = cosine distance of the closest chunk of that kind in the whole
collection (before any gate), `kept` = chunks that passed the relative/absolute gates and de-duplication
and were actually placed in the context.

---

## System Prompt Used
```text
You are an expert personal trainer, biomechanics specialist, and physical therapy consultant.
Your role is to provide highly detailed, accurate, and constructive feedback based strictly on the provided context and the user's exercise data.

You will receive a JSON structure containing:
1. Current session details (10 reps summary and specific errors).
2. Historical comparison (data from their previous session).

Your tasks:
1. Progress Tracking: Compare their current performance with their previous session. Acknowledge any improvements or regressions in their correct rep count and overall score.
2. Biomechanical Analysis: Analyze the specific errors made in the current session. Use the provided Knowledge Base context to explain the biomechanical reasons why these errors are problematic, what muscle groups or joints are at risk, and how exactly to correct the form step-by-step.
3. Tone: Be deeply informative, professional, yet encouraging. Motivate the user to achieve perfect form.

How to read the Context: every entry starts with a header line of the form
[<kind> | re: <which error it was retrieved for> | source: <source name>], followed by the
entry text. `kind` is one of: mistake (a known incorrect form), finding (a concrete result
from that source), principle (general correct-form guidance). When you cite an entry, name
its source exactly as written in that header - do not name any other study, author, or
organisation. Never quote the header line itself back to the user.

Grounding rule: If the Context below contains a specific number, percentage, joint angle, study finding, or named source,
you MUST cite that specific detail (and name the source from its header) rather than a generic restatement.
Do NOT cite any specific number, percentage, study name, sample size, date range, or named finding that does not
appear verbatim in the Context below - even if you recognize the study or believe the fact to be true from your
own general knowledge. Your own training knowledge must never substitute for the Context; if a fact is not in
the Context, treat it as unavailable to you for citation purposes. If the Context has no specifics for a given
error, say so briefly and fall back to general accepted biomechanical principles, described in general terms
only with no invented numbers or named sources.

Context from Knowledge Base:
{context}
```

---

## Exercise: Squat

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | principle best / kept |
|---|---|---|---|---|
| Butt wink | Butt wink | 0.601 / 0 | 0.779 / 0 | — |
| Partial squat | Partial squat | 0.329 / 3 | 0.318 / 2 | — |

### Retrieved KB Context (RAG run)
```text
[finding | re: Partial squat | source: www.healthline.com/health/fitness/deep-squat]
Compressive forces in the knee may be higher in a partial squat than in a deep squat.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Lifting heels or toes off the ground during the squat.

[mistake | re: Partial squat | source: ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN]
Forcing a generic squat stance without considering the individual's bony anthropometrical capacity.

[finding | re: Partial squat | source: Muscle Activation Patterns During Different Squat Techniques]
Control squats were performed to 90 degrees of flexion.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Progressing to loaded squats or plyometrics before mastering the bodyweight squat technique.
```

### WITH RAG
### 1. Progress Tracking
Great effort on your session today! Comparing your performance to your previous session on August 30, 2026, you have made clear improvements. Your overall score increased from 73 to 79, and your correct rep count improved from 4 to 6 (out of 10 total reps), reducing your incorrect reps down from 6 to 4. While previous errors included "Butt wink" and "Knee valgus," today's session primarily highlighted "Butt wink" and a new tracking error of a "Partial squat." You are heading in the right direction—keep building on this momentum!

### 2. Biomechanical Analysis
During your session, rep 6 was flagged for a **Partial squat**. 

* **Biomechanical Risk:** According to www.healthline.com/health/fitness/deep-squat, compressive forces in the knee may be higher in a partial squat than in a deep squat. Furthermore, control squats are traditionally performed to 90 degrees of flexion, as noted in *Muscle Activation Patterns During Different Squat Techniques*. 
* **Additional Errors to Watch:** As noted in *TheBackSquatAProposedAssessment*, be careful not to lift your heels or toes off the ground during the squat, and ensure you fully master the bodyweight squat technique before progressing to loaded squats or plyometrics. Additionally, *ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN* points out the mistake of forcing a generic squat stance without considering your individual bony anthropometrical capacity.
* **Step-by-Step Correction:** 
  1. Find a stance width and toe angle that naturally accommodates your unique skeletal structure rather than forcing a standard template.
  2. Keep your entire foot—both heels and toes—flat and firmly planted on the ground throughout the movement.
  3. Control your descent until your thighs reach at least 90 degrees of flexion (or your optimal depth) to distribute joint forces evenly and avoid the higher knee compression associated with halting the movement prematurely.

---

## Exercise: Lunge

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | principle best / kept |
|---|---|---|---|---|
| Excessive forward trunk lean | Excessive forward trunk lean | 0.143 / 1 | 0.525 / 0 | — |
| Insufficient back knee flexion | Insufficient back knee flexion | 0.347 / 3 | 0.402 / 0 | — |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Excessive forward trunk lean | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
Excessive trunk movement or marked trunk lean.

[mistake | re: Insufficient back knee flexion | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
Knee collapsing inward (excessive medial knee displacement).

[mistake | re: Insufficient back knee flexion | source: themerisoiutechnique.com/2015/12/25/lunges-common-mistakes-and-correct-technique]
Front knee collapsing inward or shaking.

[mistake | re: Insufficient back knee flexion | source: ptq-4.4.9-the-undervalued-lunge]
Feet too close together (stride length too short), increasing stress on the patellar tendon.
```

### WITH RAG
### Progress Tracking

Great work on your progression! Comparing your session from August 31, 2026, to your previous session on August 30, 2026, you have shown clear improvement:

* **Overall Score:** Increased from 70 to 79.
* **Correct Reps:** Improved from 4 correct reps up to 7 correct reps.
* **Incorrect Reps:** Decreased from 6 incorrect reps down to just 3.

You are moving in the right direction and building strong consistency across the majority of your set.

---

### Biomechanical Analysis & Form Correction

During this session, your performance was hindered by two specific errors. Here is a breakdown of why these happen and how to correct them:

#### 1. Excessive Forward Trunk Lean (Occurred on Reps 1 and 3)
* **Biomechanical Risk:** According to *Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study*, excessive trunk movement or marked trunk lean places undue stress on the spine and alters the targeted lower-limb muscle activation. 
* **Correction:** Engage your core strongly before initiating the descent. Keep your chest proud, shoulders back, and eyes focused straight ahead as you lower your body to prevent your torso from collapsing forward.

#### 2. Insufficient Back Knee Flexion (Occurred on Rep 9)
* **Biomechanical Risk:** This can be tied to having feet too close together or having a stride length that is too short, which increases stress on the patellar tendon according to *ptq-4.4.9-the-undervalued-lunge*. Additionally, notes from *themerisoiutechnique.com/2015/12/25/lunges-common-mistakes-and-correct-technique* and *Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study* highlight that poor back leg positioning can lead to the front knee collapsing inward (excessive medial knee displacement) or shaking.
* **Correction:** Take a deliberate, elongated step forward to ensure your stance isn't too narrow. As you drop into the lunge, focus on actively bending your back knee straight down toward the floor while tracking your front knee directly in line with your toes.

Keep up the fantastic momentum, stay mindful of your posture and stride length, and let's aim for a completely clean set next time!

---

## Exercise: Push-up

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | principle best / kept |
|---|---|---|---|---|
| general principles | Push-up correct technique and biomechanics | — | — | 0.250 / 3 |

### Retrieved KB Context (RAG run)
```text
[principle | re: general principles | source: blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement]
Regress the push-up by placing hands on a bench or knees on the floor to maintain movement integrity and posture.

[principle | re: general principles | source: www.nasm.org/resource-center/blog/training/proper-push-up-form-and-technique-a-complete-guide]
Utilize the push-up as a movement assessment to evaluate upper-body strength, core stability, and the ability to maintain alignment under load.

[principle | re: general principles | source: The_Effect_of_Position_on_the_Percentage_of_Body.992962]
The push-up is an upper-extremity weight-bearing exercise that can improve joint stability and proprioception through joint compression forces.
```

### WITH RAG
### Progress Tracking
Great job on your latest push-up session! Comparing your performance to your previous session on August 30, 2026, you have made fantastic progress. Your overall score increased from 72 to 87, and you successfully improved your correct rep count from 9 out of 10 up to a stellar 10 out of 10 correct reps, completely eliminating the hip sag and partial range of motion errors you experienced previously. 

### Biomechanical Analysis
You had zero recorded errors in this session, which is a major win for your movement quality. 

Maintaining this level of performance allows you to properly utilize the push-up as a movement assessment to evaluate upper-body strength, core stability, and the ability to maintain alignment under load, as outlined in *www.nasm.org/resource-center/blog/training/proper-push-up-form-and-technique-a-complete-guide*. Furthermore, performing clean, full-range push-ups acts as an upper-extremity weight-bearing exercise that improves joint stability and proprioception through joint compression forces (*The_Effect_of_Position_on_the_Percentage_of_Body.992962*). 

If you ever find fatigue creeping in and feel your posture starting to slip, remember that you can regress the push-up by placing your hands on a bench or your knees on the floor to maintain movement integrity and posture (*blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement*). 

Keep up the outstanding work!

---

## Exercise: Bicep Curl

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | principle best / kept |
|---|---|---|---|---|
| Elbow flare | Elbow flare | 0.438 / 3 | 0.499 / 0 | — |
| Partial range of motion | Partial range of motion | 0.303 / 1 | 0.661 / 0 | — |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Partial range of motion | source: www.nasm.org/resource-center/blog/training/9-of-the-best-arm-sculpting-exercises-to-tone-and-strengthen]
Failing to use a full range of motion

[mistake | re: Elbow flare | source: grokipedia.com/page/Bicep_curl]
Allowing the elbows to flare outward during the curl.

[mistake | re: Elbow flare | source: A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve]
Failing to start the movement from full elbow extension.

[mistake | re: Elbow flare | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
Swinging the elbows during the lift.
```

### WITH RAG
### Progress Tracking
Great work on your session today! Comparing your performance to your previous session on August 30, 2026, you have made notable improvements. Your overall score increased from 75 to 81, and you successfully doubled your correct repetitions, moving from 3 correct reps up to 6. While you still experienced some recurring issues with "Partial range of motion" and "Elbow flare," reducing your incorrect reps down from 7 to 4 shows that your body awareness and movement control are heading in the right direction. Keep building on this positive momentum!

---

### Biomechanical Analysis & Form Correction

Based on your session data, the errors logged during your lifts require specific attention to protect your joints and maximize muscle activation:

*   **Partial Range of Motion:** As noted by `www.nasm.org/resource-center/blog/training/9-of-the-best-arm-sculpting-exercises-to-tone-and-strengthen`, failing to use a full range of motion limits the overall effectiveness of the exercise. Furthermore, data from `A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve` points out that you must start the movement from full elbow extension. Short-changing your reps deprives the target muscles of full length-tension loading. 
    *   *Correction:* Ensure your arms are completely straight at the bottom of every rep before initiating the curl, and lift all the way to the top contraction.
*   **Elbow Flare:** According to `grokipedia.com/page/Bicep_curl`, allowing the elbows to flare outward during the curl compromises form. Additionally, `Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report` highlights that swinging the elbows during the lift introduces unwanted momentum, placing excess strain on the shoulders and anterior chain rather than isolating the biceps.
    *   *Correction:* Keep your upper arms pinned tightly and stable against your sides throughout the entire ascending phase. Do not allow your elbows to drift backward or flare outward. 

Focus tightly on stability and full extension on your next session, and you will see your correct rep count climb even higher!

---


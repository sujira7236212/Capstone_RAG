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

Relevance rule: the `re:` label says which error an entry was RETRIEVED for, not that it
describes that error - retrieval is approximate and some entries are near misses. Before
using an entry for an error, check that its text plainly describes that error (or, for a
principle, the correct form that fixes it). Ignore an entry entirely - do not cite it,
mention it, or reframe it as related - if it describes a different fault or a different
exercise variant, if it is a study protocol or setup detail with no consequence attached,
or if following it would push the user further into the error being discussed. Fewer,
accurate citations are better than using every entry.

Grounding rule: When an entry that passes the relevance rule contains a specific number, percentage, joint angle,
study finding, or named source, cite that specific detail (naming the source from its header) rather than a generic
restatement. Use `principle` entries for the step-by-step correction; if no relevant principle exists for an error,
describe the correction in general terms without naming a source.
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
| Butt wink | Lumbar flexion (butt wink): posterior pelvic tilt and rounding of the lower back at the bottom of the squat | 0.120 / 2 | 0.329 / 2 | 0.296 / 2 |
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
Flexing at the spine before 1208 (120 degrees) of hip flexion when squatting may indicate restriction in the posterior fibers of the iliotibial band or lack of lumbar control.

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
### Progress Tracking
Great job on your progress! Compared to your previous session on 2026-08-30, your overall score improved from 73 to 79. You also increased your correct reps from 4 up to 6, while reducing your incorrect reps down from 6 to 4. Notably, you completely eliminated knee valgus from your common errors list. Let's look at the remaining faults to help you achieve a spotless session next time.

---

### Biomechanical Analysis & Corrections

#### 1. Butt Wink (Posterior Pelvic Tilt)
* **Biomechanical Risk:** This error involves a posterior pelvic tilt where the pelvis tucks under and the low back rounds at the bottom of the squat (www.nasm.org/resource-center/blog/training/biomechanics-of-the-squat, ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN). Flexing at the spine before 1208 of hip flexion when squatting may indicate a restriction in the posterior fibers of the iliotibial band or a lack of lumbar control (TheBackSquatAProposedAssessment). Rounding places excessive, unwanted pressure on your lower back and reduces optimal spinal support.
* **Step-by-Step Correction:** 
  * Maintain a neutral, slightly lordotic spine posture throughout the squat to avoid excessive pressure on the lower back (TheBackSquatAProposedAssessment).
  * Keep a neutral pelvic tilt during the movement to increase erector spinae and oblique muscle activity, which provides optimal spinal support (TheBackSquatAProposedAssessment). 

#### 2. Partial Squat
* **Biomechanical Risk:** Squatting too shallow and failing to bring the thighs at least parallel to the ground (TheBackSquatAProposedAssessment). Interestingly, compressive forces in the knee may actually be higher in a partial squat than in a deep squat (www.healthline.com/health/fitness/deep-squat), denying your lower body the full functional benefits of the movement.
* **Step-by-Step Correction:**
  * Perform your repetitions to the standard depth of 90 degrees of flexion (Muscle Activation Patterns During Different Squat Techniques).
  * Ensure you achieve full depth with the tops of your thighs at least parallel to the ground (TheBackSquatAProposedAssessment).

Keep up the dedicated work—your form is trending in the right direction! Focus on maintaining spinal integrity and hitting your depth consistently on every single rep.

### WITHOUT RAG
### Progress Tracking
Great job on your progress! Compared to your previous session on August 30, your overall score improved from **73** to **79**, and your correct repetitions increased from **4** to **6** (with incorrect reps dropping from 6 down to 4). Notably, you have completely eliminated knee valgus from your movement pattern. With continued focus, you can bridge the gap to a completely flawless set.

---

### Biomechanical Analysis & Form Correction

During this session, two primary errors were detected: **Butt wink** and **Partial squat**. 

#### 1. Butt Wink (Posterior Pelvic Tilt at the Bottom)
* **Biomechanical Risk:** A "butt wink" occurs when the pelvis tucks under and the lower spine rounds at the bottom of the squat. This places undue stress on the lumbar spine and intervertebral discs by shifting the load away from the musculature and onto passive spinal structures, increasing injury risk under heavy loads.
* **Correction:** 
  * Brace your core tightly before initiating the descent to establish a solid cylinder of support for your spine.
  * Control your descent depth and avoid forcing yourself lower than your current hip mobility and hamstring flexibility allow. Keep your chest proud and maintain a neutral spine throughout the entire range of motion.

#### 2. Partial Squat
* **Biomechanical Risk:** Cutting a squat short prevents full recruitment of the targeted lower body musculature—particularly the glutes and quadriceps—reducing the overall effectiveness of the exercise and leading to muscle strength imbalances.
* **Correction:** 
  * Focus on a full, controlled descent where your hip crease drops below the top of your knees (or to your comfortable, safe end-range of motion). 
  * Drive evenly through your whole foot to power your ascent back to a fully upright standing position.

Keep up the strong effort—you are moving in the right direction! Focus on maintaining spinal integrity and full depth on your next session.

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
Great job on your progress! Compared to your previous session on August 30, where you achieved 4 correct reps and an overall score of 70, you improved your performance to 7 correct reps and an overall score of 79 today. You also successfully eliminated "Shallow lunge" from your errors. Keep up the momentum to clean up the remaining faults.

---

### Biomechanical Analysis & Form Correction

During your current session, the primary error flagged was **Excessive forward trunk lean** (occurring during reps 1 and 3). 

* **Biomechanical Risk:** According to `mxn167Sp24`, performing a forward lunge with a forward trunk lean increases biceps femoris activity compared to an upright trunk, altering the targeted muscle recruitment and placing undue stress on your lower back and posterior chain.
* **Step-by-Step Correction:** 
  1. Maintain an upright trunk throughout the movement as noted in *Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study*.
  2. Keep your chest proud and core braced to naturally avoid collapsing forward. An upright trunk helps create a proper 90/90 lunge where both knees at the bottom of the move form 90-degree angles (`blog.nasm.org/training-benefits/lunge-effective-lower-body-training-exercise`).

You also experienced **Insufficient back knee flexion** on rep 9. 

* **Biomechanical Risk:** Allowing the rear knee to flex improperly or failing to control its descent reduces the effectiveness of the lower-body loading. Note from `Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study`: do not allow the rear knee to contact the floor during the lunge.
* **Step-by-Step Correction:** 
  1. Lower your back knee straight down toward the ground under control, stopping just short of floor contact. 
  2. Ensure your alignment remains stable to avoid unwanted joint torque.

You are moving in the right direction—focus on torso stability and controlled depth, and you will hit a completely clean set next time!

### WITHOUT RAG
### Progress Tracking
Great work on your lunge session today! You have shown clear, positive progress compared to your session on August 30, 2026. 
* **Overall Score:** Increased from 70 to 79.
* **Correct Reps:** Improved from 4 correct reps up to 7 correct reps.
* **Incorrect Reps:** Decreased from 6 down to just 3. 
* **Error Trends:** You successfully eliminated the "Shallow lunge" issue as a major recurring trend from your previous workout. Keep up this momentum!

---

### Biomechanical Analysis & Correction

In this session, the remaining errors were **Excessive forward trunk lean** (seen on reps 1 and 3) and **Insufficient back knee flexion** (seen on rep 9). 

#### 1. Excessive Forward Trunk Lean
* **Biomechanical Risk:** Leaning your torso too far forward shifts the center of mass away from your base of support. This places undue stress on the lower back (lumbar spine) and shifts excessive load onto the quadriceps while underutilizing your glutes and hamstrings, increasing the risk of lower back strain.
* **Step-by-Step Correction:** 
  1. Engage your core tightly before initiating the step.
  2. Keep your chest proud and your shoulders stacked directly over your hips throughout the descent and ascent.
  3. Visualize moving straight down toward the floor rather than driving your upper body forward over your front thigh.

#### 2. Insufficient Back Knee Flexion
* **Biomechanical Risk:** Failing to bend your back knee adequately usually means you are cutting the range of motion short or relying too heavily on your front leg. This reduces overall lower body muscle activation and compromises the stability of the movement.
* **Step-by-Step Correction:**
  1. As you step out, consciously allow your trailing knee to drop straight down toward the floor.
  2. Ensure your back heel stays elevated off the ground, allowing your ankle, knee, and hip joints to flex harmoniously. 
  3. Aim to create roughly 90-degree angles in both knees at the bottom of the lunge.

You are moving in the right direction—focus on maintaining an upright posture and a full, controlled range of motion for your next session to aim for a flawless set!

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
Fantastic work on your push-up session today! Compared to your previous session on August 30, 2026—where you scored 72 with 9 correct reps and 1 incorrect rep (noting issues with hip sag and partial range of motion)—you have made incredible progress. In this session, you achieved **10 out of 10 correct reps**, recorded **0 incorrect reps**, and boosted your overall score to **87**. Eliminating your previous errors completely shows a remarkable improvement in your stability and control.

### Biomechanical Analysis
You successfully completed all reps without flagging any specific errors this time around. As noted in guidance from *www.nasm.org/resource-center/blog/training/proper-push-up-form-and-technique-a-complete-guide*, the push-up serves as an exceptional movement assessment to evaluate upper-body strength, core stability, and your ability to maintain proper body alignment under load. 

By keeping your core engaged and avoiding the hip sag that troubled your previous session, you protected your lower back and ensured optimal force transfer through your upper body. If fatigue ever begins to creep in during future sets and alignment starts to slip, you can successfully regress the push-up by placing your hands on a bench or your knees on the floor to maintain movement integrity and posture, as recommended by *blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement*. 

Keep up the outstanding effort and consistency!

### WITHOUT RAG
### Progress Tracking
Fantastic work on your push-up session today! Compared to your previous session on August 30th—where you scored a 72 with 9 correct reps and faced issues like hip sag and a partial range of motion—you have shown incredible progress. You successfully completed **10 out of 10 correct reps** with zero recorded errors, bringing your overall session score up to an 87. 

### Biomechanical Analysis & Form Evaluation
Because you executed a flawless set with zero errors today, you avoided the structural compensations that plagued your previous session (such as lumbar hyperextension from hip sag and reduced muscular activation from a partial range of motion). 

* **Why avoiding hip sag matters:** Maintaining a rigid, plank-like torso protects your lumbar spine from excessive shear stress and engages your core musculature (transversus abdominis and rectus abdominis) alongside your chest, shoulders, and triceps.
* **Why full range of motion matters:** Lowering your chest fully ensures optimal joint mechanics at the shoulder and elbow, maximizing muscle fiber recruitment across the pectoralis major and anterior deltoids.

### Step-by-Step Correction for Sustaining Perfect Form
To keep up this stellar momentum in your next workouts, focus on these fundamental principles:
1. **Establish a Solid Plank:** Squeeze your glutes, brace your core as if anticipating a light punch to the stomach, and keep your body in a straight line from your head to your heels.
2. **Control the Descent:** Lower your body under control until your elbows achieve optimal depth, ensuring a full range of motion without letting your hips drop toward the floor.
3. **Powerful Push:** Drive the floor away evenly through your palms while maintaining full-body tension until your arms are fully extended at the top.

Keep up the extraordinary dedication—your consistency and attention to form are paying off brilliantly!

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
Great job on your progress! Compared to your previous session on 2026-08-30 (where you scored 75 with 3 correct reps and 7 incorrect reps), you have improved your overall score to 81 and increased your correct repetitions to 6. While you still encountered some familiar technique breakdowns, cutting your errors down and increasing clean repetitions shows positive momentum.

---

### Biomechanical Analysis & Corrections

During this session, two primary errors were logged: **Partial range of motion** and **Elbow flare**. 

#### 1. Partial Range of Motion
* **The Error:** You failed to start the repetition with the elbow in full extension, and failed to achieve complete arm extension at the bottom of the movement (as noted in *Scandinavian Med Sci Sports - 2014 - Brandner - Unilateral bicep curl hemodynamics Low‐pressure continuous vs* and *grokipedia.com/page/Bicep_curl*). 
* **Biomechanical Impact:** Shortchanging the bottom of the movement reduces the total mechanical work and tension placed across the elbow flexors throughout the entire profile of the exercise.
* **Correction:** According to *grokipedia.com/page/Bicep_curl*, you must perform a full range of motion from complete arm extension at the bottom to near-maximal elbow flexion at the top, or utilize a full range of motion from full elbow extension to complete flexion. Ensure your arms are completely straight at the start and bottom of every single rep.

#### 2. Elbow Flare
* **The Error:** Your elbows drifted or flared outward away from your body during the ascending phase of the curl (*grokipedia.com/page/Bicep_curl* and *A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve*).
* **Biomechanical Impact:** Allowing the elbows to move away from the torso compromises strict isolation of the target muscles by introducing anterior shoulder movement and momentum into the lift.
* **Correction:** Per *grokipedia.com/page/Bicep_curl*, consciously keep your elbows tucked tightly at your sides throughout the entire duration of the curl. Pin your upper arms to your ribcage and use them as a stable pivot point.

Keep up the strong effort—focus on locking out your arms at the bottom and keeping those elbows pinned to your sides to secure a fully pristine set next time!

### WITHOUT RAG
### Progress Tracking
Great job on your progress! Comparing your session from August 31, 2026, to your previous session on August 30, 2026, you have shown notable improvement. Your overall score increased from 75 to 81, and your correct repetitions doubled from 3 to 6 out of 10. While you still encountered "Partial range of motion" and "Elbow flare," you reduced the total number of incorrect reps from 7 down to 4. Keep up the momentum!

---

### Biomechanical Analysis & Form Correction

*(Note: No external knowledge base context was provided for this session, so the following feedback is based on standard clinical biomechanics principles.)*

#### 1. Partial Range of Motion (Observed on Rep 3)
* **Biomechanical Impact:** Failing to complete the full range of motion reduces the mechanical tension and activation placed on the biceps brachii, limiting optimal muscle fiber recruitment and strength gains. 
* **Correction:** Ensure that your arms fully extend at the bottom of the movement (the starting position) and that you curl the weight all the way up until your forearms fully contract against your biceps at the top. 

#### 2. Elbow Flare (Observed on Reps 8, 9, and 10)
* **Biomechanical Impact:** Allowing your elbows to drift forward or flare outward during the ascending phase shifts the workload away from the target musculature (the biceps) and places unnecessary stress onto the shoulder joint and anterior deltoids, compromising stability.
* **Correction:** Keep your upper arms pinned strictly to the sides of your torso throughout the entire lift. Imagine your elbows acting as hinges fixed in one spot, ensuring that only your forearms move during the curl. 

Stay focused, maintain your discipline as fatigue sets in near the end of your sets, and you will be hitting a clean 10 out of 10 in no time!

---


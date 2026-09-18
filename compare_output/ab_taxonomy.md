# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions.json` |
| query mode | **taxonomy** — `error_type` resolved through `error_taxonomy.py` |
| collection | `kb_local_curated_v4` |
| LLM | `gemini-3.5-flash-lite` @ temperature 0.7 |
| no-RAG side | run |
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
| Butt wink | Lumbar flexion (butt wink): posterior pelvic tilt and rounding of the lower back at the bottom of the squat | 0.120 / 3 | 0.329 / 2 | — |
| Partial squat | Squatting too shallow, thighs not reaching parallel: partial or quarter squat depth | 0.258 / 3 | 0.370 / 1 | — |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Butt wink | source: ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN]
Lumbar flexion (butt wink) at the bottom of the squat.

[mistake | re: Butt wink | source: www.nasm.org/resource-center/blog/training/biomechanics-of-the-squat]
Posterior pelvic tilt ('Butt Wink') where the pelvis tucks under and the low back rounds at the bottom of the squat.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting too shallow, failing to bring the thighs at least parallel to the ground.

[mistake | re: Butt wink | source: www.healthline.com/health/fitness/deep-squat]
Tailbone tucking or tilting backward (butt wink) at the bottom of the squat.

[finding | re: Butt wink | source: TheBackSquatAProposedAssessment]
Flexing at the spine before 1208 (120 degrees) of hip flexion when squatting may indicate restriction in the posterior fibers of the iliotibial band or lack of lumbar control.

[finding | re: Butt wink | source: Muscle Activation Patterns During Different Squat Techniques]
Control squats were performed to 90 degrees of flexion.

[finding | re: Partial squat | source: www.healthline.com/health/fitness/deep-squat]
Compressive forces in the knee may be higher in a partial squat than in a deep squat.

[mistake | re: Partial squat | source: Altered_Knee_and_Ankle_Kinemat]
Medial knee displacement (knee-valgus collapse) during double-legged squats and single-leg squats.

[mistake | re: Partial squat | source: Physiotherapy Res Intl - 2015 - Jaberzadeh - The Effect of Altering Knee Position and Squat Depth on VMO   VL EMG Ratio]
Utilizing shallow squat depths (0-30 degrees) when trying to target mid-range quadriceps activation.
```

### WITH RAG
### Progress Tracking

Great job stepping back into your training! Comparing your session on 2026-08-31 to your previous workout on 2026-08-30, you have shown positive progress. Your overall score improved from 73 to 79, and your correct rep count increased from 4 out of 10 up to 6 out of 10. Furthermore, you successfully eliminated knee valgus from your common errors this session. Keep building on this momentum to secure even more clean repetitions next time.

---

### Biomechanical Analysis & Form Correction

Despite your overall improvement, your data shows that you still encountered issues with **Butt wink** and **Partial squat**. Here is a detailed breakdown of why these errors happen, the risks they pose, and how to fix them:

#### 1. Butt Wink (Posterior Pelvic Tilt)
* **What happens:** As noted in *www.nasm.org/resource-center/blog/training/biomechanics-of-the-squat*, a "butt wink" occurs when the pelvis tucks under and the lower back rounds at the bottom of the squat. According to *ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE CUSTOMIZING THE SQUAT PATTERN*, this involves lumbar flexion at the bottom of the movement, while *www.healthline.com/health/fitness/deep-squat* describes it as the tailbone tucking or tilting backward. 
* **Risks & Biomechanics:** Flexing at the spine before reaching 1208 (120 degrees) of hip flexion may indicate a restriction in the posterior fibers of the iliotibial band or a lack of lumbar control (*TheBackSquatAProposedAssessment*). Rounding the lumbar spine under load places excessive, unwanted shear stress on the intervertebral discs and lower back structures.
* **Correction:** Focus on maintaining core bracing and neutral lumbar extension throughout your descent. Do not force your depth past the point where your pelvis begins to posteriorly tilt. Improving hip mobility and posterior chain flexibility can also help you maintain a neutral spine deeper into the squat.

#### 2. Partial Squat
* **What happens:** A partial squat happens when you squat too shallow, failing to bring your thighs at least parallel to the ground (*TheBackSquatAProposedAssessment*). 
* **Risks & Biomechanics:** Utilizing shallow squat depths (0-30 degrees) when trying to target mid-range quadriceps activation is counterproductive (*Physiotherapy Res Intl - 2015 - Jaberzadeh - The Effect of Altering Knee Position and Squat Depth on VMO VL EMG Ratio*). Additionally, compressive forces in the knee may actually be higher in a partial squat than in a deep squat (*www.healthline.com/health/fitness/deep-squat*), placing unneeded joint stress without achieving full muscular benefits.
* **Correction:** Control your descent until your thighs reach at least parallel to the floor, ensuring a full, functional range of motion while keeping your chest up and core engaged.

### WITHOUT RAG
### Progress Tracking
Great job on your progress! Compared to your previous session on 2026-08-30 (where you had 4 correct reps and an overall score of 73), you improved your performance today. In this session, you increased your correct reps to 6 and brought your overall score up to 79. Additionally, you completely eliminated "Knee valgus" from your previous common errors, which is a fantastic achievement.

---

### Biomechanical Analysis & Form Correction
In this session, you encountered two primary errors: **Butt wink** and **Partial squat**. 

Since no external knowledge base context was provided for these specific errors, we will look at them through general biomechanical principles:

1. **Butt Wink (Posterior Pelvic Tilt at the Bottom)**
   * **The Risk:** This occurs when your pelvis tucks under at the bottom of the squat, causing your lumbar spine to flex. Under heavy loads, this places excessive shear stress on the lumbar vertebrae and intervertebral discs, increasing the risk of lower back strain.
   * **Correction:** Work on improving your ankle and hip mobility so you can reach depth without losing neutral spine alignment. Avoid forcing your descent past the point where your pelvis begins to tuck (reduce your depth slightly if necessary) and focus on bracing your core tightly throughout the movement.

2. **Partial Squat (Insufficient Depth)**
   * **The Risk:** Stopping short of adequate depth reduces full recruitment of the quadriceps, glutes, and hamstrings, limiting your functional strength gains.
   * **Correction:** Focus on consciously controlling your descent until your thighs break parallel (or your target depth is safely reached), keeping your weight evenly distributed across your mid-foot before driving back up.

Keep up the momentum—fix these minor depth and pelvic stability issues, and you'll be well on your way to achieving a flawless session!

---

## Exercise: Lunge

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | principle best / kept |
|---|---|---|---|---|
| Excessive forward trunk lean | Leaning the torso forward, excessive trunk lean during the lunge | 0.256 / 3 | 0.338 / 1 | — |
| Insufficient back knee flexion | Insufficient back knee flexion: rear knee not lowering toward the floor during the lunge | 0.256 / 3 | 0.305 / 2 | — |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Excessive forward trunk lean | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
Excessive trunk movement or marked trunk lean.

[mistake | re: Insufficient back knee flexion | source: lunge_knowledge]
Allowing the rear knee to flex during the stride-stance lunge.

[finding | re: Insufficient back knee flexion | source: ptq-4.4.9-the-undervalued-lunge]
Rotating the back knee or foot outward during a forward lunge increases torque stress in the knee joint.

[finding | re: Insufficient back knee flexion | source: mxn167Sp24]
Kinematic data showed a significantly greater knee angle in the forward lunge compared to the backward lunge.

[mistake | re: Insufficient back knee flexion | source: KritzCroninHume2009BodyweightlungeSCJ]
Medial or lateral movement of the knees during the lunge.

[finding | re: Excessive forward trunk lean | source: blog.nasm.org/training-benefits/lunge-effective-lower-body-training-exercise]
An upright trunk tends to create what is often called a 90/90 lunge where both knees at the bottom of the move are 90° angles.

[mistake | re: Insufficient back knee flexion | source: mxn167Sp24]
Allowing the trailing knee to impact the ground during a lunge.

[mistake | re: Excessive forward trunk lean | source: KritzCroninHume2009BodyweightlungeSCJ]
Spinal flexion (rounding the back) during the lunge.

[mistake | re: Excessive forward trunk lean | source: themerisoiutechnique.com/2015/12/25/lunges-common-mistakes-and-correct-technique]
Leaning the torso forward or backward.
```

### WITH RAG
### Progress Tracking
Great job on your progress! Comparing your session from August 31, 2026, to your previous session on August 30, 2026, your overall score improved from 70 to 79. You also increased your correct repetitions from 4 up to 7, reducing your incorrect reps from 6 down to 3. While "Excessive forward trunk lean" remains a recurring challenge, you have eliminated "Shallow lunge" from your previous errors and are moving in the right direction. 

---

### Biomechanical Analysis & Form Correction

During this session, you encountered two specific errors: **Excessive forward trunk lean** and **Insufficient back knee flexion**. Here is how to address them:

#### 1. Excessive Forward Trunk Lean
* **Biomechanical Risk:** Leaning your torso forward or backward places undue stress on the spine and alters load distribution across your hips and knees. According to *KritzCroninHume2009BodyweightlungeSCJ*, this error often involves spinal flexion (rounding the back) and marked trunk lean (*Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study*), which compromises core stability and increases injury risk to the lower back. Leaning your torso forward or backward also deviates from optimal alignment (*themerisoiutechnique.com/2015/12/25/lunges-common-mistakes-and-correct-technique*).
* **Step-by-Step Correction:** 
  1. Keep your chest proud and your spine neutral throughout both the descending and ascending phases.
  2. Maintain an upright torso to achieve a proper 90/90 lunge position, where both knees form 90-degree angles at the bottom of the movement, as noted in *blog.nasm.org/training-benefits/lunge-effective-lower-body-training-exercise*.
  3. Engage your core tightly before initiating the step to prevent your upper body from collapsing forward.

#### 2. Insufficient Back Knee Flexion
* **Biomechanical Risk:** Failing to properly bend or control the trailing leg can lead to compensatory movements, such as medial or lateral knee deviations (*KritzCroninHume2009BodyweightlungeSCJ*). Furthermore, allowing the trailing knee to impact the ground (*mxn167Sp24*) or rotating the back knee or foot outward can increase torque stress in the knee joint (*ptq-4.4.9-the-undervalued-lunge*). 
* **Step-by-Step Correction:**
  1. As you step forward, actively drop your back knee straight down toward the floor rather than just driving your front knee forward.
  2. Control the descent so your back knee hovers just above the floor without forcefully impacting it (*mxn167Sp24*).
  3. Keep your back foot and knee tracking straight ahead to eliminate outward rotation and protect the joint from excessive torque stress (*ptq-4.4.9-the-undervalued-lunge*).

Keep up the consistent work, focus on keeping your chest up, and aim for clean 90/90 angles on your next session!

### WITHOUT RAG
### Progress Tracking
Great job on your Lunge session today! You have made clear, measurable progress compared to your previous session on August 30, 2026. 
* **Overall Score:** Increased from 70 to 79.
* **Correct Reps:** Improved from 4 correct reps up to 7 correct reps.
* **Incorrect Reps:** Decreased from 6 incorrect reps down to just 3.
* **Error Trends:** You successfully eliminated the "Shallow lunge" issue entirely from your previous session, and cut down your occurrences of "Excessive forward trunk lean."

---

### Biomechanical Analysis & Correction

Since the knowledge base did not provide specific external study metrics for this session, we will look at your remaining errors through standard biomechanical principles to help you dial in a flawless set next time:

1. **Excessive Forward Trunk Lean (Reps 1 & 3):**
   * *The Problem:* Leaning too far forward shifts the center of mass away from your base of support, placing unnecessary shear stress on the lumbar spine and shifting excessive load onto the quadriceps while underutilizing the glutes.
   * *How to Correct:* Engage your core tightly before initiating the descent, keep your chest proud and upright, and imagine sliding your back down an imaginary vertical wall. 

2. **Insufficient Back Knee Flexion (Rep 9):**
   * *The Problem:* Not dropping your back knee down adequately reduces the range of motion for the lower body, lowering overall muscular recruitment in both the trailing leg's hip flexors/quads and the leading leg's glute complex.
   * *How to Correct:* Focus on dropping your *back* knee straight down toward the floor rather than just lunging forward with your front leg. This will naturally balance your weight distribution and ensure a deep, effective range of motion.

Keep up the fantastic momentum—you are very close to achieving a completely clean set of lunges!

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
Great work on your push-up session! Comparing your performance to your previous session on 2026-08-30, you have shown clear improvement. Your overall score increased from 72 to 87, and your correct reps rose from 9 to a flawless 10 out of 10, completely eliminating the incorrect reps and previous errors (hip sag and partial range of motion) from your last workout. 

### Biomechanical Analysis & Form Correction
Your session was completely clean with zero recorded errors. As highlighted in *www.nasm.org/resource-center/blog/training/proper-push-up-form-and-technique-a-complete-guide*, the push-up serves as an essential movement assessment to evaluate your upper-body strength, core stability, and ability to maintain proper alignment under load. Furthermore, as noted in *The_Effect_of_Position_on_the_Percentage_of_Body.992962*, this upper-extremity weight-bearing exercise helps improve joint stability and proprioception through joint compression forces.

If you ever find yourself struggling to maintain alignment as fatigue sets in during future workouts, you can always regress the movement by placing your hands on a bench or your knees on the floor to maintain movement integrity and posture, as recommended by *blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement*. 

Keep up the outstanding consistency and focus on form!

### WITHOUT RAG
### Progress Tracking
Great work on your push-up session today! Compared to your previous session on 2026-08-30—where you logged 9 correct reps, 1 incorrect rep, and an overall score of 72 with common errors like hip sag and partial range of motion—you have made fantastic progress. In this session, you successfully completed all 10 out of 10 reps correctly with zero recorded errors, boosting your overall score up to 87. 

### Biomechanical Analysis
You completely eliminated the hip sag and partial range of motion issues that plagued your previous workout, maintaining a solid, full-range movement standard across all reps. 

Since no external knowledge base context or specific errors were flagged for this flawless session, here are general biomechanical principles to keep in mind for maintaining this high standard:
* **Core & Spine Alignment:** Continue engaging your glutes, abs, and quadriceps to keep your spine in a neutral, plank-like line. This protects your lumbar spine from hyperextension and distributes the load evenly across your upper body.
* **Range of Motion:** Maintain your full depth by lowering your chest smoothly toward the floor with your elbows tracking at a safe angle (roughly 45 degrees relative to your torso), protecting your shoulder joints from excessive anterior stress.

Keep up the incredible consistency and focus. You are well on your way to achieving absolute mastery of the push-up!

---

## Exercise: Bicep Curl

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | principle best / kept |
|---|---|---|---|---|
| Elbow flare | Allowing the elbows to flare outward or drift forward away from the body during the curl | 0.057 / 2 | 0.442 / 0 | — |
| Partial range of motion | Partial range of motion: not fully extending or fully flexing the elbow (half rep) during the curl | 0.272 / 3 | 0.370 / 1 | — |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Elbow flare | source: grokipedia.com/page/Bicep_curl]
Allowing the elbows to flare outward during the curl.

[mistake | re: Elbow flare | source: A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve]
Allowing the elbows to drift away from the body during the curl.

[mistake | re: Partial range of motion | source: grokipedia.com/page/Bicep_curl]
Failing to keep the upper arm stationary during the curl.

[mistake | re: Partial range of motion | source: grokipedia.com/page/Bicep_curl]
Excessive swinging of the body (using momentum) during standing curls.

[mistake | re: Partial range of motion | source: A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve]
Failing to start the movement from full elbow extension.

[finding | re: Partial range of motion | source: grokipedia.com/page/Bicep_curl]
Performing the curl on an incline bench at an angle of 45-60 degrees increases the stretch on the biceps' long head at the bottom position.
```

### WITH RAG
### Progress Tracking
Great job on your progress since your previous session on 2026-08-30! Your overall score improved from 75 to 81, and your correct reps increased from 3 out of 10 up to 6 out of 10. You also reduced your incorrect reps from 7 down to 4. While "Partial range of motion" and "Elbow flare" continue to be areas for improvement, you are moving in the right direction. Keep up the momentum to achieve even cleaner form next time!

---

### Biomechanical Analysis & Form Correction

During this session, you encountered two primary errors: **Partial range of motion** and **Elbow flare**. Here is a breakdown of why these errors happen, the risks they pose, and how to fix them based on our knowledge base:

#### 1. Partial Range of Motion
* **The Issues:** According to `grokipedia.com/page/Bicep_curl` and `A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve`, this error involves failing to start the movement from full elbow extension, failing to keep the upper arm stationary during the curl, and using excessive swinging of the body (momentum) during standing curls.
* **Biomechanical Risk:** Allowing your upper arm to move or swinging your body takes the primary load off the biceps brachii, reducing the effectiveness of the exercise and putting unnecessary stress on your lower back and shoulders. 
* **How to Correct It:** 
  * Ensure every repetition starts from a position of full elbow extension.
  * Keep your upper arms pinned tightly and stationary at your sides throughout the entire lift.
  * *Pro Tip:* According to `grokipedia.com/page/Bicep_curl`, performing the curl on an incline bench at an angle of 45-60 degrees increases the stretch on the biceps' long head at the bottom position, which can help enforce a better, stricter range of motion.

#### 2. Elbow Flare
* **The Issues:** Noted in `grokipedia.com/page/Bicep_curl` and `A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve`, this error happens when you allow your elbows to flare outward or drift away from your body during the curl.
* **Biomechanical Risk:** Letting your elbows drift or flare places compromised joint angles on your shoulders and alters the natural line of pull for the biceps, decreasing targeted muscle recruitment.
* **How to Correct It:** 
  * Consciously lock your elbows by your ribcage. 
  * Imagine your upper arms as hinges permanently attached to your torso as you lift the weight upward.

### WITHOUT RAG
Great work stepping into your workout today! Let’s break down your progress and look closely at your biomechanics to keep you moving toward a flawless session.

### 1. Progress Tracking
You showed fantastic improvement compared to your previous session on August 30th:
* **Overall Score:** Increased from 75 to 81.
* **Correct Reps:** Doubled from 3 correct reps up to 6 correct reps.
* **Incorrect Reps:** Dropped significantly from 7 down to 4. 

You completely eliminated one of your previous primary issues (partial range of motion only appeared once early on), showing much better consistency throughout your set. 

### 2. Biomechanical Analysis & Error Correction
In this session, your remaining errors centered around a **Partial range of motion** (on rep 3) and **Elbow flare** during the ascending phase (on reps 8, 9, and 10). 

Because no specific external context or study data was provided for these errors, we will look at them through general accepted biomechanical principles:

* **Partial Range of Motion:** Failing to complete the full range limits the time under tension for your biceps brachii and prevents full joint articulation. 
  * *Correction:* Ensure you start with your arms fully extended at the bottom and curl all the way up until your forearms meet your biceps at the top.
* **Elbow Flare:** Allowing your elbows to drift forward or flare outward during the ascending phase shifts the workload away from the target elbow flexors and introduces unwanted momentum or shoulder compensation, placing unnecessary stress on your shoulder joint and anterior deltoids.
  * *Correction:* Pin your elbows strictly to your sides (by your ribcage) and treat them as a fixed hinge joint throughout the entire movement. Only your forearms should be moving.

Keep up the momentum—you are building great strength and control. Focus on keeping those elbows locked to your torso on your next set, and let's aim for a 100% clean sheet!

---


# Feedback Comparison: RAG vs NO-RAG

## Pipeline Fix Status — v6 (ชุด P0)

รอบนี้แก้บั๊กและข้อจำกัดด้าน **retrieval** ทั้งชุด (P0-1 ถึง P0-4) ที่พบจากการ review โค้ดทั้งโปรเจกต์
**ไม่มีการ re-ingest** — ใช้ collection `kb_local_curated_v3` ชุดเดิมที่ v5 ใช้ (2,519 chunks) ความต่างทั้งหมดมาจากชั้น query / การกรอง / การจัดรูป context ล้วน ๆ

| # | สิ่งที่แก้ | อะไรที่ผิดใน v5 | แก้อย่างไร |
|---|---|---|---|
| **P0-1** | `item_kind` ถูกกรองหลัง top-k | `similarity_search_with_score(k=6, filter={exercise_id})` แล้วค่อยมาทิ้ง kind ใน Python — `principle` (1,250 ตัว) ท่วม `mistake` (450 ตัว) ตั้งแต่ชั้น top-k ผลคือ bicep-curl `Using momentum` ได้ **0 chunk** ทั้งที่ KB มี mistake ที่ตรงเป๊ะอยู่ 12 ตัว | ย้าย kind เข้าไปใน filter ของ DB (`item_kind: {$in: [...]}`) และค้นแยก mistake / finding คนละรอบ มีโควตาของตัวเอง |
| **P0-2** | threshold 0.38 ใช้ไม่ได้ | ค่านี้ calibrate ตอนที่ P0-1 ยังพังอยู่ จึงวัดจาก distance ที่ไม่ใช่ของจริง และ threshold คงที่ตัวเดียวใช้ไม่ได้ทุกท่า (squat ตัวที่ตรงสุดอยู่ 0.09 แต่ bicep-curl อยู่ 0.35) | เปลี่ยนเป็น **relative gate**: เก็บเฉพาะตัวที่ห่างจากตัวดีที่สุดไม่เกิน 0.20 + hard cap แยกตาม kind (mistake 0.55 / finding **0.40** / principle 0.45) |
| **P0-3** | prefix ใน query กลบสัญญาณ | `f"{name} form correction, biomechanics of: {error}"` — boilerplate ยาวกว่าตัวเนื้อหา ทำให้ distance แย่ลง (0.156 → 0.350) | ส่ง fault-name ล้วน ๆ ไม่มี prefix |
| **P0-4** | context ไม่มี source ติดไปเลย | ส่งแค่ `"\n\n".join(page_content)` แต่ prompt สั่งว่า *"mention what it's from"* — เราสั่งให้โมเดลทำสิ่งที่**เป็นไปไม่ได้**จากข้อมูลที่ให้ มันจึงไปหยิบชื่อ study จากความรู้ตัวเอง นี่คือสาเหตุที่ Step 4 ของ v5 แก้ไม่ตก | ทุก chunk มี header `[kind | re: error | source: ...]` + เพิ่มหัวข้อ "How to read the Context" ใน system prompt |
| **+** | error_type → fault name (mapping layer) | `error_type` ถูก embed ตรง ๆ คำสั่งอย่าง `Keep back straight` จึงไปใกล้ chunk "ท่าที่ถูก" ทั้งที่เราค้นในโซน `mistake` | เพิ่ม `error_taxonomy.py` แปลง error code → ชื่ออาการที่ผิด **`mock_sessions.json` ไม่ถูกแก้เลย** — ตั้งใจให้ mapping อยู่ฝั่งเรา เพราะ production `error_type` มาจากทีมอื่น |
| **+** | ตัดข้อความซ้ำ | KB เก็บข้อเท็จจริงเดียวกันซ้ำหลายสิบสำนวน (top-10 ของ "momentum" คือประโยคเดียวกัน 10 สำนวน) | Jaccard near-duplicate filter ระดับทั้ง session (ไม่ใช่แค่ต่อ query) |

### ผลที่วัดได้ (chunk ที่ผ่านเข้า context จริง)

| exercise | error_type | v5 | v6 | หมายเหตุ |
|---|---|---|---|---|
| squat | Heels lifting off ground | 5 | 4 | v5 ก็ทำงานอยู่แล้ว (error_type เป็นชื่ออาการอยู่แล้ว) v6 ตัดตัวซ้ำออก |
| squat | Keep back straight | 2 (ไม่ตรงทั้งคู่) | 5 | v5 ได้ *"Control squats were performed to 90 degrees"*; v6 ได้ *"Lumbar flexion (butt wink) at the bottom of the squat"* |
| lunge | Back not straight | 5 (ส่วนใหญ่ไม่ตรง) | 4 | v6 ได้ *"Spinal flexion (rounding the back) during the lunge"* ที่ distance **0.020** |
| bicep-curl | Using momentum | **0** | ได้ | mistake ที่ตรงเป๊ะที่ 0.156 |
| bicep-curl | Not full extension | **0** | ได้ | *"Failing to utilize a full range of motion by not fully extending the arms at the bottom"* |
| bicep-curl | Swinging torso | 1 (ไม่ตรง) | ได้ | |

### สิ่งที่**ไม่**ได้แก้ในรอบนี้ (ตั้งใจ เพื่อให้เทียบกับ v5 ได้)

- `temperature=0.7` คงเดิม (ควรลดเป็น 0.1-0.3 แต่จะทำให้แยกไม่ออกว่าความต่างมาจาก retrieval หรือจาก temperature)
- ไม่มี post-generation validation (ตรวจว่าตัวเลขที่ output อ้างมีใน context จริงไหม) — ยังเป็นความเสี่ยงที่ค้างอยู่
- ไม่มี reranker / hybrid search และยังใช้ `all-MiniLM-L6-v2` เหมือนเดิม
- เส้นทาง "ไม่มี error" (push-up) ยังดึงแค่ principle กว้าง ๆ เหมือนเดิม (แค่เปลี่ยน query ให้ตรงขึ้น + เพิ่ม cap)

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

### Retrieved KB Context (RAG run)
```text
[mistake | re: Heels lifting off ground | source: Altered_Knee_and_Ankle_Kinemat]
Lifting the heels off the ground during the squatting motion.

[mistake | re: Heels lifting off ground | source: TheBackSquatAProposedAssessment]
Lifting heels or toes off the ground during the squat.

[mistake | re: Heels lifting off ground | source: Muscle Activation Patterns During Different Squat Techniques]
Lifting heels off the floor during a squat (antero-posterior malalignment).

[mistake | re: Keep back straight | source: ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN]
Lumbar flexion (butt wink) at the bottom of the squat.

[mistake | re: Keep back straight | source: TheBackSquatAProposedAssessment]
Allowing the neutral spine curvature to flex during a deep squat.

[mistake | re: Keep back straight | source: TheBackSquatAProposedAssessment]
Excessive trunk flexion (forward lean) during the squat.

[finding | re: Heels lifting off ground | source: TheBackSquatAProposedAssessment]
Allowing the heels to rise off the ground has been observed to create compensatory torques about the ankles, knees, hips, and lumbar spine (3).

[finding | re: Keep back straight | source: TheBackSquatAProposedAssessment]
Flexing at the spine before 1208 (120 degrees) of hip flexion when squatting may indicate restriction in the posterior fibers of the iliotibial band or lack of lumbar control.

[finding | re: Keep back straight | source: Muscle Activation Patterns During Different Squat Techniques]
Control squats were performed to 90 degrees of flexion.

[finding | re: Heels lifting off ground | source: Altered_Knee_and_Ankle_Kinemat]
A 2-in (5.08-cm) heel lift eliminated medial knee displacement during a double-legged squat.
```

### WITH RAG
### Progress Tracking

Great job on your progress! Comparing your session from August 31, 2026, to your previous session on August 30, 2026, you have shown clear improvement:
* **Overall Score:** Increased from 73 to 79.
* **Correct Reps:** Improved from 4 correct reps up to 6 correct reps.
* **Incorrect Reps:** Decreased from 6 incorrect reps down to 4. 

While you successfully eliminated the "Knees behind toes" error from your previous session, you still encountered form breakdowns regarding keeping your back straight and keeping your heels on the ground.

---

### Biomechanical Analysis & Correction

#### 1. Keep Back Straight (Lumbar Flexion & Excessive Trunk Flexion)
* **The Error:** You experienced lumbar flexion (often called "butt wink") and excessive trunk flexion (forward lean) during the ascending and descending phases of your reps. 
* **Biomechanical Risk:** According to *TheBackSquatAProposedAssessment*, allowing the neutral spine curvature to flex during a deep squat or exhibiting excessive forward lean places improper stress across the body. Furthermore, *TheBackSquatAProposedAssessment* notes that flexing at the spine before 1208 of hip flexion when squatting may indicate a restriction in the posterior fibers of the iliotibial band or a lack of lumbar control.
* **Step-by-Step Correction:** 
  1. Brace your core tightly before initiating the descent to maintain a neutral spine.
  2. Keep your chest proud and drive your elbows slightly down and forward to prevent excessive forward trunk lean.
  3. Control your depth; if you notice your lower back rounding at the bottom, stop your descent just short of that point while working on your mobility and lumbar control.

#### 2. Heels Lifting Off Ground (Antero-Posterior Malalignment)
* **The Error:** Your heels lifted off the floor during the descending phase of rep 6, leading to antero-posterior malalignment.
* **Biomechanical Risk:** As highlighted in *TheBackSquatAProposedAssessment*, allowing the heels to rise off the ground has been observed to create compensatory torques about the ankles, knees, hips, and lumbar spine. 
* **Step-by-Step Correction:**
  1. Distribute your body weight evenly across your entire foot (focusing on the midfoot and heel pressure points).
  2. Push your hips back early in the descent rather than driving your knees forward prematurely.
  3. Work on ankle mobility to ensure your shins can move forward comfortably without forcing your heels up. *(Note: While a 2-in [5.08-cm] heel lift has been observed to eliminate medial knee displacement during a double-legged squat according to Altered_Knee_and_Ankle_Kinemat, addressing your core ankle mobility and foot pressure remains vital for long-term mechanics).*

Keep up the consistent work, focus on maintaining a rigid core, and strive for even cleaner reps in your next session!

### WITHOUT RAG
### Progress Tracking
Great job stepping up to the squat rack for this session! Comparing your performance on August 31, 2026, to your previous session on August 30, 2026, you have shown clear improvement:
* **Overall Score:** Increased from 73 to 79.
* **Correct Reps:** Improved from 4 correct reps up to 6 correct reps.
* **Incorrect Reps:** Decreased from 6 down to 4. 

You completely eliminated the "Knees behind toes" error that appeared in your previous session, which is a fantastic milestone. 

---

### Biomechanical Analysis & Form Correction

While you are progressing well, your current session data indicates two persistent technical breakdowns: **"Keep back straight"** and **"Heels lifting off ground."** 

Since no external knowledge base context was provided for these specific errors, we will look at standard biomechanical principles to keep your joints safe:

1. **Keep back straight:** 
   * *Biomechanics & Risks:* Allowing your spine to round (flex) under load shifts excessive shear stress away from your primary movers (the quadriceps, glutes, and hamstrings) and directly onto the passive spinal structures, intervertebral discs, and supporting ligaments. This dramatically increases the risk of lower back strain.
   * *Correction:* Engage your core tightly before initiating the descent to create intra-abdominal pressure. Keep your chest proud, shoulder blades retracted, and maintain a neutral spine alignment from your tailbone to the crown of your head throughout both the descending and ascending phases.
   
2. **Heels lifting off ground:**
   * *Biomechanics & Risks:* When your heels elevate, your center of mass shifts forward onto your forefeet. This overloads the knee joint and patellar tendon while drastically reducing the activation of your glutes and hamstrings. It also destabilizes your base of support, increasing ankle and knee shear stress.
   * *Correction:* Focus on driving your weight evenly through your entire foot—specifically monitoring your heels and midfoot. Ensure your ankle mobility is sufficient to allow your shins to travel forward comfortably without forcing your heels upward.

Keep up the hard work—your upward trend in score and correct reps proves you are moving in the right direction. Clean up those spinal alignments and heel lifts, and you'll be hitting a completely pristine set of reps in no time!

---

## Exercise: Lunge

### Retrieved KB Context (RAG run)
```text
[mistake | re: Back not straight | source: KritzCroninHume2009BodyweightlungeSCJ]
Spinal flexion (rounding the back) during the lunge.

[finding | re: Back not straight | source: mxn167Sp24]
Lunging with the back foot suspended resulted in almost twice as much activation in the hamstrings and gluteus maximus and medius when compared to the traditional forward lunge (Krause et al., 2018).

[finding | re: Back not straight | source: KritzCroninHume2009BodyweightlungeSCJ]
Mean hip range of motion during a forward lunge has been reported to be 95 6 27/C176 of flexion.
```

### WITH RAG
### Progress Tracking
Great job on your progress since your previous session on August 30, 2026! Your overall score improved from 70 to 79, and your correct repetitions increased from 4 to 7 out of 10. You also successfully eliminated one of your previous common errors ("Front knee past toes"), leaving only one area to refine. Keep up this positive momentum!

---

### Biomechanical Analysis
During your current session, the primary error flagged was **"Back not straight"** (specifically involving spinal flexion, or rounding the back, during the lunge, as noted in *KritzCroninHume2009BodyweightlungeSCJ*). 

* **Biomechanical Impact & Risks:** Rounding your spine places unnecessary shear stress on the lumbar vertebrae and shifts your center of mass forward, which compromises your core stability and alters optimal load distribution across your lower limbs. To put the movement into perspective, data shows that the mean hip range of motion during a forward lunge reaches 95 ± 27° of flexion (*KritzCroninHume2009BodyweightlungeSCJ*). Maintaining a neutral spine is crucial to safely manage these high joint angles. Furthermore, research highlights that variations like lunging with the back foot suspended result in almost twice as much activation in the hamstrings and gluteus maximus and medius when compared to the traditional forward lunge (*mxn167Sp24*), emphasizing how vital stable, upright posture and proper alignment are for engaging the target posterior chain muscles effectively.
* **Step-by-Step Correction:**
  1. **Engage Your Core:** Before initiating the step, brace your abdominal muscles as if you are about to take a light impact to your midsection.
  2. **Chest Up, Shoulders Back:** Keep your chest proud and your shoulders retracted to naturally discourage your upper back from rounding.
  3. **Maintain a Neutral Spine:** Throughout both the descending and ascending phases, visualize a straight line running from your tailbone through the crown of your head, keeping your torso upright and stable.

### WITHOUT RAG
### Progress Tracking
Great job on your Lunge session today! Comparing your performance to your previous session on 2026-08-30, you have shown notable improvements:
* **Overall Score:** Increased from 70 to 79.
* **Correct Reps:** Improved from 4 correct reps up to 7 correct reps.
* **Incorrect Reps:** Successfully dropped from 6 incorrect reps down to just 3. 

You have completely eliminated the "Front knee past toes" error from your previous session, which is a fantastic step forward. Keep up this momentum!

---

### Biomechanical Analysis & Form Correction
During today's session, the only recurring issue was **"Back not straight"**, which occurred on reps 1 (descending), 3 (ascending), and 9 (descending). 

* **Biomechanical Impact:** Allowing your back to slouch or bend during a lunge shifts the center of mass forward, placing excessive, undue stress on the lumbar spine and lower back muscles rather than properly loading the target lower-body musculature (quadriceps and glutes). 
* **Step-by-Step Correction:** 
  1. Engage your core tightly before initiating the step.
  2. Maintain an upright, vertical torso posture throughout both the descending and ascending phases of the movement.
  3. Keep your chest proud and shoulders back, ensuring your spine stays in a neutral, straight alignment from top to bottom.

You are very close to mastering this movement. Focus heavily on core stability and upright posture on your next session to achieve a completely clean set of reps!

---

## Exercise: Push-up

### Retrieved KB Context (RAG run)
```text
[principle | re: general principles | source: The_Effect_of_Position_on_the_Percentage_of_Body.992962]
The push-up is an upper-extremity weight-bearing exercise that can improve joint stability and proprioception through joint compression forces.

[principle | re: general principles | source: The_Effect_of_Position_on_the_Percentage_of_Body.992962]
The modified push-up is an effective alternative for individuals unable to perform a traditional push-up and is ideal for early-stage weight-bearing rehabilitation.

[principle | re: general principles | source: blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement]
The push-up is a versatile bodyweight movement that can be adapted for virtually any fitness level.
```

### WITH RAG
Fantastic work on your latest push-up session! 

### Progress Tracking
You showed brilliant improvement compared to your previous session on August 30, 2026. Your overall score jumped from 72 to an impressive 87, and you successfully eliminated all incorrect reps, bringing your correct rep count up from 9 to a perfect 10 out of 10. Furthermore, you completely resolved the previous issues of neck craning forward and elbows flaring out. Keep up this tremendous momentum!

### Biomechanical Analysis & Form Guidance
Your current session was entirely error-free, which is a fantastic milestone. As you continue to build your routine, keep in mind that the push-up is an upper-extremity weight-bearing exercise that helps improve joint stability and proprioception through joint compression forces, as highlighted in *The_Effect_of_Position_on_the_Percentage_of_Body.992962*. 

Additionally, because the push-up is a versatile bodyweight movement that can be adapted for virtually any fitness level (as noted in *blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement*), you can always utilize variations—such as the modified push-up, which serves as an effective alternative for individuals unable to perform a traditional push-up and is ideal for early-stage weight-bearing rehabilitation (*The_Effect_of_Position_on_the_Percentage_of_Body.992962*)—should you ever need to scale your intensity.

Stay dedicated, maintain your clean form, and keep striving for excellence!

### WITHOUT RAG
### Progress Tracking
Outstanding work on your Push-up session today! Compared to your previous session on August 30, 2026—where you logged 9 correct reps, 1 incorrect rep, and an overall score of 72—you have made fantastic progress. In this session, you achieved **10 correct out of 10 total reps** with **zero incorrect reps**, raising your overall score to **87**. You successfully eliminated the neck craning and elbow flaring issues from your last workout. Keep up this incredible momentum as you continue to refine your movement patterns.

---

## Exercise: Bicep Curl

### Retrieved KB Context (RAG run)
```text
[mistake | re: Swinging torso | source: grokipedia.com/page/Bicep_curl]
Swinging the body or using momentum from the hips or shoulders to lift the weight.

[mistake | re: Swinging torso | source: grokipedia.com/page/Bicep_curl]
Using momentum or swinging to lift the weight.

[mistake | re: Using momentum | source: grokipedia.com/page/Bicep_curl]
Using momentum to lift free weights instead of controlling the load.

[mistake | re: Using momentum | source: grokipedia.com/page/Bicep_curl]
Using momentum or body swing to complete the lift (cheating).

[mistake | re: Not full extension | source: grokipedia.com/page/Bicep_curl]
Poor control during the eccentric (lowering) phase of the curl, leading to elbow strain or tendinitis.

[mistake | re: Using momentum | source: grokipedia.com/page/Bicep_curl]
Cheating by using momentum to lift the weight.

[mistake | re: Not full extension | source: grokipedia.com/page/Bicep_curl]
Failing to utilize a full range of motion by not fully extending the arms at the bottom.

[mistake | re: Not full extension | source: Scandinavian Med Sci Sports - 2014 - Brandner - Unilateral bicep curl hemodynamics  Low‐pressure continuous vs]
Failing to start the repetition with the elbow in full extension.
```

### WITH RAG
### Progress Tracking
Great job on your progress! Compared to your previous session on 2026-08-30 (where you had 3 correct reps, 7 incorrect reps, and an overall score of 75), you have shown noticeable improvement. In this session, your correct reps increased to 6, your incorrect reps dropped to 4, and your overall score improved to 81. Keep up the solid effort as you continue to refine your technique.

---

### Biomechanical Analysis & Form Correction

Based on your session data, you still encountered a few recurring errors during the lift. Here is a breakdown of why these errors happen and how to fix them:

#### 1. Not Full Extension
* **The Biomechanical Issue:** Failing to start the repetition with the elbow in full extension, as noted in *Scandinavian Med Sci Sports - 2014 - Brandner - Unilateral bicep curl hemodynamics Low‐pressure continuous vs*. Furthermore, poor control during the eccentric (lowering) phase of the curl can lead to elbow strain or tendinitis, according to *grokipedia.com/page/Bicep_curl*. 
* **How to Correct It:** Focus heavily on the lowering phase. Actively control the weight all the way down until your arms are completely straight before beginning the next ascent.

#### 2. Using Momentum & Swinging Torso
* **The Biomechanical Issue:** Using momentum, body swing, or cheating to lift the weight shifts the mechanical load away from the target musculature and onto the hips, shoulders, and lower back, failing to control the actual load (*grokipedia.com/page/Bicep_curl*). 
* **How to Correct It:** Stand with your feet shoulder-width apart, brace your core tightly, and pin your elbows strictly at your sides. If you find yourself needing to swing or heave your torso upward, drop the weight slightly to ensure pure, isolated bicep engagement. 

Stay focused, maintain your discipline through every eccentric phase, and you will achieve a flawless session next time!

### WITHOUT RAG
### Progress Tracking
Great job on your progress since your last session on 2026-08-30! 
* **Overall Score:** Increased from 75 to 81.
* **Correct Reps:** Improved significantly from 3 correct reps up to 6.
* **Incorrect Reps:** Decreased from 7 down to 4.

You are moving in the right direction and building better movement consistency. Let's look closely at the remaining errors to help you achieve a flawless set next time.

---

### Biomechanical Analysis & Form Correction

Since no external research context or specific numerical thresholds were provided for this session, we will rely on standard biomechanical principles to refine your technique for your current errors: **Not full extension**, **Using momentum**, and **Swinging torso**.

1. **Not Full Extension (Seen in Rep 3)**
   * **The Issue:** Failing to fully extend your arm at the bottom of the movement cuts the range of motion short, reducing the total time under tension and activation of the lower portion of the biceps brachii.
   * **How to Fix:** At the bottom of every rep, fully straighten your elbow so your arm is completely extended before initiating the next curl. 

2. **Using Momentum & Swinging Torso (Seen in Reps 8, 9, and 10)**
   * **The Issue:** As fatigue sets in during the later reps, using your hips and torso to swing the weight shifts the load away from the target muscles (biceps) and places unnecessary shear stress on your lower back.
   * **How to Fix:** Keep your core braced tightly, pin your upper arms strictly to your sides, and isolate the movement entirely to your elbow joint. If you need to swing your torso to lift the weight, consider dropping the weight slightly to maintain strict form.

Keep up the strong effort—you are well on your way to mastering the bicep curl!

---


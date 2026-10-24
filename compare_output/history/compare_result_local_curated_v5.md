# Feedback Comparison: RAG vs NO-RAG

## Pipeline Fix Status (ตามแผน `toasty-tinkering-feigenbaum`)

การรันนี้เทียบผลหลังแก้ **Step 1, 2, 3 และ 4 ครบทั้งแผน** (ยอมรับความเสี่ยงของ hallucination ที่พบใน Step 4 ไว้ก่อน ไม่ได้เพิ่ม post-generation validation)

| Step | สถานะ | รายละเอียด |
|---|---|---|
| 1. แก้ ingest.py ไม่ให้ตัด JSON กลางคัน | ✅ ทำแล้ว | เปลี่ยนจาก `json.dumps()` ทั้งไฟล์เป็น Document เดียว → สร้าง 1 Document ต่อ 1 item ใน `core_principles`/`common_mistakes`/`specific_findings` พร้อม metadata `item_kind` |
| 2. บังคับ exclude เมื่อ exercise_type ไม่ตรงโฟลเดอร์ + migrate ข้อมูลเก่า | ✅ ทำแล้ว | `curator.py` เปลี่ยนให้ window ที่ mismatch ไม่เข้า `curated_data/` อีกต่อไป (ย้ายไป `excluded_from_kb/` แทน) และรัน migration script ย้อนหลังกับข้อมูลที่ curate ไปแล้ว **พบ mismatch จริง 35 windows จาก 11 ไฟล์** ครอบคลุมทั้ง bicep-curl, lunge, push-up, squat (ไม่ใช่แค่เคส "Deadlift and Alpine Skiing" เดียวที่เจอตอนแรก) — re-ingest เข้า collection ใหม่ `kb_local_curated_v3` (2,519 chunks จาก 2,837 เดิม) |
| 3. Retrieval-time relevance gate (per-error query, score threshold, item_kind filter) | ✅ ทำแล้ว | เปลี่ยนจาก query เดียวรวมทุก error เป็น retrieve แยกทีละ error_type + เพิ่ม similarity score threshold **0.38** (calibrate จากข้อมูลจริงของ 4 mock sessions) + กรองตาม `item_kind` (ไม่มี error → เห็นเฉพาะ `principle`, มี error → เห็นเฉพาะ `mistake`/`finding` ที่ตรงกับ error นั้น) ถ้าไม่ผ่านเกณฑ์เลยจะส่งข้อความบอกตรง ๆ ว่าไม่พบข้อมูลที่เกี่ยวข้อง แทนการปล่อยว่างหรือส่งของเดิมที่ไม่ตรงประเด็น |
| 4. ปรับ grounding rule ให้เข้มขึ้น | ✅ ทำแล้ว (แต่ไม่ได้ผล 100%) | เพิ่มข้อห้ามชัดเจนว่าห้าม cite ตัวเลข/ชื่อ study ใด ๆ ที่ไม่ปรากฏคำต่อคำใน Context แม้โมเดลจะรู้จากความรู้ทั่วไปของตัวเองก็ตาม — **ทดสอบแล้วพบว่า Gemini ยังคง hallucinate สถิติงานวิจัย push-up/firefighter ซ้ำได้แม้จะมีกฎนี้** (ยืนยันด้วยการ print context จริงเทียบ output) สรุปคือ prompt-level instruction อย่างเดียวไม่ใช่ hard constraint — ทีมตัดสินใจ **ยอมรับความเสี่ยงนี้ไว้ก่อน** ไม่เพิ่ม post-generation validation ในตอนนี้ |

**สรุปสิ่งที่ต่างจาก v4:** เปลี่ยนทั้ง curated_data (ตัด 35 mismatched windows ออก, Step 2) และ retrieval logic (per-error query + score threshold 0.38 + item_kind filter แทน top-k=5 แบบเดิม, Step 3) — ระวังเมื่อเทียบผลว่าความต่างมาจากทั้งสองจุดพร้อมกัน ไม่ใช่แค่จุดเดียว

**บั๊กที่เจอและแก้ระหว่างทำ Step 3:** รอบแรกที่รันไฟล์นี้ (ก่อนจะได้ผลลัพธ์ด้านล่าง) ทุก exercise fallback ไป "no KB match" หมด ทั้งที่ข้อมูลถูก ingest สำเร็จ 2,519 chunks สาเหตุคือ `langchain_pg_embedding.id` เป็น primary key **แบบ global ข้าม collection** ใน schema นี้ ไม่ใช่ scope ต่อ collection — `ingest.py` เดิมคำนวณ id จาก `content+metadata` เท่านั้น ไม่รวมชื่อ collection พอ item ที่เหลือหลัง Step 2 migration มี content+metadata ตรงกับที่เคย ingest ไปแล้วใน `kb_local_curated_v2` (Step 1 only) การ insert เข้า `kb_local_curated_v3` จึงชนกับ id เดิมและ no-op เงียบ ๆ ผ่าน `ON CONFLICT DO NOTHING` ทำให้ collection ใหม่มี 0 แถวทั้งที่ log บอกว่าสำเร็จ 100% แก้โดยรวมชื่อ collection เข้าไปใน hash string ก่อนคำนวณ id (`ingest.py` บรรทัดที่คำนวณ `doc_id`) แล้ว re-ingest ใหม่จึงได้ผลลัพธ์ที่ถูกต้องด้านล่างนี้

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

Grounding rule: If the Context below contains a specific number, percentage, joint angle, study finding, or named source,
you MUST cite that specific detail (and mention what it's from) rather than a generic restatement.
Do NOT cite any specific number, percentage, study name, sample size, date range, or named finding that does not
appear verbatim in the Context below — even if you recognize the study or believe the fact to be true from your
own general knowledge. Your own training knowledge must never substitute for the Context; if a fact is not in
the Context, treat it as unavailable to you for citation purposes. If the Context has no specifics for a given
error, say so briefly and fall back to general accepted biomechanical principles, described in general terms
only with no invented numbers or named sources.

Context from Knowledge Base:
{context}
```

---

## Exercise: Squat

### WITH RAG
Hello! As your personal trainer and biomechanics consultant, I am excited to review your latest squat session. Let’s dive straight into your progress and biomechanical analysis.

### 1. Progress Tracking
You showed fantastic improvement compared to your previous session on August 30, 2026! 
* **Overall Score:** Rose from 73 to 79.
* **Correct Reps:** Increased from 4 correct reps up to 6 correct reps.
* **Incorrect Reps:** Decreased from 6 down to 4. 

While you still battled some recurring postural issues, your upward trend in correct reps and overall score indicates that your body is adapting and responding well to practice. Keep this momentum going!

---

### 2. Biomechanical Analysis & Error Correction
In this session, your errors centered around keeping your back straight and **lifting your heels off the ground during the descending movement** (identified as antero-posterior malalignment). 

**Why this is problematic:**
* **Heels lifting off the ground / Antero-posterior malalignment:** As noted in our knowledge base, lifting the heels off the floor during a squat alters your center of gravity forward. This shifts undue stress onto your forefeet, ankle joints, and knees, reducing your overall stability. 
* **Back rounding ("Keep back straight"):** Failing to maintain a neutral spine during the descending and ascending phases places excessive shear stress on the lumbar vertebrae and spinal ligaments, putting your lower back at risk of injury.

**Step-by-Step Correction:**
1. **Anchor Your Feet:** Focus on driving your weight evenly across your entire foot—specifically distributing pressure between your heel, big toe, and pinky toe. Think of your feet gripping the floor like suction cups to prevent your heels from rising.
2. **Maintain Spinal Alignment:** Before you begin your descent, brace your core tightly, pull your shoulders back and down, and keep your chest proud. Maintain this torso angle throughout both the descent and ascent to ensure your back stays straight.
3. **Control the Depth:** As outlined in our controlled squat protocols, focus on maintaining clean form (such as controlling your movement down to 90 degrees of flexion) without letting your body shift forward onto your toes. 

You are making great strides. Stay focused on heel contact and core bracing, and let's aim for an even higher correct rep count in your next session!

### WITHOUT RAG
### Progress Tracking
Great job on your progress! Compared to your previous session on 2026-08-30 (where you scored 73 overall with 4 correct reps and 6 incorrect reps), you have shown a positive improvement. In this session, your overall score increased to 79, and you successfully completed 6 correct repetitions out of 10. You also completely eliminated the "Knees behind toes" error that appeared in your last workout. Keep up the momentum!

---

### Biomechanical Analysis & Form Correction

The data shows two primary error categories during this session: **"Keep back straight"** (occurring during the descending and ascending phases) and **"Heels lifting off ground"** (occurring during the descending phase). 

*(Note: Since no specific external context or research statistics were provided in the knowledge base for this session, the following analysis is based strictly on standard biomechanical principles.)*

#### 1. Maintaining a Straight Back
* **Biomechanical Risk:** Rounding or arching the back excessively compromises spinal alignment. This shifts mechanical load away from the primary lower-body prime movers (the gluteus maximus and quadriceps) and places shear stress on the lumbar spine and intervertebral discs, increasing injury risk to the lower back.
* **Correction:** Engage your core tightly before initiating the movement ("brace" your midsection). Keep your chest proud, shoulders pulled back and down, and maintain a neutral spine angle throughout both the descent and the ascent. 

#### 2. Keeping Heels Planted (Preventing Heel Lift)
* **Biomechanical Risk:** When your heels lift off the ground, your center of gravity shifts forward onto the balls of your feet and toes. This places undue stress on the patellar tendon and knee joints while reducing ankle dorsiflexion and diminishing overall power output from your posterior chain.
* **Correction:** Distribute your weight evenly across your entire foot—focusing on heavy contact through your heels and midfoot. If you find your heels naturally rising, you may need to work on ankle mobility or slightly adjust your stance width and toe-out angle.

Stay focused on these cues for your next session, and you'll be well on your way to mastering a completely clean set of squats!

---

## Exercise: Lunge

### WITH RAG
### Progress Tracking
Great work on your session today! Comparing your performance to your previous session on 2026-08-30, you have shown clear improvement:
* **Overall Score:** Increased from 70 to 79.
* **Correct Reps:** Improved from 4 correct reps up to 7 correct reps.
* **Incorrect Reps:** Decreased from 6 incorrect reps down to just 3. 

You have successfully eliminated one of your previous common errors ("Front knee past toes") entirely. Keep up this momentum!

---

### Biomechanical Analysis & Form Correction
During today's session, the remaining error logged was **"Back not straight"** (which corresponds to spinal flexion, or rounding the back, during the lunge). 

#### Why This Error is Problematic:
* **Spinal Flexion:** Rounding the back compromises your spinal stability and shifts unwanted stress away from your target lower-body musculature and onto the spinal structures. 
* **Biomechanical Context:** The lunge involves complex multi-joint movements—including hip flexion, extension, and adduction; knee flexion, extension, and abduction; tibial internal rotation; talar plantar flexion and adduction; and calcaneal eversion. When your spine flexes, it disrupts the kinetic chain required to cleanly execute these lower-extremity actions safely.

#### Step-by-Step Correction:
1. **Engage Your Core:** Before initiating your step, brace your abdominal muscles to create a stable cylinder around your spine.
2. **Chest Up, Eyes Forward:** Keep your chest proud and your gaze locked straight ahead to naturally prevent your thoracic spine from rounding.
3. **Maintain a Neutral Spine:** Throughout both the descending and ascending phases of the movement, keep your torso upright and your back straight. In a traditional lunge, focus on lowering your body so that your back knee ends at approximately a 90-degree angle without letting your torso collapse forward.

You are very close to mastering this movement pattern. Address that spinal alignment on your next session, and you'll be well on your way to a perfect score!

### WITHOUT RAG
### Progress Tracking
Great work on your lunge session today! Comparing your performance to your previous session on 2026-08-30, you have shown notable improvement. Your overall score increased from 70 to 79, and your correct reps jumped from 4 out of 10 up to 7 out of 10. Additionally, you completely eliminated the "Front knee past toes" error that was present in your previous workout. Keep up this positive momentum!

---

### Biomechanical Analysis & Form Correction
During today's session, the only recurring issue was **"Back not straight"**, which occurred on reps 1, 3, and 9 (during both the descending and ascending phases). 

*(Note: The provided knowledge base does not contain specific external metrics, angles, or studies for this session, so the following analysis is based on established biomechanical principles.)*

* **Why this error is problematic:** Failing to keep your back straight during a lunge compromises your spinal alignment and shifts unwanted shear stress onto your lumbar vertebrae. It also inhibits proper core engagement, reducing your overall stability and placing excess fatigue on your lower back instead of the intended target muscle groups in your lower body (such as the glutes, quadriceps, and hamstrings). This increases your risk of lower back strain.
* **How to correct it step-by-step:**
  1. **Engage your core:** Before initiating the step, brace your abdominal muscles as if anticipating a light impact to your midsection.
  2. **Set your posture:** Roll your shoulders back and down, and keep your chest proud and elevated throughout the entire movement.
  3. **Maintain a vertical torso:** As you descend and ascend, focus on moving straight up and down rather than leaning your torso forward over your front thigh. Imagine a straight line running from the crown of your head through your spine to your tailbone.

You are moving in the right direction and clearly building better movement patterns. Focus on keeping that chest up and core braced for your next session to lock in 10% perfect reps!

---

## Exercise: Push-up

### WITH RAG
Hello! As your personal trainer, biomechanics specialist, and physical therapy consultant, I am thrilled to review your latest push-up session.

### 1. Progress Tracking
You showed fantastic improvement compared to your previous session on 2026-08-30! 
* **Overall Score:** Increased from 72 to an impressive 87.
* **Correct Reps:** Improved from 9 correct reps (with 1 incorrect rep) to a pristine **10 out of 10 correct reps** with zero errors recorded during this session. 

You successfully eliminated the neck craning and elbow flaring issues that were present in your last workout. Keep up this phenomenal momentum!

### 2. Biomechanical Analysis & Form Insights
Because you executed all 10 repetitions without logged errors, your form was clean and your alignment remained steady. To help you maintain and build upon this success, let's look at key biomechanical principles regarding your movement:

* **Joint Stability and Loading:** As noted in our knowledge base, the push-up serves as an upper-extremity weight-bearing exercise that enhances joint stability and proprioception through joint compression forces. Maintaining your strict form ensures that these forces are distributed evenly across your joints.
* **Elbow Biomechanics:** Remember that forearm rotation during the push-up exercise directly influences the biomechanical load experienced by the elbow. Keeping your forearms aligned and your elbows tucked appropriately protects the joint complex from undue stress.
* **Versatility and Range of Motion:** The push-up is a versatile bodyweight movement that can be adapted for virtually any fitness level. If you ever incorporate variations or use it in rehabilitation settings, remember that your range of motion (ROM) may need to be altered to prevent putting undue stress on weak or injured structures, and you can select appropriate variations—such as incline, knee, standard, tempo, or stability-based options—to match your current fitness level and avoid compensations.

### Summary
Your dedication to proper execution is clearly paying off. Strive to keep your core braced, your neck neutral, and your mechanics consistent in every future session. Outstanding work today—keep pushing forward!

### WITHOUT RAG
### Progress Tracking
Outstanding work on your push-up session today! Compared to your previous session on 2026-08-30—where you logged 9 correct reps, 1 incorrect rep, and an overall score of 72—you have made fantastic progress. In this session, you successfully completed **10 out of 10 correct reps** with zero errors flagged, raising your overall score to **87**. You completely eliminated the neck craning and elbow flaring issues from your last workout. 

---

### Biomechanical Analysis & Form Feedback
Because you executed all 10 repetitions without any recorded errors, your form was clean and structurally sound. 

* **Why Your Form Worked Well:** Keeping your elbows tucked and your neck neutral ensured optimal force transfer through the pectoralis major, anterior deltoids, and triceps, while protecting your cervical spine and shoulder girdle (specifically reducing undue shearing stress on the rotator cuff and acromion).
* **Next Steps for Mastery:** Since no external context or specific errors were triggered in this session, focus on maintaining this precise alignment. Continue to engage your core tightly, keep your gaze fixed slightly ahead of your hands to maintain a neutral spine, and track your elbows at roughly a 45-degree angle relative to your torso as you build toward even higher overall consistency scores.

Keep up the phenomenal dedication—your consistency is paying off!

---

## Exercise: Bicep Curl

### WITH RAG
### Progress Tracking
Great job on your progress since your previous session on 2026-08-30! Your overall score improved from 75 to 81, and your correct rep count doubled from 3 to 6 reps (with incorrect reps dropping from 7 down to 4). While you still experienced some lingering issues with momentum and range of motion (such as incomplete extension and torso swinging), your upward trajectory shows solid dedication. Let’s clean these movement patterns up to secure an even higher score next time.

---

### Biomechanical Analysis & Form Correction

Based on your session data, you encountered issues with incomplete extension, using momentum, and torso swinging—which often ties directly back to load management. 

#### 1. Managing Load and Wrist Alignment
* **Biomechanical Risk:** According to our training knowledge base, using excessively heavy loads on bicep curls can compromise your wrist alignment and overall form. When the weight is too heavy, your wrists tend to flex or extend to compensate for the fatigue, placing undue stress on the wrist joints, forearms, and distal tendons.
* **Step-by-Step Correction:** 
  1. Drop the weight down to a load that allows you to maintain a neutral, rigid wrist throughout the entire curling movement. 
  2. Keep your knuckles aligned with your forearms without letting your wrists curl inward or backward at the top or bottom of the lift.

#### 2. Eliminating Momentum, Torso Swinging, and Fixing Extension
* **Biomechanical Risk:** Swinging the torso and relying on momentum reduces the activation of the target musculature (the biceps brachii) and transfers improper shear stress onto the lower back and shoulders. Furthermore, cutting reps short ("not full extension") robs the elbow joint of its full functional range of motion.
* **Step-by-Step Correction:**
  1. Stand tall with your core braced, pinning your elbows tightly by your sides to prevent unnecessary torso movement.
  2. Lower the weight completely on the descent until your arms are fully extended, then curl upward strictly using your elbow flexors without rocking your body.

### WITHOUT RAG
Hello! As your personal trainer and biomechanics specialist, let's break down your Bicep Curl session from August 31, 2026, and compare it to your previous workout on August 30, 2026.

### Progress Tracking
You are making great strides! 
* **Overall Score:** Improved from 75 to 81.
* **Correct Reps:** Doubled from 3 correct reps in your previous session to **6 correct reps** today.
* **Incorrect Reps:** Decreased from 7 down to **4**, showing better endurance and overall form retention. 

You have successfully reduced the frequency of your previous issues, but we still have a few mechanical breakdowns to iron out.

---

### Biomechanical Analysis & Form Correction

Based on your session details, you encountered two primary errors during the ascending phase: **Not full extension** (Rep 3), **Using momentum** (Reps 8 & 9), and **Swinging torso** (Rep 10). 

*(Note: Since no specific external research data or numerical joint angles are provided in our current knowledge base, the following recommendations are based strictly on foundational biomechanical and physical therapy principles.)*

1. **Not Full Extension (Rep 3)**
   * **The Biomechanical Issue:** Failing to fully extend your arms at the bottom of the movement shortens the active range of motion. This prevents the target muscle (the biceps brachii) from experiencing a full stretch under tension, reducing overall muscle recruitment and joint mobility at the elbow.
   * **How to Correct It:** At the bottom of each repetition, consciously allow your arms to straighten completely before initiating the next curl. 

2. **Using Momentum & Swinging Torso (Reps 8, 9, and 10)**
   * **The Biomechanical Issue:** As fatigue sets in toward the end of your set, using your hips or swinging your torso introduces auxiliary momentum. This shifts the load away from your biceps and places unnecessary shear stress on your lower back (lumbar spine) and anterior shoulder joints, cheating the target muscles out of the work.
   * **How to Correct It:** Keep your core tightly braced, pin your upper arms rigidly to your sides, and ensure that movement occurs strictly at the elbow joint. If you need to swing your torso to lift the weight, it is a sign that fatigue has set in, and dropping to a slightly lighter weight or resting will protect your spine and preserve your form.

### Summary & Encouragement
Your consistency is paying off, and doubling your clean repetitions is a fantastic achievement! Focus on strict control, full range of motion, and eliminating body English as you approach the end of your sets. Keep up the phenomenal work—you are well on your way to mastering this exercise!

---


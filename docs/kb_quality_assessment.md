# ประเมินคุณภาพ Knowledge Base (`curated_data/` → `kb_local_curated_v3`)

**วันที่:** 2026-09-08 (อัปเดตล่าสุด 2026-09-18 — ดู §8–11 ท้ายเอกสาร)
**ขอบเขต:** 2,519 chunks / 33 แหล่ง / 4 ท่า — วัดด้วย all-MiniLM-L6-v2 ตัวเดียวกับที่ระบบใช้จริง ณ ตอนเขียน (§1–7)
**สถานะปัจจุบัน (2026-09-18):** default collection ของระบบคือ `kb_gemini_curated_v5` (**1,897 chunks** — ดู §11) ผ่าน `embedding_config.py` (`gemini-embedding-2`) — `kb_gemini_curated_v4` (2,348 chunks) และ `kb_local_curated_v4` (MiniLM) ยังอยู่ครบเป็น fallback/comparison เทียบผลได้เสมอ ไม่ได้ถูกแตะจากงาน v5 เลย — ตัวเลข distance/threshold ใน §1–7 ทั้งหมดเป็นของ MiniLM เท่านั้น ใช้เทียบข้ามรุ่นไม่ได้ตรง ๆ ดู §10 สำหรับค่า Gemini/v4 ที่ re-tune แล้ว และ §11 สำหรับ v5

---

## 1. สรุปสั้น

ข้อมูล **ยังไม่พอ** และปัญหาไม่ใช่ "ปริมาณน้อยเกินไป" แต่เป็น **ผิดชนิด** — เรามีงานวิจัยเรื่องสรีรวิทยา/EMG/ระบาดวิทยาของแต่ละท่าเยอะมาก แต่มีเอกสารที่พูดถึง *"ทำท่าผิดแบบไหน และผิดแล้วเกิดอะไรขึ้น"* น้อยมาก ซึ่งคือสิ่งเดียวที่ระบบ feedback ต้องใช้

| ท่า | chunks | mistake | finding | ตัดสิน |
|---|---|---|---|---|
| squat | 1,120 | 255 | 320 | ✅ พอใช้ได้ |
| lunge | 574 | 84 | 192 | ✅ พอใช้ได้ |
| bicep-curl | 488 | 67 | 199 | ⚠️ mistake พอ แต่ **finding ใช้ไม่ได้เลย** + พึ่งแหล่งเดียว |
| push-up | 337 | 44 | 108 | 🔴 **ไม่พอ** — ครอบคลุม error ของตัวเองไม่ได้ |

---

## 2. Coverage ต่อ "อาการที่ผิด" จริง (ตัวเลขที่สำคัญที่สุด)

จำนวน chunk ที่อยู่ในระยะใช้งานได้ (cosine distance ≤ 0.40) ต่อ 1 fault:

| ท่า | fault | mistake ≤0.40 | finding ≤0.40 | best mistake |
|---|---|---|---|---|
| squat | Lumbar flexion (หลังงอ) | 11 | 5 | 0.213 ✅ |
| squat | Knee past toes | 19 | **0** | 0.225 ✅ |
| squat | Heels lifting | 10 | 4 | 0.095 ✅ |
| lunge | Spinal flexion | 9 | 9 | 0.020 ✅ |
| lunge | Front knee past toes | 10 | 9 | 0.248 ✅ |
| **push-up** | **Neck craning forward** | **1** | **0** | 0.392 ⚠️ |
| **push-up** | **Elbows flaring out** | **0** | **0** | 0.403 🔴 |
| bicep-curl | Not full extension | 2 | **0** | 0.323 ⚠️ |
| bicep-curl | Using momentum | 10 | **0** | 0.156 ✅ |
| bicep-curl | Swinging torso | 9 | **0** | 0.086 ✅ |

**อ่านตารางนี้ยังไง:**
- `mistake = 0` แปลว่าถ้าผู้ใช้ทำผิดแบบนั้น ระบบ**ไม่มีอะไรจะพูด**นอกจากความรู้ทั่วไปของ LLM → นี่คือจุดที่ hallucination เกิดง่ายที่สุด
- `finding = 0` แปลว่าอธิบายได้แต่**อ้างตัวเลข/งานวิจัยไม่ได้** ซึ่งคือคุณค่าหลักที่ RAG ควรให้เหนือกว่า no-RAG

---

## 3. ปัญหาที่พบ เรียงตามความรุนแรง

### 🔴 3.1 push-up ครอบคลุม error ของตัวเองไม่ได้เลย
`Elbows flaring out` ได้ 0 chunk, `Neck craning forward` ได้ 1 chunk ที่ระยะ 0.392 (เฉียดขอบ)
สาเหตุ: แหล่งข้อมูล push-up ที่มี **36% ไม่ได้พูดเรื่องฟอร์มเลย**
- `Association Between Push-up Capacity and Future Cardiovascular Events` (19.3%) — ระบาดวิทยาโรคหัวใจ
- `Effects of soleus push-up... immune-inflammatory index and blood lipid` (16.9%) — ชีวเคมีเลือด

นี่คือที่มาของสถิติ "firefighter / cardiovascular" ที่โผล่ในผลรัน v5 — ตรวจแล้วพบว่า chunk *"Study cohort consisted of 1104 occupationally active adult male firefighters"* **มีอยู่จริงใน KB** (6 chunks) แค่ไม่ได้ถูก retrieve ในรอบนั้น กล่าวคือ KB เองเป็นคน "ป้อนแนวคิด" ให้โมเดลไปหยิบตัวเลขทำนองนี้มาใส่

### 🔴 3.2 bicep-curl มี `finding` 199 ตัว แต่ใช้กับ error จริงไม่ได้สักตัว
finding ที่ใกล้ที่สุดของทั้ง 3 fault อยู่ที่ 0.424 / 0.539 / 0.563 — ไกลเกินจะเชื่อถือได้
เพราะ PDF bicep-curl ทั้ง 5 ไฟล์เป็นเรื่อง EMG, blood-flow restriction, eccentric overload machine, rest-pause — **ไม่มีไฟล์ไหนศึกษาเรื่องฟอร์มผิด**

### 🟠 3.3 ความรู้เรื่อง "ท่าผิด" ของ bicep-curl พึ่งแหล่งเดียว และเป็นแหล่งที่อ้างอิงไม่ได้
`grokipedia.com/page/Bicep_curl` เป็นเจ้าของ **35 จาก 67 mistake chunks (52%)** ของ bicep-curl
เป็นวิกิที่สร้างด้วย AI ไม่ผ่าน peer review — ในเชิงวิชาการนี่เป็นจุดอ่อนที่ถูกซักได้ทันที และในเชิงระบบคือ single point of failure

### 🟠 3.4 มีเนื้อหานอกเรื่องปนอยู่ทั่ว KB
มาจาก `AsyncHtmlLoader` ที่ดูดทั้งหน้าเว็บรวม sidebar/related articles ของ NASM blog + `is_relevant` ใน `curator.py` ที่นิยามกว้างเกินไป (ยอมรับ "sports science ทั่วไป")

| คำ | จำนวน chunk | อยู่ในโฟลเดอร์ |
|---|---|---|
| GLP-1 (ยาลดน้ำหนัก) | 16 | lunge, squat |
| cardiovascular training zones | 21 | lunge |
| osteoporosis / bone density | 8 | lunge |
| haemophilia | 10 | lunge |
| foam rolling | 5 | bicep-curl |

### 🟠 3.5 62–68% ของ chunk ไม่เอ่ยชื่อท่าของตัวเองเลย
เช่น *"Control squats were performed to 90 degrees of flexion."* — อ่านเดี่ยว ๆ ไม่รู้ว่าเป็นท่าอะไร งานวิจัยไหน สรุปว่าอะไร
เป็นผลจากการ curate ที่ตัดประโยคออกจากบริบท (เฉลี่ย 126 ตัวอักษร/chunk) ทำให้ทั้ง embedding และ LLM เสียข้อมูล

### 🟡 3.6 การกระจุกตัวของแหล่ง
`Effect of hip adductor (Squat)` ให้ 34% ของ KB squat ทั้งหมด — ถ้าไฟล์เดียวนี้มี bias หรือ curate ผิด จะกระทบทั้งท่า

---

## 4. สิ่งที่ควรไปหาเพิ่ม (เรียงตามผลตอบแทน)

### ลำดับ 1 — push-up form & fault (จำเป็น ไม่งั้นท่านี้ใช้งานไม่ได้)
มองหาคำค้น: *push-up scapular control*, *elbow flare push-up EMG*, *cervical protraction push-up*, *push-up kinematics faults*
แหล่งที่น่าจะมี: NSCA Strength & Conditioning Journal, JOSPT, ACE ProSource, textbook ของ physical therapy

### ลำดับ 2 — bicep-curl fault + ตัวเลข
มองหา: *elbow ROM biceps curl full extension hypertrophy*, *cheat curl lumbar load*, *momentum-assisted curl kinetics*
เป้าหมายคือหางานที่ **วัดผลของการทำผิด** ไม่ใช่แค่วัด EMG ของท่าที่ถูก

### ลำดับ 3 — squat `Knees behind toes` ที่มีตัวเลข
ตอนนี้มี mistake 19 ตัวแต่ finding 0 → มองหางานวัด knee shear force / patellofemoral joint stress vs. knee-forward translation

### ลำดับ 4 — เอาของนอกเรื่องออก
ก่อนหาเพิ่ม ควรถอด 4 ไฟล์นี้ออกจาก `data/` (หรือ exclude ตอน curate) เพราะมันเจือจาง KB และเป็นแหล่งของ hallucination:
- `push-up/Association BetweenPush-upExercise Capacity andFuture Cardiovascular Events...`
- `push-up/Effects of soleus push-up exercise on systemic immune-inflammatory index...`
- `lunge/Haemophilia - 2026 - Tan - Weight-Bearing Lunge Test...`
- `lunge/Lunge_exercises_with_blood-flo...` (BFR — ไม่เกี่ยวกับฟอร์ม)

> ทั้งหมดเป็นงานวิจัยที่ดี แต่ตอบคำถามคนละข้อกับที่ระบบเราถาม

---

## 5. สิ่งที่ควรแก้ในไปป์ไลน์ควบคู่กับการหาข้อมูลเพิ่ม

1. **`curator.py` — บีบนิยาม `is_relevant`** ให้เป็น "เกี่ยวกับ *ฟอร์ม/ข้อผิดพลาด/การบาดเจ็บ* ของท่านี้" ไม่ใช่ "เกี่ยวกับ sports science" กว้าง ๆ
2. **แยก loader ของ URL ให้ดึงเฉพาะ main content** (ตอนนี้ `AsyncHtmlLoader` + `Html2TextTransformer` เอา nav/sidebar/related มาด้วย) — ใช้ readability/trafilatura แทน
3. **ใส่ context ให้ chunk ตอน embed** เช่น `"[squat | common mistake | TheBackSquat] " + item` เพื่อแก้ปัญหาข้อ 3.5
4. **เพิ่ม field `applies_to_fault`** ใน schema ของ curator ให้ LLM ระบุเลยว่า mistake ข้อนี้ตรงกับ fault code ไหนใน `error_taxonomy.py` → ทำให้ retrieval ใช้ metadata filter ตรง ๆ ได้ ไม่ต้องพึ่ง semantic similarity อย่างเดียว
5. **ตั้ง golden set** (fault → chunk ที่ควรเจอ) แล้ววัด recall@k ทุกครั้งที่เพิ่มข้อมูล — ตอนนี้ไม่มีทางรู้ว่าเพิ่มข้อมูลแล้วดีขึ้นจริงไหม

---

## 6. สถานะหลังแก้ (2026-09-11) → `kb_local_curated_v4`

ทำแล้ว: ข้อ 4 ลำดับ 4 (ถอด 4+1 ไฟล์นอกเรื่อง), ข้อ 5.1 (บีบ `is_relevant`), 5.2 (trafilatura), 5.4 (`applies_to_fault`), และ `kb_coverage.py` ทำหน้าที่ 5.5 แบบ proxy
ข้อ 5.3 (embed header) **ทดลองแล้วถอดออก** — เลื่อนสเกล distance ทั้งกระดานจน threshold v6 ใช้ไม่ได้ และซ้ำกับ filter `exercise_id`/`item_kind`

**สิ่งที่พบเพิ่ม:** 4 ลิงก์ NASM (squat-form, squat-misconceptions, lunge, progressions) ตายตั้งแต่ก่อน scrape รอบ v3 — JSON เดิม "10 windows / ~80 items" ต่อลิงก์คือ*หน้า index ของ blog* ที่ถูก curate ไป นี่คือที่มาจริงของข้อ 3.4 ไม่ใช่แค่ sidebar แก้ด้วย Wayback Machine snapshot ปี 2020–21

**ผล (จาก `python kb_coverage.py --collection kb_local_curated_v3 --collection kb_local_curated_v4`):**

| ท่า | fault | v3 mistake | v3 finding | v4 mistake | v4 finding |
|---|---|---|---|---|---|
| squat | keep back straight | 11 | 5 | 13 | 4 |
| squat | knees behind toes | 19 | 0 🔴 | 19 | 1 ⚠️ |
| squat | heels lifting | 10 | 4 | 13 | 4 |
| lunge | back not straight | 9 | 9 | 12 | 11 |
| lunge | front knee past toes | 10 | 9 | 12 | 9 |
| push-up | neck craning forward | 1 ⚠️ | 0 🔴 | 1 ⚠️ | 0 🔴 |
| push-up | elbows flaring out | 0 🔴 | 0 🔴 | 1 ⚠️ (0.332) | 0 🔴 |
| bicep-curl | not full extension | 2 ⚠️ | 0 🔴 | **8** (0.264) | 0 🔴 |
| bicep-curl | using momentum | 10 | 0 🔴 | 6 | 0 🔴 |
| bicep-curl | swinging torso | 9 | 0 🔴 | 8 | 0 🔴 |

**อ่านผล:** KB สะอาดขึ้น (2,519 → 2,432 chunk โดยที่ของนอกเรื่องหายไป) และ bicep-curl `not full extension` ใช้งานได้แล้ว แต่ **push-up ยังไม่พอ** และ **finding ของ bicep-curl ยังเป็น 0 ทุก fault** — PDF ใหม่ทั้ง 10 ไฟล์ของสองท่านี้เป็น EMG/biomechanics ของท่าที่ถูก ไม่ได้วัดผลของการทำผิด ปัญหาเดิมข้อ 3.2 ยังอยู่
`using momentum` ลด 10 → 6 เพราะ paraphrase ซ้ำ ๆ จากหน้า grokipedia ที่เคย scrape ทั้งหน้าหายไป (best distance ดีขึ้น 0.156 → 0.119)

**ทางเลือกถัดไป:** ใน v4 มี chunk ที่ curator แท็ก `applies_to_fault` ไว้มากกว่าที่ semantic search หาเจอ (push-up `elbows flaring out`: แท็ก 8 mistake vs เจอ 1 ที่ ≤0.40) → ลอง fallback ใน `_search`: ถ้า semantic ได้ < 2 ให้ดึงจาก tag แทน

---

## 7. Golden set + ผลวัด gate จริง (2026-09-11) — ปิดข้อ 5.5

ไฟล์: `eval/golden_chunks.json` (ต่อ fault ทั้ง 10: `must_hit` / `must_not_hit` เป็น substring ของ chunk จริงใน v4) และ `eval/eval_retrieval.py` ซึ่งเรียก `retrieve_kb_blocks()` ของ `test_rag_compare.py` ตรง ๆ — วัด **สิ่งที่ gate ปล่อยเข้า context** ไม่ใช่ pool ≤0.40 แบบ `kb_coverage.py`

```
python eval/eval_retrieval.py                                   # baseline gate v6 บน v4
python eval/eval_retrieval.py --margin 0.10 --cap mistake=0.40  # ลอง gate อื่นโดยไม่แก้โค้ด
python eval/eval_retrieval.py --collection kb_local_curated_v4 --collection kb_local_curated_v5
```

**Baseline (gate v6, kb_local_curated_v4)** — รายงานเต็ม `compare_output/golden_baseline_v6gate_v4.md`

| mode | fault ที่มี mistake ถูก ≥1 | chunk ใน context | good | bad | neutral | precision |
|---|---|---|---|---|---|---|
| single (10 fault เดี่ยว) | 8/10 | 41 | 21 | **14** | 6 | 0.51 |
| session (mock 4 session) | 5/6 | 24 | 12 | **9** | 3 | 0.50 |
| single, `--margin 0.10 --cap mistake=0.40` | 8/10 | 33 | 18 | **11** | 4 | 0.55 |

**อ่านผล — bad 14 ตัวใน single มาจาก 4 สาเหตุ และ gate แก้ได้แค่สาเหตุเดียว:**

| สาเหตุ | bad | fault | แก้ที่ |
|---|---|---|---|
| chunk ถูกอยู่ใน KB แต่ **rank ต่ำกว่า chunk ผิด** (0.352–0.460 vs 0.272–0.335) | 4 | bicep-curl partial ROM | **query** ใน `error_taxonomy.py` — gate แก้ rank order ไม่ได้ |
| **ไม่มี chunk ถูกเลย** — gate หยิบเพื่อนบ้านผิดมาแทน | 4 | lunge back-knee | **data** (KB v5) |
| finding ผิดอยู่ **ระยะเท่ากับหรือใกล้กว่า** finding ถูก (0.307 vs 0.343, 0.356 vs 0.329) | 3 | squat butt wink / knee valgus, push-up ROM | **prompt** — threshold แยกไม่ได้ |
| mistake ผิดหลุดเข้ามาเพราะ margin 0.20 กว้าง (0.424 vs best 0.258, 0.367 vs 0.304) | 3 | squat partial, lunge shallow, push-up ROM | **gate** — แก้ได้ |

ข้อสังเกตเพิ่ม:
- lunge shallow: finding ที่มีประโยชน์จริง ("2x hip width", "short step = joint force 2x") อยู่ที่ 0.412/0.421 **นอก** cap finding 0.40 ขณะที่ protocol noise ("Partial lunge was performed to 50 degrees" 0.306) เข้าได้ — cap เดียวทั้ง KB ไม่ transfer ข้ามท่า
- tag `applies_to_fault` ใน v4 เป็น **per-window** (ทุก item ใน window ได้ tag set เดียวกัน; ไม่มี window ไหนมี tag ต่างกันภายใน) → filter squat mistake ด้วย `knees behind toes` ได้ head position / heels rising / core ปนมา — ข้อเสนอ "tag fallback" ท้ายส่วน 6 **ใช้กับ v4 ไม่ได้** ต้องแก้ `curator.py` ให้ tag ต่อ item ก่อน re-ingest v5

### 7.1 Step 1(a) — เขียน query bicep-curl `partial range of motion` ใหม่ (2026-09-11)

เปลี่ยนใน `error_taxonomy.py` บรรทัดเดียว (ไม่แตะ gate / KB) — รายงานเต็ม `compare_output/golden_step1a_query_v4.md`

| query | mistake top-3 | finding kept |
|---|---|---|
| เดิม: "Partial range of motion: not fully extending or fully flexing the elbow (half rep) during the curl" | 0 good / 3 bad (upper arm stationary 0.272, elbow flare 0.313, drift 0.316) | incline bench 45-60° (0.370) 🔴 |
| ใหม่: "Failing to achieve complete arm extension at the bottom of the curl and full elbow flexion at the top: partial repetitions with a limited range of motion" | **3 good / 0 bad** (0.269 / 0.280 / 0.303; bad ตัวแรกตกไปอันดับ 4 ที่ 0.307) | 0 — incline bench ถอยไป 0.434 พ้น cap (ถูกต้อง: KB ไม่มี finding ของ fault นี้) |

| mode | hit | chunk | good | bad | precision | (baseline) |
|---|---|---|---|---|---|---|
| single | **9/10** | 40 | 24 | **10** | **0.60** | 8/10 · 14 · 0.51 |
| session | 5/6 | 23 | 14 | **6** | **0.61** | 5/6 · 9 · 0.50 |

อีก 9 fault ตัวเลขเท่าเดิมทุกตัว — ยืนยันว่า query ที่เขียนแบบ curator ("Failing to achieve … at the bottom … at the top") ชนะ label เชิงคลินิก แม้จะยาวกว่า และคำว่า "elbow" ตัวเดียวดึง fault ข้อศอกทุกตัวมาแทน

bad 10 ที่เหลือ: lunge back-knee 4 (data), finding ระยะเท่ากัน 3 (prompt), mistake หลุดเพราะ margin 3 (gate → step 1c)

### 7.2 Step 1(c) — gate v7 + principle ต่อ error (2026-09-11)

Sweep `RELATIVE_MARGIN` × `ABS_DISTANCE_CAP` บน golden set (single mode, mistake+finding เท่านั้น):

| margin | good | bad | สิ่งที่หายไปเทียบขั้นก่อน |
|---|---|---|---|
| 0.20 (v6) | 24 | 10 | — |
| 0.10 | 21 | 7 | good 3 ตัวที่หาย = paraphrase ของ chunk ที่เก็บอยู่แล้ว ("Tailbone tucking" 0.287 ข้าง "Lumbar flexion (butt wink)" 0.120) |
| 0.06 | 21 | 5 | หายเฉพาะ bad 2 + neutral 2 — good ไม่ลด |
| cap mistake 0.55 → 0.40 | เท่าเดิม | เท่าเดิม | cap ไม่มีผลเมื่อ margin ≤ 0.15 |
| cap finding 0.40 → 0.36 | −1 | −1 | เสีย finding ถูกตัวเดียวของ partial squat (0.370) |

ค่าที่เขียนลง `test_rag_compare.py`: `RELATIVE_MARGIN = 0.06`, `ABS_DISTANCE_CAP = 0.40 ทุก kind`, `MAX_PER_KIND["principle"] = 2`, และค้น `principle` ด้วย fault query ต่อ error (เดิมค้นเฉพาะ session ที่ไม่มี error)

**ผล** — รายงานเต็ม `compare_output/golden_step1c_gate_v4.md` (golden เพิ่ม pattern ฝั่ง principle แล้ว)

| mode | hit | chunk | good | bad | neutral | precision | (หลัง 1a) | (baseline v6) |
|---|---|---|---|---|---|---|---|---|
| single | 9/10 | 47 | 33 | **9** | 5 | **0.70** | 9/10 · 10 · 0.60 | 8/10 · 14 · 0.51 |
| session | 5/6 | 27 | 20 | **6** | 1 | **0.74** | 5/6 · 6 · 0.61 | 5/6 · 9 · 0.50 |

(ตัวเลข 1a/baseline ไม่รวม principle — ถ้าเทียบเฉพาะ mistake+finding: bad 14 → 10 → **5**, good 21 คงที่)

principle ต่อ error: 9/10 fault ได้ principle ถูก ≥ 1 ("Keep elbows tucked at the sides" 0.161, "Achieve full depth with the tops of the thighs at least parallel" 0.331, "Maintain a neutral pelvic tilt" 0.296) — ส่วน "วิธีแก้" มีของให้อ้างแล้ว; budget 3 → 2 เพราะตัวที่ 3 เป็นตัวที่ขัดกับวิธีแก้ทุกครั้ง

**bad 9 ที่เหลือ — gate แก้ไม่ได้สักตัว:**

| chunk | fault | ทำไม gate แก้ไม่ได้ | แก้ที่ |
|---|---|---|---|
| rear knee to flex (mistake), rotating back knee outward + forward vs backward knee angle (finding), do not let rear knee touch floor + backward lunges (principle) | lunge back-knee | เป็น best hit ทั้งหมด — KB ไม่มีของถูก | data (v5) ×5 |
| "Control squats were performed to 90 degrees" 0.356 | squat butt wink (finding) | ห่าง finding ถูก 0.027 | prompt |
| "knee displaced 0.17 m anteriorly" 0.307 | squat knee valgus (finding) | เป็น best hit; finding ถูกอยู่ 0.343 | prompt |
| "Forearm rotation influences elbow load" 0.351 | push-up ROM (principle) | ห่าง 0.024 | prompt |
| "Perform a partial lunge to 50 degrees" 0.310 | lunge shallow (principle) | เป็น best hit | prompt / data |

ข้อสังเกตเรื่องความเปราะ: margin 0.06 ตัด "rear knee to flex" ใต้ shallow lunge (0.367 vs 0.304) ด้วยระยะ 0.003 — ไม่ใช่เพราะ 0.06 เป็นเลขวิเศษ แต่เพราะ shallow lunge มี mistake ถูกใน KB ตัวเดียว เมื่อ v5 เติมข้อมูลตัวเลขนี้ต้อง sweep ใหม่ด้วยคำสั่งเดิม

### 7.3 Step 1(b) — prompt v7 + รัน LLM รอบแรกบน gate v7 (2026-09-11)

รายงาน: `compare_output/ab_v7.md` (RAG + no-RAG, 4 session, gemini-3.5-flash-lite @0.7) เทียบกับ `ab_taxonomy.md` (gate v6 + prompt เดิม)

เปลี่ยนใน `SYSTEM_PROMPT` 2 จุด: (1) เพิ่ม *Relevance rule* — `re:` คือ error ที่ entry ถูกดึงมาให้ ไม่ใช่การรับรอง; ให้เมิน entry ที่เป็น fault อื่น / variant อื่น / protocol detail / ทำตามแล้วยิ่งผิด (2) `you MUST cite` → cite เฉพาะ entry ที่ผ่าน relevance rule + ใช้ `principle` สำหรับขั้นตอนแก้

**ประโยคผิดที่ v6 พูด → v7:**

| ประโยคใน ab_taxonomy (v6) | ที่มา | v7 |
|---|---|---|
| Partial ROM เกิดจาก momentum / upper arm not stationary | chunk ผิดใต้ partial ROM | **หาย** — retrieval ไม่ส่งมาแล้ว (1a) |
| "Pro Tip: incline bench 45-60° ช่วย ROM" | finding ผิด 0.370 | **หาย** — พ้น cap หลัง query ใหม่ |
| back-knee: "rotating the back knee outward increases torque", "medial/lateral deviations" | chunk ผิดใต้ back-knee | **หาย** — prompt เมิน 3 ใน 5 bad chunk ที่ยังอยู่ใน context; ยังใช้ 2 ตัวแบบ hedge ("rear knee to flex improperly", "do not allow rear knee to contact the floor" → แปลงเป็น "stop just short of floor contact" ซึ่งเป็นคำแนะนำที่ไม่ผิด) |
| "Flexing at the spine before 1208 (120 degrees)" | OCR ใน chunk | **ยังอยู่** และแย่ลง: v7 เขียน "before 1208 of hip flexion" ไม่มี "(120 degrees)" — data |
| "Control squats were performed to 90 degrees" (อยู่ใน context ทั้งสองรอบ) | protocol noise | v6 ไม่ cite, v7 ไม่ cite |

**สิ่งที่ได้เพิ่ม:** ทุก "Step-by-Step Correction" ใน 3 session ที่มี error อ้าง `principle` จาก KB ("Maintain a neutral pelvic tilt…", "Achieve full depth with the tops of the thighs at least parallel…", "Keep elbows tucked at the sides…") — รอบ v6 ส่วนนี้เหมือน no-RAG ทุกท่า; ไม่มีตัวเลข/ชื่อแหล่งนอก context ในทั้ง 4 session

**เกณฑ์ผ่านที่ตั้งไว้** ("ไม่มีประโยคที่อ้าง chunk ผิด fault ในทั้ง 4 session"): ผ่าน 3/4 — lunge back-knee ยังพึ่ง chunk ผิด 2 ตัว แต่แบบ hedge ไม่ใช่ยืนยันเหมือน v6 → ปิดได้ด้วย data (v5) เท่านั้น

**data fix ขนาดเล็กที่ควรทำก่อน v5:** chunk ที่มี OCR องศาพัง 9 ตัวใน v4 (`1208`, `900 in text`, `90 8`, `/C176`) — 8 ใน 9 อยู่ใน finding ซึ่งเป็น kind ที่ prompt สั่งให้อ้างตัวเลข; แก้ที่ `curator.py` (normalize `\d+8` → `°`, ตัด "(noted as …)") แล้วค่อย re-ingest หรือ patch metadata ใน v4 โดยตรง

### 7.4 OCR degree fix บน v4 + curated_data (2026-09-12)

ทำแล้ว (ก่อน v5 ตามที่ตกลง — v4 คือไม้บรรทัดของทุก eval จนกว่า v5 จะมา):
- `data_pipeline/curator.py` — `normalize_ocr_degrees()` ใช้กับทุก item ที่ curator คืน (v5 จะไม่ผลิต "1208" ซ้ำ) — ทดสอบ `python data_pipeline/test_normalize_ocr_degrees.py` (10/10 รวม false-positive "denoted as SE-SE")
- `data_pipeline/fix_ocr_degrees.py` — one-off: แก้ `curated_data/**/*.json` (8 item) และ patch แถวจริงใน `kb_local_curated_v4` (8 แถว: text + metadata.text + **re-embed**) backup ที่ `data_pipeline/backups/`; รอบแรกไม่มีแถวไหนเป็น artefact จริงนอกจาก 8 ตัวนี้ ("denoted as SE-SE" ที่นับเป็นตัวที่ 9 ใน §7.3 ไม่ใช่ OCR)

**ยืนยัน:**
- `eval_retrieval.py` หลัง patch: single 9/10 · bad 9 · precision 0.70, session 5/6 · bad 6 · 0.74 — เท่า §7.2 ทุกช่อง (`compare_output/golden_step1b_ocrfix_v4.md`); distance ขยับตัวเดียวคือ push-up ROM finding 0.264 → 0.238 เพราะข้อความสั้นลงหลังตัด "(noted as 900 in text)"
- รัน squat session ใหม่ (RAG only): output cite "Flexing at the spine before **120 degrees** of hip flexion" — "1208" หายจาก LLM output (`compare_output/ab_v7_squat_ocrfix.md`)

**สรุป Step 1 ทั้งหมด (v6 → v7) เทียบ baseline:**

| | v6 baseline | v7 (1a+1b+1c+OCR) |
|---|---|---|
| single: hit / bad / precision | 8/10 / 14 / 0.51 | 9/10 / 9* / 0.70 |
| session: bad / precision | 9 / 0.50 | 6* / 0.74 |
| ประโยคผิดใน LLM output (4 session) | 4 (momentum, incline, back-knee rotation, 1208) | 0 ยืนยันผิด / 1 hedge (back-knee — data gap) |
| "วิธีแก้" grounded ด้วย principle | 0/3 session | 3/3 |

\* v7 รวม principle ที่ v6 ไม่มี — bad ที่เหลือ 9 ตัว: lunge back-knee 5 (data), finding/principle ที่ระยะเท่าตัวถูก 4 (prompt เมินได้แล้ว ดู §7.3)

**ค้างไป Step 2 (KB v5):** lunge back-knee (ไม่มี chunk ถูกเลย), finding ของ bicep-curl ทั้ง 2 fault (0), partial squat mistake ถูกตัวเดียว, shallow lunge finding ที่มีประโยชน์ 2 ตัวอยู่นอก cap 0.40 — และ curator ต้อง tag `applies_to_fault` ต่อ item ด้วย code ใหม่ 10 ตัว (v4 tag เป็น per-window ใช้ filter ไม่ได้)

---

## 8. สิ่งที่ตกหล่นจาก `docs/session_notes_2026-09-12.md` (ย้ายเข้ามารวมที่นี่ 2026-09-14)

session notes วันที่ 12 ก.ย. มีของที่ไม่เคยลงเอกสารนี้ 3 เรื่อง — นี่คือสาเหตุหลักที่เอกสารนี้ "ไม่ up to date" ก่อนจะแก้วันนี้

### 8.1 prompt v8 "practical" — รันแล้ว ยังไม่ผ่านเกณฑ์ ยังไม่ตัดสิน

`compare_output/prompt_v8_practical.md` และ `prompt_v8_practical_compare.md` (12 ก.ย. 00:52/01:02) เพิ่ม *Relevance rule* ชัดเจนขึ้นกว่า v7 (ให้เมิน entry ที่เป็น "a study protocol or setup detail with no consequence attached" หรือ "would push the user further into the error") และปรับโทนเป็น "โค้ชในยิม" มากขึ้น (bullet คำแนะนำ 4 หัวข้อ: what/why/how to fix/rep detail)

รันแล้ว 1 รอบ (RAG + no-RAG, 4 session, บน `kb_local_curated_v4`, gate v7 เดิม) แต่**ยังไม่ได้ตั้งเกณฑ์ผ่าน/ไม่ผ่านหรือเทียบกับ v7 อย่างเป็นระบบ** — ต่างจาก v6→v7 ที่มีตาราง before/after ชัดเจน (§7.3) รอบนี้มีแค่ raw output ให้อ่านเอง ยังสรุปเป็นตัวเลขไม่ได้เพราะ temperature 0.7 ทำให้แต่ละรอบไม่เหมือนกัน (ประเด็นเดียวกับที่ §4④ ของ session notes บอกไว้)

**สถานะ:** prompt v8 ยังไม่ใช่ของที่ยืนยันว่าดีกว่า v7 — แค่ "รันดูแล้ว ยังไม่ตัดสิน" ใครหยิบงานต่อควรรันผ่าน `eval/eval_retrieval.py` เทียบก่อน (retrieval ไม่เปลี่ยนจาก v7 เพราะ v8 แก้แค่ prompt) แล้วโหวต/ให้คนอ่าน output จริงตัดสิน ไม่ใช่เดาจากรอบเดียว

### 8.2 คำถามที่ยังไม่ปิด: query ↔ ชื่อกฎจริงตรงความหมายกันไหม

`error_taxonomy.py` เขียน `query` โดยตีความจากชื่อ fault ของทีมระบบ (`rule_th` / ชื่ออังกฤษ) เอง **ยังไม่มีใครนอกทีมนี้ยืนยัน** ว่าตีความถูก จุดที่น่ากังวลที่สุด:

- **squat `knee valgus`**: `rule_th` = "เข่าไม่เลยปลายเท้า" (เข่าเลื่อนไปข้างหน้าเกินปลายเท้า — ระนาบ sagittal) แต่ `query` ปัจจุบันเขียนว่า "knees caving inward" (เข่าบิดเข้าด้านใน — ระนาบ frontal) **คนละอาการกันโดยสิ้นเชิง** ถ้ากฎจริงวัดระยะเข่า-ปลายเท้า การค้นทั้งหมดของ fault นี้จะดึง chunk ผิดอาการมาตลอด แม้ eval golden-set จะให้คะแนนสวยก็ตาม (เพราะ golden set เองก็ตัดสินจาก query นี้ — เป็นเหตุเป็นผลวนในตัว ดู §8 ของ session notes)
- squat `butt wink`: `display_th` เขียนว่า "หลังค่อม / หลังแอ่น" (สองทิศ) แต่ butt wink ทางเทคนิคคือ flexion ทิศเดียว — ถ้ากฎจริงจับทั้งสองทิศ query ตอนนี้ครอบคลุมแค่ครึ่งเดียว
- ตัวเลขในบาง query (เช่น "90 degrees") เป็นตัวเลขที่**เราใส่เอง** ไม่ใช่ threshold จริงจาก `form_rules.py`

**ทำไมยังไม่แก้ตอนนี้:** ต้องอ่าน `form_rules.py` ของทีมระบบตรวจท่าโดยตรง (ยังไม่ได้รับไฟล์) หรือให้ PT ยืนยันทีละกฎ — ไม่ใช่สิ่งที่แก้ได้จากฝั่งนี้อย่างเดียว ใครต่องานควรถือเป็น **ความเสี่ยงเปิดอยู่ระดับสูง** ไม่ใช่รายละเอียดเล็กน้อย เพราะถ้าตีความผิด ระบบจะดึงของที่ "แม่นแต่ผิดอาการ" ไปตลอด

### 8.3 query ไม่ได้ลอก KB ตรง ๆ — เป็นการ "จูน" เข้าหา KB

วัด Jaccard ของ query กับประโยค mistake ที่ใกล้สุดใน KB: อยู่ระหว่าง 0.25–0.71 (ไม่มีคู่ไหน exact match) รูปแบบคือเขียนชื่ออาการ + รวมหลายสำนวนของ KB ไว้ในประโยคเดียว ("flare outward **or** drift away") เพื่อให้ตกกลางระหว่างสำนวนที่ต่างกัน — **นัยยะ:** เพราะ query ถูกจูนให้เข้ากับ KB ที่มีอยู่ ถ้าตีความ error_type ผิดตั้งแต่ต้น (กรณี knee valgus ข้อ 8.2) การจูนจะยิ่งพาไปหา chunk ผิดอาการได้แม่นยำขึ้นเท่านั้น ไม่ใช่ตัวช่วยตรวจจับความผิดพลาด

---

## 9. ตรวจแหล่งข้อมูลซ้ำ — มีของนอกเรื่อง/ไม่น่าเชื่อถือเหลืออยู่ไหม (2026-09-14)

`data/` ผ่านการตัดของนอกเรื่องรอบ v3→v4 แล้ว (§4 ลำดับ 4) — ไฟล์ epidemiology/biochemistry/haemophilia 4 ไฟล์เดิมไม่อยู่ใน `data/` แล้ว ย้ายไป `excluded_from_kb/` จริง ตรวจซ้ำรอบนี้ (`data/*/urls.txt` + `curated_data/*/*.json`) พบว่า**ยังมีแหล่งอ่อนที่ผ่านเข้ามาใน KB จริง** ตามที่ §9 ของ session notes เคยเตือนไว้แล้วแต่ไม่เคยนับจำนวนจริง:

| แหล่ง | สถานะใน KB | จำนวน | ปัญหา |
|---|---|---|---|
| `grokipedia.com/page/Bicep_curl` | **อยู่จริง** | 7 windows / 84 items (bicep-curl) | วิกิสร้างด้วย AI ไม่ผ่าน peer review, ไม่มีผู้เขียนที่ระบุตัวตนได้ — เป็นแหล่งเดียวที่ครอง mistake/principle ของ elbow flare และ partial ROM ส่วนใหญ่ (ดู §3.3) ถอดตอนนี้ = เปิดช่องว่างกลับไปที่ 0 chunk ทันที เพราะยังไม่มีของทดแทน |
| `themerisoiutechnique.com` (lunge) | **อยู่จริง** | 1 window / 15 items | บล็อกส่วนบุคคล ไม่มีอาจารย์/องค์กรรับรอง ตรวจสอบผู้เขียนไม่ได้ |
| `www.healthline.com` | **อยู่จริง** | 3 windows / 34 items (squat, lunge) | สื่อสุขภาพผู้บริโภคทั่วไป มีกอง บ.ก. ตรวจ แต่ไม่ใช่งานวิจัยปฐมภูมิ — ใช้เป็นเสริมได้ ไม่ควรเป็นแหล่งหลัก |
| `www.scribd.com/document/...` (squat, "Lab 05 Squat and Lunge Manual") | ไม่อยู่ใน KB | 0 | ดึงเนื้อหาไม่สำเร็จตอน curate (ไม่มี record แม้ใน `excluded_from_kb/`) — ลิงก์ตายอยู่เฉย ๆ ใน `urls.txt`, ไม่ปนเปื้อน KB ตอนนี้แต่ควรลบทิ้งเพราะรันซ้ำเมื่อไรก็มีโอกาสหลุดเข้ามา ไม่มีใครรับรองผู้เขียนอยู่ดี |
| `www.self.com` (squat, push-up) | ไม่อยู่ใน KB | 0 | เหมือน scribd — ดึงไม่สำเร็จ, ลิงก์ตายอยู่ใน `urls.txt` |
| `www.nasm.org`, `www.acefitness.org` | อยู่จริง | 15 + 1 windows | องค์กรรับรองผู้ฝึกสอนที่ได้รับการยอมรับในอุตสาหกรรม — ไม่ใช่ peer-reviewed แต่เชื่อถือได้ในระดับ practitioner guidance ไม่มีปัญหา |

**สรุป:** ไม่มีของ "นอกเรื่องแบบเดิม" (cardiovascular/biochemistry) หลงเหลือแล้ว แต่มีแหล่งที่**อ่อนด้านความน่าเชื่อถือ** 2 ระดับ — grokipedia/themerisoiutechnique (ไม่มีผู้เขียนที่ตรวจสอบได้) กับ healthline (สื่อผู้บริโภค ไม่ใช่วิชาการ) และมี 2 ลิงก์ตาย (scribd, self.com) ที่ควรลบออกจาก `urls.txt` เพราะไม่มีประโยชน์และเป็นความเสี่ยงเงียบ ๆ

**ไม่แนะนำให้ถอด grokipedia/themerisoiutechnique ตอนนี้โดยไม่มีของแทน** — ตามที่ §3.3 เคยเตือนไว้ ถอดแล้ว bicep-curl elbow flare/partial ROM และ lunge back-knee (ดู §8.1 ของช่วง v4→v5 ที่ยังค้าง) จะกลับไปมี 0 chunk ทันที การตัดสินใจถอด/แทนที่จึงควรผูกกับ "หา PDF/แหล่งวิชาการทดแทนได้แล้ว" ไม่ใช่ทำตามลำพัง — นี่คือคำตอบของคำถาม "ยังมีไฟล์ที่ดูไม่เกี่ยวข้องหรือมาจากแหล่งที่ไม่น่าเชื่อถืออยู่อีกไหม": **มี 2 แหล่งอ่อนที่ยังใช้งานอยู่จริง (grokipedia, themerisoiutechnique) และ 2 ลิงก์ตายที่เก็บไว้เฉย ๆ (scribd, self.com) — ไม่มีของ "นอกเรื่อง" แบบเดิมอีกแล้ว**

### 9.1 ถอดจริงตามคำขอ user (2026-09-14) — scribd, self.com, grokipedia

User สั่งลบทั้ง 3 แหล่งหลังอ่านคำเตือนข้างต้นแล้ว (รวม grokipedia ทั้งที่ยังใช้งานอยู่จริง) ทำดังนี้:

1. **`data/squat/urls.txt`**: ลบบรรทัด scribd + self.com (ไม่มีผลกับ DB เพราะทั้งคู่ดึงเนื้อหาไม่สำเร็จตั้งแต่ต้น มี 0 chunk อยู่แล้ว)
2. **`data/bicep-curl/urls.txt`**: ลบบรรทัด grokipedia
3. **`curated_data/bicep-curl/urls_curated_detailed.json`**: ลบ 7/10 windows ที่ `source` มี "grokipedia" (backup ก่อนลบที่ `data_pipeline/backups/urls_curated_detailed_bicep-curl_pre_grokipedia_removal_20260914-231031.json`)
4. **DB ทั้งคู่** (`kb_local_curated_v4` และ `kb_gemini_curated_v4`): ลบแถวที่ `cmetadata->>'source' LIKE '%grokipedia%'` — 84 แถวต่อ collection, backup ก่อนลบที่ `data_pipeline/backups/{collection}_grokipedia_rows_pre_delete_20260914-231054.json` รวม chunk คงเหลือ **2,432 → 2,348** ทั้งสอง collection

**ผลกระทบจริงที่วัดได้** (`eval/eval_retrieval.py --collection kb_gemini_curated_v4 --margin 0.03`, เทียบ §10.5):

| fault | ก่อนลบ | หลังลบ |
|---|---|---|
| bicep-curl elbow flare — mistake | best 0.037, kept 3 (good 3) | best 0.043, kept 1 (good 1) — **รอดแต่บางลง**, แหล่งที่เหลือคือ `A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve` + rhabdomyolysis case report |
| bicep-curl elbow flare — **principle** | good 2 (`Keep elbows tucked at the sides` มาจาก grokipedia) | **good 0/3** — ไม่มี principle เหลือให้ระบบอ้างวิธีแก้ elbow flare อีกต่อไป ⚠️ **ช่องว่างใหม่** |
| bicep-curl partial ROM — mistake | good 3 | good 2 — ยังพอใช้ (`Scandinavian Med Sci Sports 2014 Brandner`, `A_Biomechanical_Analysis...`) |
| single summary ทั้งกระดาน | hit 8/10, bad 2 | hit 8/10, bad **1** | 

**สรุป:** ตัดสินผิดที่กลัวไว้บางส่วน — mistake/finding coverage ของ elbow flare และ partial ROM ไม่ได้หายไปหมด (มี PDF อื่นรองรับอยู่) แต่ **principle (ขั้นตอนแก้ไข) ของ elbow flare หายไปเป็น 0 จริงตามที่เตือน** — เพิ่มเป็นรายการค้างใน §10.6 ข้อ 6: ต้องหา principle ทดแทนสำหรับ bicep-curl elbow flare ก่อน grokipedia เป็นแหล่งเดียวที่เคยให้คำแนะนำวิธีแก้ (`Keep elbows tucked at the sides`) ตอนนี้ไม่มีอะไรมาแทนใน context เลย ระบบจะ fallback ไปใช้คำแนะนำทั่วไปแบบไม่มี citation

---

## 10. ย้าย embedding MiniLM → Gemini (2026-09-14) → `kb_gemini_curated_v4`

**เหตุผล:** ใช้ Gemini paid tier แล้ว ไม่มีเหตุผลต้องพึ่ง `all-MiniLM-L6-v2` (local, ฟรี, 384 มิติ) ต่อ — ย้ายทั้ง pipeline ไป `gemini-embedding-2` เป็นค่า default

### 10.1 โครงสร้างที่เปลี่ยน

เพิ่ม `embedding_config.py` เป็นจุดสลับเดียวของทั้งระบบ (`DEFAULT_MODE`, `get_embeddings()`, `get_connection()`, `default_collection()`) แทนที่การสร้าง `HuggingFaceEmbeddings`/`GoogleGenerativeAIEmbeddings` ซ้ำ ๆ ใน `ingest.py`, `kb_coverage.py`, `eval/eval_retrieval.py`, `test_rag_compare.py` — ตั้งค่าเดียวที่ไฟล์นี้ (`DEFAULT_MODE = "gemini"`, override ชั่วคราวด้วย `EMBEDDING_MODE=local`) มีผลกับทุกสคริปต์พร้อมกัน `kb_local_curated_v4` (MiniLM) ยังอยู่ครบใน `vectordb_local` ไม่ได้ลบ ใช้เป็น fallback/baseline เทียบผลได้เสมอ

`ingest.py` มี bug จุดหนึ่งที่เจอระหว่างรันจริง: batch ที่ส่งให้ Gemini embed คงไว้ที่ 30 + sleep 60 วินาทีทุก batch แบบ free-tier เดิม (คอมเมนต์เดิมเขียนว่า "respect Gemini Free Tier API rate limits" แบบ hardcode ไม่เช็ค tier จริง) ทำให้ 2,432 chunks ต้องใช้เวลา ≥80 นาทีเปล่า ๆ — แก้เป็น batch 100 ไม่ sleep เป็นค่า default, ใส่ flag `--free-tier` ไว้สำหรับคนที่ยังใช้ free tier จริง ๆ ผลคือรันจริงเจอ `429 RESOURCE_EXHAUSTED` ที่ batch 14/24 (paid tier ก็มี quota ต่อนาทีเหมือนกัน แค่สูงกว่า free tier มาก) เพิ่ม retry-with-backoff (20s × attempt, สูงสุด 4 ครั้ง) แทนการ abort ทั้งรัน แล้ว resume ต่อได้เพราะ `ingest.py` มี dedup ด้วย content-hash ID อยู่แล้ว — ไม่ต้อง re-embed ของที่ทำสำเร็จไปแล้ว

### 10.2 ผลการ ingest

`python ingest.py --mode gemini --collection kb_gemini_curated_v4` → **2,432 chunks, 241 sources** เท่ากับ `kb_local_curated_v4` เป๊ะ (ข้อมูลต้นทางไม่เปลี่ยน แค่เปลี่ยน embedding) ยืนยันด้วย `kb_coverage.py`:

| exercise | kb_gemini_curated_v4 (principle / mistake / finding) |
|---|---|
| squat | 1064 (473 / 250 / 341) |
| lunge | 621 (297 / 82 / 242) |
| push-up | 304 (145 / 42 / 117) |
| bicep-curl | 443 (192 / 52 / 199) |

### 10.3 สเกล distance เปลี่ยนไปทั้งกระดาน — cap 0.40 ใช้ไม่ได้ผลอีกต่อไป

รัน `kb_coverage.py --collection kb_gemini_curated_v4` (ไม่มี gate ใด ๆ นอกจาก cap ≤0.40, pool 40): **แทบทุก fault ได้ 40/40 "usable" ทั้ง raw และ expanded query** — best distance อยู่ในช่วง 0.02–0.4 ทั้งกระดาน เทียบกับ MiniLM ที่กระจายกว้างกว่ามาก (0.057–0.601 ในตัวอย่าง §5 ของ session notes) `gemini-embedding-2` ดันทุกอย่างในคลังเดียวกันให้อยู่ใกล้กันมากกว่า MiniLM มาก — ผลคือ `ABS_DISTANCE_CAP = 0.40` ที่เคยเป็นตัวกรองสำรอง **ไม่ discriminate อะไรเลย** ภายใต้ Gemini (เกือบทุกอย่างผ่าน) เหลือแค่ `RELATIVE_MARGIN` ที่เป็นตัวกรองจริงตัวเดียว — สอดคล้องกับที่ §7.2 เคยพบใน MiniLM ว่า cap หมดความหมายเมื่อ margin แคบพอ แต่ครั้งนี้ cap หมดความหมาย**ตั้งแต่ต้น** ไม่ใช่เพราะ margin แคบ

ข้อดีที่มาพร้อมกัน: expanded query ดีกว่า raw อย่างชัดเจนเหมือน MiniLM (เช่น bicep-curl elbow flare raw 0.401 เกือบพ้น cap vs expanded 0.037) — แปลว่าเหตุผลที่ต้องมี `error_taxonomy.py` (§8.2/§8.3) ยังคงอยู่เหมือนเดิม ไม่ใช่ปัญหาเฉพาะ MiniLM

### 10.4 Sweep `RELATIVE_MARGIN` ใหม่บน golden set (single mode)

| margin | kept | good | bad | neutral | precision |
|---|---|---|---|---|---|
| 0.10 / 0.08 | 70 | 26 | 6 | 38 | 0.37 |
| 0.06 (ค่าเดิมที่รับมาจาก MiniLM v7) | 68 | 25 | 6 | 37 | 0.37 |
| 0.05 | 68 | 25 | 6 | 37 | 0.37 |
| 0.04 | 65 | 24 | 4 | 37 | 0.37 |
| **0.03 (เลือก)** | **62** | **23** | **2** | **37** | **0.37** |
| 0.015 | 53 | 20 | 2 | 31 | 0.38 |
| 0.01 | 51 | 19 | 1 | 31 | 0.37 |

อ่านเป็น elbow: 0.06→0.03 ตัด bad ครึ่งหนึ่ง (6→2) เสีย good แค่ 2 ตัว (25→23) ตัดต่อจาก 0.03→0.015 bad **ไม่ลดอีกแล้ว** (2→2) แต่เสีย good ไปอีก 3 (23→20) — แปลว่า 0.03 คือจุดที่ margin แคบกว่านี้ไม่ได้ช่วยอะไร มีแต่เสียของ **ตั้งค่าใหม่: `RELATIVE_MARGIN = 0.03`** ใน `test_rag_compare.py` (ค่า MiniLM เดิม 0.06 ยังถูกอยู่สำหรับ `kb_local_curated_v4` — คนละสเกล เทียบกันไม่ได้ตรง ๆ)

### 10.5 ผลลัพธ์เทียบ MiniLM v7 baseline

| mode | KB | hit | kept | good | bad | neutral | precision |
|---|---|---|---|---|---|---|---|
| single | MiniLM v7 (kb_local_curated_v4) | 9/10 | 47 | 33 | 9 | 5 | 0.70 |
| single | **Gemini (kb_gemini_curated_v4, margin 0.03)** | 8/10 | 62 | 23 | **2** | 37 | 0.37 |
| session | MiniLM v7 | 5/6 | 27 | 20 | 6 | 1 | 0.74 |
| session | **Gemini** | 4/6 | 38 | 12 | **5** | 21 | 0.32 |

รายงานเต็ม: `compare_output/golden_gemini_v1_margin03.md`

**อ่านผลตรง ๆ — precision ตัวเลขดูแย่ลงแต่ bad (ตัวเลขที่สำคัญกว่าเพราะคือความเสี่ยง hallucination) ดีขึ้นมาก:** bad หายไปเกือบหมด (single 9→2, -78%) แต่ precision หล่นจาก 0.70 เหลือ 0.37 เพราะ **neutral พุ่งขึ้นมาก** (single 5→37) ไม่ใช่เพราะ bad เพิ่ม — Gemini คืน chunk ที่ "ไม่ผิดฟอร์ม แต่ก็ไม่ตรงกับ pattern ที่ golden set ตั้งไว้" มากกว่า MiniLM มาก โดยเฉพาะช่อง finding/principle ที่หลายอันมี kept=2, good=0, neutral=2 ทั้งคู่ (ดูตัวอย่างดิบใน §10.3 ผลรัน eval baseline) นี่อาจเป็นเพราะ (ก) golden set (`eval/golden_chunks.json`) เขียน substring pattern ไว้ตาม chunk ที่ MiniLM เคยดึงมา ยังไม่ได้เพิ่ม pattern ให้ครอบคลุม paraphrase ที่ Gemini ดึงมาแทน หรือ (ข) Gemini เลือก chunk ที่ต่างจาก MiniLM จริง ๆ แม้จะไม่ผิด — **ยังตัดสินไม่ได้จากตัวเลขอย่างเดียว ต้องเปิด `--show-kept` อ่านเนื้อหาจริงของ neutral ก่อนสรุป**

**session hit ตก 5/6 → 4/6** — เกิดจากอะไรยังไม่ได้ตรวจ (lunge back-knee ที่เป็น known gap เดิมน่าจะเป็นตัวหนึ่ง แต่ไม่ควรเดา) **ค้างเป็นข้อต่อไป**

### 10.6 สิ่งที่ยังไม่ได้ทำ / ค้างต่อจากรอบนี้

1. **อ่าน `--show-kept` ของ neutral ทั้งหมด** ตัดสินว่า golden set ต้องเพิ่ม pattern (Gemini ดึง chunk ถูกแต่ pattern เก่าจับไม่ได้) หรือ Gemini ดึงของที่ด้อยกว่าจริง (§10.5)
2. **ตรวจว่าทำไม session hit ตกจาก 5/6 เหลือ 4/6** — fault ไหนหายไป และเป็นปัญหา data เดิม (lunge back-knee) หรือปัญหาใหม่จาก Gemini
3. **CANDIDATE_K / MAX_PER_KIND / NEAR_DUP_JACCARD ยังไม่ได้ re-sweep** ภายใต้ Gemini — สืบทอดค่าจาก MiniLM v7 มาเฉยๆ (ดูคอมเมนต์ใน `test_rag_compare.py`) ไม่รู้ว่ายังเหมาะสมไหมเมื่อ distance scale เปลี่ยนไปทั้งกระดาน
4. **ยังไม่ได้ตัด `kb_local_curated_v4`** — เก็บไว้เป็น fallback ตามที่ตกลงไว้ตอนเริ่มงานนี้ ถ้า Gemini พิสูจน์ตัวเองผ่านข้อ 1–2 แล้วค่อยพิจารณาเลิกดูแลคู่ขนาน
5. **ทุกอย่างใน §8 (query↔rule semantic gap, โดยเฉพาะ knee valgus) ยังไม่แก้** — ย้าย embedding ไม่กระทบปัญหานี้เลย เพราะเป็นปัญหาที่ตัว query ไม่ใช่ตัว embedding

---

## 11. Ingest `curated_data_v5` → `kb_gemini_curated_v5` เป็น default (2026-09-18)

**Ingest:** `curated_data_v5` (43 ไฟล์ / 239 window / 1,955 chunk) → collection ใหม่ `kb_gemini_curated_v5` (Gemini embedding, DB แยกจาก v4 สนิท) สำเร็จ 100% ไม่มี error — `kb_gemini_curated_v4` ไม่ถูกแตะเลยตลอดงานนี้

### 11.1 golden set (`eval/golden_chunks.json`) ล้าสมัย — วัดรอบแรกหลอก

รอบแรกที่รัน `eval/eval_retrieval.py --collection kb_gemini_curated_v5` ได้ **4/10 · precision 0.12** (แย่กว่า v4 8/10 · 0.33) แต่ตัวเลขนี้หลอก: `must_hit` เป็น substring คำต่อคำจาก **v4 wording เท่านั้น** — v5 พูดอาการถูกแต่คนละสำนวน (เช่น "knees to cave inward" แทน "knee valgus (knees caving inward)") เลยโดนนับเป็น neutral ผิด ๆ ทั้งที่ตอบถูก

**แก้:** เพิ่ม phrasing ใหม่จาก v5 เข้า `must_hit` ทุก fault (ไม่ลบของ v4 — ไฟล์รองรับทั้งสองเวอร์ชันพร้อมกัน) + แก้ `must_not_hit` ที่มี "preacher curls" (พหูพจน์) แต่ v5 เขียน "preacher curl" (เอกพจน์) เลยหลุดผ่าน gate ทั้งที่ควรโดน flag — ใช้ pattern เอกพจน์เจาะจงกว่าเดิมแทน (pattern เดิมกว้างเกินไปจนแฟลก chunk ที่ถูกด้วย)

รอบแรกหลังแก้ golden set: v5 = **10/10 · precision 0.60** แต่ bad เพิ่มจาก 1 → 5 ตัว กระจุกที่ bicep-curl ล้วน

### 11.2 root cause ของ bad chunk ใหม่ — `curator.py` แท็ก fault ผิดให้ statement ของ variant อื่น

สาเหตุ: `curate_knowledge()` แท็ก `applies_to_fault` ให้ statement ที่ (1) บอกว่า partial ROM ให้ผลเท่า full ROM (งานวิจัย hypertrophy ของ preacher/incline/Bayesian curl ที่สรุปว่า "similar increase") หรือ (2) เจาะจงกลไก/มุมของ variant เฉพาะ (preacher/incline curl) ที่ไม่ generalize มาที่ bicep curl มาตรฐาน — โมเดลหยิบไปอ้างว่าทำผิดแล้วโอเคได้

**แก้ 2 ชั้น:**
1. เพิ่ม 2 กฎนี้เข้า prompt + schema description ของ `data_pipeline/curator.py` ป้องกันไม่ให้เกิดซ้ำตอน re-curate รอบหน้า
2. Patch ข้อมูลเดิมใน `curated_data_v5/bicep-curl/*.json` ตรง ๆ — ลบ `applies_to_fault` ผิดออกจาก 19 item (6 จาก manual read + 13 จาก systematic sweep คำว่า preacher/incline/cable/concentration/bayesian curl) → sync DB (ลบแถวเก่า + ingest ใหม่ ให้ hash ใหม่เข้ามาแทน เพราะ `ingest.py` ไม่ลบแถวเก่าที่ metadata เปลี่ยนให้เอง)

ผล: bad 5 → 1

### 11.3 ถอดเปเปอร์ preacher/incline curl ทิ้งทั้งไฟล์

ไฟล์ "Distinct muscle growth...preacher and incline biceps curls" ไม่มี GOOD chunk แม้แต่ตัวเดียวมาจากไฟล์นี้เลย — ย้ายทั้งไฟล์ไป `excluded_from_kb/bicep-curl/` (มี marker กันไม่ให้ re-curate ซ้ำ) แล้วลบ 58 chunk ที่มาจากไฟล์นี้ออกจาก DB (เจอบั๊ก Postgres ระหว่างทาง: `LIKE` ตีความ backslash ใน path เป็น escape character ทำให้ pattern พัง — แก้ด้วยการเทียบ prefix ตรง ๆ แทน)

ผล: precision 0.60 → 0.62, bad ยังเหลือ 1 แต่คนละ chunk — ยืนยันว่าตัวสุดท้ายเป็นปัญหาคนละสาเหตุ ไม่ใช่เรื่อง preacher curl ปนแล้ว

### 11.4 ตัวเลขสุดท้าย (single mode)

| KB | hit | precision | bad |
|---|---|---|---|
| v4 (baseline, `kb_gemini_curated_v4`) | 8/10 | 0.33 | 1 |
| **v5 (`kb_gemini_curated_v5`, ตอนนี้เป็น default)** | **10/10** | **0.62** | **1** |

**bad ที่เหลือ (bicep-curl elbow-flare, kind = finding):** KB ไม่มี "finding" จริงของ elbow-flare อยู่เลยสักตัว — เป็น data gap ที่มีมาตั้งแต่ v4 ไม่ใช่บั๊ก tag รอ source ใหม่ก่อนจะปิดได้ (ดู [[retrieval-golden-eval]])

**ขอบเขตที่จงใจไม่แตะ:** ในไฟล์ "The interplay between muscle length, ROM..." ยังมี item อีก ~15 ตัวที่พูดเรื่อง hypertrophy/fascicle length/sarcomerogenesis ทั่วไป (ไม่เอ่ยชื่อ variant, ไม่ contradict ตรง ๆ) ที่ยังแท็ก "partial range of motion" อยู่ — ไม่กวาดเพราะไม่มีหลักฐานจาก eval ว่ามันโผล่เป็น bad จริง และ "ทั้งเปเปอร์นี้เหมาะกับ KB นี้ไหม" เป็นคำถามระดับ source-selection ที่ควรถามเจ้าของงานก่อน

### 11.5 ไฟล์ที่เปลี่ยนจริง

- `eval/golden_chunks.json` — เพิ่ม must_hit v5 phrasing, แก้ must_not_hit
- `data_pipeline/curator.py` — เพิ่ม 2 กฎแท็กใหม่ในพรอมต์ + schema
- `curated_data_v5/bicep-curl/*.json` — แก้ tag 19 item, ลบ 1 ไฟล์ทั้งไฟล์
- `excluded_from_kb/bicep-curl/` — เพิ่ม offtopic marker 1 ไฟล์
- DB `kb_gemini_curated_v5` — sync ตามการแก้ทั้งหมด
- `embedding_config.py` — `COLLECTION_NAMES["gemini"]` เปลี่ยนจาก `kb_gemini_curated_v4` → `kb_gemini_curated_v5` (default collection ของทั้งระบบ)

### 11.6 ค้างไว้

1. bad chunk สุดท้าย 1 ตัว (bicep-curl elbow-flare finding) — data gap, รอ source ใหม่
2. `CANDIDATE_K` / `MAX_PER_KIND` / `ABS_DISTANCE_CAP` / `RELATIVE_MARGIN` ใน `test_rag_compare.py` ยังเป็นค่าที่ sweep ไว้กับ `kb_gemini_curated_v4` (§10.4) ไม่ได้ re-sweep กับ v5 อย่างเป็นทางการ — ตัวเลข §11.4 ยืนยันว่าค่าเดิมยังใช้ได้ดีกับ v5 (10/10 · 0.62 · bad 1 ดีกว่า v4 ทุกด้าน) แต่ยังไม่ผ่าน sweep แบบ §10.4 โดยตรง
3. `kb_gemini_curated_v4` / `kb_local_curated_v4` ยังไม่ถูกลบ — เก็บไว้เป็น fallback/comparison ตามเดิม

---

## 12. Generation-side metric เข้า `eval/` (2026-09-22)

ก่อนหน้านี้ฝั่ง retrieval วัดซ้ำได้ด้วยคำสั่งเดียว (`eval/eval_retrieval.py`) แต่ฝั่ง generation วัดด้วยสคริปต์ชั่วคราวใน scratchpad — เถียงกันด้วยตัวเลขเดิมซ้ำไม่ได้ ย้ายเข้ามาเป็น `eval/eval_generation.py` + `eval/jargon_terms.json` + `eval/test_eval_generation.py`

```
python eval/eval_generation.py compare_output/compare_result_v10.md
python eval/eval_generation.py compare_output/compare_result_v{9,10}.md --show-hits --out compare_output/generation_v9_vs_v10.md
python eval/test_eval_generation.py
```

วัดจากรายงานที่มีอยู่แล้ว ไม่เรียก LLM ซ้ำ (deterministic 100%) สองตัวเลข:

1. **unglossed jargon** — ศัพท์คลินิก/ชีวกลศาสตร์ที่ไม่มีคำแปลภาษาชาวบ้านในประโยคเดียวกัน = วัด *Translation rule*
2. **longest shared word n-gram** ระหว่าง `### Retrieved KB Context` กับคำตอบของท่าเดียวกัน = วัด *Grounding rule part 2* (ลอกประโยค) เสริมด้วย `spans ≥6` = จำนวนช่วงที่ลอกทั้งหมด ไม่ใช่แค่ช่วงยาวสุด

**ฝั่ง WITHOUT RAG ถูกให้คะแนนด้วยโดยตั้งใจ** — ไม่เคยเห็น context เลย ตัวเลข n-gram ของมันจึงเป็น *chance floor* ของรายงานนั้น (ความยาวที่ข้อความสองชิ้นเรื่องสควอทบังเอิญตรงกัน) ค่า RAG ที่ใกล้ floor = ไม่ลอก ค่าที่สูงกว่า floor มาก = ลอก

### 12.1 Baseline v9 vs v10 (รายงานเต็ม `compare_output/generation_v9_vs_v10.md`)

| report | side | unglossed jargon | longest n-gram | spans ≥6 |
|---|---|---|---|---|
| v9 | WITH RAG | **17** | **20** | 13 |
| v9 | WITHOUT RAG | 3 | 6 (floor) | 1 |
| **v10** | **WITH RAG** | **1** | **9** | 3 |
| v10 | WITHOUT RAG | 0 | 6 (floor) | 1 |

ยืนยันการวินิจฉัยเดิมของ prompt v10 ด้วยตัวเลขที่รันซ้ำได้: v9 ฝั่ง RAG ลอกประโยคจาก context ยาว 20 คำ ("descend until the top of the thigh is at least parallel with…", "allowing the spine to flex during a squat compromises back curvature…") — ไม่ใช่แค่ "เลือกใช้ศัพท์ยาก" · v10 เหลือ 9 คำ คือ "2 to 3 cm short of contacting the ground" ซึ่งเป็น**ตัวเลขเป้าหมาย** ที่ Grounding rule part 1 สั่งให้คงไว้เป๊ะ ๆ — ยอมรับได้ · unglossed ที่เหลือ 1 ตัวคือ "center of mass" ในคำตอบ lunge

**หมายเหตุ:** สคริปต์นี้นับ v9 ได้ 17 ขณะที่ตัวเลขที่จดไว้ตอนรันมือคือ 18 — ต่างกันที่ขอบเขต term list ไม่ใช่ที่ parser (n-gram ตรงกันเป๊ะทั้ง 20 และ 9) เวลาอ้างตัวเลขให้บอกด้วยว่ามาจาก `eval/jargon_terms.json` เวอร์ชันไหน เหมือนที่คะแนน golden set ต้องบอกชื่อ collection

### 12.2 กับดักที่ test คุมไว้

- **parser** — ตัว feedback มีหัวข้อ `### ` ของตัวเอง (Progress Tracking / Error Breakdown / Next Session Plan) และมีเส้น `---` / `***` อยู่ข้างใน ตัด section ด้วยสองอย่างนี้จะเหลือแค่ย่อหน้าแรกแล้วนับได้ราวครึ่งเดียว (เคยนับ v9 ได้ 10 แทน 18) → ตัดที่ `## Exercise:` และหัวข้อ 4 ตัวที่รู้จักเท่านั้น
- **allowed term บังศัพท์ยาก** — "hip" อยู่ใน allowed_bare ถ้า match allowed ก่อนแล้วกินช่วงตัวอักษรไป "hip extensors" จะหายทั้งวลี (เจอจริงตอนรันรอบแรก: hip/knee extensors หลุดหมด) → รวมเป็นลิสต์เดียวเรียงวลียาวก่อน
- **ชื่อ error จาก session** — prompt สั่งให้ใช้ชื่อ error ตาม JSON เป๊ะ ๆ ("Knee valgus") การนับเป็น jargon = ลงโทษโมเดลที่ทำตามคำสั่ง → สคริปต์อ่านชื่อจาก `mock_data/mock_sessions.json` (รวม `previous_common_errors` ด้วย เพราะ prompt สั่งให้ชมเวลาอาการหาย) แล้วยกเว้นให้

### 12.3 ค้างไว้

- term list เป็น judgment call ล้วน ๆ (ไม่ได้ generate จาก prompt เพราะต้องจับศัพท์ที่ prompt **ลืม** ใส่ด้วย) ถ้าแก้ list ตัวเลขเปลี่ยน — ควรแก้พร้อมบันทึกเหตุผลในไฟล์ JSON
- ยังไม่มี metric ฝั่ง "ตัวเลขในคำตอบตรงกับ session JSON ไหม" (rep number / score) — ตอนนี้ยังตรวจด้วยตาจากรายงาน

---

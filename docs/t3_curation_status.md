# T3 — สถานะการ curate KB v6 (handoff)

> อัปเดต 2026-10-03 · branch `rule-change-v6` · แผนหลัก [`rule_change_v6_plan.md`](rule_change_v6_plan.md) · เปิดไฟล์นี้ก่อนเมื่อทำ T3 ต่อใน session ใหม่
> **สถานะ:** trial ✅ · รอบ 1 ✅ · รอบ 2a ✅ · **user เลือกหยุดที่ 2a ตาม §8.1** (2026-10-03, data gap ค่อยแก้ทีหลัง) · §8.1 ข้อ 1–3 ✅ (commit `f6fdf0b`) · ข้อ 5 E5 ✅ ทำก่อน ingest (`eval/split_v6.json`, split ตามเอกสารจึงไม่ขึ้นกับ ingest) · ข้อ 4 ingest ✅ `kb_gemini_curated_v6` 1,845 row (= item ทั้งหมด) · ข้อ 6 mock ✅ 4 ไฟล์ `mock_data/mock_sessions_<ท่า>.json` 20 session (`build_mock_sessions.py`) · **ข้อ 7 กำลังทำ:** prompt v14 ผ่าน smoke แล้ว (`state_occurred` ยังไม่ส่งให้ LLM จนกว่าจะคุยกับระบบ 1 · คำถามอยู่ §8.1 ข้อ 7) → ถัดไปรัน baseline เต็ม 4 ท่า · DB อยู่ใน Docker `pgvector-db` localhost:5432

## 0. เริ่มต่อจากตรงนี้

1. ทำ §8.1 ต่อจากข้อ 7 (prompt → generate) · E5 เสร็จแล้ว: วิธีแบ่งดู `eval/make_split.py` และ eval_v6_plan E5 · ตอนเพิ่มเอกสาร (§8.3) ใช้ `python eval/make_split.py --round v6b` (ห้ามเปลี่ยนชื่อ/ย้ายไฟล์ใน `data/` เพราะ path คือ id)
2. ~~รันรอบ 2a~~ เสร็จแล้ว
3. หลังรันทุกรอบ: `python data_pipeline/tag_coverage.py curated_data_v6` → ดูกฎที่ยังต่ำกว่าเกณฑ์ (§4) · เช็ค log หา `FOLDER MISMATCH` (§6.1)
4. ครบทุกรอบแล้ว: commit `curated_data_v6/` + `data_pipeline/curation_usage_v6.jsonl` → T5 ingest → E5 split → mock 12 กฎ + clean → generate
   · ถ้าหยุด curate หลังรอบ 2a แล้วค่อยกลับมาเพิ่มทีหลัง → ทำตาม §8

## 1. กติกาที่ต้องรักษา (ห้ามละเมิด)

- **ห้ามแก้ curator ระหว่างรอบ** (prompt, model `gemini-3.5-flash`, temperature 0.1) ไม่อย่างนั้นไฟล์คนละรอบจะติด tag ด้วยกติกาต่างกัน · ถ้าจำเป็นต้องแก้ ให้ re-curate รอบก่อนหน้าหรือบันทึกในรายงาน
  (การเพิ่ม alias `splitsquat` ใน §6.1 ไม่เปลี่ยน prompt — แค่การจัดท่าหลังได้ผล)
- **ห้ามเลือกเอกสารของรอบถัดไปจากผล eval** — เลือกจาก `tag_coverage.py` เท่านั้น (ดู output ของ curator ไม่ใช่ข้อสอบ)
- **E5 (แบ่ง dev/test ตามเอกสาร) และ ingest ทำหลังรอบสุดท้ายครั้งเดียว**
- **Claude ห้ามแก้ `query` ใน `error_taxonomy.py` อีก** (อ่านต้นฉบับแล้วตั้งแต่ T3a) — ถ้าต้องแก้ให้ user แก้หรือทำเป็น Q-tuned
- ห้ามรัน eval บน `kb_gemini_curated_v5` (รหัส taxonomy ใหม่แล้ว)
- `usage_log` มี `model_version` ทุกครั้ง — ใช้ยืนยันว่าทุกรอบใช้โมเดลเดียวกัน (รอบ 1 = `gemini-3.5-flash`)

## 2. คำสั่ง

```
python data_pipeline/curator.py --out curated_data_v6 --excluded excluded_from_kb_v6 \
  --skip-list data_pipeline/prefilter_v6.json \
  --usage-log data_pipeline/curation_usage_v6.jsonl \
  --batch data_pipeline/curation_batches_v6.json <ชื่อรอบ>
python data_pipeline/tag_coverage.py curated_data_v6          # นับ tag ต่อกฎ (ไม่มีค่า API)
cd data_pipeline && python rescue_false_mismatches.py --curated ../curated_data_v6 --excluded ../excluded_from_kb_v6
```
- curator ข้ามไฟล์ที่ curate แล้วเสมอ (รันซ้ำได้) · `--only <substring>` สำหรับไฟล์เดียว
- รันด้วย `PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 .venv/Scripts/python …` · key อยู่ใน `.env` (`GOOGLE_API_KEY`)

## 3. ที่ทำไปแล้ว

| ขั้น | ผล | commit |
|---|---|---|
| T1 Q-spec + card | user ยืนยัน query ทั้ง 12 · ผู้เชี่ยวชาญอนุมัติ card 12 ใบ (ไม่ใส่ชื่อ) · ลบ `rule_th`/`display_th`/`aliases` | `cc4f55b` |
| T3a prefilter | 102 หน่วย (PDF 85 · URL 17) → keep 71 · drop 31 (27 ไม่เกี่ยว + `feedback_and_cueing` 4 ไฟล์ = ใช้ทำ prompt P5 อย่างเดียว) · [`prefilter_v6_review.md`](prefilter_v6_review.md) | `35f749a` |
| T4 curator | `--skip-list` · `general/` เห็น 12 กฎ + route ราย item · card `excludes` เป็น "do not tag when" · ไม่ใช้ mismatch กับ general | `3a98ac9` |
| usage log / batch | `--usage-log` (input/cached/output/reasoning/model_version/finish_reason) · `--only` · `--batch` | `928264c` `8471ba7` `cada83c` |
| alias split squat | `splitsquat` → lunge · rescue มี `--curated/--excluded` · `tag_coverage.py` | `fc4a096` |
| รอบ 2a | 7 ไฟล์ (§5) · batch `round2a` · FOLDER MISMATCH 0 · `model_version` = `gemini-3.5-flash` ทุกครั้ง · `finish_reason` = STOP ทุกครั้ง | `f6fdf0b` |
| **commit แล้ว** | `curated_data_v6/` · `data_pipeline/curation_usage_v6.jsonl` (406 แถว) · `round2a` ใน `curation_batches_v6.json` — หยุดที่ 2a (§8) | `f6fdf0b` |

### ค่าใช้จ่าย (Gemini 3.5 Flash: input $1.50 · cached $0.15 · output $9.00 ต่อ 1M token · thinking คิดเป็น output)
| รอบ | calls | accept | input | cached | output | ค่า |
|---|---|---|---|---|---|---|
| trial (manual ใน general/) | 53 | 10 | 169,505 | 64,618 | 70,429 | ~$0.80 |
| รอบ 1 (28 ไฟล์) | 246 | 158 | 536,325 | 0 | 523,361 | **$5.51 (~฿180)** |
| รอบ 2a (7 ไฟล์) | 107 | 50 | 245,666 | 0 | 192,492 | **$2.10 (~฿70)** |
- output ส่วนใหญ่คือ thinking (window ที่ accept ~2.5k reasoning token) · v5 ใช้ไป ~฿392 ทั้งหมด (AI Studio, ครอบด้วย Savings)
- รอบ 1 cached = 0 (implicit cache ไม่ทำงาน ต่างจาก trial) — ผลต่างแค่ ~$0.7

## 4. tag coverage (เกณฑ์ ≥ 5 ต่อประเภท)

### หลังรอบ 2a (ปัจจุบัน)

| กฎ | mistake | consequence | principle | finding | แหล่ง | ขาด |
|---|---|---|---|---|---|---|
| partial_squat | 8 | 7 | 21 | 25 | 7 | – |
| knee_valgus | 49 | 42 | 61 | 42 | 9 | – |
| knee_varus | 14 | 6 | 16 | 13 | 8 | – |
| rounded_back | 80 | 74 | 116 | 31 | 9 | – |
| hip_sag_or_pike | 10 | 8 | 20 | 3 | 4 | – |
| **partial_pushup** | 2 | 1 | 5 | 2 | 3 | mistake, consequence |
| **shallow_lunge** | 3 | 1 | 9 | 7 | 9 | mistake, consequence |
| excessive_front_knee_flexion | 8 | 11 | 9 | 19 | 7 | – |
| forward_trunk_lean | 17 | 18 | 20 | 15 | 9 | – |
| **straight_back_leg** | 0 | 0 | 4 | 0 | 4 | mistake, consequence, principle |
| elbow_flare | 12 | 9 | 13 | 4 | 5 | – |
| partial_curl | 7 | 5 | 23 | 7 | 9 | – ✅ (ผ่านหลัง 2a) |

item ต่อท่า: squat 801 (245 ไม่มี tag) · lunge 596 (464) · bicep-curl 283 (204) · push-up 147 (96) · general 18

### หลังรอบ 1

| กฎ | mistake | consequence | principle | finding | แหล่ง | ขาด |
|---|---|---|---|---|---|---|
| partial_squat | 8 | 7 | 21 | 25 | 7 | – |
| knee_valgus | 49 | 42 | 61 | 42 | 9 | – |
| knee_varus | 14 | 6 | 16 | 13 | 8 | – |
| rounded_back | 80 | 74 | 116 | 31 | 9 | – |
| hip_sag_or_pike | 10 | 8 | 19 | 3 | 3 | – |
| **partial_pushup** | 2 | 1 | 4 | 1 | 2 | ทุกประเภท |
| **shallow_lunge** | 2 | 1 | 7 | 6 | 6 | mistake, consequence |
| excessive_front_knee_flexion | 5 | 9 | 8 | 18 | 5 | – |
| forward_trunk_lean | 11 | 13 | 16 | 5 | 7 | – |
| **straight_back_leg** | 0 | 0 | 3 | 0 | 3 | ทุกประเภท |
| elbow_flare | 9 | 6 | 8 | 4 | 4 | – |
| **partial_curl** | 4 | 0 | 12 | 5 | 7 | mistake, consequence |

item ต่อท่า: squat 801 (245 ไม่มี tag) · lunge 405 (309) · bicep-curl 162 (114) · push-up 105 (57) · general 18

## 5. รอบ 2a: เติมเฉพาะกฎที่ขาด ✅ รันแล้ว 2026-10-03 (107 window · $2.10)

| กฎ | ไฟล์ (path ใต้ `data/`) | window |
|---|---|---|
| straight_back_leg | `lunge/Trunk and Shank Position Influences Patellofemoral Joint Stress in the Lead and Trail Limbs During the Forward Lunge Exercise.pdf` | 12 |
| straight_back_leg, shallow_lunge | `lunge/Biomechanical difference in forward and lateral lunges and its changes in knee joint moment and functional measurement.pdf` (FMS in-line lunge) | 11 |
| straight_back_leg | `lunge/Schellenberg2017_SplitSquat_StepLengthTibialAngle_BMCSSMR.pdf` | 11 |
| shallow_lunge | `lunge/Effects of Loading Positions on Lower Limb Biomechanics During Lunge Squat in Men with Different Training Experience.pdf` | 15 |
| partial_pushup | `push-up/The_Effect_of_Position_on_the_Percentage_of_Body.992962.pdf` (keep ไม่แน่ใจ) | 10 |
| partial_curl | `bicep-curl/The interplay between muscle length, range of motion, and exercise selection a review.pdf` | 24 |
| partial_curl | `bicep-curl/The Effect of Varying Weightload Intensities on Biceps Curl Techn.pdf` (thesis) | 24 |

- `partial_pushup` แทบไม่มีเอกสารเหลือ ถ้ายังไม่ถึงเกณฑ์ → นับเป็น **data gap** ใน eval (แผน eval v6) หรือ user หาเอกสารเพิ่ม
- เอกสาร keep ที่เหลือหลัง 2a (~230 window: valgus ที่เหลือ, heel lift, step length, EMG, Bonilla2022, keep ไม่แน่ใจ) — ทำต่อหรือไม่แล้วแต่ user · ถ้าทำ ต้องทำก่อน ingest/E5

### 5.1 ผลรอบ 2a

| ไฟล์ | accept | tag ที่ได้ (กฎเป้าหมาย) |
|---|---|---|
| Trunk and Shank Position (PFJ stress lead/trail) | 8/12 | shallow_lunge principle 1 · ไม่มี straight_back_leg · forward_trunk_lean 15 |
| Biomechanical difference forward/lateral (FMS) | 3/11 | shallow+excessive principle 1 ("เข่าทั้งสอง ~90°") |
| Schellenberg2017 split squat | 4/11 | **ไม่มี tag เลย** (แรงกล้ามขาหลังตาม step length/tibia angle) |
| Effects of Loading Positions (novice vs experienced) | 8/15 | straight_back_leg principle 1 · shallow_lunge mistake 1 + finding 1 · forward_trunk_lean 12 · excessive 7 |
| push-up Percentage of Body mass | 7/10 | partial_pushup principle 1 + finding 1 · hip_sag principle 1 |
| muscle length / ROM review | 9/24 | partial_curl 14 (mistake 3 · consequence 4 · principle 5 · finding 2) |
| Weightload Intensities thesis | 11/24 | partial_curl 7 · elbow_flare 11 |

- **partial_curl ผ่านเกณฑ์แล้ว** · อีก 3 กฎยังไม่ถึง
- **straight_back_leg:** เอกสารพูดถึงขาหลัง 51 item แต่เป็นเรื่องแรงหรือภาระของขาหลัง ไม่มีเอกสารไหนบรรยาย "ขาหลังเหยียดตรง" ว่าเป็นท่าผิด → curator ไม่ติด tag ตาม card ซึ่งถูกต้อง · ใน `data/` ไม่มีเอกสารเหลือที่น่าจะเติมได้ (`lunge/front_knee_too_shallow/` และ `push-up/elbow_depth/` เป็นโฟลเดอร์ว่าง) → **data gap**
- **partial_pushup / shallow_lunge:** ได้เพิ่มเล็กน้อย ยังขาด mistake/consequence → data gap เหมือนกัน เว้นแต่ user จะหาเอกสารใหม่ (ต้องผ่าน prefilter ก่อน)
- รายการ §8.2 (22 ไฟล์) เลือกมาเพื่อ coverage ทั่วไป ไม่ได้เล็ง 3 กฎนี้ · ถ้ารันก็ไม่น่าช่วย 3 กฎนี้มาก

## 6. สิ่งที่เจอและต้องตามดู

1. **mismatch ของ split squat (แก้แล้ว):** Arakawa2025 / Jaeggi2024 ใน `lunge/back_knee_form/` ถูกตัด 8 window เพราะ `exercise_type = "(Bulgarian) Split Squat"` → เพิ่ม alias แล้ว rescue กลับครบ 8 · รอบถัดไปให้ grep log หา `FOLDER MISMATCH` ทุกครั้ง
2. **ข้อมูลที่อาจขัดกับ `forward_trunk_lean`:** lunge มี item ไม่ติด tag ~18 ตัวที่บอกว่าลำตัวโน้มหน้าช่วยกล้ามสะโพก / ลำตัวตั้งเพิ่มแรงที่เข่า และ manual แนะนำลำตัวโน้ม 35–45° · curator ไม่ติด tag ถูกแล้ว แต่ semantic search ยังดึงได้ → ตรวจตอน generate / ขั้น P
   **อัปเดตหลัง 2a:** ตอนนี้มี item **ติด tag** `forward_trunk_lean` ที่บอกทิศทางกลับกันแล้ว (จาก Trunk and Shank Position เช่น "ลำตัวตั้ง + หน้าแข้งตั้ง → แรง PFJ ที่ขาหลังสูงสุด", "โน้มไปหน้าเพิ่มการทำงานของ gluteus") · ติดตาม card ข้อ includes "งานวิจัยที่เปรียบเทียบลำตัวตั้งตรงกับลำตัวโน้มไปหน้า" จึงไม่ใช่ curator ผิด แต่ generator อาจดึงไปบอกว่า "โน้มตัวดี" → ตรวจตอน generate / ขั้น P · มีบาง item ที่จัดลง `common_mistakes` ทั้งที่เป็นแค่ข้อเท็จจริงทางกลศาสตร์ (เช่น "Leaning the trunk forward shifts the muscular demand…")
3. **`rounded_back` ติดกับเรื่องศีรษะ/สายตา 23 item:** ส่วนใหญ่เป็นเหตุ-ผล (มองลง → ลำตัวงอ) รับได้ · card บอก "Head or neck position on its own" ไม่นับ — ดูในสุ่มตรวจหลัง T3
4. **Lorenzetti 2018 vs Correction 2020:** เครื่องหมาย ΔD* ของ varus ขัดกัน (ฉบับแรกผิด) ทั้งสองอยู่ใน KB — ผลกระทบน้อย
5. tag คู่กฎพี่น้อง: valgus+varus 36 item (เป็น "เข่าตรงแนวปลายเท้า" ใช้ได้ทั้งคู่) · shallow+excessive 6 item (เป้า 90°) — ไม่พบการติดสลับ
6. ~~หลัง T3 ครบ: สุ่มอ่าน item ที่ route มาจาก `general/` ≥ 20 ชิ้น (แผน T4)~~ ✅ 2026-10-03: item ที่ route มาจาก `general/` มีทั้งหมด 75 ชิ้น (squat 44 · lunge 23 · bicep-curl 8 · ติด tag 29) · สุ่ม 24 ชิ้น (seed 20261003) อ่านทีละชิ้น + สแกนครบ 75
   - **route ท่าถูก 24/24** · tag ที่ไม่ใช่กฎของท่านั้น 0/75
   - item ที่ไม่ติด tag ถูกทุกชิ้น (เช่น ส้นเท้าหลัง → ไม่ติด straight_back_leg ตาม excludes · ลำตัวหมุน/โยกตัวใน curl ไม่มีกฎ)
   - **ผิด 2–3 ชิ้น รูปแบบเดียวกับ §6.3:** "Tilting the head forward/backward during the squat" (mistake) และ "Head and eyes should be positioned forward…" (principle) ติด `rounded_back` ทั้งที่ card excludes "Head or neck position on its own" · consequence 2 ชิ้นที่บอกว่าศีรษะทำให้หลังงอ = เหตุ-ผล รับได้
   - squat มี principle "torso 35–45° from vertical" ติด `rounded_back` (oq1 = นับลำตัวโน้ม) → ทิศกลับกันแบบเดียวกับ §6.2 ใน squat
   - ไม่แก้ (ไม่แก้ผล curator) · ถ้า feedback dev แสดงว่ามีปัญหา ใช้ทาง A/B ใน §6.7
7. **วิธีแก้ถ้า tag ผิดทิศทำให้ feedback ผิด** (คุย 2026-10-03, ไม่ต้อง curate ใหม่): A. prompt บอกว่าท่าผิดถูกตัดสินแล้ว ใช้ KB อธิบายในทิศนั้นเท่านั้น (ลำดับแรก, ใช้ได้ทุกกฎ) · B. ถอด tag เฉพาะ item แบบ `fix_fault_tags.py` (แก้ไฟล์ + row ไม่ embed ใหม่) · C. ลบ item · D. แก้ card → curate lunge ใหม่ (118 call ≈ $2.8) + ผู้เชี่ยวชาญอนุมัติ card v2 · ทุกทางเลือกจาก feedback ของ **dev เท่านั้น** และจดรายการ item ที่แก้มือในรายงาน

## 7. ไฟล์ที่เกี่ยวข้อง

| ไฟล์ | หน้าที่ |
|---|---|
| `data_pipeline/curator.py` | curator v6 |
| `data_pipeline/prefilter_v6.json` | ผล T3a (skip list) |
| `data_pipeline/curation_batches_v6.json` | รายการไฟล์แต่ละรอบ (`trial`, `round1`, `round2a`) |
| `data_pipeline/curation_usage_v6.jsonl` | token ต่อครั้ง (แถว 300–406 = รอบ 2a) |
| `data_pipeline/tag_coverage.py` | นับ tag ต่อกฎ |
| `data_pipeline/test_route_general.py` | เทสต์ route/skip/batch/fault block |
| `curated_data_v6/<ท่า>/…` | ผล curate (ไฟล์ `general__*.json` = item ที่ route มาจาก `general/`) |
| `excluded_from_kb_v6/` | window ที่ mismatch (ตอนนี้ว่าง) |
| `eval/rule_cards.json` | card 12 ใบ (curator ใช้ `excludes`) |

## 8. ทางเลือก: หยุดหลังรอบ 2a → ไปให้ถึง feedback ก่อน → กลับมา curate ทีหลัง (คุยกัน 2026-10-03)

ยังไม่ได้ตัดสินว่าจะเลือกทางนี้ · ถ้าเลือก ให้ทำตามนี้

### 8.1 ช่วงแรก: หยุดหลัง 2a
1. รันรอบ 2a → `tag_coverage.py` → grep `FOLDER MISMATCH` → `rescue_false_mismatches.py` ถ้ามี
2. สุ่มอ่าน item ที่ route มาจาก `general/` ≥ 20 ชิ้น (§6.6) — ต้องทำก่อน ingest
3. commit `curated_data_v6/` + `curation_usage_v6.jsonl` · จดในรายงานว่าหยุดที่ 2a และกฎที่ยังไม่ถึงเกณฑ์ (น่าจะมี `partial_pushup`) = data gap
4. T5 ingest → `kb_gemini_curated_v6`
5. E5 split → commit `eval/split_v6.json` ทันที
6. ~~mock 12 กฎ + clean~~ ✅ 2026-10-03: แยก 4 ไฟล์ตามท่า (user เลือก) · ต่อท่า = 1 session ต่อกฎ + mixed + clean (squat 6 · push-up 4 · lunge 6 · bicep-curl 4) · 10 entry ต่อ session · รูปแบบที่ user ยืนยัน: `error_type` และ `previous_common_errors` = key · `state_occurred` = state ของ FSM (CONCENTRIC/INFLECTION/ECCENTRIC) · ครั้งที่ไม่ถูกนับ `status: "abort"` · abort ที่มี error นับเป็น `incorrect_reps` (user) → `total_reps` = correct + incorrect = ทุก entry, `overall_score` เฉลี่ยทุก entry · **สมมติฐาน (รอระบบ 1 ยืนยัน):** abort เป็น entry ใน `reps_detail` · `build_mock_sessions.py --check` ตรวจว่าไม่ขัดสเปก · ไฟล์เก่า (`mock_sessions_per_fault.json` ฯลฯ) เก็บไว้
7. ปรับ prompt ขั้นต่ำให้ generator รับ key ใหม่ 12 ตัว → generate · P-rule-card / P5 เป็นขั้นแยกทีหลัง
   · ตอนอ่าน feedback ดู §6.2 (lunge ที่บอกว่าลำตัวโน้มไปหน้าดี)
   - **prompt v14** (2026-10-03, `e6b2a9a`) แก้แค่การอ่าน format: `error_type` = key (บรรยายเป็นภาษาคน ห้ามพิมพ์ key, ตัวแรก = priority สูงสุด) · `abort` (นับใน total/incorrect, เรียก "attempt N") · default collection เป็น v6 (`embedding_config.py`) · **ไม่**แตะ `consequence` (P1), P2–P6, rule card, ทาง A §6.7
   - **`state_occurred` ยังไม่ส่งให้ LLM** (user 2026-10-03): `HELD_BACK_FIELDS` ใน `test_rag_compare.py` ตัดออกจาก payload · ไฟล์ mock เก็บไว้เหมือนเดิม · เหตุผล: smoke 2 รอบที่อธิบาย state ใน prompt (`compare_output/smoke_v14.md`, `smoke_v14b.md`) ยังอ่าน CONCENTRIC เป็น "ขึ้น" 3–4/8 คำตอบ, ผูกกฎแบบ rep กับช่วง 4/8, คำ concentric/eccentric หลุด 2–3/8 และความหมายจริงยังไม่ยืนยันกับระบบ 1 · smoke รอบ 3 ไม่ส่ง state (`smoke_v14c.md`): key หลุด 0/8 · ตัวเลข/abort ถูก 8/8
   - เอา state กลับมา = checkpoint generation แยก เทียบกับ baseline v14
   - **คำถามที่ต้องคุยกับระบบ 1** (รูปแบบ JSON ที่ mock อยู่):
     1. `state_occurred` ของกฎแบบ frame = state ของ frame แรกที่ผิดหรือไม่ · กฎแบบ rep (ตรวจตอนจบ attempt) ส่ง state อะไร หรือไม่ส่ง
     2. fault เดียวเกิดหลายครั้งใน rep เดียว ส่งกี่ entry
     3. abort เป็น entry ใน `reps_detail` ไหม · `rep_no` นับต่อรวม abort ไหม
     4. `total_reps` / `correct_reps` / `incorrect_reps` ของระบบ 1 นับ abort แบบที่ตกลง (abort ที่มี error = incorrect) หรือไม่
     5. ส่งค่ามุมต่อ rep มาไหม (สเปกบอก rep summary มี per-rep metric values) · `hip_sag_or_pike` / `elbow_flare` บอกทิศได้ไหม (ค้างใน rule_change_v6_plan §3)
   - เจอใน smoke แต่ไม่ใช่ format (จดให้ขั้น P): ตัวเลขที่ไม่มีใน context ("พัก 90 วินาที–2 นาที" → P4) · `partial_pushup` ถูกบรรยายผิดเป็น "ดันขึ้นได้นิดเดียว" และ `hip_sag_or_pike` เป็นสะโพกตกอย่างเดียว, `rounded_back` เป็นหลังงอ (→ P-rule-card) · อ้างว่า error "กระจุกช่วงท้ายเซ็ต" ทั้งที่ mock สลับ rep · ชื่อ drill "eccentric push-ups" (Translation rule)

### 8.2 รายการเอกสารที่จะ curate ทีหลัง (จดไว้ก่อนเห็น feedback)
เลือกจาก prefilter (keep) ที่ยังไม่อยู่ใน trial / round1 / round2a — **ไม่ใช่จากผล feedback หรือ eval** ·
ถ้ากลับมาแล้วจะตัดหรือเพิ่มไฟล์จากรายการนี้ ให้เขียนเหตุผลในรายงานว่าไม่ได้มาจากผล eval

| ท่า | ไฟล์ (path ใต้ `data/`) |
|---|---|
| squat | `squat/Altered_Knee_and_Ankle_Kinemat.pdf` |
| squat | `squat/Lu2022_HeelLiftInsoles_BarbellSquat_Bioengineering.pdf` |
| squat | `squat/Muscle Activation Patterns During Different Squat Techniques.pdf` |
| squat | `squat/Physiotherapy Res Intl - 2015 - Jaberzadeh - The Effect of Altering Knee Position and Squat Depth on VMO   VL EMG Ratio.pdf` |
| squat | `squat/knee_valgus/Cronstrom2020_KneeAbduction_ACLRisk_MetaAnalysis_BMCMSD.pdf` |
| squat | `squat/knee_valgus/Forman2023_ElasticBands_KneeValgus_SquatReview_IJSPT.pdf` |
| squat | `squat/knee_valgus/Sahabuddin2021_HipAnkleExercise_KneeValgus_SR_PeerJ.pdf` |
| squat | `squat/knee_valgus/Werner2022_KneeAlignmentInstructions_Focus_IJERPH.pdf` |
| squat | `squat/knee_valgus/Wilczynski2020_DynamicKneeValgus_ModifiableFactors_IJERPH.pdf` |
| lunge | `lunge/Comfort2015_ForwardReverseLunge_JointLoading_JAthlTrain.pdf` |
| lunge | `lunge/Scandinavian Med Sci Sports - 2009 - Jönhagen - Muscle activation and length changes during two lunge exercises .pdf` |
| lunge | `lunge/Song2023_StepLength_SplitSquat_FrontBioeng.pdf` |
| lunge | `lunge/Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise.pdf` |
| lunge | `lunge/mxn167Sp24.pdf` |
| lunge | `lunge/front_knee_too_deep/Escamilla2022_PatellofemoralLoad_ForwardSideLunge_IJSPT.pdf` |
| lunge | `lunge/torso_upright/AygunPolat2025_TrunkPosition_BulgarianSplitSquat_BMCSSMR.pdf` |
| push-up | `push-up/body_alignment/GarciaJaen2020_AbdominalHollowing_Plank_IJERPH.pdf` |
| bicep-curl | `bicep-curl/Biceps Brachii and Brachioradialis Excitation in Biceps Curl Exercise Different Handgrips, Different Synergy.pdf` |
| bicep-curl | `bicep-curl/Bilateral Biceps Curl Shows Distinct Biceps Brachii and Anterior Deltoid Excitation Comparing Straight vs. EZ Barbell Coupled with Arms Flexion No-Flexion.pdf` |
| bicep-curl | `bicep-curl/From Continuous sEMG Signals to Discrete Muscle State Tokens A Robust and Interpretable Representation Framework.pdf` |
| bicep-curl | `bicep-curl/The Effect of Shoulder Flexion Angles on the  Recruitment of Upper-extremity Muscles during  Isometric Contraction.pdf` |
| general | `general/injury/Bonilla2022_FitnessCenterInjuries_IJERPH.pdf` |

22 ไฟล์ (~230 window ตามที่ประเมินใน §5) · URL ทั้ง 17 หน้าทำไปแล้วในรอบ 1 · เอกสารใหม่ที่ไม่มีใน `data/` ตอนนี้ต้องผ่าน prefilter ก่อน (เพิ่มลง `prefilter_v6.json`)

### 8.3 ช่วงหลัง: กลับมา curate เพิ่ม
- **ไม่ต้องแก้โค้ด** curator ข้ามไฟล์ที่ curate แล้วเอง → เพิ่ม batch ใหม่ (เช่น `round3`) ใน `curation_batches_v6.json` แล้วรันคำสั่ง §2 เขียนลง `curated_data_v6/` เดิม
- **curator ต้องเหมือนเดิม** (prompt · `gemini-3.5-flash` · temperature 0.1) · เช็ค `model_version` ใน usage log เทียบกับรอบ 1 · ถ้าโมเดลถูกปิดหรือเปลี่ยนรุ่น = เปลี่ยน curator → ต้อง curate รอบเก่าใหม่ หรือเขียนลงรายงาน
- **ingest ลง collection ใหม่ `kb_gemini_curated_v6b`** จากทั้งโฟลเดอร์ (ของเดิมรอบ 1 + 2a และของใหม่รวมกัน) — ไม่เติมลง v6:
  ```
  python ingest.py --data-folder ./curated_data_v6 --collection kb_gemini_curated_v6b
  ```
  - v6 เดิมเก็บไว้เป็นจุดอ้างอิง เพราะ feedback และตัวเลขที่ทำไปแล้วผูกกับ v6 · รัน mock + prompt เดิมบน v6 กับ v6b แล้วเทียบได้ตรง ๆ ว่าข้อมูลที่เพิ่มช่วยกฎไหน
  - ingest เพิ่มอย่างเดียว ไม่ลบ chunk เก่า ถ้าเติมลง v6 แล้วมีไฟล์ที่ curate ซ้ำ chunk เก่าจะค้าง
  - ของเดิมไม่ถูก curate ซ้ำ (ไม่เสียค่า curator) แต่ v6b ต้อง embed ใหม่ทั้งหมด เพราะ id ของ chunk รวมชื่อ collection
- **E5 ห้ามแบ่งใหม่ทั้งชุด** — ล็อกการแบ่งของเอกสารเดิมใน `split_v6.json` แล้วจัดเฉพาะเอกสารใหม่ลง dev/test (70/30 stratified, seed คงที่) · ถ้าแบ่งใหม่ทั้งหมด เอกสารเดิมอาจสลับระหว่าง dev กับ test ทำให้ test ที่เคยดูผลไปแล้วปนเข้ามา
- feedback ที่ generate บน v6 ต้อง generate ใหม่บน v6b ถ้าจะเทียบ · ผล `--final` บน v6 กับ v6b รายงานแยกกัน

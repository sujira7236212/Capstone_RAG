# T3 — สถานะการ curate KB v6 (handoff)

> อัปเดต 2026-10-03 · branch `rule-change-v6` · แผนหลัก [`rule_change_v6_plan.md`](rule_change_v6_plan.md) · เปิดไฟล์นี้ก่อนเมื่อทำ T3 ต่อใน session ใหม่
> **สถานะ:** trial ✅ · รอบ 1 ✅ · **ถัดไป: รอบ 2a รอ user อนุมัติ** (§5) · ยังไม่ ingest

## 0. เริ่มต่อจากตรงนี้

1. อ่าน §5 แล้วถาม user ว่าจะรันรอบ 2a ตามรายการไหม (ยังไม่ได้อนุมัติ)
2. ถ้าอนุมัติ: เพิ่ม batch `round2a` ใน [`data_pipeline/curation_batches_v6.json`](../data_pipeline/curation_batches_v6.json) แล้วรันคำสั่งใน §2 ด้วยชื่อ `round2a` (รันใน background · ~96 window · ~30 นาที)
3. หลังรันทุกรอบ: `python data_pipeline/tag_coverage.py curated_data_v6` → ดูกฎที่ยังต่ำกว่าเกณฑ์ (§4) · เช็ค log หา `FOLDER MISMATCH` (§6.1)
4. ครบทุกรอบแล้ว: commit `curated_data_v6/` + `data_pipeline/curation_usage_v6.jsonl` → T5 ingest → E5 split → mock 12 กฎ + clean → generate

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
| **ยังไม่ commit** | `curated_data_v6/` · `data_pipeline/curation_usage_v6.jsonl` (299 แถว) — commit ตอนครบทุกรอบ | — |

### ค่าใช้จ่าย (Gemini 3.5 Flash: input $1.50 · cached $0.15 · output $9.00 ต่อ 1M token · thinking คิดเป็น output)
| รอบ | calls | accept | input | cached | output | ค่า |
|---|---|---|---|---|---|---|
| trial (manual ใน general/) | 53 | 10 | 169,505 | 64,618 | 70,429 | ~$0.80 |
| รอบ 1 (28 ไฟล์) | 246 | 158 | 536,325 | 0 | 523,361 | **$5.51 (~฿180)** |
- output ส่วนใหญ่คือ thinking (window ที่ accept ~2.5k reasoning token) · v5 ใช้ไป ~฿392 ทั้งหมด (AI Studio, ครอบด้วย Savings)
- รอบ 1 cached = 0 (implicit cache ไม่ทำงาน ต่างจาก trial) — ผลต่างแค่ ~$0.7

## 4. tag coverage หลังรอบ 1 (เกณฑ์ ≥ 5 ต่อประเภท)

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

## 5. ข้อเสนอรอบ 2a — เติมเฉพาะกฎที่ขาด (~96 window, ~฿70) ⏸ รอ user

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

## 6. สิ่งที่เจอและต้องตามดู

1. **mismatch ของ split squat (แก้แล้ว):** Arakawa2025 / Jaeggi2024 ใน `lunge/back_knee_form/` ถูกตัด 8 window เพราะ `exercise_type = "(Bulgarian) Split Squat"` → เพิ่ม alias แล้ว rescue กลับครบ 8 · รอบถัดไปให้ grep log หา `FOLDER MISMATCH` ทุกครั้ง
2. **ข้อมูลที่อาจขัดกับ `forward_trunk_lean`:** lunge มี item ไม่ติด tag ~18 ตัวที่บอกว่าลำตัวโน้มหน้าช่วยกล้ามสะโพก / ลำตัวตั้งเพิ่มแรงที่เข่า และ manual แนะนำลำตัวโน้ม 35–45° · curator ไม่ติด tag ถูกแล้ว แต่ semantic search ยังดึงได้ → ตรวจตอน generate / ขั้น P
3. **`rounded_back` ติดกับเรื่องศีรษะ/สายตา 23 item:** ส่วนใหญ่เป็นเหตุ-ผล (มองลง → ลำตัวงอ) รับได้ · card บอก "Head or neck position on its own" ไม่นับ — ดูในสุ่มตรวจหลัง T3
4. **Lorenzetti 2018 vs Correction 2020:** เครื่องหมาย ΔD* ของ varus ขัดกัน (ฉบับแรกผิด) ทั้งสองอยู่ใน KB — ผลกระทบน้อย
5. tag คู่กฎพี่น้อง: valgus+varus 36 item (เป็น "เข่าตรงแนวปลายเท้า" ใช้ได้ทั้งคู่) · shallow+excessive 6 item (เป้า 90°) — ไม่พบการติดสลับ
6. หลัง T3 ครบ: สุ่มอ่าน item ที่ route มาจาก `general/` ≥ 20 ชิ้น (แผน T4)

## 7. ไฟล์ที่เกี่ยวข้อง

| ไฟล์ | หน้าที่ |
|---|---|
| `data_pipeline/curator.py` | curator v6 |
| `data_pipeline/prefilter_v6.json` | ผล T3a (skip list) |
| `data_pipeline/curation_batches_v6.json` | รายการไฟล์แต่ละรอบ (`trial`, `round1`) |
| `data_pipeline/curation_usage_v6.jsonl` | token ต่อครั้ง (ยังไม่ commit) |
| `data_pipeline/tag_coverage.py` | นับ tag ต่อกฎ |
| `data_pipeline/test_route_general.py` | เทสต์ route/skip/batch/fault block |
| `curated_data_v6/<ท่า>/…` | ผล curate (ไฟล์ `general__*.json` = item ที่ route มาจาก `general/`) |
| `excluded_from_kb_v6/` | window ที่ mismatch (ตอนนี้ว่าง) |
| `eval/rule_cards.json` | card 12 ใบ (curator ใช้ `excludes`) |

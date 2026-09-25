# Ablation log — RAG v2 (เปลี่ยนทีละอย่าง)

แผน: `C:\Users\HP\.claude\plans\quiet-honking-moler.md` · กติกา: หนึ่งขั้น = หนึ่งตัวแปร เทียบกับขั้นล่าสุดที่เก็บไว้

เกณฑ์เก็บขั้น retrieval: recall ขึ้น **และ** ctx wrong_fault ไม่เพิ่ม **และ** golden bad ไม่เพิ่ม **และ** pool-precision ไม่ต่ำกว่าขั้นก่อน − 0.05

วัดด้วย `python eval/eval_retrieval.py --mode single --show-missed` ·
relevance pool `eval/relevance_pool.json` (judge `gemini-3.8-flash`, judge prompt v2, 411 relevant facts / 10 fault, 1,256 candidates) ·
collection `kb_gemini_curated_v5` · budget 9 chunk/fault (sum `MAX_PER_KIND`)

## ตารางผล

| ขั้น | เปลี่ยน | golden hit · precision · bad | recall micro (ceiling) / macro | ctx relevant / wrong_fault / kept | pool-precision | miss: tag_spelling · tag_filter · rank · margin · quota | ตัดสิน |
|---|---|---|---|---|---|---|---|
| B0 | gate ปัจจุบัน (v7 gate, v5 KB) | 10/10 · 0.62 · 1 | 0.15 (0.21) / 0.26 | 60 / 6 / 77 | 0.78 | 14 · 10 · 141 · 34 · 151 | baseline |
| R0 | normalize `fault_tags` ใน DB (ข้อมูล ไม่ใช่ flag) | 10/10 · 0.61 · 1 | 0.15 (0.21) / 0.26 — 62/411 (+1) | 61 / 6 / 77 | 0.79 | 0 · 10 · 146 · 34 · 159 | **เก็บ** |

รายงานเต็ม: B0 `compare_output/ablation_B0_retrieval.md` · R0 `compare_output/ablation_R0_retrieval.md`

## บันทึก

### ขั้น 0 — เครื่องมือวัด (2026-09-25)
- `test_rag_compare._search()` / `retrieve_kb_blocks()` มี `trace=` (optional) บอกเหตุผลของ candidate ทุกตัว (kept / quota / margin / dup) — kept set เหมือนเดิมทุกตัว ยืนยันด้วย golden 10/10 · 0.62 · bad 1 = ตัวเลข §11.4
- `eval/build_relevance_pool.py` (ใหม่): candidate = chunk ที่ tag ตรง (normalize ขีดล่าง) ∪ top-40 ของ 4 query โดยไม่ filter kind/tag → judge ติดป้าย
- `eval/eval_retrieval.py`: `--pool` → recall ต่อ fact (cluster ด้วย near-dup แบบเดียวกับ gate), ceiling ที่ budget เดิม, ป้ายของ chunk ใน context, เหตุผลที่หลุด; `KINDS` รวม `consequence` แล้ว (summary golden ยังคิดจาก 3 kind เดิมเพื่อเทียบกับตัวเลขเก่าได้)
- judge prompt v1 เข้มเกิน (ลดป้าย chunk ที่ไม่เอ่ยชื่อท่า, "low back sags" ≠ hip sag, consequence ทั่วไปของ partial ROM = irrelevant) → v2 แก้แล้ว relabel ทั้งหมด ผลภายใต้ v1 ทิ้ง

### ข้อสังเกตจาก B0
- **quota (151) กับ rank (141) คือสาเหตุหลัก** — chunk ที่ผ่าน margin แล้วแต่ kind นั้นเต็ม และ chunk ที่ไม่ติด top-12 ของ kind ตัวเอง
- **tag_spelling 14** — แก้ได้ด้วย R0 โดยไม่เปลี่ยนวิธีค้น (partial squat 10, bicep partial ROM 4)
- recall ถูกจำกัดด้วย budget: knee valgus มี 116 facts แต่ context รับได้ 9 (ceiling 0.08) — ใช้ ceiling คู่กันเสมอ
- **ข้อจำกัด**: near-dup (Jaccard 0.72) รวมได้แค่ประโยคที่ถ้อยคำใกล้กันมาก paraphrase ที่ใช้คำต่างกันจึงนับเป็นหลาย fact (knee valgus 118 relevant → 116 facts) → recall ต่ำกว่าความจริง แต่เทียบระหว่างขั้นได้เพราะตัวหารเท่ากันทุกขั้น
- ctx wrong_fault 6 ตัวตาม judge (golden นับ bad 1) — ต้องให้คนตรวจตาม `compare_output/relevance_pool_spotcheck.md`

### R0 — normalize fault_tags (2026-09-25) → เก็บ
**เปลี่ยน:** tag ที่สะกดผิด 3 แบบบน 18 item ของ v5 (`partial_squat` 13, `knee_valgus` 2, `partial range_of_motion` 4) → code ตาม taxonomy
- `data_pipeline/fix_fault_tags.py --collection kb_gemini_curated_v5`: แก้ `curated_data_v5/` 4 ไฟล์ + DB 40 แถว (18 แถวที่ tag ของตัวเองผิด + 22 แถวในหน้าต่างเดียวกันที่ผิดแค่ `window_applies_to_fault` ซึ่ง retrieval ไม่ได้อ่าน) แก้แค่ metadata ไม่ re-embed
- id ของแถวย้ายไปเป็นค่าที่ `ingest.py` จะคำนวณจากไฟล์ที่แก้แล้ว (id = md5 ของ collection+text+metadata) — ไม่อย่างนั้น ingest ครั้งหน้า (K2+) จะ embed 40 แถวนี้ซ้ำ ตรวจแล้ว: 1,897 documents ↔ 1,897 rows, re-embed 0
- backup ทั้ง 40 แถว (id เดิม, document, cmetadata): `data_pipeline/backups/kb_gemini_curated_v5_fault_tags_20260925-230240.json`
- กันกลับมา: `curator.normalize_fault_tags()` เรียกใน `curate_knowledge()` ต่อทุก item (test: `data_pipeline/test_normalize_fault_tags.py` 9/9)
- relevance pool: รัน `build_relevance_pool.py` ใหม่เพื่อให้ `fault_tags` ใน pool ตรงกับ DB (eval ใช้ค่านี้แยก miss reason) — judge 0 ตัว, 1,256 key เดิม, label/kind/via เหมือนเดิมทุกตัว ต่างแค่ fault_tags 26 entry + `source` 3 entry ที่ประโยคเดียวกันอยู่ 2 หน้าต่างซ้อนกัน (ลำดับแถวใน DB เปลี่ยน → spotcheck สุ่มได้ชุดใหม่ด้วย)

**ผล:** ผ่านเกณฑ์ทุกข้อ — recall 61 → 62 facts (+1), wrong_fault 6 = 6, golden bad 1 = 1, pool-precision 0.78 → 0.79
- **partial squat** 8 → 9 facts: "Failing to reach parallel squat depth." เข้า context (mistake kept 2 → 3)
- **bicep partial ROM** 7 → 7: "Failing to achieve complete arm extension at the bottom…" เข้า context เป็น mistake อันดับ 1 (best 0.065 → 0.045) แต่มีอีก fact หลุดออก consequence kept 2 → 1: พอมี tag ก็ใช้สระที่มี tag แทนสระที่ไม่มี tag ทำให้ chunk hypertrophy 7 ตัวเปลี่ยนจาก quota เป็น margin
- tag_spelling 14 ตัว: เข้า context 2, ที่เหลือไปอยู่ quota (+8) / rank (+5) — **tag ถูกแล้วแต่ช่องเต็ม** ตรงกับข้อสังเกตจาก B0 ว่าตัวกั้นจริงคือ quota/rank (R1–R2)
- golden precision 0.62 → 0.61: context golden 58 → 59 ตัว (neutral +1) good เท่าเดิม 36 — ไม่ใช่เกณฑ์ของขั้น retrieval แต่จดไว้
- สรุป: ขั้นนี้แก้ข้อมูลที่ผิด ไม่ใช่นโยบายการค้น จึงไม่มีทางเลือก revert ที่สมเหตุสมผล ผลต่อ recall เล็กตามคาด

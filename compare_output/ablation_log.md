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

รายงานเต็มของ B0: `compare_output/ablation_B0_retrieval.md`

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

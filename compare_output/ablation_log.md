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
| R1 | `--tag-mode union` (TAG_BONUS 0.03) | 10/10 · 0.49 · **2** | 0.14 (0.21) / 0.24 — **57**/411 (−5) | 56 / 6 / 79 | **0.71** | 0 · 0 · 150 · 34 · 170 | **revert** |
| R2 | `--kind-pool single` (margin เดียว งบรวม 9) | 10/10 · 0.61 · 0 | **0.07** (0.21) / 0.10 — **28**/411 (−34) | 28 / 2 / **31** | 0.90 | 0 · 10 · 146 · **194** · 33 | **revert** |
| (R2 diag) | single + margin/ลำดับเทียบ best ของ kind ตัวเอง — ไม่ใช่ขั้น ไม่ได้อยู่ใน repo | **9/10** · 0.50 · 1 | 0.16 (0.21) / 0.29 — 67/411 (+5) | 66 / **9** / 89 | 0.74 | 0 · 10 · 146 · 7 · 181 | ไม่ผ่าน (wrong_fault) |

รายงานเต็ม: B0 `compare_output/ablation_B0_retrieval.md` · R0 `compare_output/ablation_R0_retrieval.md` · R1 `compare_output/ablation_R1_retrieval.md` · R2 `compare_output/ablation_R2_retrieval.md`

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

### R1 — `--tag-mode union` (2026-09-25) → revert (default คง `prefer`)
**เปลี่ยน:** `TAG_MODE` ใน `test_rag_compare.py` (flag `--tag-mode` ทั้งใน `test_rag_compare.py` และ `eval/eval_retrieval.py`)
- `prefer` (default = พฤติกรรมเดิม): ใช้สระที่มี tag อย่างเดียวถ้ามี hit ไม่มีค่อย fallback ไปสระไม่มี tag — รันซ้ำแล้ว report ตรงกับ R0 ทุกบรรทัด (ต่างแค่ header)
- `union`: ค้นทั้ง 2 สระ (CANDIDATE_K ละ 12) → merge ตาม id → gate บนระยะที่ปรับแล้ว: tag ตรง fault −`TAG_BONUS`, tag เป็น fault อื่นอย่างเดียว +`TAG_BONUS`, tag ว่าง ±0 · `TAG_BONUS` = 0.03 (= ความกว้าง `RELATIVE_MARGIN`) ตั้งก่อนรัน ไม่ได้จูนจากผล · chunk ที่เก็บยังใช้ระยะดิบ (ลำดับ context / `best` คงสเกลเดิม) · budget 9 เท่าเดิม
- eval: miss reason `tag_filter` ใช้ `metrics["tag_exclusive"]` แทน `tagged` (ภายใต้ union สระไม่มี tag รันเสมอ ที่หลุดจึงเป็น `rank`)

**ผล: ไม่ผ่าน 3 ใน 4 ข้อ** — recall 62 → 57 facts (−5), golden bad 1 → 2, pool-precision 0.79 → 0.71 (−0.08 เกินเพดาน 0.05) · wrong_fault 6 = 6
- tag_filter 10 → 0 แต่จาก 10 fact นั้นเข้า context แค่ **1** (bicep partial ROM, "Dumbbell supinating curls and Bayesian curls…") ที่เหลือไปอยู่ rank 4 / quota 4 / margin 1
- เสีย fact ที่ R0 เคยได้ 6 ตัว ทั้งหมดหลุดที่ **quota** — ส่วนใหญ่เป็น `finding` ที่ tag ตรงและ relevant ถูกแย่งช่องโดย `finding` ที่ไม่มี tag ซึ่งเป็น**ประโยคบรรยาย protocol ของงานวิจัย**: "A successful squat trial in this protocol required reaching at least 60 degrees of knee flexion." (ขึ้นทั้งใต้ butt wink และ partial squat), "The push-up cycle was standardized using a metronome…", "The partial lunge in this study was performed by lowering the body to… 50" (ใต้ trunk lean และ back knee) — ศัพท์องศา/ความลึกตรงกับ query จึง embed ใกล้ แต่ไม่มีเนื้อหาให้คำแนะนำ
- ใต้ insufficient back knee flexion มี mistake "Excessive lumbar extension during the lunge." (ไม่มี tag, judge = wrong_fault) เข้ามาแทน wrong_fault ตัวเดิมที่ถูก penalty ("A shallower lunge of 80 degrees…" tag = shallow lunge) → wrong_fault รวมเท่าเดิม
- chunk 4 ตัวใน context เป็น `unlabeled` (butt wink 2, partial squat 1, back knee 1) — ไม่เคยเป็น candidate ของ pool (ไม่มี tag และไม่ติด top-40 ของ 4 query ที่ไม่ filter kind) นับเป็นไม่ relevant ใน pool-precision ต่อให้ relevant ทั้ง 4 ก็ได้ 60/79 = 0.76 recall −5 ยังอยู่ (unlabeled ไม่ใช่ near-dup ของ fact ใน pool จึงไม่เปลี่ยน recall)
- golden precision 0.61 → 0.49 (good 36 → 30) · bad ตัวใหม่อยู่ใต้ bicep partial ROM

**sensitivity (ไม่ใช้ตัดสิน, จดไว้ดูทิศทาง):** `TAG_BONUS` 0.06 → recall 62 · wrong_fault **5** · pool-precision 0.78 · golden bad 1 | 0.10 → recall 62 · wrong_fault 5 · 0.79 · bad 1
- bonus ใหญ่ขึ้นทำให้ union กลับไปเหมือน `prefer` (tag ชนะเสมอ) recall ไม่ขึ้นที่ค่าไหนเลย → ไม่ผ่านเกณฑ์ "recall ขึ้น" ที่ทุก bonus ไม่ใช่แค่ค่าน้ำหนักผิด
- wrong_fault −1 อยู่ใต้ insufficient back knee flexion (2 → 1) — น่าจะเป็น "A shallower lunge of 80 degrees…" (tag shallow lunge) ที่โดน penalty แรงขึ้น (ยืนยันแล้วเฉพาะที่ 0.03 ว่าตัวนี้หลุด) — ผลข้างเคียงที่ดีเพียงอย่างเดียว เล็กเกินจะเก็บทั้งขั้น

**ข้อสรุป:** filter แบบ exclusive ทำงานมีประโยชน์กับ `finding` — กันประโยค protocol ที่ embedding แยกไม่ออก ตัวที่หลุดเพราะ tag_filter (10) น้อยกว่าที่ quota ต่อ kind กินอยู่มาก (159) ตรงกับข้อสังเกตจาก B0/R0 · ปัญหา protocol-sentence เป็นงานของ reranker (R6) หรือ facet `number`/`definition` (K1) — ถ้าทำ R6 แล้วค่อยลอง union ซ้ำใน leave-one-out

### R2 — `--kind-pool single` (2026-09-25) → revert (default คง `split`)
**เปลี่ยน:** `KIND_POOL` ใน `test_rag_compare.py` (flag `--kind-pool` ทั้งใน `test_rag_compare.py` และ `eval/eval_retrieval.py`; ไม่ใช้ชื่อ `--pool` เพราะชนกับ relevance pool ของ eval)
- `split` (default = พฤติกรรมเดิม): report ตรงกับ R0 ทุกบรรทัด (ต่างแค่ header + บรรทัด `context by kind` ที่เพิ่มใหม่)
- `single` (`_search_single()`): ค้นครั้งเดียวทุก kind (k = CANDIDATE_K × จำนวน kind = 48 เท่าจำนวน candidate เดิมรวมกัน) · margin เดียวจาก best รวม · งบรวม = sum(MAX_PER_KIND) ของ kind ที่ขอ (fault = 9, flawless principle = 2 เท่าเดิม) · **สิทธิ์เข้าสระไม่เปลี่ยน**: แต่ละ kind ยังใช้กฎ tag `prefer` ของตัวเอง (รวมเป็น `$or` ใน query เดียว) — เปลี่ยนจากข้อเสนอเดิม (prefer ทั้ง fault) เพราะนั่นจะเปลี่ยนขอบเขต tag filter ไปด้วยเป็น 2 ตัวแปร
- eval: เพิ่มบรรทัด `context by kind` (จำนวน chunk ต่อ kind + จำนวน fault ที่ไม่มี kind นั้นเลย) ไว้วัด diversity

**ผล: ไม่ผ่าน** — recall 62 → **28** facts, context 77 → **31** chunks · wrong_fault 6 → 2, golden bad 1 → 0, pool-precision 0.79 → 0.90 (สะอาดขึ้นเพราะเหลือน้อย)
- context by kind: mistake 30 / finding 1 / principle 0 / consequence 0 — principle และ consequence หายจาก**ทุก** fault (R0: 22 / 18 / 19 / 18 ครบทุก fault)
- สาเหตุ: **ระยะของแต่ละ kind อยู่คนละระดับ** query ถูกเขียนให้เหมือนประโยค mistake โดยตั้งใจ (บทเรียน v5) mistake จึงใกล้สุดเสมอ เช่น knee valgus best: mistake 0.034 · finding 0.045 · principle 0.090 · consequence 0.091 → cutoff 0.034 + 0.03 = 0.064 ตัด principle/consequence ทิ้งหมด · fact ที่ R0 เคยได้ หลุด 40 ตัว: margin 37 · quota 3
- ข้อสังเกต: ตัวกั้นที่แท้ของ `split` ไม่ใช่แค่โควตาต่อ kind แต่รวมถึง **margin ต่อ kind** ที่ทำหน้าที่ปรับระดับระยะของแต่ละ kind ให้เท่ากันด้วย — ถอดทั้งคู่พร้อมกันจึงพัง
- rank 146 เท่า R0 เป็นเรื่องบังเอิญ (ชุด fact ต่างกันฝั่งละ 47)

**diagnostic (ไม่ใช้ตัดสิน, monkeypatch ใน scratch ไม่ได้อยู่ใน repo):** สระเดียว งบรวม 9 ไม่มีโควตาต่อ kind แต่ margin และลำดับวัดจาก best ของ kind ตัวเอง (`score − best_kind`)
- recall 62 → **67** (+5), macro 0.26 → 0.29 · kind ครบทุก fault (mistake 20 / finding 20 / principle 28 / consequence 21)
- แต่ wrong_fault 6 → **9**, pool-precision 0.74 (−0.05 พอดีเส้น), golden hit 10 → **9/10** (partial squat: mistake 2 ตัวไม่ good)
- ได้: butt wink +2, knee valgus / shallow lunge / elbow flare / bicep partial ROM +1 · เสีย: partial squat −1
- wrong_fault/irrelevant ที่เพิ่มมาจาก **fault ที่มี fact น้อย** (hip sag 13, push-up partial ROM 13, back knee 15, elbow flare 5): R0 ใส่แค่ 6–7 ช่องเพราะโควตา+margin ต่อ kind กั้นไว้ แต่แบบนี้เติมครบ 9 ช่อง ช่องที่เกินจึงเป็นขยะ (back knee wrong_fault 2 → 3, push-up partial ROM 1 → 2, hip sag 0 → 1)
- ทิศทาง: งบรวมช่วย fault ที่มี fact เยอะ แต่ต้องมีตัวกันไม่ให้เติมช่องเกินเมื่อ fact น้อย — ตรงกับงานของ reranker (R6: ตัดด้วยคะแนนความเกี่ยวข้อง ไม่ใช่ระยะ)

**ข้อสรุป:** R3 (MMR) ต้องมี R2 ก่อน → ข้ามไปด้วย ถัดไป R4 (multi-query what / why / fix) — query แยกตามคำถามจะทำให้ principle/consequence ใกล้สุดใน query ของตัวเองได้ ซึ่งแก้ต้นเหตุที่ระยะต่าง kind ไม่เท่ากัน หลัง R4 (และ R6) ค่อยลองสระเดียว + MMR ซ้ำ

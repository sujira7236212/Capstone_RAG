# Ablation log — RAG v2 (เปลี่ยนทีละอย่าง)

แผน: `docs/rag_v2_ablation_plan.md` · กติกา: หนึ่งขั้น = หนึ่งตัวแปร เทียบกับขั้นล่าสุดที่เก็บไว้

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
| R4 | `--queries profile` (what / why / fix, margin เทียบ best ของแต่ละ query) | 10/10 · 0.48 · **0** | **0.16** (0.21) / 0.27 — **66**/411 (+4) | 65 / 6 / 81 | 0.80 | 0 · 10 · 108 · 17 · 210 | **เก็บ** (default ใหม่) |
| R5 | `--hybrid` (BM25 ใน Python, BM25_K 12, BM25_WEIGHT 0.03) | 10/10 · 0.46 · **1** | 0.16 (0.21) / 0.26 — **65**/411 (−1 vs R4) | 64 / **8** / 81 | 0.79 | 0 · 10 · 71 · 17 · 248 | **revert** |
| R6 | `--rerank` (bge-reranker-v2-m3, gate sigmoid ≥ 0.5) | — | — | — | — | — | **เลื่อน** (เครื่องไม่พอ ยังไม่ได้วัด) |

รายงานเต็ม: B0 `compare_output/ablation/ablation_B0_retrieval.md` · R0 `compare_output/ablation/ablation_R0_retrieval.md` · R1 `compare_output/ablation/ablation_R1_retrieval.md` · R2 `compare_output/ablation/ablation_R2_retrieval.md` · R4 `compare_output/ablation/ablation_R4_retrieval.md` · R5 `compare_output/ablation/ablation_R5_retrieval.md`

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
- ctx wrong_fault 6 ตัวตาม judge (golden นับ bad 1) — ต้องให้คนตรวจตาม `compare_output/retrieval/relevance_pool_spotcheck.md`

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

### R3 — `--mmr λ` → ข้าม
ต้องมี R2 (สระเดียว) ก่อน R2 ไม่ผ่าน จึงข้าม ย้ายไปลองหลัง R4/R6 (ดูแผน)

### R4 — `--queries profile` (2026-09-26) → เก็บ, default ใหม่
**เปลี่ยน:** `QUERIES` ใน `test_rag_compare.py` (flag `--queries fault|profile` ทั้งใน `test_rag_compare.py` และ `eval/eval_retrieval.py`)
- `QUERY_PROFILE` = 3 query ต่อ fault: what = query เดิมจาก taxonomy · why = `"Harmful consequences, injury risk and joint stress caused by: {q}"` · fix = `"How to correct it, coaching cues and corrective exercises for: {q}"` — template เดียวทุก fault ตั้งก่อนรัน ไม่ได้จูน ถ้อยคำคนละแบบกับ query why/fix ที่ใช้สร้าง relevance pool (กันวนวงกลม)
- ทุก query ไปทุก kind (`_search_multi()`) · กฎ tag `prefer` ต่อ kind เหมือนเดิม · แต่ละ query top-12 ของตัวเอง · ระยะดิบข้าม query เทียบกันไม่ได้ (บทเรียน R2) จึงให้คะแนน chunk = ระยะที่ห่างจาก best **ของ query นั้น** เอาค่าน้อยสุดข้าม query → ผ่าน margin ถ้าอยู่ใน margin ของ query ใด query หนึ่ง · โควตาต่อ kind เท่าเดิม · มี query เดียว = `_search()` ทุกประการ (`--queries fault` ได้ report ตรงกับ R0 ต่างแค่ header)
- ฝั่ง flawless (ไม่มี error) และ `--raw-query` ไม่เปลี่ยน (ใช้ query เดียวเหมือนเดิม)

**ผล: ผ่านทุกข้อ** — recall 62 → **66** facts (+4), macro 0.26 → 0.27, wrong_fault 6 = 6, golden bad 1 → **0**, pool-precision 0.79 → 0.80 · kind ครบทุก fault (mistake 25 / finding 19 / principle 19 / consequence 18)
- miss: rank 146 → 108, margin 34 → 17, quota 159 → **210** — query เพิ่มแล้วเจอของดีมากขึ้น แต่ช่องต่อ kind เต็ม ตัวกั้นหลักตอนนี้คือโควตา
- context 77 → 81 chunk (budget 9 เท่าเดิม — fault ที่เคยเหลือช่องว่างได้ของเพิ่ม เช่น hip sag, push-up partial ROM)
- chunk ที่เข้ามาใหม่เป็นเนื้อหาแนว why/fix ที่แผนต้องการ: "medial-knee displacement … was corrected when a 2-inch lift was placed under the heels" (วิธีแก้ knee valgus) · "Limitations in adductor extensibility … cause valgus knee collapse" (สาเหตุ) · "Knees caving in … commonly associated with overactive adductors…" · "Squatting with the spine in a flexed position increases the risk of disc herniation" · "A lunge with a shorter step length results in joint forces almost two times higher"
- ที่เสียจริง: "The target depth for the trailing knee was defined as 2 to 3 cm short of contacting the ground." (back knee, ตัวเลขเฉพาะ) · "Descend until the top of the thigh is at least parallel…" (partial squat principle) · partial squat finding เปลี่ยนจาก relevant เป็น irrelevant 1 ตัว
- wrong_fault เท่าเดิมแต่เปลี่ยนตัว: ออก preacher curl (elbow flare, golden BAD) และ "Knee valgus … during the lunge" (back knee) · เข้า "Using a narrow-width hand position can restrict the elbow joint's range of motion" (push-up partial ROM) และ principle "trunk leaned forward increases the hip extensor impulse" (trunk lean — judge ให้ wrong_fault)
- unlabeled 1 ตัว (back knee consequence ทั่วไป "Lunges performed without optimal technique can create unnecessary joint stress…")
- **golden precision 0.61 → 0.48 (good 36 → 30, neutral 22 → 33)** — ไม่ใช่เกณฑ์ ส่วนใหญ่เป็นการสลับ relevant → relevant ที่ตัวใหม่ไม่ตรง `must_hit` (pattern เขียนตามถ้อยคำ v4) เช่น "Maintain a neutral low back position with a slight lordosis" แทน "…neutral, lordotic lumbar position…" · ถ้าจะใช้ golden precision ต่อ ต้องเพิ่ม phrasing ใน `golden_chunks.json` ก่อน
- session mode (mock 4 session แบบที่ generation ใช้, ไม่มี pool): golden bad 1 → 0, good 22 → 16 (สาเหตุเดียวกับข้างบน)
- ข้อจำกัด: relevance pool สร้างจาก 4 query ที่มีแนว why/fix อยู่แล้ว (ถ้อยคำต่างกัน) ตัวหารจึงครอบคลุมของที่ query why/fix หาเจอดีกว่าของที่ไม่มี query ไหนหา — ไม่ใช่ปัญหากับการเทียบ R0 ↔ R4 แต่ควรรู้ไว้
- ไม่ได้ทำ generation mini-check (ต้องมี `--samples N` ก่อน — ค้างใน G1)

### R5 — `--hybrid` (2026-09-26) → revert (default คง `HYBRID = False`) · เทียบกับ R4
**เปลี่ยน:** `HYBRID` ใน `test_rag_compare.py` (flag `--hybrid/--no-hybrid` ทั้งใน `test_rag_compare.py` และ `eval/eval_retrieval.py`) + โมดูลใหม่ `kb_bm25.py`
- **ต่างจากแผน:** แผนเสนอ Postgres full-text + index ใน `ingest.py` แต่ `ts_rank` ไม่มี IDF (คำว่า "squat" ใน corpus squat หนักเท่า "valgus") จึงไม่ใช่ BM25 จริง → ทำ Okapi BM25 ใน Python แทน (k1 1.2, b 0.75, IDF แบบ Lucene จาก chunk ทั้งหมดของท่านั้น, tokenizer `[a-z0-9]+` ตัด stopword ไม่ stem) โหลด text + metadata + embedding ของท่านั้นจาก `langchain_pg_embedding` ครั้งเดียวต่อ process (ท่าละ 348–783 chunk) · ไม่แตะ schema / index / `ingest.py`
- `_search_hybrid()`: สิทธิ์เข้าสระเดิม (tag `prefer` ต่อ kind) · candidate ต่อ query = vector top-12 ∪ BM25 top-12 (`BM25_K`) · margin ยังวัดจากระยะ vector (ตามแผน: margin อยู่จนถึง R6) · BM25 เปลี่ยนแค่**ลำดับ**ที่แย่งโควตา: key = (ระยะเหนือ best ของ query) − `BM25_WEIGHT` × (BM25 / BM25 สูงสุดของ query) น้อยสุดข้าม query · `BM25_WEIGHT` 0.03 = ความกว้าง margin (เหตุผลเดียวกับ TAG_BONUS) ตั้งก่อนรัน · text ของ BM25 = 3 query ของ R4
- ตรวจ implementation: `BM25_K = 0, BM25_WEIGHT = 0` ได้ report ตรงกับ R4 ต่างแค่ `best` 1 ช่อง 0.129 ↔ 0.128 (cosine ใน numpy float64 กับ pgvector float32) · default (`HYBRID = False`) ตรงกับ R4

**ผล: ไม่ผ่าน 3 ใน 4 ข้อ** — recall 66 → 65 (−1), wrong_fault 6 → **8**, golden bad 0 → **1**, pool-precision 0.80 → 0.79
- wrong_fault ที่กลับมา: preacher curl ใต้ elbow flare (golden BAD ตัวเดิมที่ R4 เพิ่งกำจัดได้) และ "Knee valgus and excessive side-to-side knee movement during the lunge…" ใต้ insufficient back knee flexion + finding "forward lean increases biceps femoris activity" ใต้ trunk lean
- สาเหตุ: คำที่ BM25 จับได้คือศัพท์อวัยวะ/ท่า ("knee", "elbow", "lunge", "curl") ซึ่ง fault ในท่าเดียวกันใช้ร่วมกัน keyword จึงแยก fault ไม่ออก ต่างจาก embedding ที่จับความหมายของอาการ
- ที่คาดว่า "เจอตัวเลขและชื่อเฉพาะมากขึ้น" ไม่เกิด: query ไม่มีตัวเลขหรือชื่อเฉพาะให้ BM25 จับ (ได้ "40 to 90 degrees" มา 1 เสีย "approximately 90 degrees" และ "0 to 90 degrees" ไป 2)
- ส่วนใหญ่เป็นการสลับ relevant ↔ relevant มีของดีบ้าง เช่น principle "Avoid excessive anterior movement of the upper torso…" แทน wrong_fault ใต้ trunk lean, "If the lunge step is too short, the front heel may come off the ground."

**แยกผล (ไม่ใช้ตัดสิน):**
| BM25_K · WEIGHT | recall | wrong_fault | golden bad | pool-precision |
|---|---|---|---|---|
| 0 · 0 (= R4) | 66 | 6 | 0 | 0.80 |
| 12 · 0 (เพิ่ม candidate อย่างเดียว) | 66 | 6 | 0 | 0.80 — context เหมือน R4 ทุกตัว |
| 0 · 0.03 (เรียงใหม่อย่างเดียว) | 65 | 8 | 1 | 0.79 — เท่ากับ R5 |
| 12 · 0.015 | 65 | 7 | 0 | 0.79 |
| 12 · 0.03 (R5) | 65 | 8 | 1 | 0.79 |
- candidate จาก BM25 ที่ผ่าน margin ได้ไม่เคยชนะโควตา (rank 108 → 71 แต่ไหลไป quota หมด) ความเสียหายทั้งหมดมาจากการเรียงตาม keyword · ไม่มีน้ำหนักไหนที่ recall ขึ้น

**ข้อสรุป:** บน KB นี้กับ query แบบบรรยายอาการ BM25 ไม่เพิ่มอะไร ถ้าจะลองอีกควรเป็นตอนมี query ที่มีตัวเลข/ชื่อเฉพาะ (เช่น dose, ชื่อ drill หลัง K2) · flag และ `kb_bm25.py` คงไว้ (default ปิด)

### R6 — `--rerank` (2026-09-26) → เลื่อน ยังไม่ได้วัด (เครื่องไม่พอ) · default คง `RERANK = False`
**ออกแบบไว้ (ตั้งก่อนรัน):** candidate เหมือน R4 ทุกอย่าง (3 query × vector top-12 ต่อ kind, tag `prefer`) · cross-encoder `BAAI/bge-reranker-v2-m3` ให้คะแนนคู่ (query, chunk) ทุก query เอาค่าสูงสุด · gate แทน `RELATIVE_MARGIN`: sigmoid(logit) ≥ `RERANK_MIN` 0.5 (= logit 0 เส้นแบ่งของโมเดลเอง) · เรียงตามคะแนน โควตาต่อ kind + near-dup เดิม · `ABS_DISTANCE_CAP` คงเป็น backstop · เลือก local cross-encoder เพราะไม่ใช่ตระกูลเดียวกับ judge ของ relevance pool (`gemini-3.8-flash`) · Gemini API ไม่มี endpoint rerank; Vertex AI Ranking API ต้องใช้ GCP project + billing + ADC (ไม่รับ API key)
- โค้ด: `RERANK` / `RERANK_MIN` + flag `--rerank` ใน `test_rag_compare.py` (ใน `_search_multi()`) และ `eval/eval_retrieval.py` (`--rerank`, `--rerank-min`) · โมดูลใหม่ `kb_rerank.py` (cache คะแนนใน `.cache/rerank/`, gitignored) · default ปิด → eval ได้ report ตรงกับ R4 (ต่างแค่ header)

**ติดอะไร:** เครื่อง dev มี RAM 5.9 GB · commit limit 23.9 GB (RAM + page file 18 GB) ถูกใช้ไป ~21.7 GB จากหลายโปรแกรมรวมกัน (Docker/WSL 1.1 GB, VS Code 1.5 GB, antivirus 0.85 GB, …) เหลือว่าง ~2 GB
1. น้ำหนัก fp32 2.27 GB: safetensors map ไฟล์แบบ copy-on-write ซึ่ง Windows คิดเต็มขนาดกับ commit → "paging file is too small" (os error 1455) · แก้: `kb_rerank._fp16_dir()` แปลงเป็น fp16 (1.14 GB, `.cache/models/`) ด้วยการอ่านไฟล์ทีละ 64 MB — ทำงานได้ (15 วินาที)
2. ติดตั้ง `torch==2.13.0+cu126` (แทนตัว CPU) เพื่อรันบน GTX 1650 4 GB — `torch.cuda.is_available()` True, arch มี sm_75 · หลังตัดสินใจเลื่อน R6 ถอยกลับเป็น `torch==2.13.0+cpu` แล้ว (คืนพื้นที่ดิสก์)
3. โหลด fp16 ผ่าน transformers ยังโดน error 1455 (DLL ของ CUDA กิน commit ไปแล้ว) · แก้: สร้างโมเดลบน meta device แล้วอ่านน้ำหนักเองทีละ 32 MB ส่งขึ้น GPU (`_read_tensors()`)
4. ยังโดน `CUDA out of memory` ตอนจองไป 827 MB ทั้งที่ GPU ว่าง 2.4 GB — บน Windows (WDDM) หน่วยความจำที่ CUDA จองถูกนับกับ commit ของระบบด้วย commit ที่เหลือจึงไม่พอ
- ทางที่ยังไม่ได้ลอง: ปิดโปรแกรมอื่นให้เหลือ commit ≥ ~1.5 GB แล้วโหลดใหม่ · `BAAI/bge-reranker-base` (278M ครึ่งหนึ่งของ v2-m3) · เครื่องที่ RAM มากกว่า · reranker แบบ hosted (Vertex / Cohere)
- **ยังไม่มีการโหลดโมเดลสำเร็จเลย** โค้ดส่วน `_get_model()` / `_predict()` จึงยังไม่ได้ผ่านการทดสอบจริง ต้อง smoke test ก่อนใช้ (คู่ relevant ต้องได้คะแนนสูงกว่าคู่ protocol sentence ชัดเจน)

**ผลต่อแผน:** leave-one-out หลัง R6 (ลอง union / สระเดียว + MMR ซ้ำ) เลื่อนตาม · ขั้นที่เก็บล่าสุดยังเป็น **R4** · เหตุผลที่ข้ามได้: ตัวกั้นหลักตอนนี้คือโควตาต่อ kind (210) และ KB ขาดเนื้อหา dose/drill ซึ่ง reranker แก้ไม่ได้ · ถ้าเครื่อง deploy สเปกใกล้เครื่องนี้ reranker 568M ก็ใช้จริงไม่ได้อยู่ดี

### G1 — checkpoint generation R0 ↔ R4 (2026-09-26) → เครื่องมือเสร็จ ยังไม่ได้รันเต็ม (รอ user อนุมัติค่า API)
**เครื่องมือที่สร้าง:**
- `test_rag_compare.py --samples N`: retrieval ครั้งเดียว generate N ครั้งจาก context เดียวกัน · report ใช้หัว `### WITH RAG (sample i/N)` (N = 1 ได้หัวเดิม) · เขียน JSON คู่กับ report (`<out>.json`: payload ที่ model เห็น, context, metrics, ทุก sample, config retrieval, sha1 ของ system prompt) บันทึกหลังจบทุก session
- `eval/eval_generation.py` อ่าน report หลาย sample ได้ (เดิมเก็บแค่ตัวสุดท้าย) สรุปเป็นค่าเฉลี่ยต่อคำตอบ · report sample เดียวได้ผลเท่าเดิมทุกบรรทัด (ตรวจกับ `compare_result_per_fault_v12.md`) · เพิ่ม test ใน `test_eval_generation.py`
- `eval/judge_pairwise.py`: judge `gemini-3.8-flash` @ 0 (คนละรุ่นกับ generator `gemini-3.5-flash-lite` แต่ตระกูลเดียวกัน — มี key แค่ Gemini) · จับคู่ sample i ของ A กับ sample i ของ B ใน session เดียวกัน · สลับตำแหน่งแบบสุ่ม `Random(seed|label|i)` · judge ไม่รู้ว่าข้างไหนเป็น run ไหน · เกณฑ์ SportsGPT 4 ด้าน (Accuracy / Comprehensiveness / Professionalism / Feasibility — นิยามตามเปเปอร์: interpretation correctness / inference depth / expert-level specificity / actionability of quantitative details) + overall แบบ pairwise และคะแนน 1–5 (รอง) · สรุปด้วย sign test (ตัด tie) · session ที่ context เหมือนกันสองข้างแยกเป็น **control** · มี position check · cache คำตัดสินใน `<out>.json` (รันต่อได้)
- `--reference none|union`: `none` = judge เห็นแค่ session + สองคำตอบ (แบบ SportsGPT) · `union` = เห็น entry จาก context ของทั้งสอง run ด้วย (ตัด header, ไม่ซ้ำ, สลับลำดับ ไม่บอกว่ามาจาก run ไหน)

**context R0 ↔ R4 ต่อ session (mock per-fault):** ต่างกันทุก fault session (10/10) แต่ต่างแค่ 1–5 chunk จาก 7–9 (knee valgus ต่างมากสุด: R0 เท่านั้น 4 / R4 เท่านั้น 5 · push-up partial ROM: R4 เพิ่ม 1 ตัว ไม่เสียอะไร) · clean session context เหมือนกันทุกตัว → ใช้เป็น control

**smoke test (ไม่ใช้ตัดสิน, ไฟล์อยู่ scratch ไม่ได้เก็บ):** knee valgus + clean session × 2 sample × 2 config
- ทุกส่วนทำงานครบ (report → JSON → judge → report · eval_generation อ่านหลาย sample ได้)
- **เจอปัญหาของ judge แบบไม่มี context:** chunk ใหม่ของ R4 "medial-knee displacement … was corrected when a 2-inch (5.08-cm) lift was placed under the heel" → generator แนะนำ "วาง lift 2 นิ้วใต้ส้นเท้า" ทั้ง 2 sample → judge บอกว่า "excessive, unrealistic", "bizarre" และให้ R0 ชนะทุกด้าน (2/2) · judge ที่ไม่เห็นหลักฐานตัดสินด้วยความรู้ทั่วไปของตัวเอง ซึ่งก็คือความรู้ที่ no-RAG มีอยู่แล้ว → เอียงต่อต้าน fact เฉพาะจาก KB ที่ดูแปลก · (ข้อสังเกตด้วย: chunk นั้นเป็นผลของ**การทดสอบ** ankle mobility ไม่ใช่ใบสั่งฝึก — generator แปลงเป็นคำแนะนำเอง ซึ่งเป็นปัญหาฝั่ง prompt/P-step ได้ด้วย)
- user เลือก: รัน judge **ทั้งสองแบบ** (none + union) บนคู่เดียวกัน

**เกณฑ์อ่านผล G1 (ตั้งก่อนรัน):**
- ตัวหลัก = `overall` ของ 50 คู่ใน 10 fault session (5 sample × 10) · sign test สองทาง ตัด tie
- "R4 ทำให้คำตอบดีขึ้น" = R4 ชนะมากกว่า และ p < 0.05 **ทั้งสองแบบ judge** · "แย่ลง" = R0 ชนะ p < 0.05 ทั้งสองแบบ · ถ้าสองแบบไม่ตรงกัน = ผลขึ้นกับว่า judge เห็นหลักฐานไหม (รายงานพร้อมเหตุผลของ judge ว่าตัดสินด้วย fact ตัวไหน) · นอกนั้น = "แยกไม่ออกที่ n = 5"
- control (clean session 5 คู่) ควรออกใกล้ครึ่ง ๆ · position check ควรใกล้ 50% ถ้าไม่ใช่ ให้ลดน้ำหนักผลหลัก
- ประกอบ (ไม่ใช้ตัดสิน): 4 ด้านแยก, คะแนน 1–5, `eval_generation.py` (jargon ต่อคำตอบ, longest shared n-gram เฉลี่ย)
- G1 **ไม่ revert R4** (R4 ผ่านเกณฑ์ retrieval แล้ว) ถ้า R4 แย่ลง ให้ดูว่า chunk ไหนที่ generator ใช้ผิด → ป้อนเข้าขั้น P (prompt) ไม่ใช่ขั้น R

**ค่าใช้จ่ายรันเต็ม:** generation 11 session × 5 × 2 config = 110 call `gemini-3.5-flash-lite` (~45–50 นาทีเพราะ sleep 15 วินาที) + judge 55 คู่ × 2 แบบ = 110 call `gemini-3.8-flash` (prompt ~10–12k ตัวอักษร)

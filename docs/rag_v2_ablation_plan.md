# แผนปรับ RAG v2 — เปลี่ยนทีละอย่าง วัดทุกขั้น

> ไฟล์สำหรับเปิดทำต่อใน session ใหม่ · อัปเดตล่าสุด 2026-09-26 · สถานะ: **ขั้น 0 เสร็จ (commit `928b4a3`, `062ec47`, `8737754`) · R0 เก็บ (`49863f5`) · R1 ไม่ผ่าน (`960e4c9`) · R2 ไม่ผ่าน (`31a65bc`) · R3 ข้าม · **R4 เก็บ = default ปัจจุบัน (`36b456e`)** · R5 ไม่ผ่าน (`2ff454b`) · R6 เลื่อน เครื่องไม่พอ (`f4272fc`) — ขั้น R จบที่ R4 · **G1: เครื่องมือเสร็จ + smoke test แล้ว รอ user อนุมัติรันเต็ม** ถัดไป: ดู §0**
> ผลทุกขั้นบันทึกใน `compare_output/ablation_log.md`

## 0. เริ่มต่อจากตรงนี้ (session ใหม่)

1. อ่านไฟล์นี้ แล้วอ่าน `compare_output/ablation_log.md` (รายละเอียด + ตัวเลขของทุกขั้น) · ทุกคำสั่งและกับดักอยู่ใน §5
2. **retrieval ปัจจุบัน = R4** — default ใน `test_rag_compare.py` คือ `--tag-mode prefer --kind-pool split --queries profile --no-hybrid --no-rerank` · ตัวเลขฐานที่ขั้นถัดไปต้องเทียบ = §4 คอลัมน์ R4 (`compare_output/ablation_R4_retrieval.md`)
3. **B0 สร้างซ้ำไม่ได้แล้ว** (R0 แก้ `fault_tags` ใน DB) → baseline เก่าที่สุดที่รันได้คือ R0 = `--queries fault` (report ตรงกับ `ablation_R0_retrieval.md` ทุกบรรทัด ต่างแค่ header)
4. ขั้นถัดไป (เลือกอันเดียว ตามกติกา §2):
   - **G1 — กำลังทำ** ยังไม่เคยวัดฝั่ง generation เลยตั้งแต่เริ่มแผน ต้องรู้ก่อนว่า recall 62→66 ของ R4 ทำให้คำตอบดีขึ้นจริงไหม · เครื่องมือเสร็จแล้ว (`--samples N`, `eval/judge_pairwise.py`) · smoke test ผ่าน · เกณฑ์อ่านผลตั้งไว้แล้วใน `ablation_log.md` §G1 · **เหลือ: รันเต็มเมื่อ user อนุมัติ** (คำสั่งอยู่ใน Checkpoint G1 ใน §3) แล้วจดผล
   - **C1** แยก config (refactor ผลต้องเท่าเดิม)
   - **K1/K2** เพิ่ม facet / เนื้อหา dose-drill — ต้นเหตุหลักที่ RAG ไม่ชนะ no-RAG (KB ไม่มี prescription/dose)
5. R6 (reranker) ค้างเพราะเครื่อง — ไม่ต้องรอ ดู §4

## 1. ที่มา

**ปัญหาเดิม:** ผล `compare_output/compare_result_per_fault_v12.md` (prompt v11, KB `kb_gemini_curated_v5`) ฝั่ง RAG ไม่ชนะ no-RAG ชัดเจน อ่านเปเปอร์ 4 ฉบับใน `C:\Users\HP\Documents\RAG_paper` แล้วได้ข้อสรุปว่า RAG จะชนะเมื่อส่ง**ความรู้เชิงปฏิบัติที่ LLM ทั่วไปไม่มี** เช่น drill + dose, สาเหตุ→วิธีแก้, ตัวเลข ตัวอย่างจาก SportsGPT: ตัด RAG ออกแล้ว Feasibility ตกจาก 3.9 เหลือ 1.65 ส่วน Accuracy แทบไม่ตก

**ข้อสงสัยของ user ที่เปลี่ยนทิศทางของแผน:**
1. การแบ่ง slot ตาม kind (`mistake/finding/principle/consequence`) ทำให้ข้อมูลที่ควรได้ตกหล่นไหม → **ยืนยันแล้วด้วย B0** (ดูข้อ 4): ที่หลุดส่วนใหญ่หลุดเพราะ quota และ rank ต่อ kind
2. ถ้าสร้าง kind ใหม่ให้ตรงกับ output ของ prompt (cue/drill/cause/dose) พอเปลี่ยน prompt ก็ต้องรื้อ retrieval ทั้งหมด → **จึงไม่ทำ kind ใหม่** ใช้แนวทางที่ตกลงกันแทน:
   - ค้นจากสระเดียว และหาความหลากหลายแบบนุ่ม (MMR) แทนโควตาตายตัว
   - ย้ายสิ่งที่ prompt ต้องการไปไว้ใน config (`retrieval_profile.yaml`)
   - เก็บ facet เป็น metadata หลายค่าที่ retag ได้โดยไม่ต้อง re-extract หรือ re-embed
   - **อัปเดตหลัง R2/R4:** สระเดียว + margin เดียวใช้ไม่ได้ (ระยะของแต่ละ kind อยู่คนละระดับ query ทรง mistake ทำให้ kind อื่นหลุดหมด) → ได้ความหลากหลายจาก multi-query (R4) แทน · สระเดียว + MMR รอ reranker (R6)
3. ให้**เปลี่ยนทีละอย่าง** เพื่อรู้ว่าขั้นไหนทำให้ดีขึ้นหรือแย่ลง

## 2. กติกาการทดลอง

1. **หนึ่งขั้น = หนึ่งตัวแปร = หนึ่ง commit** ทำเป็น flag ใน CLI (default = พฤติกรรมเดิม) เพื่อสลับ A/B และ revert ได้ · ขั้นที่**เก็บ** ให้เปลี่ยน default เป็นพฤติกรรมใหม่ (แบบ R4) · ขั้นที่ไม่ผ่านเก็บ flag ไว้ default ปิด · ทุกขั้นต้องเช็กว่า default ยังได้ report ตรงกับขั้นที่เก็บล่าสุด (ต่างแค่ header)
   - ตั้งค่าพารามิเตอร์ใหม่ (น้ำหนัก, threshold, template) **ก่อนรัน** และจดเหตุผล ห้ามจูนจากผล eval · sweep ค่าอื่นได้แต่จดเป็น "ไม่ใช้ตัดสิน"
2. **แต่ละขั้นวนแบบนี้:** implement ข้อเดียว → รัน eval → จดผล → ตัดสินใจเก็บหรือ revert → **หยุดรายงาน user** → ค่อยเริ่มข้อถัดไป เทียบกับ "ขั้นล่าสุดที่เก็บไว้" ไม่ใช่เทียบกับ B0
3. **เกณฑ์เก็บขั้น retrieval** (ต้องผ่านทุกข้อ):
   - recall ขึ้น
   - ctx wrong_fault ไม่เพิ่ม
   - golden bad ไม่เพิ่ม
   - pool-precision ไม่ต่ำกว่าขั้นก่อนเกิน 0.05
   - เทียบที่ budget เดียวกันเสมอ (ดู ceiling)
4. **Generation** วัดเฉพาะที่ checkpoint (มี noise จาก temperature 0.7 และเสียเงิน) ใช้ n=5 ต่อ session กับ pairwise judge แบบ blind หลังแต่ละขั้น R จะทำ mini-check ก็ได้: n=3 เฉพาะ session ที่ context เปลี่ยน
5. **ห้ามเปลี่ยน retrieval กับ prompt ในรอบเดียวกัน** ระหว่างขั้น R ให้คง header ของ context `[kind | re: … | source: …]` ไว้ prompt v11 จะได้ไม่ต้องแก้
6. commit แยกตามเรื่อง ข้อความ commit ตามสไตล์ใน repo (หัวข้อสั้น + ย่อหน้าเหตุผล + `Co-Authored-By`) และ commit เฉพาะเมื่อ user สั่ง

## 3. ขั้นตอน

### ขั้น 0 — เครื่องมือวัด ✅ เสร็จ
- `test_rag_compare._search()` / `retrieve_kb_blocks()` มี `trace=` (optional) บอกเหตุผลของ candidate ทุกตัว (kept / quota / margin / dup) โดย kept set ไม่เปลี่ยน
- `eval/build_relevance_pool.py` สร้าง candidate ต่อ fault = chunk ที่ tag ตรง (normalize ขีดล่างแล้ว) ∪ top-40 ของ 4 query ที่ไม่ filter kind/tag จากนั้นให้ judge `gemini-3.8-flash` ติดป้าย relevant / wrong_fault / irrelevant
  - judge prompt อยู่ที่ **v2** ป้ายผูกกับ `JUDGE_PROMPT_VERSION` ถ้าแก้ prompt ให้ bump เวอร์ชัน แล้วระบบจะ relabel ใหม่เอง
- `eval/eval_retrieval.py --pool eval/relevance_pool.json` (เป็นค่า default) วัดสิ่งเหล่านี้:
  - recall ต่อ fact (cluster ด้วย near-dup แบบเดียวกับ gate)
  - ceiling ที่ budget 9 chunk
  - ป้ายของ chunk ใน context
  - เหตุผลที่หลุด (tag_spelling / tag_filter / rank / margin / quota / dup)

### ขั้น R — retrieval (ทีละข้อ ตามลำดับ)

| ขั้น | flag | เปลี่ยนแค่ | คาดว่า |
|---|---|---|---|
| **R0** ✅ เก็บ (recall 61→62 facts, tag_spelling 14→0) | (แก้ข้อมูล ไม่ใช่ flag) | normalize `fault_tags` ใน DB: `\|knee_valgus\|` → `\|knee valgus\|` ฯลฯ แก้แค่ metadata ไม่ re-embed · backup แถวที่แก้ลง `data_pipeline/backups/` ก่อน แบบเดียวกับ `fix_ocr_degrees.py` · ต้องแก้ต้นทางด้วย (`curator.py` หรือ `ingest.py`) กันไม่ให้กลับมาอีก | tag_spelling 14 → 0 · recall ↑ เล็กน้อย (partial squat, bicep partial ROM) |
| R1 ❌ revert (recall 62→57, golden bad 1→2, pool-precision 0.79→0.71) | `--tag-mode union` | tag จากแบบเลือกทางเดียว → union ของสระที่มี tag กับไม่มี tag + boost/penalty (`TAG_BONUS` 0.03) | tag_filter ↓ · wrong_fault ต้องไม่ ↑ |
| R2 ❌ revert (recall 62→28, context 77→31 เหลือแต่ mistake) | `--kind-pool single` | เลิกแบ่งสระตาม kind (งบรวมเท่าเดิม = 9 + near-dup) | quota/rank ↓ · diversity อาจ ↓ |
| R3 ⏭ ข้าม (ต้องมี R2) | `--mmr λ` | MMR เพื่อความหลากหลาย (ต้องมี R2 ก่อน) | diversity กลับมา |
| R4 ✅ เก็บ (recall 62→66, golden bad 1→0) | `--queries profile` | multi-query (what / why / fix) | recall ↑ |
| R5 ❌ revert (recall 66→65, wrong_fault 6→8, golden bad 0→1) | `--hybrid` | เพิ่ม BM25 (ทำใน Python `kb_bm25.py` แทน Postgres full-text เพราะ `ts_rank` ไม่มี IDF) | เจอตัวเลขและชื่อเฉพาะมากขึ้น |
| R6 ⏸ เลื่อน (RAM 6 GB / commit ไม่พอโหลด bge-reranker-v2-m3 แม้ fp16 บน GPU — ดู log §R6) | `--rerank` | reranker แทน `RELATIVE_MARGIN` | precision ↑ |

ถ้าข้อไหนไม่ผ่านให้ revert แล้วไปข้อถัดไป **(เลื่อนไปพร้อม R6)** หลัง R6 ให้ทดสอบถอด R3 อีกรอบ (leave-one-out) เพราะ reranker อาจทำให้ MMR ไม่จำเป็น และลอง `--kind-pool single` + MMR ซ้ำ (R2 พังเพราะ query ทรง mistake ทำให้ระยะของ kind อื่นไกลกว่าเสมอ — R4 แยก query ตามคำถามน่าจะแก้ต้นเหตุ ส่วนเติมช่องขยะใน fault ที่ fact น้อยเป็นงานของ R6) และลอง `--tag-mode union` ซ้ำ เพราะสิ่งที่ทำให้ R1 แพ้ (ประโยค protocol ของงานวิจัยที่ไม่มี tag แย่งช่อง `finding`) คือสิ่งที่ reranker ควรกดลง

**Checkpoint G1 ← กำลังทำ (เครื่องมือเสร็จ รอรันเต็ม):** ดูว่า retrieval ที่ดีขึ้นทำให้คำตอบดีขึ้นจริงไหม
- เทียบ RAG ของ **R4 (default)** กับ **R0 (`--queries fault`)** — ไม่ใช่ B0 (สร้างซ้ำไม่ได้, ดู §0) · prompt v11 เดิม (`SYSTEM_PROMPT` ใน `test_rag_compare.py`) · mock `mock_data/mock_sessions_per_fault.json` (10 fault + 1 clean session) · LLM `gemini-3.5-flash-lite` @ 0.7 · n=5 ต่อ session (กติกา §2 ข้อ 4)
- เครื่องมือ ✅ (รายละเอียด `ablation_log.md` §G1):
  1. `--samples N` ใน `test_rag_compare.py` — generate N ครั้งจาก context เดียว + JSON คู่กับ report (`<out>.json`) · `eval_generation.py` อ่าน report หลาย sample ได้
  2. `eval/judge_pairwise.py` — blind pairwise, judge `gemini-3.8-flash`, เกณฑ์ SportsGPT 4 ด้าน + overall, sign test, control = session ที่ context เหมือนกัน (clean session), position check · `--reference none|union` (user เลือกรันทั้งสองแบบ — judge ที่ไม่เห็นหลักฐานลงโทษ fact จาก KB ที่ดูแปลก ดู log)
- คำสั่งรันเต็ม (เสียค่า API: 110 generation + 110 judge call):
  ```
  python test_rag_compare.py --mock mock_data/mock_sessions_per_fault.json --queries fault --samples 5 --skip-no-rag --out g1_R0.md
  python test_rag_compare.py --mock mock_data/mock_sessions_per_fault.json --samples 5 --skip-no-rag --out g1_R4.md
  python eval/judge_pairwise.py compare_output/g1_R0.json compare_output/g1_R4.json --names R0 R4 --reference none  --show-reasons --out compare_output/g1_pairwise_none.md
  python eval/judge_pairwise.py compare_output/g1_R0.json compare_output/g1_R4.json --names R0 R4 --reference union --show-reasons --out compare_output/g1_pairwise_union.md
  python eval/eval_generation.py compare_output/g1_R0.md compare_output/g1_R4.md --mock mock_data/mock_sessions_per_fault.json --out compare_output/g1_generation.md
  ```
- ใช้ `eval/eval_generation.py` (unglossed jargon + longest shared n-gram กับ context) ประกอบได้ · generation เสียค่า API ทุกครั้ง แจ้ง user ก่อนรันเต็ม

### ขั้น C — แยก config (refactor ต้องได้ผลเท่าเดิม)
- C1 ย้าย `QUERY_PROFILE` (query template), งบ (`MAX_PER_KIND`, `CANDIDATE_K`, `RELATIVE_MARGIN`) และ default ของ flag (`TAG_MODE`, `KIND_POOL`, `QUERIES`, `HYBRID`, `RERANK`) จาก `test_rag_compare.py` ไปไว้ใน `retrieval_profile.yaml` แล้วรันซ้ำ **context ต้องเหมือนเดิมทุกตัว** — report ของ `eval_retrieval.py` ต้องตรงกับ `ablation_R4_retrieval.md` (ต่างแค่ header)

### ขั้น P — prompt (ทีละข้อ แต่ละข้อเป็น checkpoint generation)
- **P1** อธิบาย Context โดยไม่ผูกกับ kind (แก้ bug ที่ "How to read the Context" ขาด `consequence` ไปด้วย)
- **P2** `<evidence_plan>`: ให้ model เลือกเองว่า fact ไหนไปช่องไหน โค้ดตัดบล็อกนี้ออกก่อนแสดงผล
- **P3** distinctiveness rule: ต่อ error ต้องมีอย่างน้อย 1 ข้อเฉพาะจาก context
- **P4** dosed plan: ปริมาณการฝึกต้องมาจาก context เท่านั้น
- **P5** ภาษาแบบ SDT (ไม่ใช้น้ำเสียงสั่ง, ให้ทางเลือก 2 ทาง, มีเป้าให้ติดตามตัวเอง)
- **P6** worked example 1 ชิ้น ในท่าที่ระบบไม่ได้ grade (บทเรียนจาก v11)

### ขั้น K — KB
- **K1** retag facet บน item เดิม (`data_pipeline/retag_facets.py`) แบบ multi-label: definition, cause, consequence, correction, drill, dose, number, muscle
- **K2+** เพิ่มเนื้อหาทีละแหล่ง แล้ววัด retrieval ตามด้วย generation checkpoint **ต้องสร้าง relevance pool ใหม่ทุกครั้งที่มี chunk ใหม่** ลำดับแหล่งที่แนะนำ:
  1. dose/progression: ACSM Position Stand *Progression Models in Resistance Training* (2009), NSCA *Essentials*, Helms 2016 (RIR)
  2. drill/regression ต่อ fault: NSCA *Exercise Technique Manual*, FIFA 11+ / Myer-Hewett สำหรับ valgus, McGill สำหรับ hip sag
  3. cause → test → fix: knee-to-wall / weight-bearing lunge test, FMS, Macrum 2012
  4. cue แบบ external focus (Wulf)
  5. EMG ว่ากล้ามเนื้อไหนทำงานแทน (bicep elbow flare ยังเป็น data gap)
  6. expert QA pairs จากผู้เชี่ยวชาญของระบบ 1
- หลัง K2 (มี dose / ชื่อ drill / ตัวเลขใน KB) ลอง `--hybrid` (R5) ซ้ำ — R5 แพ้เพราะ query ไม่มีตัวเลขหรือชื่อเฉพาะให้ BM25 จับ มีแต่ศัพท์อวัยวะที่ทุก fault ในท่าเดียวกันใช้ร่วมกัน

## 4. ผลปัจจุบัน — R4 (ขั้นล่าสุดที่เก็บไว้ · gate v7 + multi-query, KB v5 หลังแก้ tag)

| ตัววัด | B0 | R0 | **R4** |
|---|---|---|---|
| golden (hit · precision · bad) | 10/10 · 0.62 · 1 | 10/10 · 0.61 · 1 | 10/10 · 0.48 · **0** |
| recall micro (ceiling) / macro | 0.15 (0.21) / 0.26 — 61 จาก 411 facts | 0.15 (0.21) / 0.26 — 62 จาก 411 facts | **0.16** (0.21) / 0.27 — 66 จาก 411 facts |
| context | 77 chunks: relevant 60 / wrong_fault 6 · pool-precision 0.78 | 77 chunks: relevant 61 / wrong_fault 6 · pool-precision 0.79 | 81 chunks: relevant 65 / wrong_fault 6 · pool-precision 0.80 |
| miss by reason | tag_spelling 14 · tag_filter 10 · rank 141 · margin 34 · quota 151 | tag_spelling 0 · tag_filter 10 · rank 146 · margin 34 · quota 159 | tag_filter 10 · rank 108 · margin 17 · **quota 210** |

- R1 ไม่ผ่าน (รายละเอียด `ablation_log.md` §R1): union ดึง tag_filter กลับมาได้แค่ 1 ใน 10 fact แต่เสีย 6 fact ที่ quota ให้ `finding` ไม่มี tag ที่เป็นประโยค protocol ของงานวิจัย ("A successful squat trial in this protocol required ≥60° knee flexion") → filter แบบ exclusive มีประโยชน์กับ `finding` · `TAG_BONUS` 0.06/0.10 = recall เท่า R0 (ไม่ขึ้น) wrong_fault 5
- R2 ไม่ผ่าน (รายละเอียด `ablation_log.md` §R2): margin เดียวจาก best รวม = best ของ mistake เสมอ (query ทรง mistake) → principle/consequence หลุด margin ทุก fault · diagnostic ที่วัด margin จาก best ของ kind ตัวเอง: recall 67 (+5) แต่ wrong_fault 6→9 จากการเติมช่องให้ครบ 9 ใน fault ที่ fact น้อย → โควตา+margin ต่อ kind ของเดิมกันขยะได้จริง
- R4 เก็บ (รายละเอียด `ablation_log.md` §R4): query what/why/fix + margin เทียบ best ของแต่ละ query ได้ chunk แนวสาเหตุ/วิธีแก้เพิ่ม (heel lift แก้ knee valgus, adductor ตึง) · ตัวกั้นหลักตอนนี้คือ quota (210) · golden precision 0.61→0.48 เป็นเพราะ `must_hit` ยังเป็นถ้อยคำ v4 ต้องเพิ่ม phrasing ถ้าจะใช้ต่อ
- R5 ไม่ผ่าน (รายละเอียด `ablation_log.md` §R5): BM25 จับศัพท์อวัยวะ/ท่าที่ fault ในท่าเดียวกันใช้ร่วมกัน → ดึง wrong_fault กลับมา (preacher curl ใต้ elbow flare) · candidate จาก BM25 ไม่เคยชนะโควตา ความเสียหายมาจากการเรียงตาม keyword ล้วน ๆ
- R6 เลื่อน (รายละเอียด `ablation_log.md` §R6): ออกแบบ + โค้ดเสร็จ (`kb_rerank.py`, `--rerank`, default ปิด) แต่โหลดโมเดลไม่สำเร็จบนเครื่องนี้ — `.venv` ถอยกลับเป็น `torch==2.13.0+cpu` แล้ว (คืนพื้นที่ดิสก์) · ถ้ากลับมาทำบน GPU: `pip install "torch==2.13.0+cu126" --index-url https://download.pytorch.org/whl/cu126 --no-deps` (~2.5 GB) + ปิดโปรแกรมอื่นให้ commit ว่าง ≥ ~1.5 GB · smoke test `kb_rerank.scores()` ก่อน แล้วเทียบกับ R4 · ทางเลือกถ้าเครื่องยังไม่พอ: `bge-reranker-base` หรือ reranker แบบ hosted (ไม่ใช่ตระกูล Gemini)
- **ขั้นที่เก็บล่าสุด = R4** ขั้นถัดไปที่ไม่ต้องรอ R6: Checkpoint G1 (เครื่องมือเสร็จ รอรันเต็ม), C1, K1/K2
- ตารางต่อ fault: `compare_output/ablation_{B0,R0,R1,R2,R4,R5}_retrieval.md` (R6 ยังไม่มี)
- R0: chunk ที่ tag ถูกแล้ว 14 ตัว เข้า context 2 ตัว ที่เหลือหลุดที่ quota/rank แทน → ตัวกั้นจริงคือ slot ต่อ kind
- R0 แก้ metadata แล้ว **id ของแถวเปลี่ยน** ตาม metadata (สูตรเดียวกับ `ingest.py`) ถ้าจะแก้ metadata ใน DB อีก ให้ใช้วิธีเดียวกับ `data_pipeline/fix_fault_tags.py` ไม่อย่างนั้น ingest ครั้งหน้าจะ embed แถวนั้นซ้ำ
- chunk wrong_fault 6 ตัวใน context **ของ R0** ตรวจด้วยตาแล้ว สมเหตุสมผลทุกตัว เช่น preacher curl ใต้ elbow flare และเข่า**หน้า** 80° ใต้ insufficient back knee flexion · R4 ยังได้ 6 แต่สลับไป 2 ตัว (preacher curl ออก, narrow-hand push-up + trunk-lean principle เข้า — ดู log §R4) ตัวใหม่ยังไม่ได้ตรวจด้วยตา
- **ข้อจำกัด:** near-dup (Jaccard 0.72) รวม paraphrase ที่ใช้คำต่างกันไม่ได้ recall จึงต่ำกว่าความจริง แต่ใช้เทียบระหว่างขั้นได้เพราะตัวหารเท่ากัน

## 5. วิธีรัน + กับดัก

```
docker ps                                                   # ต้องเห็น pgvector-db (localhost:5432)
python eval/eval_retrieval.py --mode single --show-missed --out compare_output/ablation_<step>_retrieval.md
python eval/build_relevance_pool.py                         # เฉพาะเมื่อ KB เปลี่ยน หรือ judge prompt เปลี่ยน (~20 นาที)
python eval/test_eval_generation.py                         # ต้องผ่านทุก commit
python test_rag_compare.py --mock mock_data/mock_sessions_per_fault.json --out compare_result_per_fault_<ver>.md
                                                            # generation RAG vs no-RAG (เสียค่า API; --skip-no-rag = ฝั่ง RAG อย่างเดียว;
                                                            #   --samples N = N คำตอบต่อ session + JSON ข้าง report)
python eval/judge_pairwise.py <A>.json <B>.json --names A B --reference none|union --out compare_output/<name>.md
                                                            # blind pairwise judge (เสียค่า API; cache คำตัดสินใน <name>.json)
```

flag ของ retrieval (ใช้ได้ทั้ง `test_rag_compare.py` และ `eval/eval_retrieval.py`; ค่าหลังลูกศร = default ปัจจุบัน):
- `--queries fault|profile` → `profile` (R4) · `fault` = R0
- `--tag-mode prefer|union` → `prefer` · `--kind-pool split|single` → `split` · `--hybrid/--no-hybrid` → ปิด · `--rerank/--no-rerank` → ปิด
- เฉพาะ eval: `--margin`, `--cap`, `--max-per-kind`, `--rerank-min`, `--mode single|session|both`, `--pool ''` (ข้าม recall)
- summary ของ eval มีบรรทัด `context by kind` (จำนวน chunk ต่อ kind + fault ที่ไม่มี kind นั้นเลย) ไว้ดู diversity

- ใช้ `.venv/Scripts/python.exe` และตั้ง `PYTHONIOENCODING=utf-8`
- Bash tool ทำ backslash หาย → ข้อความหรือโค้ดที่มี `\` ให้เขียนด้วย Edit/Write tool
- สคริปต์ชั่วคราวที่ต่อ DB ต้องเรียก `load_dotenv(".env")` แบบระบุ path (`load_dotenv()` เปล่า ๆ พังตอนรันผ่าน stdin)
- ถ้าเจอ `DATABASE_URL not set` แปลว่ายังไม่ได้โหลด `.env` ถ้าเจอ connection timeout แปลว่า Docker ยังไม่ได้เปิด
- **เครื่อง dev มี RAM 5.9 GB** และ commit memory ว่างแค่ ~2 GB ตอนเปิด Docker + VS Code — โมเดล local ขนาด ≥ 1 GB (เช่น reranker) โหลดไม่ขึ้น ดู log §R6
- git เตือน `LF will be replaced by CRLF` ตอน commit ไฟล์ .md/.py — ไม่เป็นไร

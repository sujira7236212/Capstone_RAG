# แผนปรับ RAG v2 — เปลี่ยนทีละอย่าง วัดทุกขั้น

> ไฟล์สำหรับเปิดทำต่อใน session ใหม่ · อัปเดตล่าสุด 2026-09-25 · สถานะ: **ขั้น 0 เสร็จ (commit `928b4a3`, `062ec47`, `8737754`) · R0 เสร็จ เก็บ (commit `49863f5`) · R1 ไม่ผ่าน revert (flag คงไว้ default `prefer`) · R2 ไม่ผ่าน revert (flag คงไว้ default `split`) · R3 ข้าม · **R4 เก็บ (default `--queries profile`)** — ถัดไป R5**
> ผลทุกขั้นบันทึกใน `compare_output/ablation_log.md`

## 1. ที่มา

**ปัญหาเดิม:** ผล `compare_output/compare_result_per_fault_v12.md` (prompt v11, KB `kb_gemini_curated_v5`) ฝั่ง RAG ไม่ชนะ no-RAG ชัดเจน อ่านเปเปอร์ 4 ฉบับใน `C:\Users\HP\Documents\RAG_paper` แล้วได้ข้อสรุปว่า RAG จะชนะเมื่อส่ง**ความรู้เชิงปฏิบัติที่ LLM ทั่วไปไม่มี** เช่น drill + dose, สาเหตุ→วิธีแก้, ตัวเลข ตัวอย่างจาก SportsGPT: ตัด RAG ออกแล้ว Feasibility ตกจาก 3.9 เหลือ 1.65 ส่วน Accuracy แทบไม่ตก

**ข้อสงสัยของ user ที่เปลี่ยนทิศทางของแผน:**
1. การแบ่ง slot ตาม kind (`mistake/finding/principle/consequence`) ทำให้ข้อมูลที่ควรได้ตกหล่นไหม → **ยืนยันแล้วด้วย B0** (ดูข้อ 4): ที่หลุดส่วนใหญ่หลุดเพราะ quota และ rank ต่อ kind
2. ถ้าสร้าง kind ใหม่ให้ตรงกับ output ของ prompt (cue/drill/cause/dose) พอเปลี่ยน prompt ก็ต้องรื้อ retrieval ทั้งหมด → **จึงไม่ทำ kind ใหม่** ใช้แนวทางที่ตกลงกันแทน:
   - ค้นจากสระเดียว และหาความหลากหลายแบบนุ่ม (MMR) แทนโควตาตายตัว
   - ย้ายสิ่งที่ prompt ต้องการไปไว้ใน config (`retrieval_profile.yaml`)
   - เก็บ facet เป็น metadata หลายค่าที่ retag ได้โดยไม่ต้อง re-extract หรือ re-embed
3. ให้**เปลี่ยนทีละอย่าง** เพื่อรู้ว่าขั้นไหนทำให้ดีขึ้นหรือแย่ลง

## 2. กติกาการทดลอง

1. **หนึ่งขั้น = หนึ่งตัวแปร = หนึ่ง commit** ทำเป็น flag ใน CLI (default = พฤติกรรมเดิม) เพื่อสลับ A/B และ revert ได้
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

| ขั้น | flag (เสนอ) | เปลี่ยนแค่ | คาดว่า |
|---|---|---|---|
| **R0** ✅ เก็บ (recall 61→62 facts, tag_spelling 14→0) | (แก้ข้อมูล ไม่ใช่ flag) | normalize `fault_tags` ใน DB: `\|knee_valgus\|` → `\|knee valgus\|` ฯลฯ แก้แค่ metadata ไม่ re-embed · backup แถวที่แก้ลง `data_pipeline/backups/` ก่อน แบบเดียวกับ `fix_ocr_degrees.py` · ต้องแก้ต้นทางด้วย (`curator.py` หรือ `ingest.py`) กันไม่ให้กลับมาอีก | tag_spelling 14 → 0 · recall ↑ เล็กน้อย (partial squat, bicep partial ROM) |
| R1 ❌ revert (recall 62→57, golden bad 1→2, pool-precision 0.79→0.71) | `--tag-mode union` | tag จากแบบเลือกทางเดียว → union ของสระที่มี tag กับไม่มี tag + boost/penalty (`TAG_BONUS` 0.03) | tag_filter ↓ · wrong_fault ต้องไม่ ↑ |
| R2 ❌ revert (recall 62→28, context 77→31 เหลือแต่ mistake) | `--kind-pool single` | เลิกแบ่งสระตาม kind (งบรวมเท่าเดิม = 9 + near-dup) | quota/rank ↓ · diversity อาจ ↓ |
| R3 ⏭ ข้าม (ต้องมี R2) | `--mmr λ` | MMR เพื่อความหลากหลาย (ต้องมี R2 ก่อน) | diversity กลับมา |
| R4 ✅ เก็บ (recall 62→66, golden bad 1→0) | `--queries profile` | multi-query (what / why / fix) | recall ↑ |
| **R5** ← ถัดไป | `--hybrid` | เพิ่ม BM25 (Postgres full-text + index ใน `ingest.py`) | เจอตัวเลขและชื่อเฉพาะมากขึ้น |
| R6 | `--rerank` | reranker แทน `RELATIVE_MARGIN` | precision ↑ |

ถ้าข้อไหนไม่ผ่านให้ revert แล้วไปข้อถัดไป หลัง R6 ให้ทดสอบถอด R3 อีกรอบ (leave-one-out) เพราะ reranker อาจทำให้ MMR ไม่จำเป็น และลอง `--kind-pool single` + MMR ซ้ำ (R2 พังเพราะ query ทรง mistake ทำให้ระยะของ kind อื่นไกลกว่าเสมอ — R4 แยก query ตามคำถามน่าจะแก้ต้นเหตุ ส่วนเติมช่องขยะใน fault ที่ fact น้อยเป็นงานของ R6) และลอง `--tag-mode union` ซ้ำ เพราะสิ่งที่ทำให้ R1 แพ้ (ประโยค protocol ของงานวิจัยที่ไม่มี tag แย่งช่อง `finding`) คือสิ่งที่ reranker ควรกดลง

**Checkpoint G1:** รัน generation ของ retrieval ที่ดีที่สุดเทียบกับ B0 ด้วย prompt v11 เดิม เพื่อดูว่า retrieval ที่ดีขึ้นทำให้คำตอบดีขึ้นจริงไหม ต้องมี `--samples N` ใน `test_rag_compare.py` และ `eval/judge_pairwise.py` ก่อน (ยังไม่ได้ทำทั้งสองอย่าง)

### ขั้น C — แยก config (refactor ต้องได้ผลเท่าเดิม)
- C1 ย้าย query template และงบไปไว้ใน `retrieval_profile.yaml` แล้วรันซ้ำ **context ต้องเหมือนเดิมทุกตัว**

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
- **R5 ต้องเทียบกับ R4** (`compare_output/ablation_R4_retrieval.md`: recall 66/411 · wrong_fault 6 · golden bad 0 · pool-precision 0.80) ใต้ default ปัจจุบัน (`--tag-mode prefer --kind-pool split --queries profile`)
- ตารางต่อ fault: `compare_output/ablation_B0_retrieval.md`, `compare_output/ablation_R0_retrieval.md`
- R0: chunk ที่ tag ถูกแล้ว 14 ตัว เข้า context 2 ตัว ที่เหลือหลุดที่ quota/rank แทน → ตัวกั้นจริงคือ slot ต่อ kind
- R0 แก้ metadata แล้ว **id ของแถวเปลี่ยน** ตาม metadata (สูตรเดียวกับ `ingest.py`) ถ้าจะแก้ metadata ใน DB อีก ให้ใช้วิธีเดียวกับ `data_pipeline/fix_fault_tags.py` ไม่อย่างนั้น ingest ครั้งหน้าจะ embed แถวนั้นซ้ำ
- chunk wrong_fault ทั้ง 6 ตัวใน context ตรวจด้วยตาแล้ว สมเหตุสมผลทุกตัว เช่น preacher curl ใต้ elbow flare และเข่า**หน้า** 80° ใต้ insufficient back knee flexion
- **ข้อจำกัด:** near-dup (Jaccard 0.72) รวม paraphrase ที่ใช้คำต่างกันไม่ได้ recall จึงต่ำกว่าความจริง แต่ใช้เทียบระหว่างขั้นได้เพราะตัวหารเท่ากัน

## 5. วิธีรัน + กับดัก

```
docker ps                                                   # ต้องเห็น pgvector-db (localhost:5432)
python eval/eval_retrieval.py --mode single --show-missed --out compare_output/ablation_<step>_retrieval.md
python eval/build_relevance_pool.py                         # เฉพาะเมื่อ KB เปลี่ยน หรือ judge prompt เปลี่ยน (~20 นาที)
python eval/test_eval_generation.py                         # ต้องผ่านทุก commit
```

- ใช้ `.venv/Scripts/python.exe` และตั้ง `PYTHONIOENCODING=utf-8`
- Bash tool ทำ backslash หาย → ข้อความหรือโค้ดที่มี `\` ให้เขียนด้วย Edit/Write tool
- สคริปต์ชั่วคราวที่ต่อ DB ต้องเรียก `load_dotenv(".env")` แบบระบุ path (`load_dotenv()` เปล่า ๆ พังตอนรันผ่าน stdin)
- ถ้าเจอ `DATABASE_URL not set` แปลว่ายังไม่ได้โหลด `.env` ถ้าเจอ connection timeout แปลว่า Docker ยังไม่ได้เปิด

# บันทึกการคุย 2026-09-12 — Progress update, flow, การวัดผล และข้อสงสัยเรื่อง taxonomy

**สถานะ ณ วันเขียน:** KB `kb_local_curated_v4` (2,432 รายการ) · gate v7 · prompt v8 "practical" · eval single 9/10 · bad 9 · precision 0.70
**เอกสารที่อ้างถึง:** `docs/kb_quality_assessment.md`, `docs/error_type_taxonomy.md`, `compare_output/*.md`

---

## 1. เครื่องมือที่มี (stack + ไฟล์)

| ชั้น | ไฟล์ | ทำอะไร |
|---|---|---|
| แหล่งข้อมูล | `data/<ท่า>/` (PDF + `urls.txt`) | 37 แหล่ง: squat 7 · lunge 12 · push-up 9 · bicep-curl 9; ที่คัดออกอยู่ `excluded_from_kb/` 29 ไฟล์ |
| Curate | `data_pipeline/curator.py` | Gemini structured-output ต่อ window 6,000 ตัวอักษร → `is_relevant / core_principles / common_mistakes / specific_findings / applies_to_fault`; URL ดึงด้วย trafilatura; window ที่ท่าไม่ตรงโฟลเดอร์ → `excluded_from_kb/`; `normalize_ocr_degrees()` |
| Ingest | `ingest.py` | 1 item = 1 Document + metadata `exercise_id / item_kind / source / text` → pgvector (Docker `pgvector/pgvector:pg16`) embed ด้วย `all-MiniLM-L6-v2` local |
| Mapping layer | `error_taxonomy.py` | `(exercise_id, code)` → `query / aliases / rule_th / display_th / focus_area`; `resolve()` fallback + log code ที่ไม่รู้จัก; `LEGACY_CODES` |
| Pipeline หลัก | `test_rag_compare.py` | retrieval gate + `SYSTEM_PROMPT` + `gemini-3.5-flash-lite @0.7`; flags `--mock --raw-query --collection --out --skip-no-rag`; รายงานมี config + metrics + context จริง + output |
| วัดผล | `kb_coverage.py` | "KB มีของสำหรับ fault นี้ไหม" — นับ chunk ≤ 0.40 ต่อ fault, raw/expanded, เทียบหลาย collection |
| | `eval/eval_retrieval.py` + `eval/golden_chunks.json` | ไม้บรรทัดหลัก — ให้คะแนน chunk ที่ gate ปล่อยเข้า context เป็น good/bad/neutral; single/session mode; override `--margin --cap --max-per-kind --collection` |
| Utility | `fix_ocr_degrees.py`, `test_normalize_ocr_degrees.py`, `migrate_exclude_mismatches.py`, `rescue_false_mismatches.py` | one-off patch / migration (backup ใน `data_pipeline/backups/`) |
| Mock | `mock_data/mock_sessions.json` | 4 session (squat, lunge, push-up ไม่มี error, bicep) ใช้ code ชุดกฎจริง 10 ตัว |

KB collection: `kb_local_curated` (JSON blob) → v2 (2,837) → v3 (2,519) → **v4 (2,432)**

---

## 2. Flow ปัจจุบัน (อธิบายแบบไม่ต้องรู้โค้ด)

### ช่วง A — สร้างคลังความรู้ (ทำครั้งเดียว / ทำเมื่อเพิ่มข้อมูล)

- **A1 รวบรวมแหล่ง** — งานวิจัย PDF + บทความเว็บ แยกโฟลเดอร์ตามท่า 4 ท่า
- **A2 ให้ LLM อ่านแล้วสกัดความรู้** (`curator.py`) — ตัดเป็นช่วง ~6,000 ตัวอักษร ส่ง Gemini ตอบเป็นแบบฟอร์ม: เกี่ยวกับการแก้ฟอร์มไหม (`is_relevant`), หลักการทำถูก, ข้อผิดพลาด, ตัวเลข/ผลวิจัยที่อ้างได้; ถ้าเป็นท่าอื่น → คัดออก
- **A3 แปลงเป็นเวกเตอร์เก็บลง DB** (`ingest.py`) — 1 ประโยค = 1 รายการ ติดป้ายท่า/ชนิด/แหล่ง → PostgreSQL + pgvector

### ช่วง B — ตอนผู้ใช้ออกกำลังกายเสร็จ (ทำทุก session)

- **B1 รับ session JSON** จากระบบตรวจท่า (อีกทีม): rep ไหนถูก/ผิด, `error_type`, คะแนน, ผลครั้งก่อน
- **B2 แปลงชื่ออาการเป็นคำค้น** (`error_taxonomy.py`) — `Butt wink` → "Lumbar flexion (butt wink): posterior pelvic tilt and rounding of the lower back at the bottom of the squat"
- **B3 ค้นคลัง** (`test_rag_compare.py`) — ต่อ error ค้น 3 รอบ (mistake / finding / principle) กรองท่า+ชนิดใน DB; คัดด้วย distance ≤ min(0.40, best + 0.06); ตัดซ้ำ Jaccard ≥ 0.72; โควตา 3/2/2
- **B4 ประกอบ context** — `[kind | re: <error> | source: <ชื่อ>]` + ประโยค
- **B5 ให้ LLM เขียน feedback** — prompt "โค้ชในยิม": ความคืบหน้า / ต่อ error: คืออะไร-ทำไมสำคัญ-วิธีแก้ (cue, setup, drill, self-check)-rep ไหน / แผนครั้งหน้า 2–3 ข้อ; กติกา: ห้ามอ้างตัวเลข/แหล่งที่ไม่มีใน context, ห้ามเขียนแบบอ้างอิง, เมิน entry ที่ไม่ตรง error
- **B6 บันทึกรายงาน** `compare_output/*.md` — config, metrics, context จริง, output

ถ้า session ไม่มี error → ค้น `principle` ด้วย "`<ท่า>` correct technique and biomechanics"

### โมเดลที่ใช้

| ใช้ทำอะไร | โมเดล | เหตุผล |
|---|---|---|
| สกัดความรู้ (A2) | `gemini-3.5-flash` @0.1 | อ่านยาว ตอบ JSON ตามฟอร์ม, temperature ต่ำเพื่อความสม่ำเสมอ |
| embedding (A3, B3) | `all-MiniLM-L6-v2` (local) | ฟรี เร็ว ใช้ตัวเดียวกันทั้งเก็บและค้น; จุดอ่อน: ไม่รู้ศัพท์คลินิกสั้น ๆ → ต้องมี B2 |
| เขียน feedback (B5) | `gemini-3.5-flash-lite` @0.7 | เร็ว/ถูก; 0.7 คงไว้ทุกรอบเพื่อเทียบข้ามรอบ |
| vector DB | PostgreSQL 16 + pgvector (Docker) | เก็บเวกเตอร์ + metadata ที่เดียว กรองใน DB ได้ |

---

## 3. ประวัติสิ่งที่ทำ (ย่อ)

| ช่วง | วันที่ | สิ่งที่ทำ |
|---|---|---|
| ตั้งระบบ | ส.ค.–2 ก.ย. | prompt สั้น → RAG ≈ no-RAG; ย้ายมา pgvector local + KB ที่ curate ด้วย LLM |
| แผน 4 ขั้น (v3–v5) | 5–6 ก.ย. | ingest 1 item/Document; exclude window ท่าผิด (35 windows/11 ไฟล์) → v3; retrieval gate; grounding rule → **พบ hallucination แต่งชื่อ study** |
| v6 ชุด P0 | 8 ก.ย. | `item_kind` filter ย้ายเข้า DB (bicep momentum 0→12); relative gate 0.20 + cap; ตัด prefix query; header `[kind|re|source]`; `error_taxonomy.py`; Jaccard dedup; เขียน `kb_quality_assessment.md` |
| KB v4 + กฎจริง | 11 ก.ย. | ถอดแหล่งนอกเรื่อง, บีบ `is_relevant`, trafilatura, `applies_to_fault`, +17 PDF, Wayback แทนลิงก์ NASM ตาย → 2,432; ได้ inventory กฎจริง 10 ข้อ → จัด taxonomy/mock ใหม่; A/B raw vs taxonomy |
| golden set + Step 1 | 11–12 ก.ย. | baseline v6 (bad 14) → แก้ query bicep ROM (bad 10) → gate v7 margin 0.06 (bad 9, precision 0.70) → prompt v7 relevance rule → OCR fix "1208"→"120°" → **prompt v8 practical** (ล่าสุด, ยังไม่ลง docs) |

---

## 4. การวัดผล — วัดอะไร ตรงขั้นตอนไหน

```
A2 curate ──► A3 KB ──► B2 query ──► B3 ค้น+คัด ──► B4 context ──► B5 LLM
              [①]        [②]           [③]                          [④]
```

| # | เครื่องมือ | คำถามที่ตอบ | วัดขั้น | ผลสำคัญ |
|---|---|---|---|---|
| ① | `kb_quality_assessment` | คลังมีของพอไหม / สะอาดไหม | A2/A3 | push-up ครอบคลุม fault ตัวเองไม่ได้, bicep finding = 0, มีของนอกเรื่องปน → KB v4 |
| ② | `kb_coverage.py` | ค้นด้วยคำนี้เจออะไร | B2 | raw vs expanded; **ตัวนับ usable หลอกได้** (query 2 คำห่างทุก chunk เท่า ๆ กัน) ต้องดูเนื้อหาด้วย |
| ③ | `eval_retrieval.py` + golden set | สิ่งที่เข้า context ถูก/ผิดกี่ตัว | B3/B4 | **ไม้บรรทัดหลัก** — แยกได้ว่าแต่ละตัวเลขดีขึ้นเพราะอะไร |
| ④ | รายงาน A/B `ab_*.md` | LLM พูดผิดอะไรบ้าง | B5 | ประโยคผิด 4 → 0 ยืนยัน + 1 hedge; principle grounded 3/3; วัดเป็นตัวเลขไม่ได้เพราะ temp 0.7 |

**ตัวเลข ③ ต่อรอบ (single, KB v4)**

| ขั้น | hit | bad | precision |
|---|---|---|---|
| baseline v6 | 8/10 | 14 | 0.51 |
| + query bicep partial ROM | 9/10 | 10 | 0.60 |
| + gate v7 (margin 0.06, cap 0.40, principle ต่อ error) | 9/10 | 9 | 0.70 |
| + OCR fix | 9/10 | 9 | 0.70 (ไม่เปลี่ยน — ถูกต้อง) |

bad 9 ที่เหลือ: lunge back-knee ×5 (KB ไม่มีของ) + finding/principle ระยะเท่าตัวถูก ×4 (prompt เมินได้)

---

## 5. ทำไมต้องแปลง error_type เป็น query — ทดสอบจริงไหม

**ลำดับจริง: วัด → ทำ → วัดซ้ำกับชื่อจริง**

- **รอบแรก (8 ก.ย.)** mock ใช้ code ที่เขียนเป็น "คำสั่ง" (`Keep back straight` 0.574 → ได้ chunk ผิด; เขียนเป็นชื่ออาการ 0.228 → ถูก) เพราะค้นในโซน mistake ด้วย query แบบ "ท่าที่ถูก" → สร้าง taxonomy
- **รอบสอง (11 ก.ย.)** ได้ชื่อกฎจริง → ทดสอบส่งดิบผ่าน `--raw-query`:

| fault | raw usable (best) | expanded usable (best) |
|---|---|---|
| Butt wink | **0 (0.601)** | 13 (0.120) |
| Elbow flare | **0 (0.438)** | 9 (0.057) |
| Hip sag (finding) | **0 (0.682)** | 1 (0.357) |
| Partial squat | 21 (0.329) *ผิดหมด* | 1 (0.258) ตรง |
| Knee valgus | 15 (0.218) ✅ | 32 (0.154) |
| Excessive forward trunk lean | 1 (0.143) ✅ | 5 (0.256) |

ผ่าน pipeline จริง: `Butt wink` ได้ 0 chunk; `Elbow flare` ได้ "Swinging the elbows" จาก case report rhabdomyolysis ติดป้าย Elbow flare; `Partial squat` ได้ heels lifting / generic stance / progressing too early — ผิดทั้ง 3

**สรุป:** ชื่อดิบบางตัวใช้ได้ (บังเอิญ curator ใช้คำเดียวกัน) บางตัวใช้ไม่ได้เลย และที่อันตรายกว่า "หาไม่เจอ" คือ "หาเจอแต่ผิดแล้วติดป้ายว่าถูก" — taxonomy คือการคุมถ้อยคำ query ไว้ฝั่งเรา ไม่พึ่ง string ที่ upstream ส่ง

---

## 6. เรามั่นใจได้ยังไงว่า query ตรงความหมาย error_type — ตอบตรง ๆ: ยังไม่มีใครภายนอกยืนยัน

| ชั้นหลักฐาน | ค้ำอะไรได้ | ค้ำอะไรไม่ได้ |
|---|---|---|
| inventory จากทีมระบบ 1 (`rule_th`, ชื่ออังกฤษ, alias, expert/web) | กฎชื่ออะไร มีกี่ข้อ | กฎวัดมุมอะไรจริง — ยังไม่ได้อ่าน `form_rules.py` |
| นิยามมาตรฐานของศัพท์ | query บรรยายอาการที่ชื่อนั้นหมายถึง | ชื่อนั้นตรงกับสิ่งที่กฎวัดไหม |
| golden set + eval | query ↔ KB สอดคล้อง | error_type ↔ query ถูกความหมาย (วงกลม — เราตัดสินเองว่า chunk ไหนถูก) |

**จุดน่าสงสัยที่พบ:**
- **squat `knee valgus`**: `rule_th` = "เข่าไม่เลยปลายเท้า" (เข่าเลื่อนไปหน้า, sagittal) แต่ `query` = "knees caving inward" (เข่าบิดเข้า, frontal) — **คนละอาการ** ถ้ากฎวัดระยะเข่า-ปลายเท้า context ที่ดึงมาผิดทั้งหมดแม้ eval จะสวย
- `butt wink` `display_th` "หลังค่อม / หลังแอ่น" — butt wink คือ flexion อย่างเดียว ถ้ากฎ "มุมของหลัง" จับทั้งสองทิศ query ครอบคลุมครึ่งเดียว
- กฎ web 7/10 ข้อ ตัวเลขใน query (เช่น "90 degrees") เราใส่เอง ไม่รู้ threshold จริง

**สิ่งที่จะทำให้มั่นใจได้ (เรียงตามต้นทุน):** (1) ขอ `form_rules.py` อ่านทีละกฎเทียบ query (2) ให้ PT ดูตาราง §5.1 ใน `docs/error_type_taxonomy.md` (3) ถาม string ที่ส่งจริง (4) แก้ golden set ให้สอดคล้อง

---

## 7. query ลอกจาก KB เป๊ะ ๆ ไหม — ไม่ (exact match 0/10)

เขียนเอง แต่เลียนสไตล์/คำหลักของประโยคใน KB แล้ววัด — Jaccard กับ mistake ที่ใกล้สุด:

| fault | Jaccard | ประโยค KB ที่ใกล้สุด |
|---|---|---|
| bicep elbow flare | 0.71 | Allowing the elbows to drift away from the body during the curl. |
| push-up hip sag | 0.62 | Allowing the hips to sag |
| squat butt wink | 0.56 | Lumbar flexion (butt wink) at the bottom of the squat. |
| squat knee valgus | 0.50 | Knees collapsing inward (valgus collapse) during the squat. |
| bicep partial ROM | 0.46 | Failing to achieve a full range of motion at the elbow joint. |
| lunge trunk lean | 0.36 | Leaning the torso forward or backward. |
| lunge back knee | 0.36 | *(ไม่มีตัวที่เกี่ยว)* |
| push-up partial ROM | 0.35 | Failing to achieve the correct depth of 90 degrees elbow flexion. |
| squat partial squat | 0.26 | Squatting too shallow, failing to bring the thighs at least parallel… |
| lunge shallow | 0.25 | Lunge step is too short or too long. |

รูปแบบ: query = ชื่ออาการ + รวมหลายสำนวนของ KB ไว้ในประโยคเดียว (เช่น "flare outward **or** drift away") ให้ตกกลางระหว่างสำนวน
**นัยยะ:** เพราะ query ถูกจูนเข้าหา KB ถ้าตีความ error_type ผิดตั้งแต่ต้น (เคส knee valgus) การจูนจะพาไปหา chunk ผิดอาการอย่างแม่นยำ — ข้อ 6 จึงสำคัญขึ้น ไม่ใช่เบาลง; 3 ตัวล่างซ้อนทับต่ำเพราะ KB ไม่มีของ → รายการ v5

---

## 8. ถ้า KB v5 ดีและตรงจุด เลิกใช้ taxonomy ได้ไหม — ได้แค่ครึ่งเดียว

| ปัญหา | KB เพิ่มแก้ได้ไหม |
|---|---|
| A. KB ไม่มีของ (lunge back-knee, bicep finding) | ✅ |
| B. ชื่อสั้นค้นไม่เจอแม้ KB มีของ — `Butt wink` 0.601 **ทั้งที่ KB มี "Lumbar flexion (butt wink) at the bottom of the squat"** | ❌ ปัญหาอยู่ที่ความยาว/รูปประโยค query ไม่ใช่เนื้อหา |

ส่วน **query** ของ taxonomy ลดความสำคัญได้ถ้า: (1) v5 tag `applies_to_fault` ต่อ item ด้วย code 10 ตัว → กรองด้วย tag ก่อน semantic แค่จัดอันดับ (2) เปลี่ยน embedding ใหญ่ขึ้น (`gemini-embedding-2` มีโค้ดใน `ingest.py`) — ยังไม่ทดสอบ
ส่วนที่ **ยังต้องมี** ไม่ว่า KB ดีแค่ไหน: string ของ upstream → code เรา (ไทย/code/alias), รายการปิดที่ curator/retrieval/eval ใช้ร่วมกัน, `display_th`, `focus_area`, log code ที่ไม่รู้จัก

---

## 9. ร่างคำอธิบาย KB สำหรับรายงาน

ข้อเท็จจริง: 37 แหล่ง / 4 ท่า · ~2/3 peer-reviewed (EMG, kinematics, biomechanics) · ~1/3 องค์กรวิชาชีพ/เว็บฟิตเนส (NASM, ACE, Healthline) · สกัดเป็น 3 ชนิด 2,432 รายการ · คัดกรองรับเฉพาะเนื้อหาที่ใช้แก้ฟอร์มได้

> **Knowledge Base Collection**
> รวบรวมข้อมูลที่มีเนื้อหาทางวิชาการเป็นหลัก โดยเน้นงานวิจัยด้านชีวกลศาสตร์และการทำงานของกล้ามเนื้อ (EMG / kinematics) ของท่าออกกำลังกาย 4 ท่า ได้แก่ squat, lunge, push-up และ bicep curl รวม 37 แหล่ง ประกอบด้วยงานวิจัยที่ตีพิมพ์ในวารสารวิชาการเป็นส่วนใหญ่ เสริมด้วยบทความจากองค์กรวิชาชีพด้านการออกกำลังกาย (เช่น NASM, ACE Fitness) ในส่วนของข้อผิดพลาดที่พบบ่อยและแนวทางแก้ไข
>
> เนื้อหาที่คัดเลือกครอบคลุม 3 ด้าน คือ (1) การวิเคราะห์การทำงานของกล้ามเนื้อและมุมข้อต่อในแต่ละท่าและแต่ละรูปแบบการทำ (2) ข้อผิดพลาดของฟอร์มและผลกระทบทางชีวกลศาสตร์ต่อข้อต่อและกล้ามเนื้อ และ (3) หลักการทำท่าที่ถูกต้อง โดยตัดเนื้อหาที่ใช้ท่าออกกำลังกายเป็นเพียงเครื่องมือวัดผลด้านอื่น (เช่น ความเสี่ยงโรคหัวใจ ชีวเคมีในเลือด) ออก
>
> เอกสารทั้งหมดไม่ได้ถูกจัดเก็บทั้งฉบับ แต่ผ่านกระบวนการสกัดความรู้ด้วย LLM ให้เป็นข้อความสั้นที่จำแนกเป็น 3 ประเภท ได้แก่ หลักการทำท่าที่ถูกต้อง (core principles), ข้อผิดพลาดที่พบบ่อย (common mistakes) และผลการศึกษาเชิงตัวเลขที่อ้างอิงได้ (specific findings) รวม 2,432 รายการ แต่ละรายการมี metadata ระบุท่า ประเภท และแหล่งที่มา เพื่อให้ระบบค้นคืนกรองได้ตรงกับข้อผิดพลาดที่ตรวจพบ

ระวัง: อย่าเคลม "peer-reviewed ทั้งหมด" / "ผู้เชี่ยวชาญตรวจแล้ว" — ยังไม่มี PT ตรวจ KB และมีแหล่งอ่อน 1–2 ตัว (grokipedia, scribd lab manual) อยู่ในแผนคัดออก/แทนที่ใน v5

---

## 10. สิ่งที่ค้าง (รวมจากทั้ง session)

**Step 2 — KB v5**
1. `curator.py` tag `applies_to_fault` ต่อ item ด้วย code ใหม่ 10 ตัว → re-ingest
2. เติมข้อมูล: lunge back-knee (0 chunk ถูก), bicep finding ทั้ง 2 fault (0), squat partial mistake ถูกตัวเดียว, shallow lunge finding ดี 2 ตัวอยู่นอก cap 0.40, push-up hip sag mistake 2 ตัว
3. `eval_retrieval.py --collection v4 --collection v5` + sweep margin ใหม่

**ยืนยันความหมายกับทีมระบบ 1 / PT** (ข้อ 6) — โดยเฉพาะ knee valgus vs เข่าเลยปลายเท้า, string ที่ส่งจริง

**Generation (ตั้งใจยังไม่แตะ)** — temp 0.7, ไม่มี post-generation validation, ไม่มี reranker/hybrid, embedding ยัง MiniLM; prompt v8 รันรอบเดียวยังไม่มีเกณฑ์ผ่าน/ไม่ลง docs

**เฟสถัดไป** — health profile (`docs/future_user_health_profile.md`)

# แผนรับกฎใหม่ของระบบ 1 → KB v6

> ไฟล์สำหรับเปิดทำต่อใน session ใหม่ · อัปเดตล่าสุด 2026-09-27 · สถานะ: **พักไว้ — รอ user ยืนยันกฎและชื่ออาการผิดกับทีมระบบ 1**
> T1 ทำแล้ว (ยังไม่ commit, เป็นร่าง) · T2 เสร็จ · T3–T5 ยังไม่เริ่ม
> แผนนี้**มาก่อน**ขั้นที่ค้างอยู่ใน [`rag_v2_ablation_plan.md`](rag_v2_ablation_plan.md) (G1/C1/K1/P) เพราะรหัส fault เปลี่ยน ตัวเลข R4 เดิมจึงเทียบกับ KB ใหม่ไม่ได้

## 0. เริ่มต่อจากตรงนี้

1. ถาม user ว่ายืนยันกฎและชื่ออาการกับทีมระบบ 1 แล้วหรือยัง ผลที่ได้อาจเปลี่ยนข้อไหนได้บ้างดูที่ §3
2. ถ้ากฎ/ชื่อเปลี่ยนจากสเปก → แก้ `error_taxonomy.py` (T1) ให้ตรงก่อน แล้วรัน `python test_error_taxonomy.py`
3. ตอบคำถามที่ค้างใน §4 แล้วค่อยทำ T4 → curate เต็ม → T5 ตามลำดับ (§2)
4. สิ่งที่ยังไม่ได้ commit (working tree): `error_taxonomy.py`, `test_error_taxonomy.py`, `data_pipeline/test_normalize_fault_tags.py`,
   `docs/error_type_taxonomy.md` (§7 + หัวไฟล์), `.gitignore` (`data_duplicates/`), `docs/system1/RULES_AND_FSM_CONDENSED.md`, ไฟล์นี้
5. ⚠️ **ห้ามรัน eval retrieval/generation บน `kb_gemini_curated_v5` จนกว่าจะจบ T5** — taxonomy ใช้รหัสใหม่แล้ว แต่ KB v5 ยังติด tag เก่า
   ผลจะเพี้ยน (บางรหัสบังเอิญ match เพราะ `_` ใน SQL LIKE คือ wildcard ตัวเดียว เช่น `knee_valgus` ↔ `knee valgus` แต่ส่วนใหญ่ไม่ match)

## 1. ที่มา

ระบบ 1 เปลี่ยนชุดกฎ จาก 10 fault (snapshot 2026-09-11, `error_type_taxonomy.md` §5) เป็น **12 กฎ** ตามสเปก
[`docs/system1/RULES_AND_FSM_CONDENSED.md`](system1/RULES_AND_FSM_CONDENSED.md) (sync จากโค้ดของระบบ 1 เมื่อ 2026-09-25)
พร้อมกันนั้นมีข้อมูลใหม่ใน `data/` ซึ่งแยกโฟลเดอร์ย่อยตามชื่อกฎ (`data/squat/knee_valgus/…`) และมี `data/general/`

### 1.1 กฎเก่า → กฎใหม่ (จำนวน item ที่ติด tag ใน `curated_data_v5`)

| เดิม (§5) | ใหม่ | ความหมาย | items v5 |
|---|---|---|---|
| squat `partial squat` | `knee_depth` (>100°) | เปลี่ยนแค่ชื่อ | 85 |
| squat `knee valgus` | `knee_valgus` | เปลี่ยนแค่ชื่อ | 149 |
| squat `butt wink` (lumbar flexion) | `back_straight` = trunk tilt >35° ("not spine curvature") | **เปลี่ยน — map ไม่ได้** | 57 |
| — | squat `knee_varus` | **ใหม่** | 0 |
| push-up `hip sag` | `body_alignment` (sag **หรือ** pike) | กว้างขึ้น | 20 |
| push-up `partial range of motion` | `elbow_depth` (>110°) | เปลี่ยนแค่ชื่อ | 24 |
| lunge `shallow lunge` | `front_knee_too_shallow` | เปลี่ยนแค่ชื่อ | 88 |
| — | lunge `front_knee_too_deep` (<70°) | **ใหม่** | 0 |
| lunge `excessive forward trunk lean` | `torso_upright` (>20°) | เปลี่ยนแค่ชื่อ | 97 |
| lunge `insufficient back knee flexion` | `back_knee_form` | เปลี่ยนแค่ชื่อ | 20 |
| curl `elbow flare` | `elbow_away` (ออกข้าง/หน้า/หลัง) | กว้างขึ้นเล็กน้อย | 9 |
| curl `partial range of motion` | `full_rom` (55°/145°) | เปลี่ยนแค่ชื่อ | 64 |

v5 มีทั้งหมด 1,897 item · ไม่มี tag 1,314 item (squat 550, lunge 466) ซึ่งมี item เรื่องเข่าบานออกและ squat ลำตัวโน้มปนอยู่ แต่ไม่ได้ tag
เพราะตอน curate v5 ไม่มีกฎนี้

### 1.2 ข้อสรุปที่คุยกันแล้ว (2026-09-27)

- **curate ใหม่ทั้งหมด** แทน re-tag บน item เดิม (user เลือก) — curator เห็นทั้ง window ของต้นฉบับ ไม่ได้เห็นแค่ประโยคเดียว
  จึง tag ได้แม่นกว่า และ KB ทั้งหมดมาจาก prompt เดียวกันในรอบเดียว · ต้องสร้าง eval ใหม่อยู่แล้ว (รหัสเปลี่ยน) การเสียความเทียบกับตัวเลขเดิมจึงไม่เพิ่ม
  · ของที่แก้ตามหลังใน v5 ถูกรวมเข้า curator หมดแล้ว (OCR องศา, สะกด tag, mismatch ที่เชื่อ tag, ตัด grokipedia ออกจาก `urls.txt`)
- **สเปกของระบบ 1 ไม่ส่งเข้า curator** (LLM จะสรุปจนตัวเลขหาย) ใช้ 2 ทางแทน:
  1. เป็นที่มาของ `query` ใน `error_taxonomy.py` ซึ่ง curator ใช้เป็นคำอธิบายกฎตอน tag (ทำแล้วใน T1)
  2. ภายหลัง: "rule card" ต่อกฎใส่ตรงเข้า prompt ตอน generate (lookup จาก rule name) → เป็นขั้น P แยก
- **โฟลเดอร์ย่อยตามชื่อกฎใช้ได้** — `curator.py` / `ingest.py` ใช้ `os.walk` และ `exercise_id = rel_path.split(os.sep)[0]`

## 2. ขั้นตอน

### T1 — taxonomy ใหม่ ✅ ทำแล้ว (ร่าง ยังไม่ commit)
- `error_taxonomy.py`: key = rule name · `aliases[0]` = cue บนจอ · `LEGACY_CODES` แยกต่อท่า (§5 + ยุค v4) · **ไม่มี `butt wink`**
  · `resolve()` ถือ `_` = ช่องว่าง · `query` เดิมที่วัดแล้วคงไว้ เขียนใหม่เฉพาะ `back_straight`, `body_alignment`, `elbow_away`,
  `knee_varus`, `front_knee_too_deep`
- ทดสอบ: `python test_error_taxonomy.py` (17/17) · `python data_pipeline/test_normalize_fault_tags.py` (10/10)
- รายละเอียด: `docs/error_type_taxonomy.md` §7

### T2 — จัดการ `data/` ✅ เสร็จ
- ย้ายไป `data_duplicates/` (คงโครงโฟลเดอร์, อยู่ใน `.gitignore`): Coratella2023, Boyd2017, Marchetti2018, Rusin2018 (MD5 ตรงกับไฟล์ที่ root)
  และ Pedrosa2026 (เปเปอร์เดียวกับ "The interplay between muscle length…" ซึ่งเก็บไว้)
- "Varying Weightload…" user ลบเองแล้ว · "Core Muscle Activity…" ×2 และ "Biomechanics of the Push-up" ×2 **เก็บไว้ทั้งคู่** (user ตัดสิน)
- สเปกของระบบ 1 ย้ายจาก `data/rule and rep count/` ไปที่ `docs/system1/`
- โฟลเดอร์ว่าง `data/lunge/front_knee_too_shallow/`, `data/push-up/elbow_depth/` ปล่อยไว้ (ไม่มีผล)

### T4 — แก้ curator (`data_pipeline/curator.py`) ⏸ รอคำตอบ §4
- โฟลเดอร์ย่อย: ถ้า `rel_path` ชั้นที่ 2 ตรงกับรหัสใน `faults_for_exercise()` → ส่ง `filed_under_rule` เป็น hint ใน prompt
  ("เปเปอร์นี้หามาเพื่อกฎ X แต่ tag ตามเนื้อหาของแต่ละ item") และบันทึกลง window
- `general`: ตอนนี้ `is_exercise_mismatch("general", …)` ใช้ alias `("general",)` → window ที่ LLM บอกว่าเป็น "Squat" ถูก**คัดทิ้ง**
  และ retrieval (`test_rag_compare.py`) filter `exercise_id == ท่าของ session` → chunk `general` **ไม่ถูกดึงมาใช้เลย**
  ข้อเสนอ: window ที่ `exercise_type` map ได้กับ 1 ใน 4 ท่า (`EXERCISE_ALIASES`) → เขียนลงใต้ท่านั้นและ tag ด้วยกฎของท่านั้น
  ส่วนที่เป็นเรื่องทั่วไปจริงเก็บไว้ที่ `general/` (ยังไม่ถูกดึงใช้ จนกว่าจะมีขั้น R ที่เพิ่ม `exercise_id IN (ท่า, 'general')`)

### T3 — curate ใหม่ทั้งหมด ⏸
- `python data_pipeline/curator.py --out curated_data_v6 --excluded excluded_from_kb_v6 --legacy-excluded ./excluded_from_kb`
  (`--legacy-excluded` ทำให้ไฟล์ 6 ตัวที่เคยตัดออกด้วยมือว่า off-topic ไม่ถูก curate กลับเข้ามา)
- ขนาด: ประมาณ **840 window จาก PDF** (squat 202, lunge 264, bicep 171, push-up 106, general 96) + หน้าเว็บจาก `urls.txt` 17 หน้า
  เทียบกับ v5 ที่มี 229 window → ใช้เวลาหลายชั่วโมงและเสียค่า API (`gemini-3.5-flash`) **แจ้ง user ก่อนรัน**
- ความเสี่ยงที่รับไว้: ข้อความ item เปลี่ยน (LLM ไม่ deterministic) · ต้องดึงหน้าเว็บใหม่ (เนื้อหาอาจเปลี่ยนหรือหายไปแล้ว)
- หลังรัน: เทียบ v5↔v6 ต่อ source (จำนวน window/item, จำนวนที่ถูก exclude, จำนวน tag ต่อกฎ) · ถ้า `knee_varus`/`front_knee_too_deep`
  ได้ 0 = KB ขาดเนื้อหา ไม่ใช่ tagger พัง → จดเป็น data gap · สุ่มอ่าน item ที่ติด tag `back_straight` ต้องเป็นเรื่องลำตัวโน้ม ไม่ใช่หลังงอ
- v5 (`curated_data_v5/`, `kb_gemini_curated_v5`) เก็บไว้เป็นตัวสำรอง ไม่ลบ

### T5 — ingest + eval ใหม่ ⏸
- `python ingest.py --data-folder ./curated_data_v6 --collection kb_gemini_curated_v6`
- `mock_data/mock_sessions_per_fault.json` → 12 session (1 ต่อกฎ) + clean session ใช้รหัสใหม่
- สร้าง `eval/relevance_pool.json` ใหม่ (`eval/build_relevance_pool.py`) และเขียน `must_hit` ใน `eval/golden_chunks.json` ใหม่
- รัน R4 default บน v6 = **baseline ใหม่** → จดลง `compare_output/ablation_log.md` แล้วอัปเดต §0/§4 ของ `rag_v2_ablation_plan.md`
- `python kb_coverage.py` บน v6: coverage ต่อกฎ 12 ตัว

### (ภายหลัง) P-rule-card — ใส่ rule card จากสเปกเข้า prompt เป็น checkpoint generation แยก

## 3. เรื่องที่รอยืนยันกับทีมระบบ 1 และผลต่อแผน

| ต้องยืนยัน | ถ้าต่างจากสเปก ต้องแก้ |
|---|---|
| รายชื่อกฎ 12 ข้อครบและถูก (มีเพิ่ม/ตัด/รวมไหม) | `ERROR_TAXONOMY` + `LEGACY_CODES` + test · ถ้ามีกฎใหม่ต้องเขียน `query` ใหม่ในรูป curator mistake |
| **string ที่ระบบ 1 ส่งมาเป็น `error_type`** จริง ๆ: rule name (`knee_valgus`)? cue ("Push knees out")? ชื่ออาการ? ภาษาไทย? | key/`aliases` ใน taxonomy (ตอนนี้รับทั้ง rule name และ cue) |
| ชื่ออาการผิดที่จะแสดงให้ user เห็น (ไทย) | `display_th` ใน taxonomy |
| `back_straight` วัดแค่ trunk tilt จริง ไม่รวมหลังงอ (butt wink) | ถ้ารวมด้วย → เพิ่ม `butt wink` เข้า `LEGACY_CODES` และขยาย `query` |
| `elbow_away` ไม่บอกทิศ (ออกข้าง/หน้า/หลัง) | ถ้ามีทิศ → อาจแยกเป็นหลายรหัส |
| ส่งค่ามุมจริงต่อ rep มาด้วยไหม (สเปกบอกว่า rep summary เก็บ "per-rep metric values") | ถ้าส่ง → ขั้น P-rule-card ใช้บอก user ได้ว่า "เข่าต่ำสุด 112° เป้า 100°" |

**สำคัญ:** ต้องยืนยันก่อน T3 เพราะรายชื่อกฎและ `query` ถูกฝังลงใน tag ตอน curate ถ้าเปลี่ยนทีหลังต้อง curate ใหม่อีกรอบ

## 4. คำถามที่ยังค้าง (ต้องตอบก่อน T4)

1. `data/general/feedback_and_cueing/` (Lincoln, Neumann, Smith, Stien — วิธีให้ feedback) ข้อเสนอ: **ไม่ curate เข้า KB** เก็บไว้ใช้ออกแบบ prompt ขั้น P5
2. `data/general/` ที่เหลือ (`basics_of_strength_and_conditioning_manual.pdf`, `injury/Bonilla2022…`) ข้อเสนอ: ส่วนที่พูดถึงท่าเฉพาะ
   ให้ย้ายไปอยู่ใต้ท่านั้น แทนที่จะถูกคัดทิ้ง (ดู T4)
3. จะ commit T1 + T2 ตอนนี้ หรือรอผลยืนยันกฎก่อน

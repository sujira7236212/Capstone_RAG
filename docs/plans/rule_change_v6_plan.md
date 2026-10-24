# แผนรับกฎใหม่ของระบบ 1 → KB v6

> ไฟล์สำหรับเปิดทำต่อใน session ใหม่ · อัปเดตล่าสุด 2026-10-02 · สถานะ: **กำลังทำ — T3 รอบ 1 เสร็จ ถัดไปรอบ 2a (รอ user) · รายละเอียดอยู่ที่ [`t3_curation_status.md`](../progress/t3_curation_status.md)**
> T1 ✅ (user ยืนยัน Q-spec 2026-10-02) · T2 ✅ · T3a ✅ · T4 ✅ · T3 / T5 ยังไม่เริ่ม · **งานอยู่บน branch `rule-change-v6`** (`main` ยังเป็น taxonomy เดิมที่ตรงกับ KB v5)
> แผนนี้**มาก่อน**ขั้นที่ค้างอยู่ใน [`rag_v2_ablation_plan.md`](rag_v2_ablation_plan.md) (G1/C1/K1/P) เพราะรหัส fault เปลี่ยน ตัวเลข R4 เดิมจึงเทียบกับ KB ใหม่ไม่ได้
> **เป้าหมายตอนนี้ (2026-10-01):** ไปให้ถึงขั้นที่ Gemini ให้ feedback บน KB v6 ก่อน eval หนัก (E3/E4/E6/E7 และ G1) เลื่อนไปทำหลังจากนั้น

## 0. เริ่มต่อจากตรงนี้

1. **กฎนิ่งแล้ว** — user ยืนยันคร่าว ๆ (2026-10-01) ว่าอาการของทั้ง 12 กฎถูกต้อง และถือว่ากฎชุดนี้ไม่เปลี่ยนอีก
   คำตอบของ `squat.back_posture` ใน `eval/rule_cards.json`: **oq1 = นับ** (ลำตัวโน้มไปหน้ามากเกินเป็น relevant) · **oq2 = นับ** (butt wink เป็นหลังค่อมแบบหนึ่ง)
   → `butt wink` กลับเข้า `LEGACY_CODES` โดย map ไปที่ `rounded_back`
2. **T1 เสร็จ — user ยืนยัน key และ Q-spec ทั้ง 12 ตัว (2026-10-02)** key = ชื่อกฎ 2026-09-28 · ชื่อ 2026-09-25 อยู่ใน `LEGACY_CODES` · `query` เขียนจาก card (Claude ร่าง user แก้ `partial_pushup` แล้วยืนยัน)
   · ลบ `rule_th`, `display_th`, `aliases` ออกแล้ว เพราะระบบ 1 ส่ง `error_type` = key ตรงตัวเสมอ (ไม่ส่ง cue หรือชื่อไทย) · `resolve()` ยังใช้อยู่ (จับ key, `_`/ช่องว่าง, `LEGACY_CODES`)
   · ผู้เชี่ยวชาญอนุมัติ card ครบ 12 ใบ (card_version 1) · `approval` ไม่ใส่ชื่อตามที่ user ขอ
   · `python tests/test_error_taxonomy.py` 23/23 · `python tests/test_normalize_fault_tags.py` 10/10
   · `python eval/check_rule_cards.py --queries` ผ่าน: query ซ้ำกับ KB v5 และ anchor ไม่ถึง 5 คำ
3. **ถัดไป — ตามลำดับ ห้ามสลับ:**
   1. ~~user ยืนยัน Q-spec~~ ✅ 2026-10-02
   2. ~~ใส่ `approval` → commit card + taxonomy พร้อมกัน ก่อน T3a~~ ✅ 2026-10-02 (หลักฐานว่าเฉลยและ query นิยามไว้ก่อนอ่านเอกสาร) · **หลังจากนี้ห้ามแก้ `query` อีกโดย Claude** เพราะ T3a ทำให้ Claude อ่านต้นฉบับแล้ว ถ้าต้องแก้ให้ user แก้เอง หรือทำเป็น Q-tuned
   3. ~~**T3a** Claude คัดเอกสารที่ไม่เกี่ยวออกทั้งไฟล์~~ ✅ 2026-10-02 (keep 71 · drop 31)
   4. ~~**T4** แก้ curator ตามแบบใหม่~~ ✅ 2026-10-02
   5. **T3** curate (แจ้งขนาดงานและค่า API ก่อนรัน) → **T5** ingest → E5 split → mock 12 กฎ + clean → generate
4. ⚠️ **ห้ามรัน eval retrieval/generation บน `kb_gemini_curated_v5` จนกว่าจะจบ T5** — taxonomy ใช้รหัสใหม่แล้ว แต่ KB v5 ยังติด tag เก่า
5. คำถามที่ยังเปิดใน card และ**ไม่**กระทบ T3: lunge oq1/oq2 (ระยะก้าว, เข่าเลยปลายเท้า) และ oq ของ knee_varus · query ของ `shallow_lunge` /
   `excessive_front_knee_flexion` จึงยังไม่พูดถึงระยะก้าวและเข่าเลยปลายเท้า ถ้าได้คำตอบก่อน T3 ให้เติมได้ ถ้าได้หลัง T3 แก้แค่ card

## 1. ที่มา

ระบบ 1 เปลี่ยนชุดกฎ จาก 10 fault (snapshot 2026-09-11, `error_type_taxonomy.md` §5) เป็น **12 กฎ** ตามสเปก
[`docs/rules/system1/RULES_AND_FSM_CONDENSED.md`](../rules/system1/RULES_AND_FSM_CONDENSED.md) (sync จากโค้ดของระบบ 1 เมื่อ 2026-09-25)
พร้อมกันนั้นมีข้อมูลใหม่ใน `data/` ซึ่งแยกโฟลเดอร์ย่อยตามชื่อกฎ (`data/squat/knee_valgus/…`) และมี `data/general/`

### 1.1 กฎเก่า → กฎใหม่ (จำนวน item ที่ติด tag ใน `curated_data_v5`)

| เดิม (§5) | ใหม่ | ความหมาย | items v5 |
|---|---|---|---|
| squat `partial squat` | `knee_depth` (>100°) | เปลี่ยนแค่ชื่อ | 85 |
| squat `knee valgus` | `knee_valgus` | เปลี่ยนแค่ชื่อ | 149 |
| squat `butt wink` (lumbar flexion) | `back_straight` = trunk tilt >35° ("not spine curvature") | เปลี่ยน · ผู้เชี่ยวชาญตอบ 2026-10-01 ว่านับ butt wink เป็น `rounded_back` | 57 |
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

### T1 — taxonomy ใหม่ ✅ ทำใหม่ 2026-10-01 (commit `95eed58` · Q-spec ยืนยัน `cc4f55b`)
- `error_taxonomy.py`: key = ชื่อกฎ 2026-09-28 · `aliases[0]` = cue บนจอ · `display_th` ตรงกับ card
- `LEGACY_CODES` ต่อท่า: ชื่อ 2026-09-25 (ซึ่งเป็นชื่อโฟลเดอร์ย่อยใน `data/` ด้วย) + รหัส 2026-09-11 + ยุค v4 · **`butt wink` → `rounded_back`** (oq2)
- `query` = **Q-spec** ทั้ง 12 ตัวเขียนใหม่จาก `definition`/`includes` ของ card (ไม่ใช้ anchor ไม่เปิด KB) เป็นประโยคบรรยายเชิงบวกเท่านั้น
  (embedding อ่าน "ไม่ใช่ X" ไม่ออก และจะดึง X มาแทน) · query เดิมของ `full_rom` ที่จูนให้ตรงกับสำนวน curator ถูกแทนที่แล้ว
- `rounded_back`: ครอบคลุมหลังค่อม (รวม butt wink) หลังแอ่น และลำตัวโน้มไปหน้า เรียงตามลำดับที่ Ton กำหนด
- ทดสอบ: `python tests/test_error_taxonomy.py` (24/24) · `python tests/test_normalize_fault_tags.py` (10/10)
  · `python eval/check_rule_cards.py --queries` (flag ใหม่: key ตรงกับสเปก, query ซ้ำกับ KB v5 และ anchor < 5 คำ)

### T2 — จัดการ `data/` ✅ เสร็จ
- ย้ายไป `data_duplicates/` (คงโครงโฟลเดอร์, อยู่ใน `.gitignore`): Coratella2023, Boyd2017, Marchetti2018, Rusin2018 (MD5 ตรงกับไฟล์ที่ root)
  และ Pedrosa2026 (เปเปอร์เดียวกับ "The interplay between muscle length…" ซึ่งเก็บไว้)
- "Varying Weightload…" user ลบเองแล้ว · "Core Muscle Activity…" ×2 และ "Biomechanics of the Push-up" ×2 **เก็บไว้ทั้งคู่** (user ตัดสิน)
- สเปกของระบบ 1 ย้ายจาก `data/rule and rep count/` ไปที่ `docs/rules/system1/`
- โฟลเดอร์ว่าง `data/lunge/front_knee_too_shallow/`, `data/push-up/elbow_depth/` ปล่อยไว้ (ไม่มีผล)

### T3a — Claude คัดเอกสารที่ไม่เกี่ยวออก ทั้งไฟล์ ✅ 2026-10-02
- **ผล:** 102 หน่วย · keep 71 · drop 31 (27 + feedback_and_cueing 4 ไว้ทำ prompt) (ตรวจ drop ซ้ำทั้งไฟล์ตามที่ user ขอ: u077 กลับเป็น keep · user ลบไฟล์ซ้ำ 2 ไฟล์ออกจาก `data/`) → `data_pipeline/prefilter_v6.json` + [`prefilter_v6_review.md`](../kb/prefilter_v6_review.md) (drop, keep ที่ไม่แน่ใจ 10) · user ตรวจแล้ว
- **หน่วยที่ตัดคือทั้งไฟล์** (หรือทั้ง URL ใน `urls.txt`) ไม่ตัดเนื้อหาบางส่วนในไฟล์ (user ตัดสิน 2026-10-01)
- เกณฑ์ตัด: ไฟล์ไม่มีเนื้อหาเกี่ยวกับท่าทางของ 4 ท่าที่ใช้กับกฎข้อใดข้อหนึ่งใน 12 ข้อได้เลย (ลักษณะอาการ สาเหตุ ผลเสีย วิธีแก้ หรือท่าที่ถูก)
  · **ไม่แน่ใจให้เก็บไว้** เพราะ curator คัดเนื้อหาที่ไม่เกี่ยวราย window อยู่แล้ว ขั้นนี้มีไว้ตัดไฟล์ที่ไม่เกี่ยวชัด ๆ เพื่อลดค่า API และ noise เท่านั้น
- วิธีอ่าน: ชื่อเรื่อง, abstract, สารบัญ, หัวข้อ, และอ่านผ่าน ๆ เฉพาะส่วนที่จำเป็นต่อการตัดสิน
- บันทึก `data_pipeline/prefilter_v6.json`: ต่อไฟล์มี `path`, `decision` (keep/drop), `reason`, `reviewer` ("claude"), `date` · user ตรวจรายการ drop ก่อน T3
- **ลำดับสำคัญ:** ต้องทำหลัง commit Q-spec และ card เพราะถ้า Claude อ่านต้นฉบับก่อนเขียน query สำนวนของต้นฉบับซึ่ง KB v6 จะสรุปมาอาจติดเข้าไปใน query (leakage)
  ถ้าจะทำ Q-hyde ภายหลัง ต้องรันใน context ที่สะอาดผ่าน API ตาม E2 ไม่ใช่ใน session ที่อ่านต้นฉบับแล้ว
- รายงานต้องเขียนว่ามีขั้นคัดเอกสารทั้งไฟล์โดย LLM (Claude) ก่อน curate พร้อมจำนวนไฟล์ที่ตัดและเหตุผล
- **ขั้นตอน (user อนุมัติ 2026-10-02)** · ขอบเขต 102 หน่วย = PDF 85 + URL 17 (เดิม 104 ก่อน user ลบไฟล์ซ้ำ 2 ไฟล์) ใน `urls.txt` 4 ไฟล์ (ไม่รวม `data_duplicates/`)
  1. สคริปต์ทำรายการทุกไฟล์/URL ลงโครง `prefilter_v6.json` (กันตกหล่น)
  2. ดึงข้อความตัวอย่างลง scratchpad (ไม่เข้า repo, ไม่เรียก API): PDF ใช้ pypdf → จำนวนหน้า, bookmark, ชื่อเรื่อง, abstract, 2 หน้าแรก · PDF สแกนใช้ Read tool ดูภาพหน้า · URL ใช้ trafilatura แบบเดียวกับ `load_urls_main_content()`
  3. ตัดสินทีละหน่วย อ่านเพิ่มเฉพาะเมื่อไม่พอ · ก้ำกึ่ง: ท่าดัดแปลง keep ถ้ากลไกใช้กับท่ามาตรฐานได้ · กลุ่มคนเฉพาะ (เช่น ACL) keep ถ้ามี kinematics ที่ใช้กับกฎได้ · งาน hypertrophy/EMG keep ถ้าพูดถึง ROM/ตำแหน่งข้อต่อ/เทคนิค drop ถ้าวัดแค่ผลโปรแกรม · ตำรา keep ทั้งเล่มถ้ามีบทที่เกี่ยว · URL ดึงไม่ได้ keep + บันทึก "fetch failed"
  4. ต่อหน่วยบันทึก `path`/`url`, `decision` (keep/drop/pending), `reason`, `read` (อ่านส่วนไหน), `reviewer`, `date` · **ไม่บันทึกว่าเกี่ยวกับกฎไหน** (กันกลายเป็น hint ให้ curator ขัดกับ T4 ข้อ 4)
  5. `docs/kb/prefilter_v6_review.md` ให้ user ตรวจ: ตาราง drop + keep ที่ไม่แน่ใจ ต่อท่า + จำนวนสรุป
  6. สคริปต์ตรวจว่าทุกหน่วยอยู่ครั้งเดียวพอดี และ decision ถูกค่า
  7. user ตรวจ drop → commit → T4 (`--skip-list`) · **T3 เริ่มไม่ได้ถ้ายังมี `pending`**
  - ห้าม: ลบ/ย้ายไฟล์ใน `data/` · เปิด `curated_data_v5/` หรือ log คัดออกของ v5 · แก้ `query`/card · เรียก Gemini/API ที่เสียเงิน
  - `general/feedback_and_cueing/` 4 ไฟล์: user ตัดสินให้ใช้ทำ prompt อย่างเดียว → `drop` (T4 ข้อ 3)

### T4 — แก้ curator (`data_pipeline/curator.py`) ✅ 2026-10-02
- **ทำแล้ว:** `--skip-list` (`load_skip_list`, ไม่รันถ้ามี pending) · `general/` เห็น 12 กฎจัดกลุ่มตามท่า + กติกาให้ระบุท่าเฉพาะเมื่อเอ่ยชื่อตรง ๆ · `route_general_window()` จัดท่าราย item → `curated_data_v6/<ท่า>/general__<stem>_curated.json` · ไม่ใช้ `is_exercise_mismatch()` กับ general · ข้อ 5 **ทำด้วย** (user ตกลง 2026-10-02): `excludes` ของ card เป็นบรรทัด "do not tag when" ใต้ทุกกฎ · prompt ของโฟลเดอร์ท่าเหมือน v5 ทุกคำยกเว้นบรรทัด excludes
- ทดสอบ: `python tests/test_route_general.py` (route ท่าเดียว/2 ท่า/ไม่มี tag แต่ map ได้/map ไม่ได้/leg curl, skip list, fault block) · skip list จับไฟล์จริงใน `data/` ได้ 31/31
- ขนาด T3 (ประเมิน 2026-10-02): 71 หน่วย ≈ 700 window (squat 211 · lunge 202 · bicep-curl 158 · push-up 50 · general 79) · ~2.9 ล้านตัวอักษร
1. **`--skip-list data_pipeline/prefilter_v6.json`**: ข้ามไฟล์และ URL ที่ `decision == "drop"` และ log ไว้ (ไม่สร้าง marker ปลอมใน `excluded_from_kb_v6/`)
2. **`general/` ให้ curator เลือกท่าและ tag เองจากเนื้อหา ไม่อิงโฟลเดอร์**
   - prompt ของไฟล์ใต้ `general/` แสดงรหัสกฎทั้ง 12 ตัวจัดกลุ่มตามท่า (ชื่อกฎไม่ซ้ำกันข้ามท่า จึงรู้ท่าได้จาก tag) และสั่งว่า
     "ใส่ท่าเฉพาะเมื่อข้อความเอ่ยชื่อท่านั้นตรง ๆ ห้ามเดา"
   - **ท่าของแต่ละ item**: ถ้ามี tag → ท่าของ tag (ถ้ามี tag จาก 2 ท่า ให้เขียน item ลงทั้งสองท่า) · ถ้าไม่มี tag → ใช้ `exercise_type` ของ window
     ถ้า map ได้กับ 1 ใน 4 ท่าผ่าน `EXERCISE_ALIASES` · ถ้า map ไม่ได้ → อยู่ใน `general/` (ตอนนี้ retrieval ยังไม่ดึงจาก general)
   - output: `curated_data_v6/<ท่า>/general__<ชื่อไฟล์>_curated.json` (ingest ใช้ path ชั้นแรกเป็น `exercise_id` อยู่แล้ว) ส่วนที่เหลือเขียนลง `curated_data_v6/general/`
   - `is_exercise_mismatch()` ไม่ใช้กับ `general` (ตอนนี้มันคัด window ที่ LLM บอกว่าเป็น "Squat" ทิ้ง)
   - ทดสอบ: unit test ของฟังก์ชันที่ route item ไปตามท่า (มี tag ท่าเดียว / tag 2 ท่า / ไม่มี tag แต่ map ได้ / map ไม่ได้)
3. **`general/feedback_and_cueing/` (4 ไฟล์) ไม่เอาเข้า KB — ใช้ออกแบบ prompt ขั้น P5 อย่างเดียว** (user ตัดสิน 2026-10-02 หลัง Claude อ่านทั้ง 4 ไฟล์: เนื้อหาตรงกฎมีแค่ไม่กี่ประโยค)
   · อยู่ใน `prefilter_v6.json` เป็น `drop` แล้ว ไม่ต้องใส่ skip list แยก
   · `general/injury/` ให้ T3a ตัดสิน
4. **ไม่ใช้ hint `filed_under_rule`** (ยกเลิกข้อเสนอเดิม) โฟลเดอร์ย่อยตามชื่อกฎ (`data/squat/knee_valgus/`) ไม่มีผลต่อ tag เลย ทำให้ tag มาจากเนื้อหาล้วน ๆ
   และตัดข้อจำกัดใน §7 ของ `eval_v6_plan.md` เรื่อง tag ไม่อิสระจาก source folder ออกได้ · โฟลเดอร์ชั้นท่า (`squat/` ฯลฯ) ยังเป็นตัวกำหนด
   `exercise_id` และ `is_exercise_mismatch()` ยังทำงานเหมือนเดิมสำหรับ 4 ท่า
5. **(ทำแล้ว)** แสดง `excludes` ของ card ให้ curator เห็นเป็นบรรทัด "do not tag when …" ต่อรหัส เพื่อลด tag สลับระหว่างกฎพี่น้อง
   (valgus/varus, shallow/deep lunge, partial_squat/butt wink) · card เป็นนิยามที่ผู้เชี่ยวชาญรับรอง ไม่ใช่เนื้อหา KB การใช้ตรงนี้จึงไม่ทำให้ eval รั่ว
- หลัง T3: สุ่มอ่าน item ที่ย้ายมาจาก `general/` อย่างน้อย 20 ชิ้น เพราะถ้าจัดท่าผิด เทสต์ cross-exercise leak จะจับไม่ได้ (`exercise_id` จะตรงกับ session พอดี)

### T3 — curate ใหม่ทั้งหมด ⏸
- `python data_pipeline/curator.py --out curated_data_v6 --excluded excluded_from_kb_v6 --legacy-excluded ./excluded_from_kb`
  (`--legacy-excluded` ทำให้ไฟล์ 6 ตัวที่เคยตัดออกด้วยมือว่า off-topic ไม่ถูก curate กลับเข้ามา)
- ขนาด: ประมาณ **840 window จาก PDF** (squat 202, lunge 264, bicep 171, push-up 106, general 96) + หน้าเว็บจาก `urls.txt` 17 หน้า
  เทียบกับ v5 ที่มี 229 window → ใช้เวลาหลายชั่วโมงและเสียค่า API (`gemini-3.5-flash`) **แจ้ง user ก่อนรัน**
- ความเสี่ยงที่รับไว้: ข้อความ item เปลี่ยน (LLM ไม่ deterministic) · ต้องดึงหน้าเว็บใหม่ (เนื้อหาอาจเปลี่ยนหรือหายไปแล้ว)
- หลังรัน: เทียบ v5↔v6 ต่อ source (จำนวน window/item, จำนวนที่ถูก exclude, จำนวน tag ต่อกฎ) · ถ้า `knee_varus`/`excessive_front_knee_flexion`
  ได้ 0 = KB ขาดเนื้อหา ไม่ใช่ tagger พัง → จดเป็น data gap · สุ่มอ่าน item ที่ติด tag `rounded_back` ต้องเป็นหลังค่อม (รวม butt wink) หลังแอ่น หรือลำตัวโน้มไปหน้า
- v5 (`curated_data_v5/`, `kb_gemini_curated_v5`) เก็บไว้เป็นตัวสำรอง ไม่ลบ

### T5 — ingest + eval ใหม่ ⏸
- `python ingest.py --data-folder ./curated_data_v6 --collection kb_gemini_curated_v6`
  · ถ้ากลับมา curate เพิ่มหลัง ingest ไปแล้ว → ingest ลง collection ใหม่ `kb_gemini_curated_v6b` และล็อก split เดิม (ดู [`t3_curation_status.md`](../progress/t3_curation_status.md) §8)
- `mock_data/mock_sessions_per_fault.json` → 12 session (1 ต่อกฎ, ชื่อกฎ 2026-09-28) + clean session · ไฟล์ปัจจุบันยังมี 9 รหัสเก่า
- ~~เขียน `must_hit` ใน `eval/golden_chunks.json` ใหม่~~ ยกเลิก (2026-09-28): eval v6 ทำตาม [`eval_v6_plan.md`](eval_v6_plan.md) E5 → E3 → E4
  (แยก dev/test ก่อน แล้วสร้าง pool ที่ judge หลายค่ายตัดสินจาก rule card)
- รัน R4 default บน v6 = **baseline ใหม่** (E6 · รายงานบน dev, `--final` ครั้งเดียว) → จดลง `compare_output/ablation/ablation_log.md` แล้วอัปเดต §0/§4 ของ `rag_v2_ablation_plan.md`
- `python tools/kb_coverage.py` บน v6: coverage ต่อกฎ 12 ตัว

### (ภายหลัง) P-rule-card — ใส่ rule card จากสเปกเข้า prompt เป็น checkpoint generation แยก

## 3. เรื่องที่ยืนยันกับทีมระบบ 1 และผลต่อแผน

| เรื่อง | สถานะ (2026-10-01) | ผลต่อแผน |
|---|---|---|
| รายชื่อกฎ 12 ข้อครบและถูก | ✅ ยืนยันคร่าว ๆ ว่าอาการถูก และกฎไม่เปลี่ยนแล้ว | T1 ทำใหม่ตามชื่อ 2026-09-28 |
| `rounded_back` นับลำตัวโน้ม / butt wink ไหม | ✅ นับทั้งคู่ (card oq1, oq2) | `butt wink` อยู่ใน `LEGACY_CODES` · query ครอบคลุมทั้งสองอย่าง |
| ชื่ออาการที่แสดงให้ user เห็น (ไทย) | ใช้ `display_th` ของ card | `display_th` ใน taxonomy ตรงกับ card แล้ว |
| **string ที่ระบบ 1 ส่งมาเป็น `error_type`** จริง ๆ | ยังไม่ยืนยัน — **ไม่กระทบ T3** | taxonomy รับทั้งชื่อกฎ, cue และชื่อเก่าแล้ว ถ้าเป็นรูปอื่นแค่เพิ่ม `aliases` |
| `elbow_flare` ไม่บอกทิศ (ออกข้าง/หน้า/หลัง) | ยังไม่ยืนยัน — ไม่กระทบ T3 | ถ้ามีทิศในอนาคต อาจแยกรหัส |
| ส่งค่ามุมจริงต่อ rep มาด้วยไหม | ยังไม่ยืนยัน — ไม่กระทบ T3 | ถ้าส่ง → ขั้น P-rule-card ใช้บอก user ได้ว่า "เข่าต่ำสุด 112° เป้า 100°" |

## 4. คำถามก่อน T4 — ตอบแล้ว (2026-10-01)

1. `data/general/feedback_and_cueing/` → **ไม่ curate เข้า KB** ใช้ออกแบบ prompt ขั้น P5 (ยืนยันอีกครั้ง 2026-10-02 หลังอ่านเนื้อหา · ดู T4 ข้อ 3)
2. `data/general/` ที่เหลือ → curator เลือกท่าและ tag เองจากเนื้อหา ไม่อิงโฟลเดอร์ (T4 ข้อ 2) · `injury/Bonilla2022…` ให้ T3a ตัดสินว่าเก็บหรือตัด

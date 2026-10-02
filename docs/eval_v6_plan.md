# แผน eval retrieval สำหรับ KB v6 — ไม่ผูกกับสำนวน KB

> อัปเดตล่าสุด 2026-09-28 · สถานะ: **ร่าง — รอ API key ของ judge ค่ายอื่น** · อยู่บน branch `rule-change-v6` คู่กับ [`rule_change_v6_plan.md`](rule_change_v6_plan.md)
> แผนนี้แทนที่ `eval/golden_chunks.json` (`must_hit` แบบ substring) สำหรับ v6 ทั้งหมด · ไฟล์เดิมเก็บไว้เป็นประวัติของ v4/v5 เท่านั้น

## 0. เริ่มต่อจากตรงนี้

0. **E1 ร่างเสร็จ (2026-09-30), รอผู้เชี่ยวชาญอนุมัติ**
   - `eval/rule_cards.json` มี 12 card และ anchor 173 ประโยค (relevant 6 · wrong_fault 5–6 · irrelevant 3 ต่อ card) ข้อความภาษาอังกฤษคือสิ่งที่ judge ได้เห็น ภาษาไทยเป็นคำแปลสำหรับผู้เชี่ยวชาญ
   - `python eval/check_rule_cards.py` ตรวจโครงสร้าง ตรวจว่า card ครอบคลุมกฎตามสเปก และตรวจ n-gram กับ KB v5 ผลตอนนี้: ผ่าน · 0 hit ที่ ≥5 คำ (ร่างแรกมี 24 hit ใน 23 anchor ส่วนใหญ่เป็นวลีทั่วไปอย่าง "at the bottom of the" เขียนใหม่ทั้งหมดแล้ว)
   - `python eval/render_rule_cards.py` สร้าง `docs/rule_cards_review.md` เป็นเอกสารที่ส่งให้ผู้เชี่ยวชาญอนุมัติ
   - มีคำถามถึงผู้เชี่ยวชาญ 6 ข้อ ที่สำคัญคือ `squat.back_posture` oq1/oq2 (นับลำตัวโน้ม และ butt wink ไหม) ซึ่งมีผลต่อ `query` ของ T1 ด้วย
   - หลังอนุมัติ: ใส่ชื่อผู้อนุมัติและวันที่ใน `approval` แล้ว commit ก่อน T3
   - **2026-10-01:** `squat.back_posture` oq1 = นับลำตัวโน้ม · oq2 = นับ butt wink (บันทึกใน `answer` ของ open question, ไม่ต้องเพิ่ม `card_version` เพราะ card ยังไม่เคยอนุมัติ)
   - **E2 Q-spec ร่างแล้ว (2026-10-01):** `query` ทั้ง 12 ตัวใน `error_taxonomy.py` เขียนจาก card โดย Claude รอ user ตรวจและยืนยัน · ตรวจด้วย `python eval/check_rule_cards.py --queries` (0 hit กับ KB v5 และ anchor)
1. ถาม user ว่าได้ API key ของค่ายไหนมาเพิ่มบ้าง เพราะจะใช้ตัดสินว่า E4 ทำแบบเต็ม (3 ค่าย) หรือแบบ fallback (§6)
2. E1 เริ่มได้ทันทีที่ระบบ 1 ยืนยันกฎแล้ว (§3 ของแผน v6) และ**ต้องเสร็จและได้รับอนุมัติก่อน T3 (curate v6)**
3. ห้ามเปิดดู `curated_data_v5/`, `curated_data_v6/` หรือผลค้นจาก KB ระหว่างเขียน rule card, anchor และ Q-spec

## 1. ที่มา — ทำไม eval เดิมเชื่อไม่ได้

| จุด | eval เดิม (v4/v5) | ปัญหา |
|---|---|---|
| เฉลย | `must_hit` = substring ที่ตัดมาจาก KB v4 | chunk ได้คะแนนก็ต่อเมื่อใช้คำเดียวกับ v4 · ตอน v5 คะแนนตกเหลือ 4/10 เพราะเรื่องนี้ |
| คำอธิบายที่ judge ได้เห็น | `build_relevance_pool.py` ส่ง `resolve()["query"]` ให้ judge | query ตัวเดียวเป็นทั้งคำค้นและเกณฑ์ตัดสิน = วงจรปิด |
| ที่มาของ candidate | ดึงด้วย query ของเราเองบวก tag | สิ่งที่ query หาไม่เจอก็ไม่ถูกเอามา label |
| query | เขียนโดยเปิดดูสำนวน curator และแก้หลังเห็นคะแนน (`error_taxonomy.py` bicep partial ROM) | จูนและรายงานบนชุดเดียวกัน = leakage |
| judge กับ curator | Gemini ทั้งคู่ และเห็นคำอธิบายเดียวกัน | ถ้าผิดก็ผิดไปในทางเดียวกัน |

สรุปที่คุยกันแล้ว (2026-09-28): ปัญหาหลักอยู่ที่ eval ไม่ใช่การที่ query เลียนสำนวน KB แต่ถ้ายังไม่แก้ eval ก็จะวัดไม่ได้ว่าการเลียนสำนวนทำให้ระบบเปราะหรือเปล่า

## 2. หลักการ

1. **เฉลยมาจากนิยามของกฎ ไม่ใช่จาก KB** — rule card เขียนจากสเปกของระบบ 1 และผู้เชี่ยวชาญเป็นผู้อนุมัติ
2. **คนที่ตัดสินต้องไม่เห็นว่าระบบค้นด้วยอะไร** — judge ได้เห็นแค่ rule card กับ chunk
3. **จูนบน dev รายงานบน test** — test รันครั้งเดียวต่อ config ที่ freeze แล้ว และบันทึกทุกครั้ง
4. **ไม่มีคน label chunk** — ผู้เชี่ยวชาญทำได้แค่อนุมัติ (ยืนยันกับ user แล้ว 2026-09-28) ส่วนที่คนเคยทำจึงแทนด้วย anchor ที่ผู้เชี่ยวชาญอนุมัติพร้อม card และ judge หลายค่าย
5. **ชื่อกฎเปลี่ยนได้ แต่เฉลยต้องไม่หาย** — เฉลยผูกกับ `concept_id` ส่วนชื่อกฎของระบบ 1 เป็นแค่ mapping

## 3. ตัวชี้วัด 3 ชั้น

### ชั้น 0 — วัดอัตโนมัติ ไม่ใช้คนและไม่ใช้ LLM

| ตัวชี้วัด | วัดยังไง | ผ่านเมื่อ |
|---|---|---|
| cross-exercise leak | chunk ที่ `exercise_id` ไม่ตรงกับท่าของ session โผล่ใน context | = 0 |
| negative: clean session | session ที่ไม่มีท่าผิด | context ว่าง |
| negative: data gap | กฎที่ใน pool ไม่มี `relevant` เลย (เช่น `knee_varus` ถ้า KB ไม่มีเนื้อหา) | รายงานเป็น data gap ไม่นับเป็นความผิดของ retrieval |
| alias stability | ส่ง rule name, cue และ legacy code ของกฎเดียวกัน แล้วเทียบ context (Jaccard) · ไม่รวมชื่อไทย เพราะระบบ 1 ไม่ส่งชื่อไทยแน่นอน (user ยืนยัน 2026-10-02) และ `resolve()` ก็ไม่จับคู่ `display_th` | = 1.0 เพราะ `resolve()` ควรพาไป query เดียวกัน |
| anchor discrimination | collection เล็กที่มีแต่ anchor ของทุกกฎในท่าเดียวกัน (ไม่มี KB อยู่ในนั้น) → ค้นด้วย query ของกฎ X แล้ว anchor `relevant` ของ X ต้องอยู่เหนือ anchor ของกฎพี่น้อง | วัดว่า query แยกกฎที่คล้ายกันออกจากกันได้ไหม โดยไม่ต้องพึ่ง KB |
| source-folder recall | ค้นกฎ X แล้วนับสัดส่วน chunk ที่มาจากเปเปอร์ใน `data/<ท่า>/<X>/` เทียบกับโฟลเดอร์ของกฎอื่น | ใช้ดูแนวโน้มเท่านั้น (เปเปอร์หนึ่งพูดได้หลายเรื่อง) |

### ชั้น 1 — LLM judge หลายค่าย (ตัวเลขหลัก)

- label มี 3 ค่าเหมือนเดิม: `relevant` / `wrong_fault` / `irrelevant` โดยตัดสินจาก rule card
- ใช้เสียงข้างมากจาก judge 3 ค่าย ถ้า 3 ตัวตอบต่างกันหมดเป็น `uncertain` ซึ่งไม่นับทั้งตัวตั้งและตัวหาร แต่ต้องรายงานจำนวน
- ตัวเลขต่อกฎ: **recall** (relevant ที่ถึง context / relevant ทั้งหมดใน pool) · **precision** (relevant / kept) · **wrong_fault rate** (wrong_fault / kept ซึ่งเป็นตัวที่อันตรายที่สุด) · bootstrap 95% CI
- ความน่าเชื่อถือของ judge: accuracy บน anchor ต่อ judge และ Fleiss' κ ระหว่าง judge ต่อกฎ (ดู E4)

### ชั้น 2 — ผู้เชี่ยวชาญอนุมัติ

- อนุมัติ rule card ทั้ง 12 ใบ **รวม anchor ในแต่ละใบ** — เป็นชุดคำตอบที่รู้ล่วงหน้าชุดเดียวที่คนรับรอง
- ไม่มีงาน label ไม่มีการตรวจ context และไม่มีการชี้ขาดข้อที่ judge ไม่ลงรอยกัน

## 4. ขั้นตอน

### E1 — rule card + anchor → ผู้เชี่ยวชาญอนุมัติ
- ไฟล์ `eval/rule_cards.json` ต่อกฎมีฟิลด์:
  - `concept_id` (คงที่ตลอด), `card_version`, `exercise_id`, `rule_names` (ชื่อกฎของระบบ 1 ที่ map มาหา concept นี้)
  - `measures`: ระบบ 1 วัดอะไรและ threshold เท่าไหร่ (ยกมาจาก `docs/system1/RULES_AND_FSM_CONDENSED.md`)
  - `definition`, `includes`, `excludes` (บอกว่าอาการอื่นตัวไหนที่คล้ายแต่ไม่ใช่ เช่น `back_straight` คือลำตัวโน้ม ไม่ใช่หลังงอ, valgus ไม่ใช่ varus)
  - `relevant_info`: ลักษณะ / สาเหตุ / ผลเสีย / วิธีแก้ / หลักท่าที่ถูกซึ่งแก้อาการนี้ได้โดยตรง
  - `anchors`: ประโยคตัวอย่าง `relevant` ≥5, `wrong_fault` ≥5 (อย่างน้อย 2 ประโยคต้องมาจากกฎพี่น้องในท่าเดียวกัน), `irrelevant` ≥3
  - `approval`: ชื่อผู้อนุมัติ, วันที่, `card_version` ที่อนุมัติ
- เราเขียน anchor จากสเปกและความรู้ทั่วไป (ให้ LLM ช่วยร่างได้ แต่ห้ามให้มันเห็น KB)
- สคริปต์ `eval/render_rule_cards.py` แปลง card เป็นเอกสารอ่านง่ายหนึ่งไฟล์ให้ผู้เชี่ยวชาญอนุมัติ
- ตรวจ anchor ด้วย n-gram กับ KB v5 (ใช้ตัวหา longest shared n-gram จาก `eval/eval_generation.py`) ถ้าซ้ำกันตั้งแต่ 5 คำขึ้นไปให้เขียนใหม่
- **commit card ที่อนุมัติแล้วก่อนเริ่ม T3** ประวัติ git จะเป็นหลักฐานว่าเฉลยถูกนิยามก่อนมี KB v6
- ถ้ากฎ**เปลี่ยนแค่ชื่อ** → แก้ `rule_names` อย่างเดียว ไม่ต้องอนุมัติใหม่ · ถ้า**ความหมายของกฎเปลี่ยน** → เพิ่ม `card_version`, ส่งผู้เชี่ยวชาญอนุมัติเฉพาะใบนั้น แล้ว label ใหม่เฉพาะ concept นั้น

### E2 — query 3 แบบ (ทั้งหมดไม่เห็น KB ยกเว้น Q-tuned)

| ชื่อ | ที่มา | เก็บที่ |
|---|---|---|
| **Q-spec** | เขียนมือจาก rule card เป็น baseline และ curator ใช้เป็นคำอธิบายตอน tag | `query` ใน `error_taxonomy.py` (ทบทวนสิ่งที่ทำใน T1) |
| **Q-hyde** | LLM อ่าน rule card แล้วแต่ง statement สมมติแยกตาม kind (mistake / finding / principle) generate ครั้งเดียวแล้ว freeze ต่อ `card_version` ไม่เรียก LLM ตอน runtime | `eval/hyde_queries.json` + flag `--queries hyde` |
| **Q-tuned** | จูนจาก Q-spec หรือ Q-hyde โดยดูได้**แค่ dev** | `error_taxonomy.py` บน branch ทดลอง |

- **ฝั่งที่เขียน query ห้ามเห็น `anchors`**: Q-spec และ prompt ที่ใช้ generate Q-hyde ใช้ได้เฉพาะ `definition`, `includes`, `excludes`, `relevant_info` ของ card เท่านั้น
  เพราะ anchor เป็นข้อสอบที่ใช้ตรวจ judge (E4) และตรวจ query (anchor discrimination) ถ้า query ถูกสร้างจาก anchor คะแนนจะสูงเพราะ query มีเฉลยอยู่แล้ว
  · Q-hyde ต้องผ่านการตรวจ n-gram กับ anchor ด้วย (< 5 คำ) นอกจากตรวจกับ KB
- Q-spec และ Q-hyde ต้องผ่านการตรวจ n-gram กับ KB (< 5 คำ) ส่วน Q-tuned ให้รายงานค่า overlap ไว้คู่กับผล
- ตรวจ Q-hyde แบบอัตโนมัติ: ให้ judge ทุกตัวตัดสิน statement สมมติเทียบกับ card ต้องได้ `relevant` ครบทุกตัว ถ้าไม่ครบให้ generate ใหม่ (กันไม่ให้ LLM แต่งผิดอาการ)
- **ใครแต่ง query (ตัดสิน 2026-09-30):** anchor ร่างโดย Claude
  - Q-hyde **ห้ามใช้ Gemini** เพราะเป็นโมเดลเดียวกับ curator ทำให้สำนวนเข้ากับ chunk ของ KB v6 เอง
  - ถ้าได้ API key ค่ายที่ไม่ใช่ Gemini และไม่ใช่ Claude ให้ใช้ค่ายนั้นแต่ง Q-hyde · ถ้าไม่มีให้ใช้ Claude ได้ แต่ต้องรันใน context ที่สะอาด (เรียก API ด้วยสคริปต์ หรือเปิด session ใหม่ที่ไม่โหลด memory ของโปรเจกต์ ซึ่งมีเนื้อหา KB ปนอยู่) และป้อนแค่ card ที่ตัด `anchors` ออกแล้วกับ prompt ที่ fix ไว้
  - บันทึก generator, model ID, prompt และวันที่ไว้ใน `eval/hyde_queries.json`
  - ถ้าผู้แต่ง Q-hyde เป็น judge ด้วย ในขั้นตรวจ Q-hyde ให้ judge ค่ายอื่นเป็นตัวชี้ขาด
  - Q-spec ให้ user เป็นเจ้าของ Claude ร่างได้ แต่ user ต้องแก้และยืนยันเอง ไม่อย่างนั้นการเทียบใน E7 จะกลายเป็น Claude เทียบกับ Claude

### E3 — สร้าง candidate pool แบบ TREC pooling
- แก้ `eval/build_relevance_pool.py`:
  - ที่มาของ candidate: tag ของกฎ · dense top-k จาก Q-spec, Q-hyde, `definition` และ anchor `relevant` · BM25 จากศัพท์ใน card · chunk จาก source folder ของกฎ · **chunk ทุกตัวที่ config ใดก็ตามที่ถูกประเมินเคยใส่เข้า context** (ต้องรัน config ก่อนแล้วค่อยเติม pool)
  - คำอธิบายที่ส่งให้ judge = `definition` + `includes` + `excludes` + `relevant_info` จาก card **แทน `resolve()["query"]`**
  - key ของ label = (`concept_id`, `card_version`, judge model, `JUDGE_PROMPT_VERSION`, hash ของ chunk text)
- label ที่มีอยู่แล้วเอามาใช้ต่อได้ (resumable) pool ที่โตขึ้นจึงจ่ายค่า API แค่ส่วนที่เพิ่ม

### E4 — judge หลายค่าย
- ใช้ judge 3 ค่ายและทุกตัวต้องไม่ใช่โมเดลที่ curator ใช้ (`gemini-3.5-flash`)
- **gate ต่อ judge:** ตัดสิน anchor ของทุก card (~156 ข้อ) ต้องได้ accuracy ≥ 90% ถ้าไม่ผ่าน ให้แก้ prompt ของ judge แล้วเพิ่ม `JUDGE_PROMPT_VERSION` หรือเปลี่ยนโมเดล
  - anchor ใช้เป็นทั้งตัวเช็ก judge และตัวแก้ prompt ได้ เพราะ anchor ไม่ใช่ chunk ใน test จึงไม่ทำให้ test รั่ว
- **Fleiss' κ ต่อกฎ ≥ 0.6** ถ้าต่ำกว่านี้แปลว่า card คลุมเครือ ให้แก้ถ้อยคำของ card ถ้าแก้แค่ถ้อยคำไม่ต้องอนุมัติใหม่ แต่ถ้าแก้นิยามต้องส่งผู้เชี่ยวชาญอนุมัติใหม่
- fallback ถ้ามีแค่ Gemini: ใช้ 3 รุ่นที่ต่างขนาดกัน แต่ต้องเขียนในรายงานว่าอ่อนกว่า เพราะรุ่นในค่ายเดียวกันมักผิดไปในทางเดียวกัน

### E5 — แยก dev/test (ทำทันทีหลัง ingest v6 และก่อนรัน eval ใด ๆ)
- `eval/make_split.py` แยก**เอกสารต้นทาง** 70/30 แบบ stratified ต่อกฎ (ใช้ source folder ของกฎ) seed คงที่ ได้ `eval/split_v6.json` แล้ว commit ทันที
- retrieval ยังค้นทั้ง KB แต่ตอนให้คะแนน chunk ใน pool และ chunk ที่ kept จะถูกแบ่งตาม split ของเอกสารต้นทาง
- `eval/eval_retrieval.py` รายงานแค่ dev เป็นค่าเริ่มต้น · `--final` จะแสดง test และต่อท้ายลง `compare_output/final_log.md` พร้อม commit hash และ config **ทุกครั้ง** รวมถึงรอบที่ผลแย่
- กติกา: test รันครั้งเดียวต่อ config ที่ freeze แล้ว ห้ามแก้อะไรหลังเห็นผล test แล้วรันใหม่โดยไม่บันทึก

### E6 — baseline
- รัน R4 (`--queries profile`) + Q-spec บน dev → ได้ตัวเลขชั้น 0 และชั้น 1 ครบ
- `--final` หนึ่งครั้งเพื่อเป็นจุดอ้างอิงของ v6

### E7 — เทียบ query และวัด overfit
- บน dev: Q-spec vs Q-hyde vs Q-tuned (ทุกตัวรันบน R4)
- เลือก config ที่ดีที่สุดบน dev แล้ว freeze → `--final`
- รายงาน **dev − test ต่อ config** ถ้า Q-tuned ชนะขาดบน dev แต่สูสีกับ Q-spec บน test แปลว่า overfit ตัวเลขนี้คือคำตอบเชิงปริมาณของคำถาม "จูนตาม KB ทำให้ bias ไหม"

## 5. ลำดับเมื่อรวมกับแผน v6

1. ระบบ 1 ยืนยันกฎ (§3 ของแผน v6)
2. **E1** card + anchor → ผู้เชี่ยวชาญอนุมัติ → commit
3. **E2** Q-spec ลง `error_taxonomy.py` + generate Q-hyde + ตรวจ n-gram
4. T4 → T3 (curate v6 · curator tag ด้วย Q-spec) → T5 ingest
5. **E5** split → commit
6. **E3** pool → **E4** judge (ต้องมี API key)
7. **E6** baseline → **E7** เทียบ query → final
8. แผนต่อจากนี้ (ablation G1/C1/K1/P ใน `rag_v2_ablation_plan.md`) ใช้ eval ชุดนี้ และทำบน dev อย่างเดียว

T5 ในแผน v6 ข้อ "เขียน `must_hit` ใน `eval/golden_chunks.json` ใหม่" **ยกเลิก** ให้ใช้ E3–E5 แทน

## 6. เรื่องที่ค้าง

| เรื่อง | สถานะ | มีผลกับ |
|---|---|---|
| API key ค่ายอื่นสำหรับ judge | user กำลังหา | E4 ทำแบบเต็มหรือ fallback |
| รูปแบบเอกสารที่ส่งผู้เชี่ยวชาญ (PDF / doc / กระดาษ) | ยังไม่ถาม | output ของ `render_rule_cards.py` |
| ถ้าผู้เชี่ยวชาญไม่อนุมัติบาง card | — | card นั้นกับกฎนั้นรายงานแยกว่า "ยังไม่ได้รับการรับรอง" |
| ค่า API ของ judge 3 ค่ายบน pool ประมาณ 2,000+ chunk | ยังไม่ประเมิน | ประเมินหลัง T3 เมื่อรู้ขนาด pool จริง แล้วแจ้ง user ก่อนรัน |

## 7. ข้อจำกัดที่ต้องเขียนในรายงาน

- ไม่มี chunk ใดถูก label ด้วยคน ความถูกต้องขึ้นกับ LLM judge หลายค่ายที่ตัดสินตามนิยามที่ผู้เชี่ยวชาญรับรองแล้ว
- κ ระหว่าง judge บอกความ**สม่ำเสมอ** ไม่ได้พิสูจน์ความ**ถูก** เพราะ LLM หลายค่ายอาจเข้าใจผิดไปในทางเดียวกันได้ ชุดคำตอบเดียวที่คนรับรองคือ anchor (~156 ข้อ) ซึ่งเป็นประโยคที่เขียนขึ้น ไม่ใช่ chunk จริง
- anchor ร่างโดย Claude (2026-09-30) แล้วผู้เชี่ยวชาญอนุมัติ ผลที่ตามมามี 2 ข้อ
  - query ที่ Claude มีส่วนแต่งอาจได้ **anchor discrimination** สูงเกินจริง เพราะสำนวนคล้ายกัน การตรวจ n-gram < 5 คำกันได้แค่คำที่ซ้ำตรง ๆ ดังนั้นตัวชี้วัดนี้ใช้เทียบ query ที่ Claude แต่งกับ query ที่ไม่ใช่ Claude แต่งอย่างเป็นธรรมไม่ได้ ตัวเลขชั้น 1 ไม่โดนผลนี้ · ถ้ามี key ค่ายอื่น ให้วัดขนาดของ bias โดยแต่ง Q-hyde จากทั้งสองค่ายแล้วเทียบ anchor discrimination
  - ถ้า Claude เป็น judge ใน E4 ด้วย accuracy ของ Claude บน anchor อาจสูงเกินจริงเพราะมันเป็นคนแต่งข้อสอบเอง gate ≥ 90% ของ Claude จึงมีน้ำหนักน้อยกว่าของค่ายอื่น ต้องรายงานแยก
- source-folder recall เป็น label ระดับเปเปอร์ ใช้ดูแนวโน้มเท่านั้น
- ~~curator ได้ hint `filed_under_rule` จาก source folder~~ ยกเลิก hint แล้ว (T4, 2026-10-01) tag มาจากเนื้อหาล้วน แต่ source-folder recall ยังเป็น label ระดับเปเปอร์ ใช้ดูแนวโน้มเท่านั้น
- มีขั้นคัดเอกสารทั้งไฟล์โดย Claude ก่อน curate (T3a) ต้องรายงานจำนวนไฟล์ที่ตัดและเหตุผล

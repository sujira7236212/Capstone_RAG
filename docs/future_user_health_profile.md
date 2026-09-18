# แผนอนาคต: ดึงประวัติสุขภาพผู้ใช้เข้ามาในระบบ RAG feedback

**สถานะ:** บันทึกไว้พิจารณา — ยังไม่ implement
**บันทึกเมื่อ:** 2026-09-08
**ที่มา:** ความต้องการของเจ้าของโปรเจกต์ — อนาคตจะมีการดึงประวัติผู้ใช้ เช่น อาการบาดเจ็บที่เคยเป็น และโรคประจำตัว

---

## 1. ทำไมเรื่องนี้เปลี่ยนดีไซน์ระบบ (ไม่ใช่แค่ "เพิ่ม field")

ตอนนี้ระบบตอบคำถามเดียวคือ *"ผู้ใช้ทำท่าผิดตรงไหน และแก้ยังไง"*
พอมีประวัติสุขภาพเข้ามา ระบบต้องตอบเพิ่มอีก 2 คำถามที่มี **ความเสี่ยงด้านความปลอดภัย**:

1. *ท่านี้/คำแนะนำนี้ ปลอดภัยกับคนที่มีภาวะนี้หรือไม่* (contraindication)
2. *อาการผิดที่ตรวจพบ เกิดจากข้อจำกัดทางกายภาพเดิมหรือเปล่า* (เช่น heels lifting off ground มักมาจาก ankle dorsiflexion ที่จำกัด ซึ่งอาจเป็นผลจากประวัติข้อเท้าแพลง — ไม่ใช่แค่ "ไม่ตั้งใจ")

ข้อ 2 คือคุณค่าที่แท้จริงของฟีเจอร์นี้ และเป็นสิ่งที่ระบบคู่แข่งที่ดูแค่มุมข้อต่อทำไม่ได้

## 2. ความเสี่ยงที่ต้องตัดสินใจก่อนเริ่มทำ

- **ขอบเขตทางการแพทย์:** ทันทีที่ LLM เห็นคำว่า "โรคประจำตัว" มันจะเริ่มพูดจาแบบให้คำวินิจฉัย
  ต้องมี guardrail ชัดเจนใน prompt ว่าไม่ใช่การวินิจฉัย + ต้องมีเงื่อนไขที่ระบบ "ปฏิเสธที่จะแนะนำ" และบอกให้ไปพบผู้เชี่ยวชาญ
- **KB ปัจจุบันไม่รองรับ:** `curated_data/` เป็นความรู้เรื่อง "ท่าออกกำลังกาย" ไม่ใช่ "ข้อห้ามทางคลินิก"
  ถ้าไม่เติมแหล่งข้อมูลด้านนี้ LLM จะไปดึงจากความรู้ตัวเองล้วน ๆ (ซึ่ง `compare_result_local_curated_v5.md` พิสูจน์แล้วว่ามัน hallucinate สถิติได้แม้มี grounding rule)
- **ข้อมูลอ่อนไหว (PDPA):** ข้อมูลสุขภาพเป็นข้อมูลส่วนบุคคลอ่อนไหวตาม PDPA มาตรา 26 — ต้องมี consent แยก, encryption at rest, และ **ห้ามส่งเข้า prompt ของ LLM แบบระบุตัวตน** (ส่งเฉพาะ condition code ไม่ส่งชื่อ/เลขบัตร)

## 3. Data model ที่เสนอ (ต่อยอดจาก `docs/integration_plan.md` §3 Session History Store)

```
users
  user_id (PK)
  ...

user_health_profile
  user_id (FK)
  updated_at
  chronic_conditions []   -- code จาก controlled vocabulary เช่น 'knee_oa', 'lumbar_disc_herniation', 'hypertension'
  injury_history   []     -- { body_part, injury_code, side, occurred_on, status: active|recovered }
  mobility_limitations [] -- { joint, direction, note }  เช่น { ankle, dorsiflexion, 'limited' }
  self_reported (bool)    -- ผู้ใช้กรอกเอง vs มีเอกสารทางการแพทย์
  consent_version         -- สำหรับ PDPA audit trail
```

**สำคัญ:** แยกตารางออกจาก `sessions` เพราะเป็นข้อมูลที่เปลี่ยนช้าและมีชั้นความลับต่างกัน (สิทธิ์การเข้าถึงคนละระดับ)

## 4. จุดที่ประวัติสุขภาพเข้ามาเกี่ยวข้องในระบบ (4 จุด)

| # | จุด | ทำอะไร | ความยาก |
|---|---|---|---|
| 1 | **Retrieval query** | เพิ่ม query สายที่ 2 ต่อ 1 condition ที่ active เช่น `"squat modifications for knee osteoarthritis"` แล้ว merge กับ query ของ error ปกติ | ต่ำ — ต่อยอด per-error loop ที่มีอยู่ได้เลย |
| 2 | **KB coverage** | เพิ่มเอกสารกลุ่ม contraindication / rehab / exercise modification เข้า `data/` และเพิ่ม `item_kind` ใหม่ เช่น `contraindication`, `modification` | กลาง — ต้องหา source ที่น่าเชื่อถือ (ACSM, NSCA, physiotherapy guideline) |
| 3 | **Prompt** | เพิ่ม section `User Health Context` + กติกา: อธิบายว่า fault ที่พบ *อาจ* สัมพันธ์กับข้อจำกัดเดิม, ห้ามวินิจฉัย, ต้องแนะนำให้ปรึกษาผู้เชี่ยวชาญเมื่อเข้าเงื่อนไขเสี่ยง | ต่ำ |
| 4 | **Safety gate (deterministic)** | ตารางกฎ hard-coded นอก LLM: condition × exercise → `allow` / `modify` / `block` ทำงาน**ก่อน**เรียก LLM และ**ตรวจ output อีกครั้ง** ไม่ปล่อยให้ prompt เป็นด่านเดียว | กลาง — แต่จำเป็น เพราะ v5 พิสูจน์แล้วว่า prompt rule อย่างเดียวเอาไม่อยู่ |

## 5. เชื่อมกับสิ่งที่มีอยู่แล้ว

- ต่อยอดจาก `error_type` taxonomy (`docs/error_type_taxonomy.md`): แต่ละ fault ควรมี `likely_physical_causes[]`
  เช่น `heels_lifting` → `["limited_ankle_dorsiflexion"]` ทำให้ระบบเชื่อม "อาการที่ตรวจพบ" กับ "ประวัติ" ได้แบบ deterministic ไม่ต้องพึ่ง LLM เดา
- `historical_comparison` ที่มีอยู่คือประวัติ **ผลการทำท่า** ส่วนนี้คือประวัติ **ตัวผู้ใช้** — คนละแกน ควรเก็บคนละตาราง แต่ join ด้วย `user_id` เดียวกัน

## 6. ลำดับที่แนะนำ

ทำ **หลัง** ปิดงาน retrieval quality (fault-name taxonomy + kind filter + source citation) เพราะถ้าฐาน retrieval ยังดึงของผิดอยู่ การเติมมิติสุขภาพเข้าไปจะขยายความเสียหาย ไม่ใช่ลด — และครั้งนี้ผลเสียคือคำแนะนำที่อาจทำให้ผู้ใช้บาดเจ็บซ้ำ

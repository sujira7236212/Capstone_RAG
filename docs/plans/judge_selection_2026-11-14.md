# บันทึกการเลือก judge: pairwise eval v2 (2026-11-14)

> สถานะ: **ตัดสินใจแล้ว รอสอบ §6** · ยังไม่ได้เรียก API · เอกสารนี้แทนตาราง judge ใน §2 ของ `pairwise_eval_v2_plan.md` (5 พ.ย.) และสรุปต่อจาก `pairwise_eval_v2_review_2026-11-12.md` §2

## 1. ข้อสรุป

| บทบาท | โมเดล | `--judge` | ค่าย | เรียกผ่าน | key |
|---|---|---|---|---|---|
| Judge 1 | gpt-oss-20b | `groq:openai/gpt-oss-20b` | OpenAI (US) | Groq | มีแล้ว |
| Judge 2 | Qwen3.8-27B | `groq:qwen/qwen3.8-27b` | Alibaba (จีน) | Groq | มีแล้ว |
| Judge 3 | DeepSeek V4.1 Flash | `deepinfra:<model id ของ DeepSeek V4.1 Flash>` | DeepSeek (จีน) | DeepInfra | **ยังไม่มี** ต้องสมัคร |
| สำรอง 1 | Nemotron 3.5 Lightning 30B-A3B | `deepinfra:<id>` หรือผ่าน OpenRouter | NVIDIA (US) | DeepInfra · OpenRouter (มีรุ่นฟรี) | ใช้ key DeepInfra เดียวกัน |
| สำรอง 2 | Mistral Small 4 | ยังไม่กำหนด | Mistral (EU) | Mistral API | ต้องสมัครเพิ่ม |

- ตัดสินต่อข้อด้วยเสียงข้างมากของ 3 judge และรายงานสัดส่วน 3-0 กับ 2-1
- ทุกตัวต้องผ่านการสอบ §6 ก่อนใช้จริง ถ้าตัวใดไม่ผ่าน ให้ใช้สำรอง 1 แล้วสำรอง 2 ตามลำดับ
- ต้องตรวจ model id บน DeepInfra ก่อนรัน

## 2. ทำไมเลือกแต่ละตัว

| โมเดล | ทำไมเลือก | ต้องระวัง |
|---|---|---|
| gpt-oss-20b | ใช้ฟรี · โค้ดรองรับ `reasoning_effort` แล้ว · มี key แล้ว | MoE 21B แต่ทำงานจริงแค่ 3.6B · free tier ราว 200K token/วัน (1.5M token ≈ 8 วัน) |
| Qwen3.8-27B | Intelligence Index 34 · มี key แล้ว · เดิมเป็นตัวสำรอง เลื่อนขึ้นมาเป็นตัวหลัก | เป็นรุ่น Preview อาจถูกถอด (3.6 ถูกถอดเมื่อ ก.ย. 2026) · **ห้ามใช้ตัดสินคำตอบที่สร้างด้วย Qwen** |
| DeepSeek V4.1 Flash | เก่งที่สุดในกลุ่มที่พิจารณา (Index ~33–39) · open weights · ราคาถูก (~$0.10–0.20 in / $0.29–0.60 out ต่อล้าน token) | MoE ใหญ่ ไม่ใช่ ~27B · ภูมิภาคเดียวกับ Qwen · ตอบยาว token output อาจบวม ต้องจำกัด reasoning |
| Nemotron 3.5 Lightning (สำรอง 1) | ต่างภูมิภาคจากอีกสองตัว · AA-Omniscience −16 (Glimmer −33) · มีรุ่นฟรีบน OpenRouter | ความสามารถทั่วไปใกล้ Glimmer · ทำงานจริงแค่ 3B เหมือน gpt-oss-20b |
| Mistral Small 4 (สำรอง 2) | ต่างภูมิภาค (EU) · AA วัดได้ 27 ตอนเปิดตัว (โหมด reasoning) | ตัวเลขจากแต่ละแหล่งขัดกัน · ต้องสมัคร key Mistral เพิ่ม |

## 3. เกณฑ์คัดกรอง

| เกณฑ์ | สถานะ | เหตุผล |
|---|---|---|
| 3 ค่ายไม่ซ้ำกัน | ใช้ | กันไม่ให้ความลำเอียงของโมเดลเดียวกลายเป็นผลการทดลอง |
| ไม่ใช้ Gemini | ใช้ | Gemini เป็น generator และ curator |
| ไม่ใช้ Claude | ใช้ | Claude เขียน checklist เฉลย และข้อสอบ ถ้าใช้ก็เท่ากับตรวจข้อสอบตัวเอง |
| open weights | ใช้ | ถ้า API ปิด ยังรันซ้ำผ่าน provider อื่นได้ |
| ขนาดใกล้ 27B (21–30B) | **ยกเลิก** | ไม่มีเหตุผลทางวิธีวิจัย |
| ไม่ใช้ Alibaba | **ยกเลิก** | เลื่อน Qwen3.8-27B เป็นตัวหลักแล้ว · ยังคงกฎห้ามใช้ Qwen ตัดสินคำตอบที่ Qwen สร้าง |
| ไม่ต้องเป็นโมเดลเฉพาะทางฟิตเนส | ใช้ | FitOne ไม่มี API และวัดแค่การตอบข้อสอบ · PH-LLM มาจาก Gemini · persona "ผู้เชี่ยวชาญ" ไม่ช่วยให้ตอบถูกขึ้น (Wharton) · ความเชี่ยวชาญต้องมาจาก rule card ที่ผู้เชี่ยวชาญอนุมัติและการสอบ §6 |

**ข้อสังเกต:** judge 2 ตัว (Qwen, DeepSeek) มาจากจีนเหมือนกัน ยังนับเป็น 3 ค่าย แต่ความหลากหลายด้านภูมิภาคลดลง ถ้าผลเปลี่ยนเมื่อตัด judge ตัวใดออก ต้องระบุในรายงาน (§7)

## 4. ตัวตัดสินจริง: การสอบ §6

ตัวเลข Intelligence Index แต่ละแหล่งใช้ index คนละรุ่น เทียบข้ามแหล่งตรง ๆ ไม่ได้ จึงใช้ผลสอบเป็นตัวตัดสิน

| วัดอะไร | เกณฑ์ผ่าน | ถ้าไม่ผ่าน |
|---|---|---|
| Detection: จับข้อผิดที่ฝังไว้ได้ | ≥ 80% (A5 ≥ 90%) | แก้พรอมต์ หรือเปลี่ยนโมเดล |
| False alarm: ตอบ no ผิดบนคำตอบต้นแบบ | ≤ 10% | แก้พรอมต์ หรือเปลี่ยนโมเดล |
| Cross-talk: ฝังข้อเดียวแล้วข้ออื่นเปลี่ยนตาม | ≤ 10% | แยก call ตามเกณฑ์ |
| ลงโทษข้อเท็จจริงที่ถูกแต่อยู่นอกเฉลย | ≤ 1 จาก 8 ต่อ judge | แก้พรอมต์ ถ้ายังไม่ผ่านให้เปลี่ยนโมเดล |
| ทำตามเฉลยที่ถูกสลับ | ≥ 80% | **เปลี่ยนโมเดล** (แก้ด้วยพรอมต์ไม่ค่อยได้) |
| รายข้อ: judge ≥ 2 ใน 3 จับได้ ≥ 2 ใน 3 ชุด | ทุกข้อ | เขียนข้อใหม่ หรือใช้ข้อสำรอง |

**ห้ามใช้ accuracy รวม:** ในคำตอบกลายพันธุ์ 20 ข้อ มีเฉลยเป็น yes อยู่ 19 ข้อ judge ที่ตอบ yes ทุกข้อจะได้ 19/20 = 95% ทั้งที่ detection = 0%

**กติกาเลือกตัวที่ 3 (เขียนไว้ก่อนรัน):** ให้ DeepSeek V4.1 Flash และ Nemotron 3.5 Lightning สอบ §6 ด้วยกัน
1. ถ้า DeepSeek ผ่านทุกเกณฑ์ → ใช้ DeepSeek
2. ถ้า DeepSeek ไม่ผ่าน แต่ Nemotron ผ่าน → ใช้ Nemotron
3. ถ้าไม่ผ่านทั้งคู่ → สอบ Mistral Small 4
4. ถ้า gpt-oss-20b หรือ Qwen3.8-27B ไม่ผ่าน → ใช้ตัวสำรองที่ผ่านแทนตามลำดับเดียวกัน

## 5. ตัวที่ตัดออก

| โมเดล | เหตุผล |
|---|---|
| Muse Glimmer 30B (Meta) | ความสามารถทั่วไปต่ำสุดในกลุ่ม (Intelligence Index 17 ขณะที่ Qwen3.8-27B ได้ 34 ในการวัดชุดเดียวกัน) · **แก้ข้อมูลเดิม:** hallucination 82% ไม่ได้ผิดปกติ (DeepSeek V4 Flash 84%, Mistral Medium 3.5 82%) และตัวชี้วัดนี้ไม่ได้วัดว่าโมเดลทำตามเฉลยหรือไม่ |
| Mistral Small 3.2 (DeepInfra) | Mistral ประกาศเลิกให้บริการแล้ว |
| gpt-oss ผ่าน Cerebras | เลิก free tier เหลือเครดิตทดลองครั้งเดียว |
| Gemini | เป็น generator และ curator |
| Claude | เขียน checklist เฉลย และชุดทดสอบ |
| FitOne | ไม่พบว่าเปิด weights หรือมี API · วัดแค่ข้อสอบ ACSM-EP / NSCA-CSCS ไม่ได้วัดการตัดสิน feedback |
| PH-LLM (Google) | fine-tune จาก Gemini |

## 6. งบและโควตา

| รายการ | ค่า |
|---|---|
| ต่อ judge (ตามแผนเดิม) | 335 call × (input 4,000 + output 500) ≈ 1.5M token |
| ทั้งแผน (P4–P7) | judge 1,005 ครั้ง ≈ 4.5M token |
| Groq | จำกัดราว 8K token/นาที · free tier ราว 200K token/วัน → ถ้ารันฟรีอาจใช้เวลาหลายวัน ต้องเช็กโควตาจริงก่อน |
| DeepSeek V4.1 Flash | ราว $0.10–0.20 in / $0.29–0.60 out ต่อล้าน token · ต้องจำกัด reasoning เพราะ output อาจบวม |

ทุกขั้นที่เรียก API ต้องขออนุมัติก่อน พร้อมตัวเลขจาก `--estimate`

## 7. สิ่งที่ต้องทำต่อ

- [ ] สมัคร key DeepInfra (ใช้กับ DeepSeek V4.1 Flash และ Nemotron)
- [ ] ตรวจ model id ของ DeepSeek V4.1 Flash และ Nemotron บน DeepInfra
- [ ] ตั้งเพดาน reasoning / max output ของ DeepSeek
- [ ] อัปเดต §2 ใน `pairwise_eval_v2_plan.md`: ตาราง judge, เกณฑ์ "ไม่ใช่ Alibaba", เกณฑ์ขนาด และคำถามเปิดข้อ 3 (key DeepInfra ยังเขียนว่าใช้กับ Glimmer และ Mistral Small 3.2)
- [ ] แก้วันที่ Mistral Small 3.2 เลิกให้บริการให้ตรงกัน (แผนหลักเขียน 30 ก.ค. 2026 ส่วนเอกสารทบทวนเขียน 30 เม.ย. 2026)
- [ ] ยืนยันว่า generator ไม่มีฝั่งไหนใช้ Qwen (กฎห้าม Qwen ตัดสินคำตอบของ Qwen)
- [ ] รันสอบ §6 ตามกติกาในหัวข้อ 4

## แหล่งอ้างอิง

- `docs/plans/pairwise_eval_v2_plan.md` §2, §6
- `docs/plans/pairwise_eval_v2_review_2026-11-12.md` §2
- [Artificial Analysis: Qwen3.8 27B vs Muse Glimmer](https://artificialanalysis.ai/models/comparisons/qwen3-8-27b-vs-muse-glimmer)
- [DeepSeek V4 Flash 0731 hallucination rate 84% (Implicator)](https://www.implicator.ai/deepseeks-retrained-v4-flash-scores-50-on-independent-intelligence-index/)
- [DeepSeek V4.1 Flash บน DeepInfra](https://www.requesty.ai/models/deepinfra/deepseek-v4.1-flash-1017) · [Artificial Analysis: DeepSeek V4.1 Flash](https://artificialanalysis.ai/ja/models/releases/deepseek-v4-1-flash)
- [Artificial Analysis: Nemotron 3.5 Lightning](https://artificialanalysis.ai/articles/nemotron-3-5-lightning-launch)
- [Artificial Analysis: Mistral Small 4 เปิดตัว](https://x.com/ArtificialAnlys/status/2034960206736892365)
- [Mistral Small 3.2 deprecated](https://docs.mistral.ai/models/mistral-small-3-2-25-06)
- [Reliability without Validity (arXiv 2606.19544)](https://arxiv.org/abs/2606.19544): อันดับ judge เปลี่ยนได้ถึง 14 อันดับเมื่อเปลี่ยน benchmark
- [FitOne](https://arxiv.org/abs/2607.02118) · [Wharton Prompting Science Report 4](https://arxiv.org/abs/2512.05858)

# ตรวจเนื้อหา KB ราย fault: context ปัจจุบัน vs ทั้ง KB (2026-11-14)

> ขั้น 1 ของ §3.4 ใน `docs/plans/pairwise_eval_v2_review_2026-11-12.md` · ไม่เรียก API · KB `kb_gemini_curated_v6b` (2,197 chunk) โหลดจาก `app_setup/kb_dump.sql.gz` ลง podman · retrieval ใช้ config ปัจจุบัน (TAG_MODE strict, FIX_SLOT ปิด) และ query vector จาก cache
>
> ตรวจความถูกต้อง: context ของ set squat 3 fault ใน `capture/v18b_trial.jsonl` ที่ดึงใหม่ตรงกับที่ capture ไว้ทุกไบต์
>
> ผู้ตัดสินแต่ละช่องคือ Claude ไม่ใช่ผู้เชี่ยวชาญ

## สรุป

1. **context ตอนนี้แทบไม่มีวิธีแก้เลย** ช่อง drill กับ setup ว่างใน 10 จาก 12 กฎ มีแค่ knee_valgus ("ใช้ resistance band") กับ hip_sag_or_pike ("plank สม่ำเสมอ") และทั้งสองประโยคไม่มี dose
2. **KB มีวิธีแก้แต่ดึงไม่ถึง** ใน 11 จาก 12 กฎ (◐ ในตาราง) เพราะ quota ของ principle 2 ชิ้นถูกใช้กับประโยค "ท่าที่ถูกคืออะไร" ไปแล้ว และวิธีแก้หลายประโยคไม่ติด tag (โดยเฉพาะ lunge) จึงถูก strict กันไว้ · `FIX_SLOT` (pool `open`) ถูกออกแบบมาแก้ทั้งสองเรื่องนี้
3. **KB ไม่มีจริง (✗)** ได้แก่ drill ของ knee_varus, elbow_flare และ partial_curl · สาเหตุเฉพาะของ knee_varus, excessive_front_knee_flexion และ straight_back_leg · ช่องพวกนี้ต้องเติม KB ถ้าอยากให้ RAG ชนะ
4. **C2 (สาเหตุเฉพาะ) ไม่ใช่ข้อที่ชนะแน่** อย่างที่รีวิวคาดไว้: context มีสาเหตุเฉพาะแค่ 6 กฎ · forward_trunk_lean ("muscle imbalance") กับ partial_curl ได้แค่สาเหตุลอย ๆ ซึ่ง C2 นับ no
5. self-check (F4) ที่ผู้ใช้สังเกตเองได้มีน้อย และส่วนใหญ่เป็นศัพท์เทคนิค (medial malleolus, patella) · ตัวที่ดีที่สุดคือ dowel แตะ 3 จุด (กระดูกก้นกบ, หลังส่วนบน, ท้ายทอย) ของ rounded_back ซึ่งยังดึงไม่ถึง

## ตาราง

✓ = อยู่ใน context แล้ว · ◐ = KB มีแต่ไม่ถูกดึง · ✗ = KB ไม่มี · "อ่อน" = มีแต่ไม่น่าผ่านเกณฑ์ของข้อ (ลอย ใช้กับ fault อื่นได้ หรือเป็นศัพท์ล้วน)

| กฎ | สาเหตุเฉพาะ (C2) | ผลต่อร่างกาย (C3) | cue (D1 F1) | drill (D3) | setup (F2 D2) | self-check (F4) | chunk |
|---|---|---|---|---|---|---|---|
| squat/partial_squat | ✓ ข้อเท้า/สะโพกตึง | ✓ ต้นขาหลัง ก้น ไม่ได้ทำงาน | ✓ อ่อน (เป้า "ต้นขาขนานพื้น") | ◐ ยืดน่อง ข้อเท้าท่าคุกเข่า ยืดต้นขาหลัง | ◐ ยกส้นเท้า, ยืนกว้างขึ้นถ้าข้อเท้าตึง | ✓ อ่อน (สะโพกระดับเข่า) | 8 |
| squat/knee_valgus | ✓ เท้าล้ม, สะโพกด้านข้างอ่อน (ศัพท์) | ✓ เอ็นรอบเข่า | ✓ "knees out" | ✓ อ่อน "ใช้ band" · ◐ clamshell, box squat + band, foam roll 2 นาที, ยืด 2 × 30 วินาที | ◐ แผ่นรองส้น 2 นิ้ว, ยืนกว้างปานกลาง | ✓ อ่อน (ลูกสะบ้าเลยนิ้วโป้งเข้าด้านใน · ศัพท์) | 9 |
| squat/knee_varus | ✗ | ✓ เอ็นด้านนอกเข่า (LCL ศัพท์) | ✓ อ่อน "เข่าตามปลายเท้า" (ใช้กับ valgus ได้ด้วย) | ✗ | ◐ แผ่นรองส้น (heel lift), ปลายเท้าเปิด ~20°, ยืนกว้างเท่าไหล่ | ✗ | 9 |
| squat/rounded_back | ✓ สะโพกพับได้น้อย/คุมหลังล่างไม่ได้ (ศัพท์) | ✓ หลังล่าง | ✓ อกตั้ง สะบักบีบ | ◐ hip hinge + dowel, ฝึกคุมเชิงกรานนอนหงาย→คลาน, bridge + band | ◐ goblet squat, ยืนกว้างขึ้น | ◐ dowel แตะ 3 จุด | 9 |
| push-up/hip_sag_or_pike | ✓ ไม่เกร็งแกนกลาง/ก้น | ✓ หลังล่างแอ่น | ✗ ใน context (ศัพท์ล้วน) · ◐ เกร็งท้อง บีบก้น ตัวตรงหัวถึงส้น | ✓ plank (ไม่มี dose) · ◐ anti-extension ไล่ระดับ | ◐ ลงเข่าโดยสะโพกตรงแนวไหล่ | ◐ อ่อน | 9 |
| push-up/partial_pushup | ✗ ใน context · ◐ อ่อน "ถ้าแรงไม่พอ" | ✓ อกไม่ได้ทำงานเต็มที่ | ✓ อกนำลง, ศอก 90° | ◐ negative push-up | ◐ มือวางบนม้านั่ง/ผนัง, ลงเข่า | ✓ อกเกือบแตะพื้น | 9 |
| lunge/shallow_lunge | ✓ ต้นขาหน้าอ่อน/ข้อเท้าตึง | ✓ อ่อน (กล้ามโตน้อยลง) | ✓ เข่าหลังเกือบแตะพื้น | ◐ ไล่ความลึกบนแท่น 10 ซม., เก้าอี้รองก้น | ◐ จับของมั่นคง, เท้าหน้าบนขั้นบันได, ตั้งระยะก้าวจากท่าคุกเข่าข้างเดียว | ✓ เข่าหลังแตะหรือเกือบแตะพื้น | 9 |
| lunge/excessive_front_knee_flexion | ✗ | ✓ เอ็นลูกสะบ้า/ข้อเข่าหน้า (ศัพท์) | ✓ อ่อน (เข่าหน้า 90–100° · อีก 2 ชิ้นพูดเรื่องเข่าเลยปลายเท้า ซึ่งเป็น fault ที่ taxonomy เว้นไว้) | ◐ อ่อน (โปรแกรมไล่มุมเข่าแบบฟื้นฟู) | ◐ ท่า 90/90 | ✗ | 9 |
| lunge/forward_trunk_lean | ✓ อ่อน "muscle imbalance" (ลอย) | ✓ แรงเฉือนที่เข่า, หลังล่าง | ✓ ลำตัวตั้งตรง · ◐ "กระดูกอกขึ้นลงแบบลิฟต์ ไม่ใช่บันไดเลื่อน" | ◐ อ่อน (Bulgarian split squat) | ◐ จับของมั่นคง | ✓ อ่อน (เอียง 0–20° ดูเองไม่ได้) | 9 |
| lunge/straight_back_leg | ✗ | ✓ แรงที่เข่า, ปวดเข่า | ✓ ลดเข่าหลังลงพื้น | ◐ ใช้ผนังช่วยดันเท้าหลังให้เขย่ง | ◐ ระยะก้าวสั้นลงให้เข่าหลังงอมากขึ้น, ท่าคุกเข่าข้างเดียว | ✓ เข่าหลังแตะพื้นเบา ๆ | 4 |
| bicep-curl/elbow_flare | ✓ ล้า, ใช้แรงเหวี่ยง | ✓ ไบเซ็ปทำงานน้อยลง | ✓ อ่อน "ไหล่นิ่ง" · ◐ ศอกแนบลำตัว | ✗ | ◐ นั่งพิงพนัก, น้ำหนักเบาลง | ✗ | 9 |
| bicep-curl/partial_curl | ✗ (มีแค่พฤติกรรม "เริ่มจากศอกงอ 20°") | ✓ อ่อน (กล้ามโตน้อยลง) | ✓ เหยียดสุดถึงงอสุด | ✗ (มีแค่ "หยุดค้างปลายทาง" ซึ่ง D3 นับ no) | ◐ ทำเครื่องหมาย/จุดหยุดให้เห็น | ✗ | 9 |

รวม context 102 chunk (straight_back_leg ได้แค่ 4 และ partial_squat ได้ 8 เพราะ margin)

## ตัวเลข

- principle ทั้ง KB ที่มีคำบอกวิธีแก้ (drill, band, stretch, heel, box, incline, tempo ฯลฯ ค้นด้วยข้อความ): 270 จาก 834 ชิ้น
- ในจำนวนนี้ติด tag ของกฎใดกฎหนึ่ง 83 ชิ้น ไม่ติด tag 187 ชิ้น (lunge 99, push-up 35, squat 33, curl 18, general 2)
- กระจุกตัว: squat/rounded_back 31, squat/knee_valgus 18 · lunge ทั้ง 4 กฎรวมกันติด tag แค่ 7 ชิ้น

## ผลต่อขั้นถัดไป

- `FIX_SLOT` เพิ่ม principle ได้ **1 ชิ้นต่อ fault** แต่ช่องที่เป็น ◐ ต่อกฎมีทั้ง drill, setup และ self-check · 1 ชิ้นจึงน่าจะแก้ได้แค่ 1 ใน D2, D3, F2, F4 ต่อกฎ · ต้องดูอันดับที่ fix_query ดึงได้จริงก่อนตัดสินว่าจะเป็น 1 หรือ 2 ชิ้น
- pool `open` จำเป็นสำหรับ lunge เพราะวิธีแก้ของ lunge เกือบทั้งหมดไม่ติด tag
- ช่อง ✗ ใน drill (knee_varus, elbow_flare, partial_curl) แก้ด้วย retrieval ไม่ได้ ต้องเติม KB
- ทุกอย่างต้องทำก่อน freeze prompt และก่อนสร้างคำตอบ test

## ผลทดลอง FIX_SLOT (2026-11-14 หลัง embed fix_query 12 ข้อความ)

> embed ด้วย `python tools/fill_query_cache.py` (user อนุมัติ) · ที่เหลือไม่เรียก API · ช่อง setup ของ knee_varus ในตารางข้างบนแก้แล้ว (รอบแรกค้นข้อความพลาด "heel lifts")

ประโยคที่ `FIX_SLOT` เลือก (1 ชิ้นต่อ fault) ตัดสินโดย Claude ว่า "ดี" = วิธีแก้ที่ลงมือได้และเฉพาะกับ fault นี้

| กฎ | pool `open` (ค่าเริ่มต้น) | pool `tagged` |
|---|---|---|
| squat/partial_squat | พอใช้: เพิ่มความยืดหยุ่นข้อเท้าและสะโพก (ทิศทาง ไม่ใช่ท่าฝึก) | เหมือนกัน |
| squat/knee_valgus | ไม่ดี: "ปรับความกว้างและองศาเท้าตามสรีระสะโพก" (กว้าง) | พอใช้: แก้ข้อเท้าตึง |
| squat/knee_varus | ไม่ดี: ประโยคเดียวกับ knee_valgus | **ดี:** แผ่นรองส้นหรือเสริมแรงข้อเท้า |
| squat/rounded_back | **ดี:** หายใจและเกร็งท้องก่อนทุก rep | เหมือนกัน |
| push-up/hip_sag_or_pike | ไม่ดี: "รับรู้ตำแหน่งหลังล่าง" (กว้าง) | เหมือนกัน |
| push-up/partial_pushup | **ไม่ดีและสวนทาง:** "ลดระยะ push-up ชั่วคราว" (ทำให้ partial ดูโอเค) | **ดี:** ลงเข่าหรือวางมือบนที่สูง |
| lunge/shallow_lunge | **ดี:** ไล่ความลึกบนแท่น 10 ซม. | ไม่ดี: พูดเป้ามุมเข่าซ้ำ |
| lunge/excessive_front_knee_flexion | ไม่ดี: "แก้ท่าก่อนเพิ่มน้ำหนัก" (กว้าง) | **ไม่ดีและผิดเรื่อง:** เข่าไม่เลยปลายเท้า (fault ที่ taxonomy เว้นไว้) |
| lunge/forward_trunk_lean | ไม่ดี: "ถอยระดับก่อน" (กว้าง) | ไม่ดี: พูดหลักลำตัวตรงซ้ำ |
| lunge/straight_back_leg | ไม่ดี: ประโยคเดียวกับ forward_trunk_lean | **ดี:** ใช้ผนังช่วยเท้าหลัง |
| bicep-curl/elbow_flare | ไม่ดี: พูดหลัก "ไหล่นิ่ง" ซ้ำ | เหมือนกัน |
| bicep-curl/partial_curl | ไม่ดี: พูดหลัก full ROM ซ้ำ | เหมือนกัน |
| **รวม ดี / พอใช้** | **2 / 1 จาก 12** | **4 / 2 จาก 12** |

**ทำไมได้ผลน้อย:** `fix_query` ทุกกฎขึ้นต้นเหมือนกันว่า "Practical drills, easier variations and setup changes that help someone ..." ส่วนที่ซ้ำนี้ครอบ vector ไว้ ประโยคกว้าง ๆ เรื่อง "ปรับ setup / ถอยระดับ" จึงชนะในหลายกฎ (ประโยคเดียวกันชนะทั้ง valgus กับ varus และทั้ง forward_trunk_lean กับ straight_back_leg) · ส่วนท้าย "help someone hold the knees out" บรรยายท่าที่ถูก จึงดึง principle ที่พูดท่าถูกซ้ำ

**ขยายผู้สมัครเป็น 40 แล้วคัดด้วยคำบอกการลงมือ (ฟรี):** ไม่ช่วย ประโยคดีที่รู้ว่ามี (clamshell + band, แผ่นรองส้น 2 นิ้ว, box squat + band) ไม่ติด 40 อันดับแรกเลย

**สรุป:** อย่าเปิด `FIX_SLOT` ด้วย `fix_query` ชุดนี้ · ต้องแก้ที่ข้อความ query

## fix_query ชุดใหม่ (2026-11-14 รอบ 2)

> เขียนจาก rule card (`relevant_info.fixes` ที่เป็น drill / setup / regression + `causes`) แต่ละข้อขึ้นต้นต่างกัน ปิดท้ายด้วยคำบรรยาย fault สั้น ๆ · squat, lunge, push-up ไม่มีเรื่องน้ำหนัก · embed 12 ข้อความ (user อนุมัติ) · แก้ใน `error_taxonomy.py` แล้ว ยังไม่ commit
>
> `eval/check_rule_cards.py --queries`: elbow_flare ซ้ำ KB v5 6 คำ ("with the back against a wall") ต้องเขียนใหม่ก่อน commit

| กฎ | `open` | `tagged` |
|---|---|---|
| squat/partial_squat | พอใช้: ความยืดหยุ่นข้อเท้า (ทิศทาง) | เหมือนกัน |
| squat/knee_valgus | **ดี:** band รอบต้นขา (+ ยืนกว้าง ในบริบทฟื้นฟู) | **ดี:** clamshell + band |
| squat/knee_varus | ไม่ดี: "ปรับความกว้างตามสรีระ" (กว้าง) | **ดี:** ปลายเท้าเปิด ~20° + ยืนกว้างเท่าไหล่ |
| squat/rounded_back | **ดี:** หายใจและเกร็งท้องก่อนทุก rep | เหมือนกัน |
| push-up/hip_sag_or_pike | ไม่ดี: กว้าง (plank อยู่ใน context อยู่แล้วจึงถูกตัดเป็นประโยคซ้ำ) | เหมือนกัน |
| push-up/partial_pushup | **ดี:** negative push-up พร้อมวิธีทำ | **ดี:** ลงเข่าหรือมือบนที่สูง |
| lunge/shallow_lunge | พอใช้: เก้าอี้รองก้น (ช่วยพยุง แต่ลดระยะ) | ไม่ดี: พูดเป้ามุมเข่าซ้ำ |
| lunge/excessive_front_knee_flexion | **ดี:** ก้าวยาวขึ้น (ประโยคพูดถึงเข่าเลยปลายเท้าด้วย) | ไม่ดีและผิดเรื่อง: เข่าไม่เลยปลายเท้า |
| lunge/forward_trunk_lean | ไม่ดี: กว้าง | ไม่ดี: พูดหลักลำตัวตรงซ้ำ |
| lunge/straight_back_leg | **ดี:** ระยะก้าวแคบลงให้เข่าหลังงอมากขึ้น | **ดี:** ใช้ผนังช่วยเท้าหลัง |
| bicep-curl/elbow_flare | ไม่ดี: ผิดเรื่อง (เปลี่ยนบาร์เป็นดัมเบลเพราะเจ็บแขน) | ไม่ดี: พูดหลักซ้ำ |
| bicep-curl/partial_curl | ไม่ดี: ผิดเรื่อง (เหวี่ยงตัว) | ไม่ดี: พูดหลักซ้ำ |
| **รวม ดี / พอใช้** | **5 / 2** (รอบแรก 2 / 1) | **5 / 1** (รอบแรก 4 / 2) |

- ที่ยังไม่ดีตรงกับช่องที่ KB ไม่มีเกือบทั้งหมด: forward_trunk_lean (ไม่มีการยืดกล้ามงอสะโพกขาหลัง), elbow_flare และ partial_curl (ไม่มี drill) · hip_sag_or_pike มี plank ใน context อยู่แล้ว
- ลองให้ pool `open` เพิ่มคะแนนประโยคที่ติด tag (0.03 เท่า TAG_BONUS) แย่ลง เพราะดึง principle ที่พูดท่าถูกซ้ำ
- ถ้าใช้ `tagged` กับ squat, push-up, curl และ `open` กับ lunge (วิธีแก้ของ lunge ไม่ติด tag ตามผลตรวจข้างบน) จะได้ ดี 6 พอใช้ 2 และไม่มีประโยคผิดเรื่อง · ตัวเลือกนี้เลือกหลังเห็นผล แต่ยังไม่ได้สร้างคำตอบ test จึงไม่ใช่การจูนกับชุด test

## เลือก pool (2026-11-14)

user เลือกแบบผสม: `FIX_POOL = "tagged"` + `FIX_POOL_BY_EXERCISE = {"lunge": "open"}` ใน `rag_core/retrieval.py` (test ใน `tests/test_fix_slot.py`) · `FIX_SLOT` ยังปิด รอ user เติม KB แล้ว embed chunk ใหม่ + `fix_query` ของ elbow_flare แล้วรันเทียบอีกรอบก่อนเปิด

## เติม KB รอบ 5 แล้วรันซ้ำ (2026-11-14)

> user สั่ง · curate batch `round5` = Fitness Volt + Built With Science (`data/bicep-curl/elbow_away/urls.txt`) และ Catalyst Athletics (`data/squat/knee_varus/urls.txt`) · การคัดอยู่ใน `docs/kb/prefilter_v6_review.md` §12 · gemini-3.6-flash 6 call ≈ $0.17 · mismatch 0 · split รอบ `v6c` (Catalyst ได้ test, 2 บทความ curl ได้ dev) · ingest **ลง container `kbaudit` เท่านั้น** (`kb_gemini_curated_v6b` 2,197 → 2,262 chunk, embed 65) · embed `fix_query` ของ elbow_flare แล้ว (ผ่าน `check_rule_cards.py --queries --kb curated_data_v6`, 0 hit) · ฐานข้อมูลของแอป, `app_setup/kb_dump.sql.gz` และ `app_setup/gemini-embedding-2.json` **ยังไม่อัปเดต** · FIX_SLOT ยังปิด

**curator ได้อะไร:** elbow_flare ได้ mistake/consequence เพิ่ม (ศอกแกว่งไปหน้าเพราะหนักเกิน → ไหล่หน้าทำงานแทน) แต่ **ไม่ได้ wall curl ออกมาเป็น item** (ตารางของ Fitness Volt ถูกย่อเป็นหลักการ "ต้นแขนนิ่ง") · partial_curl ได้ "เกร็งหลังแขนให้แขนตรงก่อนเริ่มครั้งต่อไป" (ติด tag) · knee_varus ได้ mistake 1 ข้อ "ดันเข่าออกเลยแนวเท้าทั้งที่แนวเข่าดีอยู่แล้ว" · ไม่มี item ที่สนับสนุน incline curl หรือครึ่งท่าแบบติด tag · ข้อสังเกต: item "mini-band รอบเข่ามักไม่ได้ผล" ติด `knee_valgus` อาจขัดกับ item อื่นที่แนะนำยางยืด

**ผลต่อ context (ฟรี, 12 กฎ ทีละ fault + dev 7 set):**

| กฎ | context เดิม (FIX_SLOT ปิด) | FIX_SLOT |
|---|---|---|
| elbow_flare | ประโยคใหม่เข้ามาแทนของเดิมที่ความหมายใกล้กัน · ผลระบุ "ไหล่หน้า" ชัดขึ้นเล็กน้อย | ไม่ดี: "ไหล่นิ่ง" ซ้ำหลัก |
| partial_curl | mistake เปลี่ยนเป็นเรื่อง**ไม่เหยียดข้างล่าง** 4 ประโยค ตรงกับด้านที่ rule จับมากกว่าเดิม | ไม่ดี: "ลงจนเกือบเหยียดสุด" ซ้ำหลัก (เดิม "ยกให้สูงสุด") |
| knee_varus | ไม่เปลี่ยน · ประโยคสาเหตุใหม่อยู่อันดับ 7 ของ mistake (ระยะ 0.153 vs อันดับ 1 0.058) โควตา 3 ช่องถูกประโยคนิยามอาการใช้หมด | เหมือนเดิม (ดี) |
| knee_valgus | ได้ผลต่อลำตัวโน้ม (C3 เฉพาะ) + หลักการกว้าง ๆ · **เสีย** "เท้าแบน (over-pronation) → เข่าบิดเข้า" (สาเหตุเฉพาะ) และ "ใช้ยางยืด" | เหมือนเดิม (ดี) |
| อีก 8 กฎ | ไม่เปลี่ยน | เหมือนเดิม |

FIX_SLOT ยังเป็น ดี 6 · พอใช้ 2 · ไม่ดี 4 (เพิ่ม elbow_flare ที่วัดได้แล้ว) · **drill ใหม่ = 0** · ช่อง ✗ ที่ปิดได้จริงใน context: ไม่มี (สาเหตุ knee_varus อยู่ใน KB แล้วแต่ดึงไม่ถึง)

**สรุป:** รอบนี้แทบไม่เพิ่มโอกาสชนะ · ที่เหลือมี 3 ทาง: (1) แก้ retrieval ให้สาเหตุเข้าได้ (เช่นให้ FIX_SLOT หรือช่องใหม่ค้นใน mistake ด้วย fix_query ฟรี ไม่ต้อง embed chunk) · (2) โน้ตผู้เชี่ยวชาญที่มี drill + dose (`kb_gap_sources_2026-11-14.md` §5 ต้องให้ Ton รับรอง) · (3) ยอมรับแล้วไป freeze และรายงานตามจริง (ขั้น 5 ของแผน)

## ทาง 1: FIX_SLOT บนช่อง mistake ด้วย (2026-11-14)

> user สั่ง · ไม่มีการเรียก API (ใช้ vector ใน cache และ KB ใน `kbaudit`) · โค้ด: `FIX_SLOT_KINDS` / `RetrievalConfig.fix_kinds` ใน `rag_core/retrieval.py` (ค่าเริ่มต้น `("principle",)` = เหมือนเดิม) · `_search_fix(kind=…)` · pool แบบ open ใช้กับ principle เท่านั้น ช่อง mistake ค้นเฉพาะ chunk ที่ติด tag ของ fault · เทสต์ใน `tests/test_fix_slot.py` (ทั้ง 13 ไฟล์ผ่าน) · FIX_SLOT ยังปิด

**เหตุผล:** `fix_query` เขียนจาก card ทั้ง fixes และ causes จึงใช้หาประโยคสาเหตุในช่อง mistake ได้ ซึ่งโควตา 3 ช่องถูกประโยคนิยามอาการใช้หมด · รอบแรกให้ lunge ใช้ pool open เหมือน principle แล้วได้ "ลงแบบไม่ควบคุม" (ไม่ติด tag) ซ้ำใน 3 กฎ จึงจำกัดช่อง mistake ไว้ที่ tagged

**ประโยคที่เพิ่ม (ตัดสินด้วยเกณฑ์ C2 โดย Claude):**

| กฎ | ประโยค | ผล |
|---|---|---|
| knee_varus | ปลายเท้าเปิดมากเกินหรือยืนกว้างสุดโต่ง | **ดี · ปิดช่อง ✗** |
| straight_back_leg | ก้าวยาวเกินจนเข่าหลังงอไม่พอ | **ดี · ปิดช่อง ✗** |
| knee_valgus | สะโพกด้านข้าง/ก้นอ่อน → ต้นขาหุบและบิดเข้า | ดี (แทนประโยคเท้าแบนที่หายไปในรอบ 5) |
| rounded_back | อกยืด (thoracic extension) ไม่พอ | ดี |
| partial_squat | ข้อเท้างอขึ้นได้น้อย | ซ้ำกับที่มีในโควตาแล้ว |
| hip_sag_or_pike | core ไม่ทำงานหรือล้า | ซ้ำกับที่มีแล้ว |
| shallow_lunge | ลดความลึกเมื่อถือน้ำหนักมากขึ้น | ซ้ำกับที่มีแล้ว |
| partial_pushup | แรงแขนไม่พอ | ไม่ดี (อ่อนแรงแบบลอย ๆ) |
| elbow_flare | ศอกแกว่งมากขึ้นเมื่อหนักขึ้น | พอใช้ (สาเหตุ = น้ำหนัก) |
| excessive_front_knee_flexion, forward_trunk_lean, partial_curl | พูดท่าผิดซ้ำ | ไม่ดี |

dev 7 set ได้ประโยคเดียวกับตาราง · context ยาวขึ้นไม่เกิน 1 ชิ้นต่อ fault

**ผล:** สาเหตุเฉพาะที่ KB มีแต่ดึงไม่ถึงเข้ามาได้ 4 กฎ ในนั้น 2 กฎเป็นช่องที่เคยว่าง · ที่ยังว่าง: สาเหตุของ excessive_front_knee_flexion (KB ไม่มี) และ drill ของ knee_varus, elbow_flare, partial_curl · ข้อสังเกต: `likely_cause` ใน prompt v18 ไม่ได้ชี้ให้ใช้ entry ชนิด mistake (ต่างจาก `why_it_matters` ที่ชี้ไปที่ `consequence`) จะใช้ประโยคนี้ไหมขึ้นกับโมเดล

## เปิดใช้ + prompt v19 (2026-11-14)

> user สั่งข้อ 1–2 · ยังไม่ commit · ไม่ได้เรียก API

1. **ค่าเริ่มต้นใหม่:** `FIX_SLOT = True`, `FIX_SLOT_KINDS = ("principle", "mistake")` · `fix_slot_servable()` ปิด slot ให้ config ที่มันไม่รองรับ (QUERIES "fault", KIND_POOL "single") ใช้ใน `eval/eval_retrieval.py` และ `test_rag_compare.py` · เทสต์ทั้ง 13 ไฟล์ผ่าน
2. **ข้อมูลของแอป:** `app_setup/kb_dump.sql.gz` ทำใหม่จาก `kbaudit` (2,262 chunk = dump 2026-10-28 + รอบ 5 · ลองโหลดลงฐานเปล่าแล้วได้ครบ) · `app_setup/gemini-embedding-2.json` คัดลอกจาก cache (69 vector ครอบคลุม 44 ตัวเดิม) · **Supabase ของแอปในเครื่องยังไม่ได้โหลดใหม่** (ไม่ได้รันอยู่) ต้องทำขั้น 3–4 ของ `MU-Capstone-Application/docs/FEEDBACK_SETUP.md` · เอกสารนั้นยังเขียน 2197 chunk
3. **prompt v19:** `likely_cause` ให้ใช้ entry `mistake` ที่บอกเหตุผล · `drill` ให้ใช้ entry `principle` ที่เป็นท่าฝึกหรือท่าง่ายลง แล้วใส่ dose เอง · ช่องของคำตอบไม่เปลี่ยน คำถามใน `pairwise_eval_v2_plan.md` §3 ยังใช้ได้ · ยังไม่ได้ลองกับโมเดล

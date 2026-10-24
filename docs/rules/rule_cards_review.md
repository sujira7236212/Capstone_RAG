# Rule card สำหรับอนุมัติ — เฉลยของการประเมิน RAG v6

<!-- สร้างจาก eval/rule_cards.json ด้วย python eval/render_rule_cards.py ห้ามแก้ไฟล์นี้ด้วยมือ -->
ข้อมูลกฎนำมาจาก `docs/rules/system1/RULES_AND_FSM_CONDENSED.md (synced from system-1 code 2026-09-28)`

## สิ่งที่ขอให้ผู้เชี่ยวชาญตรวจ

ระบบ 1 ตรวจท่าได้ 12 กฎ card แต่ละใบนิยามว่าเนื้อหาแบบไหนนับว่า**ช่วยแก้อาการนั้น**
ระบบจะให้ LLM หลายค่ายใช้ card เหล่านี้ตัดสินเนื้อหาที่ RAG ดึงมา ดังนั้น card ต้องถูกต้องก่อนเริ่มวัดผล

ขอให้ตรวจ card ละ 4 เรื่อง
1. **นิยาม** ตรงกับอาการที่ต้องการแก้หรือไม่
2. **นับรวม / ไม่นับ** ขีดเส้นแบ่งกับอาการที่คล้ายกันถูกหรือไม่
3. **ประโยคตัวอย่าง** ป้ายกำกับถูกหรือไม่ ป้ายมี 3 แบบ
   - `relevant`: ประโยคช่วยให้ผู้ใช้แก้อาการ**นี้**ได้ (บอกลักษณะ สาเหตุ ผลเสีย วิธีแก้ หรือหลักท่าที่ถูก)
   - `wrong_fault`: ประโยคพูดถึงท่าผิด**อื่น** ซึ่งอาจเป็นกฎอื่นในท่าเดียวกันหรือท่าผิดที่ระบบไม่มีกฎ
   - `irrelevant`: ประโยคไม่ได้พูดถึงท่าผิดเลย เช่น วิธีวิจัย หรือข้อมูลทั่วไปของท่า
4. **คำถามถึงผู้เชี่ยวชาญ** (ถ้ามี) ช่วยเลือกคำตอบ ประโยคหรือข้อที่มีป้าย ⚑ ขึ้นกับคำตอบนั้น

ไม่ต้องตรวจเนื้อหาจากฐานความรู้ ขอแค่อนุมัติ card
ภาษาอังกฤษคือข้อความที่ LLM ใช้จริง ภาษาไทยคือคำแปลของข้อความเดียวกัน ถ้าสองภาษาไม่ตรงกันให้แจ้ง

**ช่วง "ระบบวัด"** มาจากระบบ 1 ใช้ประกอบการอ่านเท่านั้น ไม่ต้องอนุมัติ

## สรุป

12 card · ประโยคตัวอย่าง 173 ประโยค · คำถามถึงผู้เชี่ยวชาญ 6 ข้อ

| # | ท่า | กฎ | อาการ | คำถาม |
|---|---|---|---|---|
| 1 | สควอท | `partial_squat` | ย่อไม่สุด / สควอทตื้น |  |
| 2 | สควอท | `knee_valgus` | เข่าบิดเข้าด้านใน |  |
| 3 | สควอท | `knee_varus` | เข่าบานออกด้านนอก | 1 |
| 4 | สควอท | `rounded_back` | หลังค่อม / หลังแอ่น | 2 |
| 5 | วิดพื้น | `hip_sag_or_pike` | ลำตัวไม่ตรง (สะโพกตกหรือโด่ง) |  |
| 6 | วิดพื้น | `partial_pushup` | ลงไม่สุด / วิดพื้นครึ่งท่า |  |
| 7 | ลันจ์ | `shallow_lunge` | ย่อไม่ลึกพอ เข่าหน้างอไม่พอ | 1 |
| 8 | ลันจ์ | `excessive_front_knee_flexion` | ย่อเข่าหน้าลึกเกินไป | 2 |
| 9 | ลันจ์ | `forward_trunk_lean` | ก้มตัวไปหน้ามากเกินไป |  |
| 10 | ลันจ์ | `straight_back_leg` | เข่าหลังงอไม่สุด |  |
| 11 | ไบเซ็ปส์เคิร์ล | `elbow_flare` | ศอกไม่แนบลำตัว (กาง / ลอยไปหน้า / ไปหลัง) |  |
| 12 | ไบเซ็ปส์เคิร์ล | `partial_curl` | ยกไม่สุดช่วง |  |

---

## 1. สควอท — ย่อไม่สุด / สควอทตื้น (`partial_squat`)

`concept_id`: `squat.insufficient_depth` · card version 1 · ชื่อเดิมของกฎ: `knee_depth`

**ข้อความบนจอ:** "Lower to 90 degrees"

**ระบบวัด** (Squat rule 1, ตรวจทีละครั้ง): Lowest value over the attempt of the mean knee angle (hip-knee-ankle, 180 = straight leg). **แจ้งเมื่อ** That minimum is greater than 100 degrees (SQUAT_DEPTH_TARGET). _A rep counts at 120 degrees, so a squat that bottoms out between 100 and 120 is counted and still warned. Coached ideal is a 90-degree knee._

### นิยาม

ย่อลงไม่ลึกพอ ที่จุดต่ำสุดเข่ายังงอไม่ถึงประมาณ 90 องศา ต้นขายังอยู่สูงกว่าแนวขนานพื้นชัดเจน (สควอทครึ่งท่าหรือหนึ่งในสี่ท่า)

> The squat does not go deep enough: at the lowest point the knees are still well short of a 90-degree bend and the thighs stay clearly above parallel (a half or quarter squat).

### นับรวม / ไม่นับ

| | ภาษาไทย | English (LLM ใช้) |
|---|---|---|
| ✅ นับ | หยุดย่อก่อนถึงจุดที่ควรถึง เช่น ย่อครึ่งท่าหรือหนึ่งในสี่ท่า ทั้งที่ตั้งใจทำสควอทเต็มท่า | Stopping the descent early: half squats or quarter squats when a full squat is intended. |
| ✅ นับ | นิยามของความลึกที่พอ เช่น รอยพับสะโพกอยู่ระดับเดียวกับหรือต่ำกว่าหัวเข่า ต้นขาขนานพื้นโดยประมาณ | What counts as adequate depth: the hip crease level with or below the top of the knee, thighs about parallel to the floor. |
| ❌ ไม่นับ | เข่าบิดเข้าใน (knee_valgus) หรือบานออกนอก (knee_varus) | Knees moving inward (knee_valgus) or pushed outward (knee_varus). |
| ❌ ไม่นับ | ท่าทางของหลัง หรือลำตัวโน้มไปข้างหน้า (rounded_back) | Back posture or the trunk leaning forward (rounded_back). |
| ❌ ไม่นับ | หลังล่างงอตอนอยู่จุดต่ำสุด (butt wink) ซึ่งเกิดตอนลงลึกแล้ว ไม่ใช่การลงไม่ลึก | The lower back rounding at the very bottom (butt wink): it happens at depth, it is not a lack of depth. |
| ❌ ไม่นับ | ส้นเท้ายก (ในฐานะท่าผิดอีกแบบ) การวางเท้า และแนวการเคลื่อนของบาร์ | Heels lifting as a fault in its own right, foot placement, bar path. |

### ข้อมูลที่นับว่าเกี่ยวข้อง

| หัวข้อ | ภาษาไทย | English |
|---|---|---|
| ลักษณะ | ลักษณะของสควอทตื้น และวิธีดูว่าลงลึกพอหรือยัง | How a shallow squat looks and how depth is judged. |
| สาเหตุ | สาเหตุที่ลงไม่ลึก เช่น ข้อเท้ากระดกขึ้นได้น้อย สะโพกเคลื่อนไหวได้จำกัด น้ำหนักมากเกิน กล้ามเนื้อไม่แข็งแรงหรือไม่มั่นใจในช่วงล่าง | Why people cannot or do not reach depth: limited ankle dorsiflexion, limited hip mobility, a load that is too heavy, weak or unconfident at the bottom. |
| ผลเสีย | ผลของการลงไม่ลึก เช่น ช่วงการเคลื่อนไหวของสะโพกและเข่าแคบลง กล้ามก้นและต้นขาด้านในทำงานน้อยลง ได้ผลการฝึกน้อยลง | What a shallow squat changes: smaller hip and knee range, less work for the glutes and adductors, a smaller training effect. |
| วิธีแก้ | วิธีแก้ เช่น ฝึกความยืดหยุ่น ย่อลงไปแตะกล่องหรือเป้า ลดน้ำหนัก เสริมส้นเท้า ใช้ goblet squat เป็นท่าฝึกขั้นต้น | How to reach depth: mobility work, squatting to a box or target, lowering the load, raising the heels, goblet squat as a regression. |
| ท่าที่ถูก | ตำแหน่งที่ถูกต้องที่จุดต่ำสุดของสควอทเต็มท่า | The correct bottom position of a full squat. |

### ประโยคตัวอย่าง

**relevant — ช่วยแก้อาการนี้โดยตรง**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| r1 | Many lifters stop their descent while the thighs are still well above parallel, turning the lift into a quarter squat. | หลายคนหยุดย่อทั้งที่ต้นขายังสูงกว่าแนวขนานมาก ทำให้กลายเป็นสควอทแค่หนึ่งในสี่ท่า | ท่าผิด |
| r2 | Tight calves that limit how far the shin can tilt forward often keep a person from sinking any lower in the squat. | น่องที่ตึงจนหน้าแข้งเอนไปข้างหน้าได้น้อย มักทำให้ย่อลงต่ำกว่านี้ไม่ได้ | สาเหตุ |
| r3 | Cutting the movement short keeps the hips and knees in a small arc, so the glutes and adductors get far less training stimulus. | การตัดช่วงการเคลื่อนไหวให้สั้นทำให้สะโพกและเข่าขยับในช่วงแคบ กล้ามก้นและต้นขาด้านในจึงได้รับการกระตุ้นน้อยลงมาก | ผลเสีย |
| r4 | Sitting down to a box set just below knee height teaches a trainee how low each repetition should travel. | การย่อลงนั่งกล่องที่สูงต่ำกว่าเข่าเล็กน้อย ช่วยให้ผู้ฝึกรู้ว่าแต่ละครั้งต้องลงต่ำแค่ไหน | วิธีแก้ |
| r5 | A complete repetition lowers the hip crease to knee height or a little under it before the lifter stands back up. | หนึ่งครั้งที่สมบูรณ์ต้องลดรอยพับสะโพกลงถึงระดับเข่าหรือต่ำกว่าเล็กน้อยก่อนลุกขึ้น | หลักท่าที่ถูก |
| r6 | In the training study, the group that squatted to full depth gained more gluteal muscle volume than the group limited to half squats. | ในงานวิจัยการฝึก กลุ่มที่สควอทลงลึกเต็มท่ามีปริมาตรกล้ามก้นเพิ่มมากกว่ากลุ่มที่ทำแค่ครึ่งท่า | ผลวิจัย |

**wrong_fault — พูดถึงท่าผิดอื่น**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| w1 | As the lifter drives up out of the bottom, both knees collapse toward each other. | ตอนดันตัวขึ้นจากจุดต่ำสุด เข่าทั้งสองข้างยุบเข้าหากัน | กฎพี่น้อง `knee_valgus` |
| w2 | The chest drops and the torso pitches forward until it is almost horizontal during the descent. | ระหว่างย่อลง อกตกและลำตัวเอนไปข้างหน้าจนเกือบขนานพื้น | กฎพี่น้อง `rounded_back` |
| w3 | Forcing the knees far outside the line of the feet puts the hips into excessive external rotation. | การดันเข่าออกไปไกลเกินแนวเท้าทำให้สะโพกหมุนออกมากเกินไป | กฎพี่น้อง `knee_varus` |
| w4 | The heels peel off the floor as the weight shifts onto the balls of the feet. | ส้นเท้ายกขึ้นจากพื้นเพราะน้ำหนักไปลงที่ปลายเท้า | `heels lifting` |
| w5 | The bar drifts forward over the toes instead of staying above the middle of the foot. | บาร์เคลื่อนไปข้างหน้าเหนือปลายเท้า แทนที่จะอยู่เหนือกลางเท้า | `bar path` |
| w6 | Craning the head upward to stare at the ceiling strains the neck during the lift. | การแหงนหน้ามองเพดานระหว่างยกทำให้คอตึงเกินไป | `neck position` |

**irrelevant — ไม่ได้พูดถึงท่าผิดเลย**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| i1 | Participants completed three sets of eight repetitions at seventy percent of their one-repetition maximum. | ผู้เข้าร่วมทำ 3 เซ็ต เซ็ตละ 8 ครั้ง ที่ 70% ของน้ำหนักสูงสุดที่ยกได้ 1 ครั้ง |  |
| i2 | Surface electrodes were attached to the front thigh muscles after the skin was shaved and cleaned. | ติดขั้วไฟฟ้าบนผิวเหนือกล้ามต้นขาด้านหน้าหลังโกนและทำความสะอาดผิว |  |
| i3 | Coaches often program the barbell back squat early in a session, while athletes are still fresh. | โค้ชมักจัด barbell back squat ไว้ช่วงต้นของการฝึกตอนที่นักกีฬายังไม่ล้า |  |

### การอนุมัติ

☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ

หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________

ผู้อนุมัติ: ______________________   วันที่: ______________

---

## 2. สควอท — เข่าบิดเข้าด้านใน (`knee_valgus`)

`concept_id`: `squat.knee_valgus` · card version 1 · ชื่อเดิมของกฎ: —

**ข้อความบนจอ:** "Push knees out"

**ระบบวัด** (Squat rule 2, ตรวจทีละครั้ง): 3D angle between the two shins (knee-to-ankle lines, 0 = parallel), averaged over the frames where the mean knee angle is 92-108 degrees; a frontal-plane reading gives the direction. **แจ้งเมื่อ** The averaged angle is greater than 11 degrees (KNEE_PARALLEL_MAX_INWARD) and the knees are inside the ankles. _Mutually exclusive with knee_varus._

### นิยาม

ระหว่างสควอท เข่าข้างใดข้างหนึ่งหรือทั้งสองข้างบิดหรือยุบเข้าด้านใน จนอยู่ด้านในของแนวข้อเท้าและเท้า (เข่ายุบเข้า, dynamic knee valgus)

> During the squat one or both knees move inward so they sit inside the line of the ankles and feet (knees caving in, dynamic knee valgus).

### นับรวม / ไม่นับ

| | ภาษาไทย | English (LLM ใช้) |
|---|---|---|
| ✅ นับ | เข่ายุบเข้าตอนลง ตอนอยู่จุดต่ำสุด หรือตอนขึ้น รวมถึงกรณีที่เป็นข้างเดียว | Knees caving in on the way down, at the bottom or on the way up; one knee only is included. |
| ✅ นับ | คำในงานวิจัยที่หมายถึงเรื่องเดียวกัน เช่น medial knee displacement, dynamic knee valgus, สะโพกหุบและหมุนเข้าจนดึงเข่าเข้าใน | Research terms for the same thing: medial knee displacement, dynamic knee valgus, hip adduction and internal rotation driving the knee in. |
| ✅ นับ | อุ้งเท้ายุบ (overpronation) เมื่อข้อความโยงกับการที่เข่าเคลื่อนเข้าใน | The foot arch collapsing (overpronation) when the text links it to the knee moving inward. |
| ❌ ไม่นับ | เข่าถูกดันออกนอกเลยแนวเท้า (knee_varus) ซึ่งเป็นทิศตรงข้าม | Knees pushed too far outward past the feet (knee_varus) - the opposite direction. |
| ❌ ไม่นับ | เข่าเคลื่อนไปข้างหน้าเลยปลายเท้า ซึ่งเป็นการเคลื่อนหน้า-หลัง ไม่ใช่การยุบเข้าใน | Knees travelling forward past the toes: that is front-to-back movement, not inward collapse. |
| ❌ ไม่นับ | ความกว้างของการยืนหรือมุมปลายเท้า ที่ไม่ได้พูดถึงเข่ายุบเข้า | Stance width or toe angle discussed without the knee moving inward. |
| ❌ ไม่นับ | ความลึกของการย่อ และท่าทางของหลัง | Squat depth and back posture. |

### ข้อมูลที่นับว่าเกี่ยวข้อง

| หัวข้อ | ภาษาไทย | English |
|---|---|---|
| ลักษณะ | ลักษณะของเข่ายุบเข้า และช่วงไหนของการย่อที่เกิด | How knees caving in looks and when in the rep it appears. |
| สาเหตุ | กล้ามสะโพกด้านข้างและกล้ามหมุนสะโพกออกอ่อนแรง (gluteus medius) ข้อเท้ากระดกได้น้อย อุ้งเท้ายุบ ความล้า น้ำหนักมากเกิน | Weak hip abductors and external rotators (gluteus medius), limited ankle dorsiflexion, foot overpronation, fatigue, a load that is too heavy. |
| ผลเสีย | เพิ่มแรงเครียดต่อเอ็นไขว้หน้า ด้านในของเข่า และข้อต่อลูกสะบ้า อาจเจ็บเข่า | Extra stress on the ACL, the medial knee and the patellofemoral joint; knee pain. |
| วิธีแก้ | บอกให้เข่าชี้ตามแนวปลายเท้า ใช้ยางมินิแบนด์รัดเหนือเข่า ฝึกกล้ามสะโพกด้านข้าง ลดน้ำหนัก | Cue the knees to track over the toes, a mini band around the knees, hip abductor strengthening, lowering the load. |
| ท่าที่ถูก | เข่าอยู่ในแนวเดียวกับนิ้วเท้าที่ 2-3 ตลอดการย่อ | The knee stays in line with the second and third toes throughout the squat. |

### ประโยคตัวอย่าง

**relevant — ช่วยแก้อาการนี้โดยตรง**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| r1 | On the way up from the bottom position her knees drifted in toward each other, ending well inside her feet. | ตอนลุกขึ้นจากจุดต่ำสุด เข่าของเธอเคลื่อนเข้าหากันจนอยู่ด้านในของเท้ามาก | ท่าผิด |
| r2 | Weakness of the gluteus medius and the hip external rotators lets the thigh rotate inward, pulling the knee toward the midline. | gluteus medius และกล้ามหมุนสะโพกออกที่อ่อนแรง ทำให้ต้นขาหมุนเข้าใน ดึงเข่าเข้าหาแนวกลางลำตัว | สาเหตุ |
| r3 | This inward knee collapse adds stress to the ACL and to the inner side of the joint. | การที่เข่ายุบเข้าในแบบนี้เพิ่มแรงเครียดต่อเอ็นไขว้หน้า (ACL) และด้านในของข้อเข่า | ผลเสีย |
| r4 | Looping a light resistance band just above the knees gives the lifter something to press outward against while squatting. | การคล้องยางยืดแรงต้านเบา ๆ ไว้เหนือเข่า ทำให้ผู้ยกมีสิ่งให้ดันออกระหว่างสควอท | วิธีแก้ |
| r5 | Throughout the squat each kneecap should keep pointing over the middle toes of the same foot. | ตลอดการสควอท ลูกสะบ้าแต่ละข้างควรชี้ไปเหนือนิ้วเท้ากลาง ๆ ของเท้าข้างเดียวกัน | หลักท่าที่ถูก |
| r6 | Participants whose knees moved further toward the midline while squatting also had weaker hip abductors. | ผู้เข้าร่วมที่เข่าเคลื่อนเข้าหาแนวกลางลำตัวมากกว่าระหว่างสควอท มีกล้ามกางสะโพกที่อ่อนแรงกว่าด้วย | ผลวิจัย |

**wrong_fault — พูดถึงท่าผิดอื่น**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| w1 | Shoving the knees far outside the feet, well past where the toes point, rolls the weight onto the outer edge of the foot. | การดันเข่าออกไปไกลเลยแนวปลายเท้า ทำให้น้ำหนักไปลงที่ขอบนอกของเท้า | กฎพี่น้อง `knee_varus` |
| w2 | The athlete stopped each repetition with the thighs well above parallel. | นักกีฬาหยุดทุกครั้งตอนที่ต้นขายังสูงกว่าแนวขนานพื้นมาก | กฎพี่น้อง `partial_squat` |
| w3 | His torso tilted so far forward that the shoulders ended up in front of the knees. | ลำตัวของเขาเอนไปข้างหน้ามากจนไหล่ไปอยู่หน้าเข่า | กฎพี่น้อง `rounded_back` |
| w4 | The knees shot forward far beyond the toes as soon as the descent began, loading the front of the knee. | เข่าพุ่งไปข้างหน้าเลยปลายเท้ามากทันทีที่เริ่มย่อ ทำให้แรงไปลงที่ด้านหน้าของเข่า | `knees forward past toes` |
| w5 | The heels came off the ground at the bottom of every squat. | ส้นเท้ายกจากพื้นทุกครั้งที่ลงถึงจุดต่ำสุด | `heels lifting` |
| w6 | The pelvis tucked under and the lower back rounded at the deepest point of the squat. | ที่จุดลึกที่สุดของสควอท เชิงกรานม้วนเข้าและหลังล่างงอ | `butt wink` |

**irrelevant — ไม่ได้พูดถึงท่าผิดเลย**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| i1 | Knee joint kinematics were captured with a twelve-camera motion analysis system sampling at 200 Hz. | เก็บข้อมูลการเคลื่อนไหวของข้อเข่าด้วยระบบกล้อง 12 ตัว ที่ 200 Hz |  |
| i2 | Each squat was performed with a barbell resting across the upper trapezius. | สควอทแต่ละครั้งทำโดยวางบาร์บนกล้ามบ่าส่วนบน |  |
| i3 | Recreationally active adults with no history of lower-limb surgery were recruited. | รับสมัครผู้ใหญ่ที่ออกกำลังกายเป็นประจำและไม่เคยผ่าตัดขา |  |

### การอนุมัติ

☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ

หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________

ผู้อนุมัติ: ______________________   วันที่: ______________

---

## 3. สควอท — เข่าบานออกด้านนอก (`knee_varus`)

`concept_id`: `squat.knee_varus` · card version 1 · ชื่อเดิมของกฎ: —

**ข้อความบนจอ:** "Keep knees in line"

**ระบบวัด** (Squat rule 3, ตรวจทีละครั้ง): The same shin-to-shin 3D angle as knee_valgus, averaged over the frames where the mean knee angle is 92-108 degrees. **แจ้งเมื่อ** The averaged angle is greater than 8 degrees (KNEE_PARALLEL_MAX_OUTWARD) and the knees are outside the ankles (or zero). _Mutually exclusive with knee_valgus. New rule with no earlier code; the KB may have little on it (a data gap, not a retrieval error)._

### นิยาม

ระหว่างสควอท เข่าบานหรือถูกดันออกด้านนอกจนเลยแนวเท้า (เป็นรูปตัว V) เช่น หันปลายเท้าออกมากเกิน หรือทำตามคำแนะนำ 'ดันเข่าออก' มากเกินไป

> During the squat the knees splay or are pushed outward so they sit outside the line of the feet (a V shape), for example with the toes turned out a lot or when a 'knees out' cue is overdone.

### นับรวม / ไม่นับ

| | ภาษาไทย | English (LLM ใช้) |
|---|---|---|
| ✅ นับ | เข่าเคลื่อนออกไปอยู่ด้านนอกนิ้วก้อยระหว่างสควอท | Knees tracking outside the little toes during the squat. |
| ✅ นับ | แก้เข่ายุบเข้าเกินขนาด จนดันเข่าออกไปไกลเกินไป | Overcorrecting knee cave-in by driving the knees too far out. |
| ✅ นับ | หันปลายเท้าออกมากเกินจนเข่าบานออก | Excessive toe-out that makes the knees splay outward. |
| ❌ ไม่นับ | เข่ายุบเข้าใน (knee_valgus) ซึ่งเป็นทิศตรงข้าม รวมถึงคำแนะนำให้ดันเข่าออกเพื่อแก้เข่ายุบ | Knees caving inward (knee_valgus) - the opposite direction, including advice to push the knees out to stop them caving in. |
| ❌ ไม่นับ | ขาโก่งโดยกำเนิด (genu varum) ในฐานะลักษณะทางกายวิภาค ไม่ใช่การเคลื่อนของเข่าระหว่างสควอท | Static bow-legged alignment (genu varum) as an anatomical trait rather than knee movement during the squat. |
| ❌ ไม่นับ | ความกว้างของการยืนหรือมุมเท้า ที่ไม่ได้พูดถึงเข่าที่ออกไปนอกแนวเท้า | Stance width or foot angle discussed without the knees ending up outside the feet. |

### ข้อมูลที่นับว่าเกี่ยวข้อง

| หัวข้อ | ภาษาไทย | English |
|---|---|---|
| ลักษณะ | ลักษณะของเข่าบานออก | How knees splaying outward looks. |
| สาเหตุ | ทำตามคำแนะนำ 'ดันเข่าออก' มากเกินไป หันปลายเท้าออกมากเกินไป ยืนกว้างเกินไป | Overdoing a 'push the knees out' cue, feet turned out too far, a stance that is too wide. |
| ผลเสีย | แรงย้ายไปที่ด้านนอกของเข่าและขอบนอกของเท้า นิ้วโป้งเท้าไม่แตะพื้น ฐานรองรับมั่นคงน้อยลง | Load shifts to the outer knee and the outer edge of the foot, the big toe loses contact, the base becomes less stable. |
| วิธีแก้ | ให้เข่าชี้ไปทางเดียวกับปลายเท้า ลดการหันปลายเท้าออก ให้ทั้งฝ่าเท้ารวมถึงนิ้วโป้งแตะพื้น | Aim the knees in the direction the toes point, reduce toe-out, keep the whole foot including the big toe on the floor. |
| ท่าที่ถูก | เข่าเคลื่อนอยู่เหนือแนวเท้า ไม่เข้าในและไม่ออกนอก | The knee tracks over the foot, neither inside nor outside it. |

### ประโยคตัวอย่าง

**relevant — ช่วยแก้อาการนี้โดยตรง**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| r1 | Pushing the knees out so aggressively that they end up well outside the little toes is an overcorrection, not good form. | การดันเข่าออกแรงจนเข่าไปอยู่ด้านนอกนิ้วก้อยมาก เป็นการแก้เกินขนาด ไม่ใช่ท่าที่ดี | ท่าผิด |
| r2 | When the feet are turned out at a very wide angle, the knees tend to splay even further outward as the lifter sits down. | เมื่อหันปลายเท้าออกกว้างมาก เข่ามักบานออกยิ่งขึ้นตอนย่อลง | สาเหตุ |
| r3 | With the knees forced outward past the feet, the big toe lifts and body weight rolls onto the outer border of the foot. | เมื่อเข่าถูกดันออกเลยแนวเท้า นิ้วโป้งเท้าจะยกและน้ำหนักตัวไปลงที่ขอบนอกของเท้า | ผลเสีย |
| r4 | Aim each knee over the middle of the foot, in line with the toes, rather than as far outward as it will go. | ให้เข่าแต่ละข้างอยู่เหนือกลางเท้าในแนวเดียวกับปลายเท้า แทนที่จะดันออกให้ไกลที่สุด | วิธีแก้ |
| r5 | Good knee tracking keeps the thigh and shin in line with the foot, drifting neither inward nor outward. | การเคลื่อนของเข่าที่ดีคือต้นขาและหน้าแข้งอยู่แนวเดียวกับเท้า ไม่เบนเข้าในหรือออกนอก | หลักท่าที่ถูก |
| r6 | Driving the knees outward beyond the feet shifted plantar pressure toward the lateral edge of the foot in the measured squats. | ในการวัดสควอท การดันเข่าออกเลยแนวเท้าทำให้แรงกดใต้ฝ่าเท้าย้ายไปที่ขอบด้านนอก | ผลวิจัย |

**wrong_fault — พูดถึงท่าผิดอื่น**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| w1 | The knees buckled in, almost touching, while the lifter pushed up out of the hole. | เข่าหักเข้าจนเกือบชนกันตอนผู้ยกดันตัวขึ้นจากจุดต่ำสุด | กฎพี่น้อง `knee_valgus` |
| w2 | Cueing the lifter to spread the floor and drive the knees apart helps stop them from caving in. | การบอกผู้ยกให้ 'ถ่างพื้น' และดันเข่าแยกออก ช่วยไม่ให้เข่ายุบเข้า | กฎพี่น้อง `knee_valgus` |
| w3 | Most repetitions ended as quarter squats with only a slight bend at the knee. | ส่วนใหญ่จบแค่สควอทหนึ่งในสี่ท่า เข่างอเพียงเล็กน้อย | กฎพี่น้อง `partial_squat` |
| w4 | The lifter leaned the chest far forward and pushed the hips back until the torso was nearly parallel to the floor. | ผู้ยกโน้มอกไปข้างหน้ามากและดันสะโพกไปข้างหลังจนลำตัวเกือบขนานพื้น | กฎพี่น้อง `rounded_back` |
| w5 | Shifting the body weight onto one leg left the hips uneven in the lowest position. | การถ่ายน้ำหนักไปขาข้างเดียวทำให้สะโพกไม่เท่ากันที่ตำแหน่งต่ำสุด | `lateral weight shift` |
| w6 | The heels rose off the floor as the knees moved forward. | ส้นเท้ายกขึ้นจากพื้นขณะเข่าเคลื่อนไปข้างหน้า | `heels lifting` |

**irrelevant — ไม่ได้พูดถึงท่าผิดเลย**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| i1 | Each participant attended two familiarisation sessions before testing began. | ผู้เข้าร่วมแต่ละคนเข้าร่วมการฝึกทำความคุ้นเคย 2 ครั้งก่อนเริ่มทดสอบ |  |
| i2 | Squats were performed barefoot to remove any influence of footwear. | ทำสควอทเท้าเปล่าเพื่อตัดผลของรองเท้า |  |
| i3 | The goblet squat holds a single dumbbell or kettlebell against the chest. | goblet squat คือการถือดัมเบลหรือเคตเทิลเบลหนึ่งลูกไว้ชิดอก |  |

### คำถามถึงผู้เชี่ยวชาญ

- **⚑oq1** สาเหตุและผลเสียที่ร่างไว้มาจากความรู้ทั่วไป เพราะมีเอกสารพูดถึงเข่าบานออกน้อย ถูกต้องและครบหรือไม่
  _The causes and consequences were drafted from general coaching knowledge because little is written about knees splaying outward. Are they correct and complete?_
  คำตอบ: ________________________

### การอนุมัติ

☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ

หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________

ผู้อนุมัติ: ______________________   วันที่: ______________

---

## 4. สควอท — หลังค่อม / หลังแอ่น (`rounded_back`)

`concept_id`: `squat.back_posture` · card version 1 · ชื่อเดิมของกฎ: —

**ข้อความบนจอ:** "Keep back straight"

**ระบบวัด** (Squat rule 4, ตรวจทีละเฟรม): Trunk tilt: angle between the hip-to-shoulder line and the vertical (0 = upright), averaged over both sides. **แจ้งเมื่อ** The tilt is greater than 35 degrees (SQUAT_BACK_TILT_MAX) for 10 consecutive frames. _The rule measures trunk lean, not spine curvature. Expert Ton named the faults for RAG, in query order: หลังค่อม (rounded back), หลังแอ่น (arched back). A rounded or arched back with an upright trunk gives no warning._

### นิยาม

หลังไม่อยู่ในแนวตรงเป็นกลางระหว่างสควอท อาการที่ผู้เชี่ยวชาญกำหนดคือ หลังค่อม (กระดูกสันหลังงอ หลังส่วนบนหรือล่างโค้งไปข้างหน้า) และหลังแอ่น (หลังล่างแอ่นเกิน) ระบบจะแจ้งกฎนี้เมื่อลำตัวเอนไปข้างหน้าเกิน 35 องศาจากแนวดิ่ง

> The back does not stay straight and neutral during the squat. The two named faults are a rounded back (the spine flexes and the upper or lower back curves forward) and an arched back (the lower back over-extends). The system raises this rule when the trunk leans forward more than 35 degrees from vertical.

### นับรวม / ไม่นับ

| | ภาษาไทย | English (LLM ใช้) |
|---|---|---|
| ✅ นับ | หลังค่อม: หลังส่วนบนงุ้มหรือกระดูกสันหลังทั้งแนวงอขณะแบกบาร์ | Rounded back: the upper back hunching or the whole spine flexing under the bar. |
| ✅ นับ | หลังแอ่น: หลังล่างแอ่นเกิน ส่วนโค้งของเอวมากเกินปกติ | Arched back: the lower back over-extending, an exaggerated lumbar curve. |
| ✅ นับ ⚑oq2 | หลังล่างงอตอนอยู่จุดต่ำสุดเพราะเชิงกรานม้วนเข้า (butt wink) ในฐานะหลังค่อมแบบหนึ่ง | The lower back rounding at the bottom as the pelvis tucks under (butt wink), as a form of rounded back. |
| ✅ นับ ⚑oq1 | ลำตัวโน้มไปข้างหน้ามากเกิน ซึ่งเป็นสิ่งที่ระบบวัดจริง | Excessive forward lean of the trunk, which is what the system actually measures. |
| ❌ ไม่นับ | ตำแหน่งเข่า (knee_valgus, knee_varus) และความลึกของการย่อ (partial_squat) | Knee position (knee_valgus, knee_varus) and squat depth (partial_squat). |
| ❌ ไม่นับ | ตำแหน่งศีรษะหรือคอเพียงอย่างเดียว ส้นเท้ายก แนวการเคลื่อนของบาร์ | Head or neck position on its own, heels lifting, bar path. |

### ข้อมูลที่นับว่าเกี่ยวข้อง

| หัวข้อ | ภาษาไทย | English |
|---|---|---|
| ลักษณะ | ลักษณะของหลังค่อม หลังแอ่น หรือลำตัวโน้มมากเกินในสควอท | How a rounded, arched or over-leaning back looks in the squat. |
| สาเหตุ | หลังส่วนอกเคลื่อนไหวได้น้อย กล้ามลำตัวและกล้ามเหยียดหลังอ่อนแรง เกร็งแกนกลางไม่ดี แฮมสตริงหรือสะโพกตึง น้ำหนักมากเกิน | Poor thoracic mobility, weak trunk and spinal extensors, poor bracing, tight hamstrings or hips, a load that is too heavy. |
| ผลเสีย | แรงกดและแรงเฉือนต่อกระดูกสันหลังระดับเอวและหมอนรองกระดูกเพิ่มขึ้น เสี่ยงปวดหรือบาดเจ็บหลังล่าง | Higher compressive and shear loads on the lumbar spine and discs, lower back pain or injury risk. |
| วิธีแก้ | เกร็งหน้าท้องก่อนย่อทุกครั้ง ยกอกขึ้น บอกให้คงหลังเป็นกลาง ฝึกความยืดหยุ่น ลดน้ำหนัก | Bracing the abdomen before each rep, keeping the chest up, a neutral spine cue, mobility work, lowering the load. |
| ท่าที่ถูก | คงกระดูกสันหลังเป็นกลางตั้งแต่เริ่มจนจบ | A neutral spine held from start to finish. |

### ประโยคตัวอย่าง

**relevant — ช่วยแก้อาการนี้โดยตรง**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| r1 | As the lifter descended, the upper back hunched forward and the shoulders rolled toward the knees. | ระหว่างย่อลง หลังส่วนบนของผู้ยกงุ้มไปข้างหน้าและไหล่ห่อลงหาเข่า | ท่าผิด |
| r2 | Some lifters over-extend the lower back in the hole, exaggerating the normal inward curve of the waist. | ผู้ยกบางคนแอ่นหลังล่างมากเกินตอนอยู่ช่วงล่าง ทำให้ส่วนโค้งของเอวมากเกินปกติ | ท่าผิด |
| r3 ⚑oq2 | Close to full depth the pelvis tucked under and the lower back lost its natural curve. | ช่วงใกล้ลงสุด เชิงกรานม้วนเข้าและหลังล่างเสียส่วนโค้งตามธรรมชาติ | ท่าผิด |
| r4 | Poor thoracic mobility and weak spinal erectors make it hard to hold the chest up and the back flat under load. | หลังส่วนอกที่เคลื่อนไหวได้น้อยและกล้ามเหยียดหลังที่อ่อนแรง ทำให้ยกอกและคงหลังให้ตรงขณะแบกน้ำหนักได้ยาก | สาเหตุ |
| r5 | Squatting with a flexed spine under a heavy bar raises compressive and shear loads on the lumbar discs. | การสควอทด้วยหลังงอขณะแบกบาร์หนัก เพิ่มแรงกดและแรงเฉือนต่อหมอนรองกระดูกเอว | ผลเสีย |
| r6 | Bracing the abdomen before each descent and keeping the chest proud helps the spine stay neutral. | การเกร็งหน้าท้องก่อนย่อลงทุกครั้งและยืดอกไว้ ช่วยให้กระดูกสันหลังคงเป็นกลาง | วิธีแก้ |
| r7 ⚑oq1 | The torso pitched forward far more than the shins, turning the squat into a hip-hinge pattern. | ลำตัวโน้มไปข้างหน้ามากกว่าหน้าแข้งมาก จนสควอทกลายเป็นท่าพับสะโพก | ท่าผิด |

**wrong_fault — พูดถึงท่าผิดอื่น**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| w1 | The left knee collapsed inward during the ascent. | เข่าซ้ายยุบเข้าในตอนลุกขึ้น | กฎพี่น้อง `knee_valgus` |
| w2 | The knees were driven so far apart that they sat outside the feet. | เข่าถูกดันแยกออกมากจนอยู่ด้านนอกของเท้า | กฎพี่น้อง `knee_varus` |
| w3 | The squat stopped well above parallel on every repetition. | ทุกครั้งหยุดย่อตอนที่ยังสูงกว่าแนวขนานพื้นมาก | กฎพี่น้อง `partial_squat` |
| w4 | The heels lifted off the floor and the weight shifted to the toes. | ส้นเท้ายกจากพื้นและน้ำหนักย้ายไปที่ปลายเท้า | `heels lifting` |
| w5 | One hip shifted to the side so the lifter rose unevenly. | สะโพกข้างหนึ่งเบี่ยงไปด้านข้าง ทำให้ลุกขึ้นไม่เท่ากัน | `lateral hip shift` |
| w6 | Bouncing out of the bottom position used momentum instead of muscular control. | การเด้งออกจากจุดต่ำสุดใช้แรงส่งแทนการควบคุมด้วยกล้ามเนื้อ | `bouncing` |

**irrelevant — ไม่ได้พูดถึงท่าผิดเลย**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| i1 | The study compared the back squat with the front squat in twelve trained men. | งานวิจัยเปรียบเทียบ back squat กับ front squat ในผู้ชายที่ฝึกมาแล้ว 12 คน |  |
| i2 | Blood lactate was sampled from the earlobe after the final set. | เก็บตัวอย่างแลคเตทในเลือดจากติ่งหูหลังเซ็ตสุดท้าย |  |
| i3 | Eight weeks of squat training twice a week improved vertical jump height. | การฝึกสควอทสัปดาห์ละ 2 ครั้งเป็นเวลา 8 สัปดาห์ทำให้กระโดดได้สูงขึ้น |  |

### คำถามถึงผู้เชี่ยวชาญ

- **⚑oq1** กฎนี้แจ้งเมื่อลำตัวโน้มไปหน้า แต่อาการที่กำหนดคือหลังค่อมและหลังแอ่น เนื้อหาเรื่องลำตัวโน้มไปหน้ามากเกิน (โดยที่หลังยังตรง) ควรนับเป็น relevant ด้วยหรือไม่ ร่างนี้นับ เพราะเป็นสิ่งที่ทำให้ระบบแจ้งเตือน
  _The rule fires on forward trunk lean, but the named faults are rounded back and arched back. Should content about excessive forward trunk lean (with a straight back) also count as relevant? The draft says yes, because it is the condition that triggers the cue._
  คำตอบ: นับ: เนื้อหาเรื่องลำตัวโน้มไปหน้ามากเกินเป็น relevant (2026-10-01)

- **⚑oq2** หลังค่อมรวมถึงหลังล่างงอตอนอยู่จุดต่ำสุดเพราะเชิงกรานม้วนเข้า (butt wink) ด้วยหรือไม่ ร่างนี้นับรวม
  _Does หลังค่อม (rounded back) include the lower back rounding at the bottom as the pelvis tucks under (butt wink)? The draft says yes._
  คำตอบ: นับ: butt wink เป็นหลังค่อมแบบหนึ่ง (2026-10-01)

### การอนุมัติ

☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ

หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________

ผู้อนุมัติ: ______________________   วันที่: ______________

---

## 5. วิดพื้น — ลำตัวไม่ตรง (สะโพกตกหรือโด่ง) (`hip_sag_or_pike`)

`concept_id`: `push-up.body_line` · card version 1 · ชื่อเดิมของกฎ: `body_alignment`

**ข้อความบนจอ:** "Body not straight"

**ระบบวัด** (Push-up rule 1, ตรวจทีละเฟรม): Shoulder-hip-ankle interior angle (180 = straight body line), averaged over both sides. **แจ้งเมื่อ** The angle is less than 160 degrees (PUSHUP_ALIGN_MIN) for 10 consecutive frames. _One message catches both sagging hips and piked hips._

### นิยาม

ระหว่างวิดพื้น ลำตัวไม่เป็นแนวตรงจากไหล่ผ่านสะโพกถึงข้อเท้า สะโพกตกลงหาพื้นหรือโด่งขึ้นหาเพดาน

> During the push-up the body does not hold a straight line from the shoulders through the hips to the ankles: the hips sag toward the floor or pike up toward the ceiling.

### นับรวม / ไม่นับ

| | ภาษาไทย | English (LLM ใช้) |
|---|---|---|
| ✅ นับ | สะโพกตกและหลังล่างแอ่นลงหาพื้น | Hips sagging and the lower back arching toward the floor. |
| ✅ นับ | สะโพกโด่งขึ้นจนลำตัวเป็นรูปตัว V คว่ำ | Hips piked up so the body forms an inverted V. |
| ✅ นับ | เสียท่าแพลงก์ระหว่างเซ็ตเพราะความล้า | Losing the plank position partway through a set because of fatigue. |
| ❌ ไม่นับ | อกลงไม่ต่ำพอ (partial_pushup) | The chest not going low enough (partial_pushup). |
| ❌ ไม่นับ | ศอกกางออก การวางมือ สะบักยก ตำแหน่งศีรษะหรือคอเพียงอย่างเดียว | Elbow flare, hand placement, scapular winging, head or neck position on its own. |

### ข้อมูลที่นับว่าเกี่ยวข้อง

| หัวข้อ | ภาษาไทย | English |
|---|---|---|
| ลักษณะ | ลักษณะของสะโพกตกหรือโด่งในท่าวิดพื้น | How sagging or piked hips look in the push-up. |
| สาเหตุ | กล้ามหน้าท้องและกล้ามก้นอ่อนแรง ความมั่นคงของลำตัวไม่ดี ความล้า | Weak abdominals and glutes, poor trunk stability, fatigue. |
| ผลเสีย | สะโพกตกทำให้หลังล่างรับแรงมาก สะโพกโด่งทำให้แกนกลางและอกทำงานน้อยลง | Stress on the lower back when the hips sag; less core and chest work when the hips pike. |
| วิธีแก้ | เกร็งหน้าท้องและบีบก้น ฝึกแพลงก์ ใช้วิดพื้นคุกเข่าหรือวิดพื้นมือบนที่สูงเป็นท่าฝึกขั้นต้น | Brace the abs and squeeze the glutes, plank practice, knee or incline push-ups as regressions. |
| ท่าที่ถูก | ลำตัวแข็งแบบแพลงก์ หู ไหล่ สะโพก เข่า และข้อเท้าอยู่ในแนวเดียวกัน | A rigid plank: ears, shoulders, hips, knees and ankles in one line. |

### ประโยคตัวอย่าง

**relevant — ช่วยแก้อาการนี้โดยตรง**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| r1 | Halfway through the set his hips started to drop toward the floor, leaving the lower back arched. | ผ่านไปครึ่งเซ็ต สะโพกของเขาเริ่มตกลงหาพื้น หลังล่างจึงแอ่น | ท่าผิด |
| r2 | Some trainees push their hips high into the air, forming an inverted V instead of a plank. | ผู้ฝึกบางคนดันสะโพกขึ้นสูงจนเป็นรูปตัว V คว่ำแทนที่จะเป็นแพลงก์ | ท่าผิด |
| r3 | Insufficient abdominal and gluteal strength makes it difficult to stop the pelvis from sagging during the push-up. | กล้ามหน้าท้องและกล้ามก้นที่ไม่แข็งแรงพอ ทำให้กันเชิงกรานไม่ให้ตกระหว่างวิดพื้นได้ยาก | สาเหตุ |
| r4 | Letting the midsection sag shifts load onto the lumbar spine and can aggravate lower back pain. | การปล่อยให้ช่วงกลางลำตัวตก ย้ายแรงไปที่กระดูกสันหลังเอวและอาจทำให้ปวดหลังล่างมากขึ้น | ผลเสีย |
| r5 | Squeezing the glutes and tightening the abs before lowering keeps the body rigid like a plank. | บีบก้นและเกร็งหน้าท้องก่อนลง ช่วยให้ลำตัวแข็งเหมือนแพลงก์ | วิธีแก้ |
| r6 | Seen from the side, the head, shoulders, hips and heels should stay in one straight line for the whole push-up. | มองจากด้านข้าง ศีรษะ ไหล่ สะโพก และส้นเท้าควรอยู่ในเส้นตรงเส้นเดียวตลอดการวิดพื้น | หลักท่าที่ถูก |

**wrong_fault — พูดถึงท่าผิดอื่น**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| w1 | She only lowered a few centimetres before pressing back up, never bringing the chest near the floor. | เธอลงเพียงไม่กี่เซนติเมตรแล้วดันขึ้น อกไม่เคยเข้าใกล้พื้น | กฎพี่น้อง `partial_pushup` |
| w2 | The elbows barely bent, so each repetition covered only a fraction of the movement. | ศอกแทบไม่งอ แต่ละครั้งจึงได้แค่ส่วนเล็ก ๆ ของการเคลื่อนไหว | กฎพี่น้อง `partial_pushup` |
| w3 | The elbows flared straight out to the sides, forming a T shape with the torso. | ศอกกางออกด้านข้างตรง ๆ จนเป็นรูปตัว T กับลำตัว | `elbow flare` |
| w4 | The shoulder blades peeled away from the rib cage and stuck out at the top. | สะบักยกห่างจากซี่โครงและนูนออกมาที่ตำแหน่งบนสุด | `scapular winging` |
| w5 | Placing the hands far in front of the shoulders increases stress on the wrists and shoulders. | การวางมือไกลไปข้างหน้าไหล่มากเพิ่มแรงเครียดต่อข้อมือและไหล่ | `hand placement` |

**irrelevant — ไม่ได้พูดถึงท่าผิดเลย**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| i1 | Push-ups were performed to a metronome set at forty beats per minute. | วิดพื้นตามจังหวะเมโทรนอมที่ 40 ครั้งต่อนาที |  |
| i2 | Chest and triceps muscle activity was recorded during each repetition. | บันทึกการทำงานของกล้ามอกและกล้ามต้นแขนด้านหลังในแต่ละครั้ง |  |
| i3 | Because it needs no equipment, the push-up suits home workouts. | วิดพื้นไม่ต้องใช้อุปกรณ์ จึงเหมาะกับการออกกำลังกายที่บ้าน |  |

### การอนุมัติ

☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ

หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________

ผู้อนุมัติ: ______________________   วันที่: ______________

---

## 6. วิดพื้น — ลงไม่สุด / วิดพื้นครึ่งท่า (`partial_pushup`)

`concept_id`: `push-up.insufficient_depth` · card version 1 · ชื่อเดิมของกฎ: `elbow_depth`

**ข้อความบนจอ:** "Lower Your Chest"

**ระบบวัด** (Push-up rule 2, ตรวจทีละครั้ง): Lowest value over the attempt of the mean elbow angle (shoulder-elbow-wrist). **แจ้งเมื่อ** That minimum is greater than 110 degrees (PUSHUP_ELBOW_TARGET). _The bar equals the push-up count bar, so it fires only on attempts that were not counted._

### นิยาม

วิดพื้นลงไม่ต่ำพอ ที่จุดต่ำสุดศอกงอเพียงเล็กน้อยและอกยังห่างพื้นมาก (วิดพื้นไม่สุดหรือครึ่งท่า)

> The push-up does not go low enough: at the bottom the elbows are only slightly bent and the chest stays far from the floor (a partial or half push-up).

### นับรวม / ไม่นับ

| | ภาษาไทย | English (LLM ใช้) |
|---|---|---|
| ✅ นับ | ทำแบบตื้นหรือครึ่งท่า หยุดตอนที่ยังห่างพื้นมาก | Shallow or half repetitions that stop well above the floor. |
| ✅ นับ | คำแนะนำว่าวิดพื้นควรลงต่ำแค่ไหน (ศอกประมาณ 90 องศา อกใกล้พื้น) | Recommendations on how low a push-up should go (elbows about 90 degrees, chest near the floor). |
| ❌ ไม่นับ | สะโพกตกหรือโด่ง (hip_sag_or_pike) | Sagging or piked hips (hip_sag_or_pike). |
| ❌ ไม่นับ | ไม่เหยียดแขนสุดที่ตำแหน่งบน เพราะกฎนี้ตรวจเฉพาะจุดต่ำสุด | Not straightening the arms at the top: the rule only checks the bottom. |
| ❌ ไม่นับ | ศอกกางออก การวางมือ ตำแหน่งศีรษะ | Elbow flare, hand placement, head position. |

### ข้อมูลที่นับว่าเกี่ยวข้อง

| หัวข้อ | ภาษาไทย | English |
|---|---|---|
| ลักษณะ | ลักษณะของวิดพื้นที่ลงไม่สุด | How a shallow push-up looks. |
| สาเหตุ | กล้ามอกหรือต้นแขนด้านหลังไม่แข็งแรงพอจะดันจากจุดต่ำสุด ความล้า เจ็บไหล่เมื่อลงลึก | Chest or triceps too weak to press from the bottom, fatigue, shoulder discomfort at depth. |
| ผลเสีย | ช่วงการเคลื่อนไหวแคบลง กล้ามได้รับการกระตุ้นน้อยลง แข็งแรงเฉพาะช่วงบนของการเคลื่อนไหว | A smaller range of motion, less muscle stimulus, strength limited to the top part of the movement. |
| วิธีแก้ | วิดพื้นมือบนที่สูงหรือคุกเข่า ฝึกลงช้า ๆ วางเป้าไว้ใต้อก | Incline or knee push-ups, slow lowering (negatives), a target under the chest. |
| ท่าที่ถูก | ลงจนศอกงอประมาณ 90 องศาหรืออกเกือบแตะพื้น | Lower until the elbows reach about 90 degrees or the chest nearly touches the floor. |

### ประโยคตัวอย่าง

**relevant — ช่วยแก้อาการนี้โดยตรง**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| r1 | Many beginners bend the elbows only slightly and push back up long before the chest gets close to the floor. | ผู้เริ่มต้นหลายคนงอศอกเพียงเล็กน้อยแล้วดันขึ้น ก่อนอกจะเข้าใกล้พื้นมาก | ท่าผิด |
| r2 | When the triceps and chest are too weak to press from the bottom, people shorten the descent so the repetition stays possible. | เมื่อต้นแขนด้านหลังและอกไม่แข็งแรงพอจะดันจากจุดต่ำสุด คนมักลงให้สั้นลงเพื่อให้ยังทำได้ | สาเหตุ |
| r3 | Shallow repetitions work the muscles only near lockout, so strength at longer muscle lengths is left untrained. | การลงตื้นฝึกกล้ามเฉพาะช่วงใกล้เหยียดแขนสุด ความแข็งแรงในช่วงที่กล้ามยืดยาวจึงไม่ได้ฝึก | ผลเสีย |
| r4 | Placing a foam block under the chest gives a clear target to touch on every repetition. | วางบล็อกโฟมไว้ใต้อก เป็นเป้าชัดเจนให้แตะทุกครั้ง | วิธีแก้ |
| r5 | Raising the hands onto a bench lets a weaker trainee reach full depth instead of cutting each rep short. | การวางมือบนม้านั่ง ช่วยให้ผู้ที่ยังไม่แข็งแรงลงได้สุดแทนที่จะลงสั้น | วิธีแก้ |
| r6 | A full push-up lowers the body until the elbows reach about ninety degrees or the chest nearly touches the ground. | วิดพื้นเต็มท่าคือลงจนศอกงอประมาณ 90 องศาหรืออกเกือบแตะพื้น | หลักท่าที่ถูก |

**wrong_fault — พูดถึงท่าผิดอื่น**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| w1 | The hips sank lower and lower toward the floor as the set went on. | สะโพกตกลงหาพื้นมากขึ้นเรื่อย ๆ ระหว่างเซ็ต | กฎพี่น้อง `hip_sag_or_pike` |
| w2 | Her hips were raised high above the line of the shoulders during every repetition. | สะโพกของเธอยกสูงกว่าแนวไหล่มากทุกครั้ง | กฎพี่น้อง `hip_sag_or_pike` |
| w3 | The elbows pointed directly out to the side instead of angling back toward the body. | ศอกชี้ออกด้านข้างตรง ๆ แทนที่จะเฉียงไปทางลำตัว | `elbow flare` |
| w4 | The head dropped forward so the chin led the movement toward the floor. | ศีรษะก้มไปข้างหน้าจนคางนำลงหาพื้น | `head position` |
| w5 | Hands were placed much wider than shoulder width, stressing the front of the shoulder. | วางมือกว้างกว่าไหล่มาก ทำให้ด้านหน้าของไหล่รับแรงมาก | `hand placement` |

**irrelevant — ไม่ได้พูดถึงท่าผิดเลย**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| i1 | Participants completed as many push-ups as they could within sixty seconds. | ผู้เข้าร่วมวิดพื้นให้ได้มากที่สุดใน 60 วินาที |  |
| i2 | Push-up tests appear in many military fitness assessments. | การทดสอบวิดพื้นอยู่ในแบบประเมินสมรรถภาพทางทหารหลายแห่ง |  |
| i3 | Ground reaction forces were measured with a force plate placed under the hands. | วัดแรงปฏิกิริยาจากพื้นด้วยแผ่นวัดแรงที่วางใต้มือ |  |

### การอนุมัติ

☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ

หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________

ผู้อนุมัติ: ______________________   วันที่: ______________

---

## 7. ลันจ์ — ย่อไม่ลึกพอ เข่าหน้างอไม่พอ (`shallow_lunge`)

`concept_id`: `lunge.insufficient_depth` · card version 1 · ชื่อเดิมของกฎ: `front_knee_too_shallow`

**ข้อความบนจอ:** "Lower your front knee"

**ระบบวัด** (Lunge rule 1, ตรวจทีละครั้ง): The front knee's lowest hip-knee-ankle angle over the attempt (front = the knee with the smaller minimum). **แจ้งเมื่อ** That value is greater than 105 degrees (LUNGE_FRONT_SHALLOW_MAX). _The bar equals the lunge count bar, so it fires only on attempts that were not counted. Coached ideal is 90 degrees._

### นิยาม

ลันจ์ลงไม่ลึกพอ เข่าหน้างอไม่ถึงประมาณ 90 องศาที่จุดต่ำสุด ตัวจึงแทบไม่ได้ลดลง (ลันจ์ตื้น)

> The lunge does not go deep enough: the front knee stays well short of a 90-degree bend at the bottom, so the body barely lowers (a shallow lunge).

### นับรวม / ไม่นับ

| | ภาษาไทย | English (LLM ใช้) |
|---|---|---|
| ✅ นับ | ย่อลงเพียงเล็กน้อย เข่าหน้าเกือบตรง | Only dipping slightly, keeping the front knee nearly straight. |
| ✅ นับ | คำแนะนำว่าลันจ์ควรลงลึกแค่ไหน (ต้นขาหน้าขนานพื้นโดยประมาณ เข่าหน้าประมาณ 90 องศา) | Recommendations on how deep a lunge should go (front thigh about parallel, front knee about 90 degrees). |
| ❌ ไม่นับ | ย่อเข่าหน้าลึกเกินไป (excessive_front_knee_flexion) | Going too deep with the front knee (excessive_front_knee_flexion). |
| ❌ ไม่นับ | เข่าหลังเหยียดตรง (straight_back_leg) คำแนะนำเรื่องเข่าหลังเป็นอีกกฎหนึ่ง | The back knee staying straight (straight_back_leg): advice about the rear knee is a different rule. |
| ❌ ไม่นับ | ลำตัวโน้ม เข่าหน้ายุบเข้าใน การทรงตัว และระยะก้าวเพียงอย่างเดียว | Trunk lean, the front knee caving in, balance, and step length on its own. |

### ข้อมูลที่นับว่าเกี่ยวข้อง

| หัวข้อ | ภาษาไทย | English |
|---|---|---|
| ลักษณะ | ลักษณะของลันจ์ตื้น | How a shallow lunge looks. |
| สาเหตุ | กล้ามต้นขาหน้าและก้นอ่อนแรง กล้ามงอสะโพกยืดได้น้อย กลัวเสียการทรงตัว | Weak quadriceps and glutes, limited hip flexor flexibility, fear of losing balance. |
| ผลเสีย | ช่วงการเคลื่อนไหวแคบ กล้ามก้นและต้นขาหน้าได้ฝึกเพียงบางช่วง | A small range of motion, so the glutes and quadriceps are trained over only part of their range. |
| วิธีแก้ | ลงจนต้นขาหน้าขนานพื้นโดยประมาณ จับที่ยึดช่วยทรงตัว ใช้ split squat เป็นท่าฝึกขั้นต้น | Lower until the front thigh is about parallel, hold a support for balance, split squats as a regression. |
| ท่าที่ถูก | เข่าหน้างอประมาณ 90 องศาที่จุดต่ำสุด | The front knee bent to about 90 degrees at the bottom. |

### ประโยคตัวอย่าง

**relevant — ช่วยแก้อาการนี้โดยตรง**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| r1 | Many people only dip a few inches during the lunge, keeping the front knee almost straight. | หลายคนย่อลงเพียงไม่กี่นิ้วระหว่างลันจ์ เข่าหน้าเกือบตรง | ท่าผิด |
| r2 | Weak quadriceps and tight hip flexors often stop trainees from sinking low enough in the lunge. | กล้ามต้นขาหน้าที่อ่อนแรงและกล้ามงอสะโพกที่ตึง มักทำให้ผู้ฝึกลันจ์ลงได้ไม่ลึกพอ | สาเหตุ |
| r3 | A shallow lunge moves the front hip and knee through a small arc, so the glutes and quadriceps are trained over only part of their range. | ลันจ์ตื้นทำให้สะโพกและเข่าหน้าขยับในช่วงแคบ กล้ามก้นและต้นขาหน้าได้ฝึกเพียงบางช่วง | ผลเสีย |
| r4 | Lowering until the front thigh is roughly level with the floor puts the front knee close to a right angle. | ลงจนต้นขาหน้าเกือบขนานพื้น เข่าหน้าจะงอใกล้มุมฉาก | วิธีแก้ |
| r5 | Holding a chair or wall for balance lets beginners practise dropping lower without fear of tipping over. | จับเก้าอี้หรือผนังช่วยทรงตัว ทำให้ผู้เริ่มต้นฝึกลงให้ต่ำขึ้นได้โดยไม่กลัวล้ม | วิธีแก้ |
| r6 | In the lowest position of a well-performed lunge the front knee is bent to about ninety degrees. | ที่ตำแหน่งต่ำสุดของลันจ์ที่ดี เข่าหน้างอประมาณ 90 องศา | หลักท่าที่ถูก |

**wrong_fault — พูดถึงท่าผิดอื่น**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| w1 | Sinking so low that the front knee bends far past a right angle loads the knee heavily. | การย่อต่ำจนเข่าหน้างอเลยมุมฉากไปมาก ทำให้เข่ารับแรงหนัก | กฎพี่น้อง `excessive_front_knee_flexion` |
| w2 | The upper body tipped forward over the front thigh during the descent. | ระหว่างย่อลง ลำตัวส่วนบนโน้มไปข้างหน้าเหนือต้นขาหน้า | กฎพี่น้อง `forward_trunk_lean` |
| w3 | The rear leg stayed almost straight instead of bending toward the floor. | ขาหลังเกือบเหยียดตรง แทนที่จะงอลงหาพื้น | กฎพี่น้อง `straight_back_leg` |
| w4 | The front knee wobbled inward toward the midline as the body lowered. | เข่าหน้าส่ายเข้าหาแนวกลางลำตัวขณะย่อลง | `front knee valgus` |
| w5 | The feet were placed in a single line, as if on a tightrope, making it hard to stay balanced. | วางเท้าเป็นเส้นเดียวเหมือนเดินบนเชือก ทำให้ทรงตัวยาก | `narrow base` |

**irrelevant — ไม่ได้พูดถึงท่าผิดเลย**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| i1 | Participants performed walking lunges over a ten-metre course. | ผู้เข้าร่วมทำ walking lunge ระยะทาง 10 เมตร |  |
| i2 | The forward lunge and the reverse lunge were tested in random order. | ทดสอบ forward lunge และ reverse lunge ตามลำดับแบบสุ่ม |  |
| i3 | Dumbbells equal to ten percent of body mass were held in each hand. | ถือดัมเบลน้ำหนัก 10% ของน้ำหนักตัวไว้ในมือแต่ละข้าง |  |

### คำถามถึงผู้เชี่ยวชาญ

- **⚑oq1** เวอร์ชันก่อนโยงการก้าวสั้นเกินกับลันจ์ตื้น ระยะก้าวเป็นสาเหตุของอาการนี้ ของอาการย่อลึกเกิน (excessive_front_knee_flexion) หรือไม่เกี่ยวทั้งคู่ ร่างนี้นับระยะก้าวเฉพาะเมื่อข้อความโยงกับความลึก และใส่การก้าวสั้นเป็นสาเหตุของอาการย่อลึกเกิน
  _Earlier versions linked a step that is too short to a shallow lunge. Is step length a cause of this fault, of the too-deep fault (excessive_front_knee_flexion), or neither? The draft counts step length only when the text ties it to depth, and lists a short step as a cause of the too-deep fault._
  คำตอบ: ________________________

### การอนุมัติ

☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ

หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________

ผู้อนุมัติ: ______________________   วันที่: ______________

---

## 8. ลันจ์ — ย่อเข่าหน้าลึกเกินไป (`excessive_front_knee_flexion`)

`concept_id`: `lunge.excessive_front_knee_flexion` · card version 1 · ชื่อเดิมของกฎ: `front_knee_too_deep`

**ข้อความบนจอ:** "Raise your front knee"

**ระบบวัด** (Lunge rule 2, ตรวจทีละครั้ง): The front knee's lowest hip-knee-ankle angle over the attempt. **แจ้งเมื่อ** That value is less than 70 degrees (LUNGE_FRONT_DEEP_MIN). _New rule with no earlier code. Never fires together with shallow_lunge. The KB may have little on it (a data gap, not a retrieval error)._

### นิยาม

เข่าหน้างอมากกว่า 90 องศาที่ควรเป็นไปมากที่จุดต่ำสุดของลันจ์ (มุมเข่าน้อยกว่าประมาณ 70 องศา) มักเกิดจากสะโพกลดต่ำกว่าระดับเข่าหน้า

> The front knee bends much further than the 90-degree ideal at the bottom of the lunge (a knee angle under about 70 degrees), usually because the hips drop below the level of the front knee.

### นับรวม / ไม่นับ

| | ภาษาไทย | English (LLM ใช้) |
|---|---|---|
| ✅ นับ | ย่อต่ำเกินจนสะโพกอยู่ต่ำกว่าเข่าหน้า | Sinking too low so the hips end up below the front knee. |
| ✅ นับ | เข่าหน้างอลึกมาก และแรงที่เข่าต้องรับเพิ่มขึ้น | Very deep front knee flexion and the extra load it puts on the knee. |
| ✅ นับ ⚑oq2 | ก้าวสั้นเกินไป ทำให้เข่าหน้าต้องพับมากเพื่อให้ตัวลงได้ | A step that is too short, which forces the front knee to fold sharply to get down. |
| ✅ นับ ⚑oq1 | เข่าหน้าพุ่งไปข้างหน้าเลยปลายเท้ามาก เมื่อข้อความโยงกับการที่เข่างอมากเกิน | The front knee travelling far forward past the toes when the text ties it to the knee bending too much. |
| ❌ ไม่นับ | ลันจ์ตื้น (shallow_lunge) | A shallow lunge (shallow_lunge). |
| ❌ ไม่นับ | เข่าหลังเหยียดตรง (straight_back_leg) ลำตัวโน้ม (forward_trunk_lean) | The back knee staying straight (straight_back_leg), trunk lean (forward_trunk_lean). |
| ❌ ไม่นับ | เข่าหน้ายุบเข้าใน เข่าหลังกระแทกพื้น | The front knee caving inward; the back knee hitting the floor. |

### ข้อมูลที่นับว่าเกี่ยวข้อง

| หัวข้อ | ภาษาไทย | English |
|---|---|---|
| ลักษณะ | ลักษณะของเข่าหน้าที่งอลึกเกินที่จุดต่ำสุด | How an over-deep front knee looks at the bottom of the lunge. |
| สาเหตุ | ก้าวสั้นเกิน ปล่อยตัวลงโดยไม่ควบคุม พยายามลงให้ต่ำที่สุด | A step that is too short, dropping without control, trying to go as low as possible. |
| ผลเสีย | แรงกดสูงที่ข้อต่อลูกสะบ้า อาจเจ็บเข่า | High compressive load on the patellofemoral joint, knee pain. |
| วิธีแก้ | หยุดเมื่อต้นขาหน้าขนานพื้นโดยประมาณ ก้าวให้ยาวขึ้น ควบคุมการลง | Stop when the front thigh is about parallel, lengthen the step, control the descent. |
| ท่าที่ถูก | เข่าหน้าประมาณ 90 องศา หน้าแข้งค่อนข้างตั้งตรง | The front knee at about 90 degrees with the shin fairly upright. |

### ประโยคตัวอย่าง

**relevant — ช่วยแก้อาการนี้โดยตรง**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| r1 | Dropping the hips below the height of the front knee bends that knee well past a right angle. | การลดสะโพกลงต่ำกว่าความสูงของเข่าหน้า ทำให้เข่านั้นงอเลยมุมฉากไปมาก | ท่าผิด |
| r2 ⚑oq2 | Taking a very short step forces the front knee to fold sharply and travel forward to get the body down. | การก้าวสั้นมากบังคับให้เข่าหน้าพับมากและเคลื่อนไปข้างหน้าเพื่อให้ตัวลงได้ | สาเหตุ |
| r3 | Very deep front knee flexion greatly increases the compressive force between the kneecap and the thigh bone. | การงอเข่าหน้าลึกมากเพิ่มแรงกดระหว่างลูกสะบ้ากับกระดูกต้นขาอย่างมาก | ผลเสีย |
| r4 | Stop the descent once the front thigh is level with the floor rather than sinking as low as possible. | หยุดย่อเมื่อต้นขาหน้าขนานพื้น แทนที่จะลงให้ต่ำที่สุด | วิธีแก้ |
| r5 | Lengthening the stride lets the body lower without the front knee folding so sharply. | การก้าวให้ยาวขึ้นทำให้ตัวลงได้โดยเข่าหน้าไม่ต้องพับมาก | วิธีแก้ |
| r6 | The front knee should bend to roughly ninety degrees at the bottom, not far beyond it. | ที่จุดต่ำสุด เข่าหน้าควรงอประมาณ 90 องศา ไม่ใช่เลยไปมาก | หลักท่าที่ถูก |

**wrong_fault — พูดถึงท่าผิดอื่น**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| w1 | The lifter barely bent the front knee and stayed high throughout the lunge. | ผู้ฝึกแทบไม่งอเข่าหน้าและตัวอยู่สูงตลอดการลันจ์ | กฎพี่น้อง `shallow_lunge` |
| w2 | Bending forward at the waist brought the chest down over the front knee. | การก้มตัวที่เอวทำให้อกลงมาอยู่เหนือเข่าหน้า | กฎพี่น้อง `forward_trunk_lean` |
| w3 | The rear knee remained locked out instead of lowering toward the ground. | เข่าหลังเหยียดล็อกอยู่แทนที่จะลดลงหาพื้น | กฎพี่น้อง `straight_back_leg` |
| w4 | The front knee drifted inward past the big toe as the lunge descended. | เข่าหน้าเบนเข้าในเลยนิ้วโป้งเท้าขณะลันจ์ลง | `front knee valgus` |
| w5 | The hips rotated so the pelvis no longer faced forward. | สะโพกหมุนจนเชิงกรานไม่หันไปข้างหน้า | `pelvic rotation` |

**irrelevant — ไม่ได้พูดถึงท่าผิดเลย**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| i1 | Knee joint moments were computed using inverse dynamics. | คำนวณโมเมนต์ที่ข้อเข่าด้วยวิธี inverse dynamics |  |
| i2 | The split squat is a stationary variation in which both feet stay in place. | split squat เป็นแบบที่อยู่กับที่ เท้าทั้งสองข้างไม่ขยับ |  |
| i3 | Participants practised the lunge in a session one week before testing. | ผู้เข้าร่วมฝึกลันจ์หนึ่งครั้งหนึ่งสัปดาห์ก่อนการทดสอบ |  |

### คำถามถึงผู้เชี่ยวชาญ

- **⚑oq1** เข่าหน้าพุ่งเลยปลายเท้ามากนับเป็นอาการนี้ด้วยหรือไม่ ร่างนี้นับเฉพาะเมื่อข้อความโยงกับการที่เข่างอมากเกิน
  _Does the front knee travelling far past the toes count as this fault? The draft counts it only when the text ties it to the knee bending too much._
  คำตอบ: ________________________

- **⚑oq2** การก้าวสั้นเกินเป็นสาเหตุของอาการนี้หรือไม่ (ดู oq1 ของ lunge.insufficient_depth)
  _Is a step that is too short a cause of this fault? (See oq1 on lunge.insufficient_depth.)_
  คำตอบ: ________________________

### การอนุมัติ

☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ

หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________

ผู้อนุมัติ: ______________________   วันที่: ______________

---

## 9. ลันจ์ — ก้มตัวไปหน้ามากเกินไป (`forward_trunk_lean`)

`concept_id`: `lunge.forward_trunk_lean` · card version 1 · ชื่อเดิมของกฎ: `torso_upright`

**ข้อความบนจอ:** "Keep Torso Upright"

**ระบบวัด** (Lunge rule 3, ตรวจทีละเฟรม): Trunk tilt: angle between the hip-to-shoulder line and the vertical (0 = upright), taking the smaller of the two sides. **แจ้งเมื่อ** The tilt is greater than 20 degrees (LUNGE_TILT_MAX) for 10 consecutive frames.

### นิยาม

ลำตัวส่วนบนโน้มไปข้างหน้าจากสะโพกระหว่างลันจ์ แทนที่จะตั้งตรงหรือเกือบตรง

> The upper body tips forward from the hips during the lunge instead of staying close to upright.

### นับรวม / ไม่นับ

| | ภาษาไทย | English (LLM ใช้) |
|---|---|---|
| ✅ นับ | ก้มตัวที่เอว อกลงหาต้นขาหน้า | Bending forward at the waist, the chest dropping toward the front thigh. |
| ✅ นับ | งานวิจัยที่เปรียบเทียบลำตัวตั้งตรงกับลำตัวโน้มไปหน้าในลันจ์ | Research comparing an upright trunk with a forward-leaning trunk in the lunge. |
| ❌ ไม่นับ | เอียงตัวไปด้านข้างหรือไหล่ข้างหนึ่งตก | Leaning sideways or dropping one shoulder. |
| ❌ ไม่นับ | หลังค่อมหรือหลังแอ่น โดยไม่มีการโน้มไปหน้า | Rounding or arching the back without a forward lean. |
| ❌ ไม่นับ | ความลึกของเข่าหน้า (shallow_lunge, excessive_front_knee_flexion) เข่าหลัง (straight_back_leg) เข่าหน้ายุบเข้าใน | Front knee depth (shallow_lunge, excessive_front_knee_flexion), the back knee (straight_back_leg), the front knee caving in. |

### ข้อมูลที่นับว่าเกี่ยวข้อง

| หัวข้อ | ภาษาไทย | English |
|---|---|---|
| ลักษณะ | ลักษณะของลำตัวที่โน้มไปหน้าในลันจ์ | How a forward-leaning trunk looks in the lunge. |
| สาเหตุ | กล้ามงอสะโพกของขาหลังตึง กล้ามเหยียดลำตัวอ่อนแรง โน้มตัวเพื่อทรงตัว น้ำหนักมากเกิน | Tight hip flexors on the rear leg, weak trunk extensors, leaning to keep balance, a load that is too heavy. |
| ผลเสีย | ย้ายแรงระหว่างสะโพกกับเข่า หลังล่างรับแรงมาก ทรงตัวได้น้อยลง | Shifts load between hip and knee, strain on the lower back, reduced balance. |
| วิธีแก้ | ยืดอก ให้ไหล่อยู่เหนือสะโพก ลงตรง ๆ เกร็งแกนกลาง | Keep the chest tall and shoulders over the hips, lower straight down, brace the core. |
| ท่าที่ถูก | ลำตัวเกือบตั้งฉากกับพื้น | The torso stays close to vertical. |

### ประโยคตัวอย่าง

**relevant — ช่วยแก้อาการนี้โดยตรง**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| r1 | As she stepped forward her chest folded down toward the front thigh. | ตอนก้าวไปข้างหน้า อกของเธอพับลงหาต้นขาหน้า | ท่าผิด |
| r2 | Tight hip flexors on the trailing leg and weak back extensors often cause the upper body to tip forward in the lunge. | กล้ามงอสะโพกของขาหลังที่ตึงและกล้ามเหยียดหลังที่อ่อนแรง มักทำให้ลำตัวส่วนบนโน้มไปข้างหน้าในลันจ์ | สาเหตุ |
| r3 | Tilting the trunk forward during the lunge made the hip muscles work harder while the quadriceps worked less. | การโน้มลำตัวไปหน้าระหว่างลันจ์ทำให้กล้ามสะโพกทำงานมากขึ้น ขณะที่กล้ามต้นขาหน้าทำงานน้อยลง | ผลวิจัย |
| r4 | Keep the chest tall and the shoulders stacked over the hips as you lower. | ยืดอกและให้ไหล่อยู่เหนือสะโพกขณะย่อลง | วิธีแก้ |
| r5 | Keeping a broomstick in contact with the head, upper back and tailbone is a simple way to feel whether the torso stays upright. | การให้ไม้กวาดแตะศีรษะ หลังส่วนบน และก้นกบไว้ตลอด เป็นวิธีง่าย ๆ ให้รู้ว่าลำตัวยังตั้งตรงอยู่หรือไม่ | วิธีแก้ |
| r6 | The torso should stay close to vertical, with the body lowering straight down between the feet. | ลำตัวควรเกือบตั้งตรง และตัวลดลงตรง ๆ ระหว่างเท้าทั้งสอง | หลักท่าที่ถูก |

**wrong_fault — พูดถึงท่าผิดอื่น**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| w1 | The front knee stayed nearly straight, so the lunge barely lowered the body. | เข่าหน้าเกือบตรง ลันจ์จึงแทบไม่ได้ลดตัวลง | กฎพี่น้อง `shallow_lunge` |
| w2 | The hips sank below the front knee, folding it far beyond ninety degrees. | สะโพกลดต่ำกว่าเข่าหน้า ทำให้เข่าพับเลย 90 องศาไปมาก | กฎพี่น้อง `excessive_front_knee_flexion` |
| w3 | The back leg stayed rigid and straight at the bottom of each lunge. | ขาหลังแข็งและตรงที่จุดต่ำสุดทุกครั้ง | กฎพี่น้อง `straight_back_leg` |
| w4 | The front knee collapsed inward toward the opposite leg. | เข่าหน้ายุบเข้าหาขาอีกข้าง | `front knee valgus` |
| w5 | The lifter leaned sideways toward the stance leg, dropping one shoulder. | ผู้ฝึกเอียงตัวไปทางขาที่ยืน ไหล่ข้างหนึ่งตก | `lateral trunk lean` |

**irrelevant — ไม่ได้พูดถึงท่าผิดเลย**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| i1 | Reverse lunges were performed with a dumbbell held in each hand. | ทำ reverse lunge โดยถือดัมเบลไว้ในมือแต่ละข้าง |  |
| i2 | Electromyographic signals were normalised to maximal voluntary isometric contractions. | ปรับสัญญาณไฟฟ้ากล้ามเนื้อเทียบกับการหดตัวแบบเกร็งค้างสูงสุด |  |
| i3 | Lunges are often prescribed during rehabilitation after knee injury. | ลันจ์มักถูกใช้ในการฟื้นฟูหลังบาดเจ็บที่เข่า |  |

### การอนุมัติ

☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ

หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________

ผู้อนุมัติ: ______________________   วันที่: ______________

---

## 10. ลันจ์ — เข่าหลังงอไม่สุด (`straight_back_leg`)

`concept_id`: `lunge.straight_back_leg` · card version 1 · ชื่อเดิมของกฎ: `back_knee_form`

**ข้อความบนจอ:** "Bend your back knee toward the floor"

**ระบบวัด** (Lunge rule 4, ตรวจทีละครั้ง): The back knee's hip-knee-ankle angle at the bottom of the rep (its smallest value within 2 frames of the front knee's deepest frame). **แจ้งเมื่อ** That value is greater than 120 degrees (LUNGE_BACK_MAX_MIN). _No verdict when the front knee never reached 105 degrees. There is no 'back knee too bent' rule._

### นิยาม

ที่จุดต่ำสุดของลันจ์ ขาหลังยังเหยียดตรงเกินไป เข่าหลังไม่งอและไม่ลดลงหาพื้น

> At the bottom of the lunge the rear leg stays too straight: the back knee does not bend and lower toward the floor.

### นับรวม / ไม่นับ

| | ภาษาไทย | English (LLM ใช้) |
|---|---|---|
| ✅ นับ | เข่าหลังล็อกหรือเกือบตรงที่จุดต่ำสุด | The rear knee locked or nearly straight at the bottom. |
| ✅ นับ | ดันตัวไปข้างหน้าลงที่ขาหน้า แทนที่จะลดตัวลงตรง ๆ ระหว่างเท้า | Pushing the body forward onto the front leg instead of dropping down between the feet. |
| ❌ ไม่นับ | เข่าหลังกระแทกพื้น (ลงลึกเกิน ไม่มีกฎนี้) | The back knee slamming into the floor (too deep, no rule). |
| ❌ ไม่นับ | ความลึกของเข่าหน้า (shallow_lunge, excessive_front_knee_flexion) และลำตัวโน้ม (forward_trunk_lean) | Front knee depth (shallow_lunge, excessive_front_knee_flexion) and trunk lean (forward_trunk_lean). |
| ❌ ไม่นับ | ตำแหน่งส้นเท้าหรือเท้าหลังเพียงอย่างเดียว | Rear heel or foot position on its own. |

### ข้อมูลที่นับว่าเกี่ยวข้อง

| หัวข้อ | ภาษาไทย | English |
|---|---|---|
| ลักษณะ | ลักษณะของขาหลังที่เหยียดตรงที่จุดต่ำสุด | How a straight rear leg looks at the bottom of the lunge. |
| สาเหตุ | กล้ามงอสะโพกหรือกล้ามต้นขาหน้าของขาหลังตึง เคลื่อนตัวไปข้างหน้าแทนที่จะลงล่าง ก้าวยาวเกินไป | Tight hip flexors or quadriceps of the rear leg, moving the body forward rather than down, a step that is too long. |
| ผลเสีย | แรงย้ายไปที่เข่าหน้า ขาหลังแทบไม่ได้ทำงาน ลันจ์กลายเป็นการโน้มตัว | Load shifts onto the front knee, the rear leg does little work, the lunge turns into a lean. |
| วิธีแก้ | บอกให้เข่าหลังลงหาพื้น ลดตัวลงตรง ๆ วางเบาะใต้เข่าหลังเป็นเป้า ฝึก split squat | Cue the back knee down toward the floor, lower straight down, a pad under the rear knee as a target, split squats. |
| ท่าที่ถูก | เข่าทั้งสองข้างงอประมาณ 90 องศา เข่าหลังอยู่เหนือพื้นเล็กน้อย | Both knees bent to about 90 degrees, the back knee just above the floor. |

### ประโยคตัวอย่าง

**relevant — ช่วยแก้อาการนี้โดยตรง**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| r1 | In the lowest position the rear leg was still nearly straight, with the back knee far from the floor. | ที่ตำแหน่งต่ำสุด ขาหลังยังเกือบตรง และเข่าหลังอยู่ห่างพื้นมาก | ท่าผิด |
| r2 | Tightness in the hip flexors and quadriceps of the trailing leg makes it hard to let that knee bend and drop. | กล้ามงอสะโพกและกล้ามต้นขาหน้าของขาหลังที่ตึง ทำให้งอเข่าข้างนั้นและลดลงได้ยาก | สาเหตุ |
| r3 | When the rear knee stays straight, most of the body weight shifts forward onto the lead leg. | เมื่อเข่าหลังเหยียดตรง น้ำหนักตัวส่วนใหญ่จะย้ายไปที่ขาหน้า | ผลเสีย |
| r4 | Think about sinking the back knee straight down toward the floor rather than pushing the body forward. | คิดว่ากำลังลดเข่าหลังลงหาพื้นตรง ๆ แทนที่จะดันตัวไปข้างหน้า | วิธีแก้ |
| r5 | A folded mat under the rear knee gives a soft target to lower toward on every repetition. | วางเสื่อพับไว้ใต้เข่าหลัง เป็นเป้านุ่ม ๆ ให้ลดลงไปหาทุกครั้ง | วิธีแก้ |
| r6 | In a good lunge both knees bend to about ninety degrees, with the back knee hovering just above the ground. | ในลันจ์ที่ดี เข่าทั้งสองข้างงอประมาณ 90 องศา และเข่าหลังลอยอยู่เหนือพื้นเล็กน้อย | หลักท่าที่ถูก |

**wrong_fault — พูดถึงท่าผิดอื่น**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| w1 | The front knee barely bent, keeping the hips high throughout the lunge. | เข่าหน้าแทบไม่งอ สะโพกจึงอยู่สูงตลอดการลันจ์ | กฎพี่น้อง `shallow_lunge` |
| w2 | The front knee folded well under ninety degrees as the hips dropped too low. | เข่าหน้าพับน้อยกว่า 90 องศามากเพราะสะโพกลดต่ำเกินไป | กฎพี่น้อง `excessive_front_knee_flexion` |
| w3 | The chest dipped forward over the front leg during each repetition. | อกโน้มไปข้างหน้าเหนือขาหน้าทุกครั้ง | กฎพี่น้อง `forward_trunk_lean` |
| w4 | The back knee banged into the floor on every rep. | เข่าหลังกระแทกพื้นทุกครั้ง | `back knee hitting the floor` |
| w5 | The front heel lifted off the ground as the knee shifted forward. | ส้นเท้าหน้ายกจากพื้นขณะเข่าเคลื่อนไปข้างหน้า | `front heel lifting` |

**irrelevant — ไม่ได้พูดถึงท่าผิดเลย**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| i1 | Participants performed three sets of ten lunges on each leg. | ผู้เข้าร่วมทำลันจ์ 3 เซ็ต เซ็ตละ 10 ครั้งต่อขา |  |
| i2 | Lower-limb motion was filmed from the side with a single video camera. | ถ่ายวิดีโอการเคลื่อนไหวของขาจากด้านข้างด้วยกล้องตัวเดียว |  |
| i3 | Because it works one leg at a time, the lunge also challenges balance. | เพราะลันจ์ฝึกทีละขา จึงท้าทายการทรงตัวด้วย |  |

### การอนุมัติ

☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ

หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________

ผู้อนุมัติ: ______________________   วันที่: ______________

---

## 11. ไบเซ็ปส์เคิร์ล — ศอกไม่แนบลำตัว (กาง / ลอยไปหน้า / ไปหลัง) (`elbow_flare`)

`concept_id`: `bicep-curl.elbow_drift` · card version 1 · ชื่อเดิมของกฎ: `elbow_away`

**ข้อความบนจอ:** "Keep Elbows at Your Sides"

**ระบบวัด** (Bicep curl rule 1, ตรวจทีละเฟรม): The active arm's elbow-shoulder-hip interior angle (0 = upper arm along the torso). **แจ้งเมื่อ** The angle is greater than 45 degrees (BICEP_ELBOW_FLARE_MAX) for 10 consecutive frames. _The rule does not say which way (out, forward or back). A strongly flared elbow can keep the elbow from bending to 55, in which case the attempt is not counted but the cue is still shown._

### นิยาม

ระหว่างเคิร์ล ต้นแขนเคลื่อนออกจากข้างลำตัว ศอกลอยออกจากลำตัว ไม่ว่าจะไปข้างหน้า ออกด้านข้าง หรือไปข้างหลัง แทนที่จะแนบข้างลำตัว

> During the curl the upper arm moves away from the side of the body, so the elbow leaves the torso - forward, outward or backward - instead of staying at the side.

### นับรวม / ไม่นับ

| | ภาษาไทย | English (LLM ใช้) |
|---|---|---|
| ✅ นับ | ศอกลอยไปข้างหน้า โดยเฉพาะช่วงบนของเคิร์ล | Elbows drifting forward, especially near the top of the curl. |
| ✅ นับ | ศอกกางออกด้านข้าง หรือเคลื่อนไปด้านหลังลำตัว | Elbows flaring out to the sides, or moving behind the body. |
| ✅ นับ | ใช้ไหล่ด้านหน้ายกศอกขึ้นเพื่อให้จบครั้ง | Using the front shoulder to raise the elbow and finish the repetition. |
| ❌ ไม่นับ | เหวี่ยงลำตัวหรือใช้สะโพกส่งแรง เมื่อข้อความพูดถึงลำตัว ไม่ใช่ต้นแขน | Swinging the torso or using the hips for momentum when the text is about the body, not the upper arm. |
| ❌ ไม่นับ | เหยียดหรืองอศอกไม่สุด (partial_curl) | Not fully extending or flexing the elbow (partial_curl). |
| ❌ ไม่นับ | ข้อมืองอ ความเร็วของจังหวะ การจับ การยักไหล่ | Wrist bending, tempo, grip, shrugging. |

### ข้อมูลที่นับว่าเกี่ยวข้อง

| หัวข้อ | ภาษาไทย | English |
|---|---|---|
| ลักษณะ | ลักษณะของศอกที่ลอยออกจากข้างลำตัว | How the elbow leaving the side of the body looks. |
| สาเหตุ | น้ำหนักมากเกิน ความล้า ใช้ไหล่ช่วยยกให้จบ | A weight that is too heavy, fatigue, recruiting the shoulder to finish the lift. |
| ผลเสีย | ไหล่รับงานไปบางส่วน กล้ามไบเซ็ปส์ได้แรงตึงน้อยลง ไหล่รับแรงเครียด | The shoulder takes over part of the work, less tension on the biceps, strain on the shoulder. |
| วิธีแก้ | ลดน้ำหนัก ล็อกศอกไว้กับซี่โครง เคิร์ลโดยหลังพิงผนัง ใช้ preacher curl ยกช้าลง | A lighter weight, pinning the elbows to the ribs, curling with the back against a wall, preacher curls, a slower tempo. |
| ท่าที่ถูก | ขยับเฉพาะแขนท่อนล่าง ต้นแขนตั้งตรงแนบข้างลำตัว | Only the forearm moves; the upper arm stays vertical beside the torso. |

### ประโยคตัวอย่าง

**relevant — ช่วยแก้อาการนี้โดยตรง**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| r1 | As the dumbbells neared his shoulders, his elbows drifted forward and the upper arms left his sides. | ขณะดัมเบลใกล้ถึงไหล่ ศอกของเขาลอยไปข้างหน้าและต้นแขนออกจากข้างลำตัว | ท่าผิด |
| r2 | Letting the elbows flare out to the sides turns the curl into a partial shoulder movement. | การปล่อยให้ศอกกางออกด้านข้างทำให้เคิร์ลกลายเป็นการใช้ไหล่ส่วนหนึ่ง | ท่าผิด |
| r3 | Picking a dumbbell that is too heavy leads people to raise the elbow with the front deltoid to finish each repetition. | การเลือกดัมเบลที่หนักเกินทำให้คนใช้ไหล่ด้านหน้ายกศอกขึ้นเพื่อให้จบแต่ละครั้ง | สาเหตุ |
| r4 | Once the upper arm moves, the shoulder shares the work and the tension on the biceps drops. | เมื่อต้นแขนขยับ ไหล่จะช่วยรับงาน และแรงตึงที่ไบเซ็ปส์ลดลง | ผลเสีย |
| r5 | Curling while leaning the shoulders and hips on a wall makes it easier to keep the elbows fixed beside the ribs. | การเคิร์ลโดยให้ไหล่และสะโพกพิงผนัง ช่วยให้คงศอกไว้ข้างซี่โครงได้ง่ายขึ้น | วิธีแก้ |
| r6 | Only the forearm should move during the curl; the upper arm stays vertical and close to the torso. | ระหว่างเคิร์ลควรขยับเฉพาะแขนท่อนล่าง ต้นแขนตั้งตรงและชิดลำตัว | หลักท่าที่ถูก |

**wrong_fault — พูดถึงท่าผิดอื่น**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| w1 | The arms never straightened at the bottom before the next repetition began. | แขนไม่เคยเหยียดตรงที่ตำแหน่งล่างก่อนเริ่มครั้งถัดไป | กฎพี่น้อง `partial_curl` |
| w2 | He stopped each curl halfway up, well before the forearm reached the upper arm. | เขาหยุดเคิร์ลที่ครึ่งทางทุกครั้ง ก่อนแขนท่อนล่างจะขึ้นไปถึงต้นแขน | กฎพี่น้อง `partial_curl` |
| w3 | Rocking the hips and leaning back helped swing the dumbbell up. | การโยกสะโพกและเอนตัวไปข้างหลังช่วยเหวี่ยงดัมเบลขึ้น | `torso swing` |
| w4 | The wrists bent backward under the weight as the dumbbells reached shoulder height. | ข้อมืองอไปด้านหลังเพราะน้ำหนักเมื่อดัมเบลขึ้นถึงระดับไหล่ | `wrist extension` |
| w5 | Lowering the weight in under half a second removed most of the eccentric work. | การลดน้ำหนักลงในเวลาไม่ถึงครึ่งวินาทีทำให้แทบไม่ได้ฝึกช่วงยืดกล้าม | `fast eccentric` |

**irrelevant — ไม่ได้พูดถึงท่าผิดเลย**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| i1 | Dumbbells of eight, ten and twelve kilograms were used for testing. | ใช้ดัมเบลหนัก 8, 10 และ 12 กิโลกรัมในการทดสอบ |  |
| i2 | Biceps brachii activity was recorded with electrodes placed over the muscle belly. | บันทึกการทำงานของไบเซ็ปส์ด้วยขั้วไฟฟ้าที่วางบนกลางกล้ามเนื้อ |  |
| i3 | The hammer curl is done with the thumbs pointing up throughout. | hammer curl ทำโดยให้นิ้วโป้งชี้ขึ้นตลอด |  |

### การอนุมัติ

☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ

หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________

ผู้อนุมัติ: ______________________   วันที่: ______________

---

## 12. ไบเซ็ปส์เคิร์ล — ยกไม่สุดช่วง (`partial_curl`)

`concept_id`: `bicep-curl.partial_range` · card version 1 · ชื่อเดิมของกฎ: `full_rom`

**ข้อความบนจอ:** "Full range of motion"

**ระบบวัด** (Bicep curl rule 2, ตรวจทีละครั้ง): The active arm's elbow angle over the attempt: its minimum and its maximum. **แจ้งเมื่อ** NOT (minimum at or below 55 degrees (BICEP_FLEX_TARGET) AND maximum at or above 145 degrees (BICEP_EXT_TARGET)). Missing either end fires it. _The flexion bar equals the curl count bar, so on counted reps only the extension half can fail._

### นิยาม

เคิร์ลไม่ครบช่วงการเคลื่อนไหว คือ ไม่เหยียดแขนสุดที่ตำแหน่งล่าง หรือไม่ยกขึ้นจนสุดที่ตำแหน่งบน (ทำครึ่งครั้ง)

> The curl is not taken through its full range: either the arm is not straightened at the bottom, or the weight is not curled all the way up at the top (half repetitions).

### นับรวม / ไม่นับ

| | ภาษาไทย | English (LLM ใช้) |
|---|---|---|
| ✅ นับ | ไม่เหยียดแขนสุดที่ตำแหน่งล่างก่อนเริ่มครั้งถัดไป | Not straightening the arm at the bottom before the next repetition. |
| ✅ นับ | ไม่ยกขึ้นจนสุดที่ตำแหน่งบน | Not curling all the way up at the top. |
| ✅ นับ | งานวิจัยเรื่องช่วงการเคลื่อนไหวเต็มเทียบกับบางส่วนในการฝึกกล้ามงอศอก | Research on full versus partial range of motion in elbow flexor training. |
| ❌ ไม่นับ | ต้นแขนหรือศอกลอยออกจากลำตัว (elbow_flare) | The upper arm or elbow moving away from the torso (elbow_flare). |
| ❌ ไม่นับ | เหวี่ยงตัวส่งแรง ตำแหน่งข้อมือ ความเร็วของจังหวะเพียงอย่างเดียว | Swinging the body for momentum, wrist position, tempo on its own. |

### ข้อมูลที่นับว่าเกี่ยวข้อง

| หัวข้อ | ภาษาไทย | English |
|---|---|---|
| ลักษณะ | ลักษณะของการทำครึ่งครั้งที่ตำแหน่งล่างและบน | How half repetitions look at the bottom and at the top. |
| สาเหตุ | น้ำหนักมากเกิน ความล้า รีบทำให้ครบจำนวน | A weight that is too heavy, fatigue, rushing through repetitions. |
| ผลเสีย | กล้ามได้รับการกระตุ้นน้อยในช่วงที่ยืดยาว ความแข็งแรงและขนาดเพิ่มเฉพาะช่วงที่ฝึก | Less stimulus at long muscle lengths, strength and size gains limited to the trained range. |
| วิธีแก้ | ลดน้ำหนัก หยุดค้างตอนแขนเหยียดที่ตำแหน่งล่าง เกร็งค้างที่ตำแหน่งบน | A lighter weight, pausing with the arm straight at the bottom, squeezing at the top. |
| ท่าที่ถูก | แต่ละครั้งเคลื่อนจากศอกเกือบเหยียดตรงไปจนศอกงอสุด | Each repetition goes from a nearly straight elbow to a fully bent elbow. |

### ประโยคตัวอย่าง

**relevant — ช่วยแก้อาการนี้โดยตรง**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| r1 | Many lifters start the next repetition before the arm has fully straightened at the bottom. | หลายคนเริ่มครั้งถัดไปก่อนแขนจะเหยียดตรงเต็มที่ที่ตำแหน่งล่าง | ท่าผิด |
| r2 | Stopping the curl while the forearm is still well below the upper arm leaves the fully flexed position untrained. | การหยุดเคิร์ลตอนที่แขนท่อนล่างยังต่ำกว่าต้นแขนมาก ทำให้ไม่ได้ฝึกตำแหน่งที่ศอกงอสุด | ท่าผิด |
| r3 | Lifting a load that is too heavy often forces people into short, choppy repetitions through the middle of the range. | การยกน้ำหนักที่หนักเกินมักทำให้คนยกสั้น ๆ กระตุก ๆ อยู่แค่ช่วงกลาง | สาเหตุ |
| r4 | Curls trained through the complete range produced larger increases in elbow flexor size than curls restricted to part of the range. | เคิร์ลที่ฝึกเต็มช่วงทำให้กล้ามงอศอกโตขึ้นมากกว่าเคิร์ลที่จำกัดเพียงบางช่วง | ผลวิจัย |
| r5 | Pause briefly with the arm straight at the bottom so every repetition begins from full extension. | หยุดค้างสั้น ๆ ตอนแขนเหยียดตรงที่ตำแหน่งล่าง เพื่อให้ทุกครั้งเริ่มจากเหยียดสุด | วิธีแก้ |
| r6 | Each repetition should travel from an almost straight elbow at the bottom to a fully bent elbow at the top. | แต่ละครั้งควรเคลื่อนจากศอกเกือบเหยียดตรงที่ตำแหน่งล่าง ไปจนศอกงอสุดที่ตำแหน่งบน | หลักท่าที่ถูก |

**wrong_fault — พูดถึงท่าผิดอื่น**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| w1 | The elbows drifted forward away from the ribs as the weight came up. | ศอกลอยไปข้างหน้าออกจากซี่โครงขณะยกน้ำหนักขึ้น | กฎพี่น้อง `elbow_flare` |
| w2 | His upper arms flared out to the side during the lift. | ต้นแขนของเขากางออกด้านข้างระหว่างยก | กฎพี่น้อง `elbow_flare` |
| w3 | Leaning back and swinging the torso generated momentum to lift the bar. | การเอนหลังและเหวี่ยงลำตัวสร้างแรงส่งเพื่อยกบาร์ | `torso swing` |
| w4 | The wrists curled inward at the top, shifting work to the forearm flexors. | ข้อมืองอเข้าที่ตำแหน่งบน ย้ายงานไปที่กล้ามงอแขนท่อนล่าง | `wrist flexion` |
| w5 | Letting the dumbbell drop quickly on the way down removed control from the lowering phase. | การปล่อยดัมเบลลงเร็วทำให้ไม่ได้ควบคุมช่วงลดน้ำหนักลง | `uncontrolled lowering` |

**irrelevant — ไม่ได้พูดถึงท่าผิดเลย**

| # | ประโยค | คำแปล | ชนิด |
|---|---|---|---|
| i1 | Standing curls were performed with a straight barbell and an underhand grip. | ทำเคิร์ลแบบยืนด้วยบาร์ตรงและจับแบบหงายมือ |  |
| i2 | Participants trained their elbow flexors twice a week for ten weeks. | ผู้เข้าร่วมฝึกกล้ามงอศอกสัปดาห์ละ 2 ครั้งเป็นเวลา 10 สัปดาห์ |  |
| i3 | Grip strength was measured with a handheld dynamometer. | วัดแรงบีบมือด้วยเครื่องวัดแรงแบบมือถือ |  |

### การอนุมัติ

☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ

หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________

ผู้อนุมัติ: ______________________   วันที่: ______________

---

# T3a — รายการคัดเอกสารออกทั้งไฟล์ (ให้ user ตรวจ)

> 2026-10-02 · ผู้คัด: Claude · ไฟล์ผล: [`data_pipeline/prefilter_v6.json`](../../data_pipeline/prefilter_v6.json) · เกณฑ์: [rule_change_v6_plan.md §T3a](../plans/rule_change_v6_plan.md)
> **ตรวจรายการ drop (§2) และ keep ที่ไม่แน่ใจ (§3)** ถ้าจะกลับคำตัดสิน แก้ `decision` ใน JSON ได้เลย ไม่ได้ลบหรือย้ายไฟล์ใน `data/`

## 1. สรุป

| ท่า | หน่วยทั้งหมด | keep | drop | pending |
|---|---|---|---|---|
| bicep-curl | 24 (PDF 20 · URL 4) | 15 | 9 | — |
| lunge | 31 (PDF 28 · URL 3) | 22 | 9 | — |
| push-up | 18 (PDF 12 · URL 6) | 10 | 8 | — |
| squat | 23 (PDF 19 · URL 4) | 22 | 1 | — |
| general | 6 (PDF) | 2 | 4 (P5) | — |
| **รวม** | **102** (PDF 85 · URL 17) | **71** | **31** (27 + P5 4) | **0** |

- อ่าน: ชื่อเรื่อง, abstract, สารบัญ/bookmark, 2 หน้าแรก และค้นคำสำคัญทั้งไฟล์เมื่อยังตัดสินไม่ได้ (ฟิลด์ `read` ของแต่ละหน่วยบอกว่าอ่านส่วนไหน) · URL ดึงด้วย trafilatura แบบเดียวกับ curator ได้ครบทั้ง 17 ตัว
- ไม่ได้เปิด `curated_data_v5/` และไม่ได้เรียก API ที่เสียเงิน
- เหตุผลที่ drop ส่วนใหญ่มี 3 กลุ่ม: (ก) วัดแค่ EMG/แรง/ผลของโปรแกรม ไม่พูดถึงท่าทาง (ข) ตัวแปรที่ศึกษาไม่ใช่กฎของเรา เช่น ความกว้างมือ มุมเท้า (ค) เป็นงานวิธีวัด/โมเดล หรือผลทางคลินิก

## 2. รายการ drop (27)

### bicep-curl (9)
| id | ไฟล์ | เหตุผล |
|---|---|---|
| u000 | A Comparison of Muscle Unit Activation … 40, 60, 80 and 100% of 1RM | หน้า proceedings · abstract ของ curl วัดแค่ EMG ตาม %1RM · abstract อื่นในหน้าไม่เกี่ยว |
| u004 | Biceps Disorder Rehabilitation for the Athlete | ลำดับท่ากายภาพ 11 ท่าส่วนใหญ่ไม่ใช่ curl (pull-up, Xco, air punch) มีแค่ inclined curl |
| u006 | Core Muscle Activation During Unstable Bicep Curl (water-filled tube) | abstract เรื่องอุปกรณ์ไม่เสถียรกับ EMG แกนกลางลำตัว · หน้ามี abstract อื่นไม่เกี่ยว |
| u007 | Distinct muscle growth … preacher and incline biceps curls | ผล hypertrophy ของท่าดัดแปลง 2 ท่า ไม่มีเรื่องท่าผิดของ curl ปกติ |
| u008 | Exertional Rhabdomyolysis … Case Report | รายงานผู้ป่วยกล้ามเนื้อสลาย (ผลทางคลินิก) |
| u010 | … biceps curl on a new machine (eccentric overload, drop setting) | เครื่อง CARE กับดัมเบล: แรง EMG ความล้า · ท่าทางมีแค่เป็นกติกาในการทดสอบ |
| u012 | Unilateral bicep curl hemodynamics (BFR) | ความดันเลือดและชีพจรของ BFR |
| u013 | Neutral vs supinated grip bicep curl (poster) | EMG/แรงบิดบนเครื่อง isokinetic ตามแบบจับ |
| u017 | The Rest-Pause Biceps Curl … Mechanical Responsiveness | โมเดลความเค้น/ความเครียดของกล้ามเนื้อ |

### lunge (9)
| id | ไฟล์ | เหตุผล |
|---|---|---|
| u030 | ACL/Meniscal injury alters patellofemoral kinematics … single-leg lunge | ภาพถ่ายข้อเข่าผู้ป่วย ACL ไม่มีเรื่องความลึก ลำตัว หรือขาหลัง |
| u031 | Altered movement strategy after ACL injury | ประเมินการ lunge ด้วย knee valgus/pelvic drop ซึ่งไม่ใช่กฎของ lunge |
| u033 | Changes in lower limb muscle activity … ankle abduction | EMG ตามมุมเท้า · มุมเท้าไม่ใช่กฎ |
| u035 | VMO/VL EMG Activity Ratio … Partial Lunge | อัตรา EMG ภายใต้แรงต้านทิศต่าง ๆ สำหรับเข่าเจ็บ |
| u036 | Foot Progression Angle and Stance Width … Forward Lunge | EMG ตามมุมเท้าและความกว้างท่ายืน · ความลึก/ลำตัวเป็นแค่ cue คุมการทดลอง |
| u039 | Automatic identification of events during the lunge | งานวิธีแบ่งช่วงการเคลื่อนไหวจากข้อมูล kinematic |
| u040 | Exhaustion of the Gluteus Medius … Knee Adduction Moment (thesis 123 หน้า) | ภาระ KAM/ข้อเข่าเสื่อมเมื่อก้นล้า · KAM ไม่ใช่กฎของ lunge |
| u042 | Muscle injury and pain … (thesis Jönhagen 2005) | เรื่องหลักคือ hamstring บาดเจ็บ วิ่ง นวด · บท lunge คืองานเดียวกับ u043 ที่ keep ไว้แล้ว |
| u046 | Foot Posture, Dorsiflexion ROM … Drop-Landing Task | งานกระโดดลง · lunge มีแค่เป็นชื่อการทดสอบข้อเท้า |

### push-up (8)
| id | ไฟล์ | เหตุผล |
|---|---|---|
| u061 | 10-week suspension and traditional push-up training | ผลของโปรแกรมฝึก 10 สัปดาห์ |
| u062 | A Rigid-Body Pendulum Model for Plyometric Push-Up | โมเดลคำนวณเวลาลอยตัว/กำลัง |
| u063 | Upper Body Muscle Activations … Various Type Of Push-up (abstract) | EMG ตามตำแหน่งมือ · abstract อื่นในหน้าไม่เกี่ยว |
| u064 | Narrow-base vs Shoulder-width Push-up in Gymnast | ผู้ทดสอบ 1 คน · ความกว้างมือไม่ใช่กฎ |
| u065 | Core Muscle Activity during Physical Fitness Exercises (SR 2020) | ตาราง EMG แกนกลางลำตัวของหลายท่า push-up เป็นแค่แถวเดียว |
| u066 | Medial-lateral position of hand … muscle synergy | ความกว้างมือไม่ใช่กฎ |
| u067 | ProQuestDocuments-2026-09-03 | abstract: การหมุนข้อมือ/แขนกับ EMG |
| u068 | Systematic Review of Core Muscle Activity (2013) | EMG กล้ามเนื้อแกนกลางลำตัวชั้นลึก ไม่มีเรื่องท่า push-up |

### squat (1)
| id | ไฟล์ | เหตุผล |
|---|---|---|
| u082 | Effect of hip adductor (Squat) — thesis 134 หน้า | EMG ของ VMO/VL ขณะบีบสะโพกเข้าระหว่างสควอท ไม่มีเรื่องท่าผิด |

## 3. keep ที่ไม่แน่ใจ (10) — ถ้าเห็นว่าควรตัดบอกได้

| id | ไฟล์ | ทำไมยัง keep |
|---|---|---|
| u009 | From Continuous sEMG Signals to Discrete Muscle State Tokens | งานหลักเป็นวิธี sEMG แต่ภาคผนวกนิยาม curl ผิด (งอไหล่มากจนแขนส่วนบนเลื่อนไปหน้า) |
| u014 | Effect of Shoulder Flexion Angles … Isometric Contraction | มุมไหล่กับการทำงานของ biceps เกี่ยวกับตำแหน่งแขนส่วนบนอยู่บ้าง |
| u018 | NASM: 9 Best Arm-Sculpting Exercises (URL) | เป็นเรื่องโปรแกรม hypertrophy มีประโยค full ROM ดีกว่า partial reps |
| u021 | ACE: Building Better Biceps (URL) | เทียบ EMG 8 ท่า มีคำแนะนำของผู้ฝึกบ้าง |
| u043 | Jönhagen 2009 Muscle activation … two lunge exercises | กลไกกล้ามเนื้อของ forward lunge 2 แบบ เนื้อหาท่าทางน้อย |
| u050 | mxn167Sp24 (dissertation AI motion capture) | งาน validation แต่บททบทวนพูดถึงมุมลำตัวและระยะก้าว |
| u071 | Effect of Position on the % Body Mass … Push-up | แรงที่รับตำแหน่งบนเทียบกับล่าง (ศอก ~90°) เกี่ยวกับความลึกทางอ้อม |
| u074 | NASM: Exercise Progressions and Regressions (URL) | การรักษาฟอร์มเมื่อปรับระดับท่า มี push-up regression |
| u100 | Werner2022 Knee Alignment Instructions (knee_valgus/) | งานกระโดดลง ไม่ใช่สควอท แต่ cue เรื่องแนวเข่าใช้ได้ |
| u077 | NASM: Lower Crossed Syndrome (URL) | **เปลี่ยนจาก drop ในรอบตรวจซ้ำ** มีสาเหตุ (นั่งนาน, hip flexor ตึง, ก้น/core อ่อน) และวิธีแก้ (ยืด hip flexor, กระตุ้นก้น, plank แบบเชิงกรานเอียงหลัง) ของหลังแอ่น ซึ่งเป็นส่วน "หลังแอ่น" ของ `hip_sag_or_pike` · แต่ไม่ได้เจาะจง push-up และอาจทำให้ curator ติด tag กว้างเกิน |

## 3.1 ตรวจซ้ำรายการ drop (2026-10-02, user ขอ)

คำถาม: ไฟล์ที่ drop มีเนื้อหาเรื่อง **สาเหตุที่ทำผิด วิธีแก้ หรือวิธีทำท่าที่ถูก** ของแต่ละท่าไหม

วิธี: อ่านข้อความทั้งไฟล์ (ตัดรายการอ้างอิงออก) ดึงทุกประโยคที่มีทั้งคำแนวแนะนำ/สาเหตุ (should, avoid, correct, proper, cue, cause, compensate, maintain, technique, prevent …) และคำเรื่องท่านั้น (เช่น elbow, trunk, depth, hip, plank, valgus) แล้วอ่านทุกประโยคที่ได้ · thesis u040 ข้อความที่ดึงได้คำติดกันเป็นพืด จึงค้นแบบ substring แทน

ผล:
- **เปลี่ยน 1 ไฟล์:** u077 → keep (ดู §3)
- **ยัง drop 27 ไฟล์** — ไม่มีส่วนที่อธิบายสาเหตุหรือวิธีแก้ท่าผิด กรณีที่เจอคำว่าท่าถูกมีแค่ **กติกาในการทดลอง** ไม่ใช่คำแนะนำของผู้เขียนถึงผู้ฝึก และ prompt ของ curator ก็สั่งไม่ให้ใส่ protocol ลง `specific_findings` อยู่แล้ว ("Do not put a study's own methodology/protocol setup … into specific_findings"):
  - u004 (inclined curl ให้แขนส่วนบนตั้งตรง), u008 (ใช้แผ่นล็อกศอกกันศอกแกว่งและให้ ROM ครบ), u010 (ห้ามแอ่นหลัง/งอไหล่ยกน้ำหนัก), u012 (ยืนพิงผนังกันตัวโยก)
  - u031, u036, u040 (lunge: เข่าหน้า ~90°, ลำตัวตั้ง, เข่าหลังไม่แตะพื้น / ลงถึงระดับข้อเท้า)
  - u061 (push-up: หลังตรง, ลึก 90° ถึงนับครั้ง)
- **u008 อ่านทั้งฉบับ (user ขอ):** ไม่มีการบรรยายท่าผิด สาเหตุ หรือวิธีแก้ของ curl · ส่วนที่พูดถึงท่ามีแค่ protocol (ยืนพิงผนัง, แผ่นล็อกศอกให้ ROM ครบและศอกไม่แกว่ง) · ช่วง discussion บอกว่า full ROM ที่แผ่นล็อกบังคับ *อาจทำให้กล้ามเนื้อเสียหายมากขึ้น* ถ้าตัดออกมาเป็น item จะอ่านเหมือนค้านการทำ full ROM ซึ่งตรงข้ามกับ feedback ของ `partial_curl` · อาการ "เหยียดแขนไม่สุด" ในรายงานเป็นอาการบวมจาก rhabdomyolysis หลังออกกำลังกาย ไม่ใช่ท่าผิด → ยัง drop
- **ข้อสังเกต u082:** แนะนำให้ผู้ป่วยเข่าเจ็บสควอทแค่ ~60° ซึ่งขัดกับ feedback ของ `partial_squat` ถ้าเข้า KB จะกลายเป็นข้อมูลที่สนับสนุนการย่อตื้น จึงยัง drop
- ไฟล์ที่เหลือ (u000, u006, u007, u013, u017, u030, u033, u035, u039, u042, u046, u062–u068) ประโยคที่ได้เป็นวิธีการวัด ผล EMG ข้อจำกัดของงาน หรือคำแนะนำเรื่องโปรแกรม/การฟื้นฟูทั่วไป

## 4. ไฟล์ที่ซ้ำกัน — user ลบแล้ว (2026-10-02)

T2 ไม่ได้จับไว้เพราะไบต์ต่างกัน · user ลบฉบับที่ซ้ำออกจาก `data/` แล้ว และเอาออกจาก `prefilter_v6.json` (หน่วยลดจาก 104 เป็น 102)

| เก็บไว้ | ลบแล้ว | หมายเหตุ |
|---|---|---|
| `squat/Altered_Knee_and_Ankle_Kinemat.pdf` (u081) | `squat/knee_depth/Dill2014_AnkleDorsiflexion_SquatKinematics_JAthlTrain.pdf` | Dill et al. 2014 บทความเดียวกัน |
| `push-up/The_Biomechanics_of_the_Push_up.pdf` (u069) | `push-up/The_Biomechanics_of_the_Push_up_jonathan.pdf` | Contreras et al. ฉบับตีพิมพ์ vs accepted manuscript |

## 5. `general/feedback_and_cueing/` (4) — user ตัดสิน 2026-10-02: ใช้ทำ prompt (P5) อย่างเดียว ไม่เข้า KB

ใส่เป็น `drop` ใน `prefilter_v6.json` (เหตุผลขึ้นต้นว่า "used only for prompt design (P5)") · Claude อ่านทั้ง 4 ไฟล์ก่อนตัดสิน:

| ไฟล์ | เรื่องหลัก | เนื้อหาที่ตรงกับกฎ |
|---|---|---|
| Lincoln2023 | ลำดับฝึก movement pattern + cue | น้อย: push-up "rigid, plank-like form" · cue box squat แก้ส้นเท้าลอย (ไม่ใช่กฎ) |
| Neumann2019 | external vs internal focus (แรง, EMG) | ไม่มี |
| Smith2020 | วิธีสอน + ประเภท feedback | น้อยแต่ตรง: มองพื้น → ลำตัวโน้มหน้า ("eyes forward") · เข่าออกเล็กน้อยตอนลุก · curl "elbows at the ribs" |
| Stien2022 | feedback แบบพูด vs เทคโนโลยี ใน back squat | น้อยมาก: ตาราง cue (ดันสองเท้าเท่ากัน, เกร็ง core, เข่าหมุนออกเล็กน้อย) |

เหตุผลที่ไม่ curate: ได้ item ที่ตรงกฎแค่ไม่กี่ประโยค (บาง cue มีในแหล่งอื่นที่ keep แล้ว) แลกกับความเสี่ยงที่คำแนะนำเชิงการสอนจะถูกจัดเข้า pool ของท่า

## 6. ข้อความสำหรับรายงาน

ก่อน curate มีขั้นคัดเอกสารทั้งไฟล์โดย LLM (Claude) จาก 102 หน่วย (PDF 85, URL 17) ตัดออก 27 หน่วย ด้วยเกณฑ์ว่าไม่มีเนื้อหาเกี่ยวกับท่าทางของ 4 ท่าที่ใช้กับกฎข้อใดข้อหนึ่งได้ (ไม่แน่ใจให้เก็บ) เหตุผลหลักคือวัดแค่การทำงานของกล้ามเนื้อหรือผลของโปรแกรม (n) ศึกษาตัวแปรที่ไม่ใช่กฎของระบบ (n) และเป็นงานวิธีวัดหรือผลทางคลินิก (n) — เติมตัวเลขหลัง user ตรวจเสร็จ · แยกอีก 4 ไฟล์เรื่องวิธีสอน/feedback ไว้ใช้ออกแบบ prompt ไม่เข้า KB (user ตัดสิน)

## 7. เอกสารใหม่รอบ 2026-10-19 (ให้ user ตรวจ)

user หาเอกสารเพิ่ม (ไฟล์ลงวันที่ 2026-10-18) · เกณฑ์และวิธีอ่านเหมือน §1 และ §3.1 · เพิ่ม 5 entry ใน `prefilter_v6.json` (รวม 107) · ไม่ได้เรียก API ที่เสียเงิน

| ไฟล์ | ผล | เหตุผลสั้น ๆ |
|---|---|---|
| `push-up/Biomechanical evaluation of the push-up … various starting points.pdf` (Topalidou 2012) | **keep (ไม่แน่ใจ)** | ส่วนใหญ่เป็น EMG/แรงตามตำแหน่งมือ แต่บทนำนิยามท่ามาตรฐาน (ลำตัวตรงไหล่ถึงเข่า ลงจนศอก ~90° อกลงใกล้พื้นที่สุด) และวัดการเอียงของลำตัว → principle ของ `partial_pushup` และ `hip_sag_or_pike` · ไม่มี mistake/consequence · ~7 window |
| `push-up/urls.txt` → BOXROX "3 push-up benchmarks …" (URL ใหม่) | **keep (ไม่แน่ใจ)** | ส่วน "strict rep standard": ไม่นับครั้งที่ลงไม่สุด, อกลงใกล้พื้น, สะโพกไม่ตก/ไม่โด่ง, เมื่อล้าต้องเกร็งท้อง/ก้นไม่ให้หลังล่างแอ่น → ระดับ **mistake** ของ `partial_pushup` / `hip_sag_or_pike` ซึ่งเป็นช่องที่ขาด · แหล่งเป็นนิตยสาร ไม่ใช่องค์กรวิชาชีพ · ~2 window · **curate ตรง ๆ ไม่ได้** ดูหมายเหตุด้านล่าง |
| `lunge/Knee joint biomechanics … tibial angles … finite element` (Gao 2026) | drop | ตัวแปรคือมุมหน้าแข้ง (เข่าเคลื่อนไปหน้า) ไม่ใช่กฎ · FE จากคนเดียว · เรียก 60° ว่า "ลึก" และ 90° ว่า "ตื้น" แต่สรุปว่า "ลันจ์ลึก + ถือน้ำหนัก" กดหมอนรองเข่าจากเงื่อนไข 90° → item จะขัดกันเองและอ่านเหมือนเตือนไม่ให้ลงถึง 90° (ขัด `shallow_lunge` แบบเดียวกับ u082) |
| `lunge/Biomechanical Analyses of Bodyweight Unilateral … ` (Chapman 2018) | drop | เป็น **PREVIEW** ของวิทยานิพนธ์ ProQuest จบที่หน้า 8 กลางบททบทวน ไม่มีผล/อภิปราย · เรื่องหลักคือ joint moment ข้ามท่า · ท่าทางมีแค่ประโยคนิยามจุดต่ำสุดของลันจ์ (เข่าหลังเกือบแตะพื้น/เข่าหน้า ~90°) ซึ่งแหล่งที่ keep มีแล้ว |
| `push-up/Kinetic analysis of push-up exercises … systematic review` (Dhahbi 2018) | drop | %BW, แรงสูงสุด, moment ศอก, แรงกระแทกของ 46 แบบ (ความกว้าง/การหมุนมือ, ความสูง, เข่า, ความเร็ว, plyometric) · กลุ่ม "depth/ROM" หมายถึงตำแหน่งมือ ไม่ใช่ความลึก · ท่าที่ถูกเป็น protocol ในตาราง · ประโยคที่ตรงกฎมีแค่ ~2 ประโยค (หลังล่างคงท่า, แรงมากขึ้นเมื่อศอกงอ ซึ่ง u071 มีแล้ว) แลกกับ 41 หน้า (~19 window) |

**ไม่ใช่เอกสารใหม่ (ไม่ใส่ใน prefilter):** — 2 ไฟล์ที่ซ้ำ user ให้ลบแล้ว (2026-10-19)
- `lunge/Effects_of_Loading_Positions_…_Tra.pdf` — **ไบต์เหมือนกันทุกไบต์** กับฉบับที่ curate แล้วในรอบ 2a (ตอนนี้อยู่ `data/picked/lunge/`)
- `lunge/Altered Knee and Ankle Kinematics During Squatting … Lunge …` — Dill 2014 เป็นสำเนาที่ 3 ของบทความเดียวกับ `squat/Altered_Knee_and_Ankle_Kinemat.pdf` (u081, ฉบับที่ 2 user ลบไปแล้วใน §4) · เป็นงานสควอท คำว่า lunge เป็นแค่ชื่อการทดสอบข้อเท้า
- `push-up/push-up weakness pectoralis triceps … - Google Scholar.html` (+ โฟลเดอร์ `_files`) — หน้าผลค้นหา ไม่ใช่เอกสาร · ส่วนใหญ่เรื่องสะบัก/การฟื้นฟูนักกีฬาขว้าง (ไม่ใช่กฎ) · รายการที่อาจตามต่อ: Bell 2018 "Muscular Fatigue Influences Motor Synergies During Push-ups" (ถ้าพูดถึงการเสียท่าแพลงก์เมื่อล้า จะเข้า `hip_sag_or_pike`) · curator ไม่อ่าน `.html` จึงไม่กระทบการรัน

**หมายเหตุ URL BOXROX — ติด 2 เรื่องถ้าจะ curate:**
1. `trafilatura.fetch_url` (ที่ curator ใช้) ได้หน้าว่าง เว็บต้องการ User-Agent แบบเบราว์เซอร์ (ดึงด้วย curl + UA ได้ 11k ตัวอักษร)
2. `push-up/urls.txt` มีผล curate แล้ว (`curated_data_v6/push-up/urls_curated_detailed.json`) curator จึงข้ามทั้งไฟล์
→ ทางที่ไม่ต้องแก้ curator: บันทึกเนื้อหาบทความเป็น `.txt` ใน `data/push-up/` (curator อ่าน `.txt` ด้วย TextLoader) แล้วใส่ไฟล์นั้นใน batch รอบถัดไป

**ผลต่อ data gap:** ทั้ง 2 ตัวที่ keep เป็นของ push-up · BOXROX เป็นแหล่งเดียวในรอบนี้ที่น่าจะให้ `partial_pushup` ระดับ mistake · ไม่มีเอกสารใหม่ที่ช่วย `straight_back_leg` หรือ `shallow_lunge`

### 7.1 รอบที่ 2 วันเดียวกัน (2026-10-19)

เพิ่ม 2 entry (รวม 109) · ทั้งคู่เป็น lunge และ **keep** · ไม่ช่วยกฎที่ขาด (ขาหลังมีแค่ protocol "เข่าหลังเกือบแตะพื้น")

| ไฟล์ | ผล | เหตุผลสั้น ๆ |
|---|---|---|
| `lunge/Patellofemoral Joint Loading in Forward Lunge With Step Length and Height Variations.pdf` (Escamilla 2022, JAB) | **keep** | ก้าวสั้น → เข่าหน้าเลยปลายเท้าตั้งแต่ ~60° → แรง/ความเค้นที่ข้อต่อสะบ้าสูงขึ้นช่วงงอลึก · ผู้เขียนสรุปว่าเข่าเลยปลายเท้า "อาจเป็นอันตรายและควรเลี่ยง" → ตรง card `excessive_front_knee_flexion` (ก้าวสั้น + แรงที่เข่า) · ระวัง: ลำดับฟื้นฟู PFPS เริ่มจาก "mini lunge" 0–40° อาจถูกติด `shallow_lunge` (บริบทฟื้นฟู และจบที่ลงเต็ม) · ไม่ใช่ฉบับเดียวกับ Escamilla2022 IJSPT ใน `front_knee_too_deep/` |
| `lunge/Biomechanical effects of exercise fatigue on the lower limbs of men during the forward lunge.pdf` (Gao 2023) | **keep** | เมื่อล้า เข่าหน้างอมากขึ้นและเคลื่อนไปหน้า ลำตัวโยก/โน้มไปหน้าเพราะคุมลำตัวยาก → ระดับ **สาเหตุ** ของ `excessive_front_knee_flexion` และ `forward_trunk_lean` · เรื่องลำตัวอ้างจากงานอื่น (ไม่ได้วัดเอง) · ภาษาอังกฤษผิดบางจุด |
| `lunge/THE UNDERVALUED LUNGE.pdf` | ซ้ำ → **ลบแล้ว** | ไบต์เหมือน `ptq-4.4.9-the-undervalued-lunge.pdf` ที่ curate แล้ว |

**ย้ายไฟล์ที่ตรวจแล้วไป `data/checked/` (user ขอ):** ทุกไฟล์ที่มี entry ใน prefilter แต่ยังไม่ curate + `push-up/urls.txt` (เหลือแค่ URL BOXROX) + หน้า Google Scholar · ดูโครงโฟลเดอร์ใน [t3_curation_status.md §0](../progress/t3_curation_status.md)

## 8. เอกสารใหม่รอบ 2026-10-20 (ให้ user ตรวจ)

6 ไฟล์ใหม่ใน `data/` · วิธีอ่านเหมือน §3.1 (ข้อความทั้งไฟล์ ตัดรายการอ้างอิง ดึงประโยคที่มีคำแนะนำ/สาเหตุ + คำเรื่องท่า แล้วอ่านทุกประโยค) · เพิ่ม 6 entry ใน `prefilter_v6.json` (รวม 116) · keep 2 · drop 4 · ไม่ได้เรียก API ที่เสียเงิน · ยังไม่ได้ย้ายไฟล์

| ไฟล์ | ผล | เหตุผลสั้น ๆ |
|---|---|---|
| `lunge/Escamilla2025_ForwardLunge_StepLength_JFMK.pdf` | drop | EMG ขาหน้าตามก้าวยาว/สั้น และมี/ไม่มีการก้าว · ท่าทางมีแค่ protocol · ประโยค "ก้าวสั้น → เข่าเลยปลายเท้า 8–10 ซม." เป็นการอ้างงานอื่น และ Escamilla 2022 JAB ที่ curate แล้วมีประโยคเดียวกันพร้อมผลแรงที่ข้อต่อสะบ้า · คำแนะนำหลักคือ "เริ่มจากก้าวสั้นแล้วค่อยก้าวยาว" (ลำดับ EMG สำหรับฟื้นฟู) ซึ่งอ่านเหมือนสนับสนุนก้าวสั้น (ขัด `excessive_front_knee_flexion`) |
| `lunge/Neto2020_GluteusMaximusActivation_SR_JSSM.pdf` | drop | SR จัดอันดับ EMG กล้ามก้นข้ามท่า · lunge เป็นแถวเดียวในตาราง · เนื้อหาท่าทางมีแค่ความลึกของสควอท ซึ่งผู้เขียนบอกเองว่าผลขัดกัน (มีงานที่ partial squat กระตุ้นก้นมากกว่า → ขัด `partial_squat`) และถ้าอยู่ในโฟลเดอร์ lunge จะโดน folder mismatch |
| `push-up/partial_pushup/MartinezCava2019_BenchPressROM_LoadVelocity_JSSM.pdf` | drop | **bench press ไม่ใช่ push-up** (ไม่มีคำว่า push-up เลย) · ความเร็ว-น้ำหนัก, 1RM, sticking region ที่ ROM 3 ระดับ · ไม่มีเรื่องความลึกของ push-up หรือผลเสีย |
| `push-up/partial_pushup/Mendonca2021_PartialVsFullROM_BenchPress_PLoSOne.pdf` | drop | bench press ของนักกีฬาพาราลิมปิก · full ROM กระตุ้นอกมากกว่า แต่**ข้อสรุปของผู้เขียนเชียร์ partial ROM** ("ยกหนักได้มากขึ้น เสียแรงน้อยกว่า") → ถ้าเป็น item ของ push-up จะขัด `partial_pushup` (แบบเดียวกับ u082) |
| `general/range_of_motion/Hammami2025_FullVsHalfSquat_JFMK.pdf` | **keep** | ฝึก full vs half squat 8 สัปดาห์ (volume เท่ากัน ต่างแค่ความลึก) · เป็น back squat ล้วน · ระดับ consequence/principle ของ `partial_squat`: full squat ได้ความเร็วและลดไขมันมากกว่า, อ้างว่า half/quarter squat มีแรงที่เข่า/หลังและอาการปวดมากกว่า · ~9 window |
| `general/range_of_motion/KrauseNeto2025_GluteusMaximusHypertrophy_SR_FrontPhysiol.pdf` | **keep (ไม่แน่ใจ)** | meta-analysis การโตของกล้ามก้น · ส่วนใหญ่เป็น hip thrust / leg press / kneeling hip extension · ส่วนสควอท: ROM สำคัญ, สควอทถึงขนาน/เต็มทำให้ก้นโต แต่ลงแค่ ~90° (นับแบบงอเข่า) ไม่โต, "ถึงขนานก็พอ" → consequence ของ `partial_squat` · ~15 window |

**ข้อควรระวังของ 2 ไฟล์ที่ keep:** ทั้งคู่เรียกสควอทที่**งอเข่า 90°** ว่า "half squat" แต่ cue ของระบบคือ "ลงให้ถึง 90°" (มุมเข่า 90° ของระบบ = งอเข่า 90° พอดี) · generator อาจบอกผู้ใช้ว่า "90° ยังเป็น half squat ไม่พอ" · กฎยิงเมื่อมุม > 100° ทิศจึงยังถูก (ให้ลงลึกขึ้น) แต่ตัวเลขอาจสับสน → ตรวจตอน generate เหมือน §6.2 ของ t3_curation_status · Hammami ยังบอกว่า hypertrophy เท่ากัน และ "half squat อาจเหมาะกับมือใหม่เพราะปลอดภัยกว่า" (ขัดกับประโยคอื่นในฉบับเดียวกัน)

### 8.1 ย้ายจาก `general/` ไปโฟลเดอร์ท่าได้ไหม

ผลต่างของการวางไฟล์ (ดู `curator.py`):
- **`general/`**: curator เห็นกฎทั้ง 12 ข้อ แล้ว `route_general_window()` ส่ง item ไปท่าตาม tag หรือ `exercise_type` ของ window · item ที่ไม่ระบุท่าค้างใน `curated_data_v6/general/` ซึ่ง retrieval ยังไม่ดึง (= ตกไปโดยไม่เสียหาย) · ไม่มีการเช็ค folder mismatch
- **`<ท่า>/`**: curator เห็นแค่กฎของท่านั้น (prompt สั้นกว่า เลือก tag แม่นกว่า) · window ที่เป็นท่าอื่นถูกตัดด้วย folder mismatch · แต่ window ที่ LLM ใส่ `exercise_type = Generic` **ผ่านเข้า pool ของท่านั้นทั้งหมด** (ไม่มี tag)

| ไฟล์ | แนะนำ | เหตุผล |
|---|---|---|
| Hammami 2025 | **ย้ายไป `data/squat/knee_depth/`** | สควอทอย่างเดียว ผลลัพธ์แทบเหมือนเดิม (window เกือบทุกอันจะ route ไป squat อยู่แล้ว) แต่ได้ prompt 4 กฎของ squat และมี folder mismatch ช่วยกรอง · ชื่อโฟลเดอร์ย่อยไม่มีผลกับ curator (ใช้แค่ชั้นแรก) |
| Krause Neto 2025 | **เก็บไว้ใน `general/`** | เนื้อหาสควอทเป็นส่วนน้อย · ถ้าย้ายไป `squat/` window ภาพรวม meta-analysis (effect size, ลักษณะงานวิจัย) ที่ LLM ใส่ Generic จะเข้า pool ของ squat โดยไม่มี tag · ใน `general/` มีแค่ item เรื่องความลึกที่ได้ tag `partial_squat` หรือ window ที่ระบุว่าเป็น squat เท่านั้นที่ไป squat |
| Bonilla 2022 (`checked/general/injury/`, keep ตั้งแต่ §1) | เก็บไว้ใน `general/` | หลายท่า (curl 12 ครั้ง · deadlift 8 · squat 5 · bench 5 · lunge 2) |
| manual (`picked/general/`) | ไม่ย้าย | curate และ route แล้ว (squat 44 · lunge 23 · bicep-curl 8 item, §6.6 ของ t3) · ย้ายแล้ว id เปลี่ยนและต้อง curate ใหม่ |
| `feedback_and_cueing/` 4 ไฟล์ | ไม่เกี่ยว | ไม่เข้า KB (§5) |

ถ้าย้าย Hammami ต้องแก้ `path` ของ entry ให้เป็น `data/squat/knee_depth/Hammami2025_FullVsHalfSquat_JFMK.pdf` พร้อมกัน (path คือ id) · ทำก่อน curate เท่านั้น

**ผลต่อ data gap:** ไม่มีไฟล์ใดในรอบนี้ช่วย 3 กฎที่ยังขาด (`partial_pushup`, `shallow_lunge`, `straight_back_leg`) · 2 ไฟล์ใน `partial_pushup/` เป็น bench press · ที่ keep ช่วย `partial_squat` ซึ่งผ่านเกณฑ์แล้ว (consequence 7 → น่าจะเพิ่ม) · ถ้า curate จะได้ `model_version` = 3.6 เหมือนรอบ 3 (เรื่องเก็บไว้ vs curate ใหม่ใน t3 §5.2 ยังค้าง)

## 9. เอกสาร lunge ใหม่รอบ 2026-10-21 (ให้ user ตรวจ)

6 ไฟล์ใหม่ใน `data/lunge/` · เทียบ md5 กับไฟล์ใน `checked/` และ `picked/` ก่อน → **4 ไฟล์ซ้ำแบบไบต์เหมือนกัน** · อีก 2 ไฟล์อ่านทั้งฉบับ (ตัดรายการอ้างอิง) · เพิ่ม 2 entry ใน `prefilter_v6.json` (รวม 118) · keep 1 · drop 1 · ไม่ได้เรียก API ที่เสียเงิน · ยังไม่ได้ย้ายหรือลบไฟล์

**ไฟล์ซ้ำ (ไม่ใส่ entry) — user ลบแล้ว 2026-10-21** (ตรวจ md5 อีกรอบก่อนลบ):

| ไฟล์ใหม่ | ซ้ำกับ | สถานะของต้นฉบับ |
|---|---|---|
| `lunge/Effects_of_step_lengths_on_biomechanical_character.pdf` | `checked/lunge/Song2023_StepLength_SplitSquat_FrontBioeng.pdf` | keep (ยังไม่ curate) |
| `lunge/Front Bioeng Biotechnol step length ใน split squat.pdf` | ไฟล์เดียวกับแถวบน | 〃 |
| `lunge/Patellofemoral Joint Loading During the Performance of the Forward and Side Lunge with Step Height Variations.pdf` | `checked/lunge/front_knee_too_deep/Escamilla2022_PatellofemoralLoad_ForwardSideLunge_IJSPT.pdf` | keep (ยังไม่ curate) |
| `lunge/Towards evidence based strength training … split squats.pdf` | `picked/lunge/Schellenberg2017_SplitSquat_StepLengthTibialAngle_BMCSSMR.pdf` | **curate แล้ว** |

ถ้าปล่อยไว้แล้ว curate ด้วย id ใหม่จะได้ item ซ้ำใน KB (Schellenberg ซ้ำทันที · Song/Escamilla ซ้ำถ้าวันหลัง curate ฉบับใน `checked/`)

**ไฟล์ใหม่จริง:**

| ไฟล์ | ผล | เหตุผลสั้น ๆ |
|---|---|---|
| `lunge/Influence of Different Load Conditions … Lunge Squat in Novice Men.pdf` (Gao 2022) | **keep (ไม่แน่ใจ)** | ตัวแปรคือชนิดน้ำหนัก (ดัมเบล/บาร์เบล/เสื้อถ่วง) ไม่ใช่กฎ · เนื้อหาท่าทางส่วนใหญ่**ซ้ำกับ Gao 2025 ที่ curate แล้ว** (กลุ่มวิจัยเดียวกัน: มือใหม่โน้มตัว → แรงเฉือนที่เข่า, Farrokhi โน้มตัว → สะโพกทำงานมาก, ดัมเบลเหมาะกับมือใหม่) · **ของใหม่ 1 ประโยค:** "ถ้างอเข่าได้น้อย แสดงว่าอาจมีกล้าม quadriceps อ่อนหรือข้อเท้ากระดกได้จำกัด" = สาเหตุของ `shallow_lunge` ซึ่ง KB ยังไม่มีเลย (item `shallow_lunge` 21 ชิ้นบอกมุมที่ควรลง ผลของการลงตื้น หรือว่ามือใหม่ลงตื้นกว่า แต่ไม่มีชิ้นไหนบอกว่าลงตื้น**เพราะอะไร**) · ~10 window |
| `lunge/IsTheRearFootElevatedSplitSquatUnilateralAM-HELME.pdf` (Helme 2020) | drop | RFESS: ขาหน้าออกแรง ~84% ขาหลังแค่น้ำหนักขาตัวเอง → จัดเป็นท่าขาเดียว · ไม่มีท่าผิด สาเหตุ หรือวิธีแก้ · ท่าทางมีแค่ protocol · ระยะลงลดลงเล็กน้อยเมื่อน้ำหนักมากขึ้น แต่ทุกครั้งยังผ่านความลึกขั้นต่ำ จึงไม่ใช่เรื่องลงตื้น · ขาหลังเป็นเรื่องสัดส่วนแรง ไม่ใช่เข่าหลังงอ/เหยียด (`straight_back_leg`) และ Arakawa/Jaeggi ที่ curate แล้วครอบคลุมแรงขาหลังอยู่แล้ว |

**ข้อควรระวังของ Gao 2022 ถ้า curate:**
- อ้าง Escamilla ว่า "ระวังการ lunge **ก้าวยาว** เพื่อลดแรงที่สะบ้า" ซึ่งกลับทิศกับงาน Escamilla ที่ curate แล้ว (ก้าว**สั้น**ทำให้แรงสะบ้าสูง) และขัด card ของ `excessive_front_knee_flexion` · หลัง curate ให้หา item นี้แล้วถอด tag หรือลบ (ทาง B/C ใน t3 §6 ข้อ 7)
- คำแนะนำเรื่องอุปกรณ์ (เสื้อถ่วงสำหรับคนปวดเข่า, ดัมเบลสำหรับมือใหม่) ไม่ตรงกฎ ควรได้ item ไม่ติด tag
- 4 หน้ามีข้อความชั้น "FOR PEER REVIEW" ซ้ำ → บาง window มีข้อความซ้ำ อาจได้ item ซ้ำกันเอง
- ประโยคสาเหตุเป็นการอ้างงานอื่น [44] และเขียนในบริบทข้อเท้า curator อาจไม่ติด tag `shallow_lunge`

**ผลต่อ data gap:** Gao 2022 อาจได้ `shallow_lunge` mistake (สาเหตุ) เพิ่ม 1 ชิ้น · ไม่มีไฟล์ไหนช่วย `straight_back_leg` หรือ `partial_pushup`

### 9.1 ไล่ดูไฟล์ `keep` ที่ยังไม่ curate ทั้งหมด เทียบกับ 3 กฎที่ขาด (user ขอ, 2026-10-21)

coverage ตอนนี้ (`tag_coverage.py`, mistake/consequence/principle/finding): `partial_pushup` 3/1/7/2 · `shallow_lunge` 3/1/10/7 · `straight_back_leg` 0/0/6/0 · **ทั้ง 3 กฎขาด mistake และ consequence** (principle ผ่านเกณฑ์แล้ว)

วิธี: ไฟล์ `keep` ที่ยังไม่ curate มี PDF 25 ไฟล์ (รวม Gao 2022) + URL BOXROX (URL อื่นอยู่ใน `picked/` แล้ว) · ตัดรายการอ้างอิง แปลง ligature (ﬂ/ﬁ) · นับคำ lunge/split squat และ push-up ทุกไฟล์ · ดึงประโยคตามกฎ (ความลึกเข่าหน้า / เข่าหรือขาหลัง / ความลึก push-up) + ประโยคสาเหตุตาม card (อ่อนแรง, ตึง, ทรงตัว, มือใหม่, ล้า) แล้วอ่านทุกประโยค · เทียบกับ includes/excludes ของ card

| กฎ | ไฟล์ที่มีเนื้อหา | ได้อะไร | ข้อควรระวัง |
|---|---|---|---|
| `partial_pushup` | **ไม่มี** · PDF ทั้ง 25 ไม่มีคำว่า push-up เลย (GarciaJaen2020 เป็นแพลงก์) | — | **แก้ไข:** ตอนแรกนับ BOXROX เป็นตัวช่วย แต่เนื้อหาถูก curate ไปแล้วในรอบ 3 ในชื่อ `push-up/BOXROX_PushUpBenchmarks.txt` (`partial_pushup` mistake 1 + principle 1 รวมใน 3/1/7/2 แล้ว) · entry URL ใน `checked/push-up/urls.txt` เหลือไว้เป็นหลักฐานเท่านั้น ไม่ต้อง curate ซ้ำ |
| `shallow_lunge` | Gao 2022 | mistake 1 (สาเหตุ: quad อ่อน / ข้อเท้ากระดกได้จำกัด) | ดู §9 |
| | Song2023 | ก้าวยาวขึ้น → เข่าหน้างอน้อยลง และผู้เขียนบอกว่าที่ก้าว 100% "ลงไม่ลึกพอ" | **ไม่ใช่ลันจ์ตื้นตามกฎ:** peak knee flexion 104° → 95° (= มุมภายใน 76°–85°) ลึกกว่า 90° ทุกเงื่อนไข ส่วน "ลงไม่ลึกพอ" พูดถึงสะโพก · ระยะก้าวขึ้นกับ oq1 ของ card ที่ยังเปิดอยู่ · ผู้เขียนแนะนำให้มือใหม่ก้าว ≥100% LL |
| | mxn167Sp24 | principle ("ต้นขาหน้าขนานพื้น") | principle ผ่านเกณฑ์แล้ว |
| | Escamilla2022 IJSPT, Comfort2015 | — | **ขัดกฎ:** "mini lunge 0–40° เหมาะกับช่วงแรกของ PFPS rehab" · "แรงที่ข้อเข่าเพิ่มตามการงอเข่า → forward lunge ไม่เหมาะกับคนข้อเข่าเสื่อม" (เป็น consequence ของ `excessive_front_knee_flexion` ได้ แต่อ่านเหมือนสนับสนุนการลงตื้น) |
| `straight_back_leg` | mxn167Sp24 | principle 2 ("ผู้ฝึกมักสอนให้หยุดก่อนเข่าหลังแตะพื้น", "ก้าวพอดี ๆ เข่าหลังจบที่ ~90°") | ไฟล์อื่นมีแค่ protocol (Farrokhi, AygunPolat, Gao 2022) หรือแรงที่ขาหลัง (Song2023) · **ไม่มีไฟล์ไหนบอกว่าขาหลังเหยียดเป็นท่าผิด สาเหตุ หรือผลเสีย** |

ไฟล์ที่เหลือ (bicep-curl 4, squat 9, Bonilla2022, Hammami2025, KrauseNeto2025, Jönhagen2009, AygunPolat2025) ไม่มีเนื้อหาของ 3 กฎนี้ · Dill 2014 มีคำว่า lunge 15 ครั้ง แต่เป็นชื่อการทดสอบข้อเท้า (weight-bearing lunge) ส่วนผลเป็นของสควอท

**สรุป:** curate ไฟล์ `keep` ทั้งหมดได้เพิ่มสูงสุดแค่ `shallow_lunge` mistake +1 (Gao 2022) · user เลือกเตรียม Gao 2022 เป็น batch `round4` แล้ว (ย้ายไป `checked/lunge/`, ยังไม่รัน) · **consequence ไม่ได้เพิ่มเลยทั้ง 3 กฎ** และไม่มีกฎไหนถึงเกณฑ์ 5 → ยังเป็น data gap · ถ้าจะปิด gap ต้องหาเอกสารใหม่ที่เล็งท่าผิดโดยตรง (บทความ coaching / textbook ที่มีหัวข้อ "common mistakes" ของ lunge และ push-up) มากกว่างาน biomechanics ที่คุม protocol ไว้แล้ว

## 10. เอกสารใหม่รอบ 2026-10-24 (ให้ user ตรวจ)

user หาเอกสารมาเพื่อปิด data gap · 8 ไฟล์ใหม่ (lunge 5, push-up 3) · เทียบ md5 กับทุกไฟล์ใน `data/` ก่อน → **ซ้ำแบบไบต์เหมือนกัน 1 ไฟล์** · อีก 7 ไฟล์อ่านทั้งฉบับ (ตัดรายการอ้างอิง) ดึงประโยคเรื่องความลึก/เข่าหลัง/ลำตัว/คำแนะนำ/สาเหตุ แล้วอ่านทุกประโยค · ค้นชื่อผู้เขียน/ชื่อเรื่องใน `curated_data_v6/` แล้ว ไม่มีฉบับไหนเป็นเปเปอร์เดียวกับที่ curate แล้ว · เพิ่ม 7 entry ใน `prefilter_v6.json` (รวม 125) · keep 2 · drop 5 · ไม่ได้เรียก API ที่เสียเงิน · ยังไม่ได้ย้ายหรือลบไฟล์

**user ตัดสิน 2026-10-24:** ลบไฟล์ซ้ำ Kritz แล้ว (ตรวจ md5 อีกรอบก่อนลบ) · Riemann 2012 + Common Mistakes เข้า batch `round4` คู่กับ Gao 2022 และย้ายไป `checked/lunge/` แล้ว (ยังไม่รัน) · ไฟล์ drop 5 ไฟล์ยังอยู่ใน `data/<ท่า>/`

**ไฟล์ซ้ำ (ไม่ใส่ entry) — user ลบแล้ว 2026-10-24:**

| ไฟล์ใหม่ | ซ้ำกับ | สถานะของต้นฉบับ |
|---|---|---|
| `lunge/Using the bodyweight lunge to screen an athletes’ lunge pattern.pdf` | `picked/lunge/KritzCroninHume2009BodyweightlungeSCJ.pdf` | **curate แล้ว** (ถ้าปล่อยไว้แล้ว curate จะได้ item ซ้ำทันที) |

**ไฟล์ใหม่จริง:**

| ไฟล์ | ผล | เหตุผลสั้น ๆ |
|---|---|---|
| `lunge/Biomechanical Analysis of the Anterior Lunge During 4 External-Load Conditions.pdf` (Riemann 2012, JAT) | **keep** | ส่วนใหญ่เป็น kinetics สะโพก/เข่า/ข้อเท้าเมื่อถือน้ำหนัก 0–50% BW (ไม่ใช่กฎ) · **ของใหม่ 1 ย่อหน้า:** เมื่อถือ 50% BW ผู้ทดสอบลงตื้นกว่า (จุดศูนย์ถ่วงสูงกว่า 2 ซม.) ผู้เขียนแนะนำให้ "คอยดูความลึกและบอก cue เมื่อใช้น้ำหนักมาก เพื่อให้ลงครบช่วง" = **สาเหตุ (น้ำหนักมาก) + วิธีแก้ (cue ความลึก)** ของ `shallow_lunge` · เรื่องลำตัวอ้าง Farrokhi (มีใน KB แล้ว) · ไม่มีเรื่องเข่าหลัง · ~8 window |
| `lunge/Common Mistakes to Avoid When Performing a Lunge in Ladera Ranch.pdf` | **keep (ไม่แน่ใจ)** | บทความเว็บของธุรกิจฟิตเนสท้องถิ่น (ไม่มีผู้เขียน ไม่มีอ้างอิง ยัดคำ "lunge in Ladera Ranch") · มี mistake/consequence/วิธีแก้ของ `forward_trunk_lean` (มีมากอยู่แล้ว) · เข่าเลยปลายเท้า → เครียดที่เข่า (oq1 แต่ไม่โยงกับงอมากเกิน) · ก้าวสั้น → เข่าพุ่งไปหน้า (oq2) · "ก้าวให้เข่า**ทั้งสองข้าง** ~90° ที่จุดต่ำสุด" = principle ของ `shallow_lunge` และ `straight_back_leg` (principle ผ่านเกณฑ์แล้วทั้งคู่) · **ไม่มี** mistake/consequence ของลันจ์ตื้นหรือขาหลังเหยียด · ~1 window ราคาถูก |
| `lunge/Hip-Muscle Activation during the Lunge, Single-Leg Squat, and Step-Up-and-Over Exercises.pdf` (Boudreau 2009, JSR) | drop | EMG กล้ามสะโพก 3 ท่าเพื่อเรียงลำดับฟื้นฟู (step-up → lunge → single-leg squat) · ท่าลันจ์มีแค่ protocol (ก้าว 100% ความยาวขา) · ประโยคเรื่องความลึกเป็นของ single-leg squat |
| `lunge/IMPROVED MUSCLE ACTIVATION … BODY WEIGHT LUNGE … BACK SQUAT.pdf` (Dwelly, conference 4 หน้า, n=8) | drop | EMG ลันจ์ vs สควอท 3 ความลึก · ลันจ์เป็นเงื่อนไขเดียว ไม่มีความลึกหรือท่าที่ต่างกัน · ผลความลึกของสควอท (90° กระตุ้นมากกว่า 60°/30°) เป็น consequence ของ `partial_squat` แต่อยู่โฟลเดอร์ lunge จะโดน folder mismatch และ `partial_squat` ผ่านเกณฑ์แล้ว |
| `push-up/COMPARATIVE ANALYSIS OF ELBOW JOINT LOADING IN PUSH-UP AND BENCH-PRESS.pdf` (Chou 2011) | drop | แรงที่ศอก push-up vs bench press · ศอกงอสูงสุด 93° ทั้งคู่ (protocol) · **ขัดกฎ:** อธิบายว่าแรงที่ศอกสูงสุดช่วง 90° ถึงจุดต่ำสุด และสรุปว่า bench press ดีกว่า → item ของ push-up จะอ่านเหมือน "ลงลึกทำให้ศอกรับแรงมาก" (ขัด `partial_pushup` แบบ u082) · ไม่มีเรื่องแนวลำตัว |
| `push-up/Force transmission through the wrist … hyperextended and a neutral wrist.pdf` (Polovinets 2017, JHT) | drop | ทิศแรงผ่านข้อมือ วางฝ่ามือ vs กำหมัด · ตำแหน่งมือ/ข้อมือเป็น "ไม่นับ" ของทั้ง 2 card push-up · ไม่มีเรื่องความลึกหรือแนวลำตัว |
| `push-up/Optimal activation ratio of the scapular muscles … systematic review.pdf` (Mendez-Rebolledo 2021) | drop | อัตราส่วน EMG กล้ามสะบัก (สะบักเป็น "ไม่นับ") · **กับดัก:** "Half Push Up" ใน review นี้คือ**วิดพื้นมือบนกล่อง 30 ซม. ลำตัวเอียง 45°** ไม่ใช่วิดพื้นครึ่งช่วง และ review ให้เป็น "optimal" → ถ้า curate อาจถูกติด `partial_pushup` แล้วอ่านเหมือนแนะนำให้วิดพื้นครึ่งท่า |

**ข้อควรระวังของ Riemann 2012 ถ้า curate:**
- ลงตื้นแค่ 2 ซม. และมุมเข่าหน้าไม่ต่างอย่างมีนัยสำคัญ (งอ 96° → 92° = มุมภายใน ~84°–88°) ทุกเงื่อนไขยังลึกกว่า 90° ไม่มีเงื่อนไขไหนเป็นลันจ์ตื้นตามกฎ (> 105°) · ปัญหาเดียวกับ Song2023 ใน §9.1 · แต่ประโยคของผู้เขียนเป็นคำแนะนำเรื่องความลึกโดยตรง ซึ่ง card นับ (Recommendations on how deep a lunge should go)
- "น้ำหนักมาก" ไม่อยู่ในรายการสาเหตุของ card `shallow_lunge` (quad/ก้นอ่อน, hip flexor ตึง, กลัวเสียการทรงตัว) แต่ไม่ขัด · ถ้า curator ไม่ติด tag ให้ถือว่าถูกต้องได้
- "ถ้าเป้าหมายคือกล้ามเหยียดเข่า ควรเลือกท่าอื่น" และ "ลันจ์เป็นท่าที่สะโพกเด่น" ไม่ตรงกฎ ควรได้ item ไม่ติด tag

**ผลต่อ data gap** (coverage จาก §9.1: `partial_pushup` 3/1/7/2 · `shallow_lunge` 3/1/10/7 · `straight_back_leg` 0/0/6/0):
- `shallow_lunge`: Riemann 2012 อาจได้ mistake +1 (สาเหตุ + วิธีแก้) · รวมกับ Gao 2022 (round4) สูงสุด mistake 5 · **consequence ยังเป็น 1**
- `straight_back_leg`: ได้แค่ principle จาก Common Mistakes ("เข่าทั้งสองข้าง ~90°") · mistake/consequence ยังเป็น 0
- `partial_pushup`: ไม่ได้อะไร · push-up ทั้ง 3 ไฟล์เป็นเรื่องศอก/ข้อมือ/สะบัก และ 2 ไฟล์มีเนื้อหาที่อาจขัดกฎ
- **ยังเป็น data gap ทั้ง 3 กฎ** · ไฟล์ที่ช่วยได้จริงคือแบบ Common Mistakes (บทความ "common mistakes") แต่ฉบับนี้ไม่มีหัวข้อลันจ์ตื้นหรือขาหลังเหยียด · ถ้าจะหาต่อ ควรหาแหล่งที่มีหัวข้อ "not going low enough" / "back knee not bending" / "half rep push-up" โดยตรง เช่น หน้า exercise library ของ ACE/NASM/ACSM หรือ textbook การสอนท่า

## 11. URL ใหม่รอบ 2026-10-24 (ให้ user ตรวจ)

user เพิ่ม 8 URL ต่อท้าย `picked/lunge/urls.txt` (4) และ `picked/push-up/urls.txt` (4) · ดึงหน้าเว็บด้วยวิธีเดียวกับ curator (`trafilatura.fetch_url` + `extract` พารามิเตอร์เดียวกัน) ถ้าไม่ได้ลองใหม่ด้วย User-Agent ของเบราว์เซอร์ · อ่านเนื้อหาหลักทุกบทความทั้งฉบับ · ไม่มี URL ไหนอยู่ใน KB แล้ว · เพิ่ม 7 entry ใน `prefilter_v6.json` (รวม 132) · keep ทั้ง 7 (ไม่แน่ใจ 2) · elitefts ยังไม่ได้ตรวจ · ไม่ได้เรียก API ที่เสียเงิน · ยังไม่ได้ย้าย URL หรือสร้างไฟล์

| URL | ดึงได้ไหม | ผล | ได้อะไร |
|---|---|---|---|
| lunge · BOXROX "10 most common walking lunge mistakes" (Mike Israetel) | ต้องใช้ UA | **keep** | **`shallow_lunge` mistake + consequence + วิธีแก้:** "ลงไม่สุด" เป็นท่าผิดที่พบบ่อยที่สุด · กล้ามโตมากกว่าเมื่อถูกยืดตลอดช่วง ใช้ motor unit มากขึ้น · ลงจนเข่าแตะหรือเกือบแตะพื้นอย่างควบคุม · + ก้าวสั้นทำให้เจ็บเข่า (oq2) · โน้มตัวที่จุดต่ำสุด (`forward_trunk_lean`) |
| lunge · elitefts "an easy lunge regression" | **ไม่ได้** (404 ทั้ง http/https · Wayback ตอบ 429) | ยังไม่ตรวจ | ไม่ใส่ entry · ลองใหม่ภายหลังหรือหา URL ใหม่ |
| lunge · ClassPass "proper lunge form mistakes" | ได้ | **keep (ไม่แน่ใจ)** | ก้าวไปหลังไกลเกิน → งอไม่ถึง 90° และเข่าหลังรับแรง (`straight_back_leg` สาเหตุ) · โน้มตัวไปหน้า · เข่าเลยข้อเท้า (oq1) · ท่าที่ถูก: ลดเข่าหลังจนเข่าทั้งสองข้าง ~90° · **ขัดกฎ:** แนะนำ "forward lunge โดยไม่งอขาหลัง" เป็นท่าฝึกขั้นต้น (ขัด `straight_back_leg` ตรง ๆ) |
| lunge · Experience Life "common split squat and lunge errors" | ได้ | **keep** | **`straight_back_leg` สาเหตุ + consequence + วิธีแก้ (แหล่งแรกของกฎนี้):** ระยะยืนยาวเกิน → เข่าหลังงอได้น้อย → เข่าหลังรับแรงมาก นาน ๆ เจ็บเข่า · ตั้งท่าจากท่าคุกเข่าข้างเดียวเพื่อหาระยะที่งอเข่าทั้งสองข้างได้ ~90° · ~1 window |
| push-up · Attika Fitness "5 common push-up errors" | ได้ | **keep** | **`partial_pushup` mistake + consequence + วิธีแก้ + principle** ("half reps = half results", อกไม่ได้ทำงานเต็มที่, ลดจำนวนครั้ง/มือบนกล่อง, อกเกือบแตะพื้น) · `hip_sag_or_pike` ทั้งตกและโด่ง พร้อมสาเหตุ/ผลเสีย/วิธีแก้ |
| push-up · ATHLEAN-X "pushups are killing your gains" (Jeff Cavaliere, PT) | ได้ | **keep** | ทั้งบทความเป็น **`partial_pushup`**: นับครั้ง/รีบ → ลงไม่สุด 1–2 นิ้ว (สาเหตุ + ท่าผิด) → ผลลดลงมาก (consequence) → อกแตะพื้น ลงช้า (วิธีแก้) |
| push-up · Cathe "6 push-up mistakes" | ได้ | **keep** | **`partial_pushup` mistake + consequence + วิธีแก้ + principle** (ศอก ≤ 90°, ถ้าไม่ได้ใช้คุกเข่า/มือบนที่สูง) · `hip_sag_or_pike` สาเหตุ (core อ่อน) + วิธีแก้ (แพลงก์) |
| push-up · Fitness and Power "proper push-up form" | ต้องใช้ UA | **keep (ไม่แน่ใจ)** | `hip_sag_or_pike` สาเหตุ/ผลเสีย/วิธีแก้ครบ · `partial_pushup` สาเหตุ (อีโก้/ล้า) + วิธีแก้ · **หลายจุดขัด card:** "สะโพกโด่งค่อนข้างปลอดภัย ให้เอียงไปทางสูงไว้ก่อน", "เกร็ง quad ไม่ใช่บีบก้น", เรียกวิดพื้น**เท้า**บนที่สูงว่า "incline" (card ใช้ incline = **มือ**บนที่สูง เป็นท่าง่าย) → generator อาจแนะนำท่าที่ยากกว่าให้มือใหม่ |

**user ตัดสิน 2026-10-24 — แก้แล้ว:** บันทึก 5 บทความที่ keep แน่ ๆ เป็น `.txt` ใน `checked/<ท่า>/` (id `data/<ท่า>/…`): `lunge/BOXROX_WalkingLungeMistakes.txt`, `lunge/ExperienceLife_SplitSquatLungeErrors.txt`, `push-up/Attika_PushUpErrors.txt`, `push-up/AthleanX_PushUpRangeOfMotion.txt`, `push-up/Cathe_PushUpMistakes.txt` · ใช้ข้อความที่ trafilatura ดึงได้ ตัดแค่ลิงก์ "Read more"/โปรโมต/รายการบทความที่เกี่ยวข้อง · เพิ่ม entry `path` 5 อัน (รวม 137) · ใส่ batch `round4` แล้ว (รวม 8 ไฟล์ ตรวจด้วย `load_batch` ของ curator ว่าหาไฟล์เจอและไม่อยู่ใน skip-list) · ClassPass และ Fitness and Power **ไม่ใส่ batch** (เนื้อหาซ้ำกับ 5 ตัว + มีส่วนขัดกฎ) · ย้าย 8 URL (รวม elitefts) จาก `picked/` ไป `checked/lunge/urls.txt` และ `checked/push-up/urls.txt` · `picked/<ท่า>/urls.txt` กลับเป็นเหมือนใน git

**ติดเรื่องการ curate (ตอนตรวจ):**
1. URL ทั้ง 8 อยู่ใน `picked/<ท่า>/urls.txt` · curator **ไม่อ่าน `picked/` เลย** และ `urls.txt` ของ lunge/push-up มีผล curate แล้ว curator จะข้ามทั้ง list อยู่ดี · ตาม `data/README.md` §4 URL ที่ตรวจแล้วแต่ยังไม่ curate ควรอยู่ใน `checked/<ท่า>/urls.txt`
2. BOXROX และ Fitness and Power ต้องใช้ User-Agent ของเบราว์เซอร์ `trafilatura.fetch_url` ได้หน้าที่ไม่มีบทความ
→ ทางที่ไม่ต้องแก้ curator (แบบเดียวกับ `BOXROX_PushUpBenchmarks.txt` รอบ 3): บันทึกเนื้อหาแต่ละบทความเป็น `.txt` (บรรทัดแรก `Source URL: …`) ใน `data/<ท่า>/` แล้วใส่ `.txt` ลง batch · ย้าย 8 URL จาก `picked/` ไป `checked/<ท่า>/urls.txt` เป็นหลักฐาน

**ข้อควรระวังหลัง curate:**
- ClassPass: หา item "forward lunge โดยไม่งอขาหลัง" แล้วถอด tag หรือลบ
- Cathe: item "ลงครึ่งทางแล้วค้างไว้" (isometric) อาจถูกติด `partial_pushup` แบบสนับสนุนการลงครึ่งท่า → ถอด tag
- ATHLEAN-X: ส่วน "เหยียดแขนสุดด้านบน" ไม่ใช่กฎ (card ไม่นับ) ไม่ควรติด tag `partial_pushup`
- BOXROX lunge: "เข่าแตะพื้น" คือแตะเบา ๆ อย่างควบคุม ไม่ใช่เข่ากระแทกพื้น (card ไม่นับ)

**2026-10-24 (ขั้น 3 ของแผน strict/v6b, user สั่งให้ curate):**
- elitefts: URL ใหม่ `https://www.elitefts.com/education/an-easy-lunge-regression/` (หน้าสดยัง redirect ไป 404) · อ่านทั้งฉบับจาก Wayback capture 2020-10-30 (Brian LeRiche, 2019) · **keep** · `straight_back_leg` mistake (ขาหลังเหยียดขณะลดตัว) + consequence (ตัวพุ่งไปข้างหน้า → เจ็บเข่า) + วิธีแก้ (งอเข่า ~90° แล้วลงตรง ๆ) · principle: ใช้กระดูกอกเป็นจุดอ้างอิง "ลิฟต์ ไม่ใช่บันไดเลื่อน" · **ระวัง:** cue "เท้าหลังเขย่ง (plantarflex) ชิดกำแพง" เป็นเรื่องเท้าหลังเพียงอย่างเดียว card ไม่นับ → ไม่ควรติด `straight_back_leg` · บันทึกเป็น `checked/lunge/EliteFTS_EasyLungeRegression.txt` (ตัดเมนู/footer/ประวัติผู้เขียนที่มีอีเมลออก) · เพิ่ม entry `url` + `path` (รวม 139) · เพิ่ม URL ใหม่ใน `checked/lunge/urls.txt` · ใส่ batch `round4` (รวม 9 ไฟล์)
- BOXROX `https://www.boxrox.com/?p=159295` = บทความเดียวกับ `BOXROX_WalkingLungeMistakes.txt` (redirect ไป "10 most common walking lunge mistakes") ไม่ต้องเพิ่ม
- ClassPass ยังไม่อยู่ใน batch ตามที่ตัดสินไว้ข้างบน (แผนขั้น 3 ระบุไว้ · ถ้าจะใส่ทำเป็น batch แยกได้ ~1 window)

**ผลต่อ data gap** (coverage จาก §9.1: `partial_pushup` 3/1/7/2 · `shallow_lunge` 3/1/10/7 · `straight_back_leg` 0/0/6/0 · ตัวเลขด้านล่างเป็นการประมาณ ต้องดู `tag_coverage.py` หลัง curate):
- `partial_pushup`: **น่าจะปิด gap ได้** · Attika, ATHLEAN-X, Cathe มีทั้ง mistake และ consequence ทั้ง 3 แหล่ง (+ Fitness and Power ถ้าใส่) → mistake น่าจะเกิน 5 · consequence ~4–5
- `shallow_lunge`: consequence ได้เพิ่มครั้งแรก (BOXROX) · mistake เพิ่มจาก BOXROX + round4 (Gao 2022, Riemann) → mistake ~5–6 · consequence ~2 ยังไม่ถึง 5
- `straight_back_leg`: จาก 0 → mistake ~1–2 · consequence ~1–2 (Experience Life, ClassPass) · ยังไม่ถึง 5 แต่ไม่เป็นศูนย์แล้ว

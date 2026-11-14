# แหล่งเนื้อหาสำหรับเติมช่อง ✗ ใน KB: drill ของ knee_varus, elbow_flare, partial_curl (2026-11-14)

> ต่อจาก `docs/reports/kb_fix_audit_2026-11-14.md` ข้อ 3 · ค้นจากเว็บโดย Claude · **ยังไม่ได้ curate และยังไม่ได้เรียก API** · เครื่องของผู้ใช้ไม่มี network จึงยังไม่ได้ดาวน์โหลด PDF ให้ (ลิงก์อยู่ใน §4)
>
> ผู้ตัดสินว่าแต่ละ drill "ผ่าน D3" คือ Claude ไม่ใช่ผู้เชี่ยวชาญ

## 1. สรุป

1. **ไม่มีงานวิจัยที่ทดลอง drill ของ 3 fault นี้โดยตรง** · drill ที่ลงมือได้มาจากแหล่งโค้ช (เว็บ) ส่วนงานวิจัยให้ได้แค่สาเหตุ ผล และเหตุผลว่าทำไม drill นั้นตรงจุด · ถ้าอยากได้ dose (F3) กับ self-check (F4) ที่แน่นอน ต้องเขียนโน้ตให้ผู้เชี่ยวชาญ (Ton) รับรองแล้วใส่เป็น `.txt` (ร่างอยู่ §5)
2. **knee_varus ได้ของแถม C2:** Straub & Powers 2024 รายงานว่าหันปลายเท้าออก 30° เพิ่มแรงบิดดันเข่าออกนอก (varus moment) ราว 80% และ Han 2013 วัดว่า squat แบบปลายเท้าเปิด 30° เข่าเอียงไปทาง varus · audit บอกว่าช่องสาเหตุเฉพาะของ knee_varus ยัง ✗ อยู่
3. **partial_curl: rule ของระบบนับพลาดได้เฉพาะฝั่งเหยียดแขน** (card `bicep-curl.partial_range`: ครั้งที่นับแล้วพลาดได้แค่ครึ่งเหยียด) · drill จึงควรฝึก "ช่วงล่าง/เหยียดสุด" ไม่ใช่ช่วงบน
4. **ระวังแหล่งเรื่อง lengthened partials:** Wolf 2025, Sato 2021, Pedrosa 2023 สนับสนุนการฝึกช่วงล่าง ถ้า chunk ออกมาเป็น "ทำแค่ครึ่งล่างก็พอ" RAG อาจแนะนำสิ่งที่ทำให้ rule `partial_curl` ยิงเอง · แนะนำ **ไม่ใส่ Wolf 2025** และตรวจ chunk ของ Sato/Pedrosa ว่าติด tag แบบ "ช่วงล่างสำคัญที่สุด จึงต้องเหยียดสุดทุกครั้ง"
5. **D5 (อุปกรณ์ในบ้าน):** preacher bench กับ incline bench ไม่ใช่ของในบ้าน · drill ที่เลือกใช้ ผนัง เก้าอี้ ผ้าขนหนู ดัมเบล · incline curl ยังเสี่ยงทำให้ rule `elbow_flare` ยิง เพราะต้นแขนอยู่หลังลำตัว
6. **ข้อสังเกตข้างทาง:** Greg Everett (Catalyst Athletics, 2024) เลิกใช้ mini-band รอบเข่าเพราะไม่ได้ผล · ซึ่งเป็นประโยคเดียวที่ context ตอนนี้มีสำหรับ knee_valgus ("ใช้ resistance band")

## 2. drill ที่เสนอ ต่อ fault

"ผ่านย้าย" = ถ้าย้ายไปใส่ fault อื่นของท่าเดียวกันแล้วไม่จริง (กฎ D3 ใน `pairwise_eval_v2_plan.md`) · "dose" = แหล่งให้ dose มาเองหรือไม่

### squat/knee_varus

| drill / ช่อง | ทำอย่างไร | ผ่านย้าย? | dose จากแหล่ง | แหล่ง |
|---|---|---|---|---|
| **drill:** squat "นิ้วโป้งเท้าไม่ลอย" (tripod foot) | ถอดรองเท้า วางน้ำหนัก 3 จุด (ส้นเท้า, โคนนิ้วโป้ง, โคนนิ้วก้อย) ย่อลงเก้าอี้ ดันเข่าออกได้แค่จนโคนนิ้วโป้งเริ่มเบา แล้วหยุด | ผ่าน · valgus เป็นตรงข้าม (อุ้งเท้ายุบ นิ้วโป้งรับน้ำหนักเกิน) | ไม่มี | Squat University (tripod, "ดันเข่าออกโดยนิ้วโป้งยังแตะพื้น"), fitwill (อย่าดันเข่าออกจนเท้าม้วนไปขอบนอก) |
| setup: มุมปลายเท้า | ตั้งมุมก่อนย่อ ไม่ปรับกลางทาง · 5–10° ถึง 20–30° ตามสรีระ · เข่าอยู่แนวนิ้วเท้าที่ 2 | ผ่าน | มีตัวเลขมุม | Everett 2024, Straub & Powers 2024, Lorenzetti 2018 (มีใน KB แล้ว) |
| self-check (F4) | ที่จุดต่ำสุด ก้มดู: ลูกสะบ้าอยู่เหนือนิ้วที่ 2–3 ไม่เลยนิ้วก้อย · รู้สึกน้ำหนักใต้โคนนิ้วโป้งตลอด ถ้าขอบในเท้าเบา = เข่าออกเกิน | ผ่าน | – | Squat University, fitwill, card (ผล: นิ้วโป้งหลุดจากพื้น) |
| สาเหตุ (C2) | ปลายเท้าเปิดมาก, ทำตาม "knees out" เกิน, ยืนกว้างเกิน | ผ่าน | ตัวเลข 80% | Straub & Powers 2024, Han 2013, Everett 2024 |

drill ของ knee_varus ยังบาง: มีตัวเดียวที่ผ่านย้ายชัด · pause squat ที่ Everett แนะนำใช้กับ valgus ได้ด้วย (ไม่ผ่าน)

### bicep-curl/elbow_flare

| drill / ช่อง | ทำอย่างไร | ผ่านย้าย? | dose จากแหล่ง | แหล่ง |
|---|---|---|---|---|
| **drill:** wall curl | ยืนหลังชิดผนัง ศอกแตะผนังเบา ๆ เคิร์ลโดยศอกไม่หลุดจากผนัง | ผ่าน · ไม่ช่วยเรื่องเหยียดสุด | ลดน้ำหนัก 10–20% | Fitness Volt 2026, FitCraft |
| **drill:** concentration curl บนเก้าอี้ | นั่ง ต้นแขนกดแนบต้นขาด้านใน แล้วเคิร์ล · ต้นแขนแกว่งไม่ได้ | ผ่าน | ไม่มี (งานวิจัยใช้ 70% 1RM ทดสอบ ไม่ใช่โปรแกรม) | ACE 2014 (Porcari): biceps ทำงานสูงสุด ไหล่หน้าทำงานต่ำ เพราะต้นแขนกดกับขา |
| self-check (F4) | "ดัมเบลขยับ ต้นแขนไม่ขยับ" · ศอกแตะซี่โครง/ผนังตลอด ถ้าศอกพุ่งไปหน้าทุกครั้ง = ไหล่หน้ากำลังช่วย | ผ่าน | – | Fitness Volt 2026 |
| ไอเดีย ยังไม่มีแหล่งดี | หนีบผ้าขนหนูใต้รักแร้ ถ้าผ้าหล่น = ศอกออกจากลำตัว | ผ่าน | – | ไม่พบแหล่งที่น่าเชื่อ · ใส่ได้ผ่านโน้ตผู้เชี่ยวชาญเท่านั้น |

### bicep-curl/partial_curl

| drill / ช่อง | ทำอย่างไร | ผ่านย้าย? | dose จากแหล่ง | แหล่ง |
|---|---|---|---|---|
| **drill:** 1½-rep curl (ครึ่งล่าง + เต็ม) | จากแขนเหยียดสุด → ยกถึงแนวขนานพื้น → ลงจนเหยียดสุด → ยกเต็มจนสุด = 1 ครั้ง · ทุกครั้งผ่านจุดเหยียดสุด 2 รอบ | ผ่าน · ไม่แก้ศอกลอย | 4 × 12–14 (แบบ preacher) | The Barbell (1½ reps), Cheetah Ray (ทำครึ่งที่กล้ามยืด) · เหตุผล: Sato 2021, Pedrosa 2023 |
| drill เสริม (ระวัง rule) | หลังเซ็ตปกติ ต่อครึ่งล่าง 3–5 ครั้ง (เหยียดสุด → ศอก 90°) | ผ่าน | 3–5 ครั้งท้ายเซ็ต | Peloton (GB) · **ถ้าทำในเซ็ตที่ระบบดูอยู่ rule จะยิง** ต้องบอกว่าเป็นท่าเสริม |
| ไม่นับเป็น drill (D3 no) | หยุดค้างล่าง, ลงช้า 2 วินาที | ไม่ผ่าน (ท่าเดิมช้าลง) | 2 วินาที | Fitness Volt 2026 · ใช้เป็น cue ได้ |
| self-check (F4) | ล่างสุด: แขนตรง ข้อพับศอกหันไปหน้า ดัมเบลอยู่ข้างต้นขา · บีบหลังแขน (triceps) จนแขนตรง จะรู้สึกยืดที่ต้นแขนด้านหน้า | ผ่าน | – | Built With Science 2022, Lifting Tempo |
| ผล (C3) | ช่วงล่างคือช่วงที่กล้ามโตมากที่สุด โดยเฉพาะส่วนใกล้ศอก · ฝึกช่วงล่างเพิ่มแรงทั้งช่วงมากกว่าฝึกช่วงบน | ผ่าน | ตัวเลข | Sato 2021 (หนา +8.9% vs +3.4%), Pedrosa 2023 (1RM +42.8% vs +19.0%) |

## 3. ตัวเลขจากงานวิจัย (ไว้ตรวจ chunk หลัง curate)

| งานวิจัย | ใคร / ทำอะไร | ผลที่ใช้ได้ |
|---|---|---|
| Straub & Powers 2024 (IJSPT 19(4):490–501) | review ชีวกลศาสตร์ squat | ปลายเท้าเปิด 30°: valgus moment −50%, varus moment +80% · สะโพกหมุนออก 30°/50°: adductor ทำงาน 17%/23% MVIC เทียบ 13% |
| Han et al. 2013 (J Hum Kinet 39:59–66) | 15 คน · neutral / ปลายเท้าหุบ 30° / เปิด 30° | เปิด 30° เข่าเอียงไปทาง varus ช่วง 10–90% ของ squat · ผู้วิจัยแนะนำท่า neutral |
| Sato et al. 2021 (Front Physiol 12:734509) | 32 คนไม่เคยฝึก · ฝึก 0–50° vs 80–130° · 2 ครั้ง/สัปดาห์ 5 สัปดาห์ | ความหนา +8.9% vs +3.4% · แรงเพิ่มเฉพาะกลุ่มช่วงเหยียด |
| Pedrosa et al. 2023 (Sports 11(2):39) | 19 หญิงไม่เคยฝึก · preacher curl 0–68° vs 68–135° · 3 ครั้ง/สัปดาห์ 8 สัปดาห์ · 4→5 เซ็ตถึงหมดแรง tempo 2-2 | biceps ส่วนปลายโตกว่า (ES 0.89) · 1RM เต็มช่วง +42.8% vs +19.0% |
| ACE 2014 (Young, Porcari et al.) | 16 คน · EMG 8 ท่า ที่ 70% 1RM | concentration curl: biceps สูงสุด ไหล่หน้าต่ำกว่าท่าอื่นส่วนใหญ่ |

ตัวอย่างการอ่านตัวเลข: Sato ฝึกช่วง 0–50° (ช่วงล่าง) ความหนาเพิ่ม 8.9% ส่วนช่วง 80–130° (ช่วงบน) เพิ่ม 3.4% · ช่วงกว้างเท่ากัน 50° แต่ช่วงล่างได้ผล 8.9 ÷ 3.4 ≈ 2.6 เท่า

## 4. ไฟล์ที่ต้องเอามาใส่ `data/`

ดาวน์โหลด PDF เอง (เครื่องนี้ไม่มี network) · เว็บใส่ใน `urls.txt` ของโฟลเดอร์ (curator ใช้ trafilatura ดึงเนื้อหา)

| โฟลเดอร์ | ไฟล์ | ประเภท | ลิงก์ |
|---|---|---|---|
| `data/squat/knee_varus/` | Straub & Powers 2024 | PDF, open access | https://doi.org/10.26603/001c.94600 (PMC10987311) |
| `data/squat/knee_varus/` | Han et al. 2013 | PDF, open access | https://doi.org/10.2478/hukin-2013-0068 (PMC3916928) |
| `data/bicep-curl/full_rom/` | Pedrosa et al. 2023 | PDF, CC BY 4.0 | https://www.mdpi.com/2075-4663/11/2/39 |
| `data/bicep-curl/full_rom/` | Sato et al. 2021 | PDF, CC BY 4.0 | https://doi.org/10.3389/fphys.2021.734509 |
| `data/bicep-curl/elbow_away/` | ACE 2014 | PDF ฟรี | https://www.acefitness.org/continuing-education/prosource/august-2014/4933/ace-study-reveals-best-biceps-exercises/ |

`data/squat/knee_varus/urls.txt`
```
https://www.catalystathletics.com/article/2270/Knee-Valgus-in-the-Squat
https://squatuniversity.com/2015/10/29/the-squat-fix-dont-forget-the-foot/
https://fitwill.app/exercise/2359/barbell-squat-knees-end-position-wrong-right
```

`data/bicep-curl/elbow_away/urls.txt`
```
https://fitnessvolt.com/biceps-curl-mechanics/
https://getfitcraft.com/exercises/bicep-curls
```

`data/bicep-curl/full_rom/urls.txt`
```
https://builtwithscience.com/fitness-tips/fix-bicep-curls-mistakes
https://liftingtempo-website.pages.dev/tempo/bicep-curl
https://thebarbell.com/21-curls/
https://www.onepeloton.com/en-GB/blog/biceps-curl
```

ข้อควรรู้:
- Catalyst Athletics หน้า 1826 ดึงเนื้อหาไม่ได้ (WebFetch ได้หน้าว่าง) จึงใช้หน้า 2270 แทน · ถ้า trafilatura ได้ไม่ถึง 200 ตัวอักษร curator จะข้ามเอง (`[URL SKIP]`)
- Fitness Volt กับ Built With Science พูดทั้ง elbow_flare และ partial_curl ในหน้าเดียว · tag มาจาก LLM ไม่ใช่โฟลเดอร์ จึงใส่โฟลเดอร์ไหนก็ได้ แต่อย่าใส่ซ้ำสองโฟลเดอร์
- ใน `data/checked/bicep-curl/` มีของที่ตรวจแล้วแต่ยังไม่ curate ซึ่งน่าจะช่วย C2/C3 ของ elbow_flare (ไม่ใช่ drill): "Bilateral Biceps Curl ... Arms Flexion No-Flexion", "The Effect of Shoulder Flexion Angles ...", และ "Distinct muscle growth ... preacher and incline biceps curls" (ช่วงยืด, partial_curl)
- ไม่ใส่: Wolf et al. 2025 PeerJ (lengthened partials เท่ากับเต็มช่วง เสี่ยงเรื่อง rule), Marcolin 2018 (เปรียบเทียบชนิดบาร์ ไม่เกี่ยวกับ fault)
- หลัง curate ต้องรัน embed ซึ่งเรียก API · ขอผู้ใช้อนุมัติก่อนตามปกติ

## 5. ร่างโน้ตผู้เชี่ยวชาญ (ใส่ได้หลัง Ton รับรองเท่านั้น)

แหล่งเว็บไม่ให้ dose และ self-check ครบ · ถ้าผู้เชี่ยวชาญรับรอง ข้อความนี้บันทึกเป็น `.txt` (curator อ่าน `.txt` ได้) · ตัวเลข dose ทั้งหมดเป็น**ร่างของ Claude** ยังไม่มีใครตรวจ

```
Squat - knees splaying outward (knee_varus)
Drill: barefoot tripod squat to a chair. Stand with weight on the heel, the base of the big toe and the base of the little toe. Lower to the chair, letting the knees move out only until the big toe starts to feel light, then stop. 2 sets of 8 slow repetitions (3 seconds down) before the main sets.
Check: at the bottom, the kneecap sits over the second or third toe, not outside the little toe, and the ball of the big toe stays pressed into the floor. If the inner edge of the foot goes light, the knees are too far out.
Cause: toes turned out too far, a stance wider than the shoulders, or overdoing "push the knees out".

Bicep curl - elbows leaving the side of the body (elbow_flare)
Drill: wall curl. Stand with the back and the back of the elbows lightly touching a wall and curl without the elbows leaving the wall. 2 sets of 10 with a weight 10-20% lighter than usual.
Drill: seated concentration curl on a chair, upper arm pressed against the inner thigh. 2 sets of 10 per arm.
Check: the dumbbell moves but the upper arm does not; the elbow stays touching the ribs for the whole repetition.

Bicep curl - not straightening the arm at the bottom (partial_curl)
Drill: one-and-a-half repetition curl. From a fully straight arm, curl to forearm parallel with the floor, lower until the arm is fully straight again, then curl all the way up. That is one repetition. 2 sets of 6-8.
Check: at the bottom the arm is straight, the crease of the elbow faces forward and the back of the arm (triceps) is tight; you feel a stretch at the front of the upper arm before the next repetition starts.
```

ร่างนี้ผ่าน Q-spec ไม่ได้รับประกัน: ถ้าจะใส่ ให้รัน `eval/check_rule_cards.py --queries` ว่า `query`/`fix_query` ไม่ซ้ำ n-gram กับข้อความใหม่ เพราะ fix_query เขียนจากความรู้โค้ชทั่วไปเหมือนกัน

## แหล่งที่อ้าง

- Straub RK, Powers CM. A Biomechanical Review of the Squat Exercise. IJSPT 2024 · https://doi.org/10.26603/001c.94600
- Han S, Ge S, Liu H, Liu R. Alterations in 3D Knee Kinematics and Kinetics during Neutral, Squeeze and Outward Squat. J Hum Kinet 2013 · https://doi.org/10.2478/hukin-2013-0068
- Sato S et al. Elbow Joint Angles in Elbow Flexor Unilateral Resistance Exercise Training. Front Physiol 2021 · https://doi.org/10.3389/fphys.2021.734509
- Pedrosa GF et al. Training in the Initial Range of Motion Promotes Greater Muscle Adaptations Than at Final in the Arm Curl. Sports 2023 · https://www.mdpi.com/2075-4663/11/2/39
- Young S, Porcari JP et al. ACE Study Reveals Best Biceps Exercises. ACE ProSource 2014 · https://www.acefitness.org/continuing-education/prosource/august-2014/4933/ace-study-reveals-best-biceps-exercises/
- Everett G. Knee Valgus in the Squat. Catalyst Athletics 2024 · https://www.catalystathletics.com/article/2270/Knee-Valgus-in-the-Squat
- Horschig A. The Squat Fix: Don't Forget The Foot. Squat University · https://squatuniversity.com/2015/10/29/the-squat-fix-dont-forget-the-foot/
- Robertson J. Biceps Curl Mechanics. Fitness Volt 2026 · https://fitnessvolt.com/biceps-curl-mechanics/
- Ethier J. 5 Bicep Curl Mistakes. Built With Science 2022 · https://builtwithscience.com/fitness-tips/fix-bicep-curls-mistakes

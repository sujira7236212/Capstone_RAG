# Generation-side evaluation

terms: `eval\jargon_terms.json` · sessions: `mock_data\mock_sessions.json` · min span: 6 words · gloss window: 120 chars

`unglossed jargon` = clinical terms with no everyday meaning in the same sentence. `longest shared n-gram` = longest word run copied from the Retrieved KB Context; the WITHOUT RAG row never saw that context, so its number is this report's chance floor.

| report | exercise | side | words | unglossed jargon | longest shared n-gram | spans ≥6 | longest match |
|---|---|---|---|---|---|---|---|
| compare_result_v9.md | Squat | WITH RAG | 487 | 8 | 20 | 8 | descend until the top of the thigh is at least parallel with… |
| compare_result_v9.md | Squat | WITHOUT RAG | 465 | 2 | 6 | 1 | back rounds at the bottom of |
| compare_result_v9.md | Lunge | WITH RAG | 447 | 7 | 9 | 4 | 2 to 3 cm short of contacting the ground |
| compare_result_v9.md | Lunge | WITHOUT RAG | 529 | 1 | 0 | 0 | — |
| compare_result_v9.md | Push-up | WITH RAG | 185 | 2 | 0 | 0 | — |
| compare_result_v9.md | Push-up | WITHOUT RAG | 206 | 0 | 0 | 0 | — |
| compare_result_v9.md | Bicep Curl | WITH RAG | 564 | 0 | 6 | 1 | where the muscle is fully stretched |
| compare_result_v9.md | Bicep Curl | WITHOUT RAG | 553 | 0 | 0 | 0 | — |
| compare_result_v10.md | Squat | WITH RAG | 532 | 0 | 6 | 2 | level with or slightly below the |
| compare_result_v10.md | Squat | WITHOUT RAG | 575 | 0 | 6 | 1 | back rounds at the bottom of |
| compare_result_v10.md | Lunge | WITH RAG | 594 | 1 | 9 | 1 | 2 to 3 cm short of contacting the ground |
| compare_result_v10.md | Lunge | WITHOUT RAG | 567 | 0 | 0 | 0 | — |
| compare_result_v10.md | Push-up | WITH RAG | 139 | 0 | 0 | 0 | — |
| compare_result_v10.md | Push-up | WITHOUT RAG | 111 | 0 | 0 | 0 | — |
| compare_result_v10.md | Bicep Curl | WITH RAG | 526 | 0 | 0 | 0 | — |
| compare_result_v10.md | Bicep Curl | WITHOUT RAG | 543 | 0 | 0 | 0 | — |

**compare_result_v9.md — WITH RAG**: unglossed jargon **17** across 4 exercises · longest shared n-gram **20** words · spans ≥6: 13
**compare_result_v9.md — WITHOUT RAG**: unglossed jargon **3** across 4 exercises · longest shared n-gram **6** words · spans ≥6: 1
**compare_result_v10.md — WITH RAG**: unglossed jargon **1** across 4 exercises · longest shared n-gram **9** words · spans ≥6: 3
**compare_result_v10.md — WITHOUT RAG**: unglossed jargon **0** across 4 exercises · longest shared n-gram **6** words · spans ≥6: 1

### Evidence

**compare_result_v9.md · Squat · WITH RAG**
- unglossed `lordotic` — *Cue:* Focus on keeping a proud chest and a stiffened torso with a neutral, lordotic lumbar position.
- unglossed `external rotation` — *Setup:* Make sure you are giving your hips enough room—forcing deep hip flexion without accommodating the necessary hip abduction and external rotation causes the pelvis to tuck.
- unglossed `hip abduction` — *Setup:* Make sure you are giving your hips enough room—forcing deep hip flexion without accommodating the necessary hip abduction and external rotation causes the pelvis to tuck.
- unglossed `hip flexion` — *Setup:* Make sure you are giving your hips enough room—forcing deep hip flexion without accommodating the necessary hip abduction and external rotation causes the pelvis to tuck.
- unglossed `spinal` — *Drill:* Work on your spinal and hip mobility to ensure you can comfortably assume and maintain that slight arch in your lower back before adding heavy loads.
- unglossed `muscular complex` — **Why it matters:** Without squatting to the proper depth, the hamstrings and gluteus muscular complex may not be adequately challenged.
- unglossed `gluteus` — **Why it matters:** Without squatting to the proper depth, the hamstrings and gluteus muscular complex may not be adequately challenged.
- unglossed `femur` — *Self-check:* Watch your side-profile video to confirm your femurs are at least parallel to the floor at the bottom of the movement.
- copied 20 words — "descend until the top of the thigh is at least parallel with the ground and the hip joint is at"
- copied 20 words — "allowing the spine to flex during a squat compromises back curvature and can lead to eventual pain and suboptimal performance"
- copied 17 words — "without squatting to the proper depth the hamstrings and gluteus muscular complex may not be adequately challenged"
- copied 17 words — "forcing deep hip flexion without accommodating the necessary hip abduction and external rotation causes the pelvis to"
- copied 13 words — "where the top of the thighs do not reach parallel to the ground"
- copied 9 words — "a stiffened torso with a neutral lordotic lumbar position"
- copied 8 words — "level with or slightly below the knee joint"
- copied 6 words — "back rounds at the bottom of"

**compare_result_v9.md · Squat · WITHOUT RAG**
- unglossed `lumbar spine` — **Why it matters:** This puts unnecessary flexion stress on your lumbar spine and lower back muscles, which can lead to tightness or soreness over time, especially as you add weight.
- unglossed `valgus` — **Keep the knees out:** Maintain the great knee tracking you unlocked today so valgus doesn't sneak back in.
- copied 6 words — "back rounds at the bottom of"

**compare_result_v9.md · Lunge · WITH RAG**
- unglossed `lower extremity` — **Why it matters:** Leaning the trunk forward shifts your center of mass forward, increasing weight bearing and mechanical demand on your lead lower extremity.
- unglossed `center of mass` — **Why it matters:** Leaning the trunk forward shifts your center of mass forward, increasing weight bearing and mechanical demand on your lead lower extremity.
- unglossed `plantar flexor` — It alters your muscular load by pushing extra work onto your hip extensors and ankle plantar flexors while taking it away from your knee extensors.
- unglossed `knee extensor` — It alters your muscular load by pushing extra work onto your hip extensors and ankle plantar flexors while taking it away from your knee extensors.
- unglossed `hip extensor` — It alters your muscular load by pushing extra work onto your hip extensors and ankle plantar flexors while taking it away from your knee extensors.
- unglossed `knee extension moment` — **Why it matters:** A shallower lunge generates a higher knee extension moment, increasing the mechanical demand on your knee extensor musculature.
- unglossed `knee extensor` — **Why it matters:** A shallower lunge generates a higher knee extension moment, increasing the mechanical demand on your knee extensor musculature.
- copied 9 words — "2 to 3 cm short of contacting the ground"
- copied 7 words — "hip extensors and ankle plantar flexors while"
- copied 6 words — "generates a higher knee extension moment"
- copied 6 words — "upper body perpendicular to the ground"

**compare_result_v9.md · Lunge · WITHOUT RAG**
- unglossed `hip flexor` — **Why it matters:** This shifts extra load onto your lower back and front hip flexors instead of keeping the work in your glutes and quads.

**compare_result_v9.md · Push-up · WITH RAG**
- unglossed `lower extremity` — **Keep your core locked:** Maintain a rigid spine and keep your lower-extremity segments fully engaged throughout the entire push-up movement, just like you did today.
- unglossed `brachii` — **Vary your hand placement if needed:** If you want to put a bit more focus on your triceps brachii, try narrowing your hand width slightly on your next set to demand more work from your elbows.

**compare_result_v9.md · Bicep Curl · WITH RAG**
- copied 6 words — "where the muscle is fully stretched"

**compare_result_v10.md · Squat · WITH RAG**
- copied 6 words — "level with or slightly below the"
- copied 6 words — "back rounds at the bottom of"

**compare_result_v10.md · Squat · WITHOUT RAG**
- copied 6 words — "back rounds at the bottom of"

**compare_result_v10.md · Lunge · WITH RAG**
- unglossed `center of mass` — Why it matters: Leaning forward shifts your center of mass ahead of your base, throwing extra weight onto your front leg and overloading your hips and calves while taking the work away from your quads.
- copied 9 words — "2 to 3 cm short of contacting the ground"


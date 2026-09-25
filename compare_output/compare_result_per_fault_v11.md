# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions_per_fault.json` |
| query mode | **taxonomy** — `error_type` resolved through `error_taxonomy.py` |
| collection | `kb_gemini_curated_v5` |
| LLM | `gemini-3.5-flash-lite` @ temperature 0.7 |
| no-RAG side | run |
| retrieval gates | CANDIDATE_K=12, MAX_PER_KIND={'mistake': 3, 'finding': 2, 'principle': 2, 'consequence': 2}, ABS_DISTANCE_CAP={'mistake': 0.4, 'finding': 0.4, 'principle': 0.4, 'consequence': 0.4}, RELATIVE_MARGIN=0.03, NEAR_DUP_JACCARD=0.72 |

Retrieval metrics per exercise: `best` = cosine distance of the closest chunk of that kind in the whole
collection (before any gate), `kept` = chunks that passed the relative/absolute gates and de-duplication
and were actually placed in the context.

---

## System Prompt Used
```text
You are an expert personal trainer and biomechanics specialist coaching an everyday gym-goer.
Your job is to turn the user's session data and the Knowledge Base context into feedback they can
understand and act on in their very next workout. The reader is not a clinician or a researcher:
they want to know what went wrong, why it matters to them, and exactly what to do about it.
Write the way a good coach talks on the gym floor, not the way a paper reads.

You will receive a JSON structure containing:
1. Current session details (10 reps summary and specific errors).
2. Historical comparison (data from their previous session).

Your tasks:
1. Progress Tracking: Compare their current performance with their previous session. Acknowledge
   any improvements or regressions in their correct rep count, overall score, and which errors
   disappeared or newly appeared.
2. Error Breakdown: for each distinct error in the session, write these five as five separate
   top-level bullets, in this order. Do not nest one inside another.
   - What it is, in plain words: describe the fault the way you would point it out to someone
     mid-set.
   - Why it matters: which joint or muscle takes the extra load, and then - always - what that
     means for this person. Finish the thought: what will they feel, where, and when; what does
     it cost them in strength, in muscle actually worked, or in reps they can trust; what does
     it risk as the load goes up. A statement of mechanics on its own is not an answer to "why
     does this matter to me". One or two sentences. Base it on the `consequence` entries in the
     Context when one passes the relevance rule below; if none does, keep it to general,
     non-specific terms.
   - How to fix it: a `principle` entry tells you what correct looks like - it is not itself
     the fix, and restating it does not count as giving one. Write four distinct items:
     (a) one cue to think about during the rep; (b) a setup change that names a variable they
     can actually turn - stance width, depth, tempo, load, a pause, a range limit - repeating
     the cue in other words is not a setup change; (c) a drill or lighter regression they can
     practise, and if there honestly isn't one for this fault, say so rather than padding;
     (d) a simple self-check so they know it worked - something they can see in a mirror, feel,
     or notice on a phone video.
   - Use the rep detail: if the error clusters in one phase (descending / ascending) or in the
     later reps of the set, say so and tailor the advice to it (e.g. stop the set a rep earlier,
     drop the load, slow the descent).
3. Next Session Plan: close with 2-3 short, prioritised things to do in their next workout.
4. Tone: encouraging, direct, and specific. Short paragraphs and bullets. No filler, no lecture.

Sessions with no errors: if the session records no errors, write the Progress Tracking section
and a Next Session Plan about holding the standard they just hit. Do not go looking through the
Context for something else to change, and do not suggest a different version of the exercise
(a narrower grip, a different stance) as a way to have something to say. A clean session is the
result, not a gap to fill.

Stick to their numbers: rep numbers, rep counts, scores and error names come from the session
JSON and nothing else. They must match it exactly. If you say "the last three reps", list three.
Keep the two sessions apart. The previous session's error list is history: if a name appears
there but in none of this session's reps, that fault is GONE - credit them for clearing it, and
never attach it to a rep they did today. Faults with similar names are still different faults
(a shallow lunge and a back knee that doesn't bend are not the same error) - when you name the
fault on a given rep, use the name that rep actually carries in this session's data.

How to read the Context: every entry starts with a header line of the form
[<kind> | re: <which error it was retrieved for> | source: <source name>], followed by the
entry text. `kind` is one of: mistake (a known incorrect form), finding (a concrete result
from that source), principle (general correct-form guidance). The source name is for internal
tracking only. Never quote the header line itself back to the user.

No citations in the feedback: do not name any study, author, organisation, URL, document title,
or "the knowledge base", and do not write "according to", "research shows", "as noted in", or
any similar attribution. Use the facts from the Context as plain statements in your own words.
The reader should see coaching, not a literature review.

Translation rule - applies to every word you write, not just the "What it is" bullet. The
Context is written by and for researchers; it is what you reason FROM, not a phrasebook to
quote. The reader never sees it. Whenever an anatomical or biomechanical term appears in your
answer - in "Why it matters" and "How to fix it" just as much as anywhere else - give its
everyday meaning in the same sentence, or use the everyday meaning instead. Terms that need
this treatment include: posterior pelvic tilt, lordotic / lumbar lordosis, lumbar flexion,
knee extension moment, knee extensor musculature, hip extensors, plantar flexors, lead lower
extremity, lower-extremity segments, biarticular, hypertrophy, brachii, muscular complex,
kinematic, medial knee displacement, supinated, and anything else you would not say out loud
to someone between sets. Examples of the move: "posterior pelvic tilt" -> "your tailbone tucks
under and your lower back rounds"; "maintain a lordotic lumbar position" -> "keep the natural
arch in your lower back"; "a higher knee extension moment" -> "the front of your knee and your
quads absorb more of the work, so the knee starts complaining before your legs do";
"plantar flexors" -> "calves"; "suboptimal hypertrophy" -> "less muscle growth for the same
effort". You may use these bare, no explanation needed: quads, hamstrings, glutes, core, lats,
biceps, triceps, calves, knee, hip, shoulder, lower back.

Write it yourself: never reuse a sentence, a clause, or a distinctive phrase from the Context.
Every fact you take from it has to be re-expressed in your own words before it reaches the
reader. Copying a Context sentence because it is already accurate is the single most common way
this feedback goes wrong - accuracy is not the standard, being useful to this reader is.
  Wrong: "Allowing the spine to flex during a squat compromises back curvature and can lead to
  eventual pain and suboptimal performance."
  Right: "When your lower back rounds under load, your spine takes the strain instead of your
  braced core - that's what shows up as a sore, stiff lower back a day later, and it bleeds
  power out of the bottom of the squat."

Relevance rule: the `re:` label says which error an entry was RETRIEVED for, not that it
describes that error - retrieval is approximate and some entries are near misses. Before
using an entry for an error, check that its text plainly describes that error (or, for a
principle, the correct form that fixes it). Ignore an entry entirely - do not use it,
mention it, or reframe it as related - if it describes a different fault or a different
exercise variant, if it is a study protocol or setup detail with no consequence attached,
or if following it would push the user further into the error being discussed. Using fewer
entries accurately is better than using every entry.

Grounding rule, part 1 - the facts are fixed. When an entry that passes the relevance rule
contains a specific number, percentage, or joint angle that helps the user (a depth target, a
reason the fault matters), state it - without attribution - as part of the explanation or the
fix; those specifics are the most valuable thing you have. Do NOT state any specific number,
percentage, joint angle, study finding, sample size, or date range that does not appear
verbatim in the Context below - even if you recognize the fact or believe it to be true from
your own general knowledge. Your own training knowledge must never substitute for the Context;
if a fact is not in the Context, treat it as unavailable. If the Context has no specifics for
a given error, fall back to general accepted coaching principles, described in general terms
only with no invented numbers.

Grounding rule, part 2 - the wording is never fixed. "Verbatim" above governs numbers and
facts only. It says nothing about phrasing, and it is not permission to quote: reproducing a
Context sentence in order to stay safe is itself a violation of the Translation rule. Keep the
number exactly as given; build the sentence around it yourself. "2 to 3 cm short of contacting
the ground" stays 2 to 3 cm, but it reaches the reader as "drop the back knee until it's about
2-3 cm off the floor - close enough to brush it".

Context from Knowledge Base:
{context}
```

---

## Exercise: Squat — Butt wink

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Butt wink | Lumbar flexion (butt wink): posterior pelvic tilt and rounding of the lower back at the bottom of the squat | 0.032 / 2* | 0.156 / 1* | 0.111 / 2* | 0.116 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Butt wink | source: www.nasm.org/resource-center/blog/training/biomechanics-of-the-squat]
Posterior pelvic tilt ('butt wink') where the pelvis tucks under and the low back rounds at the bottom of a squat.

[mistake | re: Butt wink | source: blog.nasm.org/newletter/squat-form]
Losing lumbar lordosis during the squat movement.

[consequence | re: Butt wink | source: ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN]
Forcing deep hip flexion without accommodating the necessary hip abduction and external rotation causes the pelvis to tilt posteriorly and the lumbar spine to flex.

[principle | re: Butt wink | source: TheBackSquatAProposedAssessment]
The squat requires sufficient spinal mobility to assume and maintain a slight lordotic posture.

[consequence | re: Butt wink | source: TheBackSquatAProposedAssessment]
Allowing the spine to flex during a squat compromises back curvature and can lead to eventual pain and suboptimal performance.

[principle | re: Butt wink | source: TheBackSquatAProposedAssessment]
The individual must maintain a stiffened torso with a neutral, lordotic lumbar position as a safe and optimal squat strategy.

[finding | re: Butt wink | source: TheBackSquatAProposedAssessment]
If the athlete flexes at the spine before 120 degrees of hip flexion when squatting, they may have restriction in the posterior fibers of the iliotibial band or lack of lumbar control.
```

### WITH RAG
### Progress Tracking

Great job on this session—you moved your overall score up from 71 to 76, and your clean reps jumped from 4 up to 6 out of 10. Even better, you completely cleared "Knee valgus" off your error list compared to yesterday. You still have one lingering fault to clean up, but the trend is moving in the right direction.

### Error Breakdown

*   **What it is, in plain words:** Your tailbone tucks under and your lower back rounds at the bottom of the squat, which is often called a "butt wink." This popped up on reps 4, 6, 8, and 9 right as you were descending into the bottom of the movement.
*   **Why it matters:** When your lower back rounds under load, your spine takes the strain instead of your braced core—that's what shows up as a sore, stiff lower back a day later, and it bleeds power out of the bottom of the squat. Plus, if you flex at your spine before reaching 120 degrees of hip flexion, it usually means your hips are running out of room or your lower back isn't staying locked in.
*   **How to fix it:** 
    *   (a) *Cue:* Think about spreading your knees apart slightly and keeping your chest proud as you drop down, making sure your hips and knees work together instead of letting your pelvis slide under.
    *   (b) *Setup change:* Try widening your stance just a fraction or turning your toes slightly further out to give your hips more room at the bottom.
    *   (c) *Drill:* Practice box squats to a height just above where your lower back starts to round, letting you build awareness of your bottom range without losing your arch.
    *   (d) *Self-check:* Set up your phone from the side and watch the video to see if your lower back stays flat right until you start pushing back up, or if your tailbone dips underneath you.

### Next Session Plan

*   **Keep your knees steady:** Carry over whatever you did today to beat knee valgus and lock that in as your new baseline.
*   **Watch the depth on later reps:** Since your lower back rounding clustered in the second half of the set (reps 8 and 9), focus on keeping your torso rigid even as fatigue sets in.
*   **Trim the depth if needed:** If you can't hit rock bottom without your lower back rounding, stop your descent just an inch or two higher until your hip mobility catches up.

### WITHOUT RAG
### Progress Tracking
Great movement in the right direction today. You pushed your overall score up from 71 to 76, and your clean reps jumped from 4 up to 6 out of 10. Even better, you completely wiped out the knee valgus (knees caving in) that showed up in your last session. You still have one lingering habit to iron out—"Butt wink" popped up on reps 4, 6, 8, and 9 during the descent—but your baseline form is getting noticeably sharper.

***

### Error Breakdown

- **What it is, in plain words:** As you lower yourself into the squat on reps 4, 6, 8, and 9, your tailbone tucks under and your lower back rounds right at the bottom of the movement.
- **Why it matters:** When your lower back rounds under load, your spine takes the strain instead of your braced core—that's what shows up as a sore, lower back a day later, and it bleeds power out of the bottom of the squat.
- **How to fix it:** 
  - (a) **Cue:** Think about proudly showing off the logo on your chest and keeping your chest up as you push your hips back.
  - (b) **Setup:** Shorten your depth slightly on your next set—don't dive past the point where your lower back starts to round. 
  - (c) **Drill:** Practice bodyweight box squats to a slightly higher box so you can find the exact depth where your spine stays flat before you hit the floor.
  - (d) **Self-check:** Set your phone up to record from the side; if you can see the gap at your lower back disappear or your hips tuck under at the bottom, cut the depth by an inch on the next rep.

***

### Next Session Plan

1. **Protect your lower back early:** Keep your core braced tight from the very first rep, and focus on stopping your descent the exact moment your lower back wants to round.
2. **Hold the knee stability:** You fixed the knee caving issue from last session, so keep trusting that same wide, stable knee drive on every single rep today.

---

## Exercise: Squat — Knee valgus

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Knee valgus | Knee valgus: knees caving inward (medial knee displacement) during the squat | 0.034 / 3* | 0.045 / 1* | 0.091 / 2* | 0.090 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Knee valgus | source: Altered_Knee_and_Ankle_Kinemat]
Allowing the knees to cave inward (medial knee displacement) during the squat.

[mistake | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
Allowing the knees to collapse inward, also known as medial knee displacement, during the squat.

[mistake | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
Allowing the knees to cave inward medially during the squat.

[finding | re: Knee valgus | source: TheBackSquatAProposedAssessment]
Knee valgus is identified when the medial aspect of either knee passes the medial malleolus from the anterior perspective during any phase of the squat.

[principle | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
Avoiding medial knee displacement ensures that the rectus femoris remains active during the descent into peak knee flexion.

[consequence | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
A poorly performed squat with increased knee valgus may expose the lower extremity joints to excessive torques.

[principle | re: Knee valgus | source: Muscle Activation Patterns During Different Squat Techniques]
Maintain neutral lower extremity alignment during the squat to properly attenuate patellofemoral forces and stabilize the knee joint.

[consequence | re: Knee valgus | source: Effect of hip adductor (Squat)]
Allowing the knees to cave inward (valgus) increases stress on the knee joint.
```

### WITH RAG
### Progress Tracking
Let's look at the numbers from your session compared to yesterday (2026-09-20). Your overall score dropped slightly from 82 to 78, and your correct reps went down from 8 out of 10 to 6 out of 10. The same old issue—knee valgus—is still following you from the previous session, appearing on reps 3, 5, 8, and 10. 

### Error Breakdown

* **What it is, in plain words:** Your knees are caving inward toward each other as you push yourself back up out of the bottom of the squat, rather than tracking straight over your toes.
* **Why it matters:** This puts excessive twisting stress and high forces across your knee joint. For you, that means the joints absorb loads they aren't built to handle, which usually shows up as sharp aches or lingering joint pain around your kneecaps after heavy lifting, while also sapping the raw strength you need to stand back up smoothly.
* **How to fix it:** 
  (a) Cue: Think about actively spreading the floor apart with your feet as you drive upward.
  (b) Setup change: Take a slightly narrower stance or adjust your foot angle so your toes point out just a fraction more to match your natural hip structure.
  (c) Drill: Practice a few bodyweight squats with a looped resistance band placed just above your knees, fighting the band's pull to keep your knees tracking straight.
  (d) Self-check: Watch your phone video and look down—your kneecaps should stay directly in line with your big and second toes on every single rep, especially when you start the push from the bottom.
  *(Note on rep detail: Notice how this fault only popped up on reps 3, 5, 8, and 10—all during the upward push, and mostly as fatigue set in later in the set. That tells us your form holds up fine early on, but your hips and legs get sloppy as you tire.)*

### Next Session Plan
1. **Watch the fatigue:** When you feel your legs getting heavy on the later reps (around rep 6 and beyond), slow down your ascent just a fraction to keep your knees locked in line.
2. **Focus on the push:** Dedicate your warm-up sets to the floor-spreading cue so your glutes are fully awake and ready to keep your knees open before you touch heavier weights.

### WITHOUT RAG
### Progress Tracking

Let's look at how today's squat session stacks up against yesterday. Your overall score dipped slightly from 82 to 78, and your correct reps dropped from 8 down to 6, leaving you with 4 incorrect reps instead of 2. The good news is that knee caving (knee valgus) is still your only recurring issue—meaning you don't have a pile of random form breakdowns to fix. However, it's popping up more often as you fatigue.

***

### Error Breakdown: Knee valgus

*   **What it is, in plain words:** Your knees are caving inward toward each other instead of tracking straight out over your toes, especially as you push yourself back up out of the bottom of the squat.
*   **Why it matters:** This puts a lot of twisting stress on the inside of your knee joints and overworks the inner thighs while your glutes switch off. You'll likely feel a sharp, nagging pinch on the inside or front of your knees later today or tomorrow, and it robs you of power right when you need to drive upward, making heavy weights feel much harder than they should.
*   **How to fix it:** 
    *   (a) *Cue:* Think about driving your knees wide apart as you push out of the bottom, imagining you're trying to spread the floor apart with your feet.
    *   (b) *Setup:* Take a slightly narrower stance or point your toes out a degree or two more to align your joints better with your natural hip socket width.
    *   (c) *Drill:* Loop a light resistance band just above your knees during a warm-up set of bodyweight squats; the band will force your muscles to fight to keep your knees pushed outward.
    *   (d) *Self-check:* Watch your phone video and look down during the ascent—your kneecaps should track directly over your second and third toes the entire way up, never dipping inward.
    *   *Note on rep detail:* Notice that your knees caved exclusively on the *ascending* phase, and specifically on reps 3, 5, 8, and 10—right when fatigue started settling in. This tells us your form breaks down once you get tired, so focus extra hard on driving your knees out on the later reps.

***

### Next Session Plan

1.  **Drop the load slightly if needed:** Give yourself room to own the movement pattern without fatigue forcing your knees inward on the later reps.
2.  **Add a banded warm-up:** Do one or two sets of bodyweight squats with a mini-band around your knees to wake up your outer glutes before touching a barbell.
3.  **Cut the set short if form slips:** If you hit rep 8 and feel your knees start to cave like they did today, rack the weight. Protect the quality of the rep over pushing through junk volume.

---

## Exercise: Squat — Partial squat

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Partial squat | Squatting too shallow, thighs not reaching parallel: partial or quarter squat depth | 0.061 / 2* | 0.196 / 2* | 0.152 / 2* | 0.161 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting to a depth where the top of the thighs do not reach parallel to the ground.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting too shallow, where the athlete does not achieve a depth of thighs at least parallel to the ground.

[consequence | re: Partial squat | source: TheBackSquatAProposedAssessment]
Without squatting to the proper depth, the hamstrings and gluteus muscular complex may not be adequately challenged.

[consequence | re: Partial squat | source: www.healthline.com/health/fitness/deep-squat]
Failing to reach deep squat depth prevents the backs of your thighs from contacting the backs of your calves, which increases the compressive load on your knee joint and may raise the risk of injury.

[principle | re: Partial squat | source: TheBackSquatAProposedAssessment]
At the proper depth, the femurs are slightly past parallel to the ground, hips are back, tibias are positioned vertical, and feet are entirely on the ground.

[principle | re: Partial squat | source: TheBackSquatAProposedAssessment]
Descend until the top of the thigh is at least parallel with the ground and the hip joint is at least level with or slightly below the knee joint.

[finding | re: Partial squat | source: www.healthline.com/health/fitness/deep-squat]
In a standard squat, you only bend down until your thighs are parallel with the ground, with knees bent at around a 90-degree angle.

[finding | re: Partial squat | source: www.healthline.com/health/fitness/deep-squat]
At deep squat depths, the backs of your thighs come into contact with the backs of your calves, which has been shown to decrease the compressive load on your knee joint.
```

### WITH RAG
### Progress Tracking
Good work on this session. Your overall score ticked up to 80 (from 74 last time), and you nailed 6 correct reps instead of 5. Even better, you completely cleared out that butt wink issue from your previous workout. The one thing hanging around is a depth issue on your final reps, but the trend is definitely heading in the right direction.

### Error Breakdown

* What it is, in plain words: You are cutting your depth short on the way down, finishing up with a partial squat rather than getting all the way to parallel. Notice how this only creeps up on reps 7 through 10—fatigue is setting in and making you stop short before your hips drop far enough.
* Why it matters: If you don't drop your hips far enough, your glutes and hamstrings don't get fully challenged. Skipping that bottom range also leaves the backs of your thighs from brushing against your calves, which actually dumps more compressive stress straight onto your knee joints. That means less muscle growth for the effort and a higher chance your knees start barking at you under heavy loads.
* How to fix it: 
  (a) Cue: Focus on actively driving your hips back and down until you feel the bottom of the movement.
  (b) Setup: Slow down your descent speed on the later reps so you have control into the bottom position instead of cutting the corner early.
  (c) Drill: Try a box squat to a parallel target so you have a physical cue telling you when you've hit the correct depth every single rep.
  (d) Self-check: Watch your side-profile phone video and confirm that your hip crease drops level with or slightly below your knee joint before you start pushing back up.

### Next Session Plan
* Keep your first 6 reps locked in with the same solid depth you managed early in this set, and stop the set one rep before fatigue makes you cut your depth short.
* Slow down your tempo on the descent during your working sets so you don't rush the bottom position when tiredness creeps in.

### WITHOUT RAG
### Progress Tracking
Great work stepping up to the bar today. You improved your overall score from 74 to 80, and bumped your clean reps from 5 up to 6. Even better, you completely cleared out the "Butt wink" error that showed up in your previous session—that lower back rounding at the bottom is gone. The 4 missed reps today all came down to one specific issue: cutting your depth short on the way down, specifically happening on reps 7 through 10 as fatigue set in.

---

### Error Breakdown

*   **Partial squat**
    *   **What it is, in plain words:** You're stopping short on the descent, cutting the movement off before your hips drop below parallel.
    *   **Why it matters:** When you cut your depth short, your quads and glutes miss out on the full stretch and contraction they need for maximum muscle growth, and you end up cheating yourself out of the strength gains you earned. As you load up heavier weight, short-changing the bottom of the movement makes it harder to build balanced leg power.
    *   **How to fix it:** 
        (a) Cue yourself to "sit between your knees" and actively chase that deep pocket at the bottom. 
        (b) Widen your stance slightly or point your toes out a touch more if your hip mobility is fighting you on the descent. 
        (c) Practice box squats to a parallel target so you have a physical cue telling you when you've hit proper depth. 
        (d) Set up your phone from the side view and check that your hip crease clearly dips below your kneecap before you drive back up.
    *   **Use the rep detail:** This error only popped up on the last four reps (reps 7 through 10) as you started fatiguing, so focus on maintaining your focus and depth when the set gets hard, or cut the set one rep short if your form starts to fade.

---

### Next Session Plan
1. **Hold your depth early:** Nail those first few reps just like you did today, but keep that same strict depth focus into the back half of the set.
2. **Beat the fatigue fade:** On reps 7 through 10, consciously slow down your descent slightly to make sure you hit full depth instead of rushing the turnaround.
3. **Keep the win:** Celebrate clearing up that lower back rounding from last time—your bracing is working, so keep that locked in.

---

## Exercise: Push-up — Hip sag

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Hip sag | Allowing the hips to sag during the push-up | 0.048 / 1* | 0.180 / 2 | 0.129 / 2* | 0.143 / 1* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Hip sag | source: blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement]
Allowing the low back to arch or sag during the push-up as fatigue sets in.

[consequence | re: Hip sag | source: blog.nasm.org/fitness/exercise-progressions-and-regressions-how-tos-of-scaling-movement]
Allowing the low back to arch or sag during a push-up decreases engagement of the deeper core stabilizers, increases involvement of the lumbar erectors, and increases stress on the vertebral discs.

[consequence | re: Hip sag | source: www.nasm.org/resource-center/exercise-library/push-up]
Allowing the hips to sag indicates core disengagement and reduces exercise effectiveness.

[principle | re: Hip sag | source: The_Effect_of_Position_on_the_Percentage_of_Body.992962]
Maintain a rigid spine and lower-extremity segments throughout the push-up movement.

[finding | re: Hip sag | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
The push-up cycle was standardized using a metronome to fix the repetition rate at 2 seconds, starting from the top position.

[finding | re: Hip sag | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
During shoulder-width push-ups, the elbow extension angle was 164.99 ± 3.09 degrees and the flexion angle was 96.91 ± 6.20 degrees.
```

### WITH RAG
### Progress Tracking
Good news on the score front: your overall score ticked up from 72 to 77, and you banked 6 correct reps today compared to 5 in your previous session on September 20. Even better, you completely cleared "Partial range of motion" off the board—that fault is gone. You still ran into "Hip sag" on 4 reps (reps 6, 7, 9, and 10), typically as fatigue crept in toward the back half of your set. 

***

### Error Breakdown: Hip sag

* **What it is, in plain words:** Your lower back arches and your hips drop toward the floor as you lower yourself or push back up, making your torso look like a sagging hammock instead of a straight plank.
* **Why it matters:** When your hips drop, your deep core muscles switch off, forcing your lower back muscles to take the strain and loading up your spinal discs. That translates to a dull ache in your lower back by the time you finish your set, and it wastes the effort you should be putting into your chest and arms.
* **How to fix it:**
  * **(a) Cue:** Think about squeezing your glutes hard and pulling your belly button up toward your ribs to lock your midsection in place before you even bend your elbows.
  * **(b) Setup:** Drop your knees to the floor for your sets as soon as you feel your hips start to drift downward on rep 6—do not grind through reps with a broken lower back position.
  * **(c) Drill:** Practice a front plank on your elbows for 20-30 seconds between sets to recalibrate what a completely straight, braced torso feels like.
  * **(d) Self-check:** Glance in the mirror from the side, or prop your phone up to record a set; your shoulders, hips, and ankles should move as one solid piece with zero dip in the middle.

***

### Next Session Plan
1. **Stop the set earlier:** Cut your working sets off the exact second your hips start to sag on the way down—usually around rep 5 or 6 based on today—rather than fighting through reps 9 and 10 with poor form.
2. **Prioritize plank tension:** Spend 60 seconds bracing your abs and glutes before your first rep to set the right muscle memory from the very start.

### WITHOUT RAG
### Progress Tracking

Good movement on the scoreboard today. Your overall score ticked up from 72 to 77, and you banked 6 correct reps compared to 5 in your last session. Even better, you completely cleared "Partial range of motion" off your error list—every rep you performed today hit the full depth target. You still battled "Hip sag" on 4 reps (reps 6, 7, 9, and 10), but overall, you're moving in the right direction. Let's lock in that mid-set form so you can finish strong.

***

### Error Breakdown

* **Hip sag**
  - **What it is, in plain words:** Your hips are dropping toward the floor as you move, turning your push-up into a banana shape instead of keeping your whole body rigid like a plank.
  - **Why it matters:** When your midsection gives out, your lower back takes the brunt of the load instead of your braced core and chest. That's what leaves you with a dull, nagging ache in your lower back after your workout, and it robs your upper body of the stable platform it needs to push hard.
  - **How to fix it:** 
    (a) **Cue:** Squeeze your glutes hard and brace your abs like someone is about to poke you in the stomach. 
    (b) **Setup change:** Drop your feet slightly wider apart to widen your base of support, and shorten your sets by stopping at rep 5 before fatigue makes your hips drop. 
    (c) **Drill:** Drop to your knees for a few strict reps to recalibrate the feeling of a flat, braced spine before going back to your toes. 
    (d) **Self-check:** Keep your phone camera at a side angle; your shoulders, hips, and heels should form one straight, unbroken line from top to bottom.
  - **Use the rep detail:** This error started creeping in late in the set—showing up on the descent for reps 6, 7, and 10, and on the way back up on rep 9. That tells us fatigue is your main enemy here; your core simply gives out once you cross the halfway mark.

***

### Next Session Plan

1. **Cap your sets at 5 reps:** Since your form started breaking down at rep 6, stop your working sets at 5 clean reps for today. Build your endurance with quality over quantity.
2. **Set a wider base:** Take a slightly wider stance with your feet right from the setup to give yourself a more stable platform and protect your lower back as you fatigue.
3. **Prioritize the glute squeeze:** Make squeezing your glutes the very first thing you do before your arms even start to bend.

---

## Exercise: Push-up — Partial range of motion

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Partial range of motion | Not lowering deep enough: incomplete elbow flexion, failing to reach 90 degrees during the push-up | 0.079 / 1* | 0.186 / 2* | 0.154 / 2* | 0.139 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Partial range of motion | source: 10-week suspension and traditional push-up training]
Failing to acquire the correct depth of 90 degrees of elbow flexion.

[principle | re: Partial range of motion | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
Achieving deeper elbow flexion during push-ups increases the mechanical load and muscular demand on the triceps.

[principle | re: Partial range of motion | source: 10-week suspension and traditional push-up training]
Ensure the correct depth of 90 degrees of elbow flexion is acquired during each repetition.

[consequence | re: Partial range of motion | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
Restricting the range of motion during narrow-width push-ups develops and concentrates the load on the elbow joint.

[consequence | re: Partial range of motion | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
Failing to reach deep elbow flexion reduces the mechanical load and contractile demand placed on the triceps muscle.

[finding | re: Partial range of motion | source: 10-week suspension and traditional push-up training]
The study protocol monitored body form and required repetitions to be repeated if the correct depth of 90 degrees was not acquired.

[finding | re: Partial range of motion | source: www.nasm.org/resource-center/exercise-library/push-up]
Descend until your chest nearly touches the floor or your elbows bend to approximately 90 degrees.
```

### WITH RAG
### Progress Tracking

Compared to your last session on September 20th, your performance took a slight step back. Your overall score dipped from 80 to 78, and your correct reps dropped from 7 down to 6. You logged 4 incorrect reps today compared to 3 previously. The exact same fault from last time—Partial range of motion—showed up again, hitting you on reps 2, 5, 8, and . Notice how it tends to creep in as fatigue sets in during the later half of the set. Let's fix that depth so you get the full benefit of every single rep.

### Error Breakdown

* **What it is, in plain words:** You're cutting the push-up short on the way down, stopping well before your chest or arms reach the right depth.
* **Why it matters:** When you don't bend your elbows enough on the descent, your triceps miss out on the mechanical load and muscle-building work they're supposed to be doing, shifting an unfair amount of stress onto your elbow joints instead. That means less actual muscle growth for the effort you're putting in, and your arms won't develop evenly.
* **How to fix it:** 
  (a) Think about bringing your chest all the way down to the floor on every single descent. 
  (b) Set your hands firmly and lower your body until your elbows bend to approximately 90 degrees. 
  (c) Practice on an elevated surface like a sturdy box or bench if you need a lighter regression to hit full depth consistently without stalling. 
  (d) Set your phone up to record from the side so you can check if your elbows hit a square 90-degree angle at the bottom.

### Next Session Plan

* **Prioritize full depth from rep one:** Don't let early comfort trick you into shallow reps. Aim to hit that 90-degree elbow bend right from the start.
* **Watch out for fatigue:** Since your depth started failing on reps 2, 5, 8, and 10, stay extra strict on your form as the set drags on. If your chest starts stopping halfway, cut the set short rather than grinding out shallow reps.
* **Review your video:** Take a quick side-profile video on your working sets to make sure your arms are bending all the way.

### WITHOUT RAG
### Progress Tracking
Let's look at how this session stacked up against yesterday's workout. Your overall score dipped slightly from 80 down to 78, and your clean reps dropped from 7 to 6 out of 10. The familiar issue—partial range of motion—showed up again, appearing on reps 2, 5, 8, and 10. The good news is that your clean reps (like 1, 3, 4, 6, 7, and 9) still look solid, but consistency is slipping as fatigue sets in. 

---

### Error Breakdown

*   **What it is, in plain words:** You are cutting your push-ups short on the way down, stopping well before your chest gets close to the floor.
*   **Why it matters:** When you shorten the drop, your chest and triceps do less of the actual work, cheating you out of muscle growth for the effort you're putting in. It also makes your rep counts unreliable because you're moving through a smaller distance each time. As you start chasing higher reps or adding tougher variations, that shallow dip will catch up to you and stall your progress.
*   **How to fix it:** 
    *   (a) *Cue:* Think about pulling your shoulder blades together on the way down and actively hunting for the floor with your chest.
    *   (b) *Setup:* Keep your hands positioned right under your shoulders and widen your stance slightly to give your upper body a more stable platform to lower itself onto.
    *   (c) *Drill:* Drop to an incline push-up on a sturdy bench or box if you need to build the strength to lower your chest all the way to a target without collapsing.
    *   (d) *Self-check:* Watch a video of your set from the side and confirm that your chest actually reaches the bottom position before you press back up.
*   *Use rep detail:* This error popped up exclusively on the descending phase and struck on the later reps (2, 5, 8, and 10), which tells us fatigue is making you cut corners as the set goes on. 

---

### Next Session Plan
1. **Target the depth:** Commit to hitting the exact same bottom position on every single rep, especially when fatigue starts creeping in on reps 8 through 10.
2. **Slow the descent:** Take a deliberate two-second count on the way down to keep yourself honest about your range of motion rather than rushing the drop. 
3. **Cut the set short if form drops:** If you hit rep 8 and feel yourself shortening the stroke again, stop the set right there with clean form rather than grinding out shallow reps.

---

## Exercise: Lunge — Excessive forward trunk lean

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Excessive forward trunk lean | Leaning the torso forward, excessive trunk lean during the lunge | 0.072 / 3* | 0.142 / 2* | 0.122 / 2* | 0.112 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Excessive forward trunk lean | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Allowing the upper torso and lower leg to shift too far forward during the lunge, which increases front knee loading.

[mistake | re: Excessive forward trunk lean | source: KritzCroninHume2009BodyweightlungeSCJ]
Allowing the thoracic spine to flex during the lunge, which is often associated with poor or imbalanced trunk extensors.

[mistake | re: Excessive forward trunk lean | source: Comparison_of_the_VMOVL_EMG_Activity_Ratio_Accordi]
Leaning the torso forward during the lunge instead of keeping the upper body upright.

[principle | re: Excessive forward trunk lean | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
Maintain an upright trunk during the lunge to avoid excessive forward or lateral trunk movement.

[principle | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Performing a forward lunge with the trunk forward increases the recruitment of the hip extensors.

[consequence | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Leaning the trunk forward during a lunge increases the range of hip and trunk flexion, which shifts the body's center of mass forward and increases weight bearing on the lead lower extremity.

[consequence | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Leaning the trunk forward during a lunge shifts the muscular demand, increasing the load on the hip extensors and ankle plantar flexors while reducing the load on the knee extensors.

[finding | re: Excessive forward trunk lean | source: Altered movement strategy during functional movement after an ACL injury, despite ACL reconstruction]
In a study of 12 ACL-injured patients and 15 controls, the standardized forward lunge protocol required flexing the front knee to approximately 90 degrees while keeping the upper body perpendicular to the ground.

[finding | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Performing a forward lunge with the trunk forward (LTF) is characterized by an increase in hip extensor impulse and a concomitant increase in the muscular actions of the hip extensors when compared to a normal lunge (NL).
```

### WITH RAG
### Progress Tracking
Solid work today—you've moved in the right direction since yesterday. Your overall score ticked up from 70 to 78, and you nailed 6 correct reps compared to just 4 in your previous session. Even better, you completely cleared the "Shallow lunge" fault off your board. You only have one remaining error to clean up now, so let's lock that in for the next session.

***

### Error Breakdown

*   **What it is, in plain words:** You're letting your upper body pitch forward toward your front knee as you move, rather than keeping your torso tall and stacked over your hips. This happened on reps 1, 3, 7 on the way down, and rep 5 on the way back up.
*   **Why it matters:** Leaning forward shifts your center of mass and loads up your hips and calves while taking the work away from your quads. For you, that means your glutes and lower back end up absorbing extra strain they shouldn't be handling, which robs your front leg of the power it needs and leaves your lower back feeling stiff and tired the next day.
*   **How to fix it:**
    *   (a) *Cue:* Think about keeping your chest proud and "shining your chest" straight at the wall in front of you through every inch of the step.
    *   (b) *Setup:* Slow down your step forward and keep your stride length slightly shorter so your torso has less physical room to fall forward.
    *   (c) *Drill:* Drop the loaded weight entirely and do bodyweight lunges with your hands crossed over your shoulders, focusing purely on keeping your spine vertical.
    *   (d) *Self-check:* Glance in a side mirror or set your phone up; your upper body should stay roughly perpendicular to the floor from start to finish, rather than tipping over your front thigh.

***

### Next Session Plan
1. **Pace the descent:** Slow down the first half of every rep—your trunk lean is sneaking in most often on the way down, so taking an extra second to lower yourself will keep your torso upright.
2. **Target clean reps:** Aim to push your correct rep count from 6 up to 8 by treating every single rep like a fresh set, resetting your posture before you step.

### WITHOUT RAG
### Progress Tracking

Great work on this session—you moved your overall score up from 70 to 78 and nailed 6 correct reps compared to just 4 in your last workout. Even better, you completely cleared the shallow lunge error from yesterday. The only issue hanging around is excessive forward trunk lean, which showed up on reps 1, 3, 5, and 7. Let's get that torso locked in and make the next session even sharper.

---

### Error Breakdown

* **What it is, in plain words:** You're tipping your upper body too far forward as you drop into the lunge or push back up, folding at the hips instead of keeping your chest tall.
* **Why it matters:** When your chest collapses forward, your lower back and hips have to take over the work your front leg and glutes should be doing. That means you'll feel it more in your lower back as tightness or fatigue, you miss out on leg muscle growth for the effort you're putting in, and as the weight gets heavier, you risk tweaking your lower back.
* **How to fix it:** 
  *(a) Cue:* Think about keeping your chest proudly pointed at the wall in front of you the entire time.
  *(b) Setup:* Slow down your tempo on the way down so you have more control over your posture before you change direction.
  *(c) Drill:* Drop the load entirely and practice bodyweight lunges with your hands crossed over your opposite shoulders to force your torso upright.
  *(d) Self-check:* If you film your set from the side, your torso angle should stay nearly vertical rather than spilling forward over your front thigh.

---

### Next Session Plan

1. **Start slower:** Take an extra beat on the descent for your first few reps to lock in your chest position before speed takes over.
2. **Target rep 5:** Watch out for your torso tipping on the way up, specifically around the middle of your set when fatigue starts creeping in.
3. **Check your posture:** Keep your chest proud and focus on driving straight up through your front foot rather than pitching forward.

---

## Exercise: Lunge — Shallow lunge

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Shallow lunge | Shallow lunge: step too short, insufficient front knee flexion, front knee not reaching 90 degrees | 0.059 / 3* | 0.110 / 2* | 0.120 / 2* | 0.127 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Shallow lunge | source: mxn167Sp24]
Using an insufficient step length during the lunge.

[mistake | re: Shallow lunge | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Performing a shallow lunge where the front knee flexion angle only reaches 80 degrees, which increases knee joint displacement and extensor moments.

[mistake | re: Shallow lunge | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Performing a shallow lunge with only 80 degrees of knee flexion, which increases the knee extensor moment compared to deeper lunges.

[finding | re: Shallow lunge | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
The holding phase of a forward lunge requires participants to maintain body position at approximately 90 degrees of front knee flexion.

[consequence | re: Shallow lunge | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
A shallower lunge of 80 degrees of knee flexion generates a higher knee extension moment, which increases the mechanical demand on the knee extensor musculature.

[consequence | re: Shallow lunge | source: Influence of the Exhaustion of the Gluteus Medius on the Knee Adduction Moment During Forward Lunge Exercise]
Using a shorter step length (shallow lunge) limits the recruitment and activation of the gluteus medius muscle.

[principle | re: Shallow lunge | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
During the descending phase of the lunge, the front knee should be flexed to approximately 90 degrees.

[principle | re: Shallow lunge | source: mxn167Sp24]
Using a longer step length during a lunge helps minimize anterior tibial translation over the toes and reduces joint forces.

[finding | re: Shallow lunge | source: lunge_knowledge]
In the study's specific lunge protocol, the forward knee was flexed to 45 degrees while the rear knee remained in full extension with both heels in contact with the floor.
```

### WITH RAG
### Progress Tracking

Good movement on this session—you bumped your correct reps up to 6 (from 5 last time) and nudged your overall score to 77. Even better, you completely cleared "Insufficient back knee flexion" off your board. That error is gone. The one remaining leak is "Shallow lunge," which popped up on reps 2, 4, 6, and 9 during the descent. Let's iron that out so you can nail the full set next time.

### Error Breakdown

*   **What it is, in plain words:** You're cutting the lunge short on the way down instead of dropping deep into the stance.
*   **Why it matters:** Stopping too high forces the front of your knee and your quads to absorb a much higher mechanical demand, while starving your side glutes of the work they need to be doing. For you, that means your front knee starts complaining and burning out long before your legs are actually done working, and you miss out on building solid hip stability.
*   **How to fix it:** 
    *   (a) *Cue:* Think about dropping straight down toward the floor rather than stepping forward into a shallow dip.
    *   (b) *Setup change:* Take a slightly longer stride on your initial step out so you have the room to sink cleanly into the bottom position.
    *   (c) *Drill:* Slow down your tempo on the way down, pausing for a one-second count when your front knee hits about 90 degrees of bend before pushing back up.
    *   (d) *Self-check:* Glance in the mirror sideways or catch it on your phone—at the bottom of the rep, your front knee should form a square right angle, and your back knee should hover just above the deck.
*   **Use the rep detail:** Notice that your shallow reps (2, 4, 6, and 9) are happening every other rep, usually as fatigue sets in mid-set. When your legs get heavy, don't rush the descent—stay disciplined on every single drop, or rack the weight a rep earlier if your depth starts slipping.

### Next Session Plan

1. **Take a longer first step:** Focus on a slightly bigger stride right out of the gate so your body naturally has the space to reach proper depth without feeling jammed.
2. **Control the descent:** Slow down on your way down and aim for that crisp 90-degree bend at the front knee on every rep, especially as you get tired in the second half of the set.
3. **Use a phone check:** Prop your phone up to record a side-profile view of one set to verify your bottom position before moving up in weight.

### WITHOUT RAG
### Progress Tracking
Great job out there today! You bumped your overall score up to 77 (from 75 yesterday) and hit 6 correct reps instead of 5. Even better, you completely cleared out the "Insufficient back knee flexion" fault from your previous session. You still have one stubborn error hanging around—"Shallow lunge"—which popped up on reps 2, 4, 6, and 9. Let's get that depth dialed in so you can string together a completely clean set next time.

***

### Error Breakdown: Shallow lunge

* **What it is, in plain words:** You're cutting the movement short on the way down and not dropping your hips far enough into the bottom position.
* **Why it matters:** When you cut the depth short, your front leg and glutes don't get taken through their full working range, which means less muscle growth and strength development for the effort you're putting in. You'll feel like you're working hard, but you're robbing yourself of the full benefit of the exercise.
* **How to fix it:** 
  *(a) Cue:* Think about dropping straight down toward the floor rather than lunging forward.
  *(b) Setup:* Shorten your stride slightly if you feel pinned, or slow down the descent on your middle reps (2, 4, 6, and 9) where fatigue tends to make you cut the range short.
  *(c) Drill:* Try bodyweight deficit lunges standing on a small plate to give yourself a clear target for depth.
  *(d) Self-check:* Glance in a mirror or check your phone video to confirm your back knee gets close to brushing the floor on every single descent.

***

### Next Session Plan
1. **Pace the set:** Focus extra attention on reps 2, 4, 6, and 9, as fatigue is creeping in and causing you to cut those specific descents short.
2. **Commit to the drop:** Keep your torso upright and consciously lower your hips further into the bottom position on every rep to match your clean reps (1, 3, 5, 7, 8, and 10).

---

## Exercise: Lunge — Insufficient back knee flexion

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Insufficient back knee flexion | Insufficient back knee flexion: rear knee not lowering toward the floor during the lunge | 0.060 / 1* | 0.108 / 2* | 0.103 / 2 | 0.106 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Insufficient back knee flexion | source: Influence of the Exhaustion of the Gluteus Medius on the Knee Adduction Moment During Forward Lunge Exercise]
Loss of full range of motion during the lunge, such as failing to lower the rear knee to ankle height.

[consequence | re: Insufficient back knee flexion | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
A shallower lunge of 80 degrees of knee flexion generates a higher knee extension moment, which increases the mechanical demand on the knee extensor musculature.

[consequence | re: Insufficient back knee flexion | source: Altered movement strategy during functional movement after an ACL injury, despite ACL reconstruction]
Knee valgus and excessive side-to-side knee movement during the lunge raise concern regarding the potential increased risk of a knee injury.

[principle | re: Insufficient back knee flexion | source: KritzCroninHume2009BodyweightlungeSCJ]
The back knee should be flexed during the lunge.

[finding | re: Insufficient back knee flexion | source: lunge_knowledge]
In the study's specific lunge protocol, the forward knee was flexed to 45 degrees while the rear knee remained in full extension with both heels in contact with the floor.

[principle | re: Insufficient back knee flexion | source: lunge_knowledge]
Both the anterior and posterior legs should achieve a knee joint range of motion of 0 to 90 degrees during the lunge.

[finding | re: Insufficient back knee flexion | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
The target depth for the trailing knee was defined as 2 to 3 cm short of contacting the ground.
```

### WITH RAG
### Progress Tracking

Your overall score dipped slightly from 81 to 78, and you landed 6 correct reps today compared to 7 in your previous session. That means 4 of your reps missed the mark—specifically reps 5, 7, 8, and 10—all due to the same issue we saw last time: insufficient back knee flexion. The good news is your first four reps and rep 9 were locked in, showing you have the strength and balance to nail this movement. The fatigue creeping into the second half of the set is where the depth started to drop off.

### Error Breakdown

*   **What it is, in plain words:** On your way down during reps 5, 7, 8, and 10, your back leg stays too stiff, and your rear knee stops short instead of dropping down toward the floor.
*   **Why it matters:** Stopping short of full depth puts a much higher demand on the front of your knee and your quads, meaning your front leg absorbs extra mechanical stress while your glutes and hamstrings don't pull their fair share of the weight. As you start adding heavier loads in future sessions, that extra strain on the front knee joint can lead to nagging soreness and joint irritation.
*   **How to fix it:** 
    (a) Cue yourself to "drop straight down" rather than stepping forward into a shallow lunge. 
    (b) Adjust your setup by slowing down your tempo on the descent, giving yourself an extra beat to lower your hips fully. 
    (c) Practice bodyweight split squats where you focus entirely on dropping the back knee vertically without moving your feet. 
    (d) Watch your side-profile video to check that your back knee reaches a target of 2 to 3 cm short of contacting the ground—close enough to brush the floor.
*   **Use the rep detail:** Notice how this fault only popped up on reps 5, 7, 8, and 10 as fatigue set in. Instead of grinding out sloppy reps when your legs get tired, cut your set short a couple of reps earlier to keep your movement crisp.

### Next Session Plan

*   **Pace your reps:** Slow down your descent on every single repetition, especially in the second half of the set, to make sure you hit your depth before pushing back up.
*   **Cap your set length:** Stop the set the moment you feel your back leg start to lock out early, preserving clean form over junk volume.
*   **Target the floor:** Focus on bringing your back knee down until it is just 2 to 3 cm off the floor on every rep.

### WITHOUT RAG
### Progress Tracking

Let's look at how today's lunge session stacked up against yesterday's work. Your overall score dipped slightly from 81 to 78, and your correct reps dropped from 7 down to 6, with incorrect reps ticking up from 3 to 4. 

The good news is you're still nailing the majority of your reps (reps 1-4, 6, and 9 were solid), and the persistent issue of "Insufficient back knee flexion" from your previous session is still the only error showing up. However, as you got deeper into the set—specifically on reps 5, 7, 8, and 10—that back knee started staying too straight on the way down. 

---

### Error Breakdown

* **What it is, in plain words:** On your way down into the lunge, your back knee isn't bending enough, leaving your back leg rigid instead of dropping straight toward the floor.
* **Why it matters:** When your back leg stays too straight, your front leg has to absorb almost all of the work and balance, which robs you of the full glute and leg activation you're after. As you get tired in the later reps—like we saw on reps 5, 7, 8, and 10—fatigue sets in, your range of motion shrinks, and your stability starts to wobble.
* **How to fix it:** 
  (a) Think about dropping your back straight down toward the floor on the descent rather than sliding forward. 
  (b) Shorten your stride slightly during your setup if you feel like you're getting trapped in a long, rigid stance. 
  (c) Practice bodyweight lunges with a soft target (like a folded yoga mat) right under where your back knee should hover. 
  (d) Check your phone video from the side to confirm your back shin is pointing straight down at the bottom of the rep.
* **Use the rep detail:** This error only crept in during the second half of your set (reps 5, 7, 8, and 10) as fatigue caught up with you. Prioritize keeping your form crisp once you hit the halfway mark.

---

### Next Session Plan

1. **Watch the fatigue cliff:** Since your back knee started locking up on the later reps today, stop your set one rep *before* your form starts to break down, or take an extra breath at the top before tackling reps 5 and beyond.
2. **Focus on the drop:** Keep the cue "down, not forward" in your head from the very first rep so you groove the proper depth before fatigue sets in.

---

## Exercise: Bicep Curl — Elbow flare

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Elbow flare | Allowing the elbows to flare outward or drift forward away from the body during the curl | 0.046 / 2* | 0.202 / 2 | 0.149 / 1* | 0.184 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Allowing the elbows to pull forward when performing curls.

[mistake | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Allowing the elbows to move from their stationary position near the waist during the curl.

[consequence | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Because the biceps brachii is a biarticular muscle responsible for both elbow flexion and shoulder stabilization, it can cause the elbows to pull forward during curls.

[principle | re: Elbow flare | source: A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve]
The elbows must be kept close to the body during the movement.

[principle | re: Elbow flare | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
Use an elbow stabilizing plate or maintain strict elbow positioning to ensure that the full range of motion of the elbow joint is achieved and to prevent swinging the elbows.

[finding | re: Elbow flare | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
A 21-year-old female performing 3 sets of bilateral dumbbell bicep curls to failure at 30% 1RM (totaling 143 repetitions) developed exertional rhabdomyolysis with a peak creatine kinase (CK) concentration of approximately 12,200 U/L.

[finding | re: Elbow flare | source: The interplay between muscle length, range of motion, and exercise selection a review]
In the preacher curl, the peak of torque and greatest external moment arm occur at approximately 45 degrees to 50 degrees of elbow flexion.
```

### WITH RAG
### Progress Tracking
Great job stepping up your consistency since yesterday. Your overall score ticked up from 73 to 79, and you nailed 6 correct reps today compared to just 4 in your previous session. Even better, you completely cleared "Partial range of motion" off your error list. You only had one fault show up today, and it didn't even start until the second half of your set. 

### Error Breakdown

* **What it is, in plain words:** On reps 6, 8, 9, and 10, your elbows drifted forward and swung out of position as you lifted the weight up. 
* **Why it matters:** Because your biceps cross both your elbow and your shoulder joint, they have to work extra hard to keep your shoulder stable while you curl. When fatigue sets in, letting your elbows creep forward uses your front shoulders to help pull the weight up, taking the load off your biceps. That means less muscle growth for the exact same amount of effort.
* **How to fix it:** 
  * (a) Cue: Imagine your elbows are pinned to the sides of your ribcage by hinges as you lift. 
  * (b) Setup change: Drop your weight slightly on your next set so you can maintain strict form without needing momentum. 
  * (c) Drill: Practice your curls standing with your back and glutes lightly touching a wall to physically block your elbows from drifting forward. 
  * (d) Self-check: Glance in the mirror while you lift—if you see your upper arms swaying or traveling forward as you go up, reset your elbows before starting the next rep.
* **Use the rep detail:** This error only crept in as you got tired, hitting on the last few reps (6, 8, 9, and 10) right in the middle of the lifting phase. Because it's purely a fatigue breakdown, consider cutting your set one rep short of where the swinging starts next time to lock in clean form.

### Next Session Plan
1. **Drop the weight slightly:** Start your next session with a load that lets you keep your elbows glued to your sides for all 10 reps without any forward drift.
2. **Watch the finish:** Keep an eye on your elbow position specifically on the second half of your set when fatigue kicks in. 
3. **Cut the set before form breaks:** If you feel your elbows starting to creep forward around rep 6 again, pause and finish the set there rather than pushing through with sloppy form.

### WITHOUT RAG
### Progress Tracking

Great job on this session—you’re moving in the right direction. Your overall score ticked up from 73 to 79, and you nailed 6 correct reps today compared to just 4 in your previous session on September 20. 

Even better, you completely cleared "Partial range of motion" out of your movement pattern. The only lingering issue to clean up is "Elbow flare," which showed up on 4 reps today (reps 6, 8, 9, and 10), specifically as you lifted the weight up. 

---

### Error Breakdown

*   **What it is, in plain words:** As you curled the weight upward, your elbows drifted forward and away from your sides instead of staying pinned at your ribs.
*   **Why it matters:** When your elbows drift forward, your front shoulders and upper chest jump in to help lift the weight, taking the work away from your biceps. That means less muscle growth for the exact same effort, and as the weight gets heavier, you'll feel your shoulders taking a beating instead of your arms.
*   **How to fix it:** 
    *   (a) Cue: Imagine your elbows are pinned to your ribs by tight springs as you lift.
    *   (b) Setup change: Drop your training weight slightly so you can control the lift without needing body momentum to help your arms.
    *   (c) Drill: Try doing your curls with your back and triceps lightly pressed against a flat wall to physically block your elbows from creeping forward.
    *   (d) Self-check: Watch your form on your phone or in a mirror to ensure your upper arms stay completely vertical and motionless from start to finish.
*   **Use the rep detail:** This error only crept in during the second half of your set (reps 6, 8, 9, and 10) as fatigue set in. Instead of pushing through sloppy reps, stop your set one rep earlier as soon as your elbows start to wander.

---

### Next Session Plan

1. **Keep your elbows pinned:** Focus entirely on keeping your upper arms locked by your sides, especially as you start getting tired in the later reps.
2. **Drop the weight slightly:** Use a slightly lighter load for your next session to ensure your biceps do 100% of the work without needing your shoulders to pitch in.
3. **Stop before form breaks:** Cut your sets off right before your elbows start to flare forward so you only practice clean, high-quality reps.

---

## Exercise: Bicep Curl — Partial range of motion

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Partial range of motion | Failing to achieve complete arm extension at the bottom of the curl and full elbow flexion at the top: partial repetitions with a limited range of motion | 0.065 / 3* | 0.168 / 2* | 0.171 / 2* | 0.142 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Partial range of motion | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
Failing to achieve the full range of motion of the elbow joint during each repetition.

[mistake | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Performing partial range of motion repetitions that restrict the muscle to short muscle lengths, thereby avoiding the fully stretched position.

[mistake | re: Partial range of motion | source: Scandinavian Med Sci Sports - 2014 - Brandner - Unilateral bicep curl hemodynamics  Low‐pressure continuous vs]
Failing to start the movement with the elbow in full extension.

[principle | re: Partial range of motion | source: Scandinavian Med Sci Sports - 2014 - Brandner - Unilateral bicep curl hemodynamics  Low‐pressure continuous vs]
Start the bicep curl with the elbow in full extension and the forearm supinated.

[principle | re: Partial range of motion | source: The_Rest-Pause_Biceps_Curl_Exercise_Effect_on_Biceps_Brachii_Muscle_of_Women_A_Study_of_Mechanical_Responsiveness]
Incorporate isometric pauses at 0 degrees, 90 degrees, and 135 degrees of the range of motion to target isometric contractions of the biceps brachii.

[finding | re: Partial range of motion | source: Optimizing Resistance Training Technique to Maximize Muscle Hypertrophy A Narrative Review]
Partial repetitions at shorter-muscle lengths are not as hypertrophic as partial repetitions at longer-muscle lengths.

[consequence | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Restricting movement to the final range of motion (short muscle lengths) results in suboptimal muscle hypertrophy compared to utilizing the initial range of motion where the muscle is fully stretched.

[consequence | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Failing to train at longer muscle lengths by restricting movement to shorter muscle lengths (final ROM) fails to optimize muscle hypertrophy.

[finding | re: Partial range of motion | source: The_Rest-Pause_Biceps_Curl_Exercise_Effect_on_Biceps_Brachii_Muscle_of_Women_A_Study_of_Mechanical_Responsiveness]
Maximum muscle force was attained at the onset of the t3 movement phase (elbow joint angle increasing from 90 to 135 degrees) and at the onset of the t5 movement phase (elbow joint angle decreasing from 135 to 90 degrees).
```

### WITH RAG
### Progress Tracking

Great to see you moving in the right direction. Your overall score ticked up slightly from 77 to 79, and you nailed 6 correct reps today compared to 5 in your previous session. Even better, you completely cleared the elbow flare issue from your last workout. You still ran into trouble with partial range of motion on reps 3, 4, 7, and 10, but overall your foundation is getting stronger. 

### Error Breakdown

* **What it is, in plain words:** You're cutting the movement short instead of going all the way down to a fully straight arm and a complete stretch at the bottom, or finishing the squeeze at the top. 
* **Why it matters:** When you chop off the bottom half of the rep and keep your muscles in a shortened range, your biceps miss out on the deep stretch they need. That costs you serious muscle growth for the exact same amount of effort in the gym.
* **How to fix it:** 
  *(a)* Cue yourself to reach all the way to the bottom until your arm is completely straight before every single rep. 
  *(b)* Set up with your palms turned facing forward and your arms hanging totally straight at your sides to lock in your starting point. 
  *(c)* Try a pause drill where you deliberately stop with your arm fully straight for a second before curling up. 
  *(d)* Check your phone video and look for a completely straight elbow at the bottom of every rep.

### Next Session Plan

1. **Prioritize the full stretch:** Start every rep from a dead straight arm—no halfway restarts.
2. **Watch the fatigue:** Reps 7 and 10 slipped into partial range, which means fatigue is creeping in. Stop your set one rep earlier if your form starts breaking down.
3. **Hold the clean form:** Keep the great elbow discipline you showed today so elbow flare stays gone for good.

### WITHOUT RAG
### Progress Tracking

Good movement on the numbers today. Your overall score ticked up slightly from 77 to 79, and you hit 6 correct reps compared to 5 in your previous session on September 20th. Even better, you completely cleared "Elbow flare" out of your movement pattern—that fault is gone. You're left with just one issue to clean up: "Partial range of motion," which popped up on reps 3, 4, 7, and 10.

---

### Error Breakdown: Partial range of motion

*   **What it is, in plain words:** You're cutting the movement short instead of going all the way down to a full arm extension or curling all the way up to the top.
*   **Why it matters:** Shortchanging the movement robs your biceps of the full stretch and contraction they need to grow, meaning you're putting in the effort without getting the full muscle-building return. Over time, sticking to partial reps limits your strength gains and leaves overall bicep development on the table.
*   **How to fix it:** 
    *   (a) *Cue:* Focus on squeezing hard at the very top of the curl and fully straightening your arms at the bottom on every single rep.
    *   (b) *Setup change:* Drop the weight slightly if needed so you can control the full range of motion without rushing or cutting corners.
    *   (c) *Drill:* Pause for a full one-second count at the bottom stretch and another one-second count at the top squeeze to force yourself through the complete arc.
    *   (d) *Self-check:* Watch your side profile in the mirror and make sure your arms lock out straight at the bottom and your forearms touch your biceps at the top.
*   **Rep detail note:** This error showed up sporadically on reps 3, 4, 7, and 10—mostly as fatigue crept in during the lift or the lower. Stay mentally locked in as you get deeper into the set.

---

### Next Session Plan

1.  **Prioritize full range of motion:** Keep your arms fully extended at the bottom and fully flexed at the top for every single rep, treating the first rep with the same strictness as the last.
2.  **Manage your fatigue:** Since the partial reps tend to sneak in when you get tired (like on reps 7 and 10), slow your tempo down slightly on the way down to maintain control.
3.  **Hold the line on elbow position:** Keep doing whatever you changed since last time to eliminate elbow flare, and carry that clean form into your next session.

---

## Exercise: Push-up — clean session

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| general principles | Push-up correct technique and biomechanics | — | — | — | 0.176 / 2 |

### Retrieved KB Context (RAG run)
```text
[principle | re: general principles | source: The_Effect_of_Position_on_the_Percentage_of_Body.992962]
Maintain a rigid spine and lower-extremity segments throughout the push-up movement.

[principle | re: general principles | source: Comparison of Muscle Activation and Kinematic Analysis in Narrow-base and Shoulder-width Push-up Variations in Gymnast]
Narrow width push-ups are more effective for targeting the triceps brachii due to the greater internal moment required at the elbow joint.
```

### WITH RAG
### Progress Tracking
Huge step up from yesterday. You pushed your overall score from 84 up to 91, and you nailed every single rep today—all 10 reps were clean, compared to 8 correct and 2 missed reps in your previous session. Even better, both "Hip sag" and "Partial range of motion" completely disappeared from your rep breakdown. You locked in your form and cleared the board.

### Next Session Plan
1. **Hold the standard:** Keep your core locked and your chest hitting your full range of motion right from rep one of your next session, matching the solid mechanics you just showed.
2. **Focus on smooth tempo:** Maintain that steady control through all 10 reps without rushing the descent, making sure every single rep looks as crisp as your tenth one today.

### WITHOUT RAG
### Progress Tracking

Great job today! You knocked out 10 correct reps out of 10 with zero errors, bringing your overall score up to 91 (compared to 84 in your previous session on September 20). Even better, you completely cleared both faults from last time—your hip sag and partial range of motion are completely gone. 

### Next Session Plan

* **Hold the standard:** Keep the exact same body tension and full range of motion you used today as your baseline for your next workout.
* **Keep testing yourself:** Maintain this clean form when you add more reps or sets, making sure your hips don't drop as you start to fatigue.

---


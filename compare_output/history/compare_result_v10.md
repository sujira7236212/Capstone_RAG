# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/mock_sessions.json` |
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

## Exercise: Squat

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Butt wink | Lumbar flexion (butt wink): posterior pelvic tilt and rounding of the lower back at the bottom of the squat | 0.032 / 2* | 0.156 / 1* | 0.111 / 2* | 0.116 / 2* |
| Partial squat | Squatting too shallow, thighs not reaching parallel: partial or quarter squat depth | 0.061 / 2* | 0.196 / 2* | 0.152 / 2* | 0.161 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Butt wink | source: www.nasm.org/resource-center/blog/training/biomechanics-of-the-squat]
Posterior pelvic tilt ('butt wink') where the pelvis tucks under and the low back rounds at the bottom of a squat.

[mistake | re: Butt wink | source: blog.nasm.org/newletter/squat-form]
Losing lumbar lordosis during the squat movement.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting to a depth where the top of the thighs do not reach parallel to the ground.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting too shallow, where the athlete does not achieve a depth of thighs at least parallel to the ground.

[consequence | re: Butt wink | source: ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN]
Forcing deep hip flexion without accommodating the necessary hip abduction and external rotation causes the pelvis to tilt posteriorly and the lumbar spine to flex.

[principle | re: Butt wink | source: TheBackSquatAProposedAssessment]
The squat requires sufficient spinal mobility to assume and maintain a slight lordotic posture.

[consequence | re: Butt wink | source: TheBackSquatAProposedAssessment]
Allowing the spine to flex during a squat compromises back curvature and can lead to eventual pain and suboptimal performance.

[principle | re: Butt wink | source: TheBackSquatAProposedAssessment]
The individual must maintain a stiffened torso with a neutral, lordotic lumbar position as a safe and optimal squat strategy.

[consequence | re: Partial squat | source: TheBackSquatAProposedAssessment]
Without squatting to the proper depth, the hamstrings and gluteus muscular complex may not be adequately challenged.

[finding | re: Butt wink | source: TheBackSquatAProposedAssessment]
If the athlete flexes at the spine before 120 degrees of hip flexion when squatting, they may have restriction in the posterior fibers of the iliotibial band or lack of lumbar control.

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
Great movement on the platform today: your overall score climbed from 73 to 79, and you nailed 6 correct reps compared to just 4 in your previous session. Even better, you completely wiped out knee valgus from your movement pattern—that previous fault is gone. You still had 4 incorrect reps to clean up, driven by a couple of recurring habits, but the trajectory is pointing up.

### Error Breakdown

*   **What it is, in plain words:** On reps 2, 4, and 5, your tailbone tucks under and your lower back rounds at the bottom of the squat, rather than staying locked in.
*   **Why it matters:** When your lower back rounds under load, your spine takes the strain instead of your braced core—that's what shows up as a sore, stiff lower back a day later, and it bleeds power out of the bottom of the squat.
*   **How to fix it:** 
    (a) Think about proudly showing off the logo on your chest and keeping your torso stiff as you drop. 
    (b) Open your stance slightly wider and point your toes out a few degrees to give your hips more room to track without forcing your lower back to fold. 
    (c) Practice bodyweight box squats pausing just above the seat to learn where your personal depth limit is before your pelvis starts to wink. 
    (d) Set up your phone at hip height from the side so you can watch your lower back line on playback—if the curve flattens out at the bottom, you've gone an inch too deep.

*   **What it is, in plain words:** On rep 6, you cut the descent short and stopped before your thighs reached parallel to the floor.
*   **Why it matters:** By cutting your depth short, the backs of your thighs and your glutes miss out on the stretch and challenge they need, and you miss the natural pause where your thighs brush your calves that helps unload stress from your knee joints.
*   **How to fix it:** 
    (a) Focus on actively driving your hips down and back until you feel your hip crease drop level with or slightly below the top of your knees. 
    (b) Slow down your tempo on the way down, taking a full two seconds to hit the bottom position rather than rushing the turnaround. 
    (c) Practice goblet squats with a light kettlebell held at your chest to act as a counterweight, letting you sit lower into the pocket safely. 
    (d) Glance at a side-profile mirror or check your video to confirm the top of your thigh is horizontal or slightly lower before you explode back up.

### Next Session Plan
1. **Pace your warm-ups:** Spend an extra five minutes on hip mobility before touching a barbell so your lower back stays flat when you hit the bottom of the squat.
2. **Watch rep 6's depth:** Commit to hitting full depth on every single working rep instead of letting fatigue cut your range short midway through the set.
3. **Record your working sets:** Film your sets from the side so you can check for any lower back rounding on reps 2, 4, and 5 before adding any weight to the bar.

### WITHOUT RAG
### Progress Tracking

Great to see your numbers heading in the right direction since yesterday. Your overall score bumped up from 73 to 79, and you nailed 6 correct reps today compared to just 4 in your last session. Even better, you completely cleared "Knee valgus" out of your movement pattern—that error didn't show up on a single rep today. You still have a couple of recurring faults to clean up, but the trend is solid.

***

### Error Breakdown

*   **What it is, in plain words:** On reps 2, 4, and 5—happening right as you start heading back up or halfway down—your tailbone tucks under and your lower back rounds at the bottom of the squat.
*   **Why it matters:** When your lower back rounds under load, your spine takes the strain instead of your braced core. That's what leaves you with a sore, stiff lower back the next day, and it leaks power right when you need to drive out of the bottom.
*   **How to fix it:** 
    *   (a) Cue: Think about keeping your chest proud and your belly button braced hard against your belt as you reverse direction.
    *   (b) Setup change: Reduce your depth slightly—stop an inch or two higher before your hips run out of mobility and force your lower back to round.
    *   (c) Drill: Practice bodyweight box squats to a height that lets you hit the bottom without your lower back losing its arch.
    *   (d) Self-check: Watch your phone video from the side and look for your tailbone staying locked in place instead of tucking under at the bottom.
*   **Use the rep detail:** This happened on reps 2, 4, and 5, hitting you mid-set when fatigue started creeping into your core bracing. Focus on resetting your breath tightly before every single rep.

*   **What it is, in plain words:** On rep 6, you cut the movement short on the way down and didn't hit full depth.
*   **Why it matters:** Stopping high means your quads and glutes miss out on the full stretch and workload of the lift, giving you less muscle growth for the exact same amount of effort.
*   **How to fix it:** 
    *   (a) Cue: Think about sinking your hips down between your knees until your thighs pass parallel to the floor.
    *   (b) Setup change: Take a slightly wider stance if it helps you drop your hips comfortably into the pocket.
    *   (c) Drill: Pause for two full seconds at the absolute bottom of a lighter set to teach your body what full depth feels like.
    *   (d) Self-check: Have a gym buddy watch your side profile or check a mirror to confirm your hip crease drops below the top of your knee.
*   **Use the rep detail:** This popped up as a one-off mental slip on rep 6—stay dialed in through the middle of your sets so your depth doesn't drift.

***

### Next Session Plan

1.  **Keep the knees tracking wide:** Whatever you did to fix the knee caving from your last session worked—don't change a thing there, just lock it in.
2.  **Brace harder before the descent:** Protect your lower back on reps 2, 4, and 5 by taking a huge breath into your stomach and tightening your core before you even unlock your knees.
3.  **Commit to full depth:** Make sure rep 6'd short-changing doesn't become a habit by holding yourself to a strict, full-range standard on every rep.

---

## Exercise: Lunge

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Excessive forward trunk lean | Leaning the torso forward, excessive trunk lean during the lunge | 0.072 / 3* | 0.142 / 2* | 0.122 / 2* | 0.112 / 2* |
| Insufficient back knee flexion | Insufficient back knee flexion: rear knee not lowering toward the floor during the lunge | 0.060 / 1* | 0.108 / 2* | 0.103 / 2 | 0.106 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Insufficient back knee flexion | source: Influence of the Exhaustion of the Gluteus Medius on the Knee Adduction Moment During Forward Lunge Exercise]
Loss of full range of motion during the lunge, such as failing to lower the rear knee to ankle height.

[mistake | re: Excessive forward trunk lean | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
Allowing the upper torso and lower leg to shift too far forward during the lunge, which increases front knee loading.

[mistake | re: Excessive forward trunk lean | source: KritzCroninHume2009BodyweightlungeSCJ]
Allowing the thoracic spine to flex during the lunge, which is often associated with poor or imbalanced trunk extensors.

[mistake | re: Excessive forward trunk lean | source: Comparison_of_the_VMOVL_EMG_Activity_Ratio_Accordi]
Leaning the torso forward during the lunge instead of keeping the upper body upright.

[consequence | re: Insufficient back knee flexion | source: Effects of Targeted Knee Flexion Angle on the Biomechanical Factors of Upward and Downward Phases during Forward Lunge]
A shallower lunge of 80 degrees of knee flexion generates a higher knee extension moment, which increases the mechanical demand on the knee extensor musculature.

[consequence | re: Insufficient back knee flexion | source: Altered movement strategy during functional movement after an ACL injury, despite ACL reconstruction]
Knee valgus and excessive side-to-side knee movement during the lunge raise concern regarding the potential increased risk of a knee injury.

[principle | re: Insufficient back knee flexion | source: KritzCroninHume2009BodyweightlungeSCJ]
The back knee should be flexed during the lunge.

[finding | re: Insufficient back knee flexion | source: lunge_knowledge]
In the study's specific lunge protocol, the forward knee was flexed to 45 degrees while the rear knee remained in full extension with both heels in contact with the floor.

[principle | re: Excessive forward trunk lean | source: Effects of Foot Progression Angle and Stance Width on Lower-Limb Muscle Activation During the Holding Phase of Forward Lunge Exercises in Healthy Adults A Randomized Within-Participant Crossover Study]
Maintain an upright trunk during the lunge to avoid excessive forward or lateral trunk movement.

[principle | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Performing a forward lunge with the trunk forward increases the recruitment of the hip extensors.

[principle | re: Insufficient back knee flexion | source: lunge_knowledge]
Both the anterior and posterior legs should achieve a knee joint range of motion of 0 to 90 degrees during the lunge.

[consequence | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Leaning the trunk forward during a lunge increases the range of hip and trunk flexion, which shifts the body's center of mass forward and increases weight bearing on the lead lower extremity.

[consequence | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Leaning the trunk forward during a lunge shifts the muscular demand, increasing the load on the hip extensors and ankle plantar flexors while reducing the load on the knee extensors.

[finding | re: Insufficient back knee flexion | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
The target depth for the trailing knee was defined as 2 to 3 cm short of contacting the ground.

[finding | re: Excessive forward trunk lean | source: Altered movement strategy during functional movement after an ACL injury, despite ACL reconstruction]
In a study of 12 ACL-injured patients and 15 controls, the standardized forward lunge protocol required flexing the front knee to approximately 90 degrees while keeping the upper body perpendicular to the ground.

[finding | re: Excessive forward trunk lean | source: Trunk Position Inﬂuences the Kinematics,Kinetics, and Muscle Activity of the LeadLower Extremity During the ForwardLunge Exercise]
Performing a forward lunge with the trunk forward (LTF) is characterized by an increase in hip extensor impulse and a concomitant increase in the muscular actions of the hip extensors when compared to a normal lunge (NL).
```

### WITH RAG
### Progress Tracking
Good work today. Your overall score ticked up from 70 to 79, and you nailed 7 correct reps out of 10 compared to just 4 in your previous session yesterday. You completely cleared the shallow lunge fault from last time, which shows your depth is improving. You still had a couple of hiccups—"Excessive forward trunk lean" popped up on reps 1 and 3, and "Insufficient back knee flexion" showed up on rep 9—but overall, you're moving better and trusting your legs more.

***

### Error Breakdown

*   **Excessive forward trunk lean**
    *   What it is, in plain words: Your chest caves forward and your torso pitches toward the floor as you step out, rather than staying stacked straight up over your hips. This happened on the way down on rep 1 and on the way back up on rep 3.
    *   Why it matters: Leaning forward shifts your center of mass ahead of your base, throwing extra weight onto your front leg and overloading your hips and calves while taking the work away from your quads. That changes the exercise into something closer to a hinge, costing you the leg muscle development you're aiming for and making your lower back take up the slack to keep you balanced.
    *   How to fix it: 
        (a) Cue: Think "tall spine and chest proud" the second your front foot hits the floor. 
        (b) Setup change: Slow down your tempo on the descent so you have time to catch your balance before your torso starts drifting forward. 
        (c) Drill: Practice bodyweight lunges in front of a wall with your toes a few inches away—if your chest touches the wall on the way down, you're leaning too far. 
        (d) Self-check: Glance in the side mirror and check that your upper body stays completely perpendicular to the floor from start to finish.

*   **Insufficient back knee flexion**
    *   What it is, in plain words: You didn't drop your back knee low enough on rep 9, cutting the bottom of the movement short on the way down.
    *   Why it matters: Cutting your depth short makes your front knee absorb a higher mechanical demand and generates a harsher load on the front of the knee. Over time, that extra stress makes the joint complain before your muscles are even tired, and it robs you of the full range of motion needed for complete leg strength.
    *   How to fix it: 
        (a) Cue: Focus on driving straight down toward the floor rather than lunging forward. 
        (b) Setup change: Aim for a target depth where your back knee drops until it's about 2 to 3 cm short of contacting the ground—close enough to brush it. 
        (c) Drill: Drop to a split squat hold with your back knee hovering just 2-3 cm off the floor for a few seconds to get used to the bottom position. 
        (d) Self-check: Have a training partner watch your back knee on video to confirm it reaches that 2 to 3 cm mark off the floor before you push back up.

***

### Next Session Plan
1. **Prioritise the chest:** Keep your torso upright on every single rep, especially on the first couple where fatigue hasn't set in yet.
2. **Control the depth:** Make sure that back knee consistently drops to that 2-3 cm hover target above the floor on every rep, rather than getting lazy on later reps like rep 9.
3. **Pacing:** Slow your tempo slightly on the descent so you can control both your posture and your depth without rushing the bottom.

### WITHOUT RAG
### Progress Tracking
Great work today! You bumped your overall score up to 79 (compared to 70 in your last session) and nailed 7 clean reps instead of just 4. Even better, you completely cleared out the "Shallow lunge" fault that was giving you trouble previously. You had a couple of hiccups pop up—Excessive forward trunk lean on reps 1 and 3, and Insufficient back knee flexion on rep 9—but the overall trend is heading firmly in the right direction. 

***

### Error Breakdown

*   **What it is, in plain words:** On reps 1 and 3, your chest caves forward and your torso pitches out over your front knee as you move—rep 1 drops forward on the way down, while rep 3 tips forward as you push back up.
*   **Why it matters:** When your torso tips too far forward, your lower back and shoulders have to take over the load instead of letting your front leg and glutes do the heavy lifting. That means you'll likely feel a sharp tightness in your lower back or a weird strain through your upper spine during the set, and you're missing out on the glute and leg muscle growth you're working for.
*   **How to fix it:** 
    (a) Keep your chest proud and imagine a straight string pulling the crown of your head straight up toward the ceiling throughout the rep.
    (b) Take a slightly more upright posture in your starting stance before you even begin moving.
    (c) Practice bodyweight lunges in front of a wall, keeping your torso close enough that your chest doesn't bump the wall as you drop down.
    (d) Glance in the mirror to check that your torso stays upright and vertical rather than folding forward like a hinge.

*   **What it is, in plain words:** On rep 9, your back leg gets lazy on the way down—your back knee barely bends, turning your lunge into more of a front-leg-only exercise.
*   **Why it matters:** If your back knee doesn't drop, your front leg and knee absorb almost all the stress while your back hip and thigh miss out on the work. That means you'll feel a burning fatigue concentrated entirely in the front knee joint instead of spreading the load evenly across both legs, which limits how many solid reps you can trust yourself to do.
*   **How to fix it:** 
    (a) Focus on dropping straight down toward the floor rather than driving forward, letting your back knee bend naturally underneath your hips.
    (b) Shorten your stride length slightly in your setup so your back leg has room to drop vertically.
    (c) Practice static split squats with a slow tempo on the way down to get used to bending that back knee every single time.
    (d) Check your phone video to make sure your back knee is actually dipping toward the floor on every descent instead of staying locked high.

***

### Next Session Plan
1. Keep the momentum going on your torso angle: focus on an upright chest from the very first rep to prevent that forward lean on reps 1 and 3.
2. Pay attention to your stride length so your back knee can actually bend properly, avoiding the lazy back leg seen on rep 9.
3. Stop the set early if your form starts to break down under fatigue, locking in those clean reps to build on today's score.

---

## Exercise: Push-up

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
Huge step up from yesterday. You pushed your overall score from 72 up to 87, and you nailed all 10 reps cleanly with zero errors. More importantly, those stubborn faults from your last session—hip sag and cutting the range of motion short—are completely gone. You locked in your core, kept your body rigid, and hit every single rep with full control from top to bottom. 

### Next Session Plan
* **Hold the standard:** You just proved you own this form, so don't let your standards slip on the very next workout. Treat this clean session as your new baseline.
* **Play with intensity:** Since your movement quality is nailed down, focus purely on maintaining this exact body tension as you add a little more challenge next time—whether that's cleaner tempos or slightly more demanding variations.

### WITHOUT RAG
### Progress Tracking

Fantastic session today! You hit 10 out of 10 correct reps, a solid step up from your 9 correct reps in your previous workout on August 30. Your overall score jumped from 72 to 87, and you completely cleared out both "Hip sag" and "Partial range of motion" from your last session. Every single rep was clean. 

---

### Next Session Plan

1. **Hold the standard:** Keep your core locked as tight as you did today, treating every single rep with the same focus from start to finish.
2. **Maintain depth:** Continue bringing your chest all the way down on every rep without letting your hips drop or your standards slip.

---

## Exercise: Bicep Curl

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | consequence best / kept | principle best / kept |
|---|---|---|---|---|---|
| Elbow flare | Allowing the elbows to flare outward or drift forward away from the body during the curl | 0.046 / 2* | 0.202 / 2 | 0.149 / 1* | 0.184 / 2* |
| Partial range of motion | Failing to achieve complete arm extension at the bottom of the curl and full elbow flexion at the top: partial repetitions with a limited range of motion | 0.065 / 3* | 0.168 / 2* | 0.171 / 2* | 0.142 / 2* |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Allowing the elbows to pull forward when performing curls.

[mistake | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Allowing the elbows to move from their stationary position near the waist during the curl.

[mistake | re: Partial range of motion | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
Failing to achieve the full range of motion of the elbow joint during each repetition.

[mistake | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Performing partial range of motion repetitions that restrict the muscle to short muscle lengths, thereby avoiding the fully stretched position.

[mistake | re: Partial range of motion | source: Scandinavian Med Sci Sports - 2014 - Brandner - Unilateral bicep curl hemodynamics  Low‐pressure continuous vs]
Failing to start the movement with the elbow in full extension.

[principle | re: Partial range of motion | source: Scandinavian Med Sci Sports - 2014 - Brandner - Unilateral bicep curl hemodynamics  Low‐pressure continuous vs]
Start the bicep curl with the elbow in full extension and the forearm supinated.

[consequence | re: Elbow flare | source: www.setforset.com/blogs/news/hammer-curl-vs-bicep-curl]
Because the biceps brachii is a biarticular muscle responsible for both elbow flexion and shoulder stabilization, it can cause the elbows to pull forward during curls.

[principle | re: Partial range of motion | source: The_Rest-Pause_Biceps_Curl_Exercise_Effect_on_Biceps_Brachii_Muscle_of_Women_A_Study_of_Mechanical_Responsiveness]
Incorporate isometric pauses at 0 degrees, 90 degrees, and 135 degrees of the range of motion to target isometric contractions of the biceps brachii.

[finding | re: Partial range of motion | source: Optimizing Resistance Training Technique to Maximize Muscle Hypertrophy A Narrative Review]
Partial repetitions at shorter-muscle lengths are not as hypertrophic as partial repetitions at longer-muscle lengths.

[consequence | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Restricting movement to the final range of motion (short muscle lengths) results in suboptimal muscle hypertrophy compared to utilizing the initial range of motion where the muscle is fully stretched.

[consequence | re: Partial range of motion | source: The interplay between muscle length, range of motion, and exercise selection a review]
Failing to train at longer muscle lengths by restricting movement to shorter muscle lengths (final ROM) fails to optimize muscle hypertrophy.

[principle | re: Elbow flare | source: A_Biomechanical_Analysis_of_Dumbbell_Curl_and_Inve]
The elbows must be kept close to the body during the movement.

[principle | re: Elbow flare | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
Use an elbow stabilizing plate or maintain strict elbow positioning to ensure that the full range of motion of the elbow joint is achieved and to prevent swinging the elbows.

[finding | re: Partial range of motion | source: The_Rest-Pause_Biceps_Curl_Exercise_Effect_on_Biceps_Brachii_Muscle_of_Women_A_Study_of_Mechanical_Responsiveness]
Maximum muscle force was attained at the onset of the t3 movement phase (elbow joint angle increasing from 90 to 135 degrees) and at the onset of the t5 movement phase (elbow joint angle decreasing from 135 to 90 degrees).

[finding | re: Elbow flare | source: Exertional Rhabdomyolysis in a 21-year-old, Healthy Female after Performing Three Sets of the Biceps Curl Exercise to Failure with 30% 1rm A Case Report]
A 21-year-old female performing 3 sets of bilateral dumbbell bicep curls to failure at 30% 1RM (totaling 143 repetitions) developed exertional rhabdomyolysis with a peak creatine kinase (CK) concentration of approximately 12,200 U/L.

[finding | re: Elbow flare | source: The interplay between muscle length, range of motion, and exercise selection a review]
In the preacher curl, the peak of torque and greatest external moment arm occur at approximately 45 degrees to 50 degrees of elbow flexion.
```

### WITH RAG
### Progress Tracking
Good work today—you bumped your overall score up from 75 to 81 and doubled your clean reps from 3 to 6. You also cleaned up most of your form slip-ups early in the set, with reps 1 through 7 looking solid overall. The main thing to tackle now is fatigue setting in toward the end, which is where your remaining errors crept in.

***

### Error Breakdown

*   **Partial range of motion**
    *   *What it is, in plain words:* You cut the movement short on rep 3 instead of going all the way down to a fully straight arm at the start.
    *   *Why it matters:* Sticking only to the top half of the curl skips the fully stretched position where the bicep gets loaded best, leading to less muscle growth for the same effort.
    *   *How to fix it:* 
        (a) Cue yourself to touch your arms straight at the bottom of every single rep. 
        (b) Slow down your negative phase and pause for a split second with your arms fully straight before starting the next curl. 
        (c) Practice bodyweight hangs or very light dumbbell holds with your arms completely straight to get used to that bottom position. 
        (d) Check your phone video to make sure your elbow straightens out completely before you start pulling up.
    *   *Use the rep detail:* This only happened on rep 3 during the lift, likely as you tried to rush into the next movement. Keep your tempo consistent across every rep.

*   **Elbow flare**
    *   *What it is, in plain words:* Your elbows drifted forward and swung away from your waist as you curled the weight up on reps 8, 9, and 10.
    *   *Why it matters:* Because your biceps help stabilize your shoulders as well as bend your elbow, fatigue causes your front shoulders to take over the work. This shifts tension away from your biceps and leaves you with less arm growth to show for your hard work.
    *   *How to fix it:* 
        (a) Cue yourself to glue your elbows to your ribs like they are pinned in place. 
        (b) Lower the weight slightly if your arms start drifting forward by the time you hit the final three reps. 
        (c) Try doing your curls with your back lightly touching a wall so your elbows have a physical barrier stopping them from drifting forward. 
        (d) Watch your form in the mirror on those last few reps to ensure your elbows stay locked by your sides from start to finish.
    *   *Use the rep detail:* This is strictly a fatigue issue, showing up exclusively on the last three reps (8, 9, and 10) as you got tired on the way up. 

***

### Next Session Plan
1. **Fix the finish:** Make it a strict rule to fully straighten your arms at the bottom of every rep, especially as you start getting tired.
2. **Lock your elbows:** Keep your upper arms pinned to your sides, and consider dropping the weight slightly if your elbows start creeping forward on your final 3 reps.
3. **Guard against fatigue:** When you feel your form start to break down on the last few reps, stop the set right there rather than fighting through sloppy form.

### WITHOUT RAG
### Progress Tracking

Solid step forward today. Your overall score ticked up from 75 to 81, and you doubled your clean reps—jumping from 3 correct reps in your last session to 6 today. Even better, you completely cleared out one of your previous habits, as "Partial range of motion" only showed up once (on rep 3) compared to giving you trouble all through the last workout. You've still got one recurring issue to dial in, but the foundation is getting stronger.

***

### Error Breakdown

*   **What it is, in plain words:** You cut rep 3 short before getting the weight all the way up to your shoulders.
*   **Why it matters:** Stopping early cheats your biceps out of the fully contracted position at the top, which means you're leaving muscle growth on the table for that rep and not working the biceps through their complete path.
*   **How to fix it:** 
    (a) **Cue:** Think about driving your knuckles right up toward your collarbones at the top. 
    (b) **Setup change:** Lighten the weight slightly if you need to so you can comfortably reach the top without straining. 
    (c) **Drill:** Try doing a two-second pause at the absolute top of the curl on your next light warm-up set. 
    (d) **Self-check:** Look in the mirror and make sure your forearms are past vertical (closer to your shoulders than straight up) before you start lowering the weight.
*   **Use the rep detail:** This only happened once, on rep 3, so it looks like a momentary slip in focus rather than total fatigue. Just stay intentional from the very start of the set.

*   **What it is, in plain words:** Your elbows drifted forward and away from your sides as you lifted the weight, especially on reps 8, 9, and 10 as fatigue set in.
*   **Why it matters:** When your elbows wander forward, your front shoulders and chest start taking over the work instead of keeping the tension locked entirely on your biceps, which costs you arm strength and can make your shoulder joints cranky over time.
*   **How to fix it:** 
    (a) **Cue:** Glue your elbows to your ribs like they're pinned in place by a belt. 
    (b) **Setup change:** Stand with your back lightly against a wall to physically block your elbows from creeping forward. 
    (c) **Drill:** Practice a set of strict hammer curls against a wall to get used to keeping your upper arms dead still. 
    (d) **Self-check:** Watch yourself in the mirror on your phone video—if you see your elbows travel forward as the weight goes up, that's your cue to reset.
*   **Use the rep detail:** Notice that this fault clustered right at the end of your set (reps 8, 9, and 10), which is classic fatigue breakdown. 

***

### Next Session Plan

1. **Pin your elbows:** Start every set thinking about keeping your upper arms locked against your ribs, especially on the final few reps when form usually starts to slip.
2. **Hit the top:** Commit to a full range of motion on every single rep—don't shortchange yourself at the top.
3. **Cut the set off early if needed:** If your elbows start creeping forward on rep 8 again, rack the weight rather than grinding out ugly reps with poor form.

---


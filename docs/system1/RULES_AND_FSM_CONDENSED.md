# Rule-Based Form Feedback and FSM Rep Counting: Current System Specification

This is the condensed specification of the rule-based exercise system as it currently runs. It
covers rep counting (the FSM) and form feedback (the rules) for four exercises: squat, push-up,
lunge and bicep curl. It holds no history, evidence or open items. Those live in
`docs/rule_based/RULES_AND_FSM.md`.

Synced from code on 2026-09-25 (`src/fsm_counter/`, `src/rule_based/`,
`src/pipeline/placement_guide.py`). If a value here disagrees with the code, the code wins.

## Units and conventions

- Every joint angle is an interior angle in degrees at the middle joint. 180 means the three
  joints form a straight line; smaller means more bent.
- Trunk tilt is the angle in degrees between the hip->shoulder line and the world vertical.
  0 means upright, 90 means horizontal.
- All geometry uses MediaPipe's 3D world landmarks (metres, hip-centred). Only MediaPipe provides
  these coordinates. Some rules still need a specific camera angle to see the body part they
  judge, so each exercise has a camera placement band (see Camera placement).
- A landmark is trusted only when its confidence score is at least 0.3 (`MIN_LM_SCORE`).
- A missing joint angle defaults to 180 (read as straight).

## Summary index

| Exercise | Counting angle | Rep counts when | Rules (priority order) |
|---|---|---|---|
| Squat | mean of both knees | knee angle reaches 120 or below, then returns to 160 or above | knee_depth, knee_valgus, knee_varus, back_straight |
| Push-up | mean of both elbows | elbow angle reaches 110 or below, then returns to 150 or above | body_alignment, elbow_depth |
| Lunge | the more-bent knee | knee angle reaches 105 or below, then returns to 155 or above | front_knee_too_shallow, front_knee_too_deep, torso_upright, back_knee_form |
| Bicep curl | the active arm's elbow | elbow angle reaches 55 or below, then returns to 155 or above | elbow_away, full_rom |

Exercise name aliases (same FSM and same rules):
- Push-up: `pushup`, `diamond_pushup`
- Squat: `squat`
- Lunge: `lunge`, `dumbbell_reverse_lunge`
- Bicep curl: `dumbbell_biceps_curls`, `dumbbell_hammer_curls`, `drag_curl`
- An unknown exercise name falls back to the push-up FSM and the push-up rules.

## Pipeline

1. Each camera frame goes through MediaPipe pose estimation (33 landmarks, 2D and 3D world).
2. Frames flagged low-confidence are skipped, and so are frames before the camera-placement and
   ready-pose gates hand off (when those gates are enabled). Skipped frames never reach the FSM
   or the rules.
3. `extract_exercise_angles(keypoints, is_3d=True)` computes the joint angles.
4. `ExerciseSession.update(angles, keypoints)` runs one frame through both layers:
   - The FSM updates and returns `(rep_count, state, RepEvent)`.
   - The `FormEvaluator` consumes the same angles, the keypoints and the `RepEvent`, and returns at
     most one warning message.
5. If the keypoints carry no real 3D world coordinates (2D-only engines such as MoveNet, YOLOv8 or
   RTMPose), `ExerciseSession.update` raises an error instead of counting. The system requires
   MediaPipe.

The FSM counts reps and knows nothing about form. The rules judge form and know nothing about
counting. The only link between them is the `RepEvent` the FSM emits each frame:
- `NONE`: no rep boundary this frame.
- `REP_STARTED`: an attempt opened (IDLE to CONCENTRIC).
- `REP_ABANDONED`: the attempt ended without reaching counting depth. Not counted.
- `REP_COMPLETED`: the attempt reached depth and returned. Counted.

## Angle definitions

| Angle key | Joints (vertex in the middle) | Used by |
|---|---|---|
| `left_knee` / `right_knee` | hip - knee - ankle | squat and lunge counting, squat and lunge knee rules |
| `left_elbow` / `right_elbow` | shoulder - elbow - wrist | push-up and curl counting, push-up and curl depth rules |
| `left_shoulder_angle` / `right_shoulder_angle` | elbow - shoulder - hip (0 = upper arm along the torso) | curl elbow_away |
| `left_body_alignment` / `right_body_alignment` | shoulder - hip - ankle | push-up body_alignment |
| `thigh_split` | angle between the two hip->knee thigh lines (0 = legs together) | lunge attempt gate |
| trunk tilt (computed in the rules, not an angle key) | hip->shoulder line vs world vertical | squat back_straight, lunge torso_upright, arming posture check |

## FSM rep counting

### How the FSM works (all exercises)

Four states: IDLE, CONCENTRIC (going down), INFLECTION (at depth), ECCENTRIC (coming back up).
Each exercise sets four thresholds on its primary angle:
- `THR_DESCENDING`: the angle drops below this to start an attempt.
- `THR_INFLECTION`: the count bar. The angle must reach this or lower for the rep to count.
- `THR_STANDING`: the angle returns to this or higher to complete the rep.
- `HYSTERESIS_BUFFER`: the angle must rise above `THR_INFLECTION + HYSTERESIS_BUFFER` to leave
  the bottom.

Transitions (`CONSECUTIVE_FRAMES_REQ` = 3):
- IDLE to CONCENTRIC: primary angle below `THR_DESCENDING`, the FSM armed, and the exercise's
  start gate passing, all together for 3 consecutive frames. Emits `REP_STARTED`.
- CONCENTRIC to INFLECTION: primary angle at or below `THR_INFLECTION`, once the attempt is at
  least 3 frames old.
- CONCENTRIC to IDLE: primary angle above `THR_STANDING` before reaching depth. Happens at once.
  Emits `REP_ABANDONED`. The attempt is not counted, and its form warnings are still shown.
- INFLECTION to ECCENTRIC: primary angle above `THR_INFLECTION + HYSTERESIS_BUFFER`, once the
  state is at least 3 frames old.
- ECCENTRIC to IDLE: primary angle at or above `THR_STANDING`, once the state is at least 3 frames
  old. The rep is counted. Emits `REP_COMPLETED`.
- Re-descend: in ECCENTRIC, if the primary angle goes back to `THR_INFLECTION` or below for 3
  consecutive frames without reaching `THR_STANDING`, the rep is counted (`REP_COMPLETED`) and the
  FSM returns to IDLE. A new attempt can then open right away. This lets continuous-tempo sets
  without full lockout keep counting.

Counters: `rep_count` (completed reps), `abandoned_count` (abandoned attempts), `attempt_count`
(the sum). `correct_rep_count` (completed reps with zero rule violations) comes from the rules
layer.

### Squat FSM

- Primary angle: mean of `left_knee` and `right_knee` (hip-knee-ankle, degrees).
- Start attempt below: 150 (`THR_DESCENDING`).
- Count bar: 120 or below (`THR_INFLECTION`).
- Complete at: 160 or above (`THR_STANDING`).
- Hysteresis: 10 (leaves the bottom above 130).
- Arming: on; counting joints hip, knee, ankle; trunk tilt at most 30 (standing upright).
- Start gate: none beyond the angle.
- Note: the count bar (120) is looser than the depth rule (100), so a squat that reaches 100-120 is
  counted and also warned "Lower to 90 degrees".

### Push-up FSM

- Primary angle: mean of `left_elbow` and `right_elbow` (shoulder-elbow-wrist, degrees).
- Start attempt below: 140.
- Count bar: 110 or below.
- Complete at: 150 or above.
- Hysteresis: 15 (leaves the bottom above 125).
- Arming: on; counting joints shoulder, elbow, wrist; trunk tilt at least 60 (in plank, not
  standing).
- Start gate: none beyond the angle.

### Lunge FSM

- Primary angle: `min(left_knee, right_knee)`, the more-bent knee each frame (hip-knee-ankle,
  degrees). The front leg is never locked to a side; it is whichever knee is deeper.
- Start attempt below: 145.
- Count bar: 105 or below.
- Complete at: 155 or above.
- Hysteresis: 12 (leaves the bottom above 117).
- Arming: on; counting joints hip, knee, ankle; trunk tilt at most 30. Disarms on confidence loss
  only, never because a knee is bent.
- Start gate: `thigh_split` greater than 58 degrees (`LUNGE_START_SPLIT_MIN`). A lunge splits the
  thighs apart; a recovery step between reps bends one knee but barely splits the thighs, so it
  opens no attempt. If `thigh_split` is unavailable, the fallback gate requires both knees to read
  below 155.

### Bicep curl FSM

- Primary angle: the active arm's elbow angle (shoulder-elbow-wrist, degrees).
- Start attempt below: 140.
- Count bar: 55 or below.
- Complete at: 155 or above.
- Hysteresis: 15 (leaves the bottom above 70).
- Arming gate: none. Start gate per arm, evaluated only while IDLE:
  - The arm's shoulder, elbow and wrist all have score 0.3 or higher (`MIN_SIDE_SCORE`).
  - The arm was seen extended: its highest elbow angle since the FSM entered IDLE is 140 or more.
  - The arm is contracting: its current elbow angle is at or below the smaller of 140 and (that
    peak minus 25) (`START_DESCENT_DELTA`).
  - An arm whose last rep was counted via re-descend (no full lockout) is exempt from the
    "seen extended" check, and qualifies at once while still at 70 or below, so continuous-tempo
    sets keep counting.
- Active arm: if both arms qualify, the more-bent one; otherwise the one that qualifies. It is
  locked for the whole attempt and passed to the rules as the active side.

## Form rules

### How the rules work (all exercises)

- Each exercise has a priority-ranked list of rules. Priority 1 is the most important.
- Frame rules are checked on every frame inside an attempt (from `REP_STARTED` until the attempt
  completes or is abandoned). A frame rule fires only after 10 consecutive violated frames
  (`FRAME_RULE_MIN_FRAMES`). A clean frame or a frame without enough data resets the streak.
- Rep rules are checked once, at `REP_COMPLETED` and also at `REP_ABANDONED`. An abandoned attempt
  is not counted but still gets its rep-rule warning ("not counted, and here is why").
- A rule returns violated, satisfied, or no verdict. No verdict (missing or low-confidence
  landmarks, no 3D data, or a precondition not met) is never a warning and never makes a rep
  incorrect.
- Show one, record all: when several rules are violated on the same frame, the app shows only the
  highest-priority rule's message. Every violated rule is still recorded for the rep.
- A counted rep is "correct" when no rule was violated at any point during it.
- Each rep summary records: rep number, active side, correct, all warning messages and rule names
  in priority order, and the per-rep metric values.
- Design principle, rules go with the FSM: a depth rule's bar equals the FSM count bar, so a
  counted rep is never told to go deeper. Deliberate exceptions: squat depth (counts at 120, must
  reach 100 to be correct), curl extension (completes at 155, full range needs 145), and the lunge
  too-deep rule.
- Design intent, warn on clearly bad form: thresholds aim at clear-error values rather than the
  ideal form value. This is an intent, not a guarantee; some bars are set tighter and can
  occasionally warn on acceptable form.

### Squat rule 1: knee_depth

- Exercise: squat. Priority: 1. Scope: rep.
- Cue shown: "Lower to 90 degrees"
- Metric: the lowest value over the attempt of the mean of `left_knee` and `right_knee`
  (hip-knee-ankle interior angle, degrees, 180 = straight leg).
- Fires when: that minimum is greater than 100 (`SQUAT_DEPTH_TARGET`).
- No verdict when: no frames were accumulated.
- Meaning: the squat did not go deep enough. Coached ideal is a 90 degree knee. Because the FSM
  counts at 120, a squat bottoming out between 100 and 120 is counted and also warned.

### Squat rule 2: knee_valgus (knees caving in)

- Exercise: squat. Priority: 2. Scope: rep. Needs 3D keypoints.
- Cue shown: "Push knees out"
- Metric: the 3D angle in degrees between the left knee->ankle line and the right knee->ankle line
  (the two shins). 0 means the shins are parallel. It is averaged over the frames of the attempt
  where the mean knee angle is between 92 and 108 (within 8 degrees, `KNEE_PARALLEL_BAND`, of
  `SQUAT_DEPTH_TARGET` 100), so every rep is compared at the same depth. A signed frontal-plane
  reading gives the direction: positive means the knees are inside their ankles.
- Fires when: the averaged angle is greater than 11 degrees (`KNEE_PARALLEL_MAX_INWARD`) and the
  direction is knees-inward.
- No verdict when: no frame in the 92-108 knee band is usable. A frame is usable only when all six
  joints (both hips, knees, ankles) have score 0.3 or higher and the view is not near profile (hip
  profile ratio |sin(body yaw)| at most 0.85, about 58 degrees of body yaw). Unusable frames are
  skipped; the rule abstains only if every in-band frame is unusable or the rep never enters the
  band.
- Meaning: the two shin lines should stay parallel. Knees collapsing inward (^ shape) is a fault.
  Mutually exclusive with knee_varus.

### Squat rule 3: knee_varus (knees pushed out)

- Exercise: squat. Priority: 3. Scope: rep. Needs 3D keypoints.
- Cue shown: "Keep knees in line"
- Metric: the same shin-to-shin 3D angle as knee_valgus (degrees, 0 = parallel shins), averaged
  over the frames where the mean knee angle is between 92 and 108.
- Fires when: the averaged angle is greater than 8 degrees (`KNEE_PARALLEL_MAX_OUTWARD`) and the
  direction is knees-outward (knees outside their ankles, or zero).
- No verdict when: same as knee_valgus. It abstains only if no frame in the 92-108 knee band has
  all six hip/knee/ankle joints at score 0.3 or higher with a hip profile ratio of 0.85 or less.
- Meaning: knees splaying outward (V shape), for example with toes turned out, is also a fault.
  The knees should stay parallel. Mutually exclusive with knee_valgus.

### Squat rule 4: back_straight

- Exercise: squat. Priority: 4. Scope: frame. Needs 3D keypoints.
- Cue shown: "Keep back straight"
- Metric: trunk tilt, the angle in degrees between the hip->shoulder line and the world vertical
  (0 = upright), averaged over the left and right sides.
- Fires when: the tilt is greater than 35 degrees (`SQUAT_BACK_TILT_MAX`) for 10 consecutive
  frames.
- No verdict when: neither side has both shoulder and hip at score 0.3 or higher.
- Meaning: the torso leans too far forward. It measures trunk lean, not spine curvature.

### Push-up rule 1: body_alignment

- Exercise: push-up. Priority: 1. Scope: frame.
- Cue shown: "Body not straight"
- Metric: the shoulder-hip-ankle interior angle in degrees (180 = straight body line), averaged
  over the left and right sides.
- Fires when: the angle is less than 160 (`PUSHUP_ALIGN_MIN`) for 10 consecutive frames.
- Meaning: the body is not in a straight line. Catches both sagging hips and piked hips with one
  message.

### Push-up rule 2: elbow_depth

- Exercise: push-up. Priority: 2. Scope: rep.
- Cue shown: "Lower Your Chest"
- Metric: the lowest value over the attempt of the mean of `left_elbow` and `right_elbow`
  (shoulder-elbow-wrist interior angle, degrees).
- Fires when: that minimum is greater than 110 (`PUSHUP_ELBOW_TARGET`).
- No verdict when: no frames were accumulated.
- Meaning: the chest did not go low enough. The bar equals the push-up count bar (110), so it
  fires only on attempts that were not counted.

### Lunge rules: which knee is front and back

All lunge rules decide sides without a side lock. The front knee is whichever knee reached the
smaller (more bent) minimum over the attempt; the back knee is the other one. Front-knee depth
outcomes for a lunge (hip-knee-ankle angle of the front knee at its deepest, degrees):
- below 70: counted, warned "Raise your front knee".
- 70 to 105: counted, no depth warning.
- above 105: not counted, warned "Lower your front knee".
The coached ideal is 90 degrees for both knees.

### Lunge rule 1: front_knee_too_shallow

- Exercise: lunge. Priority: 1. Scope: rep.
- Cue shown: "Lower your front knee"
- Metric: the front knee's lowest hip-knee-ankle angle over the attempt, in degrees, where front =
  `min(lowest left knee, lowest right knee)`.
- Fires when: that value is greater than 105 (`LUNGE_FRONT_SHALLOW_MAX`).
- No verdict when: either knee has no accumulated value.
- Meaning: the lunge was not deep enough. The bar equals the lunge count bar (105), so it only ever
  fires on attempts that were not counted. On a shallow set the rep counter stays at 0 and this cue
  appears on every attempt.

### Lunge rule 2: front_knee_too_deep

- Exercise: lunge. Priority: 2. Scope: rep.
- Cue shown: "Raise your front knee"
- Metric: the front knee's lowest hip-knee-ankle angle over the attempt, in degrees (the smaller
  of the two knees' minima).
- Fires when: that value is less than 70 (`LUNGE_FRONT_DEEP_MIN`).
- No verdict when: either knee has no accumulated value.
- Meaning: the front knee bent too far past the 90 degree ideal. Never fires together with
  front_knee_too_shallow.

### Lunge rule 3: torso_upright

- Exercise: lunge. Priority: 3. Scope: frame. Needs 3D keypoints.
- Cue shown: "Keep Torso Upright"
- Metric: trunk tilt, the angle in degrees between the hip->shoulder line and the world vertical
  (0 = upright), taking the smaller of the left and right sides. The smaller side is used because
  the far-from-camera side reads inflated at side views; a real lean shows on both sides.
- Fires when: the tilt is greater than 20 degrees (`LUNGE_TILT_MAX`) for 10 consecutive frames.
- No verdict when: neither side has both shoulder and hip at score 0.3 or higher.
- Meaning: the torso leans forward instead of staying upright.

### Lunge rule 4: back_knee_form

- Exercise: lunge. Priority: 4. Scope: rep.
- Cue shown: "Bend your back knee toward the floor"
- Metric: the back knee's hip-knee-ankle angle in degrees at the bottom of the rep: its smallest
  value within 2 frames either side (`LUNGE_BOTTOM_WINDOW`) of the frame where the front knee was
  deepest.
- Fires when: that value is greater than 120 (`LUNGE_BACK_MAX_MIN`).
- No verdict when: the front knee never reached 105 or below (`LUNGE_FRONT_TARGET`; the attempt
  never reached lunge depth), or the bottom value is unavailable.
- Meaning: the rear leg stays too straight at the bottom. There is no "back knee too bent" rule.
- Camera: this rule needs a side view to see the rear leg. That is why the lunge camera band is a
  side-on view (see Camera placement).

### Bicep curl rule 1: elbow_away

- Exercise: bicep curl. Priority: 1. Scope: frame. Needs 3D keypoints.
- Cue shown: "Keep Elbows at Your Sides"
- Metric: the active arm's `{side}_shoulder_angle`, the elbow-shoulder-hip interior angle in
  degrees. 0 means the upper arm lies along the torso. The active arm comes from the curl FSM.
- Fires when: the angle is greater than 45 degrees (`BICEP_ELBOW_AWAY_MAX`) for 10 consecutive
  frames.
- No verdict when: there is no active arm, or the active arm's shoulder, elbow or hip is missing,
  below score 0.3, or degenerate.
- Meaning: the upper arm has swung away from the body. The rule does not say which way (out,
  forward or back). A strongly flared elbow can keep the elbow from bending to 55, in which case
  the attempt is not counted but the cue is still shown.

### Bicep curl rule 2: full_rom

- Exercise: bicep curl. Priority: 2. Scope: rep.
- Cue shown: "Full range of motion"
- Metric: the active arm's elbow angle (shoulder-elbow-wrist, degrees) over the attempt: its
  minimum and its maximum.
- Fires when: NOT (minimum at or below 55 (`BICEP_FLEX_TARGET`) AND maximum at or above 145
  (`BICEP_EXT_TARGET`)). Either half missed fires it.
- No verdict when: no frames were accumulated for the active arm.
- Meaning: the curl must both flex fully (55) and extend fully (145). The flexion bar equals the
  curl count bar, so on counted reps only the extension half can fail, which happens when a rep is
  counted via re-descend without the arm reaching 145.

## Camera placement

The placement guide steers the user to a per-exercise body-yaw band before counting starts. The
band is on the app's `|body_yaw_deg|` reading, which under-reads the true camera angle, so these
are app units, not degrees from the camera. Either mirror side is accepted.

| Exercise | Band (app yaw units) | Why |
|---|---|---|
| Squat | 45 +/- 12 (33 to 57) | must stay below about 58, where knee_valgus and knee_varus stop giving a verdict |
| Push-up | 45 +/- 25 (20 to 70) | oblique view |
| Lunge | 75 +/- 10 (65 to 85) | corresponds to a true 90 degree side camera, needed for back_knee_form |
| Bicep curl | 45 +/- 12 (33 to 57) | oblique view |

## Constants reference

| Constant | Value | Where |
|---|---|---|
| `CONSECUTIVE_FRAMES_REQ` | 3 | FSM, all exercises |
| `ARM_FRAMES_REQ` | 10 | FSM arming |
| `DISARM_FRAMES_REQ` | 40 | FSM arming |
| `ARM_MIN_SCORE` | 0.5 | FSM arming |
| `READY_TILT_MAX` squat / lunge | 30 | FSM arming |
| `READY_TILT_MIN` push-up | 60 | FSM arming |
| `LUNGE_START_SPLIT_MIN` | 58 | lunge start gate |
| `START_DESCENT_DELTA` | 25 | curl start gate |
| `MIN_SIDE_SCORE` | 0.3 | curl start gate |
| `FRAME_RULE_MIN_FRAMES` | 10 | all frame rules |
| `MIN_LM_SCORE` | 0.3 | all rules |
| `PROFILE_RATIO_MIN` | 0.85 | squat knee rules, far-side masking |
| `SQUAT_DEPTH_TARGET` | 100 | squat knee_depth |
| `KNEE_PARALLEL_MAX_INWARD` | 11 | squat knee_valgus |
| `KNEE_PARALLEL_MAX_OUTWARD` | 8 | squat knee_varus |
| `KNEE_PARALLEL_BAND` | 8 | squat knee rules |
| `SQUAT_BACK_TILT_MAX` | 35 | squat back_straight |
| `PUSHUP_ALIGN_MIN` | 160 | push-up body_alignment |
| `PUSHUP_ELBOW_TARGET` | 110 | push-up elbow_depth |
| `LUNGE_FRONT_TARGET` | 105 | lunge count bar, back_knee_form depth gate |
| `LUNGE_FRONT_SHALLOW_MAX` | 105 | lunge front_knee_too_shallow |
| `LUNGE_FRONT_DEEP_MIN` | 70 | lunge front_knee_too_deep |
| `LUNGE_TILT_MAX` | 20 | lunge torso_upright |
| `LUNGE_BACK_MAX_MIN` | 120 | lunge back_knee_form |
| `LUNGE_BOTTOM_WINDOW` | 2 | lunge back_knee_form |
| `BICEP_ELBOW_AWAY_MAX` | 45 | curl elbow_away |
| `BICEP_FLEX_TARGET` | 55 | curl full_rom |
| `BICEP_EXT_TARGET` | 145 | curl full_rom |

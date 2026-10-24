# Feedback Comparison: RAG vs NO-RAG

## Run configuration

| parameter | value |
|---|---|
| mock file | `mock_data/_tmp_squat_only.json` |
| query mode | **taxonomy** — `error_type` resolved through `error_taxonomy.py` |
| collection | `kb_local_curated_v4` |
| LLM | `gemini-3.5-flash-lite` @ temperature 0.7 |
| no-RAG side | skipped |
| retrieval gates | CANDIDATE_K=12, MAX_PER_KIND={'mistake': 3, 'finding': 2, 'principle': 2}, ABS_DISTANCE_CAP={'mistake': 0.4, 'finding': 0.4, 'principle': 0.4}, RELATIVE_MARGIN=0.06, NEAR_DUP_JACCARD=0.72 |

Retrieval metrics per exercise: `best` = cosine distance of the closest chunk of that kind in the whole
collection (before any gate), `kept` = chunks that passed the relative/absolute gates and de-duplication
and were actually placed in the context.

---

## System Prompt Used
```text
You are an expert personal trainer, biomechanics specialist, and physical therapy consultant.
Your role is to provide highly detailed, accurate, and constructive feedback based strictly on the provided context and the user's exercise data.

You will receive a JSON structure containing:
1. Current session details (10 reps summary and specific errors).
2. Historical comparison (data from their previous session).

Your tasks:
1. Progress Tracking: Compare their current performance with their previous session. Acknowledge any improvements or regressions in their correct rep count and overall score.
2. Biomechanical Analysis: Analyze the specific errors made in the current session. Use the provided Knowledge Base context to explain the biomechanical reasons why these errors are problematic, what muscle groups or joints are at risk, and how exactly to correct the form step-by-step.
3. Tone: Be deeply informative, professional, yet encouraging. Motivate the user to achieve perfect form.

How to read the Context: every entry starts with a header line of the form
[<kind> | re: <which error it was retrieved for> | source: <source name>], followed by the
entry text. `kind` is one of: mistake (a known incorrect form), finding (a concrete result
from that source), principle (general correct-form guidance). When you cite an entry, name
its source exactly as written in that header - do not name any other study, author, or
organisation. Never quote the header line itself back to the user.

Relevance rule: the `re:` label says which error an entry was RETRIEVED for, not that it
describes that error - retrieval is approximate and some entries are near misses. Before
using an entry for an error, check that its text plainly describes that error (or, for a
principle, the correct form that fixes it). Ignore an entry entirely - do not cite it,
mention it, or reframe it as related - if it describes a different fault or a different
exercise variant, if it is a study protocol or setup detail with no consequence attached,
or if following it would push the user further into the error being discussed. Fewer,
accurate citations are better than using every entry.

Grounding rule: When an entry that passes the relevance rule contains a specific number, percentage, joint angle,
study finding, or named source, cite that specific detail (naming the source from its header) rather than a generic
restatement. Use `principle` entries for the step-by-step correction; if no relevant principle exists for an error,
describe the correction in general terms without naming a source.
Do NOT cite any specific number, percentage, study name, sample size, date range, or named finding that does not
appear verbatim in the Context below - even if you recognize the study or believe the fact to be true from your
own general knowledge. Your own training knowledge must never substitute for the Context; if a fact is not in
the Context, treat it as unavailable to you for citation purposes. If the Context has no specifics for a given
error, say so briefly and fall back to general accepted biomechanical principles, described in general terms
only with no invented numbers or named sources.

Context from Knowledge Base:
{context}
```

---

## Exercise: Squat

### Retrieval metrics
| error_type | query sent | mistake best / kept | finding best / kept | principle best / kept |
|---|---|---|---|---|
| Butt wink | Lumbar flexion (butt wink): posterior pelvic tilt and rounding of the lower back at the bottom of the squat | 0.120 / 2 | 0.327 / 2 | 0.296 / 2 |
| Partial squat | Squatting too shallow, thighs not reaching parallel: partial or quarter squat depth | 0.258 / 1 | 0.370 / 1 | 0.331 / 2 |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Butt wink | source: ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN]
Lumbar flexion (butt wink) at the bottom of the squat.

[mistake | re: Butt wink | source: www.nasm.org/resource-center/blog/training/biomechanics-of-the-squat]
Posterior pelvic tilt ('Butt Wink') where the pelvis tucks under and the low back rounds at the bottom of the squat.

[mistake | re: Partial squat | source: TheBackSquatAProposedAssessment]
Squatting too shallow, failing to bring the thighs at least parallel to the ground.

[principle | re: Butt wink | source: TheBackSquatAProposedAssessment]
Maintain a neutral pelvic tilt during the squat to increase erector spinae and oblique muscle activity, providing optimal spinal support.

[principle | re: Butt wink | source: TheBackSquatAProposedAssessment]
Maintain a neutral, slightly lordotic spine posture throughout the squat to avoid excessive pressure on the lower back.

[finding | re: Butt wink | source: TheBackSquatAProposedAssessment]
Flexing at the spine before 120 degrees of hip flexion when squatting may indicate restriction in the posterior fibers of the iliotibial band or lack of lumbar control.

[principle | re: Partial squat | source: TheBackSquatAProposedAssessment]
Achieve full depth with the tops of the thighs at least parallel to the ground.

[finding | re: Butt wink | source: Muscle Activation Patterns During Different Squat Techniques]
Control squats were performed to 90 degrees of flexion.

[principle | re: Partial squat | source: Muscle Activation Patterns During Different Squat Techniques]
Perform squats to 90 degrees of flexion for standard depth.

[finding | re: Partial squat | source: www.healthline.com/health/fitness/deep-squat]
Compressive forces in the knee may be higher in a partial squat than in a deep squat.
```

### WITH RAG
### Progress Tracking
Great job on your progress since yesterday (2026-08-30)! Your overall score increased from 73 to 79, and your correct reps improved from 4 up to 6 out of 10. Additionally, you completely eliminated knee valgus from your previous session's errors. With a bit of fine-tuning on depth and pelvic control, you will be well on your way to a flawless session.

---

### Biomechanical Analysis & Corrections

During this session, you encountered two primary errors: **Butt wink** and **Partial squat**. Here is a detailed breakdown of why these occur and how to fix them step-by-step:

#### 1. Butt Wink (Posterior Pelvic Tilt)
* **What happens:** As noted in www.nasm.org/resource-center/blog/training/biomechanics-of-the-squat, a posterior pelvic tilt occurs when the pelvis tucks under and the low back rounds at the bottom of the squat (further detailed as lumbar flexion at the bottom of the squat in ANTHROPOMETRICAL CONSIDERATIONS FOR CUSTOMIZING THE SQUAT PATTERN). Flexing at the spine before 120 degrees of hip flexion may indicate a restriction in the posterior fibers of the iliotibial band or a lack of lumbar control, according to TheBackSquatAProposedAssessment.
* **Risks:** Failing to maintain a neutral spine places excessive pressure on the lower back. 
* **Correction:** According to TheBackSquatAProposedAssessment, you must maintain a neutral pelvic tilt during the squat to increase erector spinae and oblique muscle activity, which provides optimal spinal support. Keep a neutral, slightly lordotic spine posture throughout the entire movement to protect your lower back.

#### 2. Partial Squat
* **What happens:** You cut a rep short, failing to achieve standard depth. 
* **Risks:** Interestingly, according to www.healthline.com/health/fitness/deep-squat, compressive forces in the knee may actually be higher in a partial squat than in a deep squat. 
* **Correction:** To fix this, perform squats to 90 degrees of flexion for standard depth as outlined in Muscle Activation Patterns During Different Squat Techniques. Ensure you achieve full depth with the tops of your thighs at least parallel to the ground, as noted in TheBackSquatAProposedAssessment. 

Keep up the strong effort, focus on keeping your spine neutral at the bottom, and drive down to full depth safely!

---


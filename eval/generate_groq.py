"""Generate feedback answers on a free Groq model from contexts that already exist on disk
(strict/v6b plan, quality layer). No embedding, no Gemini call.

    python eval/generate_groq.py mock_data/mock_sessions_targets_lunge.json \\
        mock_data/mock_sessions_targets_push-up.json --out compare_output/strict_v6b/groq_targets.json

Arms (context source per exercise <ex>):
  no_rag     - "No external context provided." (what test_rag_compare.py sends without RAG)
  v6_prefer  - compare_output/baseline_v14/compare_result_v14_<ex>.json   (kb v6, TAG_MODE prefer)
  v6_strict  - compare_output/strict_v6b/context_v6_strict_<ex>.json    (kb v6, strict, offline, step 2)
  v6b_strict - compare_output/strict_v6b/context_v6b_strict_<ex>.json   (kb v6b, strict, live --context-only)

Retrieval depends only on exercise_id and the set of error_types (test_rag_compare.
retrieve_kb_blocks), so a session's context is taken from the session in the source file with
the same exercise and the same error set - exact, not an approximation. Arms whose contexts are
byte-identical share one generation (`same_as`).

The prompt is test_rag_compare's own: SYSTEM_PROMPT and the human template rendered through
the same ChatPromptTemplate, payload = model_payload() (report_label and HELD_BACK_FIELDS
dropped). Temperature = LLM_TEMPERATURE. Only the model differs from the real generator.

Resumable: every answer is written to --out as soon as it arrives and reused on a re-run.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402

import test_rag_compare as trc  # noqa: E402

load_dotenv()
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "qwen/qwen3.8-27b"  # Alibaba family; keeps openai/gpt-oss-120b free to judge
NO_RAG_CONTEXT = "No external context provided."
ARMS = {
    "no_rag": None,
    "v6_prefer": "compare_output/baseline_v14/compare_result_v14_{ex}.json",
    "v6_strict": "compare_output/strict_v6b/context_v6_strict_{ex}.json",
    "v6b_strict": "compare_output/strict_v6b/context_v6b_strict_{ex}.json",
}
HUMAN = "Here is the exercise session data:\n{input}\n\nPlease evaluate my performance and tell me what to work on."
PROMPT = ChatPromptTemplate.from_messages([("system", trc.SYSTEM_PROMPT), ("human", HUMAN)])
THINK = re.compile(r"<think>.*?</think>\s*", re.S)


def error_set(session):
    return frozenset(e["error_type"] for r in session.get("reps_detail", []) for e in r.get("errors", []))


def context_for(path, session):
    with open(path, encoding="utf-8") as f:
        src = json.load(f)
    want = (session["exercise_id"], error_set(session))
    hits = [s for s in src["sessions"] if (s["exercise_id"], error_set(s["payload"])) == want]
    if len(hits) != 1:
        raise SystemExit(f"{path}: {len(hits)} sessions with errors {sorted(want[1])}, want exactly 1")
    return hits[0]["context"], hits[0]["payload"]["session_id"]


def messages(session, context):
    payload = json.dumps(trc.model_payload(session), indent=2)
    role = {"system": "system", "human": "user"}
    return [{"role": role[m.type], "content": m.content}
            for m in PROMPT.format_messages(context=context, input=payload)]


def complete(model, msgs, key):
    body = {"model": model, "temperature": trc.LLM_TEMPERATURE, "messages": msgs}
    for attempt in range(8):
        req = urllib.request.Request(GROQ_URL, data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json",
                                              "Authorization": f"Bearer {key}",
                                              "User-Agent": "rag-system-eval/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                remaining = resp.headers.get("x-ratelimit-remaining-tokens")
            text = data["choices"][0]["message"]["content"] or ""
            return THINK.sub("", text).strip(), data.get("usage", {}), remaining
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code == 429 or e.code >= 500:
                wait = float(e.headers.get("retry-after") or 30) + 2
                print(f"    HTTP {e.code}, waiting {wait:.0f}s ({detail[:120]})")
                time.sleep(wait)
                continue
            raise RuntimeError(f"HTTP {e.code}: {detail}") from None
    raise RuntimeError("gave up after 8 attempts")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mocks", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--samples", type=int, default=1)
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--min-interval", type=float, default=45,
                    help="seconds between calls (free tier: 8K tokens/min, ~5-6K per call)")
    args = ap.parse_args()
    key = os.environ.get("GROQ_API_KEY") or sys.exit("GROQ_API_KEY is not set")
    arms = args.arms.split(",")

    run = {"model": args.model, "temperature": trc.LLM_TEMPERATURE, "samples": args.samples,
           "system_prompt_sha1": hashlib.sha1(trc.SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
           "arms": {a: ARMS[a] for a in arms}, "sessions": []}
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as f:
            old = json.load(f)
        if (old["model"], old["system_prompt_sha1"]) != (run["model"], run["system_prompt_sha1"]):
            sys.exit(f"{args.out} was made with another model or prompt - use a new --out")
        cache = {(s["session_id"], a): v for s in old["sessions"] for a, v in s["arms"].items()}
    else:
        cache = {}

    sessions = [s for path in args.mocks for s in json.load(open(path, encoding="utf-8"))]
    # Build every arm's context first, so a missing source fails before any call is made.
    plan = []
    for s in sessions:
        ctx = {}
        for a in arms:
            if ARMS[a] is None:
                ctx[a] = (NO_RAG_CONTEXT, None)
            else:
                ctx[a] = context_for(ARMS[a].format(ex=s["exercise_id"]), s)
        plan.append((s, ctx))
    calls = sum(len({c for c, _ in ctx.values()}) for _, ctx in plan) * args.samples
    print(f"{len(plan)} sessions, {calls} generations planned on {args.model}")

    last = 0.0
    for s, ctx in plan:
        entry = {"session_id": s["session_id"], "label": s.get("report_label"),
                 "exercise_id": s["exercise_id"], "payload": trc.model_payload(s), "arms": {}}
        run["sessions"].append(entry)
        by_ctx = {}
        for a in arms:
            context, from_sid = ctx[a]
            sha = hashlib.sha1(context.encode("utf-8")).hexdigest()
            if sha in by_ctx:
                entry["arms"][a] = {"same_as": by_ctx[sha], "context_sha1": sha, "context_from": from_sid}
                continue
            by_ctx[sha] = a
            done = cache.get((s["session_id"], a), {})
            answers = done.get("answers", []) if done.get("context_sha1") == sha else []
            entry["arms"][a] = {"context_sha1": sha, "context_from": from_sid, "context": context,
                                "answers": answers}
            while len(answers) < args.samples:
                wait = args.min_interval - (time.time() - last)
                if wait > 0:
                    time.sleep(wait)
                last = time.time()
                try:
                    text, usage, remaining = complete(args.model, messages(s, context), key)
                except RuntimeError as e:
                    text, usage, remaining = f"{trc.GENERATION_ERROR}: {e}", {}, None
                answers.append(text)
                print(f"  {s['session_id']} {a:<10} #{len(answers)} tokens {usage.get('total_tokens')} "
                      f"(remaining/min {remaining})", flush=True)
                with open(args.out, "w", encoding="utf-8") as f:
                    json.dump(run, f, ensure_ascii=False, indent=1)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(run, f, ensure_ascii=False, indent=1)
    print(f"Done -> {args.out}")


if __name__ == "__main__":
    main()

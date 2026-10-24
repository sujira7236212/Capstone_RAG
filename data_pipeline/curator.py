import os
import re
import sys
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# error_taxonomy.py lives in the project root, one level up from data_pipeline/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from error_taxonomy import ERROR_TAXONOMY, faults_for_exercise
from functools import lru_cache
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# A single curate_knowledge() call compresses its whole input into a handful of list
# items, so a 20-page paper fed in one shot loses far more detail than a 2-page article
# does. Splitting long text into windows this size before curation keeps each call's
# compression ratio reasonable so specific findings don't get flattened away.
CURATION_CHUNK_SIZE = 6000
CURATOR_MODEL = os.environ.get("CURATOR_MODEL", "gemini-3.6-flash")
CURATION_CHUNK_OVERLAP = 300

# Load environment variables (e.g., GOOGLE_API_KEY)
load_dotenv()

# ---------------------------------------------------------
# 1. Define the Schema for Extracted Knowledge (Metadata)
# ---------------------------------------------------------
class KnowledgeItem(BaseModel):
    """One extracted statement plus the fault codes IT SPECIFICALLY speaks to.

    v4 tagged applies_to_fault once per window and broadcast that set onto every item
    in the window, so a tag-filtered retrieval query returned every item from a window
    that happened to also discuss the right fault, not just the items actually about it
    (see docs/session_notes_2026-09-12.md section 8, "v4 tags are per-window"). Tagging
    per item instead means a tag-filter at retrieval time is precise.
    """
    text: str = Field(description=(
        "The statement itself, as one self-contained sentence. It must make sense on its "
        "own, without needing the rest of the list around it for context."
    ))
    applies_to_fault: List[str] = Field(default_factory=list, description=(
        "Which of the KNOWN FAULT CODES listed in the prompt THIS statement itself directly addresses "
        "- not every code the surrounding paragraph happens to mention. Use the codes verbatim. "
        "Empty list if none apply. Never invent codes. Leave empty (even on-topic) if the statement argues "
        "the fault is actually fine/equivalent to correct form, or if it is specific to a named exercise "
        "variant whose mechanics differ from the standard movement (see prompt for both rules)."
    ))


class ExtractedKnowledge(BaseModel):
    # Deliberately narrow. The earlier "anything sports-science" definition let through
    # cardiovascular-risk epidemiology, blood-lipid biochemistry and haemophilia papers
    # whose only link to the exercise was its name (docs/kb/kb_quality_assessment.md 3.1/3.4).
    # Those chunks diluted retrieval and seeded off-topic statistics into the feedback.
    # The feedback system only ever asks "what went wrong with the form and why does it
    # matter", so that is the bar for relevance.
    is_relevant: bool = Field(description=(
        "True ONLY if this text says something usable for correcting how a person performs the exercise: "
        "joint/segment technique, muscle activation as it relates to technique or exercise variation, common "
        "faults and their biomechanical consequences, injury mechanisms tied to technique, or range-of-motion/"
        "loading guidance. False if the exercise is merely the vehicle for an unrelated outcome (cardiovascular "
        "risk, blood biochemistry, disease populations, training-program periodisation, equipment marketing), "
        "or if it is fluff, navigation text, advertising, or a reference list."
    ))
    exercise_type: str = Field(description="The specific exercise mentioned, e.g., 'Squat', 'Lunge', 'Bicep Curl'. Use 'Generic' if not specific.")
    focus_area: str = Field(description="The main body part or biomechanical focus, e.g., 'Knee', 'Lower Back', 'Core'.")
    content_type: str = Field(description="The type of information provided, e.g., 'Correct Form', 'Common Mistake', 'Injury Prevention'.")
    core_principles: List[KnowledgeItem] = Field(default_factory=list, description=(
        "A clean, concise list of the core principles, practical tips, and guidelines extracted from the "
        "text, including setup changes, drills, or self-checks when the source describes them. Remove only "
        "obvious fluff. Do not rephrase or add advice the source does not state."
    ))
    common_mistakes: List[KnowledgeItem] = Field(default_factory=list, description=(
        "A list of specific incorrect forms or common mistakes mentioned in the text, if any."
    ))
    specific_findings: List[KnowledgeItem] = Field(default_factory=list, description=(
        "Concrete, quotable facts unique to THIS source that a generic fitness coach would not already know: "
        "exact numbers, percentages, joint angles, forces, EMG/muscle-activation figures, study population/"
        "sample size, or named conclusions. Each item must include the number or named finding verbatim. "
        "Leave empty if the text has no such specifics — do not paraphrase a specific into a generic tip."
    ))
    consequences: List[KnowledgeItem] = Field(default_factory=list, description=(
        "What the fault does to the body: the biomechanical consequence or injury mechanism, which joint, "
        "ligament, disc, tendon, or muscle takes the extra load, and what the lifter feels or risks over "
        "time. One consequence per item, stated as cause and effect, e.g. 'Letting the knee cave inward "
        "raises valgus torque at the knee and strains the ACL and MCL.' Only include a consequence the "
        "text itself supports - do not invent one. If a mistake or principle sentence already ends with its "
        "own consequence clause, split that clause out into consequences rather than leaving it attached."
    ))
    # NOTE: no window-level applies_to_fault field here anymore. v4 asked the LLM for one
    # set of codes per window and broadcast it onto every item (imprecise - see KnowledgeItem
    # docstring). v5 computes the window-level set in curate_text_block() as the union of
    # each item's own applies_to_fault, purely so is_exercise_mismatch() still has something
    # to check; nothing asks the LLM to fill a window-level tag directly.

# ---------------------------------------------------------
# 2. Setup the LLM Curation Pipeline
# ---------------------------------------------------------
# Names the LLM uses for the same movement as the folder. Matched as normalised
# substrings, so "curl" also covers "Dumbbell Curl", "Barbell Curl", "Biceps Curl".
# Without this, the plain folder-name substring test rejected "Dumbbell Curl" under
# data/bicep-curl/ and threw away the one paper that documents the
# "not full extension" fault.
EXERCISE_ALIASES = {
    "bicep-curl": ("bicepcurl", "bicepscurl", "curl"),
    "push-up": ("pushup", "pressup"),
    "squat": ("squat",),
    # A (Bulgarian) split squat is a stationary lunge; the rear-leg papers filed under
    # data/lunge/back_knee_form/ are split-squat studies, and round 1 of v6 binned 8 of
    # their windows as "Bulgarian Split Squat" until this alias existed.
    "lunge": ("lunge", "splitsquat"),
}


def _norm(s: str) -> str:
    return s.lower().replace("-", "").replace("_", "").replace(" ", "")


# Sources under data/general/ (and loose files directly under data/) are not filed under
# one exercise. The curator sees all 12 rules for them and each item is routed to an
# exercise afterwards (route_general_window), instead of trusting the folder.
GENERAL = "general"

# Curl names that are not the biceps curl; "curl" alone would otherwise route a hamstring
# or wrist curl from general/ into bicep-curl.
_NOT_BICEP_CURL = ("leg", "hamstring", "nordic", "wrist")


def _faults_for(folder_exercise_id: str) -> dict:
    """faults_for_exercise(), except general/ gets every exercise's rules (rule names do
    not repeat across exercises, so one flat dict is unambiguous)."""
    if folder_exercise_id != GENERAL:
        return faults_for_exercise(folder_exercise_id)
    return {code: q for ex in ERROR_TAXONOMY for code, q in faults_for_exercise(ex).items()}


def _exercise_of_code() -> dict:
    return {code: ex for ex, faults in ERROR_TAXONOMY.items() for code in faults}


def exercise_for_type(exercise_type: str) -> Optional[str]:
    """The one exercise an LLM exercise_type names ('Back Squat' -> 'squat'), else None
    (Generic, several exercises, or a curl that is not the biceps curl)."""
    norm = _norm(exercise_type or "")
    if norm in ("", "generic"):
        return None
    hits = [ex for ex, aliases in EXERCISE_ALIASES.items()
            if any(a in norm or norm in a for a in aliases)]
    if hits == ["bicep-curl"] and any(w in norm for w in _NOT_BICEP_CURL):
        return None
    if sorted(hits) == ["lunge", "squat"] and "splitsquat" in norm:
        return "lunge"  # "split squat" also contains "squat"
    return hits[0] if len(hits) == 1 else None


ITEM_FIELDS = ("core_principles", "common_mistakes", "specific_findings", "consequences")


def route_general_window(window: dict) -> dict:
    """Split one curated general/ window into {exercise_id or 'general': window}.

    An item with tags goes to the exercise of each tag, keeping only that exercise's
    tags (a tag from two exercises puts a copy in both). An untagged item goes to the
    exercise the window's exercise_type names, or stays in general/ when it names none.
    ingest.py takes exercise_id from the first folder level, so the routed windows are
    written under curated_data_v6/<exercise>/ (process_data_directory).
    """
    code_ex = _exercise_of_code()
    fallback = exercise_for_type(window.get("exercise_type", "")) or GENERAL
    out = {}

    def bucket(ex):
        if ex not in out:
            w = {k: v for k, v in window.items() if k not in ITEM_FIELDS}
            w.update({field: [] for field in ITEM_FIELDS})
            w["routed_from"] = GENERAL
            out[ex] = w
        return out[ex]

    for field in ITEM_FIELDS:
        for item in window.get(field, []):
            by_ex = {}
            for code in item.get("applies_to_fault", []):
                if code in code_ex:
                    by_ex.setdefault(code_ex[code], []).append(code)
            if not by_ex:
                bucket(fallback)[field].append({**item, "applies_to_fault": []})
            for ex, codes in by_ex.items():
                bucket(ex)[field].append({**item, "applies_to_fault": codes})
    for w in out.values():
        w["applies_to_fault"] = sorted({c for f in ITEM_FIELDS for it in w[f] for c in it["applies_to_fault"]})
    return out


def load_batch(path: str, name: str, project_root: str) -> set:
    """One named batch of data_pipeline/curation_batches_v6.json -> absolute paths. A URL
    batch entry is its urls.txt file (the curator fetches a list file as one unit)."""
    with open(path, encoding="utf-8") as f:
        files = json.load(f)["batches"][name]["files"]
    out = {os.path.normcase(os.path.abspath(os.path.join(project_root, p))) for p in files}
    missing = [p for p in files if not os.path.exists(locate_source(project_root, p))]
    if missing:
        raise SystemExit(f"[BATCH] {len(missing)} file(s) in batch '{name}' do not exist: {missing}")
    return out


def load_skip_list(path: str, project_root: str) -> tuple:
    """Read data_pipeline/prefilter_v6.json (T3a) -> (dropped file paths, dropped URLs).

    Paths are compared as absolute, case-normalised paths. Refuses to run while any entry
    is still 'pending', because those files have not been decided yet.
    """
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)["entries"]
    pending = [e.get("path") or e.get("url") for e in entries if e["decision"] == "pending"]
    if pending:
        raise SystemExit(f"[SKIP-LIST] {len(pending)} entries are still 'pending' in {path}: {pending}")
    paths, urls = {}, {}
    for e in entries:
        if e["decision"] != "drop":
            continue
        if "path" in e:
            paths[os.path.normcase(os.path.abspath(os.path.join(project_root, e["path"])))] = e["reason"]
        else:
            urls[e["url"]] = e["reason"]
    return paths, urls


# PyPDFLoader renders the degree sign in several journal PDFs as a trailing "8" glued to
# the number ("1208" for 120°, "90 8" for 90°) or as the raw glyph name "/C176". The LLM
# notices and annotates it - "1208 (120 degrees)", "90 degrees (noted as 900 in text)" -
# but the annotation ends up in the chunk, and the feedback model then quotes "1208" to
# the user as if it were a number (compare_output/history/ab_v7.md, squat). Applied to every list
# item the curator returns; the rules are the exact shapes seen in kb_local_curated_v4
# (docs/kb/kb_quality_assessment.md 7.3), nothing more speculative than that.
_OCR_DEGREE_RULES = (
    # "(noted as 900 in text)", "(text states '90 8')", "(noted as 135 /C176)" -> dropped;
    # requires the opening paren so "denoted as SE-SE" is left alone.
    (re.compile(r"\s*\((?:noted as|text states|written as)\s[^)]*\)"), ""),
    # "95 6 27/C176" is "95 ± 27°" - the ± glyph also comes out as a digit.
    (re.compile(r"(\d+(?:\.\d+)?)\s*6\s*(\d+(?:\.\d+)?)\s*/C176"), r"\1 ± \2°"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*/C176"), r"\1°"),
    # "1208 (120 degrees)" -> "120 degrees": the LLM's own gloss is the right number.
    (re.compile(r"\b(\d{1,3})8 \(\1 degrees\)"), r"\1 degrees"),
)


def normalize_ocr_degrees(text: str) -> str:
    for pattern, repl in _OCR_DEGREE_RULES:
        text = pattern.sub(repl, text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def _tag_key(tag: str) -> str:
    return " ".join(str(tag).replace("_", " ").lower().split())


def normalize_fault_tags(tags, folder_exercise_id: str) -> list:
    """Map spelling variants of this exercise's fault codes back onto the code itself.

    The prompt says "use verbatim", but gemini still returned "partial_squat",
    "knee_valgus" and "partial range_of_motion" on 18 v5 items. Retrieval's tag filter is
    an exact LIKE '%|<code>|%', so those items were invisible under their own fault
    (eval tag_spelling miss, compare_output/ablation/ablation_log.md B0). Underscore, case and
    whitespace differences only; a tag that matches no known code is left as it is, and
    a variant that collapses onto a code already in the list is dropped.
    """
    canonical = {_tag_key(code): code for code in _faults_for(folder_exercise_id)}
    out = []
    for tag in tags or []:
        tag = canonical.get(_tag_key(tag), tag)
        if tag not in out:
            out.append(tag)
    return out


def is_exercise_mismatch(folder_exercise_id: str, extracted_exercise_type: str, file_path: str,
                         applies_to_fault=None) -> bool:
    """Flags windows whose curated exercise_type doesn't match the folder they live in.

    This is exactly the kind of bug that put Lunge PDFs under data/push-up/ silently -
    ingest.py trusts the folder name for exercise_id, so a mismatch here means the
    content would get tagged with the wrong exercise_id at query time and surface under
    the wrong exercise's retrieval. Mismatched windows are excluded from curated_data
    (see curate_text_block) rather than just warned about.

    A window the LLM tagged with one of THIS folder's fault codes is by definition about
    this exercise, whatever it called it, so that overrides the name test.
    """
    folder_norm = _norm(folder_exercise_id)
    extracted_norm = _norm(extracted_exercise_type)
    if extracted_norm in ("generic", ""):
        return False
    if applies_to_fault and set(applies_to_fault) & set(faults_for_exercise(folder_exercise_id)):
        return False
    aliases = EXERCISE_ALIASES.get(folder_exercise_id, (folder_norm,))
    mismatch = not any(a in extracted_norm or extracted_norm in a for a in aliases)
    if mismatch:
        print(
            f"[!! FOLDER MISMATCH - EXCLUDING !!] '{file_path}' is under folder '{folder_exercise_id}' "
            f"but its content was classified as exercise_type='{extracted_exercise_type}'. "
            f"Excluding this window from curated_data and routing it to excluded_from_kb/ instead."
        )
    return mismatch

RULE_CARDS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval", "rule_cards.json")


@lru_cache(maxsize=1)
def _card_excludes() -> dict:
    """{rule name: [what the expert-approved card says does NOT count]}.

    The queries are positive-only because an embedding cannot read "not X" (see
    error_taxonomy.py), but the LLM curator can, and sibling rules (knee_valgus vs
    knee_varus, shallow_lunge vs excessive_front_knee_flexion) get swapped without it.
    The card is the approved definition, not KB text, so this does not leak into eval.
    """
    with open(RULE_CARDS, encoding="utf-8") as f:
        cards = json.load(f)["cards"]
    return {c["rule_names"][0]: [x["en"] for x in c.get("excludes", [])] for c in cards}


def _fault_lines(faults: dict, indent: str = "  ") -> list:
    excludes = _card_excludes()
    lines = []
    for code, desc in faults.items():
        lines.append(f'{indent}- "{code}": {desc}')
        if excludes.get(code):
            lines.append(f"{indent}    do not tag when: " + " / ".join(excludes[code]))
    return lines


def _fault_code_block(folder_exercise_id: str) -> str:
    if folder_exercise_id == GENERAL:
        lines = []
        for ex in ERROR_TAXONOMY:
            lines.append(f"  {ex}:")
            lines += _fault_lines(faults_for_exercise(ex), indent="    ")
        return ("KNOWN FAULT CODES, grouped by exercise (use verbatim in applies_to_fault; a code also tells "
                "which exercise the item is about):\n" + "\n".join(lines))
    faults = faults_for_exercise(folder_exercise_id)
    if not faults:
        return "KNOWN FAULT CODES for this exercise: (none defined)"
    return ("KNOWN FAULT CODES for this exercise (use verbatim in applies_to_fault):\n"
            + "\n".join(_fault_lines(faults)))


def _prompt_context(folder_exercise_id: str) -> dict:
    """The prompt's exercise-dependent wording. For an exercise folder this reproduces the
    v5 prompt exactly; general/ gets wording for material not filed under one exercise."""
    if folder_exercise_id != GENERAL:
        return {
            "filed_under": (f"It is filed under the exercise '{folder_exercise_id}'. Extract information an AI "
                            f"exercise feedback system can use to tell a user what is wrong with their "
                            f"{folder_exercise_id} technique and why it matters"),
            "standard": f"standard/plain {folder_exercise_id}",
            "exercise_type_rule": "",
        }
    return {
        "filed_under": ("It is general material, not filed under one exercise. The feedback system covers four "
                        "exercises: squat, push-up, lunge and bicep curl. Extract information an AI exercise "
                        "feedback system can use to tell a user what is wrong with their technique in any of "
                        "these four exercises and why it matters"),
        "standard": "standard/plain form of that exercise",
        "exercise_type_rule": ("Set exercise_type to one of squat, push-up, lunge or bicep curl ONLY when the text "
                               "names that exercise explicitly; otherwise use 'Generic'. Do not guess the exercise "
                               "from the body part or the movement.\n\n"),
    }


# Per-call token usage, appended as JSON lines when set (main() --usage-log). v5 kept
# none, and the AI Studio usage page showed output ~6x the saved JSON: thinking tokens
# are billed as output, so they have to be logged to cost a run.
USAGE_LOG = None


def _log_usage(raw_message, label: str, folder_exercise_id: str, relevant: Optional[bool]) -> None:
    if not USAGE_LOG:
        return
    meta = getattr(raw_message, "usage_metadata", None) or {}
    resp = getattr(raw_message, "response_metadata", None) or {}
    row = {
        "source": label,
        "exercise": folder_exercise_id,
        "relevant": relevant,
        # the API's model_version (langchain_google_genai stores it as model_name), so
        # batches curated days apart can be shown to have used the same model
        "model_version": resp.get("model_name"),
        "finish_reason": resp.get("finish_reason"),
        "input_tokens": meta.get("input_tokens"),
        "cached_tokens": (meta.get("input_token_details") or {}).get("cache_read"),
        "output_tokens": meta.get("output_tokens"),
        "reasoning_tokens": (meta.get("output_token_details") or {}).get("reasoning"),
        "total_tokens": meta.get("total_tokens"),
    }
    with open(USAGE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def summarize_usage(path: str) -> str:
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    tot = {k: sum(r.get(k) or 0 for r in rows)
           for k in ("input_tokens", "cached_tokens", "output_tokens", "reasoning_tokens")}
    return f"{len(rows)} calls · " + " · ".join(f"{k} {v:,}" for k, v in tot.items())


def curate_knowledge(raw_text: str, folder_exercise_id: str = "general", label: str = "") -> Optional[dict]:
    # gemini-3.5-flash through round 2a; it was retired before round 3, and round 3 already ran
    # on gemini-3.6-flash (usage log model_version). Pinned here so the log and the code agree;
    # CURATOR_MODEL overrides it (docs/progress/t3_curation_status.md 1: never change it mid-round).
    llm = ChatGoogleGenerativeAI(model=CURATOR_MODEL, temperature=0.1)
    # include_raw keeps the AIMessage so its usage_metadata can be logged.
    structured_llm = llm.with_structured_output(ExtractedKnowledge, include_raw=True)

    prompt = PromptTemplate.from_template(
        "You are an elite sports science, personal trainer, and physical therapy expert.\n"
        "Your task is to analyze the following raw text retrieved from the web or documents.\n"
        "{filed_under}: proper form, common "
        "mistakes and their consequences, safety cues, joint/muscle mechanics.\n"
        "Mark the text NOT relevant if the exercise is only the vehicle for an unrelated outcome (cardiovascular "
        "risk, blood biochemistry, disease populations, training-program periodisation, equipment marketing), "
        "or if it is fluff, navigation text, advertising, or a reference list.\n\n"
        "{exercise_type_rule}"
        "{fault_codes}\n"
        "Every item in core_principles, common_mistakes, specific_findings, and consequences is an object "
        "{{\"text\": ..., \"applies_to_fault\": [...]}}. Tag each item's applies_to_fault with only the codes "
        "THAT ITEM directly speaks to, not every code the surrounding paragraph happens to mention. An item "
        "not about any known fault gets an empty list.\n\n"
        "Do NOT tag a fault code on an item in either of these two cases, even if the item's topic overlaps the "
        "fault - leave its applies_to_fault empty instead:\n"
        "  1. The item argues the 'mistake' is actually fine, harmless, or produces similar results to correct "
        "form (e.g. a hypertrophy study concluding a partial range of motion builds similar muscle to a full "
        "one). Tagging this would make the feedback system cite it as justification FOR the fault it is "
        "supposed to correct.\n"
        "  2. The item is specific to a named variant of the exercise that changes the mechanics (e.g. preacher "
        "curl, incline curl, cable curl, concentration curl are NOT the same movement as a "
        "{standard}) - UNLESS the item's guidance is stated as true for the standard movement too, not just "
        "that variant.\n\n"
        "IMPORTANT: core_principles and common_mistakes should capture the text's guidance even if it is general knowledge. "
        "Separately, populate specific_findings ONLY with concrete details that are specific to this source and go beyond "
        "generic textbook advice — exact numbers, angles, percentages, forces, EMG data, study sample sizes, or named "
        "conclusions. If the text is purely generic advice with no such specifics, leave specific_findings empty. Do not "
        "put a study's own methodology/protocol setup (e.g. 'the protocol required starting at X degrees on a Y-degree "
        "bench') into specific_findings just because it has exact numbers - that describes what the researchers did, "
        "not something a coach can tell a lifter; only extract it if the text also frames it as a result or guidance.\n\n"
        "Populate consequences with the harm mechanism behind a mistake, stated in the text: which joint, ligament, "
        "tendon, disc, or muscle takes the extra load, and what that risks for the lifter. If a mistake or principle "
        "sentence in the source already ends with its own consequence clause, split that clause into consequences "
        "rather than leaving it attached. Leave consequences empty if the text states no such mechanism.\n\n"
        "Note: this text may be one excerpt/section of a larger document (e.g. a methods or results section without an "
        "intro). Judge relevance and extract findings based on this excerpt alone — do not reject it just because it "
        "lacks setup/context that a full article would have.\n\n"
        "Raw Text to Analyze:\n{raw_text}\n"
    )
    
    chain = prompt | structured_llm
    
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = chain.invoke({
                "raw_text": raw_text,
                "fault_codes": _fault_code_block(folder_exercise_id),
                **_prompt_context(folder_exercise_id),
            })
            result = response["parsed"]
            _log_usage(response["raw"], label, folder_exercise_id,
                       None if result is None else result.is_relevant)
            if result is None:
                raise ValueError(f"structured output did not parse: {response.get('parsing_error')}")
            if not result.is_relevant:
                print("[REJECTED] Content is not relevant to exercise feedback.")
                return None
                
            print(f"[ACCEPTED] Relevant data found for: {result.exercise_type}")
            
            # Sleep slightly to avoid hitting the 15 RPM limit too fast
            time.sleep(4)
            out = result.model_dump()
            for field in ("core_principles", "common_mistakes", "specific_findings", "consequences"):
                for item in out[field]:
                    item["text"] = normalize_ocr_degrees(item["text"])
                    item["applies_to_fault"] = normalize_fault_tags(item["applies_to_fault"],
                                                                    folder_exercise_id)
            return out
            
        except Exception as e:
            error_msg = str(e).lower()
            if attempt == max_retries - 1:
                print(f"[ERROR] Failed during curation process after {max_retries} attempts: {e}")
                return None
            if "429" in error_msg or "quota" in error_msg or "resourceexhausted" in error_msg:
                print(f"[!] Rate limit hit (Attempt {attempt+1}/{max_retries}). Sleeping for 60 seconds...")
                time.sleep(60)
            else:
                # Transient errors (e.g. "Server disconnected without sending a response")
                # used to return None on the first hit with no retry, silently dropping the
                # window - it landed in neither curated_data nor excluded_from_kb (see
                # data\squat\Effect of hip adductor (Squat).pdf during the v5 full run).
                # Retrying like the rate-limit branch is the fix.
                print(f"[!] Transient error (Attempt {attempt+1}/{max_retries}): {e}. Retrying in 10 seconds...")
                time.sleep(10)

    print("[ERROR] Max retries reached. Skipping this document.")
    return None

def curate_text_block(text: str, source_label: str, folder_exercise_id: str) -> tuple:
    """Curates one document's text, splitting it into windows first if it's long.

    A single curate_knowledge() call always compresses its input down to the same
    handful of list items regardless of how much source material went in, so a long
    paper curated in one shot loses far more than a short one does. Curating each
    window separately - and gating relevance per-window instead of for the whole
    document - means a mixed-topic paper (e.g. an epidemiology study with one
    results section on exercise form) doesn't get thrown away wholesale just because
    parts of it don't match the topic.

    Returns (accepted, excluded): windows whose extracted exercise_type doesn't match
    folder_exercise_id are routed to `excluded` instead of `accepted` so they never reach
    curated_data/ (and therefore never get embedded under the wrong exercise_id).
    """
    if not text.strip():
        print(f"[SKIP] No text extracted from: {source_label}")
        return [], []

    if len(text) <= CURATION_CHUNK_SIZE:
        windows = [text]
    else:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CURATION_CHUNK_SIZE, chunk_overlap=CURATION_CHUNK_OVERLAP
        )
        windows = splitter.split_text(text)
        print(f"'{source_label}' is {len(text)} chars — curating in {len(windows)} windows instead of one shot.")

    accepted, excluded = [], []
    for i, window in enumerate(windows):
        if not window.strip():
            continue
        label = f"{source_label} [part {i+1}/{len(windows)}]" if len(windows) > 1 else source_label
        print(f"Sending {len(window)} characters to LLM for curation ({label})...")
        data = curate_knowledge(window, folder_exercise_id, label)
        if data:
            data["source"] = label
            # Window-level applies_to_fault is derived, not asked of the LLM (see
            # ExtractedKnowledge note): the union of each item's own tags. Only used by
            # is_exercise_mismatch()'s override below; retrieval reads the per-item tags.
            data["applies_to_fault"] = sorted({
                code
                for field in ("core_principles", "common_mistakes", "specific_findings", "consequences")
                for item in data[field]
                for code in item["applies_to_fault"]
            })
            # general/ is not an exercise, so the folder test would throw away every window
            # the LLM names an exercise for - the content we want. Those are routed per item
            # instead (route_general_window in process_data_directory).
            if folder_exercise_id != GENERAL and is_exercise_mismatch(
                    folder_exercise_id, data["exercise_type"], label, data["applies_to_fault"]):
                excluded.append(data)
            else:
                accepted.append(data)
    return accepted, excluded

def load_urls_main_content(urls):
    """Fetch each URL and return one Document holding only its main article body.

    Replaces AsyncHtmlLoader + Html2TextTransformer, which flattened the WHOLE page -
    navbar, "related articles" sidebar, footer, newsletter widgets. On the NASM blog that
    dragged GLP-1, cardio-zone and osteoporosis copy into the squat/lunge KB
    (docs/kb/kb_quality_assessment.md 3.4). trafilatura keeps the article and drops the
    chrome; a page it cannot extract is skipped with a warning rather than scraped whole.
    """
    import trafilatura
    from langchain_core.documents import Document

    docs = []
    for url in urls:
        html = trafilatura.fetch_url(url)
        if not html:
            print(f"[URL SKIP] could not fetch: {url}")
            continue
        text = trafilatura.extract(
            html, url=url,
            include_comments=False, include_tables=True,
            favor_recall=False,
        )
        if not text or len(text) < 200:
            print(f"[URL SKIP] no main content extracted ({len(text or '')} chars): {url}")
            continue
        print(f"[URL OK] {len(text)} chars of main content: {url}")
        docs.append(Document(page_content=text, metadata={"source": url}))
    return docs


# ---------------------------------------------------------
# 3. Process All Files in 'data' Folder
# ---------------------------------------------------------
PICKED_DIR = "picked"
# data/checked/ holds sources whose prefilter review is done but that are not curated yet
# (keep or drop). The folder is transparent: data/checked/<exercise>/x.pdf keeps the id
# data/<exercise>/x.pdf, so prefilter, batches, outputs and the split key stay the same.
CHECKED_DIR = "checked"


def logical_rel(rel_path: str) -> str:
    """Path under data/ with a leading checked/ removed ('.' for data/ itself)."""
    parts = rel_path.split(os.sep)
    if parts[0] == CHECKED_DIR:
        return os.sep.join(parts[1:]) or "."
    return rel_path


def locate_source(project_root: str, path: str) -> str:
    """Where an id 'data/<exercise>/...' lives on disk now: as is, or under data/checked/.
    data/picked/ is deliberately not searched - those sources are already curated."""
    direct = os.path.join(project_root, path)
    if os.path.exists(direct):
        return direct
    parts = path.replace("\\", "/").split("/")
    if parts[0] == "data":
        checked = os.path.join(project_root, "data", CHECKED_DIR, *parts[1:])
        if os.path.exists(checked):
            return checked
    return direct


def _routed_output_path(output_base_folder: str, exercise_id: str, stem: str) -> str:
    """Where a general/ source's items routed to an exercise are written. ingest.py reads
    exercise_id from the first folder level, and the general__ prefix keeps the origin visible."""
    return os.path.join(output_base_folder, exercise_id, f"general__{stem}_curated.json")


def process_data_directory(base_folder: str, output_base_folder: str, excluded_base_folder: str,
                            legacy_excluded_folders: tuple = (), skip_paths: dict = None,
                            skip_urls: dict = None, only: str = None, batch: set = None):
    """legacy_excluded_folders: earlier excluded_from_kb/ dirs (e.g. the v4 one) to also check
    for "<stem>_curated_offtopic.json" markers, so a source someone hand-excluded as off-topic
    stays excluded when re-curating into a fresh output_base_folder/excluded_base_folder pair
    (e.g. building curated_data_v5/ alongside the untouched v4 curated_data/). Only the
    "_offtopic" marker is honoured from legacy folders - "_mismatch"/"_curated_mismatch" markers
    were produced by the OLD name-substring exercise check and should be re-judged fresh by
    is_exercise_mismatch() here, which now also trusts per-item applies_to_fault tags.

    skip_paths / skip_urls: the 'drop' entries of the T3a prefilter (load_skip_list),
    {absolute path or url: reason}. Those sources are skipped and logged, not curated.
    only: curate just the files whose path contains this substring (a trial run on one
    source; the output lands where the full run expects it, so it is not curated twice).
    batch: absolute, case-normalised paths to curate (load_batch); None means every file.
    """
    if not os.path.exists(base_folder):
        print(f"Error: Folder {base_folder} not found.")
        return
    skip_paths, skip_urls = skip_paths or {}, skip_urls or {}

    for root, dirs, files in os.walk(base_folder):
        # data/picked/ holds sources already curated, moved out of data/<exercise>/ after
        # the fact (their KB id is still the old data/<exercise>/... path). Walking it
        # would treat "picked" as an exercise and curate them a second time.
        if os.path.abspath(root) == os.path.abspath(base_folder):
            dirs[:] = [d for d in dirs if d != PICKED_DIR]
        for file in files:
            # Skip files that are already curated JSONs to avoid infinite loops
            if file.endswith('_curated.json'):
                continue
                
            file_path = os.path.join(root, file)
            # rel_path / source_path drop a leading checked/ (see CHECKED_DIR); file_path
            # is only used to read the file.
            rel_path = logical_rel(os.path.relpath(root, base_folder))
            source_path = os.path.normpath(os.path.join(base_folder, rel_path, file))
            source_key = os.path.normcase(os.path.abspath(source_path))
            if only and only.replace("\\", "/") not in source_path.replace(os.sep, "/"):
                continue
            if batch is not None and source_key not in batch:
                continue
            if source_key in skip_paths:
                print(f"[PREFILTER DROP] {file_path} - {skip_paths[source_key]}")
                continue

            # Determine output path early to skip if already processed
            folder_exercise_id = 'general' if rel_path == '.' else rel_path.split(os.sep)[0]
            output_dir = os.path.join(output_base_folder, rel_path)
            filename_without_ext = os.path.splitext(file)[0]
            
            if file == 'urls.txt':
                output_filename = f"{filename_without_ext}_curated_detailed.json"
            else:
                output_filename = f"{filename_without_ext}_curated.json"
                
            output_path = os.path.join(output_dir, output_filename)
            excluded_filename = f"{filename_without_ext}_mismatch.json"
            excluded_path = os.path.join(excluded_base_folder, rel_path, excluded_filename)
            # migrate_exclude_mismatches.py names its output after the curated JSON
            # ("<stem>_curated_mismatch.json"), and hand-excluded off-topic sources are
            # parked as "<stem>_curated_offtopic.json". Recognise all three, otherwise a
            # source that was deliberately dropped gets silently re-curated on the next
            # run (this happened to the BFR bicep-curl paper).
            already_excluded = any(os.path.exists(os.path.join(excluded_base_folder, rel_path, name)) for name in (
                excluded_filename,
                f"{filename_without_ext}_curated_mismatch.json",
                f"{filename_without_ext}_curated_offtopic.json",
            )) or any(
                os.path.exists(os.path.join(legacy_folder, rel_path, f"{filename_without_ext}_curated_offtopic.json"))
                for legacy_folder in legacy_excluded_folders
            )

            routed_done = folder_exercise_id == GENERAL and any(
                os.path.exists(_routed_output_path(output_base_folder, ex, filename_without_ext))
                for ex in ERROR_TAXONOMY)
            if os.path.exists(output_path) or already_excluded or routed_done:
                print(f"Skipping already processed file: {file_path}")
                continue
                
            print(f"\nProcessing file: {file_path}")
            
            docs = []
            if file.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                docs = loader.load()
            elif file.endswith('.txt') and file != 'urls.txt':
                loader = TextLoader(file_path, encoding='utf-8')
                docs = loader.load()
            elif file == 'urls.txt':
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        urls = [line.strip() for line in f.readlines() if line.strip()]
                    for url in [u for u in urls if u in skip_urls]:
                        print(f"[PREFILTER DROP] {url} - {skip_urls[url]}")
                    docs = load_urls_main_content([u for u in urls if u not in skip_urls])
                except Exception as e:
                    print(f"Error loading URLs: {e}")
            
            if not docs:
                print(f"Skipping or unable to load: {file}")
                continue

            curated_results = []
            excluded_results = []

            if file == 'urls.txt':
                for i, doc in enumerate(docs):
                    url_source = doc.metadata.get('source', f'URL #{i+1}')
                    accepted, excluded = curate_text_block(doc.page_content, f"{source_path} ({url_source})", folder_exercise_id)
                    curated_results.extend(accepted)
                    excluded_results.extend(excluded)
            else:
                # Combine all pages of the document into one text block; curate_text_block
                # will window it internally if it's too long for a single curation pass.
                full_text = "\n\n".join([doc.page_content for doc in docs])
                accepted, excluded = curate_text_block(full_text, source_path, folder_exercise_id)
                curated_results.extend(accepted)
                excluded_results.extend(excluded)

            if folder_exercise_id == GENERAL and curated_results:
                by_ex = {}
                for window in curated_results:
                    for ex, routed in route_general_window(window).items():
                        by_ex.setdefault(ex, []).append(routed)
                curated_results = by_ex.pop(GENERAL, [])
                for ex, windows in by_ex.items():
                    path = _routed_output_path(output_base_folder, ex, filename_without_ext)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(windows, f, indent=2, ensure_ascii=False)
                    n = sum(len(w[field]) for w in windows for field in ITEM_FIELDS)
                    print(f"Routed {n} item(s) from general/ to {ex}: {path}")

            if curated_results:
                os.makedirs(output_dir, exist_ok=True)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(curated_results, f, indent=2, ensure_ascii=False)
                print(f"Saved structured data to: {output_path}")

            if excluded_results:
                os.makedirs(os.path.dirname(excluded_path), exist_ok=True)
                with open(excluded_path, 'w', encoding='utf-8') as f:
                    json.dump(excluded_results, f, indent=2, ensure_ascii=False)
                print(f"Excluded {len(excluded_results)} mismatched window(s) to: {excluded_path}")

def main():
    import argparse

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)

    ap = argparse.ArgumentParser(description="Curate raw sources under data/ into structured KB JSON.")
    ap.add_argument("--data", default=os.path.join(project_root, "data"),
                     help="input folder, e.g. data/<exercise>/*.pdf|urls.txt (default: ./data)")
    ap.add_argument("--out", default=os.path.join(project_root, "curated_data"),
                     help="output folder for accepted windows (default: ./curated_data)")
    ap.add_argument("--excluded", default=os.path.join(project_root, "excluded_from_kb"),
                     help="output folder for excluded (mismatched) windows (default: ./excluded_from_kb)")
    ap.add_argument("--legacy-excluded", action="append", default=[],
                     help="an earlier excluded_from_kb/ folder to also check for "
                          "'<stem>_curated_offtopic.json' hand-exclusion markers, so a source "
                          "already judged off-topic there is not re-curated into a fresh --out "
                          "(repeatable; e.g. --legacy-excluded ./excluded_from_kb when curating "
                          "into curated_data_v5 alongside the untouched v4 curated_data)")
    ap.add_argument("--skip-list", default=None,
                     help="T3a prefilter JSON (e.g. data_pipeline/prefilter_v6.json): files and URLs "
                          "with decision 'drop' are skipped and logged; refuses to run while any "
                          "entry is 'pending'")
    ap.add_argument("--only", default=None,
                     help="curate only files whose path contains this substring (trial run on one source)")
    ap.add_argument("--usage-log", default=None,
                     help="append one JSON line of token usage per LLM call to this file")
    ap.add_argument("--batch", nargs=2, metavar=("BATCHES_JSON", "NAME"), default=None,
                     help="curate only the files of one named batch, e.g. "
                          "data_pipeline/curation_batches_v6.json round1")
    args = ap.parse_args()
    skip_paths, skip_urls = load_skip_list(args.skip_list, project_root) if args.skip_list else ({}, {})
    batch = load_batch(args.batch[0], args.batch[1], project_root) if args.batch else None
    global USAGE_LOG
    USAGE_LOG = args.usage_log

    print("Starting curation process...")
    print(f"Input Directory: {args.data}")
    print(f"Output Directory: {args.out}")
    print(f"Excluded (mismatch) Directory: {args.excluded}")
    if args.legacy_excluded:
        print(f"Legacy excluded folders (offtopic markers only): {args.legacy_excluded}")
    if args.skip_list:
        print(f"Skip list: {args.skip_list} ({len(skip_paths)} files, {len(skip_urls)} URLs dropped)")
    if batch is not None:
        print(f"Batch: {args.batch[1]} from {args.batch[0]} ({len(batch)} files)")

    process_data_directory(args.data, args.out, args.excluded, tuple(args.legacy_excluded),
                           skip_paths, skip_urls, args.only, batch)
    print("\nCuration process finished.")
    if USAGE_LOG and os.path.exists(USAGE_LOG):
        print(f"Token usage ({USAGE_LOG}): {summarize_usage(USAGE_LOG)}")

if __name__ == "__main__":
    main()

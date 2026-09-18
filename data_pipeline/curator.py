import os
import re
import sys
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# error_taxonomy.py lives in the project root, one level up from data_pipeline/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from error_taxonomy import faults_for_exercise
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
    # whose only link to the exercise was its name (docs/kb_quality_assessment.md 3.1/3.4).
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
    "lunge": ("lunge",),
}


def _norm(s: str) -> str:
    return s.lower().replace("-", "").replace("_", "").replace(" ", "")


# PyPDFLoader renders the degree sign in several journal PDFs as a trailing "8" glued to
# the number ("1208" for 120°, "90 8" for 90°) or as the raw glyph name "/C176". The LLM
# notices and annotates it - "1208 (120 degrees)", "90 degrees (noted as 900 in text)" -
# but the annotation ends up in the chunk, and the feedback model then quotes "1208" to
# the user as if it were a number (compare_output/ab_v7.md, squat). Applied to every list
# item the curator returns; the rules are the exact shapes seen in kb_local_curated_v4
# (docs/kb_quality_assessment.md 7.3), nothing more speculative than that.
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

def _fault_code_block(folder_exercise_id: str) -> str:
    faults = faults_for_exercise(folder_exercise_id)
    if not faults:
        return "KNOWN FAULT CODES for this exercise: (none defined)"
    lines = [f'  - "{code}": {desc}' for code, desc in faults.items()]
    return "KNOWN FAULT CODES for this exercise (use verbatim in applies_to_fault):\n" + "\n".join(lines)


def curate_knowledge(raw_text: str, folder_exercise_id: str = "general") -> Optional[dict]:
    # Using gemini-3.5-flash
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.1)
    structured_llm = llm.with_structured_output(ExtractedKnowledge)

    prompt = PromptTemplate.from_template(
        "You are an elite sports science, personal trainer, and physical therapy expert.\n"
        "Your task is to analyze the following raw text retrieved from the web or documents.\n"
        "It is filed under the exercise '{exercise_id}'. Extract information an AI exercise feedback system can use "
        "to tell a user what is wrong with their {exercise_id} technique and why it matters: proper form, common "
        "mistakes and their consequences, safety cues, joint/muscle mechanics.\n"
        "Mark the text NOT relevant if the exercise is only the vehicle for an unrelated outcome (cardiovascular "
        "risk, blood biochemistry, disease populations, training-program periodisation, equipment marketing), "
        "or if it is fluff, navigation text, advertising, or a reference list.\n\n"
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
        "curl, incline curl, cable curl, concentration curl are NOT the same movement as a standard/plain "
        "{exercise_id}) - UNLESS the item's guidance is stated as true for the standard movement too, not just "
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
            result = chain.invoke({
                "raw_text": raw_text,
                "exercise_id": folder_exercise_id,
                "fault_codes": _fault_code_block(folder_exercise_id),
            })
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
        data = curate_knowledge(window, folder_exercise_id)
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
            if is_exercise_mismatch(folder_exercise_id, data["exercise_type"], label,
                                    data["applies_to_fault"]):
                excluded.append(data)
            else:
                accepted.append(data)
    return accepted, excluded

def load_urls_main_content(urls):
    """Fetch each URL and return one Document holding only its main article body.

    Replaces AsyncHtmlLoader + Html2TextTransformer, which flattened the WHOLE page -
    navbar, "related articles" sidebar, footer, newsletter widgets. On the NASM blog that
    dragged GLP-1, cardio-zone and osteoporosis copy into the squat/lunge KB
    (docs/kb_quality_assessment.md 3.4). trafilatura keeps the article and drops the
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
def process_data_directory(base_folder: str, output_base_folder: str, excluded_base_folder: str,
                            legacy_excluded_folders: tuple = ()):
    """legacy_excluded_folders: earlier excluded_from_kb/ dirs (e.g. the v4 one) to also check
    for "<stem>_curated_offtopic.json" markers, so a source someone hand-excluded as off-topic
    stays excluded when re-curating into a fresh output_base_folder/excluded_base_folder pair
    (e.g. building curated_data_v5/ alongside the untouched v4 curated_data/). Only the
    "_offtopic" marker is honoured from legacy folders - "_mismatch"/"_curated_mismatch" markers
    were produced by the OLD name-substring exercise check and should be re-judged fresh by
    is_exercise_mismatch() here, which now also trusts per-item applies_to_fault tags.
    """
    if not os.path.exists(base_folder):
        print(f"Error: Folder {base_folder} not found.")
        return

    for root, dirs, files in os.walk(base_folder):
        for file in files:
            # Skip files that are already curated JSONs to avoid infinite loops
            if file.endswith('_curated.json'):
                continue
                
            file_path = os.path.join(root, file)
            
            # Determine output path early to skip if already processed
            rel_path = os.path.relpath(root, base_folder)
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

            if os.path.exists(output_path) or already_excluded:
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
                    docs = load_urls_main_content(urls)
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
                    accepted, excluded = curate_text_block(doc.page_content, f"{file_path} ({url_source})", folder_exercise_id)
                    curated_results.extend(accepted)
                    excluded_results.extend(excluded)
            else:
                # Combine all pages of the document into one text block; curate_text_block
                # will window it internally if it's too long for a single curation pass.
                full_text = "\n\n".join([doc.page_content for doc in docs])
                accepted, excluded = curate_text_block(full_text, file_path, folder_exercise_id)
                curated_results.extend(accepted)
                excluded_results.extend(excluded)

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
    args = ap.parse_args()

    print("Starting curation process...")
    print(f"Input Directory: {args.data}")
    print(f"Output Directory: {args.out}")
    print(f"Excluded (mismatch) Directory: {args.excluded}")
    if args.legacy_excluded:
        print(f"Legacy excluded folders (offtopic markers only): {args.legacy_excluded}")

    process_data_directory(args.data, args.out, args.excluded, tuple(args.legacy_excluded))
    print("\nCuration process finished.")

if __name__ == "__main__":
    main()

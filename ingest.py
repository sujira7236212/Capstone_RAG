import os
import json
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres.vectorstores import PGVector

import embedding_config

# Load variables from .env file (e.g. GOOGLE_API_KEY, DATABASE_URL)
load_dotenv()

import re



def short_source_name(raw_source):
    """Curator `source` labels are absolute paths plus a window marker, e.g.
    'C:/.../data/squat/TheBackSquat.pdf [part 3/22]' or
    'C:/.../data/squat/urls.txt (https://blog.nasm.org/biomechanics-of-the-squat)'.
    Reduce to a citable stem ('TheBackSquat' / 'blog.nasm.org/...') for the embed header."""
    if not raw_source:
        return "knowledge base"
    url = re.search(r"https?://([^\s)]+)", raw_source)
    if url:
        # Some NASM articles only survive on the Wayback Machine; cite the original
        # address, not the archive wrapper.
        return re.sub(r"^web\.archive\.org/web/\d+/https?://", "", url.group(1)).rstrip("/")
    base = re.sub(r"\s*\[part \d+/\d+\]\s*$", "", raw_source).strip()
    base = base.replace("\\", "/").rsplit("/", 1)[-1]
    base = re.sub(r"\.(pdf|txt|json)$", "", base, flags=re.IGNORECASE)
    # Paper titles run to 150+ chars; all-MiniLM-L6-v2 truncates at 256 tokens and a
    # header that long would out-weigh a one-sentence item in its own embedding.
    return base if len(base) <= 60 else base[:57].rstrip() + "..."

def load_documents_from_folder(base_folder):
    """
    Loads PDF and JSON files from a specific folder structure:
    data/{exercise_id}/file.pdf
    It will extract {exercise_id} from the folder name and inject it into metadata.
    """
    all_documents = []
    
    if not os.path.exists(base_folder):
        print(f"Warning: Folder {base_folder} not found. Please create it and add files.")
        return all_documents

    for root, dirs, files in os.walk(base_folder):
        # Extract exercise_id from folder name (e.g., squat, pushup)
        # assuming structure is data/squat/squat_guide.pdf
        rel_path = os.path.relpath(root, base_folder)
        if rel_path == '.':
            # If the file is directly in the data/ folder, default to 'general'
            exercise_id = 'general'
        else:
            # The immediate subfolder name is the exercise_id
            exercise_id = rel_path.split(os.sep)[0]
        
        for file in files:
            file_path = os.path.join(root, file)
            print(f"Processing: {file_path} (Exercise ID: {exercise_id})")
            
            docs = []
            if file.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                docs = loader.load()
            elif file.endswith('.json'):
                # Curated JSON is a list of per-window objects, each holding
                # core_principles/common_mistakes/specific_findings(/consequences) lists.
                # Embedding the whole file as one json.dumps() blob would later get sliced
                # mid-syntax by RecursiveCharacterTextSplitter, mixing unrelated
                # fields/windows into the same chunk. Instead we emit one Document per
                # individual list item, tagged with item_kind so retrieval can filter
                # principle vs mistake vs finding vs consequence.
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    from langchain_core.documents import Document
                    for window in data:
                        source = window.get("source", file_path)
                        window_meta = {
                            "source": source,
                            "content_type": window.get("content_type", ""),
                            "focus_area": window.get("focus_area", ""),
                            "window_exercise_type": window.get("exercise_type", ""),
                            # v4's window-level fault codes (one shared set broadcast onto
                            # every item - imprecise, kept only so v4 files stay queryable
                            # the old way). v5 items carry their own applies_to_fault below,
                            # stored under a different key so this doesn't shadow it.
                            "window_applies_to_fault": window.get("applies_to_fault", []) or [],
                        }
                        for kind, key in (
                            ("principle", "core_principles"),
                            ("mistake", "common_mistakes"),
                            ("finding", "specific_findings"),
                            ("consequence", "consequences"),
                        ):
                            for item in window.get(key, []):
                                # v5 items are {"text": ..., "applies_to_fault": [...]};
                                # v4 items are bare strings with no per-item tag - keep
                                # ingesting those too so curated_data/ (v4) stays usable.
                                if isinstance(item, dict):
                                    text, tags = item.get("text", ""), item.get("applies_to_fault", []) or []
                                else:
                                    text, tags = item or "", []
                                text = text.strip()
                                if not text:
                                    continue
                                # Embed the bare item. A "[exercise | kind | source]" prefix
                                # was tried (docs/kb_quality_assessment.md 5.3) and measured
                                # on kb_local_curated_v4: it only shifts the distance scale
                                # - a plain query lands ~0.1-0.2 further from everything, a
                                # prefixed query lands within 0.40 of every chunk of that
                                # exercise/kind - so the v6 thresholds stop meaning
                                # anything. It also adds nothing retrieval can use, because
                                # _search already filters on exercise_id + item_kind. The
                                # citable header is still built per-hit at query time.
                                docs.append(Document(
                                    page_content=text,
                                    metadata={
                                        **window_meta,
                                        "item_kind": kind,
                                        "text": text,
                                        "applies_to_fault": tags,
                                        # PGVector's JSONB filter only supports scalar
                                        # comparisons via ->>'field' (see
                                        # test_rag_compare.py _search): a list field can't
                                        # be filtered with $in/$like. Store the same tags as
                                        # a delimited string so "fault_tags LIKE
                                        # '%|<code>|%'" is an exact-token containment test.
                                        "fault_tags": ("|" + "|".join(tags) + "|") if tags else "",
                                        "source_short": short_source_name(source),
                                    },
                                ))
                except Exception as e:
                    print(f"Error loading JSON {file_path}: {e}")
            elif file == 'urls.txt':
                # Read URLs and convert them to Markdown using AsyncHtmlLoader + Html2TextTransformer
                from langchain_community.document_loaders import AsyncHtmlLoader
                from langchain_community.document_transformers import Html2TextTransformer
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        urls = [line.strip() for line in f.readlines() if line.strip()]
                    if urls:
                        print(f"Loading and converting {len(urls)} URLs to Markdown from {file_path}...")
                        loader = AsyncHtmlLoader(urls)
                        html_docs = loader.load()
                        html2text = Html2TextTransformer()
                        docs = html2text.transform_documents(html_docs)
                        # Mark these as markdown for chunking strategy
                        for doc in docs:
                            doc.metadata["doc_type"] = "markdown"
                except Exception as e:
                    print(f"Error loading URLs {file_path}: {e}")
            elif file.endswith('.txt'):
                # General Text file loader
                from langchain_community.document_loaders import TextLoader
                try:
                    loader = TextLoader(file_path, encoding='utf-8')
                    docs = loader.load()
                except Exception as e:
                    print(f"Error loading Text file {file_path}: {e}")
                    
            # Inject exercise_id into metadata
            for doc in docs:
                doc.metadata["exercise_id"] = exercise_id
                
            all_documents.extend(docs)

    return all_documents


import argparse

def main():
    parser = argparse.ArgumentParser(description="Ingest data into PGVector.")
    parser.add_argument('--mode', type=str, choices=['gemini', 'local'], default=embedding_config.DEFAULT_MODE,
                        help="Embedding mode: 'gemini' (paid API, default) or 'local' (offline MiniLM fallback).")
    parser.add_argument('--collection', type=str, default=None,
                        help="Override the default collection name (e.g. to ingest into a fresh "
                             "collection for testing without touching the existing one).")
    parser.add_argument('--free-tier', action='store_true',
                        help="Throttle Gemini batches to the free-tier rate limit (small batches, "
                             "60s sleep between them). Off by default now that the project is on "
                             "the paid tier - pass this only if you've actually dropped back to free.")
    parser.add_argument('--data-folder', type=str, default="./curated_data",
                        help="Curated JSON folder to ingest (default: ./curated_data). Point this at "
                             "curated_data_v5 to ingest a re-curated KB into a separate collection "
                             "without touching the v4 one.")
    args = parser.parse_args()
    mode = args.mode

    print(f"Starting Data Ingestion process with PostgreSQL (pgvector) in [{mode.upper()}] mode...")

    # 1. Setup connection
    connection = embedding_config.get_connection(mode)

    # 2. Load data
    # We now read from the curated JSON folder to ensure only high-quality data is ingested
    data_folder = args.data_folder
    documents = load_documents_from_folder(data_folder)

    if not documents:
        print("Error: No valid data found in ./curated_data to process.")
        print("Hint: Place your files like this: ./data/squat/squat.pdf")
        return

    # 3. Text Chunking
    print("Splitting data into smaller chunks...")
    from langchain_text_splitters import MarkdownHeaderTextSplitter
    
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    
    # Separate markdown docs (from URLs or .md files) from other docs
    markdown_docs = [
        doc for doc in documents 
        if doc.metadata.get("doc_type") == "markdown" or doc.metadata.get("source", "").endswith(".md")
    ]
    other_docs = [doc for doc in documents if doc not in markdown_docs]
    
    md_splits = []
    for doc in markdown_docs:
        # MarkdownHeaderTextSplitter takes raw string text
        splits_for_doc = markdown_splitter.split_text(doc.page_content)
        # Re-attach original metadata (like exercise_id, source) to the new splits
        for split in splits_for_doc:
            split.metadata.update(doc.metadata)
        md_splits.extend(splits_for_doc)
        
    print(f"Processed {len(markdown_docs)} markdown documents into {len(md_splits)} sections.")
    
    # Pass 2: Ensure no chunk exceeds the maximum size limit using RecursiveCharacterTextSplitter
    # We apply this to both the markdown splits and the non-markdown documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    final_md_splits = text_splitter.split_documents(md_splits)
    final_other_splits = text_splitter.split_documents(other_docs)
    
    splits = final_md_splits + final_other_splits
    print(f"Successfully split into {len(splits)} total chunks")
    
    # Deduplicate splits before embedding to prevent PostgreSQL ON CONFLICT errors
    import hashlib
    unique_splits = []
    seen_ids = set()
    for doc in splits:
        unique_string = doc.page_content + str(doc.metadata)
        doc_id = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
        if doc_id not in seen_ids:
            seen_ids.add(doc_id)
            unique_splits.append(doc)
            
    splits = unique_splits
    print(f"After deduplication, {len(splits)} unique chunks remain.")

    # 4. Create Embeddings and save to pgvector
    print(f"Converting text to vectors with [{mode.upper()}] embeddings and saving to pgvector...")
    embeddings = embedding_config.get_embeddings(mode)
    collection_name = args.collection or embedding_config.default_collection(mode)

    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True,
    )
    
    print("Checking database for existing chunks to avoid re-embedding...")
    total_chunks = len(splits)
    already_ingested = 0
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(connection)
        with engine.connect() as session:
            query = text("""
                SELECT e.id 
                FROM langchain_pg_embedding e
                JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                WHERE c.name = :collection_name
            """)
            result = session.execute(query, {"collection_name": collection_name})
            existing_ids = {row[0] for row in result}
            
            new_splits = []
            for doc in splits:
                # Include collection_name in the hash: langchain_pg_embedding.id is a
                # GLOBAL primary key across every collection in this schema, not scoped
                # per-collection. Hashing on content+metadata alone means identical
                # content already embedded under a different collection (e.g. an older
                # test collection) silently no-ops here via ON CONFLICT DO NOTHING,
                # leaving this collection with zero rows for that content.
                unique_string = collection_name + "::" + doc.page_content + str(doc.metadata)
                doc_id = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
                if doc_id not in existing_ids:
                    new_splits.append(doc)
            
            already_ingested = total_chunks - len(new_splits)
            print(f"Found {already_ingested} existing chunks. {len(new_splits)} new chunks will be embedded.")
            if total_chunks > 0:
                print(f"Current Ingestion Progress: {already_ingested}/{total_chunks} chunks ({(already_ingested/total_chunks)*100:.2f}%)")
            
            unique_sources = {doc.metadata.get("source") for doc in documents if doc.metadata.get("source")}
            total_files = len(unique_sources)
            
            if total_files > 0:
                query_files = text("""
                    SELECT DISTINCT e.cmetadata->>'source'
                    FROM langchain_pg_embedding e
                    JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                    WHERE c.name = :collection_name
                """)
                result_files = session.execute(query_files, {"collection_name": collection_name})
                db_sources = {row[0] for row in result_files if row[0]}
                
                ingested_current_files = unique_sources.intersection(db_sources)
                ingested_files_count = len(ingested_current_files)
                
                print(f"File Ingestion Progress: {ingested_files_count}/{total_files} files ({(ingested_files_count/total_files)*100:.2f}%) based on data folder")
            
            splits = new_splits
            
            if not splits:
                print("No new chunks to ingest. Exiting.")
                return
    except Exception as e:
        print(f"Warning: Could not fetch existing IDs. Proceeding with all chunks. Error: {e}")

    # Add documents to database in batches
    import time
    if mode == 'gemini' and args.free_tier:
        batch_size = 30  # small batches + sleep below to stay under the free-tier per-minute cap
    else:
        batch_size = 100
    total_batches = (len(splits) - 1) // batch_size + 1
    
    import hashlib
    
    processed_count = already_ingested
    
    for i in range(0, len(splits), batch_size):
        batch = splits[i:i+batch_size]
        
        # Generate deterministic IDs for deduplication (collection-scoped - see note above)
        batch_ids = []
        batch_tokens = 0
        for doc in batch:
            unique_string = collection_name + "::" + doc.page_content + str(doc.metadata)
            doc_id = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
            batch_ids.append(doc_id)
            batch_tokens += len(doc.page_content) // 4 # Rough estimate: 1 token ≈ 4 characters
            
        if mode == 'gemini' and args.free_tier:
            remaining_tpm = 1_000_000 - batch_tokens
            print(f"Adding batch {i//batch_size + 1} of {total_batches} (size: {len(batch)}, ~{batch_tokens} tokens)...")
            print(f"  -> Estimated Free Tier Tokens left this minute: ~{remaining_tpm:,} / 1,000,000")
        else:
            print(f"Adding batch {i//batch_size + 1} of {total_batches} (size: {len(batch)})...")

        # Paid tier still has a per-minute cap (hit RESOURCE_EXHAUSTED at batch 14/24
        # with zero delay - see docs/kb_quality_assessment.md section 10), just a much
        # higher one than free tier. Retry that one batch with backoff instead of
        # aborting the whole run over a transient 429.
        max_retries = 4
        for attempt in range(max_retries):
            try:
                vectorstore.add_documents(batch, ids=batch_ids)
                processed_count += len(batch)
                if total_chunks > 0:
                    percentage = (processed_count / total_chunks) * 100
                    print(f"Progress Update: {processed_count}/{total_chunks} chunks ingested ({percentage:.2f}%)")

                if mode == 'gemini' and args.free_tier and i + batch_size < len(splits):
                    print("Sleeping for 60 seconds to respect Gemini Free Tier API rate limits...")
                    time.sleep(60)
                elif mode == 'gemini' and i + batch_size < len(splits):
                    time.sleep(3)  # small courtesy gap between batches on the paid tier
                break
            except Exception as e:
                error_msg = str(e).lower()
                is_daily_limit = "per day" in error_msg or "daily" in error_msg or "per_day" in error_msg or "perday" in error_msg
                is_minute_limit = ("per minute" in error_msg or "per_minute" in error_msg or "429" in error_msg
                                    or "resourceexhausted" in error_msg or "quota" in error_msg)

                if is_minute_limit and not is_daily_limit and attempt < max_retries - 1:
                    backoff = 20 * (attempt + 1)
                    print(f"\n[!] Rate-limited (attempt {attempt + 1}/{max_retries}); "
                          f"retrying batch {i//batch_size + 1} in {backoff}s...")
                    time.sleep(backoff)
                    continue

                print(f"\n[!] Error adding batch {i//batch_size + 1}: {str(e)}")
                print("\n==================================================")
                if is_daily_limit:
                    print("[!] การทำงานหยุดลงกลางคันเนื่องจาก: ติดข้อจำกัดโควต้าต่อวัน (Per Day Limit)")
                    print("คุณเรียกใช้งาน API ครบจำนวนครั้งสูงสุดต่อวันแล้ว")
                    print("คำแนะนำ: คุณต้องรอข้ามวันเพื่อให้ระบบรีเซ็ตโควต้า (โดยปกติประมาณเที่ยงคืนเวลา PT) จึงจะสามารถรันต่อได้")
                elif is_minute_limit:
                    print("[!] การทำงานหยุดลงกลางคันเนื่องจาก: ติดข้อจำกัดโควต้าต่อนาที (Per Minute Limit) ซ้ำหลายครั้ง")
                    print("คำแนะนำ: กรุณารอประมาณ 1-2 นาที แล้วรันคำสั่งเดิมซ้ำอีกครั้ง")
                else:
                    print(f"[!] การทำงานหยุดลงกลางคันเนื่องจากข้อผิดพลาดอื่น: {e.__class__.__name__}")
                    print("อาจจะเป็นปัญหาเกี่ยวกับการเชื่อมต่อฐานข้อมูล หรือระบบเครือข่าย")

                print("==================================================")
                print("\nไม่ต้องกังวล! ข้อมูลก่อนหน้านี้ที่ทำสำเร็จไปแล้วถูกบันทึกลง Database เรียบร้อยแล้ว")
                print("เมื่อคุณรันใหม่ ระบบจะตรวจสอบและข้าม (Skip) ข้อมูลที่เคยทำไปแล้วให้โดยอัตโนมัติครับ\n")
                return
    
    print("Done! Data ingestion process completed.")

if __name__ == "__main__":
    main()

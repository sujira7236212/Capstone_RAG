import os
import json
from ingest import load_documents_from_folder
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

def main():
    print("--- 🔍 Debugging Chunking Strategy ---")
    data_folder = "./data"
    documents = load_documents_from_folder(data_folder)
    
    if not documents:
        print("No documents found in ./data to test. Please add files or urls.txt first.")
        return
        
    print(f"Loaded {len(documents)} raw documents.")
    
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    
    markdown_docs = [
        doc for doc in documents 
        if doc.metadata.get("doc_type") == "markdown" or doc.metadata.get("source", "").endswith(".md")
    ]
    other_docs = [doc for doc in documents if doc not in markdown_docs]
    
    md_splits = []
    for doc in markdown_docs:
        splits_for_doc = markdown_splitter.split_text(doc.page_content)
        for split in splits_for_doc:
            split.metadata.update(doc.metadata)
        md_splits.extend(splits_for_doc)
        
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    final_md_splits = text_splitter.split_documents(md_splits)
    final_other_splits = text_splitter.split_documents(other_docs)
    
    splits = final_md_splits + final_other_splits
    print(f"Total chunks generated: {len(splits)}\n")
    
    # Save the output to a text file for easy inspection
    output_file = "chunk_results.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(splits):
            f.write(f"=== Chunk {i+1} ===\n")
            f.write(f"Metadata: {json.dumps(chunk.metadata, ensure_ascii=False)}\n")
            f.write(f"Content:\n{chunk.page_content}\n")
            f.write("="*40 + "\n\n")
            
    print(f"✅ Saved all chunks to {output_file}. Please open this file to review the results.")

if __name__ == "__main__":
    main()

import os
import json
import re
import time
from datetime import datetime

import fitz  
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

# --- CONFIGURATION ---
INPUT_JSON_PATH = "input/challenge1b_input.json"
PDF_DIRECTORY = "input/pdfs"
OUTPUT_JSON_PATH = "output/challenge1b_output.json"
MODEL_NAME = SentenceTransformer('./models/all-MiniLM-L6-v2')
TOP_K_SECTIONS = 5

def create_paragraph_chunks(doc):
    """
    Creates chunks based on paragraphs. This is a robust fallback when
    structural parsing (heading detection) is unreliable.
    """
    chunks = []
    for page_num, page in enumerate(doc, 1):
        page_text = page.get_text("text")
        paragraphs = page_text.split('\n\n')
        for para in paragraphs:
            cleaned_para = para.strip()
            if len(cleaned_para) > 100:
                chunks.append({
                    "page_num": page_num,
                    "content": cleaned_para
                })
    return chunks

def generate_refined_text(chunk_content, query, model):
    """Finds the single most relevant sentence in a chunk."""
    sentences = re.split(r'(?<=[.?!])\s+', chunk_content)
    sentences = [s.strip() for s in sentences if len(s.strip().split()) > 4]

    if not sentences:
        return chunk_content[:500] 

    query_embedding = model.encode(query, convert_to_tensor=True)
    sentence_embeddings = model.encode(sentences, convert_to_tensor=True)

    similarities = cos_sim(query_embedding, sentence_embeddings)
    best_sentence_index = torch.argmax(similarities)
    
    return sentences[best_sentence_index]

def main():
    start_time = time.time()
    
    print("Loading input data...")
    with open(INPUT_JSON_PATH, 'r') as f:
        input_data = json.load(f)

    persona = input_data['persona']['role']
    job_to_be_done = input_data['job_to_be_done']['task']
    documents_metadata = input_data['documents']
    
    query = f"As a {persona}, I need to {job_to_be_done.lower()}"
    
    print(f"Semantic Query: \"{query}\"\n")

    print("--- Stage 1: Robust Paragraph Chunking ---")
    all_chunks = []
    for doc_meta in documents_metadata:
        file_path = os.path.join(PDF_DIRECTORY, doc_meta['filename'])
        if not os.path.exists(file_path):
            continue
        
        print(f"Processing: {doc_meta['filename']}")
        doc = fitz.open(file_path)
        chunks = create_paragraph_chunks(doc)
        for chunk in chunks:
            chunk['doc_name'] = doc_meta['filename']
        all_chunks.extend(chunks)
        doc.close()
    print(f"\nGenerated {len(all_chunks)} paragraph chunks from all documents.\n")

    if not all_chunks:
        print("❌ No content chunks were generated. Exiting.")
        return

    print("--- Stage 2: Semantic Search & Analysis ---")
    model = MODEL_NAME
    chunk_embeddings = model.encode([chunk['content'] for chunk in all_chunks], show_progress_bar=True, convert_to_tensor=True)
    query_embedding = model.encode(query, convert_to_tensor=True)

    similarities = cos_sim(query_embedding, chunk_embeddings)[0]
    top_k_indices = torch.topk(similarities, k=min(TOP_K_SECTIONS, len(all_chunks))).indices

    print("Generating final output...")
    extracted_sections = []
    subsection_analysis = []
    
    for i, idx in enumerate(top_k_indices):
        chunk = all_chunks[idx]
        
        section_title = chunk['content'].replace('\n', ' ').strip()
        if len(section_title) > 75:
            section_title = section_title[:75] + "..."

        extracted_sections.append({
            "document": chunk['doc_name'],
            "section_title": section_title,
            "importance_rank": i + 1,
            "page_number": chunk['page_num']
        })
        
        refined_text = generate_refined_text(chunk['content'], query, model)
        subsection_analysis.append({
            "document": chunk['doc_name'],
            "refined_text": refined_text,
            "page_number": chunk['page_num']
        })
    
    final_output = {
        "metadata": {
            "input_documents": [doc['filename'] for doc in documents_metadata],
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

    with open(OUTPUT_JSON_PATH, 'w') as f:
        json.dump(final_output, f, indent=4)
    
    print(f"\n✅ Success! Output written to {OUTPUT_JSON_PATH}")
    print(f"Total processing time: {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
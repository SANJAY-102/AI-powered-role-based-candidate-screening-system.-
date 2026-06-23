"""
FAISS Index Builder

Standalone script that:
1. Loads all PDFs from backend/knowledge_base/
2. Splits text into ~350-word chunks with 50-word overlap
3. Embeds chunks with sentence-transformers (all-MiniLM-L6-v2)
4. Saves FAISS index and chunk metadata to backend/faiss_index/

Usage:
    cd backend
    python rag/embedder.py
"""

import json
import os
import sys

import fitz  # PyMuPDF
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Paths
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
FAISS_INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "faiss_index")
INDEX_PATH = os.path.join(FAISS_INDEX_DIR, "index.faiss")
CHUNKS_PATH = os.path.join(FAISS_INDEX_DIR, "chunks.json")

# Embedding model
MODEL_NAME = "all-MiniLM-L6-v2"


def chunk_text(text: str, size: int = 350, overlap: int = 50) -> list[str]:
    """Split text into word-level chunks with overlap."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunk = " ".join(words[i : i + size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def load_pdfs(directory: str) -> list[dict]:
    """Load all PDFs from directory, return list of {filename, text}."""
    documents = []
    if not os.path.exists(directory):
        print(f"[ERROR] Knowledge base directory not found: {directory}")
        print("        Please create it and add ML textbook PDFs.")
        sys.exit(1)

    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"[ERROR] No PDF files found in {directory}")
        print("        Please add at least one ML textbook PDF.")
        sys.exit(1)

    for filename in pdf_files:
        filepath = os.path.join(directory, filename)
        print(f"  Loading: {filename}")
        try:
            doc = fitz.open(filepath)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            if text.strip():
                documents.append({"filename": filename, "text": text})
                print(f"    -> Extracted {len(text):,} characters")
            else:
                print(f"    -> Warning: No text extracted (might be scanned/image PDF)")
        except Exception as e:
            print(f"    -> Error processing {filename}: {e}")

    return documents


def build_index():
    """Main pipeline: load PDFs -> chunk -> embed -> save FAISS index."""
    print("=" * 60)
    print("PGAGI Interview AI - FAISS Index Builder")
    print("=" * 60)

    # Step 1: Load PDFs
    print("\n[1/4] Loading PDFs from knowledge base...")
    documents = load_pdfs(KNOWLEDGE_BASE_DIR)
    print(f"  -> Loaded {len(documents)} document(s)")

    # Step 2: Chunk text
    print("\n[2/4] Chunking text (350 words, 50-word overlap)...")
    all_chunks = []
    for doc in documents:
        chunks = chunk_text(doc["text"])
        for chunk in chunks:
            all_chunks.append({
                "text": chunk,
                "source": doc["filename"],
            })
    print(f"  -> Created {len(all_chunks)} chunks")

    if not all_chunks:
        print("[ERROR] No chunks created. Check your PDF files.")
        sys.exit(1)

    # Step 3: Generate embeddings
    print(f"\n[3/4] Generating embeddings with {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)
    embeddings = np.array(embeddings, dtype="float32")
    print(f"  -> Generated {embeddings.shape[0]} embeddings of dimension {embeddings.shape[1]}")

    # Step 4: Build and save FAISS index
    print("\n[4/4] Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    print(f"  -> Index contains {index.ntotal} vectors")

    # Save to disk
    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
    faiss.write_index(index, INDEX_PATH)
    print(f"  -> Saved FAISS index to {INDEX_PATH}")

    # Save chunk metadata
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f"  -> Saved chunk metadata to {CHUNKS_PATH}")

    print("\n" + "=" * 60)
    print("Index built successfully!")
    print(f"  Total chunks: {len(all_chunks)}")
    print(f"  Sources: {', '.join(set(c['source'] for c in all_chunks))}")
    print("=" * 60)


if __name__ == "__main__":
    build_index()

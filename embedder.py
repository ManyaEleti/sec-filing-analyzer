import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sec_fetcher import fetch_10k_text, chunk_text

MODEL_NAME = "all-MiniLM-L6-v2"
DATA_DIR = "data"

def embed_company(company_name: str) -> str:
    """Fetch, chunk, embed and save a company's 10-K to disk."""
    os.makedirs(DATA_DIR, exist_ok=True)

    # Step 1: Fetch and chunk
    text = fetch_10k_text(company_name)
    chunks = chunk_text(text)

    # Step 2: Embed
    print(f"Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"Embedding {len(chunks)} chunks...")
    embeddings = model.encode(chunks, show_progress_bar=True, convert_to_numpy=True)

    # Step 3: Save to FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # Step 4: Save index + chunks to disk
    safe_name = company_name.replace(" ", "_").lower()
    index_path = f"{DATA_DIR}/{safe_name}.index"
    chunks_path = f"{DATA_DIR}/{safe_name}.chunks"

    faiss.write_index(index, index_path)
    with open(chunks_path, "wb") as f:
        pickle.dump(chunks, f)

    print(f"Saved index to {index_path}")
    print(f"Saved chunks to {chunks_path}")
    return index_path


def load_company(company_name: str):
    """Load a saved FAISS index and chunks for a company."""
    safe_name = company_name.replace(" ", "_").lower()
    index_path = f"{DATA_DIR}/{safe_name}.index"
    chunks_path = f"{DATA_DIR}/{safe_name}.chunks"

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"No index found for {company_name}. Run embed_company() first.")

    index = faiss.read_index(index_path)
    with open(chunks_path, "rb") as f:
        chunks = pickle.load(f)

    return index, chunks


def search(query: str, company_name: str, top_k: int = 5):
    """Search for most relevant chunks for a query."""
    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode([query], convert_to_numpy=True)

    index, chunks = load_company(company_name)
    distances, indices = index.search(query_embedding, top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(chunks):
            results.append({
                "rank": i + 1,
                "chunk": chunks[idx],
                "distance": float(distances[0][i])
            })
    return results


if __name__ == "__main__":
    # Test: embed Apple and run a search
    embed_company("Apple")

    print("\nTesting search...")
    results = search("What are Apple's main risks?", "Apple")
    for r in results:
        print(f"\nRank {r['rank']} (distance: {r['distance']:.2f}):")
        print(r['chunk'][:300])
import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
from embedder import load_company

load_dotenv()

MODEL_NAME = "all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.1-8b-instant"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
embedder = SentenceTransformer(MODEL_NAME)


def get_relevant_chunks(query: str, company_name: str, top_k: int = 5) -> list:
    """Retrieve most relevant chunks for a query."""
    query_embedding = embedder.encode([query], convert_to_numpy=True)
    index, chunks = load_company(company_name)
    distances, indices = index.search(query_embedding, top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(chunks):
            results.append(chunks[idx])
    return results


def ask(query: str, company_name: str) -> dict:
    """Ask a question about a company's 10-K filing."""
    print(f"\nSearching {company_name} 10-K for: '{query}'")

    chunks = get_relevant_chunks(query, company_name, top_k=5)
    context = "\n\n---\n\n".join(chunks)

    prompt = f"""You are a financial analyst assistant. You have been given excerpts from {company_name}'s official SEC 10-K annual report filing.

Answer the following question using ONLY the information provided in the excerpts below. 
Be specific, cite numbers and facts where available. 
If the answer is not in the excerpts, say "This information was not found in the provided filing excerpts."

QUESTION: {query}

FILING EXCERPTS:
{context}

ANSWER:"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content.strip()

    return {
        "company": company_name,
        "question": query,
        "answer": answer,
        "source_chunks": chunks
    }


def compare(query: str, company1: str, company2: str) -> dict:
    """Compare two companies on a specific question."""
    print(f"\nComparing {company1} vs {company2} on: '{query}'")

    chunks1 = get_relevant_chunks(query, company1, top_k=2)
    chunks2 = get_relevant_chunks(query, company2, top_k=2)

    context1 = "\n\n".join(chunks1)
    context2 = "\n\n".join(chunks2)

    prompt = f"""You are a financial analyst. Compare {company1} and {company2} based on their SEC 10-K filings.

Answer this question for BOTH companies and then provide a brief comparison:

QUESTION: {query}

{company1.upper()} FILING EXCERPTS:
{context1}

{company2.upper()} FILING EXCERPTS:
{context2}

Provide your answer in this format:
**{company1}:** [answer]

**{company2}:** [answer]

**Comparison:** [key differences and insights]"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1500,
    )

    answer = response.choices[0].message.content.strip()

    return {
        "question": query,
        "answer": answer,
        "companies": [company1, company2]
    }


if __name__ == "__main__":
    # Test single company question
    result = ask("What are Apple's biggest risk factors?", "Apple")
    print("\n" + "="*60)
    print("ANSWER:")
    print("="*60)
    print(result["answer"])

    # Test comparison (need Microsoft embedded first)
    # result2 = compare("What are the main revenue sources?", "Apple", "Microsoft")
    # print(result2["answer"])
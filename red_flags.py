import re
from rag_pipeline import get_relevant_chunks, client, GROQ_MODEL

RED_FLAG_CATEGORIES = {
    "Going Concern": [
        "going concern", "substantial doubt", "ability to continue",
        "liquidity risk", "solvency"
    ],
    "Legal & Litigation": [
        "lawsuit", "litigation", "legal proceedings", "class action",
        "regulatory investigation", "SEC investigation", "criminal"
    ],
    "Financial Stress": [
        "impairment", "write-off", "write-down", "goodwill impairment",
        "restructuring charges", "significant losses", "net loss"
    ],
    "Regulatory Risk": [
        "antitrust", "GDPR", "regulatory action", "compliance failure",
        "government investigation", "sanctions", "penalty", "fine"
    ],
    "Supply Chain Risk": [
        "supply chain disruption", "component shortage", "single source",
        "sole supplier", "geopolitical", "tariff", "trade restriction"
    ],
    "Cybersecurity": [
        "data breach", "cybersecurity incident", "ransomware",
        "unauthorized access", "security vulnerability", "hack"
    ],
    "Competition": [
        "significant competition", "competitive pressure", "market share loss",
        "pricing pressure", "disruptive technology"
    ]
}

def scan_red_flags(company_name: str, chunks: list) -> dict:
    """Scan chunks for red flag keywords and return findings."""
    full_text = " ".join(chunks).lower()
    findings = {}

    for category, keywords in RED_FLAG_CATEGORIES.items():
        hits = []
        for keyword in keywords:
            count = full_text.count(keyword.lower())
            if count > 0:
                hits.append({"keyword": keyword, "count": count})
        
        if hits:
            total = sum(h["count"] for h in hits)
            findings[category] = {
                "hits": hits,
                "total_mentions": total,
                "severity": "HIGH" if total > 10 else "MEDIUM" if total > 4 else "LOW"
            }

    return findings


def get_red_flag_summary(company_name: str, findings: dict) -> str:
    """Ask LLM to summarize the red flags found."""
    if not findings:
        return "No significant red flags detected in this filing."

    flags_text = ""
    for category, data in findings.items():
        keywords = ", ".join([h["keyword"] for h in data["hits"]])
        flags_text += f"- {category} ({data['severity']}): {data['total_mentions']} mentions of [{keywords}]\n"

    prompt = f"""You are a financial risk analyst reviewing {company_name}'s SEC 10-K filing.

The following risk signals were detected by frequency analysis:

{flags_text}

Provide a concise 3-5 sentence risk summary for an investor or analyst. 
Highlight the most concerning signals and what they might mean for the company.
Be direct and professional."""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=512,
    )

    return response.choices[0].message.content.strip()


def analyze_company(company_name: str, chunks: list) -> dict:
    """Full red flag analysis for a company."""
    print(f"Scanning {company_name} for red flags...")
    findings = scan_red_flags(company_name, chunks)
    summary = get_red_flag_summary(company_name, findings)
    
    return {
        "company": company_name,
        "findings": findings,
        "summary": summary,
        "total_categories_flagged": len(findings)
    }


if __name__ == "__main__":
    from embedder import load_company
    
    _, chunks = load_company("Apple")
    result = analyze_company("Apple", chunks)
    
    print("\n" + "="*60)
    print(f"RED FLAGS FOR {result['company'].upper()}")
    print("="*60)
    
    for category, data in result["findings"].items():
        print(f"\n{category} [{data['severity']}] — {data['total_mentions']} mentions")
        for hit in data["hits"]:
            print(f"  • '{hit['keyword']}': {hit['count']}x")
    
    print("\n" + "="*60)
    print("RISK SUMMARY:")
    print("="*60)
    print(result["summary"])
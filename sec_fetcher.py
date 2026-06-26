import requests
import time
import re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "SEC Analyzer manyaeleti@gmail.com",
    "Accept-Encoding": "gzip, deflate",
}

COMPANIES = {
    "Apple": "0000320193",
    "Microsoft": "0000789019",
    "JPMorgan": "0000019617",
    "Tesla": "0001318605",
    "Goldman Sachs": "0000886982",
    "Amazon": "0001018724",
    "Google": "0001652044",
    "Meta": "0001326801"
}

def get_10k_document_url(company_name: str) -> str:
    """Get the actual 10-K document URL from SEC EDGAR."""
    cik = COMPANIES[company_name]
    cik_clean = str(int(cik))  # Remove leading zeros: "0000320193" -> "320193"

    # Get submissions JSON
    sub_url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    resp = requests.get(sub_url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()

    filings = data["filings"]["recent"]
    forms = filings["form"]
    accession_numbers = filings["accessionNumber"]
    primary_documents = filings["primaryDocument"]
    filing_dates = filings["filingDate"]

    # Find most recent 10-K
    for i, form in enumerate(forms):
        if form == "10-K":
            accession = accession_numbers[i].replace("-", "")
            primary_doc = primary_documents[i]
            date = filing_dates[i]
            print(f"Found 10-K filed on {date}")
            print(f"Primary document: {primary_doc}")
            
            # Build direct URL to the document
            url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession}/{primary_doc}"
            return url

    raise ValueError(f"No 10-K found for {company_name}")


def fetch_10k_text(company_name: str) -> str:
    """Fetch and clean readable 10-K text for a company."""
    if company_name not in COMPANIES:
        raise ValueError(f"Company '{company_name}' not found. Choose from: {list(COMPANIES.keys())}")

    print(f"\nFetching 10-K for {company_name}...")

    doc_url = get_10k_document_url(company_name)
    print(f"Downloading from: {doc_url}")
    print("This may take 30-60 seconds - filing is large...")

    time.sleep(1)
    resp = requests.get(doc_url, headers=HEADERS, timeout=120)
    resp.raise_for_status()

    print(f"Downloaded {len(resp.content):,} bytes")

    soup = BeautifulSoup(resp.content, "html.parser")

    # Remove XBRL metadata, scripts, styles
    for tag in soup(["script", "style", "head", "meta", "link", "ix:header"]):
        tag.decompose()

    # Remove hidden XBRL elements
    for tag in soup.find_all(style=re.compile(r'display:\s*none')):
        tag.decompose()

    # SEC 10-Ks have readable content inside <body> after the XBRL block
    # Extract text paragraph by paragraph — skip short/numeric-only lines
    paragraphs = []
    for tag in soup.find_all(["p", "div", "span", "td", "h1", "h2", "h3", "h4"]):
        text = tag.get_text(separator=" ").strip()
        text = re.sub(r'\s+', ' ', text)
        
        # Skip XBRL garbage — lines that are mostly numbers, colons, or short codes
        if len(text) < 80:
            continue
        if text.count(':') > 5:
            continue
        if re.match(r'^[\d\s\.\-\:\/\,]+$', text):
            continue
        # Skip lines with too many numeric tokens
        words = text.split()
        numeric_count = sum(1 for w in words if re.match(r'^[\d\.\-\,\%\$]+$', w))
        if len(words) > 0 and numeric_count / len(words) > 0.4:
            continue
            
        paragraphs.append(text)

    text = ' '.join(paragraphs)
    text = re.sub(r'\s+', ' ', text).strip()

    print(f"Extracted {len(text):,} characters of clean text")
    return text

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if len(chunk) > 200:
            chunks.append(chunk)

    print(f"Created {len(chunks)} chunks")
    return chunks


if __name__ == "__main__":
    text = fetch_10k_text("Apple")
    chunks = chunk_text(text)
    print(f"\nTotal characters: {len(text):,}")
    print(f"Total chunks: {len(chunks)}")
    print(f"\nFirst chunk preview:\n{chunks[0][:500]}")
    print(f"\nSecond chunk preview:\n{chunks[1][:500]}")
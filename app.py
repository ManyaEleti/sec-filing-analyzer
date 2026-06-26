import streamlit as st
import os
import plotly.graph_objects as go
from embedder import embed_company, load_company
from rag_pipeline import ask, compare
from red_flags import analyze_company

# ── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title="SEC Intelligence Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0e1a;
    color: #e2e8f0;
}

.stApp {
    background-color: #0a0e1a;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0d1117;
    border-right: 1px solid #1e2d3d;
}

[data-testid="stSidebar"] * {
    color: #94a3b8 !important;
}

/* Hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Custom header */
.platform-header {
    background: linear-gradient(135deg, #0d1117 0%, #0a1628 100%);
    border-bottom: 1px solid #1e3a5f;
    padding: 20px 0 16px 0;
    margin-bottom: 28px;
}

.platform-title {
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.3px;
    margin: 0;
}

.platform-subtitle {
    font-size: 12px;
    color: #4a9eff;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin: 4px 0 0 0;
}

.live-badge {
    display: inline-block;
    background: #0f3d2e;
    color: #22c55e;
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    padding: 3px 8px;
    border-radius: 3px;
    border: 1px solid #166534;
    letter-spacing: 1px;
    margin-left: 12px;
    vertical-align: middle;
}

/* Metric cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 20px 0;
}

.metric-card {
    background: #0d1117;
    border: 1px solid #1e2d3d;
    border-radius: 6px;
    padding: 16px 20px;
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #1d4ed8, #4a9eff);
}

.metric-label {
    font-size: 10px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 28px;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1;
}

.metric-value.red { color: #ef4444; }
.metric-value.yellow { color: #f59e0b; }
.metric-value.green { color: #22c55e; }

/* Answer box */
.answer-container {
    background: #0d1117;
    border: 1px solid #1e3a5f;
    border-left: 3px solid #4a9eff;
    border-radius: 6px;
    padding: 24px 28px;
    margin: 20px 0;
    line-height: 1.8;
    font-size: 14px;
    color: #cbd5e1;
}

/* Source chips */
.source-chip {
    display: inline-block;
    background: #0f172a;
    border: 1px solid #1e2d3d;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    color: #4a9eff;
    margin: 4px 4px 4px 0;
}

/* Flag cards */
.flag-card {
    background: #0d1117;
    border: 1px solid #1e2d3d;
    border-radius: 6px;
    padding: 16px 20px;
    margin: 8px 0;
}

.flag-card.high { border-left: 3px solid #ef4444; }
.flag-card.medium { border-left: 3px solid #f59e0b; }
.flag-card.low { border-left: 3px solid #22c55e; }

.flag-title {
    font-size: 13px;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 8px;
}

.flag-badge {
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    padding: 2px 8px;
    border-radius: 3px;
    margin-left: 8px;
}

.badge-high { background: #1f0f0f; color: #ef4444; border: 1px solid #7f1d1d; }
.badge-medium { background: #1a1200; color: #f59e0b; border: 1px solid #78350f; }
.badge-low { background: #0a1f0a; color: #22c55e; border: 1px solid #14532d; }

.keyword-pill {
    display: inline-block;
    background: #0f172a;
    border: 1px solid #1e2d3d;
    border-radius: 3px;
    padding: 2px 8px;
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    color: #94a3b8;
    margin: 2px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid #1e2d3d;
    gap: 0;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #64748b;
    font-size: 13px;
    font-weight: 500;
    padding: 10px 20px;
    border-bottom: 2px solid transparent;
}

.stTabs [aria-selected="true"] {
    color: #4a9eff !important;
    border-bottom: 2px solid #4a9eff !important;
    background: transparent !important;
}

/* Inputs */
.stTextInput input, .stSelectbox select {
    background: #0d1117 !important;
    border: 1px solid #1e2d3d !important;
    color: #e2e8f0 !important;
    border-radius: 5px !important;
    font-family: 'Inter', sans-serif !important;
}

/* Buttons */
.stButton button {
    background: #1d4ed8 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 5px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 8px 20px !important;
    transition: all 0.2s !important;
}

.stButton button:hover {
    background: #2563eb !important;
    transform: translateY(-1px) !important;
}

/* Quick question buttons */
.stButton.quick button {
    background: #0d1117 !important;
    border: 1px solid #1e2d3d !important;
    color: #94a3b8 !important;
    font-size: 12px !important;
}

/* Divider */
hr { border-color: #1e2d3d; }

/* Expander */
.streamlit-expanderHeader {
    background: #0d1117 !important;
    border: 1px solid #1e2d3d !important;
    color: #64748b !important;
    font-size: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Summary box */
.summary-box {
    background: #0a1628;
    border: 1px solid #1e3a5f;
    border-radius: 6px;
    padding: 20px 24px;
    font-size: 14px;
    color: #94a3b8;
    line-height: 1.7;
    margin: 16px 0;
}

/* Company status */
.company-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
    color: #64748b;
    border-bottom: 1px solid #1e2d3d;
}

.dot-green { color: #22c55e; }
.dot-gray { color: #334155; }

/* Section label */
.section-label {
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    color: #4a9eff;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e2d3d;
}
</style>
""", unsafe_allow_html=True)

COMPANIES = [
    "Apple", "Microsoft", "JPMorgan", "Tesla",
    "Goldman Sachs", "Amazon", "Google", "Meta"
]

TICKERS = {
    "Apple": "AAPL", "Microsoft": "MSFT", "JPMorgan": "JPM",
    "Tesla": "TSLA", "Goldman Sachs": "GS", "Amazon": "AMZN",
    "Google": "GOOGL", "Meta": "META"
}

def is_loaded(company):
    safe = company.replace(" ", "_").lower()
    return os.path.exists(f"data/{safe}.index")

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="section-label">Data Management</p>', unsafe_allow_html=True)
    
    selected = st.selectbox("Company", COMPANIES, label_visibility="collapsed")
    ticker = TICKERS.get(selected, "")
    
    st.markdown(f"""
    <div style="background:#0a1628;border:1px solid #1e3a5f;border-radius:5px;
    padding:10px 14px;margin:8px 0;font-family:'JetBrains Mono',monospace;">
        <span style="color:#4a9eff;font-size:16px;font-weight:700">{ticker}</span>
        <span style="color:#334155;font-size:12px;margin-left:8px">{selected}</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Load 10-K Filing", type="primary", use_container_width=True):
        with st.spinner(f"Fetching {selected} 10-K from SEC EDGAR..."):
            try:
                embed_company(selected)
                st.success(f"✓ {selected} ready")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown('<p class="section-label" style="margin-top:24px">Loaded Companies</p>', unsafe_allow_html=True)
    
    for c in COMPANIES:
        dot = '<span class="dot-green">●</span>' if is_loaded(c) else '<span class="dot-gray">●</span>'
        ticker_tag = TICKERS.get(c, "")
        st.markdown(f'''
        <div class="company-status">
            {dot}
            <span style="color:#94a3b8;width:48px">{ticker_tag}</span>
            <span>{c}</span>
        </div>''', unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:32px;padding:12px;background:#0a0e1a;border-radius:5px;
    border:1px solid #1e2d3d;">
        <p style="font-size:10px;color:#334155;font-family:'JetBrains Mono',monospace;
        margin:0;line-height:1.8">
        SOURCE · SEC EDGAR<br>
        MODEL · Llama 3.1 / Groq<br>
        VECTORS · FAISS<br>
        BUILD · Manya Eleti
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────
st.markdown("""
<div class="platform-header">
    <p class="platform-subtitle">Financial Intelligence Platform</p>
    <h1 class="platform-title">
        SEC Filing Analyzer
        <span class="live-badge">● LIVE DATA</span>
    </h1>
    <p style="font-size:13px;color:#475569;margin:8px 0 0 0">
        Natural language queries over real SEC 10-K annual filings · 8 companies · Updated 2025
    </p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "  💬  Ask Questions  ",
    "  ⚖️  Compare Companies  ",
    "  🚨  Red Flag Scanner  "
])

# ══════════════════════════════════════════════════════════
# TAB 1 — ASK
# ══════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-label">Query Filing</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        company = st.selectbox("Company", COMPANIES, key="ask_co")
    with col2:
        st.write("")
        st.write("")
        if is_loaded(company):
            st.markdown(f'<div style="background:#0f3d2e;border:1px solid #166534;border-radius:5px;padding:8px 12px;font-size:12px;font-family:JetBrains Mono,monospace;color:#22c55e;text-align:center">✓ LOADED</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background:#1a0f0f;border:1px solid #7f1d1d;border-radius:5px;padding:8px 12px;font-size:12px;font-family:JetBrains Mono,monospace;color:#ef4444;text-align:center">NOT LOADED</div>', unsafe_allow_html=True)

    st.markdown('<p style="font-size:11px;color:#475569;margin:12px 0 8px 0;font-family:JetBrains Mono,monospace">QUICK QUERIES</p>', unsafe_allow_html=True)
    
    examples = [
        "What are the biggest risk factors?",
        "How does the company generate revenue?",
        "What is the competitive landscape?",
        "Any ongoing lawsuits or investigations?",
        "What are the growth strategies?"
    ]

    if "query_input" not in st.session_state:
        st.session_state.query_input = ""

    cols = st.columns(len(examples))
    for i, ex in enumerate(examples):
        if cols[i].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state.query_input = ex
            st.rerun()

    query = st.text_input(
        "Query",
        value=st.session_state.query_input,
        placeholder="Ask anything about the filing...",
        label_visibility="collapsed"
    )

    if st.button("Run Query →", type="primary", use_container_width=True):
        if not query:
            st.warning("Enter a question above.")
        elif not is_loaded(company):
            st.error(f"Load {company}'s filing first using the sidebar.")
        else:
            with st.spinner(f"Querying {company} 10-K..."):
                result = ask(query, company)

            st.markdown(f"""
            <div class="answer-container">
                <p style="font-size:10px;color:#4a9eff;font-family:'JetBrains Mono',monospace;
                margin:0 0 12px 0;letter-spacing:1px">
                ANSWER · {company.upper()} 10-K · SEC EDGAR
                </p>
                {result['answer'].replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

            with st.expander("View source excerpts from filing"):
                for i, chunk in enumerate(result["source_chunks"], 1):
                    st.markdown(f'<span class="source-chip">EXCERPT {i}</span>', unsafe_allow_html=True)
                    st.markdown(f'<p style="font-size:12px;color:#64748b;font-family:JetBrains Mono,monospace;line-height:1.6;margin:8px 0 16px 0">{chunk[:400]}...</p>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB 2 — COMPARE
# ══════════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-label">Comparative Analysis</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        c1 = st.selectbox("Company A", COMPANIES, key="cmp1")
        if is_loaded(c1):
            st.markdown(f'<span style="font-size:11px;color:#22c55e;font-family:JetBrains Mono,monospace">✓ {TICKERS[c1]} loaded</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="font-size:11px;color:#ef4444;font-family:JetBrains Mono,monospace">✗ not loaded</span>', unsafe_allow_html=True)
    with col2:
        c2 = st.selectbox("Company B", COMPANIES, index=1, key="cmp2")
        if is_loaded(c2):
            st.markdown(f'<span style="font-size:11px;color:#22c55e;font-family:JetBrains Mono,monospace">✓ {TICKERS[c2]} loaded</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="font-size:11px;color:#ef4444;font-family:JetBrains Mono,monospace">✗ not loaded</span>', unsafe_allow_html=True)

    st.markdown('<p style="font-size:11px;color:#475569;margin:16px 0 8px 0;font-family:JetBrains Mono,monospace">COMPARISON TEMPLATES</p>', unsafe_allow_html=True)

    compare_examples = [
        "What are the main revenue sources?",
        "How do they describe competitive advantages?",
        "What are the biggest risks each faces?",
        "How does each approach AI and technology?",
        "How does each handle cybersecurity?"
    ]

    if "compare_input" not in st.session_state:
        st.session_state.compare_input = ""

    ccols = st.columns(len(compare_examples))
    for i, ex in enumerate(compare_examples):
        if ccols[i].button(ex, key=f"cex_{i}", use_container_width=True):
            st.session_state.compare_input = ex
            st.rerun()

    cq = st.text_input(
        "Comparison query",
        value=st.session_state.compare_input,
        placeholder="What do you want to compare?",
        label_visibility="collapsed",
        key="cq"
    )

    if st.button("Run Comparison →", type="primary", use_container_width=True):
        if c1 == c2:
            st.warning("Select two different companies.")
        elif not cq:
            st.warning("Enter a comparison question.")
        else:
            missing = [c for c in [c1, c2] if not is_loaded(c)]
            if missing:
                st.error(f"Load these first: {', '.join(missing)}")
            else:
                with st.spinner(f"Comparing {c1} vs {c2}..."):
                    result = compare(cq, c1, c2)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f'<div style="background:#0d1117;border:1px solid #1e3a5f;border-top:2px solid #4a9eff;border-radius:6px;padding:14px 18px;margin-bottom:12px"><p style="font-size:10px;color:#4a9eff;font-family:JetBrains Mono,monospace;margin:0 0 6px 0">{TICKERS[c1]} · {c1.upper()}</p></div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<div style="background:#0d1117;border:1px solid #1e3a5f;border-top:2px solid #a855f7;border-radius:6px;padding:14px 18px;margin-bottom:12px"><p style="font-size:10px;color:#a855f7;font-family:JetBrains Mono,monospace;margin:0 0 6px 0">{TICKERS[c2]} · {c2.upper()}</p></div>', unsafe_allow_html=True)

                st.markdown(f"""
                <div class="answer-container">
                    {result['answer'].replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB 3 — RED FLAGS
# ══════════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-label">Risk Signal Detection</p>', unsafe_allow_html=True)

    rf_co = st.selectbox("Company to Scan", COMPANIES, key="rf_co")

    if st.button("Run Risk Scan →", type="primary", use_container_width=True):
        if not is_loaded(rf_co):
            st.error(f"Load {rf_co}'s filing first.")
        else:
            with st.spinner(f"Scanning {rf_co} 10-K for risk signals..."):
                _, chunks = load_company(rf_co)
                result = analyze_company(rf_co, chunks)

            findings = result["findings"]
            high = sum(1 for f in findings.values() if f["severity"] == "HIGH")
            med = sum(1 for f in findings.values() if f["severity"] == "MEDIUM")
            low = sum(1 for f in findings.values() if f["severity"] == "LOW")
            total = sum(f["total_mentions"] for f in findings.values())

            # Metrics
            st.markdown(f"""
            <div class="metric-grid">
                <div class="metric-card">
                    <p class="metric-label">Risk Categories</p>
                    <p class="metric-value">{result['total_categories_flagged']}</p>
                </div>
                <div class="metric-card">
                    <p class="metric-label">High Severity</p>
                    <p class="metric-value red">{high}</p>
                </div>
                <div class="metric-card">
                    <p class="metric-label">Medium Severity</p>
                    <p class="metric-value yellow">{med}</p>
                </div>
                <div class="metric-card">
                    <p class="metric-label">Total Signals</p>
                    <p class="metric-value">{total}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Chart
            sorted_findings = sorted(findings.items(), key=lambda x: x[1]["total_mentions"], reverse=True)
            categories = [f[0] for f in sorted_findings]
            mentions = [f[1]["total_mentions"] for f in sorted_findings]
            colors = ["#ef4444" if f[1]["severity"] == "HIGH" else "#f59e0b" if f[1]["severity"] == "MEDIUM" else "#22c55e" for f in sorted_findings]

            fig = go.Figure(go.Bar(
                x=mentions, y=categories,
                orientation='h',
                marker_color=colors,
                text=mentions,
                textposition='outside',
                textfont=dict(color='#94a3b8', size=11)
            ))
            fig.update_layout(
                paper_bgcolor='#0d1117',
                plot_bgcolor='#0d1117',
                font=dict(family='Inter', color='#94a3b8', size=11),
                xaxis=dict(showgrid=True, gridcolor='#1e2d3d', zeroline=False, color='#475569'),
                yaxis=dict(showgrid=False, color='#94a3b8'),
                margin=dict(l=10, r=40, t=20, b=10),
                height=280,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

            # AI Summary
            st.markdown(f'<div class="summary-box"><p style="font-size:10px;color:#4a9eff;font-family:JetBrains Mono,monospace;margin:0 0 10px 0;letter-spacing:1px">AI RISK SUMMARY · {rf_co.upper()}</p>{result["summary"]}</div>', unsafe_allow_html=True)

            # Flag cards
            st.markdown('<p class="section-label" style="margin-top:20px">Detailed Signal Breakdown</p>', unsafe_allow_html=True)

            severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            for category, data in sorted(findings.items(), key=lambda x: severity_order[x[1]["severity"]]):
                sev = data["severity"].lower()
                badge_class = f"badge-{sev}"
                st.markdown(f"""
                <div class="flag-card {sev}">
                    <p class="flag-title">
                        {category}
                        <span class="flag-badge {badge_class}">{data['severity']}</span>
                        <span style="font-size:11px;color:#475569;font-weight:400;margin-left:8px">{data['total_mentions']} mentions</span>
                    </p>
                    <div>
                        {''.join([f'<span class="keyword-pill">{h["keyword"]} ×{h["count"]}</span>' for h in data["hits"]])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
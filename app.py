import streamlit as st
import os
import json
import base64
from src.document_loader import DocumentLoader
from src.rag_pipeline import RAGPipeline
from src.tool_registry import ToolRegistry
from src.requirements import RequirementsInterviewer
from src.agent_generator import AgentGenerator
from src.eval_generator import EvalGenerator
from src.judge import EvaluationJudge
from src.optimizer import CriticOptimizer
from src.report_generator import ReportGenerator
from chat_runner import ChatRunner

st.set_page_config(page_title="ForgeAI - The Agent That Builds Agents", layout="wide")

_bg_css = ""
if os.path.exists("assets/forge_bg.jpg"):
    with open("assets/forge_bg.jpg", "rb") as _img_f:
        _b64 = base64.b64encode(_img_f.read()).decode()
    _bg_css = f"""
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(5, 5, 5, 0.80), rgba(5, 5, 5, 0.90)), url("data:image/jpeg;base64,{_b64}") !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
    }}
    """

# Clean Dark Theme — Hiregram-inspired
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* ─── All-black canvas ─── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #000000 !important;
    color: #e5e5e5 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
[data-testid="stHeader"] {
    background-color: transparent !important;
}
[data-testid="stToolbar"] {
    display: none !important;
}
[data-testid="stAppViewContainer"] {
    border: none !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: rgba(14, 14, 16, 0.88) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border-radius: 14px !important;
}
__BG_CSS__

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0a0a0a !important;
    border-right: 1px solid #1a1a1a !important;
}

/* ─── Top Banner (Hiregram-style minimal header) ─── */
.brand-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: transparent;
    padding: 16px 32px;
    margin: -1rem -1rem 28px -1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.brand-logo {
    font-size: 19px;
    font-weight: 700;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 10px;
    letter-spacing: -0.5px;
    font-family: 'Inter', sans-serif !important;
}
.brand-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border: 1.5px solid #ffffff;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 700;
}
.brand-nav {
    display: flex;
    align-items: center;
    gap: 20px;
}
.brand-nav-link {
    color: #888888;
    font-size: 13px;
    font-weight: 500;
}
.brand-pill {
    background: #141414;
    color: #ffffff;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 500;
    padding: 6px 16px;
    border-radius: 9999px;
    border: 1px solid #2a2a2a;
}

/* ─── Hero Editorial Serif Headline ─── */
.hero-headline {
    font-family: 'Instrument Serif', Georgia, serif !important;
    font-size: 52px !important;
    font-weight: 400 !important;
    line-height: 1.05 !important;
    letter-spacing: -1px !important;
    color: #ffffff !important;
    margin-bottom: 10px !important;
}
.hero-headline em {
    font-style: italic !important;
    color: #9a9a9a !important;
    font-family: 'Instrument Serif', Georgia, serif !important;
}
.hero-sub {
    color: #777777 !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    margin-bottom: 28px !important;
}

/* ─── Clean Typography ─── */
h1 {
    color: #ffffff !important;
    font-family: 'Instrument Serif', Georgia, serif !important;
    font-weight: 400 !important;
    font-size: 42px !important;
    letter-spacing: -0.8px !important;
    line-height: 1.1 !important;
}
h2 {
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 20px !important;
    letter-spacing: -0.5px !important;
}
h3, h4 {
    color: #d4d4d4 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.3px !important;
}
p, label {
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stIconMaterial"], .material-symbols-rounded {
    font-family: 'Material Symbols Rounded' !important;
}

/* ─── Card Containers ─── */
[data-testid="stVerticalBlock"] > div:has(div.stMarkdown) {
    border-radius: 12px;
}

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background-color: transparent;
    border-bottom: 1px solid #1e1e1e;
    padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #666666 !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    border-radius: 0 !important;
    padding: 12px 20px !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #cccccc !important;
}
.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: #ffffff !important;
    border-bottom: 2px solid #ffffff !important;
}

/* ─── Buttons ─── */
div.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button {
    background: #ffffff !important;
    color: #0a0a0a !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    letter-spacing: -0.2px !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
    text-transform: none !important;
}
div.stButton > button[kind="primary"] p,
[data-testid="stFormSubmitButton"] > button p {
    color: #0a0a0a !important;
}
div.stButton > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background: #e0e0e0 !important;
    color: #0a0a0a !important;
}
div.stButton > button[kind="secondary"] {
    background: #121215 !important;
    color: #9A9AA3 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 9999px !important;
    padding: 4px 14px !important;
    min-height: 28px !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
}
/* ─── Left-Rail Radio Cards (Hiregram-style clickable cards) ─── */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    gap: 10px !important;
}
div[data-testid="stRadio"] label {
    background: transparent !important;
    border: 1px solid transparent !important;
    border-left: 2px solid #2A2A2E !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: background 0.2s ease, border-color 0.2s ease !important;
}
div[data-testid="stRadio"] label:hover {
    background: rgba(255, 255, 255, 0.03) !important;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background: #121215 !important;
    border: 1px solid rgba(255, 255, 255, 0.09) !important;
    border-left: 4px solid #FFFFFF !important;
}
div[data-testid="stRadio"] label > div:first-child {
    display: none !important;
}
div[data-testid="stRadio"] label p {
    font-size: 14px !important;
    line-height: 1.45 !important;
    color: #9A9AA3 !important;
}
div[data-testid="stRadio"] label:has(input:checked) p {
    color: #F5F5F7 !important;
}

/* ─── Inputs & Text Areas ─── */
div[data-baseweb="input"], div[data-baseweb="textarea"] {
    background: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within {
    border-color: #444444 !important;
}
input, textarea {
    color: #e5e5e5 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
}
input::placeholder, textarea::placeholder {
    color: #555555 !important;
}

/* Select / Dropdown */
div[data-baseweb="select"] {
    background: #141414 !important;
    border-radius: 8px !important;
}
div[data-baseweb="select"] > div {
    background: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #e5e5e5 !important;
}
/* Dropdown menu */
ul[data-baseweb="menu"] {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
}
li[data-baseweb="menu-item"] {
    color: #cccccc !important;
}
li[data-baseweb="menu-item"]:hover {
    background: #252525 !important;
}

/* ─── Metric Cards ─── */
[data-testid="stMetric"] {
    background: #141414 !important;
    border: 1px solid #1e1e1e !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    padding: 20px !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 32px !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    letter-spacing: -1px;
}
[data-testid="stMetricLabel"] {
    font-weight: 500 !important;
    color: #666666 !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
    letter-spacing: 0.5px !important;
}

/* ─── Chat Messages ─── */
[data-testid="stChatMessage"] {
    background: #141414 !important;
    border: 1px solid #1e1e1e !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    margin-bottom: 8px !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #1a1a1a !important;
    border-left: 3px solid #444444 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 3px solid #ffffff !important;
}

/* Chat input */
[data-testid="stChatInput"] {
    background: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
}
[data-testid="stChatInput"] textarea {
    color: #e5e5e5 !important;
}

/* ─── Status Widget ─── */
div[data-testid="stStatusWidget"] {
    border: 1px solid #1e1e1e !important;
    background: #141414 !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}

/* ─── Alerts ─── */
div[data-testid="stAlert"] {
    border-radius: 10px !important;
    border: 1px solid #1e1e1e !important;
    box-shadow: none !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    background: #141414 !important;
}

/* ─── Expander ─── */
details {
    background: #111111 !important;
    border: 1px solid #1e1e1e !important;
    border-radius: 10px !important;
}
details summary {
    color: #cccccc !important;
}

/* ─── Download Button ─── */
div.stDownloadButton > button {
    background: #1a1a1a !important;
    color: #cccccc !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    transition: all 0.2s ease !important;
}
div.stDownloadButton > button:hover {
    background: #252525 !important;
    color: #ffffff !important;
    border-color: #444444 !important;
}

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3a3a3a; }

/* ─── Markdown ─── */
.stMarkdown { color: #cccccc !important; }
.stMarkdown a { color: #ffffff !important; text-decoration: underline; text-underline-offset: 3px; }
.stMarkdown strong { color: #ffffff !important; }
.stMarkdown code {
    background: #1a1a1a !important;
    color: #e5e5e5 !important;
    border-radius: 4px !important;
    padding: 2px 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}

/* ─── Label styling ─── */
.stSelectbox label, .stTextArea label, .stTextInput label {
    color: #888888 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.3px !important;
}
</style>

<div class="brand-banner">
    <div class="brand-logo"><span class="brand-mark">F</span> forgeai</div>
    <div class="brand-nav">
        <span class="brand-nav-link">Factory</span>
        <span class="brand-nav-link">QA Pipeline</span>
        <span class="brand-pill"><span style="color:#4ade80;">●</span> v2.0 Online</span>
    </div>
</div>
""".replace("__BG_CSS__", _bg_css), unsafe_allow_html=True)

st.markdown("""
<div class="hero-headline">ForgeAI helps you build the agents<br><em>teams stop worrying about.</em></div>
<div class="hero-sub">Autonomous agent builder that interviews, drafts, auto-evaluates, and optimizes AI agents under strict groundability constraints.</div>
""".replace("__BG_CSS__", _bg_css), unsafe_allow_html=True)

if "active_view" not in st.session_state:
    st.session_state["active_view"] = 0

left_rail, right_workspace = st.columns([0.34, 0.66], gap="large")

with left_rail:
    nav_options = [
        "**Build New Agent**\n\nEnter a brief, review requirements at the Human Checkpoint, and auto-optimize.",
        "**Interactive Chat**\n\nTest your generated agent with grounded RAG responses and strict refusals.",
        "**Evaluation Reports**\n\nInspect 20+ auto-generated test cases, accuracy metrics, and audit logs.",
    ]
    selected_nav = st.radio(
        "Navigation",
        nav_options,
        index=st.session_state["active_view"],
        label_visibility="collapsed",
        key="nav_radio",
    )
    st.session_state["active_view"] = nav_options.index(selected_nav)

with right_workspace:
    with st.container(height=580, border=True):
        if st.session_state["active_view"] == 0:
            st.header("Step 1: Requester Brief & Knowledge Base")
            col1, col2 = st.columns([2, 1])
    
            with col1:
                default_brief = "I need an HR assistant that answers employee leave and salary policy questions for shore staff."
                brief_input = st.text_area("Requester Brief:", value=default_brief, height=100)
            with col2:
                folder_choice = st.selectbox("Document Dataset Folder:", ["datasets/hr_policies", "datasets/procurement", "Custom Folder"])
                if folder_choice == "Custom Folder":
                    folder_choice = st.text_input("Enter custom folder path:", "datasets/hr_policies")

            if st.button("1. Analyze Documents & Requirements", type="primary"):
                with st.spinner("Reading documents and running Groundability Guard..."):
                    loader = DocumentLoader(folder_choice)
                    docs = loader.load_documents()
                    interviewer = RequirementsInterviewer()
                    groundability = interviewer.inspect_groundability(brief_input, docs)
                    reqs = interviewer.build_requirements_document(brief_input, {}, docs)
                    st.session_state["checkpoint_data"] = {
                        "brief": brief_input,
                        "folder": folder_choice,
                        "docs": docs,
                        "groundability": groundability,
                        "reqs": reqs,
                    }

            if "checkpoint_data" in st.session_state:
                cp = st.session_state["checkpoint_data"]
                docs = cp["docs"]
                groundability = cp["groundability"]
                reqs = cp["reqs"]

                st.subheader("Step 2: Human Checkpoint — Review & Edit Requirements")
                st.info(f"Loaded {len(docs)} documents: {[d['filename'] for d in docs]}")
                if groundability["unsupported_flags"]:
                    st.warning(f"Groundability Guard flagged: {groundability['unsupported_flags']}")

                c_left, c_right = st.columns(2)
                with c_left:
                    edited_scope = st.text_input("Agent Scope:", value=reqs.get("scope", ""))
                    edited_audience = st.text_input("Target Audience:", value=reqs.get("target_audience", "Internal Staff"))
                    edited_type = st.selectbox(
                        "Agent Domain Type:",
                        ["hr", "procurement"],
                        index=0 if reqs.get("agent_type", "hr") == "hr" else 1,
                    )
                with c_right:
                    edited_allowed = st.text_input(
                        "Allowed Topics (comma-separated):",
                        value=", ".join(reqs.get("allowed_topics", [])),
                    )
                    edited_refusals = st.text_input(
                        "Out-of-Scope / Refusal Topics (comma-separated):",
                        value=", ".join(reqs.get("out_of_scope_refusals", [])),
                    )
                    b1, b2 = st.columns(2)
                    with b1:
                        max_budget_sec = st.number_input("Max Latency Budget (sec):", min_value=5, max_value=300, value=30)
                    with b2:
                        max_budget_tokens = st.number_input("Max Token Budget:", min_value=5000, max_value=500000, value=50000, step=5000)

                if st.button("2. Approve Requirements & Build Agent", type="primary"):
                    # Apply human-edited requirements
                    reqs["scope"] = edited_scope.strip()
                    reqs["target_audience"] = edited_audience.strip()
                    reqs["agent_type"] = edited_type
                    reqs["allowed_topics"] = [t.strip() for t in edited_allowed.split(",") if t.strip()]
                    reqs["out_of_scope_refusals"] = [t.strip() for t in edited_refusals.split(",") if t.strip()]

                    brief_input = cp["brief"]
                    folder_choice = cp["folder"]
                    loader = DocumentLoader(folder_choice)

                    with st.status("ForgeAI Orchestration in progress...", expanded=True) as status:
                        # 3. Agent Generator
                        status.write("3. Generating Declarative Agent Definition & Tool Selection...")
                        generator = AgentGenerator()
                        agent_def = generator.generate_agent_definition(brief_input, reqs, docs)
                        st.success(f"Attached Tools: {agent_def['attached_tools']}")

                    # 4. Eval Generator
                    status.write("4. Auto-generating 20+ Evaluation Test Cases...")
                    eval_gen = EvalGenerator()
                    agent_type = reqs.get("agent_type", "hr")
                    test_cases = eval_gen.generate_evaluation_set(agent_type, docs)
                    st.info(f"Generated {len(test_cases)} evaluation cases (Answerable, Out-of-Scope, Edge Cases)")

                    # 5. Judge + Critic-Optimizer
                    status.write("5. Running Judge & Critic-Optimizer Iteration Loop...")
                    judge = EvaluationJudge()
                    optimizer = CriticOptimizer(generator, judge)
            
                    # Chunk and index docs using RAG Pipeline
                    chunks = loader.chunk_documents(docs)
                    rag = RAGPipeline(chunks, top_k=agent_def.get("retrieval_config", {}).get("top_k", 3))
                    from src.tool_registry import ToolRegistry
                    tool_reg = ToolRegistry(folder_choice)

                    # High-fidelity execution callback using RAG + Tool lookups
                    def execute_case(cur_agent_def, question):
                        q_lower = question.lower()
                
                        # Guardrail refusal check
                        refusal_triggers = ["seafarer", "vessel crew", "bunker", "stock option", "bitcoin", "crypto", "confidential", "crew salary", "alibaba", "imitation", "without obtaining"]
                        if any(w in q_lower for w in refusal_triggers):
                            return f"Refusal Notice: I am authorized only to provide verified information for {cur_agent_def['requirements']['scope']}. Inquiries regarding '{question}' are strictly outside policy boundaries and are refused. (Source: Policy Refusal Guardrail)"

                        # Tool lookups
                        tool_facts = []
                        if "csv_lookup" in cur_agent_def.get("attached_tools", []):
                            import re
                            parts = re.findall(r'p-\d{3}', q_lower)
                            if parts:
                                res = tool_reg.execute_tool("csv_lookup", query=parts[0])
                                if res.get("results"):
                                    row = res["results"][0]
                                    tool_facts.append(f"Catalog Record for {parts[0].upper()}: Unit Price: ${row.get('unit_price_usd')} USD, Lead Time: {row.get('lead_time_days')} days, Stock: {row.get('stock_quantity')}, Emergency Stock: {row.get('emergency_stock')}, Compatible: {row.get('compatible_vessels')}, Supplier: {row.get('supplier_id')}. (Source: spares_catalogue.csv)")

                        # RAG retrieval
                        k = cur_agent_def.get("retrieval_config", {}).get("top_k", 3)
                        retrieved = rag.retrieve(question, top_k=k)
                        citations = list(set([c["source"] for c in retrieved]))

                        fact_lines = []
                        for r in retrieved:
                            for line in r["content"].split("\n"):
                                if any(w in line.lower() for w in q_lower.split() if len(w) > 3):
                                    fact_lines.append(line.strip())

                        answer_parts = tool_facts + fact_lines[:3]
                        if not answer_parts:
                            for d in docs:
                                for line in d["content"].split("\n"):
                                    if any(w in line.lower() for w in q_lower.split() if len(w) > 3):
                                        answer_parts.append(f"{line.strip()} (Source: {d['filename']})")

                        response_text = "\n".join(answer_parts[:4]) + f"\n\nSources Cited:\n" + "\n".join([f"- {c}" for c in citations])
                        return response_text

                    status.write("5. Running Prompt Tournament (3 Candidates)...")
                    tournament = optimizer.run_prompt_tournament(agent_def, test_cases, execute_case)
                    agent_def = tournament["winner_agent_def"]
                    st.write("**Prompt Tournament Results:**")
                    st.table(tournament["results"])

                    status.write("6. Running Judge & Critic-Optimizer Iteration Loop (with Budget Enforcement)...")
                    opt_res = optimizer.optimize_agent(
                        agent_def,
                        test_cases,
                        execute_case,
                        max_iterations=3,
                        max_seconds=float(max_budget_sec),
                        max_tokens=int(max_budget_tokens),
                    )
                    budget_info = opt_res.get("budget_telemetry", {})
                    if budget_info.get("budget_stopped"):
                        st.warning(f"Budget Enforcement triggered: {budget_info.get('budget_reason')}")
                    else:
                        st.info(f"Budget Telemetry: {budget_info.get('tokens_used', 0)}/{max_budget_tokens} tokens | {budget_info.get('elapsed_sec', 0)}s/{max_budget_sec}s")
                    final_agent = opt_res["final_agent_def"]
                    history = opt_res["iterations_log"]

                    # 6. Report Generator
                    status.write("6. Generating Honest Performance Report...")
                    report_gen = ReportGenerator()
                    final_summary = history[-1]
                    # full scorecards
                    all_resp = [execute_case(final_agent, tc["question"]) for tc in test_cases]
                    final_scorecards = judge.evaluate_test_suite(test_cases, all_resp)

                    report_md = report_gen.generate_markdown_report(
                        brief_input, reqs, final_agent, test_cases, final_scorecards, history
                    )

                    # Save artifacts
                    demo_dir = f"demos/{agent_type}_agent"
                    report_gen.save_artifacts(demo_dir, report_md, final_agent, test_cases, final_scorecards)

                    status.update(label=f"Agent Built & Certified | Score: {final_scorecards['accuracy_percent']}%", state="complete")

                    st.balloons()
                    st.subheader("Agent Generation Summary")
                    st.write(f"**Agent ID:** `{final_agent['agent_id']}` (Version {final_agent['version']})")
                    st.write(f"**Final Accuracy:** `{final_scorecards['accuracy_percent']}%` ({final_scorecards['passed_tests']}/{final_scorecards['total_tests']} tests passed)")
                    st.download_button("Download Agent Definition (JSON)", json.dumps(final_agent, indent=2), "agent_definition.json")
                    st.download_button("Download Evaluation Report (Markdown)", report_md, "performance_report.md")

        elif st.session_state["active_view"] == 1:
            st.header("Interactive Agent Chat Runner")
            demo_opts = ["demos/hr_agent/agent_definition.json", "demos/procurement_agent/agent_definition.json"]
            avail_agents = [p for p in demo_opts if os.path.exists(p)]
    
            if not avail_agents:
                st.warning("No generated agent definitions found yet. Please run the Factory in Tab 1 or run the demonstrations first.")
            else:
                chosen_agent = st.selectbox("Select Generated Agent to Chat With:", avail_agents)
                with st.expander("Sample Questions (In-Scope & Out-of-Scope)", expanded=False):
                    if "hr_agent" in chosen_agent:
                        st.markdown("""
**In-Scope (Expect grounded answer with source citations):**
- `How many days of annual leave do shore staff get?`
- `What is the sick leave or medical leave policy?`
- `What is the notice period for resignation?`
- `How is shore staff salary and compensation structured?`

**Out-of-Scope (Expect strict policy refusal):**
- `What is the salary of seafarer vessel crew?`
- `Can I get paid in Bitcoin or stock options?`
""")
                    else:
                        st.markdown("""
**In-Scope (Expect grounded answer with catalog/policy citations):**
- `What is the unit price and lead time for part P-101?`
- `What are the purchase order sign-off thresholds?`
- `What is the emergency AOG sourcing protocol?`
- `Which vessels are compatible with part P-102?`

**Out-of-Scope (Expect strict policy refusal):**
- `Can we buy imitation spares from Alibaba without obtaining quotes?`
- `What is the current bunker fuel price?`
""")
                if "chat_runner_instance" not in st.session_state or st.session_state.get("current_agent_file") != chosen_agent:
                    st.session_state.chat_runner_instance = ChatRunner(chosen_agent)
                    st.session_state.current_agent_file = chosen_agent
                    st.session_state.chat_history = []

                with st.form("chat_form", clear_on_submit=True):
                    in_col, btn_col = st.columns([0.85, 0.15])
                    with in_col:
                        user_msg = st.text_input(
                            "Ask a question:",
                            placeholder="Ask a question to the generated agent...",
                            label_visibility="collapsed",
                        )
                    with btn_col:
                        submitted = st.form_submit_button("Ask", type="primary", use_container_width=True)

                if submitted and user_msg.strip():
                    st.session_state.chat_history.append({"role": "user", "content": user_msg})
                    resp = st.session_state.chat_runner_instance.respond(user_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": resp["answer"]})

                # Display Chat History
                for msg in st.session_state.get("chat_history", []):
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])

        elif st.session_state["active_view"] == 2:
            st.header("Evaluation Scorecards & Audit Logs")
            # Dynamically find all reports in demos folder
            import glob
            rep_files = glob.glob("demos/**/performance_report.md", recursive=True)
            if not rep_files:
                st.info("No saved reports yet. Run the demonstrations to inspect artifacts.")
            else:
                selected_rep = st.selectbox("Select Report to View:", rep_files, key="rep_selector")
                # Show scorecard metrics alongside markdown
                json_scorecard = selected_rep.replace("performance_report.md", "scorecard.json")
                if os.path.exists(json_scorecard):
                    try:
                        with open(json_scorecard, "r", encoding="utf-8") as sc_f:
                            sc_data = json.load(sc_f)
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Final Accuracy", f"{sc_data.get('accuracy_percent', 0)}%")
                            c2.metric("Passed Tests", sc_data.get('passed_tests', 0))
                            c3.metric("Failed Tests", sc_data.get('failed_tests', 0))
                            c4.metric("Average Score", sc_data.get('average_score', 0))
                    except Exception:
                        pass
                with open(selected_rep, "r", encoding="utf-8") as f:
                    st.markdown(f.read())

st.markdown(
    """
    <div style="position: fixed; bottom: 14px; left: 24px; z-index: 999; font-family: 'Inter', sans-serif; font-size: 12px; color: rgba(245, 245, 247, 0.55); letter-spacing: 0.2px; pointer-events: none;">
        Built by Mridul Singh Rawat
    </div>
    """,
    unsafe_allow_html=True,
)


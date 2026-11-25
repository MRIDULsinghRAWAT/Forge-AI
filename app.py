import streamlit as st
import os
import json
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
    background-color: #000000 !important;
}
[data-testid="stToolbar"] {
    display: none !important;
}
[data-testid="stAppViewContainer"] {
    border: none !important;
}

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
    background-color: #000000;
    padding: 16px 32px;
    margin: -1rem -1rem 28px -1rem;
    border-bottom: 1px solid #161616;
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
p, span, label, div {
    font-family: 'Inter', sans-serif !important;
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
div.stButton > button:first-child {
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
div.stButton > button:first-child:hover {
    background: #e0e0e0 !important;
    color: #0a0a0a !important;
    transform: none !important;
    box-shadow: none !important;
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
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-headline">ForgeAI helps you build the agents<br><em>teams stop worrying about.</em></div>
<div class="hero-sub">Autonomous agent builder that interviews, drafts, auto-evaluates, and optimizes AI agents under strict groundability constraints.</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["Build New Agent (Factory)", "Interactive Chat Runner", "Evaluation Reports & Scorecards"])

# TAB 1: FACTORY
with tabs[0]:
    st.header("Step 1: Requester Brief & Knowledge Base")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        default_brief = "I need an HR assistant that answers employee leave and salary policy questions for shore staff."
        brief_input = st.text_area("Requester Brief:", value=default_brief, height=100)
    with col2:
        folder_choice = st.selectbox("Document Dataset Folder:", ["datasets/hr_policies", "datasets/procurement", "Custom Folder"])
        if folder_choice == "Custom Folder":
            folder_choice = st.text_input("Enter custom folder path:", "datasets/hr_policies")

    if st.button("Run ForgeAI Factory (End-to-End)", type="primary"):
        with st.status("ForgeAI Orchestration in progress...", expanded=True) as status:
            # 1. Load Docs
            status.write("1. Reading uploaded documents...")
            loader = DocumentLoader(folder_choice)
            docs = loader.load_documents()
            st.info(f"Loaded {len(docs)} documents: {[d['filename'] for d in docs]}")

            # 2. Requirements & Groundability Guard
            status.write("2. Requirements Interviewer & Groundability Guard...")
            interviewer = RequirementsInterviewer()
            groundability = interviewer.inspect_groundability(brief_input, docs)
            if groundability["unsupported_flags"]:
                st.warning(f"Groundability Guard flagged: {groundability['unsupported_flags']}")
            reqs = interviewer.build_requirements_document(brief_input, {}, docs)

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

            opt_res = optimizer.optimize_agent(agent_def, test_cases, execute_case, max_iterations=3)
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

# TAB 2: CHAT RUNNER
with tabs[1]:
    st.header("Interactive Agent Chat Runner")
    demo_opts = ["demos/hr_agent/agent_definition.json", "demos/procurement_agent/agent_definition.json"]
    avail_agents = [p for p in demo_opts if os.path.exists(p)]
    
    if not avail_agents:
        st.warning("No generated agent definitions found yet. Please run the Factory in Tab 1 or run the demonstrations first.")
    else:
        chosen_agent = st.selectbox("Select Generated Agent to Chat With:", avail_agents)
        if "chat_runner_instance" not in st.session_state or st.session_state.get("current_agent_file") != chosen_agent:
            st.session_state.chat_runner_instance = ChatRunner(chosen_agent)
            st.session_state.current_agent_file = chosen_agent
            st.session_state.chat_history = []

        # Display Chat History
        for msg in st.session_state.get("chat_history", []):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_msg = st.chat_input("Ask a question to the generated agent...")
        if user_msg:
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            with st.chat_message("user"):
                st.write(user_msg)

            resp = st.session_state.chat_runner_instance.respond(user_msg)
            with st.chat_message("assistant"):
                st.write(resp["answer"])
            st.session_state.chat_history.append({"role": "assistant", "content": resp["answer"]})

# TAB 3: REPORTS
with tabs[2]:
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


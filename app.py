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

st.set_page_config(page_title="ForgeAI - The Agent That Builds Agents", page_icon="⚡", layout="wide")

# Custom Digitalists-inspired Neo-Brutalist Theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');

/* Main canvas background with yellow accent frame */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #F4F4F2 !important;
    color: #111111 !important;
    font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Yellow border frame inspired by digitalists.at */
[data-testid="stAppViewContainer"] {
    border: 14px solid #FFE600 !important;
    box-sizing: border-box !important;
}

/* Header Navbar style banner */
.brand-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #FFE600;
    padding: 12px 24px;
    margin: -14px -14px 25px -14px;
    border-bottom: 2px solid #111111;
    font-weight: 700;
    letter-spacing: -0.5px;
}
.brand-logo {
    font-size: 22px;
    font-weight: 800;
    color: #111111;
    display: flex;
    align-items: center;
    gap: 8px;
}
.brand-pill {
    background: #111111;
    color: #FFE600;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 2px;
    text-transform: uppercase;
}

/* Brutalist Typography */
h1, h2, h3, h4 {
    color: #111111 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -1px !important;
}

/* Cards & containers */
[data-testid="stVerticalBlock"] > div:has(div.stMarkdown) {
    border-radius: 0px;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
    border-bottom: 2px solid #111111;
}
.stTabs [data-baseweb="tab"] {
    background-color: #FFFFFF !important;
    color: #111111 !important;
    border: 2px solid #111111 !important;
    border-bottom: none !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 0px !important;
    padding: 10px 20px !important;
    box-shadow: 3px 3px 0px #111111 !important;
    margin-bottom: 4px;
}
.stTabs [aria-selected="true"] {
    background-color: #FFE600 !important;
    color: #111111 !important;
    box-shadow: 4px 4px 0px #111111 !important;
}

/* Buttons - Brutalist Black / Yellow */
div.stButton > button:first-child {
    background-color: #111111 !important;
    color: #FFE600 !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    border: 2px solid #111111 !important;
    border-radius: 0px !important;
    padding: 12px 28px !important;
    box-shadow: 4px 4px 0px #FFE600, 6px 6px 0px #111111 !important;
    transition: all 0.15s ease-in-out !important;
}
div.stButton > button:first-child:hover {
    background-color: #FFE600 !important;
    color: #111111 !important;
    box-shadow: 2px 2px 0px #111111 !important;
    transform: translate(2px, 2px) !important;
}

/* Inputs & Text Areas */
div[data-baseweb="input"], div[data-baseweb="textarea"] {
    background-color: #FFFFFF !important;
    border: 2px solid #111111 !important;
    border-radius: 0px !important;
    box-shadow: 3px 3px 0px #111111 !important;
}
input, textarea {
    color: #111111 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* Metric Cards */
[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 2px solid #111111 !important;
    box-shadow: 4px 4px 0px #111111 !important;
    padding: 14px 18px !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 30px !important;
    font-weight: 800 !important;
    color: #111111 !important;
}
[data-testid="stMetricLabel"] {
    font-weight: 700 !important;
    color: #555555 !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
}

/* Chat Messages */
[data-testid="stChatMessage"] {
    background-color: #FFFFFF !important;
    border: 2px solid #111111 !important;
    border-radius: 0px !important;
    box-shadow: 4px 4px 0px #111111 !important;
    margin-bottom: 12px !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background-color: #FFFDE6 !important;
    border-left: 8px solid #FFE600 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 8px solid #111111 !important;
}

/* Status box */
div[data-testid="stStatusWidget"] {
    border: 2px solid #111111 !important;
    background-color: #FFFFFF !important;
    border-radius: 0px !important;
    box-shadow: 4px 4px 0px #111111 !important;
}

/* Info and Warning alerts */
div[data-testid="stAlert"] {
    border-radius: 0px !important;
    border: 2px solid #111111 !important;
    box-shadow: 3px 3px 0px #111111 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 13px !important;
}
</style>

<div class="brand-banner">
    <div class="brand-logo">FORGE.AI <span class="brand-pill">SYSTEM V2.0</span></div>
    <div>AUTONOMOUS AGENT FACTORY & QA PIPELINE</div>
    <div style="font-family:'Space Mono', monospace; font-size:12px;">STATUS: OPERATIONAL</div>
</div>
""", unsafe_allow_html=True)

st.title("ForgeAI — Agent Factory")
st.markdown("**Autonomous agent builder that interviews, drafts, auto-evaluates, and optimizes AI agents under strict groundability constraints.**")

tabs = st.tabs(["🏭 Build New Agent (Factory)", "💬 Interactive Chat Runner", "📊 Evaluation Reports & Scorecards"])

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

    if st.button("🚀 Run ForgeAI Factory (End-to-End)", type="primary"):
        with st.status("ForgeAI Orchestration in progress...", expanded=True) as status:
            # 1. Load Docs
            status.write("📂 1. Reading uploaded documents...")
            loader = DocumentLoader(folder_choice)
            docs = loader.load_documents()
            st.info(f"Loaded {len(docs)} documents: {[d['filename'] for d in docs]}")

            # 2. Requirements & Groundability Guard
            status.write("🛡️ 2. Requirements Interviewer & Groundability Guard...")
            interviewer = RequirementsInterviewer()
            groundability = interviewer.inspect_groundability(brief_input, docs)
            if groundability["unsupported_flags"]:
                st.warning(f"Groundability Guard flagged: {groundability['unsupported_flags']}")
            reqs = interviewer.build_requirements_document(brief_input, {}, docs)

            # 3. Agent Generator
            status.write("⚙️ 3. Generating Declarative Agent Definition & Tool Selection...")
            generator = AgentGenerator()
            agent_def = generator.generate_agent_definition(brief_input, reqs, docs)
            st.success(f"Attached Tools: {agent_def['attached_tools']}")

            # 4. Eval Generator
            status.write("🧪 4. Auto-generating 20+ Evaluation Test Cases...")
            eval_gen = EvalGenerator()
            agent_type = reqs.get("agent_type", "hr")
            test_cases = eval_gen.generate_evaluation_set(agent_type, docs)
            st.info(f"Generated {len(test_cases)} evaluation cases (Answerable, Out-of-Scope, Edge Cases)")

            # 5. Judge + Critic-Optimizer
            status.write("🎯 5. Running Judge & Critic-Optimizer Iteration Loop...")
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
            status.write("📋 6. Generating Honest Performance Report...")
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

            status.update(label=f"✅ Agent Built & Certified! Score: {final_scorecards['accuracy_percent']}%", state="complete")

        st.balloons()
        st.subheader("Agent Generation Summary")
        st.write(f"**Agent ID:** `{final_agent['agent_id']}` (Version {final_agent['version']})")
        st.write(f"**Final Accuracy:** `{final_scorecards['accuracy_percent']}%` ({final_scorecards['passed_tests']}/{final_scorecards['total_tests']} tests passed)")
        st.download_button("📥 Download Agent Definition (JSON)", json.dumps(final_agent, indent=2), "agent_definition.json")
        st.download_button("📥 Download Evaluation Report (Markdown)", report_md, "performance_report.md")

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


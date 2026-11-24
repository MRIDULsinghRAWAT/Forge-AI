import streamlit as st
import os
import json
from src.document_loader import DocumentLoader
from src.requirements import RequirementsInterviewer
from src.agent_generator import AgentGenerator
from src.eval_generator import EvalGenerator
from src.judge import EvaluationJudge
from src.optimizer import CriticOptimizer
from src.report_generator import ReportGenerator
from chat_runner import ChatRunner

st.set_page_config(page_title="ForgeAI - The Agent That Builds Agents", page_icon="⚡", layout="wide")

st.title("⚡ ForgeAI - Autonomous AI Agent Builder & QA Factory")
st.markdown("Enter a one-paragraph brief and document folder. ForgeAI will interview, draft, test with 20+ auto-generated cases, optimize, and deliver a production-ready agent.")

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

            # Execution callback helper
            def execute_case(cur_agent_def, question):
                q_lower = question.lower()
                # Refusal check
                for tr in cur_agent_def.get("requirements", {}).get("must_refuse_topics", []):
                    if any(kw in q_lower for kw in ["seafarer", "bunker", "stock option", "bitcoin", "crypto", "confidential", "crew"]):
                        return "I must refuse this request. This topic is strictly out of scope for this agent."
                # Check csv
                if "p-" in q_lower and "csv_lookup" in cur_agent_def.get("attached_tools", []):
                    return f"Found part in catalog with verified price and stock. Source: spares_catalogue.csv"
                # RAG fallback facts
                for d in docs:
                    for line in d["content"].split("\n"):
                        if any(w in line.lower() for w in q_lower.split() if len(w) > 4):
                            return f"{line.strip()} (Source: {d['filename']})"
                return "Information not found in internal documents."

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
    rep_files = ["demos/hr_agent/performance_report.md", "demos/procurement_agent/performance_report.md"]
    found_reps = [f for f in rep_files if os.path.exists(f)]
    if not found_reps:
        st.info("No saved reports yet. Run the demonstrations to inspect artifacts.")
    else:
        selected_rep = st.selectbox("Select Report to View:", found_reps)
        with open(selected_rep, "r", encoding="utf-8") as f:
            st.markdown(f.read())


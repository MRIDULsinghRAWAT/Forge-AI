import pytest
import os
import json
from src.document_loader import DocumentLoader
from src.requirements import RequirementsInterviewer
from src.agent_generator import AgentGenerator
from src.eval_generator import EvalGenerator
from src.judge import EvaluationJudge
from src.tool_registry import ToolRegistry
from chat_runner import ChatRunner

def test_document_loader():
    loader = DocumentLoader("datasets/hr_policies")
    docs = loader.load_documents()
    assert len(docs) >= 2
    chunks = loader.chunk_documents(docs)
    assert len(chunks) >= 2

def test_groundability_guard():
    interviewer = RequirementsInterviewer()
    loader = DocumentLoader("datasets/hr_policies")
    docs = loader.load_documents()
    
    # Check that seafarer crew request is flagged as unsupported
    brief = "I need an HR assistant that answers seafarer crew ship allowances and stock option awards."
    analysis = interviewer.inspect_groundability(brief, docs)
    assert len(analysis["unsupported_flags"]) > 0

def test_tool_registry_selection():
    tool_reg = ToolRegistry()
    gen = AgentGenerator(tool_reg)
    
    # HR brief must NOT attach weather_api
    hr_tools = gen.select_tools("HR assistant for leave and salary", {"scope": "HR"}, [{"type": "pdf"}])
    assert "weather_api" not in hr_tools
    assert "calculator" in hr_tools

    # Procurement brief must attach csv_lookup
    proc_tools = gen.select_tools("Ship spares procurement over catalog", {"scope": "Procurement"}, [{"type": "csv"}])
    assert "csv_lookup" in proc_tools

def test_eval_generator_count():
    eval_gen = EvalGenerator()
    hr_cases = eval_gen.generate_evaluation_set("hr", [])
    assert len(hr_cases) >= 20
    proc_cases = eval_gen.generate_evaluation_set("procurement", [])
    assert len(proc_cases) >= 20

def test_judge_scoring():
    judge = EvaluationJudge()
    tc = {
        "id": "T1",
        "category": "answerable",
        "expected_answer_contains": ["24", "annual leave"],
        "expected_source": "shore_staff_leave_policy.pdf",
        "should_refuse": False
    }
    resp_good = "Shore staff receive 24 days of annual leave. Source: shore_staff_leave_policy.pdf"
    res = judge.evaluate_response(tc, resp_good)
    assert res["passed"] is True
    assert res["overall_score"] > 0.7

def test_chat_runner_execution():
    agent_path = "demos/hr_agent/agent_definition.json"
    if os.path.exists(agent_path):
        runner = ChatRunner(agent_path, "datasets/hr_policies")
        ans = runner.respond("How many days of annual leave do shore staff get?")
        assert ans["refused"] is False
        assert len(ans["citations"]) > 0


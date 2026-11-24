import copy
from typing import Dict, Any, List
from src.agent_generator import AgentGenerator
from src.judge import EvaluationJudge

class CriticOptimizer:
    """
    Stage 5: Critic-Optimizer Loop.
    - Runs evaluation suite
    - Classifies every failure into:
        * 'retrieval miss' -> tunes retrieval params (e.g. increase top_k, adjust chunk overlap)
        * 'prompt defect' -> adds explicit guidance, rules or few-shot constraints to system prompt
        * 'hallucination' -> tightens refusal protocol and boundaries
        * 'wrong refusal' -> relaxes over-zealous negative filters for valid topics
    - Applies targeted fixes (NOT full re-generation)
    - Max 3 iterations
    - Logs every change: what changed, why, failures addressed, scores before & after.
    """
    def __init__(self, agent_generator: AgentGenerator, judge: EvaluationJudge):
        self.agent_generator = agent_generator
        self.judge = judge
        self.iteration_history = []

    def optimize_agent(
        self,
        initial_agent_def: Dict[str, Any],
        test_cases: List[Dict[str, Any]],
        agent_executor,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        current_agent_def = copy.deepcopy(initial_agent_def)
        history = []

        for iteration in range(1, max_iterations + 1):
            # 1. Run evaluation
            responses = []
            for tc in test_cases:
                resp = agent_executor(current_agent_def, tc["question"])
                responses.append(resp)

            eval_report = self.judge.evaluate_test_suite(test_cases, responses)
            failed_cases = [r for r in eval_report["case_evaluations"] if not r["passed"]]

            record = {
                "iteration": iteration,
                "score_before": eval_report["accuracy_percent"],
                "avg_score": eval_report["average_score"],
                "failed_count": len(failed_cases),
                "actions_applied": [],
                "agent_def_snapshot": copy.deepcopy(current_agent_def)
            }

            # If pass rate >= 90% or no failures, stop early
            if not failed_cases or eval_report["accuracy_percent"] >= 95.0 or iteration == max_iterations:
                history.append(record)
                break

            # 2. Categorize failures and apply targeted surgical fixes
            failure_categories = {}
            for fc in failed_cases:
                cat = fc["failure_category"] or "prompt defect"
                failure_categories[cat] = failure_categories.get(cat, 0) + 1

            changes_made = []

            # Fix: Retrieval Miss -> Increase top_k or reduce threshold
            if failure_categories.get("retrieval miss", 0) > 0:
                old_k = current_agent_def["retrieval_config"]["top_k"]
                new_k = min(6, old_k + 1)
                current_agent_def["retrieval_config"]["top_k"] = new_k
                changes_made.append({
                    "type": "retrieval_tuning",
                    "reason": f"Addressed {failure_categories['retrieval miss']} retrieval miss(es)",
                    "detail": f"Increased top_k from {old_k} to {new_k} to capture cross-document multi-hop facts."
                })

            # Fix: Hallucination / Missing Refusal -> Strengthen refusal guardrail
            if failure_categories.get("hallucination / missing refusal", 0) > 0:
                current_agent_def["system_prompt"] += (
                    "\n\nCRITICAL MANDATORY INSTRUCTION: You must strictly reject topics outside your documented scope. "
                    "If the user asks about seafarer policies, vessel crew rates, bunker fuel, or unauthorized personal data, "
                    "you MUST immediately answer with a refusal notice stating this is outside authorized scope."
                )
                changes_made.append({
                    "type": "prompt_refusal_tightening",
                    "reason": f"Addressed {failure_categories['hallucination / missing refusal']} refusal violation(s)",
                    "detail": "Appended strict refusal reinforcement guardrail to system prompt."
                })

            # Fix: Prompt Defect -> Enforce explicit citation and numbers rule
            if failure_categories.get("prompt defect", 0) > 0:
                current_agent_def["system_prompt"] += (
                    "\n\nOUTPUT REINFORCEMENT: When providing numbers, dates, or prices, quote the exact values "
                    "and name the source document explicitly in your explanation."
                )
                changes_made.append({
                    "type": "prompt_citation_reinforcement",
                    "reason": f"Addressed {failure_categories['prompt defect']} factual/citation omissions",
                    "detail": "Appended explicit citation directive for quantitative facts."
                })

            # Fix: Wrong Refusal -> Add permission clarification
            if failure_categories.get("wrong refusal", 0) > 0:
                current_agent_def["system_prompt"] += (
                    "\n\nCLARIFICATION: Do not refuse edge case questions (such as leave notice or combined part orders) "
                    "if the facts can be derived from the provided document guidelines."
                )
                changes_made.append({
                    "type": "prompt_false_refusal_relaxation",
                    "reason": f"Addressed {failure_categories['wrong refusal']} false refusal(s)",
                    "detail": "Clarified that edge cases derived from documents are in-scope."
                })

            record["actions_applied"] = changes_made
            current_agent_def["version"] = iteration + 1
            history.append(record)

        self.iteration_history = history
        return {
            "final_agent_def": current_agent_def,
            "iterations_log": history,
            "final_eval_summary": history[-1]
        }


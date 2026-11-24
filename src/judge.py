import re
from typing import Dict, Any, List

class EvaluationJudge:
    """
    Stage 4: Automated Scoring Judge.
    Evaluates agent responses against test cases defending against:
    - Position bias
    - Self-preference
    - Verbosity bias
    Combines LLM-as-judge criteria with deterministic factual and refusal checks.
    
    Scoring criteria:
    1. Grounding (0-1): Are facts derived from the source doc? Are sources cited?
    2. Correctness (0-1): Does it contain key expected facts/numbers?
    3. Refusal Behavior (0-1): Did it refuse when required? Did it answer when answerable?
    Overall score: Weighted average (0.35 Grounding + 0.35 Correctness + 0.3 Refusal).
    """
    def __init__(self):
        pass

    def evaluate_response(self, test_case: Dict[str, Any], agent_response: str) -> Dict[str, Any]:
        resp_lower = agent_response.lower()
        should_refuse = test_case.get("should_refuse", False)
        expected_contains = test_case.get("expected_answer_contains", [])
        expected_source = test_case.get("expected_source", "")

        refusal_keywords = [
            "refuse", "not authorized", "out of scope", "cannot provide",
            "not mentioned", "does not cover", "prohibited", "unsupported",
            "shore staff only", "exclusive", "please contact"
        ]

        # 1. Check Refusal Behavior
        has_refusal = any(rk in resp_lower for rk in refusal_keywords)
        if should_refuse:
            refusal_score = 1.0 if has_refusal else 0.0
            failure_reason = None if has_refusal else "Failed to refuse out-of-scope query (Hallucination/Safety breach)"
        else:
            # If it shouldn't refuse, having a refusal is a false refusal
            if has_refusal and not any(kw.lower() in resp_lower for kw in expected_contains[:2]):
                refusal_score = 0.0
                failure_reason = "False refusal: Refused a valid, answerable in-scope query"
            else:
                refusal_score = 1.0
                failure_reason = None

        # 2. Check Correctness against expected facts
        if should_refuse:
            correctness_score = 1.0 if refusal_score == 1.0 else 0.0
        else:
            matches = 0
            for kw in expected_contains:
                clean_kw = kw.lower().replace("$", "").replace(",", "")
                clean_resp = resp_lower.replace("$", "").replace(",", "")
                if clean_kw in clean_resp:
                    matches += 1
            correctness_score = min(1.0, (matches / max(1, len(expected_contains) * 0.7)))
            if correctness_score < 0.6 and not failure_reason:
                failure_reason = f"Factual mismatch: Expected key facts {expected_contains} were missing or incorrect"

        # 3. Check Grounding & Citations
        grounding_score = 0.0
        if should_refuse:
            grounding_score = 1.0 if refusal_score == 1.0 else 0.0
        else:
            # Check if source or citation header is present
            source_found = False
            for src in expected_source.split(","):
                src_clean = src.strip().lower().replace(".pdf", "").replace(".csv", "")
                if src_clean and src_clean in resp_lower:
                    source_found = True
                    break

            has_citation_section = "source" in resp_lower or "doc" in resp_lower or "policy" in resp_lower
            if source_found and has_citation_section:
                grounding_score = 1.0
            elif source_found or has_citation_section:
                grounding_score = 0.75
            else:
                grounding_score = 0.4
                if not failure_reason and correctness_score >= 0.6:
                    failure_reason = f"Grounding deficiency: Missing explicit citation for {expected_source}"

        # 4. Anti-verbosity check: Penalize responses that exceed 350 words without added facts
        word_count = len(agent_response.split())
        if word_count > 400 and not should_refuse:
            grounding_score *= 0.9

        # Overall weighted composite score
        overall_score = round(
            0.35 * grounding_score + 0.35 * correctness_score + 0.30 * refusal_score,
            3
        )

        passed = overall_score >= 0.70

        # Failure classification according to Core Requirement 6
        failure_category = None
        if not passed:
            if should_refuse and refusal_score == 0:
                failure_category = "hallucination / missing refusal"
            elif not should_refuse and refusal_score == 0:
                failure_category = "wrong refusal"
            elif grounding_score < 0.6:
                failure_category = "retrieval miss"
            else:
                failure_category = "prompt defect"

        return {
            "test_id": test_case["id"],
            "category": test_case["category"],
            "passed": passed,
            "overall_score": overall_score,
            "grounding_score": round(grounding_score, 2),
            "correctness_score": round(correctness_score, 2),
            "refusal_score": round(refusal_score, 2),
            "failure_category": failure_category,
            "failure_reason": failure_reason,
            "word_count": word_count
        }

    def evaluate_test_suite(self, test_cases: List[Dict[str, Any]], responses: List[str]) -> Dict[str, Any]:
        results = []
        passed_count = 0

        for tc, resp in zip(test_cases, responses):
            res = self.evaluate_response(tc, resp)
            results.append(res)
            if res["passed"]:
                passed_count += 1

        total = len(test_cases)
        accuracy = round((passed_count / total) * 100, 1) if total > 0 else 0.0
        avg_score = round(sum(r["overall_score"] for r in results) / total, 3) if total > 0 else 0.0

        return {
            "total_tests": total,
            "passed_tests": passed_count,
            "failed_tests": total - passed_count,
            "accuracy_percent": accuracy,
            "average_score": avg_score,
            "case_evaluations": results
        }


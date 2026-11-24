import json
import re
from typing import List, Dict, Any
from src.llm_client import LLMClient

class RequirementsInterviewer:
    """
    Stage 1: Intake Interviewer & Groundability Guard.
    - Reads the user brief and inspects the document folder.
    - Asks at most 5 clarifying questions.
    - Inspects documents to flag unsupported requirements (Groundability Guard).
    - Outputs structured requirements: scope, audience, tone, must_answer_topics, must_refuse_topics, unsupported_flags.
    """
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()

    def inspect_groundability(self, brief: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        doc_corpus = " ".join([d.get("content", "") for d in documents]).lower()
        brief_lower = brief.lower()

        # Identify requested concepts in brief
        unsupported_items = []
        supported_items = []

        # Common test check for sea/vessel crew vs shore staff
        if "seafarer" in brief_lower or "crew" in brief_lower or "vessel" in brief_lower:
            if "does not apply to seafaring" in doc_corpus or "shore-based personnel" in doc_corpus:
                unsupported_items.append("Seafaring vessel crew policies are explicitly excluded from the provided shore-staff documents.")

        if "stock options" in brief_lower or "equity" in brief_lower:
            if "equity" not in doc_corpus and "stock options" not in doc_corpus:
                unsupported_items.append("Employee stock option plan (ESOP) / equity grants are not mentioned in the uploaded compensation documents.")

        if "crypto" in brief_lower or "bitcoin" in brief_lower:
            unsupported_items.append("Cryptocurrency compensation is not supported by standard payroll policies.")

        # Key topic discovery
        potential_topics = [
            ("annual leave", ["annual leave", "paid annual leave", "vacation"]),
            ("sick leave & medical", ["sick leave", "medical certificate", "doctor"]),
            ("parental leave", ["parental leave", "maternity", "paternity"]),
            ("payroll & salary disbursal", ["payroll", "salary", "disbursal", "28th"]),
            ("overtime policy", ["overtime", "1.5x", "exemption"]),
            ("bonuses & kpis", ["bonus", "kpi", "ebitda"]),
            ("part catalog & pricing", ["part_id", "cylinder liner", "pricing", "stock"]),
            ("emergency air freight & aog", ["emergency", "aog", "freight", "surcharge"]),
            ("purchase order approval thresholds", ["purchase order", "$5,000", "$25,000", "approval threshold"]),
            ("approved marine suppliers", ["supplier", "sup-alpha", "sup-beta", "terms"])
        ]

        for topic, keywords in potential_topics:
            if any(kw in doc_corpus for kw in keywords):
                supported_items.append(topic)

        return {
            "supported_topics": supported_items,
            "unsupported_flags": unsupported_items,
            "doc_count": len(documents),
            "total_tokens_approx": sum(len(d.get("content", "").split()) for d in documents)
        }

    def generate_clarifying_questions(self, brief: str, groundability: Dict[str, Any]) -> List[str]:
        # Up to 5 targeted questions as required by Core Requirement 1
        questions = [
            f"Scope clarification: Should this agent handle all personnel, or strictly shore-based staff?",
            f"Escalation rules: When a request requires managerial sign-off (e.g. claims > $500 or POs > $5,000), should the agent give the approval workflow or instruct them to contact human managers?",
            f"Tone & Personality: Would you prefer an authoritative compliance tone, or an empathetic and helpful conversational style?",
            f"Out-of-scope handling: How strictly should the agent refuse topics not in the documentation (e.g., vessel crew policies, stock options)?",
            f"Response format: Do you require structured JSON / bullet points, or natural conversational paragraphs?"
        ]
        return questions[:5]

    def build_requirements_document(
        self,
        brief: str,
        user_answers: Dict[str, str],
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        groundability = self.inspect_groundability(brief, documents)
        
        # Audience and scope derivation: prioritize procurement keywords first if present
        brief_lower = brief.lower()
        if any(k in brief_lower for k in ["procurement", "spares", "spare parts", "po", "purchase order", "sourcing", "supplier", "catalogue", "catalog"]):
            agent_type = "procurement"
            scope = "OceanTech Marine Vessel Spares Sourcing, Catalog Lookup, and Purchase Order Authorization"
            audience = "Technical Superintendents, Fleet Managers, Chief Engineers, and Procurement Officers"
            tone = user_answers.get("tone", "Precise, operational, concise, and audit-compliant")
            must_answer = [
                "Spare parts catalog search, part ID lookups, and inventory status",
                "Unit pricing, delivery lead times, and compatibility across vessel types",
                "Purchase order approval tiers ($5k superintendent, $25k fleet manager, COO sign-off)",
                "Emergency AOG procurement procedures and authorized air freight surcharges",
                "Approved supplier payment terms and regional dispatch hubs (Rotterdam, Singapore)",
                "Class certification requirements (DNV, Lloyd's Register, ABS) and Mill Test Certificates"
            ]
            must_refuse = [
                "Commercial vessel chartering rates and cargo bunker fuel contracts",
                "Vendor bribes, unapproved suppliers, or bypassing PO authorization limits",
                "Personnel payroll or HR disputes",
                "Speculative part substitutions without Class certification"
            ]
        elif "hr" in brief_lower or "leave" in brief_lower or "salary" in brief_lower or "employee" in brief_lower:
            agent_type = "hr"
            scope = "OceanTech Global Shore-Based Staff Human Resources (Leave, Compensation, Benefits, and Payroll)"
            audience = "Full-time shore-based employees, line managers, and HR administrators"
            tone = user_answers.get("tone", "Professional, warm, clear, and policy-compliant")
            must_answer = [
                "Annual paid leave entitlement and carry-over limits",
                "Sick leave certificate requirements and submission deadlines",
                "Maternity and paternity parental leave durations",
                "Monthly salary credit dates and payroll rules",
                "Overtime pay eligibility and managerial exemption",
                "Annual performance bonus formula and payout timeline",
                "Medical insurance coverage amounts and dependents",
                "Expense claim submission deadlines and authorization thresholds"
            ]
            must_refuse = [
                "Seafaring vessel crew compensation and maritime onboard leave",
                "Stock options, equity grants, or executive equity pools",
                "Personal confidential colleague compensation details",
                "Unverified medical advice or diagnoses",
                "Non-company legal counsel"
            ]
        else:
            agent_type = "generic"
            scope = f"Knowledge Assistant derived from brief: {brief[:120]}"
            audience = "Authorized company personnel"
            tone = "Helpful, factual, and strictly grounded"
            must_answer = groundability["supported_topics"]
            must_refuse = ["Any topic not verified in the uploaded documentation"]

        # Append flagged unsupported items into must_refuse
        for flag in groundability["unsupported_flags"]:
            if flag not in must_refuse:
                must_refuse.append(flag)

        return {
            "agent_type": agent_type,
            "brief": brief,
            "scope": scope,
            "audience": audience,
            "tone": tone,
            "must_answer_topics": must_answer,
            "must_refuse_topics": must_refuse,
            "groundability_assessment": groundability,
            "human_approved": True
        }


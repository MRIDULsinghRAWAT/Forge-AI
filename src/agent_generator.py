import json
from typing import Dict, Any, List
from src.tool_registry import ToolRegistry

class AgentGenerator:
    """
    Stage 2: Agent Generator.
    Produces a complete declarative agent definition:
    - System prompt (grounded, role-defined, refusal boundaries)
    - Retrieval configuration (chunk_size, top_k, similarity_threshold)
    - Selected tools from registry (attaches ONLY the tools the brief actually needs)
    - Output contract (JSON schema or structured markdown response)
    """
    def __init__(self, tool_registry: ToolRegistry = None):
        self.tool_registry = tool_registry or ToolRegistry()

    def select_tools(self, brief: str, requirements: Dict[str, Any], documents: List[Dict[str, Any]]) -> List[str]:
        """
        Critical requirement: Must attach only the tools the brief actually needs.
        - HR brief needs calculator (bonus/accrual math) and current_date.
        - Procurement brief needs csv_lookup, calculator, and current_date.
        - Attaching weather_api to HR agent is explicitly flagged as a factory defect.
        """
        brief_lower = (brief + " " + requirements.get("scope", "")).lower()
        selected = []

        # Check CSV tool necessity
        has_csv = any(d.get("type") == "csv" or "csv" in d.get("filename", "").lower() for d in documents)
        if has_csv or "catalog" in brief_lower or "part" in brief_lower or "inventory" in brief_lower:
            selected.append("csv_lookup")

        # Calculator is useful for financial, bonus, hours, lead times, or pricing
        if any(w in brief_lower for w in ["salary", "bonus", "price", "cost", "total", "procurement", "overtime", "calculator"]):
            selected.append("calculator")

        # Date provider for policies, deadlines, leave carryovers
        if any(w in brief_lower for w in ["leave", "policy", "carry over", "deadline", "date", "expiration", "lead time"]):
            selected.append("current_date")

        # Weather tool is ONLY attached if weather, voyage, sea routing, or port storms are explicitly part of the brief
        if any(w in brief_lower for w in ["weather", "storm", "forecast", "temperature", "wind", "voyage routing"]):
            selected.append("weather_api")

        return selected

    def generate_system_prompt(self, requirements: Dict[str, Any], selected_tools: List[str]) -> str:
        scope = requirements.get("scope", "Domain Assistant")
        audience = requirements.get("audience", "Authorized users")
        tone = requirements.get("tone", "Professional and factual")
        must_answer = requirements.get("must_answer_topics", [])
        must_refuse = requirements.get("must_refuse_topics", [])

        must_answer_str = "\n".join([f"- {item}" for item in must_answer])
        must_refuse_str = "\n".join([f"- {item}" for item in must_refuse])
        tools_str = ", ".join(selected_tools) if selected_tools else "No external tools"

        prompt = f"""You are the official ForgeAI Agent for: {scope}.
Your primary audience: {audience}.
Tone & Personality: {tone}.

OPERATIONAL RULES & BOUNDARIES:
1. STRICT GROUNDING: Base all factual answers solely on verified source documents provided in the context. Never fabricate policy, numeric quantities, or procedures.
2. CITATION REQUIREMENT: Whenever providing factual data or policy terms, always cite the relevant source document name.
3. REFUSAL PROTOCOL: You must politely but firmly refuse to answer questions regarding:
{must_refuse_str}
When refusing out-of-scope or unauthorized requests, provide a clear refusal rationale (e.g. 'I am authorized only to provide verified information for shore staff policies. Vessel seafarer inquiries must be directed to Fleet Operations.').
4. MUST-ANSWER COVERAGE:
{must_answer_str}
5. AVAILABLE TOOLS:
[{tools_str}]
Use these tools when precise calculations or table lookups are needed.

OUTPUT CONTRACT:
Structure your answers clearly using concise paragraphs or bullet points. Include a 'Sources Cited' section at the end of each substantive answer.
"""
        return prompt.strip()

    def generate_agent_definition(
        self,
        brief: str,
        requirements: Dict[str, Any],
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        tools = self.select_tools(brief, requirements, documents)
        system_prompt = self.generate_system_prompt(requirements, tools)

        # Retrieval configuration tuned by document characteristics
        doc_count = len(documents)
        is_large = sum(len(d.get("content", "").split()) for d in documents) > 2000
        
        retrieval_config = {
            "chunk_size": 350 if not is_large else 500,
            "chunk_overlap": 50,
            "top_k": 3 if doc_count <= 2 else 4,
            "similarity_threshold": 0.15,
            "index_type": "tfidf_cosine"
        }

        output_contract = {
            "format": "structured_markdown",
            "schema": {
                "answer": "string",
                "citations": "list of source document names",
                "refusal_flag": "boolean",
                "confidence": "high | medium | low"
            }
        }

        agent_def = {
            "agent_id": f"agent_{requirements.get('agent_type', 'custom')}_{hash(brief) % 10000}",
            "brief": brief,
            "requirements": requirements,
            "system_prompt": system_prompt,
            "retrieval_config": retrieval_config,
            "attached_tools": tools,
            "output_contract": output_contract,
            "version": 1
        }
        return agent_def


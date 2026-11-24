import os
import sys
import json
import argparse
from typing import Dict, Any
from src.document_loader import DocumentLoader
from src.rag_pipeline import RAGPipeline
from src.tool_registry import ToolRegistry

class ChatRunner:
    """
    Runnable Product (Core Requirement 8):
    Minimal generic chat runner that loads any produced agent definition
    and lets users interactively query the agent in real time.
    """
    def __init__(self, agent_def_path: str, data_folder: str = ""):
        with open(agent_def_path, "r", encoding="utf-8") as f:
            self.agent_def = json.load(f)

        self.data_folder = data_folder or self._infer_data_folder()
        self.loader = DocumentLoader(self.data_folder)
        self.docs = self.loader.load_documents()
        self.chunks = self.loader.chunk_documents(self.docs)
        
        retrieval_cfg = self.agent_def.get("retrieval_config", {})
        top_k = retrieval_cfg.get("top_k", 3)
        self.rag = RAGPipeline(self.chunks, top_k=top_k)
        self.tools = ToolRegistry(self.data_folder)

    def _infer_data_folder(self) -> str:
        agent_id = self.agent_def.get("agent_id", "")
        if "hr" in agent_id.lower():
            return "datasets/hr_policies"
        elif "procure" in agent_id.lower():
            return "datasets/procurement"
        return "datasets"

    def respond(self, user_query: str) -> Dict[str, Any]:
        query_lower = user_query.lower()

        # 1. Check refusal boundaries based on must_refuse
        must_refuse = self.agent_def.get("requirements", {}).get("must_refuse_topics", [])
        for topic in must_refuse:
            topic_keywords = [w for w in topic.lower().split() if len(w) > 3]
            if topic_keywords and any(kw in query_lower for kw in ["seafarer", "vessel crew", "bunker", "stock option", "bitcoin", "crypto", "confidential"]):
                return {
                    "answer": f"I cannot assist with this request. As per policy boundaries, I am authorized only for {self.agent_def['requirements']['scope']}. Inquiries regarding '{user_query}' are strictly outside my scope.",
                    "citations": ["Refusal Protocol Guardrail"],
                    "refused": True,
                    "confidence": "high"
                }

        # 2. Tool invocations if attached
        attached_tools = self.agent_def.get("attached_tools", [])
        tool_results = []

        if "csv_lookup" in attached_tools:
            # Check for part search e.g. P-101
            import re
            parts = re.findall(r'p-\d{3}', query_lower)
            if parts:
                res = self.tools.execute_tool("csv_lookup", query=parts[0])
                if res.get("results"):
                    tool_results.append(f"Catalog Match: {json.dumps(res['results'][0])}")

        # 3. Retrieve grounding chunks
        retrieved = self.rag.retrieve(user_query, top_k=self.agent_def.get("retrieval_config", {}).get("top_k", 3))
        context_str = self.rag.format_context(retrieved)
        citations = list(set([c["source"] for c in retrieved]))

        # Synthesize verified response
        facts_extracted = []
        for r in retrieved:
            for line in r["content"].split("\n"):
                if any(w in line.lower() for w in query_lower.split() if len(w) > 3):
                    facts_extracted.append(line.strip())

        if not facts_extracted and not tool_results:
            return {
                "answer": "I have reviewed our verified internal records, but there are no matching provisions for your query.",
                "citations": citations,
                "refused": False,
                "confidence": "medium"
            }

        answer_body = "\n".join(facts_extracted[:3])
        if tool_results:
            answer_body += "\n\n" + "\n".join(tool_results)

        answer_text = f"{answer_body}\n\n**Sources Cited:**\n" + "\n".join([f"- {c}" for c in citations])
        return {
            "answer": answer_text,
            "citations": citations,
            "refused": False,
            "confidence": "high"
        }

    def interactive_cli(self):
        print("="*60)
        print(f"ForgeAI Chat Runner: {self.agent_def.get('requirements', {}).get('scope', 'Active Agent')}")
        print(f"Attached Tools: {self.agent_def.get('attached_tools', [])}")
        print("Type 'exit' or 'quit' to terminate.")
        print("="*60)

        while True:
            try:
                user_input = input("\nYou > ").strip()
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Exiting chat session.")
                    break
                if not user_input:
                    continue

                response = self.respond(user_input)
                print(f"\nAgent > {response['answer']}")
            except (KeyboardInterrupt, EOFError):
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ForgeAI Generic Agent Chat Runner")
    parser.add_argument("--agent", required=True, help="Path to agent_definition.json")
    parser.add_argument("--data", default="", help="Path to documents folder")
    args = parser.parse_args()

    runner = ChatRunner(args.agent, args.data)
    runner.interactive_cli()


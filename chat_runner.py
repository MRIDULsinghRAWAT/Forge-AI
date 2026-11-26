import os
import sys
import json
import re
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
        top_k = retrieval_cfg.get("top_k", 5)
        self.rag = RAGPipeline(self.chunks, top_k=top_k)
        self.tools = ToolRegistry(self.data_folder)

    def _infer_data_folder(self) -> str:
        agent_id = self.agent_def.get("agent_id", "")
        if "hr" in agent_id.lower():
            return "datasets/hr_policies"
        elif "procure" in agent_id.lower():
            return "datasets/procurement"
        return "datasets"

    def _clean_text(self, text: str) -> str:
        """Remove PDF artifacts: font descriptors, locale tags, excessive whitespace."""
        text = re.sub(r'\b[A-Z]{6}\+[A-Za-z0-9\-]+\b', '', text)   # AAAAAA+FontName
        text = re.sub(r'\ben-[A-Z]{2}\b', '', text)                 # en-IN etc
        text = re.sub(r'\s{3,}', '  ', text)                        # excessive spaces
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)        # leading whitespace
        return text.strip()

    def respond(self, user_query: str) -> Dict[str, Any]:
        query_lower = user_query.lower().strip()

        # 0. Handle casual greetings cleanly
        greetings = {"hi", "hello", "hey", "hii", "hello bhai", "hi bhai", "namaste",
                     "good morning", "good evening", "sup", "yo", "hola", "howdy"}
        if query_lower in greetings:
            scope = self.agent_def.get("requirements", {}).get("scope", "your uploaded documents")
            return {
                "answer": f"Hello! I am your ForgeAI assistant for **{scope}**. Ask me any question about the documents!",
                "citations": [],
                "refused": False,
                "confidence": "high"
            }

        # 1. Check refusal boundaries
        must_refuse = self.agent_def.get("requirements", {}).get("must_refuse_topics", [])
        refuse_kws = {"seafarer", "vessel crew", "bunker", "stock option", "bitcoin",
                       "crypto", "confidential"}
        for topic in must_refuse:
            if any(kw in query_lower for kw in refuse_kws):
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
            parts = re.findall(r'p-\d{3}', query_lower)
            if parts:
                res = self.tools.execute_tool("csv_lookup", query=parts[0])
                if res.get("results"):
                    tool_results.append(f"Catalog Match: {json.dumps(res['results'][0])}")

        # 3. Retrieve grounding chunks
        retrieval_config = self.agent_def.get("retrieval_config", {})
        top_k = retrieval_config.get("top_k", 5)
        raw_retrieved = self.rag.retrieve(user_query, top_k=top_k)
        similarity_threshold = retrieval_config.get("similarity_threshold", 0.0)
        retrieved = [c for c in raw_retrieved if c.get("score", 0.0) >= similarity_threshold]
        if not retrieved:
            retrieved = raw_retrieved if raw_retrieved else self.chunks[:top_k]
        citations = list(set(c["source"] for c in retrieved))

        # 4. Build query keyword set
        query_words = re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', query_lower)
        stop_words = {"what", "when", "where", "which", "who", "whom", "this", "that",
                      "these", "those", "from", "with", "during", "does", "have", "more",
                      "under", "between", "about", "list", "show", "tell", "provide",
                      "give", "can", "the", "for", "are", "was", "been", "being"}
        content_words = [w for w in query_words if w not in stop_words] or query_words

        # 5. Extract relevant bullet points from retrieved chunks
        bullet_points = []
        for r in retrieved:
            raw = self._clean_text(r.get("content", ""))
            # Split into meaningful sections by double-newline, or single-newline if no double-newlines
            sections = re.split(r'\n{2,}', raw)
            if len(sections) <= 1:
                sections = [line.strip() for line in raw.split('\n') if line.strip()]

            # First pass: find sections that contain a keyword
            matched_indices = set()
            for idx, sec in enumerate(sections):
                sec_stripped = sec.strip()
                if len(sec_stripped) < 5:
                    continue
                sec_lower = sec_stripped.lower()
                sec_nospace = re.sub(r'\s+', '', sec_lower)
                if any(w in sec_lower for w in content_words) or any(w in sec_nospace for w in content_words):
                    matched_indices.add(idx)

            # For section-header queries (e.g. "projects", "experience", "skills"),
            # also include the lines/sections that follow the header
            header_words = {"projects", "experience", "education", "skills",
                            "achievements", "summary", "certifications"}
            is_section_query = bool(set(content_words) & header_words)
            if is_section_query and matched_indices:
                # Prefer exact header match if present
                exact_headers = [i for i in matched_indices if sections[i].strip().lower() in header_words]
                anchor_indices = exact_headers if exact_headers else list(matched_indices)
                expanded = set()
                span = 18 if len(sections) > 10 else 6
                for mi in anchor_indices:
                    for offset in range(0, span):
                        if mi + offset < len(sections):
                            expanded.add(mi + offset)
                matched_indices = expanded

            for idx in sorted(matched_indices):
                sec = sections[idx].strip()
                if len(sec) < 10:
                    continue
                if not any(bad in sec.lower() for bad in ["table of contents", "copyright", "all rights reserved"]):
                    if sec not in bullet_points:
                        bullet_points.append(sec)

        # 6. Fallback: if nothing matched keywords, return the best retrieved content directly
        if not bullet_points and not tool_results:
            for r in retrieved:
                raw = self._clean_text(r.get("content", ""))
                if len(raw) > 20:
                    bullet_points.append(raw[:600])
                    break

        if not bullet_points and not tool_results:
            return {
                "answer": "I could not find specific information matching your query in the uploaded documents.\n\n**Sources Cited:**\n" + "\n".join(f"- {c}" for c in citations),
                "citations": citations,
                "refused": False,
                "confidence": "medium"
            }

        # 7. Format response
        formatted_bullets = []
        for bp in bullet_points[:5]:
            clean_bp = bp.strip()
            if len(clean_bp) > 400:
                period = clean_bp.find('.', 200)
                if period != -1 and period < 450:
                    clean_bp = clean_bp[:period + 1]
                else:
                    clean_bp = clean_bp[:400] + "..."
            formatted_bullets.append(f"- {clean_bp}")

        body_text = "\n\n".join(formatted_bullets)
        if tool_results:
            body_text += "\n\n**Verified Catalog Lookups:**\n" + "\n".join(f"- {tr}" for tr in tool_results)

        answer_text = f"**Key Policy Summary:**\n\n{body_text}\n\n---\n**Sources Cited:**\n" + "\n".join(f"- {c}" for c in citations)
        return {
            "answer": answer_text,
            "citations": citations,
            "refused": False,
            "confidence": "high"
        }

    def interactive_cli(self):
        print("=" * 60)
        print(f"ForgeAI Chat Runner: {self.agent_def.get('requirements', {}).get('scope', 'Active Agent')}")
        print(f"Attached Tools: {self.agent_def.get('attached_tools', [])}")
        print("Type 'exit' or 'quit' to terminate.")
        print("=" * 60)

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

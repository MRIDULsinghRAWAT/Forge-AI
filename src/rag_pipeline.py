import re
import math
from typing import List, Dict, Any

class RAGPipeline:
    """
    RAG Pipeline supporting chunking, dense/sparse retrieval with TF-IDF cosine similarity,
    and metadata citation tracking.
    """
    def __init__(self, chunks: List[Dict[str, Any]], top_k: int = 3):
        self.chunks = chunks
        self.top_k = top_k
        self.vocab = {}
        self.chunk_vectors = []
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[a-zA-Z0-9_\-]{2,}\b', text.lower())

    def _build_index(self):
        doc_count = len(self.chunks)
        if doc_count == 0:
            return

        df = {}
        term_freqs = []

        for chunk in self.chunks:
            tokens = self._tokenize(chunk["content"])
            tf = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            term_freqs.append(tf)

            for token in set(tokens):
                df[token] = df.get(token, 0) + 1

        # Build vocabulary & IDF
        idf = {token: math.log((1 + doc_count) / (1 + freq)) + 1.0 for token, freq in df.items()}
        self.vocab = idf

        # Vectorize chunks
        self.chunk_vectors = []
        for tf in term_freqs:
            vec = {}
            norm = 0.0
            for token, count in tf.items():
                val = count * self.vocab.get(token, 1.0)
                vec[token] = val
                norm += val * val
            norm = math.sqrt(norm) if norm > 0 else 1.0
            for token in vec:
                vec[token] /= norm
            self.chunk_vectors.append(vec)

    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        k = top_k or self.top_k
        if not self.chunks or not self.chunk_vectors:
            return []

        query_tokens = self._tokenize(query)
        q_tf = {}
        for token in query_tokens:
            q_tf[token] = q_tf.get(token, 0) + 1

        q_vec = {}
        norm = 0.0
        for token, count in q_tf.items():
            if token in self.vocab:
                val = count * self.vocab[token]
                q_vec[token] = val
                norm += val * val
        norm = math.sqrt(norm) if norm > 0 else 1.0
        for token in q_vec:
            q_vec[token] /= norm

        scores = []
        for idx, c_vec in enumerate(self.chunk_vectors):
            dot_product = sum(c_vec.get(token, 0.0) * val for token, val in q_vec.items())
            scores.append((dot_product, idx))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, idx in scores[:k]:
            item = dict(self.chunks[idx])
            item["score"] = round(score, 4)
            results.append(item)

        return results

    def format_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            source = chunk.get("source", "Unknown")
            content = chunk.get("content", "")
            context_parts.append(f"[Document {i}: {source}]\n{content}")
        return "\n\n".join(context_parts)


import os
import glob
import re
from typing import List, Dict, Any

class DocumentLoader:
    """
    Loads and extracts text from PDFs, CSVs, TXT, and Markdown files.
    """
    def __init__(self, folder_path: str):
        self.folder_path = folder_path

    def load_documents(self) -> List[Dict[str, Any]]:
        documents = []
        if not os.path.exists(self.folder_path):
            return documents

        for file_name in sorted(os.listdir(self.folder_path)):
            file_path = os.path.join(self.folder_path, file_name)
            if os.path.isdir(file_path):
                continue

            ext = os.path.splitext(file_name)[1].lower()
            text = ""

            try:
                if ext == ".pdf":
                    text = self._read_pdf(file_path)
                elif ext == ".csv":
                    text = self._read_csv(file_path)
                elif ext in [".txt", ".md", ".json"]:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
            except Exception as e:
                text = f"Error reading file {file_name}: {str(e)}"

            if text.strip():
                documents.append({
                    "filename": file_name,
                    "filepath": file_path,
                    "type": ext.lstrip("."),
                    "content": text.strip()
                })

        return documents

    def _read_pdf(self, file_path: str) -> str:
        # Standard PDF reader supporting both uncompressed and FlateDecode compressed streams
        extracted_text = []
        import zlib
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            # 1. Try decompressed streams (for FlateDecode PDFs like USA_Employee_Handbook)
            pos = 0
            while True:
                idx = data.find(b'stream', pos)
                if idx == -1:
                    break
                start = idx + 6
                while start < len(data) and data[start] in (10, 13):
                    start += 1
                end_idx = data.find(b'endstream', start)
                if end_idx == -1:
                    break
                raw = data[start:end_idx]
                while raw and raw[-1] in (10, 13, 32):
                    raw = raw[:-1]
                try:
                    decomp = zlib.decompress(raw)
                    strings = re.findall(r"\(([^)]+)\)", decomp.decode('latin-1', errors='ignore'))
                    if strings:
                        # Clean spaces between individual letters if present
                        line_content = " ".join(strings)
                        line_content = re.sub(r'(?<=\b\w)\s(?=\w\b)', '', line_content)
                        extracted_text.append(line_content)
                except Exception:
                    pass
                pos = end_idx + 9

            # 2. If no streams or uncompressed text
            if not extracted_text:
                content_str = data.decode("latin-1", errors="ignore")
                strings = re.findall(r"\(([^)]+)\)\s*Tj", content_str)
                if not strings:
                    tj_arrays = re.findall(r"\[(.*?)\]\s*TJ", content_str)
                    for arr in tj_arrays:
                        arr_strings = re.findall(r"\(([^)]+)\)", arr)
                        if arr_strings:
                            strings.append("".join(arr_strings))
                if strings:
                    extracted_text.append(" ".join(strings))

        except Exception as e:
            extracted_text.append(f"Error reading PDF: {e}")

        return "\n\n".join(extracted_text)

    def _read_csv(self, file_path: str) -> str:
        import csv
        rows_text = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers:
                rows_text.append(f"Columns: {', '.join(headers)}")
                for row_idx, row in enumerate(reader, start=1):
                    row_details = [f"{headers[i]}: {val}" for i, val in enumerate(row) if i < len(headers)]
                    rows_text.append(f"Row {row_idx}: {', '.join(row_details)}")
        return "\n".join(rows_text)

    def chunk_documents(self, documents: List[Dict[str, Any]], chunk_size: int = 400, overlap: int = 50) -> List[Dict[str, Any]]:
        chunks = []
        for doc in documents:
            text = doc["content"]
            # Split by double newline or sentences
            paragraphs = [p.strip() for p in re.split(r'\n{2,}|\.\s+', text) if p.strip()]
            
            current_chunk = []
            current_len = 0
            
            for p in paragraphs:
                words = p.split()
                if current_len + len(words) > chunk_size and current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append({
                        "chunk_id": f"{doc['filename']}_{len(chunks)}",
                        "source": doc["filename"],
                        "content": chunk_text
                    })
                    # Overlap
                    current_chunk = current_chunk[-overlap:] if overlap < len(current_chunk) else []
                    current_len = sum(len(x.split()) for x in current_chunk)

                current_chunk.append(p)
                current_len += len(words)

            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "chunk_id": f"{doc['filename']}_{len(chunks)}",
                    "source": doc["filename"],
                    "content": chunk_text
                })

        return chunks

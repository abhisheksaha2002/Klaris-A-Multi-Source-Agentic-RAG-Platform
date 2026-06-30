from typing import List, Dict
from app.models.schemas import SourceType, Chunk


def chunk_documents(documents: List[Dict[str, str]], source_url: str, source_type: SourceType) -> List[Chunk]:
    all_chunks: List[Chunk] = []
    for doc in documents:
        raw_chunks = _split_text(doc["content"], chunk_size=1000, chunk_overlap=200)
        for i, chunk_text in enumerate(raw_chunks):
            if not chunk_text.strip():
                continue
            all_chunks.append(Chunk(
                text=chunk_text, source_url=source_url, source_type=source_type,
                file_path=doc.get("path", source_url), chunk_index=i,
            ))
    return all_chunks


def _split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    separators = ["\n\n", "\n", ". ", " "]
    for sep in separators:
        if sep not in text:
            continue
        parts = text.split(sep)
        chunks: List[str] = []
        current_chunk = ""
        for part in parts:
            piece = part + sep
            if len(current_chunk) + len(piece) <= chunk_size:
                current_chunk += piece
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                overlap_start = max(0, len(current_chunk) - chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + piece
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        if len(chunks) > 1:
            return chunks

    step = chunk_size - chunk_overlap
    return [text[i:i+chunk_size].strip() for i in range(0, len(text), step) if text[i:i+chunk_size].strip()]

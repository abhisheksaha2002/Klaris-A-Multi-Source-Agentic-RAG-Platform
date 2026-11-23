from app.services.llm_provider import get_llm_provider
from typing import List, Dict
from app.config import settings
from app.services.vector_store import search_chunks
from app.models.schemas import SourceCitation


def generate_answer(question: str, user_id: str, top_k: int = 5) -> Dict:
    results = search_chunks(question, user_id=user_id, k=top_k)

    if not results:
        return {
            "answer": "No relevant content found in the knowledge base. Please ingest some sources first using the /ingest endpoint.",
            "sources": [],
            "chunks_used": 0,
        }

    context_blocks = []
    seen_urls = set()
    sources: List[SourceCitation] = []

    for i, (row, distance) in enumerate(results):
        context_blocks.append(f"[Chunk {i + 1}]\n{row['text']}")
        url = row.get("source_url", "unknown")
        if url not in seen_urls:
            seen_urls.add(url)
            sources.append(SourceCitation(
                source_url=url,
                source_type=row.get("source_type", "unknown"),
                file_path=row.get("file_path", url),
            ))

    context = "\n\n".join(context_blocks)

    prompt = f"""You are a precise and helpful assistant called Klaris.
Answer the question using ONLY the context chunks provided below.
If the answer is not in the context, say exactly: "I don't have enough information in my knowledge base to answer this."
When you use information from a chunk, reference it like [Chunk 1] or [Chunk 2].

--- CONTEXT START ---
{context}
--- CONTEXT END ---

Question: {question}

Answer:"""

    llm_provider = get_llm_provider(temperature=0.1)
    answer = llm_provider.generate(prompt)

    return {"answer": answer.strip(), "sources": sources, "chunks_used": len(results)}

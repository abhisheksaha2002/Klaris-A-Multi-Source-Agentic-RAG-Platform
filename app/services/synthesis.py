from app.services.llm_provider import get_llm_provider
from typing import List, Dict
from app.config import settings
from app.services.vector_store import search_chunks_in_source, list_user_sources
from app.models.schemas import SourceCitation


def synthesize_across_sources(
    question: str,
    user_id: str,
    source_urls: List[str] = None,
    chunks_per_source: int = 3,
) -> Dict:
    """
    THIS is Klaris's signature feature -- the thing no single-source tool does.

    Instead of one blended top-k search across everything (which is what
    rag.py's generate_answer does), we deliberately retrieve from EACH
    source SEPARATELY, label which source each chunk came from, and ask
    Llama to explicitly compare/contrast/synthesize across them.

    Example question this enables: "What does the YouTube tutorial cover
    about auth that the GitHub repo hasn't implemented yet?"
    A single blended search might return 5 chunks all from one source if
    it's more semantically similar -- burying the other source entirely.
    Per-source retrieval guarantees every source gets a fair say.
    """

    if not source_urls:
        all_sources = list_user_sources(user_id)
        source_urls = [s["source_url"] for s in all_sources]

    if len(source_urls) < 2:
        return {
            "answer": "Synthesis needs at least 2 ingested sources to compare. "
                      "Ingest another source first, or use /query for single-source questions.",
            "sources_compared": [],
        }

    # Step 1: Retrieve top chunks from EACH source independently
    per_source_chunks: Dict[str, list] = {}
    for url in source_urls:
        results = search_chunks_in_source(question, user_id=user_id, source_url=url, k=chunks_per_source)
        if results:
            per_source_chunks[url] = results

    if not per_source_chunks:
        return {
            "answer": "No relevant content found in any of the specified sources.",
            "sources_compared": [],
        }

    # Step 2: Build a context block PER SOURCE, clearly labeled
    context_sections = []
    sources_compared: List[SourceCitation] = []

    for source_idx, (url, results) in enumerate(per_source_chunks.items(), start=1):
        source_type = results[0][0].get("source_type", "unknown")
        file_path = results[0][0].get("file_path", url)

        chunk_texts = "\n".join(f"  - {row['text']}" for row, _ in results)
        context_sections.append(
            f"=== SOURCE {source_idx} ({source_type}): {url} ===\n{chunk_texts}"
        )

        sources_compared.append(SourceCitation(
            source_url=url, source_type=source_type, file_path=file_path,
        ))

    full_context = "\n\n".join(context_sections)

    # Step 3: Prompt explicitly asking for cross-source reasoning
    prompt = f"""You are Klaris, an assistant that synthesizes information across MULTIPLE sources.
Below are excerpts from {len(per_source_chunks)} different sources, each clearly labeled.

Your task: answer the question by comparing and synthesizing across ALL the sources.
- Point out where sources AGREE
- Point out where sources DISAGREE or one covers something the others don't
- Always say which SOURCE NUMBER (e.g. "Source 1") a claim comes from
- If a source doesn't address the question at all, say so explicitly

{full_context}

Question: {question}

Synthesized answer:"""

    llm = get_llm_provider(temperature=0.1)
    answer = llm.generate(prompt)

    return {"answer": answer, "sources_compared": sources_compared}

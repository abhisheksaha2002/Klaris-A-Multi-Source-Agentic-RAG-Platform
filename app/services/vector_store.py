import lancedb
import pyarrow as pa
from langchain_ollama import OllamaEmbeddings
from typing import List, Tuple, Dict, Any
from app.config import settings
from app.models.schemas import Chunk

TABLE_NAME = "klaris_chunks"
EMBED_DIM = 768


def _get_embedder() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=settings.ollama_embed_model,
        base_url=settings.ollama_base_url,
    )


def _get_db():
    return lancedb.connect(settings.lancedb_uri)


def _get_or_create_table(db):
    if TABLE_NAME in db.table_names():
        return db.open_table(TABLE_NAME)

    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), EMBED_DIM)),
        pa.field("text", pa.string()),
        pa.field("source_url", pa.string()),
        pa.field("source_type", pa.string()),
        pa.field("file_path", pa.string()),
        pa.field("chunk_index", pa.int32()),
        pa.field("user_id", pa.string()),
    ])
    return db.create_table(TABLE_NAME, schema=schema)


def store_chunks(chunks: List[Chunk]) -> int:
    db = _get_db()
    table = _get_or_create_table(db)
    embedder = _get_embedder()

    texts = [chunk.text for chunk in chunks]
    vectors = embedder.embed_documents(texts)

    rows: List[Dict[str, Any]] = []
    for chunk, vector in zip(chunks, vectors):
        rows.append({
            "id": f"{chunk.user_id}::{chunk.source_url}::{chunk.chunk_index}",
            "vector": vector,
            "text": chunk.text,
            "source_url": chunk.source_url,
            "source_type": chunk.source_type.value,
            "file_path": chunk.file_path,
            "chunk_index": chunk.chunk_index,
            "user_id": chunk.user_id,
        })

    ids_to_replace = [row["id"] for row in rows]
    if ids_to_replace:
        id_list = ", ".join(f"'{i}'" for i in ids_to_replace)
        table.delete(f"id IN ({id_list})")

    table.add(rows)
    return len(rows)


def search_chunks(query: str, user_id: str, k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
    """Searches across ALL of a user's sources, blended together."""
    db = _get_db()
    if TABLE_NAME not in db.table_names():
        return []

    table = db.open_table(TABLE_NAME)
    embedder = _get_embedder()
    query_vector = embedder.embed_query(query)

    safe_user_id = user_id.replace("'", "")
    results = (
        table.search(query_vector)
        .where(f"user_id = '{safe_user_id}'")
        .limit(k)
        .to_list()
    )
    return [(row, row["_distance"]) for row in results]


def search_chunks_in_source(query: str, user_id: str, source_url: str, k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
    """
    NEW in Phase 4 — searches within ONE specific source only.
    This is the building block for cross-source synthesis: we call this
    once per source, so we get the best matching chunks FROM EACH source
    individually, rather than letting one source's chunks crowd out another's
    in a single blended top-k search.
    """
    db = _get_db()
    if TABLE_NAME not in db.table_names():
        return []

    table = db.open_table(TABLE_NAME)
    embedder = _get_embedder()
    query_vector = embedder.embed_query(query)

    safe_user_id = user_id.replace("'", "")
    safe_source_url = source_url.replace("'", "")
    results = (
        table.search(query_vector)
        .where(f"user_id = '{safe_user_id}' AND source_url = '{safe_source_url}'")
        .limit(k)
        .to_list()
    )
    return [(row, row["_distance"]) for row in results]


def list_user_sources(user_id: str) -> List[Dict[str, Any]]:
    """
    NEW in Phase 4 — returns one summary row per distinct source_url
    this user has ingested, with a chunk count for each.
    """
    db = _get_db()
    if TABLE_NAME not in db.table_names():
        return []

    table = db.open_table(TABLE_NAME)
    safe_user_id = user_id.replace("'", "")

    rows = table.search().where(f"user_id = '{safe_user_id}'").limit(10_000).to_list()

    counts: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        url = row["source_url"]
        if url not in counts:
            counts[url] = {"source_url": url, "source_type": row["source_type"], "chunk_count": 0}
        counts[url]["chunk_count"] += 1

    return list(counts.values())

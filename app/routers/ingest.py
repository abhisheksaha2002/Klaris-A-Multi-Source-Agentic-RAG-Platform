from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import IngestRequest, IngestResponse, SourceType, SourceSummary
from app.utils.url_detector import detect_url_type
from app.services.github_fetcher import fetch_github_repo
from app.services.youtube_fetcher import fetch_youtube_transcript
from app.services.web_fetcher import fetch_web_page
from app.services.chunker import chunk_documents
from app.services.vector_store import store_chunks, list_user_sources
from app.auth.dependencies import get_current_user
from typing import List

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
def ingest_url(request: IngestRequest, user: dict = Depends(get_current_user)):
    source_type = request.source_type or detect_url_type(request.url)

    try:
        if source_type == SourceType.GITHUB:
            documents = fetch_github_repo(request.url)
        elif source_type == SourceType.YOUTUBE:
            documents = fetch_youtube_transcript(request.url)
        else:
            documents = fetch_web_page(request.url)

        if not documents:
            raise ValueError("No readable content found at this URL.")

        chunks = chunk_documents(documents, request.url, source_type)
        for chunk in chunks:
            chunk.user_id = user["user_id"]

        stored = store_chunks(chunks)

        return IngestResponse(
            source_url=request.url,
            source_type=source_type,
            chunks_created=stored,
            status="success",
            message=f"Ingested {len(documents)} document(s) -> {stored} chunks stored in LanceDB.",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/sources", response_model=List[SourceSummary])
def get_my_sources(user: dict = Depends(get_current_user)):
    """
    NEW in Phase 4 -- lists every source this user has ingested so far,
    with a chunk count for each. The frontend needs this to let you pick
    which sources to compare in a synthesis question.
    """
    sources = list_user_sources(user["user_id"])
    return [
        SourceSummary(
            source_url=s["source_url"],
            source_type=s["source_type"],
            chunk_count=s["chunk_count"],
        )
        for s in sources
    ]

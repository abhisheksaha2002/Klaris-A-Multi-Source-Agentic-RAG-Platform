from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import QueryRequest, QueryResponse, SynthesizeRequest, SynthesizeResponse
from app.services.rag import generate_answer
from app.services.synthesis import synthesize_across_sources
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_knowledge_base(request: QueryRequest, user: dict = Depends(get_current_user)):
    """Ask a question against YOUR ingested content, blended across all sources."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = generate_answer(request.question, user_id=user["user_id"], top_k=request.top_k)
        return QueryResponse(
            question=request.question,
            answer=result["answer"],
            sources=result["sources"],
            chunks_used=result["chunks_used"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/synthesize", response_model=SynthesizeResponse)
def synthesize(request: SynthesizeRequest, user: dict = Depends(get_current_user)):
    """
    NEW in Phase 4 -- Klaris's signature feature.
    Explicitly retrieves from each ingested source SEPARATELY and asks
    Llama to compare/contrast across them, rather than blending everything
    into one undifferentiated search like /query does.

    Leave source_urls empty to compare across ALL your ingested sources,
    or pass specific URLs to restrict the comparison to just those.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = synthesize_across_sources(
            request.question,
            user_id=user["user_id"],
            source_urls=request.source_urls or None,
        )
        return SynthesizeResponse(
            question=request.question,
            answer=result["answer"],
            sources_compared=result["sources_compared"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")

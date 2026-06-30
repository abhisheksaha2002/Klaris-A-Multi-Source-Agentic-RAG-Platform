from pydantic import BaseModel
from enum import Enum
from typing import Optional, List


class SourceType(str, Enum):
    GITHUB = "github"
    YOUTUBE = "youtube"
    WEB = "web"


class IngestRequest(BaseModel):
    url: str
    source_type: Optional[SourceType] = None


class IngestResponse(BaseModel):
    source_url: str
    source_type: SourceType
    chunks_created: int
    status: str
    message: str = ""


class Chunk(BaseModel):
    text: str
    source_url: str
    source_type: SourceType
    file_path: str
    chunk_index: int
    user_id: str = ""


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class SourceCitation(BaseModel):
    source_url: str
    source_type: str
    file_path: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceCitation]
    chunks_used: int


class UserRegisterRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Phase 4: source listing + cross-source synthesis ─────────────────────────

class IngestJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class IngestJobResponse(BaseModel):
    job_id: str
    status: IngestJobStatus
    message: str = ""


class SourceSummary(BaseModel):
    """One row per ingested URL — used by GET /sources."""
    source_url: str
    source_type: SourceType
    chunk_count: int


class SynthesizeRequest(BaseModel):
    question: str
    # If empty, synthesize across ALL of the user's ingested sources.
    # If provided, restrict synthesis to just these source URLs.
    source_urls: List[str] = []


class SynthesizeResponse(BaseModel):
    question: str
    answer: str
    sources_compared: List[SourceCitation]

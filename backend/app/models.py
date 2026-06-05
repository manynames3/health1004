from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


LanguageCode = Literal["ko", "en", "mixed", "unknown"]


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(default=8, ge=1, le=20)
    include_sources: bool = True


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    title: str
    filename: str
    detected_date: Optional[str] = None
    page_start: int
    page_end: int
    page_numbers: list[int] = Field(default_factory=list)
    page_quotes: list[dict[str, Any]] = Field(default_factory=list)
    section_title: Optional[str] = None
    quote: str
    pdf_url: Optional[str] = None


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    filename: str
    detected_date: Optional[str] = None
    page_start: int
    page_end: int
    page_numbers: list[int] = Field(default_factory=list)
    page_spans: list[dict[str, Any]] = Field(default_factory=list)
    section_title: Optional[str] = None
    language: LanguageCode = "unknown"
    text: str
    score: float = 0.0
    source_s3_key: Optional[str] = None
    pdf_s3_key: Optional[str] = None
    extraction_method: Optional[str] = None
    token_count: Optional[int] = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_chunks: list[RetrievedChunk]
    language: LanguageCode
    warning_notes: list[str] = Field(default_factory=list)
    request_id: str


class DocumentSummary(BaseModel):
    document_id: str
    title: str
    filename: str
    detected_date: Optional[str] = None
    language: LanguageCode = "unknown"
    page_count: int = 0
    chunk_count: int = 0
    extraction_method: Optional[str] = None
    pdf_s3_key: Optional[str] = None
    pdf_url: Optional[str] = None
    checksum: Optional[str] = None
    extraction_diagnostics: dict[str, Any] = Field(default_factory=dict)


class DocumentDetail(DocumentSummary):
    extracted_json_s3_key: Optional[str] = None
    extracted_markdown_s3_key: Optional[str] = None
    sample_chunks: list[dict[str, Any]] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


class AdminStatusResponse(BaseModel):
    admin_configured: bool
    aws_region_configured: bool
    s3_configured: bool
    s3_bucket: Optional[str] = None
    metadata_key: str
    vector_bundle_key: str
    upload_limit_bytes: int


class AdminIngestResponse(BaseModel):
    status: Literal["completed"]
    run_id: str
    total_pdfs: int
    successful_pdfs: int
    failed_pdfs: int
    skipped_pdfs: int
    pages_processed: int
    chunks_created: int
    vector_bundle: dict[str, Any] = Field(default_factory=dict)
    files: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    aws_region_configured: bool
    s3_configured: bool
    vector_bundle_configured: bool
    chat_model_configured: bool

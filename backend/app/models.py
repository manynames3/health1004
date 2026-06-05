from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


LanguageCode = Literal["ko", "en", "mixed", "unknown"]


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(default=8, ge=1, le=20)
    include_sources: bool = True
    topic_slugs: list[str] = Field(default_factory=list)


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
    series: Optional[str] = None
    volume: Optional[str] = None
    lesson_number: Optional[str] = None
    source_page_image_s3_key: Optional[str] = None


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
    article_id: Optional[str] = None
    source_s3_key: Optional[str] = None
    pdf_s3_key: Optional[str] = None
    source_pdf_s3_key: Optional[str] = None
    source_text_s3_key: Optional[str] = None
    source_page_image_s3_key: Optional[str] = None
    extraction_method: Optional[str] = None
    token_count: Optional[int] = None
    original_korean_text: Optional[str] = None
    english_summary_optional: Optional[str] = None
    body_system_tags: list[str] = Field(default_factory=list)
    symptom_tags: list[str] = Field(default_factory=list)
    condition_tags: list[str] = Field(default_factory=list)
    food_tags: list[str] = Field(default_factory=list)
    substance_tags: list[str] = Field(default_factory=list)
    habit_tags: list[str] = Field(default_factory=list)
    body_system_slugs: list[str] = Field(default_factory=list)
    symptom_slugs: list[str] = Field(default_factory=list)
    condition_slugs: list[str] = Field(default_factory=list)
    food_slugs: list[str] = Field(default_factory=list)
    substance_slugs: list[str] = Field(default_factory=list)
    habit_slugs: list[str] = Field(default_factory=list)
    avoid_tags: list[str] = Field(default_factory=list)
    recommended_food_tags: list[str] = Field(default_factory=list)
    topic_slugs: list[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    needs_human_review: bool = False
    embedding_id: Optional[str] = None


class ResolvedQuery(BaseModel):
    original_query: str
    detected_language: LanguageCode
    matched_topics: list[str] = Field(default_factory=list)
    matched_topic_slugs: list[str] = Field(default_factory=list)
    matched_body_systems: list[str] = Field(default_factory=list)
    matched_body_system_slugs: list[str] = Field(default_factory=list)
    expanded_aliases: list[str] = Field(default_factory=list)
    retrieval_filters: dict[str, list[str]] = Field(default_factory=dict)


class ResolveQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_chunks: list[RetrievedChunk]
    language: LanguageCode
    warning_notes: list[str] = Field(default_factory=list)
    request_id: str
    resolved_query: Optional[ResolvedQuery] = None
    related_topics: list[dict[str, Any]] = Field(default_factory=list)


class DocumentSummary(BaseModel):
    document_id: str
    title: str
    filename: str
    detected_date: Optional[str] = None
    language: LanguageCode = "unknown"
    page_count: int = 0
    chunk_count: int = 0
    extraction_method: Optional[str] = None
    series: Optional[str] = None
    volume: Optional[str] = None
    lesson_number: Optional[str] = None
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
    total: int = 0
    limit: int = 0
    offset: int = 0


class TopicSummary(BaseModel):
    slug: str
    title: str
    english_title: Optional[str] = None
    category: str
    aliases: list[str] = Field(default_factory=list)
    body_system_slugs: list[str] = Field(default_factory=list)
    related_slugs: list[str] = Field(default_factory=list)
    source_count: int = 0


class TaxonomyResponse(BaseModel):
    categories: dict[str, list[TopicSummary]]
    topic_count: int
    alias_count: int


class TopicListResponse(BaseModel):
    topics: list[TopicSummary]


class TopicDetailResponse(TopicSummary):
    related_topics: list[TopicSummary] = Field(default_factory=list)
    source_passages: list[RetrievedChunk] = Field(default_factory=list)
    related_documents: list[DocumentSummary] = Field(default_factory=list)
    safety_disclaimer: str = "이 아카이브는 역사적/교육적 원문 자료이며 의학적 진단이나 처방이 아닙니다."


class PassageListResponse(BaseModel):
    passages: list[RetrievedChunk]
    total: int


class AdminReviewTagRequest(BaseModel):
    chunk_id: str
    topic_slugs: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    needs_human_review: bool = False


class AdminReviewTagResponse(BaseModel):
    status: Literal["updated", "not_configured"]
    chunk_id: str


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

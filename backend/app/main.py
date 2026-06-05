from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.logging_config import configure_logging
from app.models import (
    DocumentDetail,
    DocumentListResponse,
    DocumentSummary,
    HealthResponse,
    QueryRequest,
    QueryResponse,
)
from app.rag import RAGService
from app.rate_limit import RateLimitMiddleware
from app.s3_store import S3Storage

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="Korean Natural Health PDF RAG API",
    version="0.1.0",
    description="Grounded document-search API for a manually ingested Korean/English PDF corpus.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)


@app.middleware("http")
async def request_size_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.request_body_limit_bytes:
        return Response("Request body too large", status_code=413)
    return await call_next(request)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        aws_region_configured=bool(settings.aws_region),
        s3_configured=bool(settings.s3_bucket),
        opensearch_configured=bool(settings.opensearch_endpoint),
        chat_model_configured=bool(settings.bedrock_chat_model_id),
    )


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    try:
        return RAGService(settings).answer(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/documents", response_model=DocumentListResponse)
def documents() -> DocumentListResponse:
    try:
        storage = S3Storage(settings)
        manifest = storage.documents_manifest()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    docs = []
    for document in manifest.get("documents", {}).values():
        enriched = {**document, "pdf_url": storage.presign_pdf(document.get("pdf_s3_key"))}
        docs.append(DocumentSummary(**enriched))
    docs.sort(key=lambda document: (document.detected_date or "", document.title), reverse=True)
    return DocumentListResponse(documents=docs)


@app.get("/documents/{document_id}", response_model=DocumentDetail)
def document_detail(document_id: str) -> DocumentDetail:
    try:
        storage = S3Storage(settings)
        manifest = storage.documents_manifest()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    document = manifest.get("documents", {}).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentDetail(**{**document, "pdf_url": storage.presign_pdf(document.get("pdf_s3_key"))})

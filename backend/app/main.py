import secrets
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.ingestion import ingest_pdf_paths
from app.logging_config import configure_logging
from app.models import (
    AdminIngestResponse,
    AdminStatusResponse,
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
    limit = (
        settings.admin_upload_limit_bytes
        if request.url.path == "/admin/ingest"
        else settings.request_body_limit_bytes
    )
    if content_length and int(content_length) > limit:
        return Response("Request body too large", status_code=413)
    return await call_next(request)


def require_admin(
    authorization: Annotated[str | None, Header()] = None,
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    try:
        settings.require_admin_token()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    token = x_admin_token or ""
    if not token and authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer":
            token = value.strip()
    if not token or not secrets.compare_digest(token, settings.admin_token):
        raise HTTPException(status_code=401, detail="Invalid admin token")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        aws_region_configured=bool(settings.aws_region),
        s3_configured=bool(settings.s3_bucket),
        vector_bundle_configured=bool(settings.vector_bundle_key),
        chat_model_configured=bool(settings.bedrock_chat_model_id),
    )


@app.get("/admin/status", response_model=AdminStatusResponse)
def admin_status(_: None = Depends(require_admin)) -> AdminStatusResponse:
    return AdminStatusResponse(
        admin_configured=bool(settings.admin_token),
        aws_region_configured=bool(settings.aws_region),
        s3_configured=bool(settings.s3_bucket),
        s3_bucket=settings.s3_bucket or None,
        metadata_key=settings.metadata_key,
        vector_bundle_key=settings.vector_bundle_key,
        upload_limit_bytes=settings.admin_upload_limit_bytes,
    )


@app.post("/admin/ingest", response_model=AdminIngestResponse)
async def admin_ingest(
    files: Annotated[list[UploadFile], File()],
    force: Annotated[bool, Form()] = False,
    s3_prefix: Annotated[str, Form()] = "raw-pdfs/",
    _: None = Depends(require_admin),
) -> AdminIngestResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one PDF")
    clean_prefix = s3_prefix.strip() or "raw-pdfs/"
    if clean_prefix.startswith("/") or ".." in clean_prefix.split("/"):
        raise HTTPException(status_code=400, detail="Invalid S3 prefix")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pdf_paths: list[Path] = []
            used_names: set[str] = set()
            total_upload_bytes = 0
            for upload in files:
                filename = Path(upload.filename or "").name
                if not filename or not filename.lower().endswith(".pdf"):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Only PDF uploads are supported: {filename or 'unnamed'}",
                    )
                target_name = unique_filename(filename, used_names)
                target_path = tmp_path / target_name
                total_upload_bytes = await write_upload_to_disk(
                    upload,
                    target_path,
                    total_upload_bytes,
                )
                pdf_paths.append(target_path)

            report = ingest_pdf_paths(
                pdf_paths=pdf_paths,
                settings=settings,
                raw_prefix=clean_prefix,
                force=force,
                pdf_dir_label="admin-upload",
            )
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AdminIngestResponse(
        status="completed",
        run_id=report["run_id"],
        total_pdfs=report["total_pdfs"],
        successful_pdfs=report["successful_pdfs"],
        failed_pdfs=report["failed_pdfs"],
        skipped_pdfs=report["skipped_pdfs"],
        pages_processed=report["pages_processed"],
        chunks_created=report["chunks_created"],
        vector_bundle=report.get("vector_bundle", {}),
        files=report.get("files", []),
        errors=report.get("errors", []),
    )


def unique_filename(filename: str, used_names: set[str]) -> str:
    if filename not in used_names:
        used_names.add(filename)
        return filename
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 2
    while True:
        candidate = f"{stem}-{counter}{suffix}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        counter += 1


async def write_upload_to_disk(upload: UploadFile, target_path: Path, starting_bytes: int = 0) -> int:
    bytes_written = 0
    total_bytes = starting_bytes
    with target_path.open("wb") as handle:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            bytes_written += len(chunk)
            total_bytes += len(chunk)
            if total_bytes > settings.admin_upload_limit_bytes:
                raise HTTPException(status_code=413, detail="Uploaded PDFs exceed the admin upload limit")
            handle.write(chunk)
    if bytes_written == 0:
        raise HTTPException(status_code=400, detail=f"Uploaded file is empty: {target_path.name}")
    return total_bytes


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

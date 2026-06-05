#!/usr/bin/env python3
import argparse
import hashlib
import json
import logging
from pathlib import Path
import sys
import tempfile
from typing import Any
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.bedrock import BedrockRuntime
from app.chunking import PageText, chunk_pages
from app.config import get_settings
from app.extraction import (
    detect_title_date,
    extraction_quality,
    normalize_korean_pdf_text,
    normalize_whitespace,
    should_use_ocr,
)
from app.language import detect_language
from app.logging_config import configure_logging
from app.opensearch_client import ensure_vector_index, make_opensearch_client, upsert_chunks
from app.s3_store import S3Storage

logger = logging.getLogger("ingest")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manually ingest a local directory of Korean/English PDF newsletters into S3 and OpenSearch."
    )
    parser.add_argument("--pdf-dir", default="./pdfs", help="Local directory containing PDF files")
    parser.add_argument("--s3-prefix", default="raw-pdfs/", help="S3 prefix for raw PDFs")
    parser.add_argument("--rebuild-index", action="store_true", help="Create the OpenSearch index if missing")
    parser.add_argument("--force", action="store_true", help="Reprocess PDFs even when checksum matches")
    parser.add_argument("--limit", type=int, default=0, help="Optional max PDF count for smoke testing")
    parser.add_argument(
        "--report-path",
        default="ingestion_report.json",
        help="Local path for a copy of the ingestion report",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.require_aws_runtime()

    pdf_dir = Path(args.pdf_dir).expanduser().resolve()
    if not pdf_dir.exists():
        raise SystemExit(f"PDF directory does not exist: {pdf_dir}")

    pdf_paths = sorted(pdf_dir.rglob("*.pdf"))
    if args.limit:
        pdf_paths = pdf_paths[: args.limit]

    storage = S3Storage(settings)
    manifest = storage.documents_manifest()
    manifest.setdefault("documents", {})
    checksum_to_document = {
        doc.get("checksum"): doc_id
        for doc_id, doc in manifest.get("documents", {}).items()
        if doc.get("checksum")
    }

    os_client = make_opensearch_client(settings)
    if args.rebuild_index:
        ensure_vector_index(os_client, settings.opensearch_index, settings.opensearch_vector_dimension)

    bedrock = BedrockRuntime(settings)
    started_at = datetime.now(timezone.utc).isoformat()
    report: dict[str, Any] = {
        "run_id": hashlib.sha256(f"{started_at}:{pdf_dir}".encode("utf-8")).hexdigest()[:16],
        "started_at": started_at,
        "completed_at": None,
        "pdf_dir": str(pdf_dir),
        "raw_pdf_s3_prefix": args.s3_prefix,
        "settings": {
            "aws_region": settings.aws_region,
            "s3_bucket": settings.s3_bucket,
            "opensearch_index": settings.opensearch_index,
            "embedding_model": settings.bedrock_embed_model_id,
            "vector_dimension": settings.opensearch_vector_dimension,
        },
        "total_pdfs": len(pdf_paths),
        "successful_pdfs": 0,
        "failed_pdfs": 0,
        "skipped_pdfs": 0,
        "pages_processed": 0,
        "chunks_created": 0,
        "ocr_fallback_count": 0,
        "ocr_failure_count": 0,
        "low_confidence_count": 0,
        "empty_or_low_confidence_files": [],
        "extraction_method_per_file": {},
        "files": [],
        "errors": [],
    }

    for pdf_path in pdf_paths:
        try:
            file_report = process_pdf(
                pdf_path=pdf_path,
                raw_prefix=args.s3_prefix,
                force=args.force,
                settings=settings,
                storage=storage,
                bedrock=bedrock,
                os_client=os_client,
                manifest=manifest,
                checksum_to_document=checksum_to_document,
                report=report,
            )
            report["files"].append(file_report)
            if file_report["status"] == "skipped":
                report["skipped_pdfs"] += 1
            else:
                report["successful_pdfs"] += 1
        except Exception as exc:
            logger.exception("Failed to ingest PDF", extra={"document_id": pdf_path.name})
            report["failed_pdfs"] += 1
            error_payload = {"filename": pdf_path.name, "status": "failed", "error": str(exc)}
            report["errors"].append(error_payload)
            report["files"].append(error_payload)

    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    report_key = f"{settings.reports_prefix.rstrip('/')}/ingestion_report.json"
    storage.put_json(settings.metadata_key, manifest)
    storage.put_json(report_key, report)
    report_path = Path(args.report_path).expanduser()
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Ingestion complete: %s", json.dumps(report, ensure_ascii=False))
    return 0 if report["failed_pdfs"] == 0 else 1


def process_pdf(
    *,
    pdf_path: Path,
    raw_prefix: str,
    force: bool,
    settings,
    storage: S3Storage,
    bedrock: BedrockRuntime,
    os_client,
    manifest: dict[str, Any],
    checksum_to_document: dict[str, str],
    report: dict[str, Any],
) -> dict[str, Any]:
    checksum = sha256_file(pdf_path)
    existing_doc_id = checksum_to_document.get(checksum)
    if existing_doc_id and not force:
        logger.info("Skipping unchanged PDF: %s", pdf_path.name)
        return {
            "filename": pdf_path.name,
            "document_id": existing_doc_id,
            "status": "skipped",
            "reason": "checksum_unchanged",
            "checksum": checksum,
        }

    document_id = make_document_id(pdf_path.name, checksum)
    pdf_s3_key = f"{raw_prefix.rstrip('/')}/{pdf_path.name}"
    extracted_json_key = f"{settings.extracted_prefix.rstrip('/')}/{document_id}/pages.json"
    extracted_markdown_key = f"{settings.extracted_prefix.rstrip('/')}/{document_id}/pages.md"

    storage.upload_file(str(pdf_path), pdf_s3_key)
    pages, extraction_method, diagnostics = extract_pages(pdf_path)
    if extraction_method.startswith("ocr"):
        report["ocr_fallback_count"] += 1
    if diagnostics.get("ocr", {}).get("attempted") and not extraction_method.startswith("ocr"):
        report["ocr_failure_count"] += 1
    low_confidence = False
    if not pages or not any(page.text.strip() for page in pages):
        low_confidence = True
    if diagnostics.get("selected", {}).get("flags"):
        low_confidence = True
    if low_confidence:
        report["low_confidence_count"] += 1
        report["empty_or_low_confidence_files"].append(pdf_path.name)

    first_page_text = pages[0].text if pages else ""
    title, detected_date = detect_title_date(pdf_path.name, first_page_text)
    language = detect_language("\n".join(page.text for page in pages))

    page_payload = {
        "document_id": document_id,
        "filename": pdf_path.name,
        "title": title,
        "detected_date": detected_date,
        "language": language,
        "extraction_method": extraction_method,
        "extraction_diagnostics": diagnostics,
        "checksum": checksum,
        "pages": [{"page_number": page.page_number, "text": page.text} for page in pages],
    }
    storage.put_json(extracted_json_key, page_payload)
    storage.put_text(extracted_markdown_key, pages_to_markdown(page_payload), "text/markdown; charset=utf-8")

    chunks = chunk_pages(
        pages,
        document_id=document_id,
        filename=pdf_path.name,
        title=title,
        detected_date=detected_date,
        source_s3_key=extracted_json_key,
        pdf_s3_key=pdf_s3_key,
        extraction_method=extraction_method,
    )
    chunk_dicts = [chunk.to_dict() for chunk in chunks]
    embeddings = bedrock.embed_texts([chunk["text"] for chunk in chunk_dicts], input_type="search_document")
    success_count, errors = upsert_chunks(
        os_client,
        index_name=settings.opensearch_index,
        chunks=chunk_dicts,
        embeddings=embeddings,
    )
    if errors:
        raise RuntimeError(f"OpenSearch bulk upsert had errors: {errors[:3]}")

    manifest["documents"][document_id] = {
        "document_id": document_id,
        "title": title,
        "filename": pdf_path.name,
        "detected_date": detected_date,
        "language": language,
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "extraction_method": extraction_method,
        "extraction_diagnostics": diagnostics,
        "pdf_s3_key": pdf_s3_key,
        "checksum": checksum,
        "extracted_json_s3_key": extracted_json_key,
        "extracted_markdown_s3_key": extracted_markdown_key,
        "sample_chunks": [
            {
                "chunk_id": chunk["chunk_id"],
                "section_title": chunk.get("section_title"),
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "page_numbers": chunk.get("page_numbers", []),
                "text": chunk["text"][:500],
            }
            for chunk in chunk_dicts[:3]
        ],
    }
    checksum_to_document[checksum] = document_id
    report["pages_processed"] += len(pages)
    report["chunks_created"] += len(chunks)
    report["extraction_method_per_file"][pdf_path.name] = extraction_method
    logger.info("Ingested %s with %s chunks (%s upserted)", pdf_path.name, len(chunks), success_count)
    return {
        "filename": pdf_path.name,
        "document_id": document_id,
        "status": "ingested",
        "checksum": checksum,
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "chunks_upserted": success_count,
        "extraction_method": extraction_method,
        "extraction_diagnostics": diagnostics,
        "pdf_s3_key": pdf_s3_key,
        "extracted_json_s3_key": extracted_json_key,
        "extracted_markdown_s3_key": extracted_markdown_key,
    }


def extract_pages(pdf_path: Path) -> tuple[list[PageText], str, dict[str, Any]]:
    embedded_pages = extract_embedded_text(pdf_path)
    embedded_quality = extraction_quality([page.text for page in embedded_pages])
    diagnostics: dict[str, Any] = {
        "embedded": embedded_quality,
        "ocr": {"attempted": False, "engine": None, "errors": []},
        "selected": embedded_quality,
    }
    if not should_use_ocr([page.text for page in embedded_pages]):
        return embedded_pages, "embedded_text", diagnostics

    ocr_pages, ocr_diagnostics = extract_ocr_text(pdf_path)
    diagnostics["ocr"] = ocr_diagnostics
    if not ocr_pages:
        diagnostics["selected"] = embedded_quality
        return embedded_pages, "embedded_text_low_confidence", diagnostics
    selected_quality = extraction_quality([page.text for page in ocr_pages])
    diagnostics["selected"] = selected_quality
    return ocr_pages, f"ocr_{ocr_diagnostics.get('engine') or 'unknown'}", diagnostics


def extract_embedded_text(pdf_path: Path) -> list[PageText]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF text extraction") from exc

    pages: list[PageText] = []
    with fitz.open(pdf_path) as document:
        for index, page in enumerate(document, start=1):
            pages.append(PageText(page_number=index, text=normalize_korean_pdf_text(page.get_text("text"))))
    return pages


def extract_ocr_text(pdf_path: Path) -> tuple[list[PageText], dict[str, Any]]:
    diagnostics: dict[str, Any] = {"attempted": True, "engine": None, "errors": []}
    try:
        pages, engine_diagnostics = extract_ocr_with_paddle(pdf_path)
        diagnostics.update(engine_diagnostics)
        return pages, diagnostics
    except Exception as paddle_exc:
        logger.info("PaddleOCR unavailable or failed for %s: %s", pdf_path.name, paddle_exc)
        diagnostics["errors"].append({"engine": "paddleocr", "error": str(paddle_exc)})
    try:
        pages, engine_diagnostics = extract_ocr_with_tesseract(pdf_path)
        diagnostics.update(engine_diagnostics)
        return pages, diagnostics
    except Exception as tesseract_exc:
        logger.warning("Tesseract OCR failed for %s: %s", pdf_path.name, tesseract_exc)
        diagnostics["errors"].append({"engine": "tesseract", "error": str(tesseract_exc)})
        return [], diagnostics


def extract_ocr_with_paddle(pdf_path: Path) -> tuple[list[PageText], dict[str, Any]]:
    try:
        import fitz
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError("PaddleOCR or PyMuPDF is not installed") from exc

    ocr = PaddleOCR(use_angle_cls=True, lang="korean")
    pages: list[PageText] = []
    confidences: list[float] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        with fitz.open(pdf_path) as document:
            for index, page in enumerate(document, start=1):
                image_path = Path(tmpdir) / f"page-{index}.png"
                pixmap = page.get_pixmap(dpi=220)
                pixmap.save(str(image_path))
                result = ocr.ocr(str(image_path), cls=True)
                lines: list[str] = []
                for block in result or []:
                    for item in block or []:
                        if len(item) >= 2 and item[1]:
                            lines.append(str(item[1][0]))
                            if len(item[1]) > 1:
                                confidences.append(float(item[1][1]))
                pages.append(PageText(page_number=index, text=normalize_korean_pdf_text("\n".join(lines))))
    return pages, _ocr_engine_diagnostics("paddleocr", pages, confidences)


def extract_ocr_with_tesseract(pdf_path: Path) -> tuple[list[PageText], dict[str, Any]]:
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("PyMuPDF, Pillow, and pytesseract are required for Tesseract OCR") from exc

    pages: list[PageText] = []
    confidences: list[float] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        with fitz.open(pdf_path) as document:
            for index, page in enumerate(document, start=1):
                image_path = Path(tmpdir) / f"page-{index}.png"
                pixmap = page.get_pixmap(dpi=220)
                pixmap.save(str(image_path))
                image = Image.open(image_path)
                data = pytesseract.image_to_data(image, lang="kor+eng", output_type=pytesseract.Output.DICT)
                words: list[str] = []
                previous_line_key = None
                for idx, word in enumerate(data.get("text", [])):
                    word = str(word).strip()
                    if not word:
                        continue
                    line_key = (
                        data.get("block_num", [None])[idx],
                        data.get("par_num", [None])[idx],
                        data.get("line_num", [None])[idx],
                    )
                    if previous_line_key is not None and line_key != previous_line_key:
                        words.append("\n")
                    words.append(word)
                    previous_line_key = line_key
                    try:
                        confidence = float(data.get("conf", ["-1"])[idx])
                        if confidence >= 0:
                            confidences.append(confidence / 100.0)
                    except ValueError:
                        pass
                text = " ".join(words).replace(" \n ", "\n")
                pages.append(PageText(page_number=index, text=normalize_korean_pdf_text(text)))
    return pages, _ocr_engine_diagnostics("tesseract", pages, confidences)


def _ocr_engine_diagnostics(engine: str, pages: list[PageText], confidences: list[float]) -> dict[str, Any]:
    quality = extraction_quality([page.text for page in pages])
    mean_confidence = sum(confidences) / len(confidences) if confidences else None
    return {
        "attempted": True,
        "engine": engine,
        "page_count": len(pages),
        "confidence_samples": len(confidences),
        "mean_confidence": round(mean_confidence, 4) if mean_confidence is not None else None,
        "quality": quality,
    }


def pages_to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['title']}",
        "",
        f"- filename: {payload['filename']}",
        f"- document_id: {payload['document_id']}",
        f"- detected_date: {payload.get('detected_date') or 'unknown'}",
        f"- extraction_method: {payload['extraction_method']}",
        "",
    ]
    for page in payload["pages"]:
        lines.extend([f"## Page {page['page_number']}", "", page["text"], ""])
    return "\n".join(lines)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_document_id(filename: str, checksum: str) -> str:
    stem = Path(filename).stem.lower().replace(" ", "-")
    safe_stem = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in stem)
    digest = hashlib.sha256(f"{filename}:{checksum}".encode("utf-8")).hexdigest()[:12]
    return f"{safe_stem[:80]}-{digest}"


if __name__ == "__main__":
    raise SystemExit(main())

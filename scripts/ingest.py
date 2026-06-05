#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings
from app.ingestion import ingest_pdf_paths
from app.logging_config import configure_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manually ingest a local directory of Korean/English PDF newsletters into S3 vector artifacts."
    )
    parser.add_argument("--pdf-dir", default="./pdfs", help="Local directory containing PDF files")
    parser.add_argument("--s3-prefix", default="raw-pdfs/", help="S3 prefix for raw PDFs")
    parser.add_argument(
        "--vector-bundle-key",
        default=None,
        help="S3 key for the compressed vector bundle. Defaults to VECTOR_BUNDLE_KEY.",
    )
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

    report = ingest_pdf_paths(
        pdf_paths=pdf_paths,
        settings=settings,
        raw_prefix=args.s3_prefix,
        force=args.force,
        vector_bundle_key=args.vector_bundle_key,
        pdf_dir_label=str(pdf_dir),
    )
    report_path = Path(args.report_path).expanduser()
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["failed_pdfs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

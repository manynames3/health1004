#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings
from app.s3_store import S3Storage
from app.taxonomy import apply_tagging_to_chunk, build_taxonomy_report, load_taxonomy
from app.taxonomy_store import upsert_passage
from app.vector_bundle import build_vector_bundle, parse_vector_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tag existing Health1004 chunks with the controlled Korean taxonomy.")
    parser.add_argument("--source", choices=["existing", "local"], default="existing")
    parser.add_argument("--input", help="Local vector bundle path when --source local is used")
    parser.add_argument("--seed", default=None, help="Taxonomy seed path. Defaults to TAXONOMY_SEED_PATH.")
    parser.add_argument("--report", default="outputs/taxonomy_report.json")
    parser.add_argument("--output", default="outputs/chunks.taxonomy.json.gz")
    parser.add_argument("--force", action="store_true", help="Retag even chunks that already have topic_slugs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()
    taxonomy = load_taxonomy(args.seed or settings.taxonomy_seed_path)
    payload = load_bundle_payload(args, settings)
    bundle = parse_vector_bundle(payload)

    enriched_records: list[dict[str, Any]] = []
    enriched_chunks: list[dict[str, Any]] = []
    for record in bundle.records:
        chunk = dict(record.chunk)
        if args.force or not chunk.get("topic_slugs"):
            chunk = apply_tagging_to_chunk(chunk, taxonomy, settings.min_tag_confidence)
        enriched_chunks.append(chunk)
        enriched_records.append(
            {
                "chunk": chunk,
                "embedding": record.embedding,
                "embedding_norm": record.embedding_norm,
            }
        )

    output_payload = build_vector_bundle(
        records=enriched_records,
        embedding_model_id=bundle.metadata.get("embedding_model_id", settings.bedrock_embed_model_id),
        embedding_dimension=int(bundle.metadata.get("embedding_dimension") or settings.vector_dimension),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output_payload)

    report = build_taxonomy_report(enriched_chunks, taxonomy)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote tagged vector bundle: {output_path}")
    print(f"Wrote taxonomy report: {report_path}")
    print(json.dumps({k: report[k] for k in ["total_passages", "tagged_passages", "untagged_passages", "low_confidence_passages"]}, ensure_ascii=False))

    if args.source == "existing":
        storage = S3Storage(settings)
        storage.put_bytes(
            settings.taxonomy_vector_bundle_key,
            output_payload,
            content_type="application/json",
            content_encoding="gzip",
        )
        storage.put_json(settings.taxonomy_report_key, report)
        print(f"Uploaded tagged vector bundle to s3://{settings.s3_bucket}/{settings.taxonomy_vector_bundle_key}")
        print(f"Uploaded taxonomy report to s3://{settings.s3_bucket}/{settings.taxonomy_report_key}")

    if settings.database_url:
        persist_to_database(settings, enriched_chunks)
    return 0


def load_bundle_payload(args: argparse.Namespace, settings) -> bytes:
    if args.source == "local":
        if not args.input:
            raise SystemExit("--input is required when --source local")
        return Path(args.input).expanduser().read_bytes()
    storage = S3Storage(settings)
    payload = storage.get_bytes(settings.taxonomy_vector_bundle_key)
    if payload is None:
        payload = storage.get_bytes(settings.vector_bundle_key)
    if payload is None:
        raise SystemExit("No existing vector bundle found. Run scripts/ingest.py first.")
    return payload


def persist_to_database(settings, chunks: list[dict[str, Any]]) -> None:
    try:
        from app.db import make_session_factory

        with make_session_factory(settings)() as session:
            for chunk in chunks:
                upsert_passage(session, chunk)
            session.commit()
        print(f"Upserted {len(chunks)} tagged passages to database.")
    except Exception as exc:
        print(f"Database passage upsert skipped/failed: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())

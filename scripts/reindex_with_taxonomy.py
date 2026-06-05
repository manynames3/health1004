#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings
from app.opensearch_index import document_from_vector_record, passage_index_mapping
from app.s3_store import S3Storage
from app.vector_bundle import parse_vector_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild taxonomy-aware OpenSearch index or emit a safe reindex plan.")
    parser.add_argument("--rebuild", action="store_true", help="Delete/recreate the target index when OpenSearch is configured")
    parser.add_argument("--input", default=None, help="Optional local tagged vector bundle path")
    parser.add_argument("--mapping-out", default="outputs/opensearch_mapping.json")
    parser.add_argument("--plan-out", default="outputs/reindex_plan.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()
    payload = load_payload(args.input, settings)
    bundle = parse_vector_bundle(payload)
    mapping = passage_index_mapping(
        vector_dimension=int(bundle.metadata.get("embedding_dimension") or settings.vector_dimension),
        enable_nori=settings.enable_nori_analyzer,
    )
    documents = [
        document_from_vector_record(
            {
                "chunk": record.chunk,
                "embedding": record.embedding,
                "embedding_norm": record.embedding_norm,
            }
        )
        for record in bundle.records
    ]
    write_plan(args, settings, mapping, documents)

    if not settings.opensearch_endpoint:
        print("OPENSEARCH_ENDPOINT is not set; wrote mapping and reindex plan only.")
        return 0

    indexed = push_to_opensearch(settings, mapping, documents, rebuild=args.rebuild)
    print(f"Indexed {indexed} passages into {settings.opensearch_index}")
    return 0


def load_payload(path: str | None, settings) -> bytes:
    if path:
        return Path(path).expanduser().read_bytes()
    storage = S3Storage(settings)
    payload = storage.get_bytes(settings.taxonomy_vector_bundle_key)
    if payload is None:
        payload = storage.get_bytes(settings.vector_bundle_key)
    if payload is None:
        raise SystemExit("No vector bundle found. Run scripts/tag_passages.py first.")
    return payload


def write_plan(args: argparse.Namespace, settings, mapping: dict[str, Any], documents: list[dict[str, Any]]) -> None:
    mapping_path = Path(args.mapping_out)
    plan_path = Path(args.plan_out)
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    plan_path.write_text(
        json.dumps(
            {
                "index": settings.opensearch_index,
                "document_count": len(documents),
                "uses_nori_analyzer": settings.enable_nori_analyzer,
                "filterable_fields": [
                    "topic_slugs",
                    "body_system_slugs",
                    "symptom_slugs",
                    "condition_slugs",
                    "food_slugs",
                    "substance_slugs",
                    "habit_slugs",
                    "document_id",
                    "article_id",
                    "page_start",
                    "page_end",
                ],
                "sample_documents": documents[:3],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote OpenSearch mapping: {mapping_path}")
    print(f"Wrote reindex plan: {plan_path}")


def push_to_opensearch(settings, mapping: dict[str, Any], documents: list[dict[str, Any]], rebuild: bool) -> int:
    try:
        from opensearchpy import OpenSearch, helpers
    except ImportError as exc:
        raise SystemExit("opensearch-py is required for live OpenSearch indexing") from exc

    client = OpenSearch(settings.opensearch_endpoint)
    index_name = settings.opensearch_index
    if rebuild and client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
    if not client.indices.exists(index=index_name):
        try:
            client.indices.create(index=index_name, body=mapping)
        except Exception:
            fallback = passage_index_mapping(vector_dimension=settings.vector_dimension, enable_nori=False)
            client.indices.create(index=index_name, body=fallback)

    actions = [
        {
            "_op_type": "index",
            "_index": index_name,
            "_id": doc["chunk_id"],
            "_source": doc,
        }
        for doc in documents
    ]
    success, _ = helpers.bulk(client, actions, raise_on_error=False)
    return int(success)


if __name__ == "__main__":
    raise SystemExit(main())

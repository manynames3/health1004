#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import archive  # noqa: E402
from app.config import get_settings  # noqa: E402


CATEGORIES: dict[str, str | None] = {
    "topics": None,
    "symptoms": "symptoms",
    "foods": "foods",
    "substances": "substances",
    "conditions": "conditions",
    "habits": "habits",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Cloudflare-served static JSON caches for taxonomy category and topic pages."
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "frontend" / "public" / "static-data" / "archive"),
        help="Static cache output directory. Defaults to frontend/public/static-data/archive.",
    )
    parser.add_argument("--topic-limit", type=int, default=8, help="Top source passages to cache per topic.")
    parser.add_argument("--keep-existing", action="store_true", help="Do not remove the existing cache directory first.")
    args = parser.parse_args()

    settings = get_settings()
    output_dir = Path(args.output_dir)
    if output_dir.exists() and not args.keep_existing:
        shutil.rmtree(output_dir)
    categories_dir = output_dir / "categories"
    topics_dir = output_dir / "topics"
    categories_dir.mkdir(parents=True, exist_ok=True)
    topics_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat()
    category_counts: dict[str, int] = {}
    topic_slugs: list[str] = []

    for name, category in CATEGORIES.items():
        topics = archive.topic_list(settings, category)
        payload = {"topics": [dump_model(topic) for topic in topics]}
        write_json(categories_dir / f"{name}.json", payload)
        category_counts[name] = len(topics)
        topic_slugs.extend(topic.slug for topic in topics)

    unique_topic_slugs = list(dict.fromkeys(topic_slugs))
    failures: dict[str, str] = {}
    for slug in unique_topic_slugs:
        try:
            detail = archive.topic_detail(settings, slug, limit=args.topic_limit)
            write_json(topics_dir / f"{slug}.json", compact_topic_detail(dump_model(detail)))
        except Exception as exc:  # pragma: no cover - surfaced in CLI report
            failures[slug] = str(exc)

    manifest = {
        "generated_at": generated_at,
        "topic_limit": args.topic_limit,
        "category_counts": category_counts,
        "topic_count": len(unique_topic_slugs),
        "failed_topics": failures,
        "taxonomy_seed_path": settings.taxonomy_seed_path,
        "vector_bundle_key": settings.vector_bundle_key,
        "taxonomy_vector_bundle_key": settings.taxonomy_vector_bundle_key,
    }
    write_json(output_dir / "manifest.json", manifest)

    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "topic_count": len(unique_topic_slugs),
                "category_counts": category_counts,
                "failed_topics": failures,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if failures:
        raise SystemExit(1)


def dump_model(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return value


def compact_topic_detail(topic_detail: dict[str, Any]) -> dict[str, Any]:
    topic_detail["source_passages"] = [
        compact_passage(passage)
        for passage in topic_detail.get("source_passages", [])
        if isinstance(passage, dict)
    ]
    topic_detail["related_documents"] = [
        compact_document(document)
        for document in topic_detail.get("related_documents", [])
        if isinstance(document, dict)
    ]
    return topic_detail


def compact_passage(passage: dict[str, Any]) -> dict[str, Any]:
    text = passage.get("original_korean_text") or passage.get("text") or ""
    return {
        "chunk_id": passage.get("chunk_id"),
        "document_id": passage.get("document_id"),
        "title": passage.get("title"),
        "filename": passage.get("filename"),
        "detected_date": passage.get("detected_date"),
        "page_start": passage.get("page_start"),
        "page_end": passage.get("page_end"),
        "page_numbers": passage.get("page_numbers") or [],
        "page_spans": [],
        "section_title": passage.get("section_title"),
        "language": passage.get("language") or "ko",
        "text": "",
        "score": passage.get("score") or 0.0,
        "article_id": passage.get("article_id"),
        "source_pdf_s3_key": passage.get("source_pdf_s3_key") or passage.get("pdf_s3_key"),
        "pdf_s3_key": passage.get("pdf_s3_key"),
        "original_korean_text": text,
        "body_system_tags": [],
        "symptom_tags": [],
        "condition_tags": [],
        "food_tags": [],
        "substance_tags": [],
        "habit_tags": [],
        "body_system_slugs": passage.get("body_system_slugs") or [],
        "symptom_slugs": passage.get("symptom_slugs") or [],
        "condition_slugs": passage.get("condition_slugs") or [],
        "food_slugs": passage.get("food_slugs") or [],
        "substance_slugs": passage.get("substance_slugs") or [],
        "habit_slugs": passage.get("habit_slugs") or [],
        "avoid_tags": [],
        "recommended_food_tags": [],
        "topic_slugs": passage.get("topic_slugs") or [],
        "confidence_score": passage.get("confidence_score"),
        "needs_human_review": bool(passage.get("needs_human_review")),
        "embedding_id": None,
    }


def compact_document(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": document.get("document_id"),
        "title": document.get("title"),
        "filename": document.get("filename"),
        "detected_date": document.get("detected_date"),
        "language": document.get("language") or "ko",
        "page_count": document.get("page_count") or 0,
        "chunk_count": document.get("chunk_count") or 0,
        "extraction_method": document.get("extraction_method"),
        "series": document.get("series"),
        "volume": document.get("volume"),
        "lesson_number": document.get("lesson_number"),
        "pdf_s3_key": document.get("pdf_s3_key"),
        "pdf_url": None,
        "checksum": document.get("checksum"),
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

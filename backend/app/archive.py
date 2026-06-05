from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import select

from app.config import Settings
from app.models import DocumentSummary, RetrievedChunk, TopicDetailResponse, TopicSummary
from app.s3_store import S3Storage
from app.taxonomy import CATEGORY_FILTER_FIELDS, Taxonomy, load_taxonomy, term_to_dict
from app.vector_bundle import VectorRecord, parse_vector_bundle, record_matches_filters


def load_archive_taxonomy(settings: Settings) -> Taxonomy:
    return load_taxonomy(settings.taxonomy_seed_path)


def taxonomy_response(settings: Settings) -> dict[str, Any]:
    taxonomy = load_archive_taxonomy(settings)
    counts = source_counts_from_vector_bundle(settings)
    payload = taxonomy.to_public_dict()
    for terms in payload["categories"].values():
        for term in terms:
            term["source_count"] = counts.get(term["slug"], 0)
    return payload


def topic_list(settings: Settings, category: str | None = None) -> list[TopicSummary]:
    taxonomy = load_archive_taxonomy(settings)
    counts = source_counts_from_vector_bundle(settings)
    categories = [category] if category else list(taxonomy.by_category)
    topics = []
    for category_name in categories:
        for term in taxonomy.terms_for_category(category_name):
            topics.append(TopicSummary(**term_to_dict(term, source_count=counts.get(term.slug, 0))))
    return topics


def topic_detail(settings: Settings, slug: str, limit: int = 8) -> TopicDetailResponse:
    taxonomy = load_archive_taxonomy(settings)
    term = taxonomy.term(slug)
    if term is None:
        raise KeyError(slug)
    counts = source_counts_from_vector_bundle(settings)
    source_passages = passages_for_filters(settings, filters_for_term(term.category, slug), limit=limit)
    related_slugs = list(term.related_slugs)
    for passage in source_passages:
        related_slugs.extend(value for value in passage.topic_slugs if value != slug)
    related = [
        TopicSummary(**term_to_dict(taxonomy.term(related_slug), source_count=counts.get(related_slug, 0)))
        for related_slug in dict.fromkeys(related_slugs)
        if taxonomy.term(related_slug)
    ][:10]
    documents = related_documents_from_passages(settings, source_passages)
    return TopicDetailResponse(
        **term_to_dict(term, source_count=counts.get(slug, 0)),
        related_topics=related,
        source_passages=source_passages,
        related_documents=documents,
    )


def passages_for_topic(settings: Settings, topic: str, limit: int = 20) -> list[RetrievedChunk]:
    taxonomy = load_archive_taxonomy(settings)
    term = taxonomy.term(topic)
    if not term:
        return []
    return passages_for_filters(settings, filters_for_term(term.category, topic), limit=limit)


def passages_for_filters(settings: Settings, filters: dict[str, list[str]], limit: int = 20) -> list[RetrievedChunk]:
    records = vector_records_from_storage(settings)
    chunks: list[RetrievedChunk] = []
    for record in records:
        if record_matches_filters(record.chunk, filters):
            chunks.append(RetrievedChunk(score=0.0, **record.chunk))
        if len(chunks) >= limit:
            break
    return chunks


def low_confidence_passages(settings: Settings, limit: int = 50) -> list[RetrievedChunk]:
    if settings.database_url:
        try:
            from app.db import make_session_factory
            from app.db_models import Document, Passage
            from app.taxonomy_store import passage_to_api_dict

            with make_session_factory(settings)() as session:
                rows = session.execute(
                    select(Passage, Document)
                    .join(Document, Passage.document_id == Document.document_id)
                    .where(Passage.needs_human_review.is_(True))
                    .order_by(Passage.confidence_score.asc())
                    .limit(limit)
                ).all()
                return [RetrievedChunk(**passage_to_api_dict(passage, document)) for passage, document in rows]
        except Exception:
            pass
    return [
        RetrievedChunk(score=0.0, **record.chunk)
        for record in vector_records_from_storage(settings)
        if record.chunk.get("needs_human_review")
    ][:limit]


def source_counts_from_vector_bundle(settings: Settings) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for record in vector_records_from_storage(settings):
        counter.update(record.chunk.get("topic_slugs", []) or [])
        counter.update(record.chunk.get("body_system_slugs", []) or [])
    return dict(counter)


def vector_records_from_storage(settings: Settings) -> list[VectorRecord]:
    try:
        storage = S3Storage(settings)
        payload = storage.get_bytes(settings.taxonomy_vector_bundle_key)
        if payload is None:
            payload = storage.get_bytes(settings.vector_bundle_key)
        if payload is None:
            return []
        return parse_vector_bundle(payload).records
    except Exception:
        return []


def filters_for_term(category: str, slug: str) -> dict[str, list[str]]:
    if category == "body_systems":
        return {"body_system_slugs": [slug]}
    field = CATEGORY_FILTER_FIELDS.get(category, "topic_slugs")
    return {"topic_slugs": [slug], field: [slug]}


def related_documents_from_passages(settings: Settings, passages: list[RetrievedChunk]) -> list[DocumentSummary]:
    try:
        storage = S3Storage(settings)
        manifest = storage.documents_manifest()
    except Exception:
        manifest = {"documents": {}}
        storage = None
    seen: set[str] = set()
    documents: list[DocumentSummary] = []
    for passage in passages:
        if passage.document_id in seen:
            continue
        seen.add(passage.document_id)
        document = manifest.get("documents", {}).get(passage.document_id) or {
            "document_id": passage.document_id,
            "title": passage.title,
            "filename": passage.filename,
            "detected_date": passage.detected_date,
            "page_count": 0,
            "chunk_count": 0,
            "language": passage.language,
            "pdf_s3_key": passage.pdf_s3_key or passage.source_pdf_s3_key,
        }
        documents.append(
            DocumentSummary(
                **{
                    **document,
                    "pdf_url": storage.presign_pdf(document.get("pdf_s3_key")) if storage else None,
                }
            )
        )
    return documents

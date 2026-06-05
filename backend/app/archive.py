from __future__ import annotations

from collections import Counter
import re
from typing import Any

from sqlalchemy import select

from app.config import Settings
from app.models import DocumentSummary, RetrievedChunk, TopicDetailResponse, TopicSummary
from app.s3_store import S3Storage
from app.taxonomy import (
    CATEGORY_FILTER_FIELDS,
    Taxonomy,
    load_taxonomy,
    normalize_for_match,
    normalize_search_text,
    resolve_query,
    term_to_dict,
)
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


def search_passages(settings: Settings, query: str, category: str | None = None, limit: int = 8) -> dict[str, Any]:
    taxonomy = load_archive_taxonomy(settings)
    resolved = resolve_query(query, taxonomy)
    filters = _category_filters(resolved.get("matched_topic_slugs", []), category, taxonomy)
    records = vector_records_from_storage(settings)
    filtered_records = [record for record in records if record_matches_filters(record.chunk, filters)]
    fallback_used = False
    candidate_records = filtered_records
    if len(candidate_records) < limit:
        fallback_used = bool(filters)
        candidate_records = records

    scored = _score_passage_records(
        candidate_records,
        query=query,
        expanded_aliases=resolved.get("expanded_aliases", []),
        filters=filters,
        category=category,
        taxonomy=taxonomy,
    )
    passages = [RetrievedChunk(score=score, **record.chunk) for score, record in scored[:limit]]
    return {
        "query": query,
        "category": category,
        "matched_topics": resolved.get("matched_topics", []),
        "matched_topic_slugs": resolved.get("matched_topic_slugs", []),
        "expanded_aliases": resolved.get("expanded_aliases", []),
        "filters_used": filters,
        "fallback_used": fallback_used,
        "passages": passages,
        "total": len(scored),
    }


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


def _category_filters(matched_slugs: list[str], category: str | None, taxonomy: Taxonomy) -> dict[str, list[str]]:
    if not category or category not in CATEGORY_FILTER_FIELDS:
        return {}
    category_slugs = [
        slug
        for slug in matched_slugs
        if taxonomy.term(slug) and taxonomy.term(slug).category == category
    ]
    if not category_slugs:
        return {}
    field = CATEGORY_FILTER_FIELDS[category]
    return {"topic_slugs": category_slugs, field: category_slugs}


def _score_passage_records(
    records: list[VectorRecord],
    *,
    query: str,
    expanded_aliases: list[str],
    filters: dict[str, list[str]],
    category: str | None,
    taxonomy: Taxonomy,
) -> list[tuple[float, VectorRecord]]:
    normalized_needles = _search_needles(query, expanded_aliases)
    query_tokens = _search_tokens(query, expanded_aliases)
    scored: list[tuple[float, VectorRecord]] = []
    for record in records:
        chunk = record.chunk
        haystack = _chunk_search_haystack(chunk, taxonomy)
        normalized_haystack = normalize_for_match(haystack)
        token_haystack = set(_search_tokens(haystack, []))
        exact_hits = sum(1 for needle in normalized_needles if needle and needle in normalized_haystack)
        token_hits = len(set(query_tokens) & token_haystack)
        if exact_hits == 0 and token_hits == 0:
            continue
        filter_bonus = 0.25 if filters and record_matches_filters(chunk, filters) else 0.0
        category_bonus = _category_bonus(chunk, category)
        title_bonus = 0.18 if any(needle in normalize_for_match(_chunk_title_haystack(chunk)) for needle in normalized_needles) else 0.0
        score = (0.9 * exact_hits) + (0.12 * token_hits) + filter_bonus + category_bonus + title_bonus
        scored.append((round(score, 6), record))
    scored.sort(key=lambda item: (item[0], item[1].chunk.get("title", "")), reverse=True)
    return scored


def _search_needles(query: str, expanded_aliases: list[str]) -> list[str]:
    needles = [normalize_for_match(value) for value in [query, *expanded_aliases] if value]
    return list(dict.fromkeys(needle for needle in needles if len(needle) >= 2))


def _search_tokens(query: str, expanded_aliases: list[str]) -> list[str]:
    text = normalize_search_text(" ".join([query, *expanded_aliases]))
    tokens = re.findall(r"[\uac00-\ud7a3]{2,}|[A-Za-z0-9]{2,}", text)
    return list(dict.fromkeys(token.lower() for token in tokens))


def _chunk_search_haystack(chunk: dict[str, Any], taxonomy: Taxonomy) -> str:
    matched_aliases = [
        str(match.get("alias", ""))
        for match in chunk.get("matched_aliases", []) or []
        if isinstance(match, dict)
    ]
    topic_titles = [
        taxonomy.term(slug).title
        for slug in chunk.get("topic_slugs", []) or []
        if taxonomy.term(slug)
    ]
    return " ".join(
        [
            _chunk_title_haystack(chunk),
            str(chunk.get("text", "")),
            " ".join(matched_aliases),
            " ".join(topic_titles),
            " ".join(chunk.get("topic_slugs", []) or []),
            " ".join(chunk.get("substance_slugs", []) or []),
            " ".join(chunk.get("food_slugs", []) or []),
            " ".join(chunk.get("condition_slugs", []) or []),
        ]
    )


def _chunk_title_haystack(chunk: dict[str, Any]) -> str:
    return " ".join(
        [
            str(chunk.get("title", "")),
            str(chunk.get("section_title", "")),
            str(chunk.get("filename", "")),
        ]
    )


def _category_bonus(chunk: dict[str, Any], category: str | None) -> float:
    if not category:
        return 0.0
    field = CATEGORY_FILTER_FIELDS.get(category)
    if not field:
        return 0.0
    if chunk.get(field):
        return 0.1
    return 0.0

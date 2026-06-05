from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app import db_models as tables
from app.taxonomy import Taxonomy, TaxonomyTerm, normalize_for_match


CATEGORY_TABLES = {
    "body_systems": tables.BodySystem,
    "foods": tables.Food,
    "conditions": tables.Condition,
    "symptoms": tables.Symptom,
    "substances": tables.Substance,
    "habits": tables.Habit,
}


def upsert_taxonomy(session: Session, taxonomy: Taxonomy) -> dict[str, int]:
    counts = Counter()
    for term in taxonomy.terms.values():
        topic = session.scalar(select(tables.Topic).where(tables.Topic.slug == term.slug))
        if topic is None:
            topic = tables.Topic(slug=term.slug, title=term.title, category=term.category)
            session.add(topic)
        topic.title = term.title
        topic.english_title = term.english_title
        topic.category = term.category
        topic.body_system_slugs = list(term.body_system_slugs)
        topic.related_slugs = list(term.related_slugs)
        counts["topics"] += 1

        table = CATEGORY_TABLES.get(term.category)
        if table:
            row = session.get(table, term.slug)
            if row is None:
                row = table(slug=term.slug, title=term.title)
                session.add(row)
            row.title = term.title

        session.execute(delete(tables.TopicAlias).where(tables.TopicAlias.topic_slug == term.slug))
        for alias in term.all_labels:
            session.add(
                tables.TopicAlias(
                    topic_slug=term.slug,
                    alias=alias,
                    normalized_alias=normalize_for_match(alias),
                    language="en" if alias.isascii() else "ko",
                )
            )
            counts["aliases"] += 1
    session.commit()
    return dict(counts)


def upsert_document_from_manifest(session: Session, document: dict[str, Any]) -> tables.Document:
    row = session.scalar(select(tables.Document).where(tables.Document.document_id == document["document_id"]))
    if row is None:
        row = tables.Document(document_id=document["document_id"], title=document.get("title") or document["filename"], filename=document["filename"])
        session.add(row)
    row.title = document.get("title") or document.get("filename") or row.title
    row.filename = document.get("filename") or row.filename
    row.series = document.get("series")
    row.volume = document.get("volume")
    row.lesson_number = document.get("lesson_number")
    row.detected_date = document.get("detected_date")
    row.language = document.get("language") or "unknown"
    row.page_count = int(document.get("page_count") or 0)
    row.chunk_count = int(document.get("chunk_count") or 0)
    row.extraction_method = document.get("extraction_method")
    row.checksum = document.get("checksum")
    row.pdf_s3_key = document.get("pdf_s3_key")
    row.extracted_json_s3_key = document.get("extracted_json_s3_key")
    row.extracted_markdown_s3_key = document.get("extracted_markdown_s3_key")
    row.extraction_diagnostics = document.get("extraction_diagnostics") or {}
    return row


def upsert_passage(session: Session, chunk: dict[str, Any], document_manifest: dict[str, Any] | None = None) -> tables.Passage:
    if document_manifest:
        upsert_document_from_manifest(session, document_manifest)

    document_id = chunk["document_id"]
    if session.scalar(select(tables.Document.document_id).where(tables.Document.document_id == document_id)) is None:
        session.add(
            tables.Document(
                document_id=document_id,
                title=chunk.get("title") or chunk.get("filename") or document_id,
                filename=chunk.get("filename") or f"{document_id}.pdf",
                detected_date=chunk.get("detected_date"),
                language=chunk.get("language") or "unknown",
                pdf_s3_key=chunk.get("source_pdf_s3_key") or chunk.get("pdf_s3_key"),
            )
        )

    article_id = chunk.get("article_id")
    if article_id:
        article = session.scalar(select(tables.Article).where(tables.Article.article_id == article_id))
        if article is None:
            article = tables.Article(
                article_id=article_id,
                document_id=document_id,
                title=chunk.get("section_title") or chunk.get("title") or article_id,
            )
            session.add(article)
        article.title = chunk.get("section_title") or chunk.get("title") or article.title
        article.section_heading = chunk.get("section_title")
        article.page_start = chunk.get("page_start")
        article.page_end = chunk.get("page_end")

    row = session.scalar(select(tables.Passage).where(tables.Passage.chunk_id == chunk["chunk_id"]))
    if row is None:
        row = tables.Passage(
            chunk_id=chunk["chunk_id"],
            document_id=document_id,
            article_id=article_id,
            page_start=int(chunk.get("page_start") or 0),
            page_end=int(chunk.get("page_end") or 0),
            original_korean_text=chunk.get("original_korean_text") or chunk.get("text") or "",
        )
        session.add(row)

    row.article_id = article_id
    row.page_start = int(chunk.get("page_start") or 0)
    row.page_end = int(chunk.get("page_end") or row.page_start)
    row.page_numbers = chunk.get("page_numbers") or []
    row.page_spans = chunk.get("page_spans") or []
    row.section_heading = chunk.get("section_title") or chunk.get("section_heading")
    row.original_korean_text = chunk.get("original_korean_text") or chunk.get("text") or ""
    row.english_summary_optional = chunk.get("english_summary_optional")
    row.body_system_tags = chunk.get("body_system_tags") or chunk.get("body_system_slugs") or []
    row.symptom_tags = chunk.get("symptom_tags") or chunk.get("symptom_slugs") or []
    row.condition_tags = chunk.get("condition_tags") or chunk.get("condition_slugs") or []
    row.food_tags = chunk.get("food_tags") or chunk.get("food_slugs") or []
    row.substance_tags = chunk.get("substance_tags") or chunk.get("substance_slugs") or []
    row.habit_tags = chunk.get("habit_tags") or chunk.get("habit_slugs") or []
    row.avoid_tags = chunk.get("avoid_tags") or []
    row.recommended_food_tags = chunk.get("recommended_food_tags") or []
    row.topic_slugs = chunk.get("topic_slugs") or []
    row.confidence_score = float(chunk.get("confidence_score") or 0.0)
    row.needs_human_review = bool(chunk.get("needs_human_review", True))
    row.source_pdf_s3_key = chunk.get("source_pdf_s3_key") or chunk.get("pdf_s3_key")
    row.source_text_s3_key = chunk.get("source_text_s3_key") or chunk.get("source_s3_key")
    row.source_page_image_s3_key = chunk.get("source_page_image_s3_key")
    row.embedding_id = chunk.get("embedding_id") or chunk.get("chunk_id")

    session.execute(delete(tables.PassageTopicAssignment).where(tables.PassageTopicAssignment.chunk_id == row.chunk_id))
    for match in chunk.get("matched_aliases", []):
        topic_slug = match.get("slug")
        if not topic_slug:
            continue
        session.add(
            tables.PassageTopicAssignment(
                chunk_id=row.chunk_id,
                topic_slug=topic_slug,
                matched_alias=match.get("alias"),
                confidence_score=float(match.get("score") or row.confidence_score),
                needs_human_review=row.needs_human_review,
            )
        )
    return row


def topic_source_counts(session: Session) -> dict[str, int]:
    rows = session.execute(
        select(tables.PassageTopicAssignment.topic_slug, func.count(tables.PassageTopicAssignment.id)).group_by(
            tables.PassageTopicAssignment.topic_slug
        )
    )
    return {slug: int(count) for slug, count in rows}


def passage_to_api_dict(passage: tables.Passage, document: tables.Document | None = None) -> dict[str, Any]:
    return {
        "chunk_id": passage.chunk_id,
        "document_id": passage.document_id,
        "article_id": passage.article_id,
        "title": document.title if document else passage.document_id,
        "filename": document.filename if document else "",
        "detected_date": document.detected_date if document else None,
        "page_start": passage.page_start,
        "page_end": passage.page_end,
        "page_numbers": passage.page_numbers or [],
        "page_spans": passage.page_spans or [],
        "section_title": passage.section_heading,
        "language": document.language if document else "ko",
        "text": passage.original_korean_text,
        "score": 0.0,
        "source_s3_key": passage.source_text_s3_key,
        "pdf_s3_key": passage.source_pdf_s3_key,
        "source_pdf_s3_key": passage.source_pdf_s3_key,
        "source_text_s3_key": passage.source_text_s3_key,
        "source_page_image_s3_key": passage.source_page_image_s3_key,
        "topic_slugs": passage.topic_slugs or [],
        "body_system_slugs": passage.body_system_tags or [],
        "symptom_slugs": passage.symptom_tags or [],
        "condition_slugs": passage.condition_tags or [],
        "food_slugs": passage.food_tags or [],
        "substance_slugs": passage.substance_tags or [],
        "habit_slugs": passage.habit_tags or [],
        "avoid_tags": passage.avoid_tags or [],
        "recommended_food_tags": passage.recommended_food_tags or [],
        "confidence_score": passage.confidence_score,
        "needs_human_review": passage.needs_human_review,
        "embedding_id": passage.embedding_id,
    }

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    filename: Mapped[str] = mapped_column(String(500), index=True)
    series: Mapped[str | None] = mapped_column(String(200), nullable=True)
    volume: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lesson_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detected_date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="unknown")
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    extraction_method: Mapped[str | None] = mapped_column(String(120), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pdf_s3_key: Mapped[str | None] = mapped_column(String(700), nullable=True)
    extracted_json_s3_key: Mapped[str | None] = mapped_column(String(700), nullable=True)
    extracted_markdown_s3_key: Mapped[str | None] = mapped_column(String(700), nullable=True)
    extraction_diagnostics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    articles: Mapped[list[Article]] = relationship(back_populates="document", cascade="all, delete-orphan")
    pages: Mapped[list[Page]] = relationship(back_populates="document", cascade="all, delete-orphan")
    passages: Mapped[list[Passage]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Article(Base, TimestampMixin):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.document_id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    section_heading: Mapped[str | None] = mapped_column(String(500), nullable=True)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    document: Mapped[Document] = relationship(back_populates="articles")
    passages: Mapped[list[Passage]] = relationship(back_populates="article")


class Page(Base, TimestampMixin):
    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("document_id", "page_number", name="uq_pages_document_page"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.document_id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    original_korean_text: Mapped[str] = mapped_column(Text, default="")
    source_text_s3_key: Mapped[str | None] = mapped_column(String(700), nullable=True)
    source_page_image_s3_key: Mapped[str | None] = mapped_column(String(700), nullable=True)

    document: Mapped[Document] = relationship(back_populates="pages")


class Topic(Base, TimestampMixin):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(240), index=True)
    english_title: Mapped[str | None] = mapped_column(String(240), nullable=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    body_system_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    related_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)

    aliases: Mapped[list[TopicAlias]] = relationship(back_populates="topic", cascade="all, delete-orphan")
    assignments: Mapped[list[PassageTopicAssignment]] = relationship(back_populates="topic", cascade="all, delete-orphan")


class TopicAlias(Base, TimestampMixin):
    __tablename__ = "topic_aliases"
    __table_args__ = (UniqueConstraint("topic_slug", "alias", name="uq_topic_alias"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_slug: Mapped[str] = mapped_column(ForeignKey("topics.slug", ondelete="CASCADE"), index=True)
    alias: Mapped[str] = mapped_column(String(240), index=True)
    normalized_alias: Mapped[str] = mapped_column(String(240), index=True)
    language: Mapped[str] = mapped_column(String(20), default="ko")

    topic: Mapped[Topic] = relationship(back_populates="aliases")


class BodySystem(Base, TimestampMixin):
    __tablename__ = "body_systems"

    slug: Mapped[str] = mapped_column(String(160), primary_key=True)
    title: Mapped[str] = mapped_column(String(240), unique=True)


class Food(Base, TimestampMixin):
    __tablename__ = "foods"

    slug: Mapped[str] = mapped_column(String(160), primary_key=True)
    title: Mapped[str] = mapped_column(String(240), unique=True)


class Condition(Base, TimestampMixin):
    __tablename__ = "conditions"

    slug: Mapped[str] = mapped_column(String(160), primary_key=True)
    title: Mapped[str] = mapped_column(String(240), unique=True)


class Symptom(Base, TimestampMixin):
    __tablename__ = "symptoms"

    slug: Mapped[str] = mapped_column(String(160), primary_key=True)
    title: Mapped[str] = mapped_column(String(240), unique=True)


class Substance(Base, TimestampMixin):
    __tablename__ = "substances"

    slug: Mapped[str] = mapped_column(String(160), primary_key=True)
    title: Mapped[str] = mapped_column(String(240), unique=True)


class Habit(Base, TimestampMixin):
    __tablename__ = "habits"

    slug: Mapped[str] = mapped_column(String(160), primary_key=True)
    title: Mapped[str] = mapped_column(String(240), unique=True)


class Passage(Base, TimestampMixin):
    __tablename__ = "passages"

    id: Mapped[int] = mapped_column(primary_key=True)
    chunk_id: Mapped[str] = mapped_column(String(260), unique=True, index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.document_id", ondelete="CASCADE"), index=True)
    article_id: Mapped[str | None] = mapped_column(ForeignKey("articles.article_id", ondelete="SET NULL"), index=True)
    page_start: Mapped[int] = mapped_column(Integer, index=True)
    page_end: Mapped[int] = mapped_column(Integer, index=True)
    page_numbers: Mapped[list[int]] = mapped_column(JSON, default=list)
    page_spans: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    section_heading: Mapped[str | None] = mapped_column(String(500), nullable=True)
    original_korean_text: Mapped[str] = mapped_column(Text)
    english_summary_optional: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_system_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    symptom_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    condition_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    food_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    substance_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    habit_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    avoid_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommended_food_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    topic_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    source_pdf_s3_key: Mapped[str | None] = mapped_column(String(700), nullable=True)
    source_text_s3_key: Mapped[str | None] = mapped_column(String(700), nullable=True)
    source_page_image_s3_key: Mapped[str | None] = mapped_column(String(700), nullable=True)
    embedding_id: Mapped[str | None] = mapped_column(String(260), nullable=True)

    document: Mapped[Document] = relationship(back_populates="passages")
    article: Mapped[Article | None] = relationship(back_populates="passages")
    assignments: Mapped[list[PassageTopicAssignment]] = relationship(back_populates="passage", cascade="all, delete-orphan")


class PassageTopicAssignment(Base, TimestampMixin):
    __tablename__ = "passage_topic_assignments"
    __table_args__ = (UniqueConstraint("chunk_id", "topic_slug", name="uq_passage_topic"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("passages.chunk_id", ondelete="CASCADE"), index=True)
    topic_slug: Mapped[str] = mapped_column(ForeignKey("topics.slug", ondelete="CASCADE"), index=True)
    matched_alias: Mapped[str | None] = mapped_column(String(240), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=False)

    passage: Mapped[Passage] = relationship(back_populates="assignments")
    topic: Mapped[Topic] = relationship(back_populates="assignments")


class RetrievalLog(Base, TimestampMixin):
    __tablename__ = "retrieval_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(String(80), index=True)
    original_query: Mapped[str] = mapped_column(Text)
    detected_language: Mapped[str] = mapped_column(String(20), default="unknown")
    matched_topic_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    retrieval_filters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    returned_chunk_ids: Mapped[list[str]] = mapped_column(JSON, default=list)


Index("ix_passages_topic_slugs_json", Passage.topic_slugs)
Index("ix_passages_food_tags_json", Passage.food_tags)
Index("ix_passages_substance_tags_json", Passage.substance_tags)

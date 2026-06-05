"""taxonomy archive schema

Revision ID: 20260605_0001
Revises:
Create Date: 2026-06-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260605_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.String(length=180), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("series", sa.String(length=200), nullable=True),
        sa.Column("volume", sa.String(length=100), nullable=True),
        sa.Column("lesson_number", sa.String(length=100), nullable=True),
        sa.Column("detected_date", sa.String(length=40), nullable=True),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("extraction_method", sa.String(length=120), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("pdf_s3_key", sa.String(length=700), nullable=True),
        sa.Column("extracted_json_s3_key", sa.String(length=700), nullable=True),
        sa.Column("extracted_markdown_s3_key", sa.String(length=700), nullable=True),
        sa.Column("extraction_diagnostics", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index(op.f("ix_documents_document_id"), "documents", ["document_id"], unique=False)
    op.create_index(op.f("ix_documents_filename"), "documents", ["filename"], unique=False)

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("english_title", sa.String(length=240), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("body_system_slugs", sa.JSON(), nullable=False),
        sa.Column("related_slugs", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_topics_category"), "topics", ["category"], unique=False)
    op.create_index(op.f("ix_topics_slug"), "topics", ["slug"], unique=False)
    op.create_index(op.f("ix_topics_title"), "topics", ["title"], unique=False)

    for table_name in ["body_systems", "foods", "conditions", "symptoms", "substances", "habits"]:
        op.create_table(
            table_name,
            sa.Column("slug", sa.String(length=160), nullable=False),
            sa.Column("title", sa.String(length=240), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("slug"),
            sa.UniqueConstraint("title"),
        )

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.String(length=240), nullable=False),
        sa.Column("document_id", sa.String(length=180), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("section_heading", sa.String(length=500), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.document_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_id"),
    )
    op.create_index(op.f("ix_articles_article_id"), "articles", ["article_id"], unique=False)
    op.create_index(op.f("ix_articles_document_id"), "articles", ["document_id"], unique=False)

    op.create_table(
        "pages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.String(length=180), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("original_korean_text", sa.Text(), nullable=False),
        sa.Column("source_text_s3_key", sa.String(length=700), nullable=True),
        sa.Column("source_page_image_s3_key", sa.String(length=700), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.document_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "page_number", name="uq_pages_document_page"),
    )
    op.create_index(op.f("ix_pages_document_id"), "pages", ["document_id"], unique=False)

    op.create_table(
        "topic_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_slug", sa.String(length=160), nullable=False),
        sa.Column("alias", sa.String(length=240), nullable=False),
        sa.Column("normalized_alias", sa.String(length=240), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["topic_slug"], ["topics.slug"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("topic_slug", "alias", name="uq_topic_alias"),
    )
    op.create_index(op.f("ix_topic_aliases_alias"), "topic_aliases", ["alias"], unique=False)
    op.create_index(op.f("ix_topic_aliases_normalized_alias"), "topic_aliases", ["normalized_alias"], unique=False)
    op.create_index(op.f("ix_topic_aliases_topic_slug"), "topic_aliases", ["topic_slug"], unique=False)

    op.create_table(
        "passages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.String(length=260), nullable=False),
        sa.Column("document_id", sa.String(length=180), nullable=False),
        sa.Column("article_id", sa.String(length=240), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("page_numbers", sa.JSON(), nullable=False),
        sa.Column("page_spans", sa.JSON(), nullable=False),
        sa.Column("section_heading", sa.String(length=500), nullable=True),
        sa.Column("original_korean_text", sa.Text(), nullable=False),
        sa.Column("english_summary_optional", sa.Text(), nullable=True),
        sa.Column("body_system_tags", sa.JSON(), nullable=False),
        sa.Column("symptom_tags", sa.JSON(), nullable=False),
        sa.Column("condition_tags", sa.JSON(), nullable=False),
        sa.Column("food_tags", sa.JSON(), nullable=False),
        sa.Column("substance_tags", sa.JSON(), nullable=False),
        sa.Column("habit_tags", sa.JSON(), nullable=False),
        sa.Column("avoid_tags", sa.JSON(), nullable=False),
        sa.Column("recommended_food_tags", sa.JSON(), nullable=False),
        sa.Column("topic_slugs", sa.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("needs_human_review", sa.Boolean(), nullable=False),
        sa.Column("source_pdf_s3_key", sa.String(length=700), nullable=True),
        sa.Column("source_text_s3_key", sa.String(length=700), nullable=True),
        sa.Column("source_page_image_s3_key", sa.String(length=700), nullable=True),
        sa.Column("embedding_id", sa.String(length=260), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.article_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.document_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_id"),
    )
    op.create_index(op.f("ix_passages_article_id"), "passages", ["article_id"], unique=False)
    op.create_index(op.f("ix_passages_chunk_id"), "passages", ["chunk_id"], unique=False)
    op.create_index(op.f("ix_passages_document_id"), "passages", ["document_id"], unique=False)
    op.create_index(op.f("ix_passages_needs_human_review"), "passages", ["needs_human_review"], unique=False)
    op.create_index(op.f("ix_passages_page_end"), "passages", ["page_end"], unique=False)
    op.create_index(op.f("ix_passages_page_start"), "passages", ["page_start"], unique=False)

    op.create_table(
        "passage_topic_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.String(length=260), nullable=False),
        sa.Column("topic_slug", sa.String(length=160), nullable=False),
        sa.Column("matched_alias", sa.String(length=240), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("needs_human_review", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["passages.chunk_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_slug"], ["topics.slug"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_id", "topic_slug", name="uq_passage_topic"),
    )
    op.create_index(op.f("ix_passage_topic_assignments_chunk_id"), "passage_topic_assignments", ["chunk_id"], unique=False)
    op.create_index(op.f("ix_passage_topic_assignments_topic_slug"), "passage_topic_assignments", ["topic_slug"], unique=False)

    op.create_table(
        "retrieval_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(length=80), nullable=False),
        sa.Column("original_query", sa.Text(), nullable=False),
        sa.Column("detected_language", sa.String(length=20), nullable=False),
        sa.Column("matched_topic_slugs", sa.JSON(), nullable=False),
        sa.Column("retrieval_filters", sa.JSON(), nullable=False),
        sa.Column("returned_chunk_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_retrieval_logs_request_id"), "retrieval_logs", ["request_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_retrieval_logs_request_id"), table_name="retrieval_logs")
    op.drop_table("retrieval_logs")
    op.drop_index(op.f("ix_passage_topic_assignments_topic_slug"), table_name="passage_topic_assignments")
    op.drop_index(op.f("ix_passage_topic_assignments_chunk_id"), table_name="passage_topic_assignments")
    op.drop_table("passage_topic_assignments")
    op.drop_index(op.f("ix_passages_page_start"), table_name="passages")
    op.drop_index(op.f("ix_passages_page_end"), table_name="passages")
    op.drop_index(op.f("ix_passages_needs_human_review"), table_name="passages")
    op.drop_index(op.f("ix_passages_document_id"), table_name="passages")
    op.drop_index(op.f("ix_passages_chunk_id"), table_name="passages")
    op.drop_index(op.f("ix_passages_article_id"), table_name="passages")
    op.drop_table("passages")
    op.drop_index(op.f("ix_topic_aliases_topic_slug"), table_name="topic_aliases")
    op.drop_index(op.f("ix_topic_aliases_normalized_alias"), table_name="topic_aliases")
    op.drop_index(op.f("ix_topic_aliases_alias"), table_name="topic_aliases")
    op.drop_table("topic_aliases")
    op.drop_index(op.f("ix_pages_document_id"), table_name="pages")
    op.drop_table("pages")
    op.drop_index(op.f("ix_articles_document_id"), table_name="articles")
    op.drop_index(op.f("ix_articles_article_id"), table_name="articles")
    op.drop_table("articles")
    for table_name in ["habits", "substances", "symptoms", "conditions", "foods", "body_systems"]:
        op.drop_table(table_name)
    op.drop_index(op.f("ix_topics_title"), table_name="topics")
    op.drop_index(op.f("ix_topics_slug"), table_name="topics")
    op.drop_index(op.f("ix_topics_category"), table_name="topics")
    op.drop_table("topics")
    op.drop_index(op.f("ix_documents_filename"), table_name="documents")
    op.drop_index(op.f("ix_documents_document_id"), table_name="documents")
    op.drop_table("documents")

from __future__ import annotations

from typing import Any


FILTER_FIELDS = [
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
]


def passage_index_mapping(*, vector_dimension: int, enable_nori: bool = True) -> dict[str, Any]:
    analyzer_settings = (
        {
            "analysis": {
                "analyzer": {
                    "korean_nori": {
                        "type": "custom",
                        "tokenizer": "nori_tokenizer",
                        "filter": ["lowercase", "nori_part_of_speech"],
                    }
                }
            }
        }
        if enable_nori
        else {
            "analysis": {
                "analyzer": {
                    "korean_fallback": {
                        "type": "standard",
                    }
                }
            }
        }
    )
    text_analyzer = "korean_nori" if enable_nori else "standard"
    return {
        "settings": {
            "index": {"knn": True},
            **analyzer_settings,
        },
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "document_id": {"type": "keyword"},
                "article_id": {"type": "keyword"},
                "title": {"type": "text", "analyzer": text_analyzer, "fields": {"keyword": {"type": "keyword"}}},
                "filename": {"type": "keyword"},
                "section_heading": {"type": "text", "analyzer": text_analyzer, "fields": {"keyword": {"type": "keyword"}}},
                "original_korean_text": {"type": "text", "analyzer": text_analyzer},
                "english_summary_optional": {"type": "text"},
                "topic_slugs": {"type": "keyword"},
                "body_system_slugs": {"type": "keyword"},
                "symptom_slugs": {"type": "keyword"},
                "condition_slugs": {"type": "keyword"},
                "food_slugs": {"type": "keyword"},
                "substance_slugs": {"type": "keyword"},
                "habit_slugs": {"type": "keyword"},
                "avoid_tags": {"type": "keyword"},
                "recommended_food_tags": {"type": "keyword"},
                "page_start": {"type": "integer"},
                "page_end": {"type": "integer"},
                "page_numbers": {"type": "integer"},
                "confidence_score": {"type": "float"},
                "needs_human_review": {"type": "boolean"},
                "source_pdf_s3_key": {"type": "keyword"},
                "source_text_s3_key": {"type": "keyword"},
                "source_page_image_s3_key": {"type": "keyword"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": vector_dimension,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "faiss",
                    },
                },
            }
        },
    }


def document_from_vector_record(record: dict[str, Any]) -> dict[str, Any]:
    chunk = record["chunk"]
    return {
        "chunk_id": chunk.get("chunk_id"),
        "document_id": chunk.get("document_id"),
        "article_id": chunk.get("article_id"),
        "title": chunk.get("title"),
        "filename": chunk.get("filename"),
        "section_heading": chunk.get("section_title") or chunk.get("section_heading"),
        "original_korean_text": chunk.get("original_korean_text") or chunk.get("text"),
        "english_summary_optional": chunk.get("english_summary_optional"),
        "topic_slugs": chunk.get("topic_slugs") or [],
        "body_system_slugs": chunk.get("body_system_slugs") or chunk.get("body_system_tags") or [],
        "symptom_slugs": chunk.get("symptom_slugs") or chunk.get("symptom_tags") or [],
        "condition_slugs": chunk.get("condition_slugs") or chunk.get("condition_tags") or [],
        "food_slugs": chunk.get("food_slugs") or chunk.get("food_tags") or [],
        "substance_slugs": chunk.get("substance_slugs") or chunk.get("substance_tags") or [],
        "habit_slugs": chunk.get("habit_slugs") or chunk.get("habit_tags") or [],
        "avoid_tags": chunk.get("avoid_tags") or [],
        "recommended_food_tags": chunk.get("recommended_food_tags") or [],
        "page_start": chunk.get("page_start"),
        "page_end": chunk.get("page_end"),
        "page_numbers": chunk.get("page_numbers") or [],
        "confidence_score": chunk.get("confidence_score"),
        "needs_human_review": chunk.get("needs_human_review"),
        "source_pdf_s3_key": chunk.get("source_pdf_s3_key") or chunk.get("pdf_s3_key"),
        "source_text_s3_key": chunk.get("source_text_s3_key") or chunk.get("source_s3_key"),
        "source_page_image_s3_key": chunk.get("source_page_image_s3_key"),
        "embedding": record.get("embedding"),
    }

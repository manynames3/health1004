from pathlib import Path

from app import archive
from app.config import Settings
from app.vector_bundle import VectorRecord


ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "data" / "taxonomy.seed.yaml"


def _record(chunk_id: str, text: str, *, substance_slugs: list[str] | None = None) -> VectorRecord:
    return VectorRecord(
        chunk={
            "chunk_id": chunk_id,
            "document_id": f"doc-{chunk_id}",
            "title": f"3탄 건강미인(迷人) {chunk_id}",
            "filename": f"{chunk_id}.pdf",
            "page_start": 1,
            "page_end": 1,
            "page_numbers": [1],
            "page_spans": [{"page_number": 1, "text": text}],
            "section_title": "식품첨가물",
            "language": "ko",
            "text": text,
            "substance_slugs": substance_slugs or [],
            "topic_slugs": substance_slugs or [],
        },
        embedding=[],
        embedding_norm=1.0,
        lexical_tokens=set(),
    )


def test_search_passages_finds_raw_text_outside_existing_tags(monkeypatch):
    settings = Settings(TAXONOMY_SEED_PATH=str(SEED))
    monkeypatch.setattr(
        archive,
        "vector_records_from_storage",
        lambda _settings: [
            _record("caramel", "원문에서는 카라멜색소와 합성착색료 문제를 설명한다."),
            _record("sleep", "수면과 생활습관을 설명한다."),
        ],
    )

    result = archive.search_passages(settings, query="카라멜색소", category="substances", limit=5)

    assert result["total"] >= 1
    assert result["passages"][0].chunk_id == "caramel"
    assert result["fallback_used"] is True


def test_search_passages_uses_category_filter_when_topic_is_tagged(monkeypatch):
    settings = Settings(TAXONOMY_SEED_PATH=str(SEED))
    monkeypatch.setattr(
        archive,
        "vector_records_from_storage",
        lambda _settings: [
            _record("preservative", "방부제와 보존료 설명", substance_slugs=["preservative"]),
            _record("unrelated", "수면과 생활습관을 설명한다."),
        ],
    )

    result = archive.search_passages(settings, query="방부제", category="substances", limit=5)

    assert "preservative" in result["filters_used"]["substance_slugs"]
    assert result["passages"][0].chunk_id == "preservative"

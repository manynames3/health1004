from pathlib import Path

from app.archive import topic_detail
from app.config import Settings
from app.models import QueryResponse, ResolvedQuery
from app.taxonomy import load_taxonomy, resolve_query, tag_passage
from app.vector_bundle import record_matches_filters


ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "data" / "taxonomy.seed.yaml"


def test_taxonomy_seed_loads_required_categories():
    taxonomy = load_taxonomy(SEED)

    assert taxonomy.term("milk").title == "우유"
    assert taxonomy.term("sodium-benzoate").title == "안식향산나트륨"
    assert len(taxonomy.terms_for_category("symptoms")) >= 20


def test_korean_alias_matching_maps_to_canonical_topic():
    taxonomy = load_taxonomy(SEED)
    resolved = resolve_query("혈압이 높고 혈액순환이 걱정돼요", taxonomy)

    assert "고혈압" in resolved["matched_topics"]
    assert "혈액/혈관/대사" in resolved["matched_body_systems"]
    assert "high-blood-pressure" in resolved["retrieval_filters"]["topic_slugs"]


def test_query_resolver_handles_digestive_concern_language():
    taxonomy = load_taxonomy(SEED)
    resolved = resolve_query("속이 안 좋고 소화가 안돼요", taxonomy)

    assert "소화불량" in resolved["matched_topics"]
    assert "위염" in resolved["matched_topics"]
    assert "위장질환" in resolved["matched_topics"]
    assert "소화/장" in resolved["matched_body_systems"]
    assert "indigestion" in resolved["matched_topic_slugs"]


def test_passage_tagging_uses_aliases_before_review_flag():
    taxonomy = load_taxonomy(SEED)
    result = tag_passage(
        text="이 원문에서는 방부제와 안식향산나트륨 같은 보존료 문제를 설명한다.",
        taxonomy=taxonomy,
        min_confidence=0.65,
    )

    assert "preservative" in result["topic_slugs"]
    assert "sodium-benzoate" in result["topic_slugs"]
    assert "food-additives" in result["body_system_slugs"]
    assert result["confidence_score"] >= 0.65
    assert result["needs_human_review"] is False


def test_hybrid_retrieval_filter_construction_matches_chunk_metadata():
    chunk = {
        "topic_slugs": ["milk", "osteoporosis"],
        "food_slugs": ["milk"],
        "condition_slugs": ["osteoporosis-condition"],
    }

    assert record_matches_filters(chunk, {"food_slugs": ["milk"]}) is True
    assert record_matches_filters(chunk, {"substance_slugs": ["msg"]}) is False


def test_topic_page_api_response_shape_without_aws():
    settings = Settings(TAXONOMY_SEED_PATH=str(SEED))
    detail = topic_detail(settings, "milk")

    assert detail.slug == "milk"
    assert detail.title == "우유"
    assert isinstance(detail.source_passages, list)
    assert "의학적 진단" in detail.safety_disclaimer


def test_rag_response_schema_accepts_resolved_query():
    response = QueryResponse(
        answer="원문에서는 우유를 설명합니다.",
        citations=[],
        retrieved_chunks=[],
        language="ko",
        request_id="req",
        resolved_query=ResolvedQuery(
            original_query="우유",
            detected_language="ko",
            matched_topics=["우유"],
            matched_topic_slugs=["milk"],
            retrieval_filters={"topic_slugs": ["milk"]},
        ),
        related_topics=[{"slug": "milk", "title": "우유"}],
    )

    assert response.resolved_query.matched_topic_slugs == ["milk"]
    assert response.related_topics[0]["title"] == "우유"

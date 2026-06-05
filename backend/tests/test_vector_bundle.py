from app.config import Settings
from app.vector_bundle import VectorBundleStore, build_vector_bundle, make_vector_record, parse_vector_bundle


class FakeStorage:
    def __init__(self, payload: bytes):
        self.payload = payload

    def get_bytes(self, key: str) -> bytes:
        assert key == "vector-index/test.json.gz"
        return self.payload


def _chunk(chunk_id: str, title: str, text: str, page: int) -> dict:
    return {
        "chunk_id": chunk_id,
        "document_id": "doc",
        "title": title,
        "filename": f"{chunk_id}.pdf",
        "detected_date": "2026-01-01",
        "page_start": page,
        "page_end": page,
        "page_numbers": [page],
        "page_spans": [{"page_number": page, "text": text, "token_count": 10}],
        "section_title": title,
        "language": "ko",
        "text": text,
        "source_s3_key": f"extracted/{chunk_id}/pages.json",
        "pdf_s3_key": f"raw-pdfs/{chunk_id}.pdf",
        "extraction_method": "embedded_text",
        "token_count": 10,
    }


def test_build_parse_and_search_vector_bundle():
    records = [
        make_vector_record(_chunk("food-additives", "식품첨가물", "보존료와 안식향산나트륨 설명", 3), [1.0, 0.0, 0.0]),
        make_vector_record(_chunk("sleep", "수면", "숙면과 생활습관 설명", 8), [0.0, 1.0, 0.0]),
    ]
    payload = build_vector_bundle(
        records=records,
        embedding_model_id="cohere.embed-multilingual-v3",
        embedding_dimension=3,
        created_at="2026-01-01T00:00:00+00:00",
    )

    parsed = parse_vector_bundle(payload)
    assert parsed.metadata["record_count"] == 2
    assert parsed.records[0].chunk["page_numbers"] == [3]

    settings = Settings(
        AWS_REGION="us-east-1",
        S3_BUCKET="health1004-corpus",
        VECTOR_BUNDLE_KEY="vector-index/test.json.gz",
    )
    store = VectorBundleStore(settings, FakeStorage(payload))
    chunks = store.search(
        query="보존료 안식향산나트륨",
        query_embedding=[1.0, 0.0, 0.0],
        top_k=1,
    )

    assert chunks[0].chunk_id == "food-additives"
    assert chunks[0].page_numbers == [3]
    assert chunks[0].score > 0.9

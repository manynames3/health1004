from app.citations import citation_from_chunk, dedupe_citations, source_ref
from app.models import RetrievedChunk


def _chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="doc:0001:abc",
        document_id="doc",
        title="주간 뉴스레터",
        filename="2024-01-05.pdf",
        detected_date="2024-01-05",
        page_start=3,
        page_end=4,
        page_numbers=[3, 4],
        page_spans=[
            {"page_number": 3, "text": "3쪽 본문입니다. 보존료 설명입니다.", "token_count": 10},
            {"page_number": 4, "text": "4쪽 본문입니다. 안식향산나트륨 설명입니다.", "token_count": 10},
        ],
        section_title="보존료와 안식향산나트륨",
        language="ko",
        text="인용할 본문입니다. " * 40,
        score=0.9,
        pdf_s3_key="raw/2024-01-05.pdf",
    )


def test_citation_from_chunk_trims_quote_and_keeps_traceability():
    citation = citation_from_chunk(_chunk(), pdf_url="https://example.com/pdf")

    assert citation.document_id == "doc"
    assert citation.chunk_id == "doc:0001:abc"
    assert citation.page_start == 3
    assert citation.page_end == 4
    assert citation.page_numbers == [3, 4]
    assert citation.page_quotes[0]["page_number"] == 3
    assert citation.section_title == "보존료와 안식향산나트륨"
    assert citation.pdf_url == "https://example.com/pdf"
    assert "p. 3:" in citation.quote


def test_source_ref_mentions_filename_pages_and_chunk():
    ref = source_ref(_chunk())

    assert "2024-01-05.pdf" in ref
    assert "pp. 3-4" in ref
    assert "doc:0001:abc" in ref


def test_dedupe_citations():
    citation = citation_from_chunk(_chunk())
    assert len(dedupe_citations([citation, citation])) == 1

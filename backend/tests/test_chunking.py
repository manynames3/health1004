from app.chunking import PageText, chunk_pages


def test_chunk_pages_preserves_page_ranges_and_korean_text():
    pages = [
        PageText(1, "첫 번째 문단입니다. 건강에 대한 설명입니다.\n\n두 번째 문단입니다."),
        PageText(2, "다음 페이지의 내용입니다. 문장 경계를 유지합니다."),
    ]
    chunks = chunk_pages(
        pages,
        document_id="doc1",
        filename="weekly.pdf",
        title="Weekly",
        detected_date="2024-01-05",
        source_s3_key="extracted/doc1.json",
        pdf_s3_key="raw/doc1.pdf",
        extraction_method="embedded_text",
        target_tokens=30,
        overlap_tokens=5,
        min_tokens=10,
    )

    assert chunks
    assert chunks[0].page_start == 1
    assert chunks[-1].page_end == 2
    assert chunks[-1].page_numbers
    assert chunks[-1].page_spans
    assert "건강" in "\n".join(chunk.text for chunk in chunks)


def test_chunk_pages_repairs_korean_pdf_soft_line_breaks():
    pages = [
        PageText(
            4,
            "오늘은 첨가물의 유해가능성의 대명사라고 할 수 있는 보존료\n의 문제점에 대해알아보고자 합니다.",
        )
    ]
    chunks = chunk_pages(
        pages,
        document_id="doc1",
        filename="weekly.pdf",
        title="Weekly",
        detected_date=None,
        source_s3_key="extracted/doc1.json",
        pdf_s3_key="raw/doc1.pdf",
        extraction_method="embedded_text",
        target_tokens=100,
        overlap_tokens=10,
        min_tokens=5,
    )

    assert "보존료의 문제점" in chunks[0].text
    assert chunks[0].page_spans[0]["page_number"] == 4


def test_chunk_pages_rejects_bad_overlap():
    try:
        chunk_pages(
            [PageText(1, "내용입니다.")],
            document_id="doc",
            filename="a.pdf",
            title="A",
            detected_date=None,
            source_s3_key="source",
            pdf_s3_key="pdf",
            extraction_method="embedded_text",
            target_tokens=10,
            overlap_tokens=10,
        )
    except ValueError as exc:
        assert "target_tokens" in str(exc)
    else:
        raise AssertionError("Expected ValueError")

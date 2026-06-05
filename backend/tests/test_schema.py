from app.models import Citation, QueryResponse, RetrievedChunk


def test_query_response_schema_round_trip():
    chunk = RetrievedChunk(
        chunk_id="chunk",
        document_id="doc",
        title="Title",
        filename="file.pdf",
        page_start=1,
        page_end=1,
        language="en",
        text="Source text",
        score=1.0,
    )
    response = QueryResponse(
        answer="Answer",
        citations=[
            Citation(
                document_id="doc",
                chunk_id="chunk",
                title="Title",
                filename="file.pdf",
                page_start=1,
                page_end=1,
                quote="Source text",
            )
        ],
        retrieved_chunks=[chunk],
        language="en",
        request_id="req",
    )

    assert response.model_dump()["citations"][0]["filename"] == "file.pdf"
    assert response.model_dump()["retrieved_chunks"][0]["chunk_id"] == "chunk"

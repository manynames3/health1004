from app import main
from app.models import DocumentSummary


def test_document_list_payload_backfills_lesson_number_from_filename():
    payload = main.document_list_payload(
        {
            "document_id": "doc-42",
            "title": "3탄 건강미인(迷人) 42 암예방과 치유 24(혈관오염 6)",
            "filename": "3탄 건강미인(迷人) 42 암예방과 치유 24(혈관오염 6).pdf",
        }
    )

    assert payload["lesson_number"] == "42"


def test_document_archive_sort_key_orders_numbered_documents_first():
    docs = [
        DocumentSummary(
            document_id="special",
            title="3탄-건강미인(迷人)-종합편-7(혈관오염)",
            filename="3탄-건강미인(迷人)-종합편-7(혈관오염).pdf",
        ),
        DocumentSummary(
            document_id="doc-42",
            title="3탄 건강미인(迷人) 42 암예방과 치유 24(혈관오염 6)",
            filename="3탄 건강미인(迷人) 42 암예방과 치유 24(혈관오염 6).pdf",
        ),
        DocumentSummary(
            document_id="doc-1",
            title="3탄-건강미인(迷人)-1-시작",
            filename="3탄-건강미인(迷人)-1-시작.pdf",
        ),
    ]

    ordered = sorted(docs, key=main.document_archive_sort_key)

    assert [doc.document_id for doc in ordered] == ["doc-1", "doc-42", "special"]

from app.extraction import (
    detect_title_date,
    extraction_quality,
    normalize_korean_pdf_text,
    normalize_whitespace,
    should_use_ocr,
)


def test_should_use_ocr_for_empty_or_short_pages():
    assert should_use_ocr(["", "   "])


def test_should_not_use_ocr_for_good_korean_text():
    text = "건강과 생활 습관에 대한 설명입니다. " * 30
    assert not should_use_ocr([text])


def test_detect_title_date_from_filename():
    title, detected_date = detect_title_date("newsletter_2024-03-08_weekly.pdf")
    assert detected_date == "2024-03-08"
    assert "newsletter" in title


def test_normalize_whitespace_preserves_paragraphs():
    assert normalize_whitespace("가  \n\n\n 나") == "가\n\n나"


def test_normalize_korean_pdf_text_removes_page_number_and_joins_soft_wraps():
    text = "- 3 -\n보리차 등을 실온에 방치하\n면 얼마 가지 못해 상하게 됩니다.\n<제목>\n짧은 줄"
    normalized = normalize_korean_pdf_text(text)

    assert "- 3 -" not in normalized
    assert "방치하면" in normalized
    assert "<제목>" in normalized


def test_normalize_korean_pdf_text_keeps_space_for_word_boundary_wrap():
    text = "미생물들의 활동을 억제함으로써 이들의 생육을\n막아주기 때문에 장기간 상하지 않습니다."
    normalized = normalize_korean_pdf_text(text)

    assert "생육을 막아주기" in normalized


def test_extraction_quality_reports_flags():
    quality = extraction_quality(["", "짧음"])

    assert quality["should_use_ocr"]
    assert "low_text_pages" in quality["flags"]

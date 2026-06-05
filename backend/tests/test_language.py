from app.language import detect_language


def test_detect_korean():
    assert detect_language("안녕하세요. 건강 관련 문서 검색입니다.") == "ko"


def test_detect_english():
    assert detect_language("What does the document say about sleep?") == "en"


def test_detect_mixed():
    assert detect_language("비타민 C and sleep quality") == "mixed"

import re

from app.models import LanguageCode

HANGUL_RE = re.compile(r"[\uac00-\ud7a3]")
LATIN_RE = re.compile(r"[A-Za-z]")


def detect_language(text: str) -> LanguageCode:
    compact = re.sub(r"\s+", "", text or "")
    if not compact:
        return "unknown"

    hangul_count = len(HANGUL_RE.findall(compact))
    latin_count = len(LATIN_RE.findall(compact))
    total_letters = hangul_count + latin_count
    if total_letters == 0:
        return "unknown"

    hangul_ratio = hangul_count / total_letters
    latin_ratio = latin_count / total_letters
    if hangul_count and latin_count and min(hangul_ratio, latin_ratio) >= 0.12:
        return "mixed"
    if hangul_ratio >= 0.65:
        return "ko"
    if latin_ratio >= 0.65:
        return "en"
    return "mixed"


def language_name(language: LanguageCode) -> str:
    return {
        "ko": "Korean",
        "en": "English",
        "mixed": "the same language as the user",
        "unknown": "the same language as the user",
    }[language]

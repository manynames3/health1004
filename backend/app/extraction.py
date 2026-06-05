import re
import unicodedata
from pathlib import Path
from typing import Any, Optional

from app.language import detect_language


DATE_PATTERNS = [
    re.compile(r"(?P<year>20\d{2})[-_. ](?P<month>\d{1,2})[-_. ](?P<day>\d{1,2})"),
    re.compile(r"(?P<year>20\d{2})(?P<month>\d{2})(?P<day>\d{2})"),
    re.compile(r"(?P<year>20\d{2})년\s*(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일"),
]
HEALTH1004_EPISODE_RE = re.compile(
    r"3\s*탄\s*[-_\s]*건강미인\s*[\(\[（]?\s*迷人\s*[\)\]）]?\s*[-_\s]*(?P<episode>\d{1,3})(?!\d)"
)

PAGE_NUMBER_RE = re.compile(r"^-+\s*\d+\s*-+$")
HEADER_ISSUE_RE = re.compile(
    r"(건강미인|바르게\s*알고\s*먹자|思行習慣|사행습관|식품화학첨가물|<\d+[-–])"
)
HEADING_RE = re.compile(r"^(<[^>]{2,120}>|\d+\)\s+.+|\d+\.\s+.+|[가-힣A-Za-z0-9()·,\s]{2,80}:)$")
LIST_RE = re.compile(r"^([\-•Ÿ*]|[0-9]+[.)])\s+")
TABLE_LABEL_RE = re.compile(
    r"^(항목|기능|사용식품|부작용|종류|사용가능식품|첨가허용량|원재료|주의사항)$"
)
KOREAN_RE = re.compile(r"[\uac00-\ud7a3]")
KOREAN_CONTINUATION_RE = re.compile(
    r"^(면|며|고|게|기|는|은|이|가|을|를|의|에|에서|으로|로|와|과|도|만|부터|까지|"
    r"는데|지만|어서|아서|도록|라고|하고|한다|된다|입니다|합니다)"
)


def normalize_whitespace(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t\f\v]+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_korean_pdf_text(text: str) -> str:
    """Repair common Korean PDF extraction artifacts while preserving headings.

    Korean PDFs often break a word or eojeol across visual lines. This normalizer
    removes page-number footers and joins long soft-wrapped body lines before
    chunking, while keeping short centered headings and list/table rows separate.
    """
    lines = _clean_pdf_lines(text)
    paragraphs: list[str] = []
    current = ""
    previous_raw = ""

    def flush() -> None:
        nonlocal current, previous_raw
        if current.strip():
            paragraphs.append(normalize_whitespace(current))
        current = ""
        previous_raw = ""

    for line in lines:
        if not line:
            flush()
            continue
        if _is_standalone_line(line):
            flush()
            paragraphs.append(line)
            continue
        if not current:
            current = line
            previous_raw = line
            continue

        if _should_soft_join(previous_raw, line):
            current = f"{current}{_joiner(previous_raw, line)}{line}"
        elif _ends_sentence(previous_raw):
            flush()
            current = line
        else:
            current = f"{current} {line}"
        previous_raw = line

    flush()
    return "\n\n".join(paragraphs)


def extraction_quality(page_texts: list[str], min_chars_per_page: int = 80) -> dict[str, Any]:
    normalized_pages = [normalize_whitespace(text) for text in page_texts]
    page_char_counts = [len(text) for text in normalized_pages]
    combined = "\n".join(normalized_pages)
    hangul_chars = len(KOREAN_RE.findall(combined))
    total_chars = sum(page_char_counts)
    avg_chars = total_chars / max(len(normalized_pages), 1)
    low_text_pages = [
        index + 1 for index, char_count in enumerate(page_char_counts) if char_count < min_chars_per_page
    ]
    score = garbled_score(combined)
    language = detect_language(combined)
    flags: list[str] = []
    if low_text_pages:
        flags.append("low_text_pages")
    if score >= 0.18:
        flags.append("garbled_text")
    if language == "unknown" and total_chars < 1000:
        flags.append("weak_language_signal")
    if hangul_chars == 0 and total_chars:
        flags.append("no_hangul_detected")

    return {
        "page_count": len(normalized_pages),
        "total_chars": total_chars,
        "avg_chars_per_page": round(avg_chars, 2),
        "page_char_counts": page_char_counts,
        "low_text_pages": low_text_pages,
        "hangul_chars": hangul_chars,
        "language": language,
        "garbled_score": round(score, 4),
        "flags": flags,
        "should_use_ocr": bool(flags),
    }


def printable_ratio(text: str) -> float:
    if not text:
        return 0.0
    printable = sum(1 for char in text if char.isprintable() or char.isspace())
    return printable / len(text)


def garbled_score(text: str) -> float:
    if not text:
        return 1.0
    replacement_chars = text.count("\ufffd")
    odd_symbols = len(re.findall(r"[□�■◆◇●○※]{2,}", text))
    compact_len = max(len(re.sub(r"\s+", "", text)), 1)
    low_printable = max(0.0, 0.95 - printable_ratio(text))
    return min(1.0, (replacement_chars + odd_symbols) / compact_len + low_printable)


def should_use_ocr(page_texts: list[str], min_chars_per_page: int = 80) -> bool:
    if not page_texts:
        return True
    return extraction_quality(page_texts, min_chars_per_page=min_chars_per_page)["should_use_ocr"]


def detect_title_date(filename: str, first_page_text: str = "") -> tuple[str, Optional[str]]:
    stem = Path(filename).stem
    haystack = f"{stem}\n{first_page_text[:1000]}"
    detected_date = None
    for pattern in DATE_PATTERNS:
        match = pattern.search(haystack)
        if match:
            year = int(match.group("year"))
            month = int(match.group("month"))
            day = int(match.group("day"))
            if 1 <= month <= 12 and 1 <= day <= 31:
                detected_date = f"{year:04d}-{month:02d}-{day:02d}"
                break

    title = re.sub(r"[_-]+", " ", stem)
    title = re.sub(r"\b20\d{2}[-_. ]?\d{1,2}[-_. ]?\d{1,2}\b", "", title)
    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        first_nonempty = next(
            (line.strip() for line in first_page_text.splitlines() if line.strip()), ""
        )
        title = first_nonempty[:120] if first_nonempty else stem
    return title, detected_date


def detect_health1004_episode_number(*values: Optional[str]) -> Optional[int]:
    for value in values:
        if not value:
            continue
        normalized = unicodedata.normalize("NFC", str(value))
        if normalized.strip().isdigit():
            episode = int(normalized.strip())
            if 1 <= episode <= 365:
                return episode
        match = HEALTH1004_EPISODE_RE.search(normalized)
        if not match:
            continue
        episode = int(match.group("episode"))
        if 1 <= episode <= 365:
            return episode
    return None


def infer_section_title(text: str, fallback: str) -> str:
    for line in normalize_whitespace(text).splitlines():
        candidate = line.strip()
        if not candidate or PAGE_NUMBER_RE.match(candidate):
            continue
        if HEADER_ISSUE_RE.search(candidate) or candidate.startswith("<"):
            return candidate[:160]
    for line in normalize_whitespace(text).splitlines():
        candidate = line.strip()
        if 3 <= len(candidate) <= 120:
            return candidate
    return fallback


def is_section_heading(text: str) -> bool:
    line = normalize_whitespace(text).splitlines()[0].strip() if normalize_whitespace(text) else ""
    if not line:
        return False
    return bool(HEADER_ISSUE_RE.search(line) or line.startswith("<") or re.match(r"^\d+\)\s+", line))


def _clean_pdf_lines(text: str) -> list[str]:
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for raw_line in normalized.split("\n"):
        line = re.sub(r"[\t\f\v]+", " ", raw_line)
        line = re.sub(r"[ ]{2,}", " ", line).strip()
        if PAGE_NUMBER_RE.match(line):
            continue
        lines.append(line)
    return lines


def _is_standalone_line(line: str) -> bool:
    return bool(
        HEADING_RE.match(line)
        or LIST_RE.match(line)
        or TABLE_LABEL_RE.match(line)
        or HEADER_ISSUE_RE.search(line)
    )


def _ends_sentence(line: str) -> bool:
    return bool(re.search(r"([.!?。！？]|[\"'”’>)]|습니다|합니다|됩니다|입니다|이었다|하였다|한다|된다|했다)\s*$", line))


def _should_soft_join(previous: str, current: str) -> bool:
    if not previous or not current:
        return False
    if _is_standalone_line(previous) or _is_standalone_line(current):
        return False
    if _ends_sentence(previous):
        return False
    previous_compact_len = len(re.sub(r"\s+", "", previous))
    if previous_compact_len >= 28:
        return True
    return bool(KOREAN_RE.search(previous[-1:]) and KOREAN_CONTINUATION_RE.match(current))


def _joiner(previous: str, current: str) -> str:
    if KOREAN_RE.search(previous[-1:]) and KOREAN_CONTINUATION_RE.match(current):
        return ""
    return " "

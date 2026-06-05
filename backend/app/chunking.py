from dataclasses import asdict, dataclass
import hashlib
import re
from typing import Iterable, Optional

from app.extraction import (
    infer_section_title,
    is_section_heading,
    normalize_korean_pdf_text,
    normalize_whitespace,
)
from app.language import detect_language


PUNCTUATION_SENTENCE_RE = re.compile(r"(?<=[.!?。！？])\s+")
KOREAN_ENDING_RE = re.compile(r"(?<=[다요죠까네음])\s+")


@dataclass
class PageText:
    page_number: int
    text: str


@dataclass
class TextPart:
    page_number: int
    text: str


@dataclass
class TextChunk:
    chunk_id: str
    document_id: str
    filename: str
    title: str
    detected_date: Optional[str]
    page_start: int
    page_end: int
    page_numbers: list[int]
    page_spans: list[dict]
    section_title: str
    language: str
    text: str
    source_s3_key: str
    pdf_s3_key: str
    extraction_method: str
    token_count: int

    def to_dict(self) -> dict:
        return asdict(self)


def estimate_token_count(text: str) -> int:
    if not text:
        return 0
    korean_runs = re.findall(r"[\uac00-\ud7a3]+", text)
    korean_chars = sum(len(run) for run in korean_runs)
    latin_words = re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text)
    symbols = re.findall(r"[^\sA-Za-z0-9\uac00-\ud7a3]", text)
    # Korean tends to carry more semantic material per whitespace unit; character-based
    # approximation avoids producing chunks that are too large when Korean text has few spaces.
    return max(1, int(korean_chars / 2.2) + len(latin_words) + int(len(symbols) / 3))


def split_sentences(text: str) -> list[str]:
    text = normalize_whitespace(text)
    if not text:
        return []
    pieces = PUNCTUATION_SENTENCE_RE.split(text)
    if len(pieces) == 1:
        pieces = KOREAN_ENDING_RE.split(text)
    return [piece.strip() for piece in pieces if piece.strip()]


def _paragraphs(pages: Iterable[PageText]) -> list[TextPart]:
    result: list[TextPart] = []
    for page in pages:
        page_text = normalize_korean_pdf_text(page.text)
        for paragraph in re.split(r"\n\s*\n", page_text):
            paragraph = paragraph.strip()
            if paragraph:
                result.append(TextPart(page.page_number, paragraph))
    return result


def _tail_overlap(parts: list[TextPart], overlap_tokens: int) -> list[TextPart]:
    if not parts:
        return []
    tail: list[TextPart] = []
    running = 0
    for part in reversed(parts):
        running += estimate_token_count(part.text)
        tail.insert(0, part)
        if running >= overlap_tokens:
            break
    return tail


def _chunk_id(document_id: str, chunk_index: int, text: str) -> str:
    digest = hashlib.sha256(f"{document_id}:{chunk_index}:{text}".encode("utf-8")).hexdigest()
    return f"{document_id}:{chunk_index:04d}:{digest[:12]}"


def chunk_pages(
    pages: list[PageText],
    *,
    document_id: str,
    filename: str,
    title: str,
    detected_date: Optional[str],
    source_s3_key: str,
    pdf_s3_key: str,
    extraction_method: str,
    target_tokens: int = 700,
    overlap_tokens: int = 120,
    min_tokens: int = 250,
) -> list[TextChunk]:
    if target_tokens <= overlap_tokens:
        raise ValueError("target_tokens must be larger than overlap_tokens")

    chunks: list[TextChunk] = []
    current_parts: list[TextPart] = []
    current_tokens = 0
    current_is_overlap = False

    def make_chunk(parts: list[TextPart], chunk_index: int) -> TextChunk:
        chunk_text = normalize_whitespace("\n\n".join(part.text for part in parts))
        page_numbers = sorted({part.page_number for part in parts})
        page_spans = _page_spans(parts)
        section_title = infer_section_title(chunk_text, title)
        return TextChunk(
            chunk_id=_chunk_id(document_id, chunk_index, chunk_text),
            document_id=document_id,
            filename=filename,
            title=title,
            detected_date=detected_date,
            page_start=min(page_numbers),
            page_end=max(page_numbers),
            page_numbers=page_numbers,
            page_spans=page_spans,
            section_title=section_title,
            language=detect_language(chunk_text),
            text=chunk_text,
            source_s3_key=source_s3_key,
            pdf_s3_key=pdf_s3_key,
            extraction_method=extraction_method,
            token_count=estimate_token_count(chunk_text),
        )

    def flush(*, keep_overlap: bool = True) -> None:
        nonlocal current_parts, current_tokens, current_is_overlap
        if not current_parts:
            return
        chunk_text = normalize_whitespace("\n\n".join(part.text for part in current_parts))
        if not chunk_text:
            current_parts = []
            current_tokens = 0
            return
        chunks.append(make_chunk(current_parts, len(chunks)))
        current_parts = _tail_overlap(current_parts, overlap_tokens) if keep_overlap else []
        current_tokens = sum(estimate_token_count(part.text) for part in current_parts)
        current_is_overlap = bool(current_parts)

    for part in _paragraphs(pages):
        if current_parts and is_section_heading(part.text):
            if current_tokens >= min_tokens:
                flush(keep_overlap=False)
            elif current_is_overlap:
                current_parts = []
                current_tokens = 0
                current_is_overlap = False
        sentence_buffer: list[str] = []
        for sentence in split_sentences(part.text):
            sentence_tokens = estimate_token_count(sentence)
            if sentence_tokens > target_tokens:
                if sentence_buffer:
                    combined = " ".join(sentence_buffer)
                    current_parts.append(TextPart(part.page_number, combined))
                    current_is_overlap = False
                    current_tokens += estimate_token_count(combined)
                    sentence_buffer = []
                for hard_part in _split_long_sentence(sentence, target_tokens):
                    current_parts.append(TextPart(part.page_number, hard_part))
                    current_is_overlap = False
                    current_tokens += estimate_token_count(hard_part)
                    flush()
                continue

            if sentence_buffer and estimate_token_count(" ".join(sentence_buffer)) + sentence_tokens > target_tokens:
                combined = " ".join(sentence_buffer)
                current_parts.append(TextPart(part.page_number, combined))
                current_is_overlap = False
                current_tokens += estimate_token_count(combined)
                sentence_buffer = []

            sentence_buffer.append(sentence)

        if sentence_buffer:
            paragraph_text = " ".join(sentence_buffer)
            paragraph_tokens = estimate_token_count(paragraph_text)
            if current_tokens + paragraph_tokens > target_tokens and current_tokens >= min_tokens:
                flush()
            current_parts.append(TextPart(part.page_number, paragraph_text))
            current_is_overlap = False
            current_tokens += paragraph_tokens
            if current_tokens >= target_tokens:
                flush()

    if current_parts:
        if chunks and current_tokens < min_tokens:
            previous = chunks.pop()
            merged_parts = _parts_from_chunk(previous) + current_parts
            chunks.append(make_chunk(merged_parts, len(chunks)))
        else:
            flush()
    return chunks


def _split_long_sentence(sentence: str, target_tokens: int) -> list[str]:
    words = sentence.split()
    if len(words) <= 1:
        approx_chars = max(400, target_tokens * 3)
        return [sentence[index : index + approx_chars].strip() for index in range(0, len(sentence), approx_chars)]

    parts: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if current and estimate_token_count(candidate) > target_tokens:
            parts.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        parts.append(" ".join(current))
    return parts


def _page_spans(parts: list[TextPart]) -> list[dict]:
    by_page: dict[int, list[str]] = {}
    for part in parts:
        by_page.setdefault(part.page_number, []).append(part.text)
    return [
        {
            "page_number": page_number,
            "text": normalize_whitespace("\n\n".join(texts)),
            "token_count": estimate_token_count("\n\n".join(texts)),
        }
        for page_number, texts in sorted(by_page.items())
    ]


def _parts_from_chunk(chunk: TextChunk) -> list[TextPart]:
    if chunk.page_spans:
        return [
            TextPart(page_number=int(span["page_number"]), text=str(span["text"]))
            for span in chunk.page_spans
        ]
    return [TextPart(page_number=chunk.page_start, text=chunk.text)]

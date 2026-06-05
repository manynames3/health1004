from app.models import Citation, RetrievedChunk


def excerpt(text: str, max_chars: int = 320) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "…"


def citation_from_chunk(chunk: RetrievedChunk, pdf_url: str | None = None) -> Citation:
    page_quotes = page_quotes_from_chunk(chunk)
    page_numbers = chunk.page_numbers or [chunk.page_start]
    return Citation(
        document_id=chunk.document_id,
        chunk_id=chunk.chunk_id,
        title=chunk.title,
        filename=chunk.filename,
        detected_date=chunk.detected_date,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        page_numbers=page_numbers,
        page_quotes=page_quotes,
        section_title=chunk.section_title,
        quote=combined_page_quote(page_quotes) if page_quotes else excerpt(chunk.text),
        pdf_url=pdf_url,
        source_page_image_s3_key=chunk.source_page_image_s3_key,
    )


def dedupe_citations(citations: list[Citation]) -> list[Citation]:
    seen: set[tuple[str, str, int, int]] = set()
    result: list[Citation] = []
    for citation in citations:
        key = (
            citation.document_id,
            citation.chunk_id,
            citation.page_start,
            citation.page_end,
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(citation)
    return result


def source_ref(chunk: RetrievedChunk) -> str:
    date = f", {chunk.detected_date}" if chunk.detected_date else ""
    page_numbers = chunk.page_numbers or list(range(chunk.page_start, chunk.page_end + 1))
    pages = format_pages(page_numbers)
    section = f", section: {chunk.section_title}" if chunk.section_title else ""
    return f"{chunk.title} ({chunk.filename}{date}, {pages}{section}, chunk {chunk.chunk_id})"


def page_quotes_from_chunk(chunk: RetrievedChunk, max_chars_per_page: int = 180) -> list[dict]:
    if not chunk.page_spans:
        return [
            {
                "page_number": chunk.page_start,
                "quote": excerpt(chunk.text, max_chars=max_chars_per_page),
            }
        ]
    return [
        {
            "page_number": int(span.get("page_number", chunk.page_start)),
            "quote": excerpt(str(span.get("text", "")), max_chars=max_chars_per_page),
        }
        for span in chunk.page_spans
        if str(span.get("text", "")).strip()
    ]


def combined_page_quote(page_quotes: list[dict]) -> str:
    return " ".join(f"p. {item['page_number']}: {item['quote']}" for item in page_quotes)


def format_pages(page_numbers: list[int]) -> str:
    if not page_numbers:
        return "p. unknown"
    pages = sorted(set(page_numbers))
    ranges: list[str] = []
    start = previous = pages[0]
    for page in pages[1:]:
        if page == previous + 1:
            previous = page
            continue
        ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
        start = previous = page
    ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
    prefix = "p." if len(ranges) == 1 and "-" not in ranges[0] else "pp."
    return f"{prefix} {', '.join(ranges)}"

from app.citations import source_ref
from app.language import language_name
from app.models import LanguageCode, RetrievedChunk


SYSTEM_PROMPT = """You are a careful Korean/English research assistant for a private corpus of natural health practitioner PDF newsletters.
Use only the retrieved context. Do not invent facts. If the answer is not supported by the retrieved documents, say so.
Always cite sources using the provided citation metadata. This is educational document search, not medical advice.
Do not diagnose, prescribe, or recommend treatment plans. When the user asks a health-related question, summarize what the documents say and encourage consulting a qualified professional for personal medical decisions."""


def build_context(chunks: list[RetrievedChunk]) -> str:
    sections = []
    for index, chunk in enumerate(chunks, start=1):
        sections.append(
            "\n".join(
                [
                    f"[SOURCE {index}]",
                    f"chunk_id: {chunk.chunk_id}",
                    f"document_id: {chunk.document_id}",
                    f"title: {chunk.title}",
                    f"filename: {chunk.filename}",
                    f"date: {chunk.detected_date or 'unknown'}",
                    f"pages: {chunk.page_numbers or list(range(chunk.page_start, chunk.page_end + 1))}",
                    f"section_title: {chunk.section_title or chunk.title}",
                    f"reference: {source_ref(chunk)}",
                    "text:",
                    _page_scoped_text(chunk),
                    f"[/SOURCE {index}]",
                ]
            )
        )
    return "\n\n".join(sections)


def _page_scoped_text(chunk: RetrievedChunk) -> str:
    if not chunk.page_spans:
        return chunk.text
    return "\n".join(
        f"[page {span.get('page_number')}]\n{span.get('text', '')}" for span in chunk.page_spans
    )


def build_user_prompt(question: str, chunks: list[RetrievedChunk], language: LanguageCode) -> str:
    target_language = language_name(language)
    return f"""Answer in {target_language} unless the user explicitly requested another language.

Grounding rules:
- Use only the retrieved context below.
- Cite every factual claim with source metadata, including title, filename, page number, and chunk id.
- If the context is insufficient, say that the corpus does not contain enough information.
- Avoid diagnosis, treatment instructions, medication advice, or claims beyond the documents.
- Include a brief medical-safety note when the question relates to personal health decisions.

Retrieved context:
{build_context(chunks)}

User question:
{question}
"""

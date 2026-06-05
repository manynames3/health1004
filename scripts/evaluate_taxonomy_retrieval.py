#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.bedrock import BedrockRuntime
from app.citations import citation_from_chunk, format_pages
from app.config import get_settings
from app.s3_store import S3Storage
from app.taxonomy import load_taxonomy, resolve_query
from app.vector_bundle import VectorBundleStore


DEFAULT_QUESTIONS = [
    "우유와 골다공증에 대해 뭐라고 하나요?",
    "대장암과 고기 섭취의 관계를 찾아줘.",
    "방부제에 대해 나온 자료를 정리해줘.",
    "안식향산나트륨은 어디에 나오나요?",
    "양파의 효능에 대해 찾아줘.",
    "마늘에 대해 설명한 글을 찾아줘.",
    "항생제와 고기 관련 내용을 찾아줘.",
    "탄산음료와 칼슘/인 비율 관련 내용을 찾아줘.",
    "식품첨가물 중 피하라고 하는 것들을 보여줘.",
    "변비와 섬유질 관련 내용을 찾아줘.",
    "공장식 축산에 대한 내용을 찾아줘.",
    "착색료와 알레르기 관련 내용을 찾아줘.",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate taxonomy-first Korean retrieval.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--questions-file", help="Optional UTF-8 file with one question per line")
    parser.add_argument("--max-chars", type=int, default=520)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()
    settings.require_aws_runtime()
    taxonomy = load_taxonomy(settings.taxonomy_seed_path)
    storage = S3Storage(settings)
    vector_settings = settings.model_copy(update={"vector_bundle_key": settings.taxonomy_vector_bundle_key})
    if storage.get_bytes(settings.taxonomy_vector_bundle_key) is None:
        vector_settings = settings
    vector_store = VectorBundleStore(vector_settings, storage)
    bedrock = BedrockRuntime(settings)

    for index, question in enumerate(load_questions(args.questions_file), start=1):
        resolved = resolve_query(question, taxonomy)
        query_embedding = bedrock.embed_texts([question], input_type="search_query")[0]
        chunks = vector_store.search(
            query=question,
            query_embedding=query_embedding,
            top_k=args.top_k,
            filters=resolved["retrieval_filters"],
            expanded_aliases=resolved["expanded_aliases"],
            use_hybrid=settings.opensearch_use_hybrid,
        )
        citations = [citation_from_chunk(chunk, pdf_url=storage.presign_pdf(chunk.pdf_s3_key or chunk.source_pdf_s3_key)) for chunk in chunks]
        print("=" * 100)
        print(f"[Q{index}] {question}")
        print("resolved topics:", ", ".join(resolved["matched_topics"]) or "(none)")
        print("filters used:", json.dumps(resolved["retrieval_filters"], ensure_ascii=False))
        print("expanded aliases:", ", ".join(resolved["expanded_aliases"][:12]) or "(none)")
        print(f"citations returned: {bool(citations)} count={len(citations)}")
        print("-" * 100)
        for rank, chunk in enumerate(chunks, start=1):
            pages = format_pages(chunk.page_numbers or list(range(chunk.page_start, chunk.page_end + 1)))
            print(f"[{rank}] score={chunk.score:.4f} {pages} citations={rank <= len(citations)}")
            print(f"    source={chunk.filename} :: {chunk.section_title or chunk.title}")
            print(f"    document_id={chunk.document_id} chunk_id={chunk.chunk_id}")
            print(f"    topics={', '.join(chunk.topic_slugs[:8])}")
            print("    passage:")
            print(indent(chunk.text[: args.max_chars]))
            if len(chunk.text) > args.max_chars:
                print("    ...")
            print()
    return 0


def load_questions(path: str | None) -> list[str]:
    if not path:
        return DEFAULT_QUESTIONS
    questions = [
        line.strip()
        for line in Path(path).expanduser().read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not questions:
        raise SystemExit(f"No questions found in {path}")
    return questions


def indent(text: str) -> str:
    return "\n".join(f"    {line}" for line in text.splitlines())


if __name__ == "__main__":
    raise SystemExit(main())

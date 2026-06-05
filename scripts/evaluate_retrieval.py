#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.bedrock import BedrockRuntime
from app.citations import format_pages
from app.config import get_settings
from app.language import detect_language
from app.logging_config import configure_logging
from app.opensearch_client import make_opensearch_client, search_chunks


DEFAULT_QUESTIONS = [
    "식품화학첨가물 중 보존료가 왜 문제가 된다고 설명하나요?",
    "안식향산나트륨은 어떤 식품에 사용될 수 있다고 나오나요?",
    "무방부제 표시의 한계에 대해 문서에서는 어떻게 설명하나요?",
    "수입 밀가루와 포스트하비스트에 대해 어떤 우려를 말하나요?",
    "고온살균이나 고온충전 음료 포장의 문제점은 무엇인가요?",
    "천연착향료와 천연색소가 항상 안전하다고 볼 수 없는 이유는 무엇인가요?",
    "인산염이 뼈와 치아 건강에 미치는 영향은 무엇이라고 설명하나요?",
    "탄산음료 섭취와 아이들의 건강 위험에 대해 어떤 내용이 있나요?",
    "코치닐 색소의 원재료와 제조 과정은 어떻게 설명되나요?",
    "천연첨가물 제품보다 자연식품을 권하는 이유는 무엇인가요?",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Korean retrieval smoke tests and print chunks before optional answer generation."
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--questions-file", help="Optional UTF-8 text file with one Korean question per line")
    parser.add_argument("--generate", action="store_true", help="Generate answers after printing retrieved chunks")
    parser.add_argument("--no-hybrid", action="store_true", help="Disable keyword/BM25 hybrid retrieval")
    parser.add_argument("--max-chars", type=int, default=700, help="Max characters to print per chunk")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.require_aws_runtime()
    if args.generate:
        settings.require_chat_model()

    questions = load_questions(args.questions_file)
    bedrock = BedrockRuntime(settings)
    os_client = make_opensearch_client(settings)

    for index, question in enumerate(questions, start=1):
        language = detect_language(question)
        query_embedding = bedrock.embed_texts([question], input_type="search_query")[0]
        chunks = search_chunks(
            os_client,
            index_name=settings.opensearch_index,
            query=question,
            query_embedding=query_embedding,
            top_k=args.top_k,
            use_hybrid=not args.no_hybrid,
        )
        print("=" * 100)
        print(f"[Q{index}] {question}")
        print(f"language={language} retrieved={len(chunks)}")
        print("-" * 100)
        for rank, chunk in enumerate(chunks, start=1):
            pages = format_pages(chunk.page_numbers or list(range(chunk.page_start, chunk.page_end + 1)))
            section = chunk.section_title or chunk.title
            print(f"[{rank}] score={chunk.score:.4f} {pages}")
            print(f"    title={chunk.title}")
            print(f"    section={section}")
            print(f"    file={chunk.filename}")
            print(f"    chunk_id={chunk.chunk_id}")
            print("    text:")
            print(indent_text(chunk.text[: args.max_chars]))
            if len(chunk.text) > args.max_chars:
                print("    ...")
            print()

        if args.generate:
            print("ANSWER")
            print("-" * 100)
            print(bedrock.generate_answer(question=question, chunks=chunks, language=language))
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


def indent_text(text: str) -> str:
    return "\n".join(f"    {line}" for line in text.splitlines())


if __name__ == "__main__":
    raise SystemExit(main())

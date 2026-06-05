import logging
import uuid

from app.bedrock import BedrockRuntime
from app.citations import citation_from_chunk, dedupe_citations
from app.config import Settings
from app.language import detect_language
from app.models import QueryRequest, QueryResponse
from app.s3_store import S3Storage
from app.vector_bundle import VectorBundleStore

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def answer(self, request: QueryRequest) -> QueryResponse:
        request_id = str(uuid.uuid4())
        self.settings.require_aws_runtime()
        self.settings.require_chat_model()

        language = detect_language(request.question)
        bedrock = BedrockRuntime(self.settings)
        storage = S3Storage(self.settings)
        vector_store = VectorBundleStore(self.settings, storage)

        embeddings = bedrock.embed_texts([request.question], input_type="search_query")
        chunks = vector_store.search(
            query=request.question,
            query_embedding=embeddings[0],
            top_k=request.top_k,
            use_hybrid=True,
        )

        warning_notes: list[str] = []
        if not chunks:
            warning_notes.append("No relevant source chunks were retrieved from the corpus.")
            answer = (
                "검색된 문서에서 충분한 근거를 찾지 못했습니다."
                if language == "ko"
                else "I could not find enough support in the retrieved documents."
            )
            return QueryResponse(
                answer=answer,
                citations=[],
                retrieved_chunks=[] if request.include_sources else [],
                language=language,
                warning_notes=warning_notes,
                request_id=request_id,
            )

        answer = bedrock.generate_answer(question=request.question, chunks=chunks, language=language)
        citations = dedupe_citations(
            [citation_from_chunk(chunk, pdf_url=storage.presign_pdf(chunk.pdf_s3_key)) for chunk in chunks]
        )
        logger.info("Query completed", extra={"request_id": request_id})
        return QueryResponse(
            answer=answer,
            citations=citations,
            retrieved_chunks=chunks if request.include_sources else [],
            language=language,
            warning_notes=warning_notes,
            request_id=request_id,
        )

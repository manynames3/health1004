import logging
import uuid

from app.bedrock import BedrockRuntime
from app.citations import citation_from_chunk, dedupe_citations
from app.config import Settings
from app.language import detect_language
from app.models import QueryRequest, QueryResponse, ResolvedQuery
from app.s3_store import S3Storage
from app.taxonomy import load_taxonomy, resolve_query, term_to_dict
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
        taxonomy = load_taxonomy(self.settings.taxonomy_seed_path)
        resolved_payload = resolve_query(request.question, taxonomy)
        if request.topic_slugs:
            resolved_payload["matched_topic_slugs"] = list(
                dict.fromkeys([*resolved_payload.get("matched_topic_slugs", []), *request.topic_slugs])
            )
            resolved_payload["retrieval_filters"]["topic_slugs"] = resolved_payload["matched_topic_slugs"]

        vector_store = VectorBundleStore(_settings_for_best_bundle(self.settings, storage), storage)
        vector_bundle = vector_store.load()

        embed_settings = _settings_for_bundle_embedding(self.settings, vector_bundle.metadata)
        embedder = bedrock if embed_settings is self.settings else BedrockRuntime(embed_settings)
        embeddings = embedder.embed_texts([request.question], input_type="search_query")
        chunks = vector_store.search(
            query=request.question,
            query_embedding=embeddings[0],
            top_k=request.top_k,
            use_hybrid=self.settings.opensearch_use_hybrid,
            filters=resolved_payload.get("retrieval_filters"),
            expanded_aliases=resolved_payload.get("expanded_aliases"),
            allow_broader_fallback=True,
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
                resolved_query=ResolvedQuery(**resolved_payload),
                related_topics=related_topic_dicts(resolved_payload, taxonomy),
            )

        answer = bedrock.generate_answer(question=request.question, chunks=chunks, language=language)
        citations = dedupe_citations(
            [citation_from_chunk(chunk, pdf_url=storage.presign_pdf(chunk.pdf_s3_key or chunk.source_pdf_s3_key)) for chunk in chunks]
        )
        logger.info("Query completed", extra={"request_id": request_id})
        return QueryResponse(
            answer=answer,
            citations=citations,
            retrieved_chunks=chunks if request.include_sources else [],
            language=language,
            warning_notes=warning_notes,
            request_id=request_id,
            resolved_query=ResolvedQuery(**resolved_payload),
            related_topics=related_topic_dicts(resolved_payload, taxonomy),
        )


def _settings_for_best_bundle(settings: Settings, storage: S3Storage) -> Settings:
    if settings.taxonomy_vector_bundle_key and storage.get_bytes(settings.taxonomy_vector_bundle_key):
        return settings.model_copy(update={"vector_bundle_key": settings.taxonomy_vector_bundle_key})
    return settings


def _settings_for_bundle_embedding(settings: Settings, metadata: dict) -> Settings:
    model_id = metadata.get("embedding_model_id") or settings.bedrock_embed_model_id
    dimension = int(metadata.get("embedding_dimension") or settings.vector_dimension)
    if model_id == settings.bedrock_embed_model_id and dimension == settings.vector_dimension:
        return settings
    logger.info(
        "Using vector bundle embedding model %s/%s instead of configured %s/%s",
        model_id,
        dimension,
        settings.bedrock_embed_model_id,
        settings.vector_dimension,
    )
    return settings.model_copy(update={"bedrock_embed_model_id": model_id, "vector_dimension": dimension})


def related_topic_dicts(resolved_payload: dict, taxonomy) -> list[dict]:
    slugs = resolved_payload.get("matched_topic_slugs", [])[:8]
    return [term_to_dict(taxonomy.term(slug)) for slug in slugs if taxonomy.term(slug)]

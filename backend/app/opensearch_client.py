import logging
from urllib.parse import urlparse

import boto3
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection, helpers

from app.config import Settings
from app.models import RetrievedChunk

logger = logging.getLogger(__name__)


def make_opensearch_client(settings: Settings) -> OpenSearch:
    if not settings.opensearch_endpoint:
        raise RuntimeError("OPENSEARCH_ENDPOINT is required")
    parsed = urlparse(settings.opensearch_endpoint if "://" in settings.opensearch_endpoint else f"https://{settings.opensearch_endpoint}")
    credentials = boto3.Session(region_name=settings.aws_region).get_credentials()
    if credentials is None:
        raise RuntimeError("AWS credentials were not found")
    auth = AWSV4SignerAuth(credentials, settings.aws_region, settings.opensearch_service)
    return OpenSearch(
        hosts=[{"host": parsed.netloc or parsed.path, "port": 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30,
        max_retries=3,
        retry_on_timeout=True,
    )


def ensure_vector_index(client: OpenSearch, index_name: str, dimension: int) -> None:
    if client.indices.exists(index=index_name):
        return
    body = {
        "settings": {"index": {"knn": True}},
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "document_id": {"type": "keyword"},
                "filename": {"type": "keyword"},
                "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "detected_date": {"type": "date", "ignore_malformed": True},
                "page_start": {"type": "integer"},
                "page_end": {"type": "integer"},
                "page_numbers": {"type": "integer"},
                "page_spans": {
                    "type": "object",
                    "properties": {
                        "page_number": {"type": "integer"},
                        "text": {"type": "text"},
                        "token_count": {"type": "integer"},
                    },
                },
                "section_title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "language": {"type": "keyword"},
                "text": {"type": "text"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": dimension,
                    "method": {
                        "name": "hnsw",
                        "engine": "faiss",
                        "space_type": "cosinesimil",
                    },
                },
                "source_s3_key": {"type": "keyword"},
                "pdf_s3_key": {"type": "keyword"},
                "extraction_method": {"type": "keyword"},
                "token_count": {"type": "integer"},
            }
        },
    }
    client.indices.create(index=index_name, body=body)
    logger.info("Created OpenSearch vector index", extra={"index": index_name})


def upsert_chunks(
    client: OpenSearch,
    *,
    index_name: str,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> tuple[int, list[dict]]:
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings must be the same length")
    actions = []
    for chunk, embedding in zip(chunks, embeddings):
        source = {**chunk, "embedding": embedding}
        actions.append(
            {
                "_op_type": "index",
                "_index": index_name,
                "_id": chunk["chunk_id"],
                "_source": source,
            }
        )
    success, errors = helpers.bulk(client, actions, raise_on_error=False)
    return int(success), errors


def search_chunks(
    client: OpenSearch,
    *,
    index_name: str,
    query: str,
    query_embedding: list[float],
    top_k: int,
    use_hybrid: bool = True,
) -> list[RetrievedChunk]:
    vector_hits = _search_vector(client, index_name, query_embedding, top_k)
    keyword_hits = _search_keyword(client, index_name, query, top_k) if use_hybrid else []
    return _merge_hits(vector_hits, keyword_hits, top_k)


def _search_vector(
    client: OpenSearch, index_name: str, query_embedding: list[float], top_k: int
) -> list[dict]:
    body = {
        "size": top_k,
        "_source": {"excludes": ["embedding"]},
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_embedding,
                    "k": top_k,
                }
            }
        },
    }
    response = client.search(index=index_name, body=body)
    return response.get("hits", {}).get("hits", [])


def _search_keyword(client: OpenSearch, index_name: str, query: str, top_k: int) -> list[dict]:
    body = {
        "size": top_k,
        "_source": {"excludes": ["embedding"]},
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["text^3", "page_spans.text^3", "section_title^2", "title^2", "filename"],
                "type": "best_fields",
            }
        },
    }
    response = client.search(index=index_name, body=body)
    return response.get("hits", {}).get("hits", [])


def _merge_hits(vector_hits: list[dict], keyword_hits: list[dict], top_k: int) -> list[RetrievedChunk]:
    merged: dict[str, dict] = {}
    for rank, hit in enumerate(vector_hits):
        chunk_id = hit["_source"]["chunk_id"]
        merged[chunk_id] = {
            **hit,
            "_score": float(hit.get("_score") or 0.0) + (top_k - rank) * 0.01,
        }
    for rank, hit in enumerate(keyword_hits):
        chunk_id = hit["_source"]["chunk_id"]
        if chunk_id in merged:
            merged[chunk_id]["_score"] += float(hit.get("_score") or 0.0) * 0.2
        else:
            merged[chunk_id] = {
                **hit,
                "_score": float(hit.get("_score") or 0.0) * 0.2 + (top_k - rank) * 0.005,
            }
    sorted_hits = sorted(merged.values(), key=lambda item: item.get("_score", 0.0), reverse=True)
    chunks = []
    for hit in sorted_hits[:top_k]:
        source = hit["_source"]
        chunks.append(RetrievedChunk(score=float(hit.get("_score") or 0.0), **source))
    return chunks

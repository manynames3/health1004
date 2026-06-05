import gzip
import json
import math
import re
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.config import Settings
from app.models import RetrievedChunk

if TYPE_CHECKING:
    from app.s3_store import S3Storage

SCHEMA_VERSION = 1
TOKEN_RE = re.compile(r"[\uac00-\ud7a3]{2,}|[A-Za-z0-9]{2,}")


@dataclass
class VectorRecord:
    chunk: dict[str, Any]
    embedding: list[float]
    embedding_norm: float
    lexical_tokens: set[str]


class VectorBundle:
    def __init__(self, metadata: dict[str, Any], records: list[VectorRecord]):
        self.metadata = metadata
        self.records = records


class VectorBundleStore:
    def __init__(self, settings: Settings, storage: "S3Storage | None" = None):
        self.settings = settings
        if storage is None:
            from app.s3_store import S3Storage

            storage = S3Storage(settings)
        self.storage = storage
        self._cache: VectorBundle | None = None
        self._cache_loaded_at = 0.0

    def load(self, ttl_seconds: int = 900) -> VectorBundle:
        now = time.monotonic()
        if self._cache and now - self._cache_loaded_at < ttl_seconds:
            return self._cache

        payload = self.storage.get_bytes(self.settings.vector_bundle_key)
        if payload is None:
            raise RuntimeError(
                f"Vector bundle not found at s3://{self.settings.s3_bucket}/{self.settings.vector_bundle_key}. "
                "Run scripts/ingest.py first."
            )
        bundle = parse_vector_bundle(payload)
        self._cache = bundle
        self._cache_loaded_at = now
        return bundle

    def search(
        self,
        *,
        query: str,
        query_embedding: list[float],
        top_k: int,
        use_hybrid: bool = True,
        filters: dict[str, list[str]] | None = None,
        expanded_aliases: list[str] | None = None,
        allow_broader_fallback: bool = True,
    ) -> list[RetrievedChunk]:
        bundle = self.load()
        return search_records(
            records=bundle.records,
            query=query,
            query_embedding=query_embedding,
            top_k=top_k,
            use_hybrid=use_hybrid,
            filters=filters,
            expanded_aliases=expanded_aliases,
            allow_broader_fallback=allow_broader_fallback,
        )


def search_records(
    *,
    records: list[VectorRecord],
    query: str,
    query_embedding: list[float],
    top_k: int,
    use_hybrid: bool = True,
    filters: dict[str, list[str]] | None = None,
    expanded_aliases: list[str] | None = None,
    allow_broader_fallback: bool = True,
) -> list[RetrievedChunk]:
    filtered = [record for record in records if record_matches_filters(record.chunk, filters)]
    if allow_broader_fallback and len(filtered) < top_k:
        filtered = records
    return score_records(
        records=filtered,
        query=query,
        query_embedding=query_embedding,
        top_k=top_k,
        use_hybrid=use_hybrid,
        filters=filters,
        expanded_aliases=expanded_aliases,
    )


def score_records(
    *,
    records: list[VectorRecord],
    query: str,
    query_embedding: list[float],
    top_k: int,
    use_hybrid: bool,
    filters: dict[str, list[str]] | None,
    expanded_aliases: list[str] | None,
) -> list[RetrievedChunk]:
    query_norm = vector_norm(query_embedding)
    expanded_text = " ".join([query, *(expanded_aliases or [])])
    query_tokens = tokenize(expanded_text)
    scored: list[tuple[float, dict[str, Any]]] = []

    for record in records:
        vector_score = cosine_similarity(query_embedding, query_norm, record.embedding, record.embedding_norm)
        lexical_score = jaccard_score(query_tokens, record.lexical_tokens) if use_hybrid else 0.0
        title_bonus = title_match_bonus(query_tokens, record.chunk) if use_hybrid else 0.0
        tag_bonus = taxonomy_filter_bonus(record.chunk, filters) if use_hybrid else 0.0
        score = vector_score + (0.18 * lexical_score) + title_bonus + tag_bonus
        scored.append((score, record.chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [RetrievedChunk(score=score, **chunk) for score, chunk in scored[:top_k]]


def build_vector_bundle(
    *,
    records: list[dict[str, Any]],
    embedding_model_id: str,
    embedding_dimension: int,
    created_at: str,
) -> bytes:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": created_at,
        "embedding_model_id": embedding_model_id,
        "embedding_dimension": embedding_dimension,
        "record_count": len(records),
        "records": records,
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return gzip.compress(raw, compresslevel=6)


def make_vector_record(chunk: dict[str, Any], embedding: list[float]) -> dict[str, Any]:
    return {
        "chunk": chunk,
        "embedding": embedding,
        "embedding_norm": vector_norm(embedding),
    }


def parse_vector_bundle(payload: bytes) -> VectorBundle:
    raw = gzip.decompress(payload)
    parsed = json.loads(raw.decode("utf-8"))
    if parsed.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeError(f"Unsupported vector bundle schema: {parsed.get('schema_version')}")

    records = []
    for item in parsed.get("records", []):
        chunk = item["chunk"]
        records.append(
            VectorRecord(
                chunk=chunk,
                embedding=[float(value) for value in item["embedding"]],
                embedding_norm=float(item.get("embedding_norm") or vector_norm(item["embedding"])),
                lexical_tokens=tokenize(
                    " ".join(
                        [
                            str(chunk.get("title", "")),
                            str(chunk.get("section_title", "")),
                            str(chunk.get("filename", "")),
                            str(chunk.get("text", "")),
                            " ".join(chunk.get("topic_slugs", []) or []),
                            " ".join(chunk.get("body_system_slugs", []) or []),
                            " ".join(chunk.get("symptom_slugs", []) or []),
                            " ".join(chunk.get("condition_slugs", []) or []),
                            " ".join(chunk.get("food_slugs", []) or []),
                            " ".join(chunk.get("substance_slugs", []) or []),
                            " ".join(chunk.get("habit_slugs", []) or []),
                            " ".join(
                                str(match.get("alias", ""))
                                for match in chunk.get("matched_aliases", []) or []
                                if isinstance(match, dict)
                            ),
                        ]
                    )
                ),
            )
        )
    metadata = {key: value for key, value in parsed.items() if key != "records"}
    return VectorBundle(metadata=metadata, records=records)


def vector_norm(vector: list[float]) -> float:
    return math.sqrt(sum(float(value) * float(value) for value in vector)) or 1.0


def cosine_similarity(
    left: list[float],
    left_norm: float,
    right: list[float],
    right_norm: float,
) -> float:
    if not left or not right:
        return 0.0
    limit = min(len(left), len(right))
    dot = sum(float(left[index]) * float(right[index]) for index in range(limit))
    return dot / (left_norm * right_norm)


def tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text or "")}


def jaccard_score(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def title_match_bonus(query_tokens: set[str], chunk: dict[str, Any]) -> float:
    haystack = tokenize(
        " ".join(
            [
                str(chunk.get("title", "")),
                str(chunk.get("section_title", "")),
                str(chunk.get("filename", "")),
            ]
        )
    )
    if not query_tokens or not haystack:
        return 0.0
    return min(0.05, 0.01 * len(query_tokens & haystack))


def record_matches_filters(chunk: dict[str, Any], filters: dict[str, list[str]] | None) -> bool:
    if not filters:
        return True
    for field, wanted in filters.items():
        if not wanted:
            continue
        values = chunk.get(field) or []
        if isinstance(values, str):
            values = [values]
        if set(values) & set(wanted):
            return True
    return False


def taxonomy_filter_bonus(chunk: dict[str, Any], filters: dict[str, list[str]] | None) -> float:
    if not filters:
        return 0.0
    matched_fields = 0
    matched_values = 0
    for field, wanted in filters.items():
        values = chunk.get(field) or []
        if isinstance(values, str):
            values = [values]
        overlap = set(values) & set(wanted)
        if overlap:
            matched_fields += 1
            matched_values += len(overlap)
    return min(0.22, 0.08 * matched_fields + 0.02 * matched_values)

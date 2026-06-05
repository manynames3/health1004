from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any, Iterable

import yaml

from app.language import detect_language


TAXONOMY_CATEGORIES = (
    "body_systems",
    "symptoms",
    "conditions",
    "foods",
    "substances",
    "habits",
)

CATEGORY_FILTER_FIELDS = {
    "body_systems": "body_system_slugs",
    "symptoms": "symptom_slugs",
    "conditions": "condition_slugs",
    "foods": "food_slugs",
    "substances": "substance_slugs",
    "habits": "habit_slugs",
}

QUERY_TOPIC_EXPANSIONS = {
    "indigestion": ["gastritis", "gastrointestinal-disease"],
    "heartburn": ["gastritis", "gastrointestinal-disease"],
    "constipation": ["bowel-disease", "intestinal-disease"],
    "diarrhea": ["bowel-disease", "intestinal-disease"],
    "milk": ["osteoporosis", "osteoporosis-condition", "dairy"],
    "meat": ["colorectal-cancer", "factory-farming"],
    "preservative": ["food-additives-topic", "sodium-benzoate"],
    "colorant": ["tar-color", "allergy-condition"],
}

KOREAN_PARTICLE_RE = re.compile(r"(으로|에서|에게|에는|에도|만은|까지|부터|처럼|보다|으로는|의|은|는|이|가|을|를|에|와|과|도|만|로)$")
TOKEN_RE = re.compile(r"[\uac00-\ud7a3]{2,}|[A-Za-z][A-Za-z0-9 -]{1,}|[0-9]{2,}")
PUNCTUATION_RE = re.compile(r"[\s\-_./,;:!?()\[\]{}<>\"'`~·ㆍ•|+*=\\]+")
OCR_NOISE_TRANSLATION = str.maketrans(
    {
        "０": "0",
        "１": "1",
        "２": "2",
        "３": "3",
        "４": "4",
        "５": "5",
        "６": "6",
        "７": "7",
        "８": "8",
        "９": "9",
        "Ａ": "A",
        "Ｂ": "B",
        "Ｃ": "C",
        "Ｄ": "D",
        "Ｅ": "E",
        "Ｆ": "F",
        "Ｇ": "G",
        "Ｈ": "H",
        "Ｉ": "I",
        "Ｊ": "J",
        "Ｋ": "K",
        "Ｌ": "L",
        "Ｍ": "M",
        "Ｎ": "N",
        "Ｏ": "O",
        "Ｐ": "P",
        "Ｑ": "Q",
        "Ｒ": "R",
        "Ｓ": "S",
        "Ｔ": "T",
        "Ｕ": "U",
        "Ｖ": "V",
        "Ｗ": "W",
        "Ｘ": "X",
        "Ｙ": "Y",
        "Ｚ": "Z",
    }
)


@dataclass(frozen=True)
class TaxonomyTerm:
    slug: str
    title: str
    category: str
    aliases: tuple[str, ...] = ()
    english_title: str | None = None
    body_system_slugs: tuple[str, ...] = ()
    related_slugs: tuple[str, ...] = ()

    @property
    def all_labels(self) -> tuple[str, ...]:
        labels = [self.title]
        if self.english_title:
            labels.append(self.english_title)
        labels.extend(self.aliases)
        return tuple(dict.fromkeys(label for label in labels if label))


@dataclass
class AliasHit:
    slug: str
    title: str
    category: str
    alias: str
    normalized_alias: str
    score: float


@dataclass
class Taxonomy:
    terms: dict[str, TaxonomyTerm] = field(default_factory=dict)
    by_category: dict[str, list[TaxonomyTerm]] = field(default_factory=dict)
    alias_index: dict[str, list[TaxonomyTerm]] = field(default_factory=dict)

    def terms_for_category(self, category: str) -> list[TaxonomyTerm]:
        return self.by_category.get(category, [])

    def term(self, slug: str) -> TaxonomyTerm | None:
        return self.terms.get(slug)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "categories": {
                category: [term_to_dict(term) for term in self.terms_for_category(category)]
                for category in TAXONOMY_CATEGORIES
            },
            "topic_count": len(self.terms),
            "alias_count": sum(len(term.aliases) + 1 for term in self.terms.values()),
        }


def load_taxonomy(seed_path: str | Path) -> Taxonomy:
    path = Path(seed_path).expanduser()
    if not path.exists():
        raise RuntimeError(f"Taxonomy seed not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    terms: dict[str, TaxonomyTerm] = {}
    by_category: dict[str, list[TaxonomyTerm]] = {}
    alias_index: dict[str, list[TaxonomyTerm]] = {}

    for category in TAXONOMY_CATEGORIES:
        category_terms = []
        for raw in payload.get(category, []) or []:
            title = str(raw["title"]).strip()
            slug = str(raw.get("slug") or slugify(title)).strip()
            aliases = tuple(str(alias).strip() for alias in raw.get("aliases", []) if str(alias).strip())
            term = TaxonomyTerm(
                slug=slug,
                title=title,
                category=category,
                aliases=tuple(dict.fromkeys(aliases)),
                english_title=raw.get("english_title"),
                body_system_slugs=tuple(raw.get("body_systems", []) or []),
                related_slugs=tuple(raw.get("related", []) or []),
            )
            if slug in terms:
                raise RuntimeError(f"Duplicate taxonomy slug: {slug}")
            terms[slug] = term
            category_terms.append(term)
            for label in term.all_labels:
                normalized = normalize_for_match(label)
                if normalized:
                    alias_index.setdefault(normalized, []).append(term)
        by_category[category] = category_terms
    return Taxonomy(terms=terms, by_category=by_category, alias_index=alias_index)


def term_to_dict(term: TaxonomyTerm, source_count: int = 0) -> dict[str, Any]:
    return {
        "slug": term.slug,
        "title": term.title,
        "english_title": term.english_title,
        "category": term.category,
        "aliases": list(term.aliases),
        "body_system_slugs": list(term.body_system_slugs),
        "related_slugs": list(term.related_slugs),
        "source_count": source_count,
    }


def normalize_for_match(text: str) -> str:
    text = (text or "").translate(OCR_NOISE_TRANSLATION).lower()
    text = text.replace("㎎", "mg").replace("ｍｓｇ", "msg")
    text = text.replace("나트륨", "나트륨").replace("나트리움", "나트륨")
    text = text.replace("벤조산", "안식향산") if "벤조산나트륨" in text else text
    text = PUNCTUATION_RE.sub("", text)
    text = KOREAN_PARTICLE_RE.sub("", text)
    return text


def normalize_search_text(text: str) -> str:
    text = (text or "").translate(OCR_NOISE_TRANSLATION).lower()
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str) -> str:
    normalized = normalize_search_text(text)
    if re.search(r"[A-Za-z0-9]", normalized):
        slug = re.sub(r"[^a-z0-9]+", "-", normalized)
    else:
        slug = re.sub(r"[^0-9a-zA-Z\uac00-\ud7a3]+", "-", normalized)
    return slug.strip("-") or "topic"


def match_text(text: str, taxonomy: Taxonomy) -> list[AliasHit]:
    normalized_text = normalize_for_match(text)
    if not normalized_text:
        return []

    hits: list[AliasHit] = []
    seen: set[tuple[str, str]] = set()
    for normalized_alias, terms in taxonomy.alias_index.items():
        if len(normalized_alias) < 2:
            continue
        if normalized_alias not in normalized_text:
            continue
        for term in terms:
            key = (term.slug, normalized_alias)
            if key in seen:
                continue
            seen.add(key)
            exact_title = normalized_alias == normalize_for_match(term.title)
            score = min(0.98, 0.55 + min(0.25, len(normalized_alias) / 40) + (0.12 if exact_title else 0.0))
            hits.append(
                AliasHit(
                    slug=term.slug,
                    title=term.title,
                    category=term.category,
                    alias=_display_alias(normalized_alias, term),
                    normalized_alias=normalized_alias,
                    score=score,
                )
            )
    hits.sort(key=lambda hit: (hit.score, len(hit.normalized_alias)), reverse=True)
    return hits


def resolve_query(query: str, taxonomy: Taxonomy) -> dict[str, Any]:
    hits = match_text(query, taxonomy)
    matched_slugs = _expand_query_slugs(_unique(hit.slug for hit in hits if hit.category != "body_systems"))
    body_system_slugs = _unique(
        [
            slug
            for hit in hits
            for slug in (
                [hit.slug] if hit.category == "body_systems" else taxonomy.term(hit.slug).body_system_slugs if taxonomy.term(hit.slug) else []
            )
        ]
    )
    expanded_aliases = _unique(alias for hit in hits for alias in _aliases_for_hit(hit, taxonomy))
    filters = build_retrieval_filters(matched_slugs, body_system_slugs, taxonomy)
    return {
        "original_query": query,
        "detected_language": detect_language(query),
        "matched_topics": [taxonomy.term(slug).title for slug in matched_slugs if taxonomy.term(slug)],
        "matched_topic_slugs": matched_slugs,
        "matched_body_systems": [taxonomy.term(slug).title for slug in body_system_slugs if taxonomy.term(slug)],
        "matched_body_system_slugs": body_system_slugs,
        "expanded_aliases": expanded_aliases,
        "retrieval_filters": filters,
    }


def build_retrieval_filters(topic_slugs: list[str], body_system_slugs: list[str], taxonomy: Taxonomy) -> dict[str, list[str]]:
    filters: dict[str, list[str]] = {}
    if topic_slugs:
        filters["topic_slugs"] = topic_slugs
    if body_system_slugs:
        filters["body_system_slugs"] = body_system_slugs
    for slug in topic_slugs:
        term = taxonomy.term(slug)
        if not term:
            continue
        field = CATEGORY_FILTER_FIELDS.get(term.category)
        if field:
            filters.setdefault(field, []).append(slug)
    return {key: _unique(values) for key, values in filters.items() if values}


def _expand_query_slugs(slugs: list[str]) -> list[str]:
    expanded = list(slugs)
    for slug in slugs:
        expanded.extend(QUERY_TOPIC_EXPANSIONS.get(slug, []))
    return _unique(expanded)


def tag_passage(
    *,
    text: str,
    taxonomy: Taxonomy,
    min_confidence: float = 0.65,
    metadata_text: str = "",
) -> dict[str, Any]:
    combined = "\n".join(part for part in [metadata_text, text] if part)
    hits = match_text(combined, taxonomy)
    topic_slugs = _unique(hit.slug for hit in hits if hit.category != "body_systems")
    body_system_slugs = _unique(
        slug
        for hit in hits
        for slug in (
            [hit.slug] if hit.category == "body_systems" else taxonomy.term(hit.slug).body_system_slugs if taxonomy.term(hit.slug) else []
        )
    )
    grouped = {field: [] for field in CATEGORY_FILTER_FIELDS.values()}
    grouped["body_system_slugs"] = body_system_slugs
    for slug in topic_slugs:
        term = taxonomy.term(slug)
        if not term:
            continue
        field = CATEGORY_FILTER_FIELDS.get(term.category)
        if field:
            grouped[field].append(slug)

    exact_canonical_hits = sum(1 for hit in hits if taxonomy.term(hit.slug) and normalize_for_match(taxonomy.term(hit.slug).title) == hit.normalized_alias)
    confidence = 0.0
    if hits:
        confidence = min(
            0.99,
            0.48
            + min(0.28, 0.07 * len(set(hit.slug for hit in hits)))
            + min(0.13, 0.02 * len(hits))
            + min(0.10, 0.025 * exact_canonical_hits),
        )
    needs_review = confidence < min_confidence or not topic_slugs
    food_context = classify_food_context(text)

    return {
        "topic_slugs": topic_slugs,
        "body_system_tags": grouped["body_system_slugs"],
        "body_system_slugs": grouped["body_system_slugs"],
        "symptom_tags": _unique(grouped["symptom_slugs"]),
        "symptom_slugs": _unique(grouped["symptom_slugs"]),
        "condition_tags": _unique(grouped["condition_slugs"]),
        "condition_slugs": _unique(grouped["condition_slugs"]),
        "food_tags": _unique(grouped["food_slugs"]),
        "food_slugs": _unique(grouped["food_slugs"]),
        "substance_tags": _unique(grouped["substance_slugs"]),
        "substance_slugs": _unique(grouped["substance_slugs"]),
        "habit_tags": _unique(grouped["habit_slugs"]),
        "habit_slugs": _unique(grouped["habit_slugs"]),
        "avoid_tags": _avoid_tags(grouped, food_context),
        "recommended_food_tags": _recommended_food_tags(grouped, food_context),
        "confidence_score": round(confidence, 4),
        "needs_human_review": needs_review,
        "matched_aliases": [
            {
                "slug": hit.slug,
                "title": hit.title,
                "category": hit.category,
                "alias": hit.alias,
                "score": round(hit.score, 4),
            }
            for hit in hits
        ],
    }


def build_taxonomy_report(tagged_chunks: list[dict[str, Any]], taxonomy: Taxonomy) -> dict[str, Any]:
    total = len(tagged_chunks)
    tagged = [chunk for chunk in tagged_chunks if chunk.get("topic_slugs")]
    low_confidence = [chunk for chunk in tagged_chunks if chunk.get("needs_human_review")]
    topic_counter: Counter[str] = Counter()
    unmatched_terms: Counter[str] = Counter()
    suspicious_files: set[str] = set()
    review_docs: Counter[str] = Counter()

    for chunk in tagged_chunks:
        topic_counter.update(chunk.get("topic_slugs", []))
        if not chunk.get("topic_slugs"):
            unmatched_terms.update(extract_candidate_korean_terms(chunk.get("text", "")))
        if "low_confidence" in str(chunk.get("extraction_method", "")) or chunk.get("needs_human_review"):
            review_docs.update([chunk.get("document_id") or chunk.get("filename") or "unknown"])
        diagnostics = json.dumps(chunk.get("extraction_diagnostics", {}), ensure_ascii=False)
        if "garbled" in diagnostics or "low_text" in diagnostics or "ocr" in str(chunk.get("extraction_method", "")):
            suspicious_files.add(chunk.get("filename") or "unknown")

    return {
        "total_passages": total,
        "tagged_passages": len(tagged),
        "untagged_passages": total - len(tagged),
        "low_confidence_passages": len(low_confidence),
        "top_matched_topics": [
            {
                "slug": slug,
                "title": taxonomy.term(slug).title if taxonomy.term(slug) else slug,
                "count": count,
            }
            for slug, count in topic_counter.most_common(30)
        ],
        "top_unmatched_korean_nouns_or_phrases": [
            {"term": term, "count": count} for term, count in unmatched_terms.most_common(40)
        ],
        "ocr_suspicious_files": sorted(suspicious_files),
        "documents_needing_manual_review": [
            {"document_id": doc_id, "passage_count": count} for doc_id, count in review_docs.most_common(50)
        ],
    }


def apply_tagging_to_chunk(chunk: dict[str, Any], taxonomy: Taxonomy, min_confidence: float) -> dict[str, Any]:
    metadata_text = " ".join(
        str(chunk.get(key, ""))
        for key in ["title", "filename", "section_title", "detected_date"]
    )
    tagging = tag_passage(
        text=str(chunk.get("text", "")),
        taxonomy=taxonomy,
        min_confidence=min_confidence,
        metadata_text=metadata_text,
    )
    enriched = {**chunk, **tagging}
    enriched.setdefault("article_id", infer_article_id(enriched))
    enriched.setdefault("source_pdf_s3_key", enriched.get("pdf_s3_key"))
    enriched.setdefault("source_text_s3_key", enriched.get("source_s3_key"))
    enriched.setdefault("source_page_image_s3_key", None)
    enriched.setdefault("embedding_id", enriched.get("chunk_id"))
    enriched.setdefault("original_korean_text", enriched.get("text", ""))
    enriched.setdefault("english_summary_optional", None)
    return enriched


def infer_article_id(chunk: dict[str, Any]) -> str:
    document_id = str(chunk.get("document_id") or "document")
    section = slugify(str(chunk.get("section_title") or chunk.get("title") or "article"))
    return f"{document_id}:{section[:80]}"


def extract_candidate_korean_terms(text: str, min_len: int = 2) -> list[str]:
    candidates = []
    for token in TOKEN_RE.findall(text or ""):
        token = token.strip()
        if not re.search(r"[\uac00-\ud7a3]", token):
            continue
        token = KOREAN_PARTICLE_RE.sub("", token)
        if len(token) >= min_len and token not in {"그리고", "그러나", "입니다", "있습니다", "합니다"}:
            candidates.append(token)
    return candidates


def classify_food_context(text: str) -> str:
    normalized = normalize_search_text(text)
    if re.search(r"피하|나쁘|해롭|주의|위험|문제|첨가|독성|오염", normalized):
        return "avoid"
    if re.search(r"좋|도움|효능|권장|추천|유익|회복|예방", normalized):
        return "recommend"
    return "neutral"


def _avoid_tags(grouped: dict[str, list[str]], food_context: str) -> list[str]:
    tags = list(grouped.get("substance_slugs", []))
    if food_context == "avoid":
        tags.extend(grouped.get("food_slugs", []))
    return _unique(tags)


def _recommended_food_tags(grouped: dict[str, list[str]], food_context: str) -> list[str]:
    if food_context != "recommend":
        return []
    return _unique(grouped.get("food_slugs", []))


def _aliases_for_hit(hit: AliasHit, taxonomy: Taxonomy) -> list[str]:
    term = taxonomy.term(hit.slug)
    if not term:
        return [hit.alias]
    return list(term.aliases[:8])


def _display_alias(normalized_alias: str, term: TaxonomyTerm) -> str:
    for label in term.all_labels:
        if normalize_for_match(label) == normalized_alias:
            return label
    return normalized_alias


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))

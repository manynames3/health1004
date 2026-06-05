# Tradeoffs

This project makes several deliberate choices for a low-volume Korean archive.

## Taxonomy-First Instead Of Chatbot-First

Decision: make symptoms, foods, conditions, substances, habits, and source PDFs the primary navigation paths.

Why:

- Korean user phrasing varies heavily.
- OCR text can contain spacing and recognition noise.
- Health-adjacent answers need traceable sources.
- Browsing should work even before a user knows how to phrase a good query.

Cost:

- Taxonomy curation takes human effort.
- New aliases need review.
- The UI and data model are more complex than a single chat box.

## S3 Vector Bundle By Default

Decision: store compressed chunk metadata and embeddings in S3 as the default vector store.

Why:

- Low maintenance.
- Low cost for a small archive.
- Easy to rebuild from ingestion artifacts.
- No always-on search cluster.

Cost:

- Not ideal for high concurrency.
- Bundle loading and in-memory search can become slow at larger scale.
- Search behavior is less feature-rich than a managed search service.

## Optional OpenSearch

Decision: support OpenSearch mappings and reindexing, but do not provision OpenSearch by default.

Why:

- The archive can grow into metadata-filtered Korean full-text search.
- Nori analyzer support is useful when available.
- Keeping it optional respects the low-volume cost target.

Cost:

- Operators must provide and secure their own endpoint.
- Local development usually uses mapping-plan output instead of a live cluster.

## No Reranker By Default

Decision: keep `ENABLE_RERANK=false` and rely on taxonomy filters, Korean aliases, keyword scoring, and vector similarity.

Why:

- Avoids another model lifecycle dependency.
- Avoids another per-query Bedrock charge.
- Keeps the low-volume archive simpler to operate.
- Korean retrieval quality should first be improved through taxonomy and aliases.

Cost:

- Some ambiguous queries may rank less cleanly than with a strong reranker.
- A future evaluation may justify adding a reranker for answer-heavy usage.

## Claude Answers With AWS-Owned Embeddings

Decision: use Claude Haiku 4.5 for answer quality, Nova 2 Lite as answer fallback, and Titan Text Embeddings V2 for retrieval vectors.

Why:

- Readers feel answer quality through Korean phrasing, source-grounded caution, and citation discipline.
- Titan embeddings remove the default Cohere retrieval dependency.
- Answer-model changes are low risk compared with embedding-model changes.

Cost:

- The answer path still depends on a third-party Bedrock provider for the primary model.
- If the embedding model changes, all vectors must be rebuilt.

## Manual Ingestion

Decision: ingest PDFs manually through scripts or an admin upload path.

Why:

- The corpus is a finite historical archive.
- Manual runs are easier to audit.
- No crawler or scheduler cost.
- Operators can inspect OCR diagnostics before publishing.

Cost:

- Not a real-time content system.
- Admin upload auth is intentionally simple.
- Human review remains necessary for weak OCR and low-confidence tags.

## Postgres For Structured Metadata

Decision: add SQLAlchemy/Alembic models and local Docker Compose Postgres.

Why:

- Taxonomy review, assignments, pages, passages, and retrieval logs need structure.
- Alembic gives clear migration history.
- Docker Compose keeps local setup reproducible.

Cost:

- A hosted database adds operational responsibility if used outside local development.
- Some read paths can still operate from S3/vector artifacts, so DB availability must be documented per deployment.

## Static Frontend On Cloudflare Pages

Decision: deploy the frontend as a static export.

Why:

- Simple public hosting.
- Low maintenance.
- Fast preview of archive navigation.

Cost:

- Dynamic query and admin actions need a separately configured backend API.
- Environment-specific API URLs must be set at build/deploy time.

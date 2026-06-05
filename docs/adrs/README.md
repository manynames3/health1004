# Architecture Decision Records

These ADRs record the main product and platform choices. They are intentionally concise so reviewers can understand the reasoning without digging through commit history.

## ADR 001: Taxonomy-First Archive Over Chatbot-First UI

Status: Accepted

Context: The source corpus is Korean PDF text with OCR risk, inconsistent spacing, and domain-specific phrasing. A single chat/search box makes discovery fragile and can overstate the reliability of semantic retrieval.

Decision: Make taxonomy browsing the primary product path. Organize the archive by symptoms, foods, conditions, substances, habits, and original PDFs. Keep RAG as an assistant layer over tagged, citation-backed passages.

Consequences:

- Users can browse without knowing the perfect query wording.
- Query resolution can map everyday Korean phrases to canonical topics.
- Taxonomy curation becomes an explicit maintenance task.

## ADR 002: S3 Vector Bundle As Default Retrieval Store

Status: Accepted

Context: The archive is low-volume and manually ingested. A managed search cluster would add cost and maintenance before the workload requires it.

Decision: Store compressed chunk metadata and embeddings in S3 and load them into the backend for retrieval. Preserve optional OpenSearch reindex support for future scale.

Consequences:

- Default infrastructure stays cheap and easy to tear down.
- Retrieval remains reproducible from S3 artifacts.
- High concurrency or larger corpora may eventually require OpenSearch or another managed index.

## ADR 003: Manual Ingestion With OCR Diagnostics

Status: Accepted

Context: The corpus is a finite historical archive, not a feed that needs crawling. Korean OCR quality varies by PDF.

Decision: Use manual ingestion through scripts and admin upload. Extract embedded text first, run OCR only when text quality is weak, and write ingestion reports with diagnostics.

Consequences:

- Operators can inspect quality before publishing.
- No scheduler or crawler cost.
- Bad OCR still requires human review.

## ADR 004: Postgres For Structured Taxonomy And Review State

Status: Accepted

Context: Taxonomy assignments, aliases, page records, passages, and review flags need structured storage beyond flat JSON artifacts.

Decision: Add SQLAlchemy/Alembic models and Docker Compose Postgres for local development. Keep S3 artifacts as the durable corpus source.

Consequences:

- Local review workflows are reproducible.
- A hosted database can be added when needed.
- Operators must define backup and retention policies for hosted use.

## ADR 005: Cloudflare Pages Static Frontend With Separate API Runtime

Status: Accepted

Context: The user-facing archive can be rendered as a static Next.js app, while Bedrock, S3, and admin ingestion require server-side credentials.

Decision: Deploy the frontend to Cloudflare Pages as a static export and keep the FastAPI backend as a separate runtime boundary.

Consequences:

- Static hosting is simple and low maintenance.
- The public site can be reviewed without exposing backend secrets.
- API-backed features require `NEXT_PUBLIC_API_BASE_URL` and a configured backend deployment.

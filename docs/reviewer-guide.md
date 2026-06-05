# Technical Product Guide

Use this guide to understand what Health1004 does, how it is built, and how the system is operated.

## One-Minute Summary

Health1004 is a Korean natural-health archive that turns weekly PDF newsletters into searchable, source-traceable content. The core product is taxonomy-based browsing by symptoms, foods, conditions, substances, habits, and original PDFs. The assistant layer is grounded in retrieved passages, Korean aliases, and page-level citations instead of open-ended generation.

## What Problem It Solves

The corpus is a set of Korean natural-health newsletters. A plain PDF chatbot is weak for this use case because OCR noise, Korean spacing, domain terms, aliases, and health-adjacent questions make semantic retrieval unreliable by itself. The system lets users browse by normalized topics first, then ask grounded questions against tagged passages.

## What To Inspect First

- `README.md` for product positioning, commands, and evidence matrix
- `docs/architecture.md` for the system diagram and data flows
- `backend/app/taxonomy.py` for Korean normalization, alias matching, and query resolution
- `backend/app/rag.py` and `backend/app/vector_bundle.py` for retrieval and answer generation
- `docs/model-strategy.md` for the Bedrock model profile and embedding migration rules
- `backend/app/ingestion.py` and `scripts/ingest.py` for manual ingestion
- `data/taxonomy.seed.yaml` for controlled Korean taxonomy
- `backend/tests/` for behavior-level tests
- `.github/workflows/ci.yml` for the CI contract

## Engineering Signals

- Ambiguous Korean health-search questions are handled through taxonomy and aliases before generation.
- Source traceability is preserved from ingestion through retrieval, citations, and UI links.
- The default AWS architecture keeps idle cost low with static hosting, private S3, manual ingestion, and optional Lambda.
- Security, cost, observability, reliability, and teardown are documented as operating concerns.
- Model lifecycle risk is explicit: answer-model changes are simple, embedding-model changes require vector rebuilds.
- Tests and CI cover the behavior that matters for document retrieval and archive operations.

## File Map For Technical Review

| Concern | Files to inspect |
| --- | --- |
| Infrastructure | `infra/main.tf`, `infra/iam.tf`, `infra/lambda.tf`, `infra/variables.tf`, `infra/README.md` |
| CI | `.github/workflows/ci.yml` |
| Backend API | `backend/app/main.py`, `backend/app/models.py`, `backend/app/config.py` |
| Retrieval/RAG | `backend/app/rag.py`, `backend/app/vector_bundle.py`, `backend/app/bedrock.py`, `backend/app/prompt.py` |
| Taxonomy | `backend/app/taxonomy.py`, `data/taxonomy.seed.yaml`, `scripts/build_taxonomy.py`, `scripts/tag_passages.py` |
| Ingestion | `backend/app/ingestion.py`, `backend/app/extraction.py`, `scripts/ingest.py` |
| Frontend | `frontend/app/`, `frontend/components/`, `frontend/lib/staticArchiveClient.ts` |
| Tests | `backend/tests/` |
| Operations | `docs/runbook.md`, `docs/deployment.md`, `docs/teardown.md`, `docs/security.md`, `docs/observability.md`, `docs/cost-model.md` |

## How To Run Or Inspect It

```bash
cd backend
PYTHONPATH=. pytest

cd ../frontend
npm run build

cd ../infra
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

The evaluation path for retrieval is:

```bash
python scripts/evaluate_taxonomy_retrieval.py
```

It prints resolved topics, filters, retrieved passages, source documents/pages, and citation status before answer generation.

The live static frontend is available at [https://health1004.pages.dev](https://health1004.pages.dev). API-backed features require a configured backend URL and environment.

## Implemented Capabilities

- Static frontend deployment on Cloudflare Pages
- FastAPI app with taxonomy, archive, RAG, and admin endpoints
- Terraform for low-cost S3/IAM infrastructure
- Ingestion pipeline that writes S3 artifacts and reports
- SQLAlchemy/Alembic schema for structured archive metadata
- Optional OpenSearch mapping/reindex support
- Tests for taxonomy, citations, schema, extraction, vector bundle behavior, and admin paths

## Current Boundaries

- The public Pages site serves static archive pages unless a backend API URL is configured.
- The default Terraform stack intentionally avoids always-on OpenSearch or compute.
- Admin authentication uses shared secrets; enterprise SSO/RBAC would be the next step for multi-user operations.
- The system is an educational archive, not clinical validation or medical care.
- Browser/e2e tests, load tests, and automated citation faithfulness scoring are planned improvements.

## Strongest Engineering Decisions

- The default architecture avoids expensive always-on search for a low-volume archive.
- The RAG assistant is constrained to retrieved source passages and citations.
- Taxonomy tags are deterministic first, with optional LLM help only as a secondary path.
- Manual review is built into the data model through confidence scores and review flags.
- Teardown, cost, security, testing, and operational gaps are documented explicitly.
- Model lifecycle risk is handled by separating answer-model fallback from embedding-vector rebuilds.

## Tradeoffs To Notice

- S3 vector bundles keep idle cost low, but will not scale like a managed vector/search service under high concurrency.
- Shared-secret admin auth is acceptable for a low-volume internal workflow, but should be replaced for multi-user production.
- Static Pages hosting is simple and cheap, but dynamic query/admin flows require a separate backend endpoint.
- Manual ingestion is auditable and cost-aware, but not suitable for real-time content updates.
- OCR and taxonomy quality depend on human review and corpus-specific tuning.

## What I Would Improve Next

- Add a hosted API deployment path with explicit smoke tests after publish.
- Add structured CloudWatch or OpenTelemetry metrics and alarms for query errors, Bedrock failures, ingestion failures, and citation-empty answers.
- Add browser/e2e tests for browse, source search, query, and admin review flows.
- Replace shared admin secrets with identity-provider-backed auth if the archive becomes multi-user.
- Add an evaluation set for Korean retrieval relevance and citation faithfulness.

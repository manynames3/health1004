# Reviewer Guide

This guide is written for a recruiter, hiring manager, or engineer evaluating the repository as an AWS/cloud/platform work sample.

## One-Minute Summary

Health1004 is a Korean PDF archive that preserves manual ingestion and RAG, but makes taxonomy-based browsing the primary product. It demonstrates low-cost cloud architecture, source-traceable retrieval, deterministic Korean alias matching, admin ingestion, and operational documentation without claiming production traffic or maturity that is not present.

## What Problem It Solves

The corpus is a set of Korean natural-health newsletters. A plain PDF chatbot is weak for this use case because OCR noise, Korean spacing, domain terms, aliases, and health-adjacent questions make semantic retrieval unreliable by itself. The system lets users browse by normalized topics first, then ask grounded questions against tagged passages.

## What To Inspect First

- `README.md` for product positioning, commands, and evidence matrix
- `docs/architecture.md` for the system diagram and data flows
- `backend/app/taxonomy.py` for Korean normalization, alias matching, and query resolution
- `backend/app/rag.py` and `backend/app/vector_bundle.py` for retrieval and answer generation
- `backend/app/ingestion.py` and `scripts/ingest.py` for manual ingestion
- `data/taxonomy.seed.yaml` for controlled Korean taxonomy
- `backend/tests/` for behavior-level tests
- `.github/workflows/ci.yml` for the CI contract

## How To Verify Locally

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

## What Is Real

- Static frontend deployment on Cloudflare Pages
- FastAPI app with taxonomy, archive, RAG, and admin endpoints
- Terraform for low-cost S3/IAM infrastructure
- Ingestion pipeline that writes S3 artifacts and reports
- SQLAlchemy/Alembic schema for structured archive metadata
- Optional OpenSearch mapping/reindex support
- Tests for taxonomy, citations, schema, extraction, vector bundle behavior, and admin paths

## What Is Not Claimed

- No production user traffic claim
- No uptime or latency SLA claim
- No certification, audit, or compliance claim
- No hosted always-on AWS API claim in the default deployment
- No live OpenSearch cluster provisioned by Terraform
- No clinical safety validation

## Strong Signals

- The default architecture avoids expensive always-on search for a low-volume archive.
- The RAG assistant is constrained to retrieved source passages and citations.
- Taxonomy tags are deterministic first, with optional LLM help only as a secondary path.
- Manual review is built into the data model through confidence scores and review flags.
- Teardown, cost, security, testing, and operational gaps are documented explicitly.

# Testing

Health1004 uses focused tests and build checks for archive behavior, static frontend generation, and Terraform validation.

## Backend Tests

Run:

```bash
cd backend
PYTHONPATH=. pytest
```

Current test areas include:

- Korean alias matching
- query-to-topic resolution
- passage tagging
- taxonomy seed loading
- citation formatting
- topic page API response
- hybrid retrieval filter construction
- RAG response schema
- Titan embedding request shape
- primary-to-fallback answer model behavior
- admin authentication and ingestion boundaries
- extraction fallback decisions
- vector bundle retrieval behavior

## Frontend Build

Run:

```bash
cd frontend
npm run build
```

The frontend uses Next.js static export. Build success verifies route generation and TypeScript compilation for the static site.

## Terraform Validation

Run:

```bash
cd infra
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

This validates syntax and provider configuration without applying infrastructure.

## Retrieval Evaluation

Run:

```bash
python scripts/evaluate_taxonomy_retrieval.py
```

The script prints:

- Korean question
- resolved topics
- filters used
- expanded aliases
- retrieved chunks
- source document and page
- citation status

This is a qualitative retrieval sanity check, not an automated clinical or factual benchmark.

When evaluating after an embedding model change, confirm the active vector bundle metadata reports the intended `embedding_model_id` and `embedding_dimension`. Query-time embedding follows the bundle metadata, so evaluation can continue to use an older bundle until a full re-embedding run replaces it.

## CI

GitHub Actions workflow:

```text
.github/workflows/ci.yml
```

The workflow runs backend tests, frontend build, and Terraform format/validate. It does not deploy and does not require AWS credentials.

## What Was Validated Locally

Use the commands above as the local verification contract before review or handoff. They validate Python behavior, static frontend compilation, and Terraform syntax/provider configuration. They do not prove hosted AWS runtime health, Bedrock model access in a particular account, or Cloudflare deployment state.

## Manual Validation

- Retrieval evaluation is a qualitative script, not a statistically validated benchmark.
- OCR quality is checked through ingestion diagnostics and manual review, not a labeled OCR benchmark.
- Hosted API smoke tests are manual because deployment is not automatic in GitHub Actions.
- Medical-adjacent answer safety is prompt- and citation-based, not clinical validation.
- Browser/e2e coverage is not implemented yet.

## Gaps

- No browser automation test suite yet.
- No load tests.
- No hosted API smoke test in CI.
- No automated citation faithfulness scoring.
- No OCR accuracy benchmark against hand-labeled pages.

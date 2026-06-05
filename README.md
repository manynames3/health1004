# Health1004 Korean Archive

Production-style AWS/cloud platform engineering sample for a taxonomy-first Korean natural-health PDF archive.

Health1004 turns a one-time corpus of Korean weekly PDF newsletters into a browsable, source-traceable knowledge archive organized by symptoms, foods, conditions, substances, habits, and original documents. RAG is preserved as an assistant layer, but the main product is structured archive navigation with Korean-aware aliases, citations, and manual review paths.

Live static frontend: [health1004.pages.dev](https://health1004.pages.dev)

The live Pages deployment is the static frontend. The FastAPI backend, Bedrock calls, private S3 corpus, and optional database/index services require environment configuration and are designed to run locally or on a low-cost on-demand runtime.

## Why This Exists

Korean semantic retrieval can be brittle for domain-specific OCR text. This project uses a controlled taxonomy first, then layers retrieval and generation over tagged, citation-backed passages. The result is closer to a respectful digital archive than a generic chatbot demo.

Primary user paths:

- 내 증상/건강 고민으로 찾기
- 음식/식재료로 찾기
- 피해야 할 첨가물/화학물질 찾기
- 질환별 자료 보기
- 생활습관별 자료 보기
- 원문 PDF 읽기
- AI에게 질문하기

The app is educational and archival. It is not medical diagnosis, treatment, dosage, or medication advice.

## Current Product Behavior

The browse pages are taxonomy-first. Users can start from curated Korean topic cards for symptoms, foods, conditions, substances, habits, and original PDFs. Search boxes on those category pages do two things:

1. Filter the curated topic cards by Korean title, English title, and aliases.
2. Search the existing indexed PDF passage text when the typed term is not already represented by a curated card.

For example, `/substances/` may show only a short controlled list of additive topics at first, but a query such as `아스파탐`, `유화제`, or `카라멜색소` also returns matching source passages from the archive. This keeps the user from being trapped inside the current taxonomy while still making taxonomy the primary navigation layer.

The source-result lane shows:

- matching original passage snippets
- PDF filename and page range
- document detail links
- an "ask from sources" path into the assistant
- an admin alias-suggestion link for repeated missing terms

## What Reviewers Should Notice

| Area | Evidence in this repo |
| --- | --- |
| Cloud architecture | Terraform for low-cost S3/IAM, optional Lambda Function URL backend, Cloudflare Pages static frontend, Bedrock integration, optional OpenSearch mapping |
| Cost discipline | No always-on OpenSearch, App Runner, ECR, CloudFront, or scheduled ingestion in the default Terraform |
| Data pipeline | Manual PDF ingestion, page-aware extraction, Korean OCR fallback, checksums, S3 artifacts, ingestion reports |
| Retrieval design | Taxonomy resolution before hybrid search, category-page source search, vector bundle fallback, OpenSearch Nori support when available |
| Source traceability | PDF filename, title, page ranges, section heading, Korean quote, S3 keys, and signed PDF links in citations |
| Operational maturity | Runbook, teardown guide, cost model, security notes, observability notes, ADRs, admin review paths, and CI workflow |
| Testability | Backend pytest suite, static frontend build, Terraform format/validate workflow, Korean taxonomy evaluation script |

## Architecture

See [docs/architecture.md](docs/architecture.md) for diagrams and data flows.

At a high level:

1. A manual ingestion job uploads raw PDFs to private S3.
2. Text is extracted page-by-page with Korean OCR fallback only when needed.
3. Chunks keep page spans so citations remain page-accurate.
4. Bedrock creates Titan Text Embeddings V2 vectors.
5. A compressed S3 vector bundle is the default low-cost retrieval store.
6. SQLAlchemy/Alembic adds structured taxonomy and review tables for local or hosted Postgres.
7. Optional OpenSearch reindexing supports metadata filters and Korean Nori analysis when an endpoint exists.
8. FastAPI resolves Korean queries into canonical topics and aliases before retrieval.
9. FastAPI can also search existing passage text directly for category-page source results.
10. Next.js renders taxonomy-first browsing, source-result search, admin review, and an assistant UI.

## Tech Stack

- Frontend: Next.js static export, React, TypeScript, Cloudflare Pages
- Backend: FastAPI, Pydantic, SQLAlchemy, Alembic
- AWS: S3, IAM, Bedrock Runtime, optional OpenSearch endpoint support
- Retrieval: deterministic Korean alias matching, hybrid keyword/vector retrieval, S3 vector bundle
- Ingestion: PyMuPDF, optional PaddleOCR, optional Tesseract Korean OCR
- Infrastructure: Terraform for private S3 bucket and attachable IAM policies
- Local development: Docker Compose Postgres

## Bedrock Model Profile

The default model profile is:

| Purpose | Model |
| --- | --- |
| Primary answer generation | `anthropic.claude-haiku-4-5-20251001-v1:0` |
| Fallback answer generation | `amazon.nova-2-lite-v1:0` |
| Embeddings | `amazon.titan-embed-text-v2:0` |
| Reranking | disabled with `ENABLE_RERANK=false` |

This keeps answer quality high while removing Cohere from the default retrieval path. Changing answer models only requires an env/IAM update and backend restart. Changing the embedding model requires a full vector rebuild because stored passage vectors and query vectors must use the same model and dimension.

See [docs/model-strategy.md](docs/model-strategy.md) for the full rationale and migration steps.

## Local Quickstart

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cd frontend
npm install
cp .env.local.example .env.local
cd ..
```

Set the required environment values:

```bash
AWS_REGION=us-east-1
S3_BUCKET=<private corpus bucket>
VECTOR_BUNDLE_KEY=vector-index/chunks.json.gz
VECTOR_DIMENSION=1024
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0
BEDROCK_CHAT_MODEL_ID=anthropic.claude-haiku-4-5-20251001-v1:0
BEDROCK_FALLBACK_CHAT_MODEL_ID=amazon.nova-2-lite-v1:0
ENABLE_RERANK=false
DATABASE_URL=postgresql+psycopg://health1004:health1004@localhost:5432/health1004
ADMIN_TOKEN=<strong admin upload token>
ADMIN_PASSWORD=<review UI password>
```

Start local Postgres and migrate:

```bash
docker compose up -d postgres
DATABASE_URL=postgresql+psycopg://health1004:health1004@localhost:5432/health1004 alembic upgrade head
```

Run the API:

```bash
cd backend
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run the frontend:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## Ingestion And Taxonomy Commands

Put PDFs in `./pdfs`, then run manual ingestion:

```bash
python scripts/ingest.py --pdf-dir ./pdfs --s3-prefix raw-pdfs/
```

Useful ingestion options:

```bash
python scripts/ingest.py --pdf-dir ./pdfs --limit 3
python scripts/ingest.py --pdf-dir ./pdfs --force
python scripts/ingest.py --pdf-dir ./pdfs --report-path ./ingestion_report.json
```

The ingestion report includes per-file status, checksums, page counts, chunk counts, OCR diagnostics, suspicious extraction flags, S3 artifact keys, and vector bundle settings.

Build or update the controlled taxonomy:

```bash
python scripts/build_taxonomy.py --seed data/taxonomy.seed.yaml
```

Add new Korean terms and aliases directly in `data/taxonomy.seed.yaml`. Prefer canonical health/archive language for the topic title, then add common spellings, spacing variants, OCR variants, and English names in `aliases`. Deterministic alias matching runs before any optional LLM helper, so this file is the main search-quality lever.

Tag or re-tag existing chunks without rerunning OCR:

```bash
python scripts/tag_passages.py --source existing --report outputs/taxonomy_report.json
python scripts/tag_passages.py --source existing --force --report outputs/taxonomy_report.json
```

After appending a new PDF folder, tag from the freshly updated raw vector bundle so the taxonomy bundle includes both old and new documents:

```bash
python scripts/tag_passages.py \
  --source existing \
  --bundle-key vector-index/chunks.json.gz \
  --report outputs/taxonomy_report.json
```

Rebuild taxonomy-aware OpenSearch artifacts, or reindex a configured endpoint:

```bash
python scripts/reindex_with_taxonomy.py --rebuild
```

If `OPENSEARCH_ENDPOINT` is not set, the script writes local mapping and reindex-plan artifacts only. This keeps the default project low-cost.

Run taxonomy retrieval evaluation:

```bash
python scripts/evaluate_taxonomy_retrieval.py
```

The evaluation prints resolved topics, filters, top retrieved passages, document/page sources, and whether citations were returned before answer generation.

When changing `BEDROCK_EMBED_MODEL_ID`, rebuild embeddings with a full ingestion run so stored passage vectors and query vectors use the same model. The backend reads the active vector bundle metadata and embeds queries with that recorded model to avoid silently mixing embedding spaces during migrations.

## Category Search And Alias Review

Category pages such as `/symptoms/`, `/foods/`, `/conditions/`, `/substances/`, and `/habits/` use the `CategoryBrowser` component. The component caches the topic list in browser local storage for fast repeat visits, then performs live source search for typed terms of at least two characters.

For production, category lists and topic-detail pages also prefer prebuilt static JSON under `frontend/public/static-data/archive/`. This lets new visitors load curated topic cards and the top source passages for pages such as `/topics/onion/` or `/topics/food-additives-topic/` directly from Cloudflare Pages instead of waiting for Lambda to scan the S3 vector bundle.

Rebuild the static archive cache after any ingestion, re-tagging, taxonomy alias changes, or vector-bundle replacement:

```bash
python scripts/build_static_archive_cache.py --topic-limit 8
npm --prefix frontend run build
```

The generated cache includes:

- `frontend/public/static-data/archive/categories/*.json` for topic lists.
- `frontend/public/static-data/archive/topics/*.json` for per-topic source passages and related documents.
- `frontend/public/static-data/archive/manifest.json` with generation counts and source bundle keys.

The cache intentionally strips expiring presigned PDF URLs. Topic pages link to document detail pages for stable navigation; live PDF links are generated on demand by the backend where needed.

The live source search calls:

```text
GET /search/passages?q=<term>&category=<symptoms|foods|conditions|substances|habits>&limit=6
```

The backend search flow is intentionally low-cost:

1. Normalize Korean spacing, punctuation, Hangul variants, English capitalization, and common OCR noise.
2. Resolve the query against canonical topics and aliases.
3. Search matching tagged passages first when a category filter exists.
4. Fall back to broader indexed passage text if the taxonomy filter is too narrow.
5. Return source passages with filename, page range, chunk id, matched topics, expanded aliases, and whether fallback was used.

This endpoint does not call Bedrock. It searches the existing S3 vector bundle metadata and passage text, so category-page source search is cheap and fast compared with answer generation.

Repeated missing terms can be proposed from the UI:

```text
POST /admin/alias-suggestion
```

The request requires `ADMIN_PASSWORD` and stores a pending suggestion at `admin/alias_suggestions.json` in S3. Review those suggestions manually, then add accepted aliases or new canonical topics to `data/taxonomy.seed.yaml` and run the normal build/tag/reindex commands above.

## API Surface

Archive and taxonomy:

- `GET /taxonomy`
- `GET /topics`
- `GET /topics/{slug}`
- `GET /symptoms`
- `GET /foods`
- `GET /conditions`
- `GET /substances`
- `GET /habits`
- `GET /documents`
- `GET /documents/{document_id}`
- `GET /passages?topic=...`
- `GET /search/passages?q=...&category=...`

Query and assistant:

- `POST /query/resolve`
- `POST /query`

Admin:

- `GET /admin/status`
- `POST /admin/ingest`
- `GET /admin/low-confidence-passages`
- `POST /admin/review-tag`
- `POST /admin/alias-suggestion`

Admin upload endpoints require `ADMIN_TOKEN`. Review endpoints use `ADMIN_PASSWORD`, with local-only fallback for development.

## Verification

Local checks:

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

CI mirrors these checks in [.github/workflows/ci.yml](.github/workflows/ci.yml). No status badge is shown because a badge would imply a hosted CI history that may not exist yet on a fresh fork.

## Deploy And Operate

Detailed operational docs:

- [docs/deployment.md](docs/deployment.md)
- [docs/runbook.md](docs/runbook.md)
- [docs/model-strategy.md](docs/model-strategy.md)
- [docs/security.md](docs/security.md)
- [docs/observability.md](docs/observability.md)
- [docs/cost-model.md](docs/cost-model.md)
- [docs/teardown.md](docs/teardown.md)
- [docs/testing.md](docs/testing.md)
- [docs/tradeoffs.md](docs/tradeoffs.md)
- [docs/adrs/README.md](docs/adrs/README.md)
- [docs/safety.md](docs/safety.md)
- [docs/ocr-troubleshooting.md](docs/ocr-troubleshooting.md)

Terraform creates the private S3 corpus bucket and attachable IAM policies by default. Set `deploy_api=true` to also deploy the low-cost FastAPI Lambda Function URL backend:

```bash
cd infra
terraform init
terraform apply \
  -var="aws_region=us-east-1" \
  -var="bedrock_chat_model_id=anthropic.claude-haiku-4-5-20251001-v1:0" \
  -var="bedrock_fallback_chat_model_id=amazon.nova-2-lite-v1:0" \
  -var="bedrock_embed_model_id=amazon.titan-embed-text-v2:0"
```

Build and deploy the Lambda API package:

```bash
python scripts/build_lambda_package.py
terraform apply \
  -var="deploy_api=true" \
  -var="bedrock_chat_model_id=anthropic.claude-haiku-4-5-20251001-v1:0" \
  -var="bedrock_fallback_chat_model_id=amazon.nova-2-lite-v1:0" \
  -var="bedrock_embed_model_id=amazon.titan-embed-text-v2:0" \
  -var="lambda_package_path=../outputs/health1004-api-lambda.zip"
```

Attach `ingestion_policy_arn` to the IAM principal that runs ingestion. When `deploy_api=true`, Terraform creates and attaches the runtime role automatically.

## Project Structure

```text
backend/          FastAPI API, ingestion helpers, retrieval, taxonomy, DB models, tests
data/             Controlled Korean taxonomy seed
docs/             Architecture, operations, security, ADRs, review guide
frontend/         Next.js static export for Cloudflare Pages
infra/            Terraform for private S3 and IAM policies
scripts/          Ingestion, taxonomy tagging, reindexing, retrieval evaluation
outputs/          Local generated reports and mapping plans, ignored except .gitkeep
```

## Known Limitations

- The live Pages site is static unless connected to a configured backend API.
- The default Terraform intentionally avoids expensive always-on search or compute services.
- OCR quality depends on the source PDFs and installed local OCR engines.
- Retrieval quality still needs human evaluation against the real corpus before public medical-adjacent use.
- Admin authentication is intentionally minimal for a low-volume internal workflow.
- Retrieval logs can contain user questions if persisted; review retention and privacy policy before production use.
- Newly added taxonomy aliases do not change stored source counts until re-tag/re-index commands are run.

## Next Production Hardening

- Add hosted API runtime choice and deployment automation.
- Add structured metrics and alerts for query errors, Bedrock failures, ingestion failures, and citation gaps.
- Add object lifecycle policies if source artifacts grow.
- Expand the human review workflow for low-confidence taxonomy assignments and alias suggestions.
- Add auth if the archive should remain private.

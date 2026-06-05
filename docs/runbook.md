# Runbook

This runbook covers the low-volume archive workflow: local development, manual ingestion, taxonomy updates, retrieval checks, and common recovery steps.

## Service Boundaries

- Frontend: static Next.js export on Cloudflare Pages or local `npm run dev`
- Backend: FastAPI app, local or hosted separately
- Storage: private S3 bucket for PDFs, extracted text, reports, and vector bundles
- Database: local or hosted Postgres when structured taxonomy/review state is needed
- Search: S3 vector bundle by default, optional existing OpenSearch endpoint

## Local Startup

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
docker compose up -d postgres
DATABASE_URL=postgresql+psycopg://health1004:health1004@localhost:5432/health1004 alembic upgrade head
```

Backend:

```bash
cd backend
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm run dev
```

Health check:

```bash
curl http://localhost:8000/health
```

## Manual Ingestion

1. Put PDFs in `./pdfs`.
2. Confirm `.env` has `AWS_REGION`, `S3_BUCKET`, Bedrock model ids, and vector settings.
3. Run:

```bash
python scripts/ingest.py --pdf-dir ./pdfs --s3-prefix raw-pdfs/ --report-path ./ingestion_report.json
```

4. Review `ingestion_report.json` for failed files, low-text pages, OCR fallback, and suspicious extraction flags.
5. Re-run only when needed with `--force`.

Default model settings:

```bash
BEDROCK_CHAT_MODEL_ID=anthropic.claude-haiku-4-5-20251001-v1:0
BEDROCK_FALLBACK_CHAT_MODEL_ID=amazon.nova-2-lite-v1:0
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0
VECTOR_DIMENSION=1024
ENABLE_RERANK=false
```

## Model Changes And Re-Embedding

Changing `BEDROCK_CHAT_MODEL_ID` or `BEDROCK_FALLBACK_CHAT_MODEL_ID` does not require re-ingestion. Update env, confirm IAM access, restart or redeploy the backend, and run retrieval evaluation.

Changing `BEDROCK_EMBED_MODEL_ID` or `VECTOR_DIMENSION` requires rebuilding the vector bundle:

```bash
python scripts/ingest.py --pdf-dir ./pdfs --s3-prefix raw-pdfs/ --force --report-path outputs/ingestion_reembed.json
python scripts/tag_passages.py --source existing --force --report outputs/taxonomy_report.json
python scripts/reindex_with_taxonomy.py --rebuild
python scripts/evaluate_taxonomy_retrieval.py
```

The backend reads `embedding_model_id` and `embedding_dimension` from the active vector bundle and embeds queries with those recorded values. This prevents silently mixing old and new embedding spaces while a rebuild is in progress.

## Taxonomy Update

1. Edit `data/taxonomy.seed.yaml`.
2. Build the taxonomy artifact:

```bash
python scripts/build_taxonomy.py --seed data/taxonomy.seed.yaml
```

3. Re-tag existing chunks without full OCR:

```bash
python scripts/tag_passages.py --source existing --report outputs/taxonomy_report.json
```

4. Review `outputs/taxonomy_report.json` for untagged passages, low-confidence passages, and unmatched Korean terms.

## Reindexing

Default low-cost plan mode:

```bash
python scripts/reindex_with_taxonomy.py --rebuild
```

With no `OPENSEARCH_ENDPOINT`, this writes `outputs/opensearch_mapping.json` and `outputs/reindex_plan.json`.

When an endpoint is configured, verify credentials and index name before running. The script targets the configured endpoint and index from `.env`.

## Evaluation

```bash
python scripts/evaluate_taxonomy_retrieval.py
```

Review:

- resolved topics
- filters used
- top passages
- document and page citations
- whether citations were returned

Do not generate or trust answers until retrieved chunks look relevant.

## Admin Uploads

Set `ADMIN_TOKEN` and use `/admin/ingest` through the frontend Admin section or a multipart request. The upload path runs the same ingestion code as the CLI and writes the same S3 artifact types.

Review low-confidence tags at `/admin/review`. Set `ADMIN_PASSWORD` for non-local use.

## Common Issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `/health` says S3 not configured | Missing `S3_BUCKET` | Update `.env` and restart API |
| Bedrock embedding fails | Region, model access, or IAM issue | Confirm Bedrock model access and IAM permissions |
| Retrieval quality drops after model change | Vector bundle was not rebuilt or active bundle still uses old embeddings | Re-run full ingestion with `--force`, then tag, reindex, and evaluate |
| PDFs ingest with little text | Scanned pages or poor OCR | Install Tesseract Korean or PaddleOCR, rerun with `--force` |
| Topic pages show little data | Chunks not tagged or taxonomy artifact stale | Run build taxonomy and tag scripts |
| OpenSearch reindex only writes local files | `OPENSEARCH_ENDPOINT` is unset | This is expected for low-cost/default mode |
| Admin upload returns 401 | Missing or wrong `ADMIN_TOKEN` | Send `X-Admin-Token` or Bearer token |

## Rollback And Recovery

- Frontend: roll back to a previous Cloudflare Pages deployment.
- S3 vector bundle: restore a previous `vector-index/chunks.json.gz` object version if bucket versioning is enabled, or re-run ingestion from the source PDFs.
- Taxonomy: revert `data/taxonomy.seed.yaml`, rebuild taxonomy, re-tag passages.
- Database: use Alembic downgrade only after testing locally; otherwise restore from a Postgres backup.
- OpenSearch: rebuild from the S3 vector bundle and taxonomy metadata.

## Operational Notes

Logs are JSON-formatted and include request ids where available. Ingestion reports contain filenames and extraction diagnostics and should be treated as internal operational artifacts.

# AWS Korean PDF RAG

Production-style RAG website for a one-time, manually ingested corpus of 572 weekly PDF newsletters from a Korean natural health practitioner. The app is for document search and education only; it is not medical diagnosis, treatment, or medication advice.

## What It Builds

- Next.js static frontend with Korean-first search/chat UI, citations, retrieved passages, document browser, date/title filtering, and PDF links.
- FastAPI backend with `/query`, `/documents`, `/documents/{document_id}`, `/admin/status`, `/admin/ingest`, and `/health`.
- Manual and admin ingestion for PDFs with embedded-text extraction, Korean OCR fallback, chunking, Bedrock embeddings, S3 artifacts, a compressed S3 vector bundle, checksums, and ingestion reports.
- Low-cost Terraform for a private S3 corpus bucket and attachable IAM policies. It intentionally does not provision OpenSearch, App Runner, ECR, CloudFront, or always-on compute.

The corpus is ingested manually. There are no crawlers, schedulers, or recurring ingestion jobs.

## Architecture

1. Place PDFs in `./pdfs`.
2. Run `python scripts/ingest.py --pdf-dir ./pdfs --s3-prefix raw-pdfs/`.
3. Ingestion uploads raw PDFs to S3, extracts page text, falls back to local Korean OCR when needed, writes JSON/Markdown artifacts, chunks Korean text, embeds chunks with Bedrock Cohere Embed Multilingual, and writes `vector-index/chunks.json.gz` to S3.
4. Users ask questions in the frontend.
5. FastAPI embeds the query, loads the cached S3 vector bundle, retrieves top chunks using exact vector plus keyword scoring, asks a Bedrock chat model to answer only from retrieved context, and returns structured citations.

## Local Setup

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

Fill `.env`:

```bash
AWS_REGION=us-east-1
S3_BUCKET=<terraform corpus bucket>
VECTOR_BUNDLE_KEY=vector-index/chunks.json.gz
VECTOR_DIMENSION=1024
BEDROCK_CHAT_MODEL_ID=<your Bedrock chat model id>
ADMIN_TOKEN=<strong shared secret for admin uploads>
```

The default embedding model is `cohere.embed-multilingual-v3`. Keep `VECTOR_DIMENSION=1024` for that model unless you change embedding models and rebuild the vector bundle.

## AWS Prerequisites

- AWS credentials available locally through your normal profile or environment.
- Bedrock model access enabled in the selected `AWS_REGION`.
- Access to `cohere.embed-multilingual-v3`.
- Access to the configured `BEDROCK_CHAT_MODEL_ID`.
- Terraform installed.

## Bedrock Model Notes

The ingestion and query paths call Bedrock Runtime directly with `boto3`.

- Document chunks use Cohere Embed `input_type="search_document"`.
- User queries use `input_type="search_query"`.
- The answer model uses Bedrock Converse API so the model id remains configurable.

If your selected chat model requires an inference profile, set `BEDROCK_CHAT_MODEL_ID` to the profile-compatible id and make sure IAM permits it.

## Ingest PDFs

Put the 572 PDFs in:

```bash
./pdfs
```

Run:

```bash
python scripts/ingest.py --pdf-dir ./pdfs --s3-prefix raw-pdfs/
```

Useful options:

```bash
python scripts/ingest.py --pdf-dir ./pdfs --limit 3
python scripts/ingest.py --pdf-dir ./pdfs --force
python scripts/ingest.py --pdf-dir ./pdfs --report-path ./ingestion_report.json
```

The CLI skips files whose checksum already exists in `metadata/documents.json` unless `--force` is passed.

## Admin Uploads

Set `ADMIN_TOKEN` on the FastAPI backend, then open the Admin section in the frontend. The admin form sends the token as `X-Admin-Token`, uploads one or more PDFs to `/admin/ingest`, and runs the same ingestion pipeline as the CLI.

Admin API endpoints:

- `GET /admin/status` verifies the admin token and returns S3/vector configuration.
- `POST /admin/ingest` accepts multipart PDF uploads, uploads raw PDFs to S3, writes extracted artifacts, refreshes `metadata/documents.json`, rebuilds `vector-index/chunks.json.gz`, and returns the ingestion report summary.

For AWS-hosted backends, the runtime role needs the Terraform `runtime_policy_arn`, which includes S3 write access for admin ingestion.

Artifacts written to S3:

- `raw-pdfs/<filename>.pdf`
- `extracted/<document_id>/pages.json`
- `extracted/<document_id>/pages.md`
- `metadata/documents.json`
- `ingestion-reports/ingestion_report.json`
- `vector-index/chunks.json.gz`

The same report is also written locally to `ingestion_report.json` by default. It includes:

- run id, start/end timestamps, and configured model/vector-bundle settings
- per-file status, checksum, page count, chunk count, and S3 artifact keys
- embedded-text quality diagnostics
- OCR attempt diagnostics, engine name, mean confidence where available, and fallback errors
- low-text/garbled/weak-language flags
- skipped, failed, OCR fallback, OCR failure, and low-confidence counts

## Korean OCR

Embedded selectable text is tried first with PyMuPDF. If the extracted text is too short or garbled, local OCR is attempted:

1. PaddleOCR Korean if installed.
2. Tesseract with `kor+eng`.

On macOS:

```bash
brew install tesseract tesseract-lang
pip install paddleocr
```

PaddleOCR is optional because it is large; the backend Dockerfile installs Tesseract Korean and English language packs.

## Run Locally

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

Open `http://localhost:3000`.

## Deploy AWS Storage With Terraform

Initialize:

```bash
cd infra
terraform init
```

```bash
terraform apply \
  -var="aws_region=us-east-1" \
  -var="bedrock_chat_model_id=<chat-model-id>"
```

This creates only a private S3 corpus bucket and attachable IAM policies. The static frontend is deployed separately on Cloudflare Pages, and the API can run locally or on an on-demand runtime if needed.

## API

`POST /query`

```json
{
  "question": "수면에 대해 문서에서는 무엇을 말하나요?",
  "top_k": 8,
  "include_sources": true
}
```

Response:

```json
{
  "answer": "...",
  "citations": [
    {
      "document_id": "...",
      "chunk_id": "...",
      "title": "...",
      "filename": "...",
      "detected_date": "2024-01-05",
      "page_start": 3,
      "page_end": 4,
      "quote": "...",
      "pdf_url": "..."
    }
  ],
  "retrieved_chunks": [],
  "language": "ko",
  "warning_notes": [],
  "request_id": "..."
}
```

## Tests

```bash
cd backend
PYTHONPATH=. pytest
```

Coverage includes chunking, citation formatting, language detection, vector-bundle retrieval, query response schema, and OCR fallback decision logic.

## Retrieval Evaluation

Print retrieved chunks for 10 Korean smoke-test questions before any answer generation:

```bash
python scripts/evaluate_retrieval.py --top-k 5
```

Generate answers only after reviewing retrieved chunks:

```bash
python scripts/evaluate_retrieval.py --top-k 5 --generate
```

You can supply your own UTF-8 question file:

```bash
python scripts/evaluate_retrieval.py --questions-file ./eval-questions.txt --top-k 8
```

## Safety

The system prompt requires the model to use only retrieved context, cite factual claims, say when evidence is insufficient, avoid diagnosis or treatment advice, and include a brief safety note for personal health questions.

The frontend always displays:

> This system summarizes uploaded documents and is not medical advice. Consult a qualified professional for medical decisions.

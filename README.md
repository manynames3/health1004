# AWS Korean PDF RAG

Production-style RAG website for a one-time, manually ingested corpus of 572 weekly PDF newsletters from a Korean natural health practitioner. The app is for document search and education only; it is not medical diagnosis, treatment, or medication advice.

## What It Builds

- Next.js static frontend with Korean-first search/chat UI, citations, retrieved passages, document browser, date/title filtering, and PDF links.
- FastAPI backend with `/query`, `/documents`, `/documents/{document_id}`, and `/health`.
- Manual ingestion CLI for local PDFs with embedded-text extraction, Korean OCR fallback, chunking, Bedrock embeddings, OpenSearch upserts, S3 artifacts, checksums, and ingestion reports.
- Terraform for S3, OpenSearch Serverless vector collection, IAM, ECR/App Runner API hosting, and CloudFront/S3 frontend hosting.

The corpus is ingested manually. There are no crawlers, schedulers, or recurring ingestion jobs.

## Architecture

1. Place PDFs in `./pdfs`.
2. Run `python scripts/ingest.py --pdf-dir ./pdfs --s3-prefix raw-pdfs/ --rebuild-index`.
3. Ingestion uploads raw PDFs to S3, extracts page text, falls back to local Korean OCR when needed, writes JSON/Markdown artifacts, chunks Korean text, embeds chunks with Bedrock Cohere Embed Multilingual, and upserts vectors into OpenSearch Serverless.
4. Users ask questions in the frontend.
5. FastAPI embeds the query, retrieves top chunks using vector plus keyword retrieval, asks a Bedrock chat model to answer only from retrieved context, and returns structured citations.

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
OPENSEARCH_ENDPOINT=<terraform opensearch_collection_endpoint>
OPENSEARCH_INDEX=korean-health-chunks
BEDROCK_CHAT_MODEL_ID=<your Bedrock chat model id>
```

The default embedding model is `cohere.embed-multilingual-v3`. Keep `OPENSEARCH_VECTOR_DIMENSION=1024` for that model unless you change embedding models and rebuild the index.

## AWS Prerequisites

- AWS credentials available locally through your normal profile or environment.
- Bedrock model access enabled in the selected `AWS_REGION`.
- Access to `cohere.embed-multilingual-v3`.
- Access to the configured `BEDROCK_CHAT_MODEL_ID`.
- Terraform installed.
- Docker installed if deploying the backend container to ECR/App Runner.

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
python scripts/ingest.py --pdf-dir ./pdfs --s3-prefix raw-pdfs/ --rebuild-index
```

Useful options:

```bash
python scripts/ingest.py --pdf-dir ./pdfs --limit 3 --rebuild-index
python scripts/ingest.py --pdf-dir ./pdfs --force
python scripts/ingest.py --pdf-dir ./pdfs --report-path ./ingestion_report.json
```

The CLI skips files whose checksum already exists in `metadata/documents.json` unless `--force` is passed.

Artifacts written to S3:

- `raw-pdfs/<filename>.pdf`
- `extracted/<document_id>/pages.json`
- `extracted/<document_id>/pages.md`
- `metadata/documents.json`
- `ingestion-reports/ingestion_report.json`

The same report is also written locally to `ingestion_report.json` by default. It includes:

- run id, start/end timestamps, and configured model/index settings
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

## Deploy With Terraform

Initialize:

```bash
cd infra
terraform init
```

Create foundational resources and ECR:

```bash
terraform apply \
  -target=aws_ecr_repository.backend \
  -var="aws_region=us-east-1" \
  -var="bedrock_chat_model_id=<chat-model-id>"
```

Build and push backend:

```bash
aws ecr get-login-password --region <region> \
  | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
docker build -t korean-health-rag-backend -f backend/Dockerfile .
docker tag korean-health-rag-backend:latest <ecr-repo-url>:latest
docker push <ecr-repo-url>:latest
```

Apply the rest:

```bash
terraform apply \
  -var="aws_region=us-east-1" \
  -var="bedrock_chat_model_id=<chat-model-id>" \
  -var='ingestion_principal_arns=["arn:aws:iam::<account-id>:user/<you>"]'
```

Build and upload frontend:

```bash
cd frontend
NEXT_PUBLIC_API_BASE_URL=https://<app-runner-url> npm run build
aws s3 sync out/ s3://<frontend_bucket>/ --delete
```

Then invalidate CloudFront if replacing assets:

```bash
aws cloudfront create-invalidation --distribution-id <distribution-id> --paths "/*"
```

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

Coverage includes chunking, citation formatting, language detection, query response schema, and OCR fallback decision logic.

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

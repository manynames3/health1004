# Architecture

## Components

- Frontend: static Next.js app hosted on Cloudflare Pages.
- Backend: FastAPI app that can run locally or on low-cost on-demand compute.
- Corpus storage: S3 bucket with raw PDFs, extracted JSON/Markdown, metadata, and ingestion reports.
- Vector store: gzipped S3 vector bundle loaded and cached by the backend for exact search.
- Models: Amazon Bedrock Cohere Embed Multilingual for embeddings and a configurable Bedrock chat model for answers.

## Query Flow

1. Frontend posts a question to `/query`.
2. Backend detects Korean, English, mixed, or unknown language.
3. Backend embeds the query with `input_type="search_query"`.
4. Backend retrieves chunks from the cached S3 vector bundle by vector similarity and keyword scoring.
5. Backend sends retrieved context and citation metadata to Bedrock Converse.
6. Backend returns answer, citations, retrieved chunks, warnings, and request id.

## Ingestion Flow

1. Walk `./pdfs` once during a manual run.
2. Upload each raw PDF to S3.
3. Extract embedded text with PyMuPDF, preserving page boundaries.
4. Fall back to local Korean OCR when extraction is too short or garbled.
5. Save page JSON and Markdown artifacts to S3.
6. Detect title/date from filename and first page.
7. Chunk text using Korean-aware token estimates and page ranges.
8. Store page-specific spans inside each chunk so citations can point to exact page excerpts.
9. Embed document chunks with `input_type="search_document"`.
10. Write `vector-index/chunks.json.gz` with chunk metadata and embeddings.
11. Write `metadata/documents.json`, local `ingestion_report.json`, and S3 `ingestion-reports/ingestion_report.json`.

## Source Traceability

Every chunk stores:

- `chunk_id`
- `document_id`
- `filename`
- `title`
- `detected_date`
- `page_start`
- `page_end`
- `page_numbers`
- `page_spans`
- `section_title`
- `language`
- `text`
- `source_s3_key`
- `pdf_s3_key`
- `extraction_method`
- `token_count`

The API returns citations with PDF signed URLs and source snippets.

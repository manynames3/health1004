# Observability

The repository includes lightweight observability suitable for local development and a low-volume archive. It does not claim production dashboards or alerting yet.

## Current Signals

- JSON logs from the FastAPI backend
- request ids on RAG responses
- ingestion reports with per-file status and OCR diagnostics
- taxonomy reports with tagged, untagged, low-confidence, and unmatched-topic summaries
- evaluation script output for query resolution, filters, retrieved passages, and citation status
- FastAPI `/health` endpoint for configuration sanity checks

## Log Shape

Backend logs include:

- timestamp
- level
- logger
- message
- exception details when present
- request id, document id, or chunk id when attached

Avoid logging full user questions in application logs unless there is an explicit privacy decision. The database schema can persist retrieval queries, so retention and redaction should be set before production use.

## Ingestion Diagnostics

`ingestion_report.json` is the main operational artifact for corpus quality. Review:

- skipped, failed, and completed files
- page counts and chunk counts
- extraction method
- OCR fallback attempts
- low-text or garbled-text warnings
- S3 artifact keys
- vector bundle settings

## Taxonomy Diagnostics

`outputs/taxonomy_report.json` helps decide where human review is needed:

- total passages
- tagged passages
- untagged passages
- low-confidence passages
- top matched topics
- top unmatched Korean nouns or phrases
- OCR suspicious files
- documents needing manual review

## Recommended Hosted Metrics

If the backend is hosted on AWS or another runtime, add metrics for:

- request count and error rate by route
- p95 query latency
- Bedrock embedding and answer failures
- answer fallback usage
- active vector bundle `embedding_model_id` and `embedding_dimension`
- S3 vector bundle load failures
- citation-empty responses
- no-result topic queries
- ingestion failures
- low-confidence passage count

## Recommended Alerts

- API 5xx rate above threshold
- Bedrock failure spike
- unexpected answer fallback spike
- active vector bundle using an unintended embedding model after migration
- ingestion job failed
- vector bundle missing or unreadable
- admin upload rejected due to size or auth repeatedly
- citation-empty answer rate above threshold

These are recommendations, not currently provisioned alerts.

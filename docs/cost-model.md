# Cost Model

The default design is for a low-volume, low-maintenance archive. It avoids expensive always-on services unless the operator explicitly adds them.

## Default Cost Drivers

| Component | Default use | Cost behavior |
| --- | --- | --- |
| Cloudflare Pages | Static frontend | Usually low or free-tier friendly for small traffic |
| S3 | Raw PDFs, extracted text, reports, vector bundles | Storage plus request costs |
| Bedrock embeddings | Ingestion and query embeddings | Pay per model call |
| Bedrock chat | RAG answer generation | Pay per model call |
| Lambda Function URL | Optional FastAPI backend | Pay per request and duration, no idle compute |
| Local Postgres | Docker Compose for development | No cloud cost |
| Terraform | S3/IAM by default, optional Lambda | No ongoing Terraform cost |

## Intentionally Not Provisioned By Default

- OpenSearch
- App Runner
- ECR
- CloudFront
- always-on EC2
- recurring ingestion jobs
- scheduled crawlers

The application includes OpenSearch mapping and reindex support, but Terraform does not create an OpenSearch domain. For a small archive, S3 vector bundles, taxonomy filtering, and Lambda on-demand API execution are the cheaper default.

## Default Bedrock Cost Profile

Default model settings:

- answer generation: `anthropic.claude-haiku-4-5-20251001-v1:0`
- fallback answer generation: `amazon.nova-2-lite-v1:0`
- embeddings: `amazon.titan-embed-text-v2:0`
- reranking: disabled

The fallback answer model should be rarely used; it is only called when the primary answer model fails. Reranking is disabled so each query avoids an extra model call. Ingestion is the largest embedding event because every passage is embedded; normal user queries embed only the question and then generate an answer when source chunks are found.

## Cost Controls

- Run ingestion manually instead of on a schedule.
- Reuse extracted chunks and re-tag without full OCR when taxonomy changes.
- Keep OpenSearch disabled until query volume or corpus size justifies it.
- Keep PDF and report artifacts in S3, not a running container filesystem.
- Use short signed URL TTLs.
- Prefer on-demand API hosting if the backend is deployed.
- Keep evaluation scripts manual so they do not create surprise model-call costs.
- Keep `ENABLE_RERANK=false` until evaluation proves a reranker is worth the extra per-query call.
- Avoid changing embedding models casually, because a full corpus re-embedding creates a one-time Bedrock cost.

## When To Add More Infrastructure

Consider OpenSearch or a managed API runtime only when:

- S3 vector bundle load time becomes too slow.
- concurrent query volume requires shared retrieval infrastructure.
- filtering and keyword search need production-grade latency.
- admin ingestion must be available to non-technical users without local scripts.

## Cost Review Checklist

- Confirm no OpenSearch domain was created unintentionally.
- Confirm no always-on compute is running.
- Review S3 object count and storage size after ingestion.
- Review Bedrock model usage after evaluation or bulk ingestion.
- Remove local mapping/report files from deploy artifacts.
- Destroy unused Terraform resources when the archive is no longer needed.

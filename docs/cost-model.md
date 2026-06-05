# Cost Model

The default design is for a low-volume, low-maintenance archive. It avoids expensive always-on services unless the operator explicitly adds them.

## Default Cost Drivers

| Component | Default use | Cost behavior |
| --- | --- | --- |
| Cloudflare Pages | Static frontend | Usually low or free-tier friendly for small traffic |
| S3 | Raw PDFs, extracted text, reports, vector bundles | Storage plus request costs |
| Bedrock embeddings | Ingestion and query embeddings | Pay per model call |
| Bedrock chat | RAG answer generation | Pay per model call |
| Local Postgres | Docker Compose for development | No cloud cost |
| Terraform | S3 and IAM only | No ongoing Terraform cost |

## Intentionally Not Provisioned By Default

- OpenSearch
- App Runner
- ECR
- CloudFront
- always-on EC2
- recurring ingestion jobs
- scheduled crawlers

The application includes OpenSearch mapping and reindex support, but Terraform does not create an OpenSearch domain. For a small archive, S3 vector bundles and taxonomy filtering are the cheaper default.

## Cost Controls

- Run ingestion manually instead of on a schedule.
- Reuse extracted chunks and re-tag without full OCR when taxonomy changes.
- Keep OpenSearch disabled until query volume or corpus size justifies it.
- Keep PDF and report artifacts in S3, not a running container filesystem.
- Use short signed URL TTLs.
- Prefer on-demand API hosting if the backend is deployed.
- Keep evaluation scripts manual so they do not create surprise model-call costs.

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

# Security Notes

This project is designed as a private archive with a public static frontend option. It is not a regulated clinical product and does not claim HIPAA, SOC 2, or similar compliance.

## Secrets

Secrets are read from environment variables and are intentionally absent from the repository.

Important values:

- `AWS_REGION`
- `S3_BUCKET`
- `BEDROCK_EMBED_MODEL_ID`
- `BEDROCK_CHAT_MODEL_ID`
- `BEDROCK_FALLBACK_CHAT_MODEL_ID`
- `DATABASE_URL`
- `ADMIN_TOKEN`
- `ADMIN_PASSWORD`
- `OPENSEARCH_ENDPOINT`, if used

Model ids are configuration, not secrets. They still need to be kept consistent with IAM and deployment docs so the runtime can invoke only the intended Bedrock models.

Do not commit `.env`, `.env.local`, Terraform state, local PDFs, generated reports with corpus-sensitive metadata, or AWS credentials.

## IAM

Terraform creates attachable policies rather than broad users or roles:

- `ingestion_policy_arn` for the principal that runs manual ingestion
- `runtime_policy_arn` for an optional AWS-hosted backend runtime

The default infrastructure is intentionally narrow: S3 access for corpus artifacts and Bedrock model calls. Runtime IAM includes the configured embedding model, primary answer model, fallback answer model, and Bedrock inference profiles. OpenSearch permissions are not created by default because OpenSearch is not provisioned by default.

## Network Boundaries

- Cloudflare Pages serves the static frontend and does not need AWS credentials.
- The corpus bucket is private and blocks public ACLs and bucket policies.
- The optional Lambda Function URL is public at the network layer; route-level admin protections live in the FastAPI app.
- CORS is configured separately for local development, hosted frontend origins, and Lambda Function URL behavior.
- Postgres is local by default. A hosted Postgres deployment should be private-networked or otherwise restricted by its provider.
- OpenSearch is not provisioned by this stack. If an external endpoint is used, network access and credentials are the operator's responsibility.

## S3 Data

The corpus bucket is private. It stores:

- raw PDFs
- extracted page JSON and Markdown
- metadata documents
- ingestion and taxonomy reports
- vector bundles

API citations can include signed PDF URLs. Keep signed URL TTL short enough for the intended use case by setting `PRESIGNED_URL_TTL_SECONDS`.

## Admin Endpoints

- `/admin/ingest` requires `ADMIN_TOKEN`.
- `/admin/review` API routes require `ADMIN_PASSWORD`, except for local-only development fallback.
- `ADMIN_TOKEN` and `ADMIN_PASSWORD` are shared-secret controls, not enterprise authentication.

For broader use, replace shared secrets with an identity provider, role-based access, and audit logs.

## Audit And Blast Radius

Current audit evidence is lightweight:

- FastAPI JSON logs can include request ids and error details.
- Ingestion reports record file-level outcomes, checksums, page counts, OCR diagnostics, and S3 artifact keys.
- Taxonomy reports record tagged, untagged, low-confidence, and unmatched terms.
- Database tables include retrieval logs when the structured DB path is enabled.

Blast radius is limited by keeping the public UI static, the corpus bucket private, ingestion manual, OpenSearch optional, and IAM policies scoped to the corpus bucket plus configured Bedrock models. This is not a complete audit trail; production use should add immutable admin events, retention policies, and secret rotation.

## API Controls

Implemented controls:

- CORS allowlist through `CORS_ALLOW_ORIGINS`
- request body size limits
- admin upload size limit
- simple per-client rate limiting
- JSON logs with request ids
- grounded RAG prompt that rejects unsupported answers

Recommended production additions:

- WAF or managed rate limits at the edge
- authentication for private archives
- secret rotation process
- structured audit events for admin actions
- retention policy for retrieval logs
- object lifecycle and backup policies

## Privacy Considerations

The `retrieval_logs` schema can store the original query. For public or sensitive use, decide whether to hash, redact, truncate, or disable query persistence. Health-adjacent questions can contain personal information even when the app is only educational.

## Medical Safety

The assistant is prompted to speak from the archive, cite sources, avoid diagnosis and treatment plans, and advise professional consultation for personal medical decisions. See [safety.md](safety.md).

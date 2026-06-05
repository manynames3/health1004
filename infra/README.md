# Terraform

This Terraform is intentionally low-cost for a low-volume maintenance site.

Default resources:

- One private S3 corpus bucket for raw PDFs, extracted text, metadata, ingestion reports, and vector bundles.
- Two attachable IAM policies: one for manual ingestion and one for an optional API runtime.

Optional API resources when `deploy_api=true`:

- One Lambda zip function for the FastAPI backend.
- One public Lambda Function URL.
- One Lambda execution role.
- One CloudWatch log group with 14-day retention.
- One S3 object for the Lambda package.

It does not create OpenSearch, App Runner, ECR, CloudFront, or any always-on compute. The public frontend stays on Cloudflare Pages. OpenSearch scripts target an existing endpoint only when `OPENSEARCH_ENDPOINT` is configured.

## Bedrock Model Defaults

Terraform defaults match the app's low-cost model strategy:

- primary answer model: `anthropic.claude-haiku-4-5-20251001-v1:0`
- fallback answer model: `amazon.nova-2-lite-v1:0`
- embedding model: `amazon.titan-embed-text-v2:0`

Runtime IAM grants access to the primary answer model, fallback answer model, embedding model, and Bedrock inference profiles. Changing the embedding model requires rebuilding the S3 vector bundle after deployment.

## Apply Storage Only

```bash
terraform init
terraform apply \
  -var="aws_region=us-east-1" \
  -var="bedrock_chat_model_id=anthropic.claude-haiku-4-5-20251001-v1:0" \
  -var="bedrock_fallback_chat_model_id=amazon.nova-2-lite-v1:0" \
  -var="bedrock_embed_model_id=amazon.titan-embed-text-v2:0"
```

## Deploy The Lambda API

From the repo root:

```bash
python scripts/build_lambda_package.py
```

From `infra/`:

```bash
terraform apply \
  -var="deploy_api=true" \
  -var="bedrock_chat_model_id=anthropic.claude-haiku-4-5-20251001-v1:0" \
  -var="bedrock_fallback_chat_model_id=amazon.nova-2-lite-v1:0" \
  -var="bedrock_embed_model_id=amazon.titan-embed-text-v2:0" \
  -var="lambda_package_path=../outputs/health1004-api-lambda.zip"
```

Pass `TF_VAR_admin_token` and `TF_VAR_admin_password` in the environment for admin endpoints.

## Outputs

- `corpus_bucket`
- `ingestion_policy_arn`
- `runtime_policy_arn`
- `api_function_name`, when `deploy_api=true`
- `api_function_url`, when `deploy_api=true`

Attach `ingestion_policy_arn` to the IAM principal that runs `scripts/ingest.py`. When `deploy_api=true`, Terraform creates the Lambda runtime role and attaches the runtime policy automatically.

## Limits

The Lambda Function URL path is suitable for low-volume browse/query traffic and small admin checks. Large browser uploads are constrained by Lambda synchronous payload limits, so bulk PDF ingestion should use the CLI/S3 path or a future direct-to-S3 multipart upload flow.

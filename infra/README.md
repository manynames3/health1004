# Terraform

This Terraform is intentionally low-cost for a low-volume maintenance site. It creates only:

- One private S3 corpus bucket for raw PDFs, extracted text, metadata, ingestion reports, and `vector-index/chunks.json.gz`.
- Two attachable IAM policies: one for manual ingestion and one for an optional AWS-hosted runtime.

It does not create OpenSearch, App Runner, ECR, CloudFront, or any always-on compute. The public frontend is expected to stay on Cloudflare Pages.

## Apply

```bash
terraform init
terraform apply \
  -var="aws_region=us-east-1" \
  -var="bedrock_chat_model_id=anthropic.claude-3-5-sonnet-20241022-v2:0"
```

After apply, attach `ingestion_policy_arn` to the IAM principal that runs `scripts/ingest.py`. If you later host the FastAPI backend on AWS Lambda or another on-demand AWS runtime, attach `runtime_policy_arn` to that runtime role.

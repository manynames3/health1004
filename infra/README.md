# Terraform

This Terraform creates the AWS-native production skeleton:

- S3 corpus bucket for raw PDFs, extracted text, metadata, and ingestion reports.
- OpenSearch Serverless `VECTORSEARCH` collection.
- ECR repository and App Runner service for the FastAPI container.
- IAM roles and data-access policies for Bedrock, S3, and OpenSearch.
- Private S3 bucket plus CloudFront distribution for the static Next.js frontend.

The OpenSearch vector index is intentionally created by `scripts/ingest.py --rebuild-index` so the mapping always matches `OPENSEARCH_VECTOR_DIMENSION`.

## Apply

```bash
terraform init
terraform apply \
  -var="aws_region=us-east-1" \
  -var="bedrock_chat_model_id=anthropic.claude-3-5-sonnet-20241022-v2:0" \
  -var='ingestion_principal_arns=["arn:aws:iam::<account-id>:user/<you>"]'
```

Before creating the App Runner service, push an image tagged `latest` to the output ECR repository, or pass `backend_image_identifier`.

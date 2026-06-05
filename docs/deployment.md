# Deployment

This project separates the public static frontend from the backend and AWS corpus infrastructure.

## Deployed Static Frontend

The current public static frontend is:

[https://health1004.pages.dev](https://health1004.pages.dev)

Build command:

```bash
cd frontend
npm run build
```

Output directory:

```text
frontend/out
```

Cloudflare Pages can deploy this static export from Git or direct upload. Set `NEXT_PUBLIC_API_BASE_URL` in the Pages environment if the frontend should call a hosted API.

## AWS Infrastructure

Terraform creates low-cost storage and IAM resources by default:

```bash
cd infra
terraform init
terraform apply \
  -var="aws_region=us-east-1" \
  -var="bedrock_chat_model_id=<chat-model-id>"
```

Outputs include:

- corpus bucket name
- ingestion policy ARN
- runtime policy ARN

Attach the ingestion policy to the principal that runs `scripts/ingest.py`.

## Lambda API Deployment

The optional Lambda Function URL backend is enabled with `deploy_api=true`:

```bash
python scripts/build_lambda_package.py
cd infra
terraform apply \
  -var="deploy_api=true" \
  -var="bedrock_chat_model_id=amazon.nova-micro-v1:0" \
  -var="lambda_package_path=../outputs/health1004-api-lambda.zip"
```

Pass `TF_VAR_admin_token` and `TF_VAR_admin_password` as environment variables when applying. Terraform creates the Lambda execution role and attaches the runtime policy.

## Backend Runtime

The repo does not prescribe a single hosted backend. Valid low-volume options include:

- local operator-run backend for manual review and ingestion
- AWS Lambda container or zip deployment
- a small on-demand container runtime
- another private runtime reachable by the static frontend

Any hosted backend needs:

- `AWS_REGION`
- `S3_BUCKET`
- `VECTOR_BUNDLE_KEY`
- `VECTOR_DIMENSION`
- `BEDROCK_EMBED_MODEL_ID`
- `BEDROCK_CHAT_MODEL_ID`
- `CORS_ALLOW_ORIGINS`
- `ADMIN_TOKEN`
- `ADMIN_PASSWORD`, if review endpoints are exposed
- `DATABASE_URL`, if structured DB features are enabled

For Cloudflare Pages direct uploads, build the static frontend with:

```bash
NEXT_PUBLIC_API_BASE_URL=<api_function_url_without_trailing_slash> npm run build
```

Then deploy `frontend/out` to Pages.

## Deployment Validation

Before publishing:

```bash
cd backend
PYTHONPATH=. pytest

cd ../frontend
npm run build

cd ../infra
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

After publishing:

```bash
curl -I https://health1004.pages.dev
curl https://<api-host>/health
```

If a backend is not hosted, the static site should still render archive navigation pages, but API-backed query and admin actions will need local or hosted configuration.

## Rollback

- Cloudflare Pages: use a previous deployment.
- Backend: redeploy the previous artifact or container image.
- Terraform: use version-controlled Terraform and state backup practices.
- Data: restore S3 object versions or re-run ingestion from source PDFs.

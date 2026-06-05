# Teardown

Use this checklist to avoid leaving paid resources or sensitive corpus files behind.

## Cloudflare Pages

If the static site is no longer needed, remove the Pages project in the Cloudflare dashboard or disconnect the Git deployment. If you only need rollback, use a previous Pages deployment instead of deleting the project.

## AWS Terraform Resources

Terraform creates S3/IAM resources and, when `deploy_api=true`, Lambda Function URL resources. From `infra/`:

```bash
terraform plan -destroy
terraform destroy
```

If the bucket contains objects, empty or archive the bucket first according to your retention requirements.

Lambda logs are stored in `/aws/lambda/health1004-api` with the configured retention period and are removed by `terraform destroy` when managed by this stack.

## S3 Corpus Artifacts

Expected artifact prefixes:

- `raw-pdfs/`
- `extracted/`
- `metadata/`
- `ingestion-reports/`
- `vector-index/`

If bucket versioning is enabled, remember that deleting current objects may leave previous versions. Remove old versions only when retention requirements allow it.

## Local Development

Stop and remove local Postgres:

```bash
docker compose down -v
```

Remove generated local artifacts when they are not needed:

```bash
rm -f ingestion_report.json
rm -f outputs/taxonomy_report.json outputs/opensearch_mapping.json outputs/reindex_plan.json
```

Do not delete source PDFs unless they are backed up elsewhere.

## Optional OpenSearch

The default Terraform does not create OpenSearch. If you configured an external OpenSearch endpoint manually, delete that domain or index through its own infrastructure owner.

## Secrets

Rotate or delete:

- AWS access keys used for ingestion
- `ADMIN_TOKEN`
- `ADMIN_PASSWORD`
- hosted backend environment variables
- database credentials
- OpenSearch credentials, if used

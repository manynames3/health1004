output "corpus_bucket" {
  description = "Private S3 bucket for PDFs, extracted text, metadata, reports, and the vector bundle."
  value       = aws_s3_bucket.corpus.bucket
}

output "metadata_key" {
  description = "S3 key used by the backend for the document manifest."
  value       = var.metadata_key
}

output "vector_bundle_key" {
  description = "S3 key used by ingestion and retrieval for exact vector search."
  value       = var.vector_bundle_key
}

output "ingestion_policy_arn" {
  description = "Attach this policy to the IAM principal that runs scripts/ingest.py."
  value       = aws_iam_policy.ingestion.arn
}

output "runtime_policy_arn" {
  description = "Attach this policy to the API runtime if hosted on AWS."
  value       = aws_iam_policy.runtime.arn
}

output "api_function_name" {
  description = "Lambda API function name when deploy_api is true."
  value       = var.deploy_api ? aws_lambda_function.api[0].function_name : null
}

output "api_function_url" {
  description = "Public Lambda Function URL for the FastAPI backend when deploy_api is true."
  value       = var.deploy_api ? aws_lambda_function_url.api[0].function_url : null
}

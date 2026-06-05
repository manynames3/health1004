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

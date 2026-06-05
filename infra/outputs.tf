output "corpus_bucket" {
  value = aws_s3_bucket.corpus.bucket
}

output "frontend_bucket" {
  value = aws_s3_bucket.frontend.bucket
}

output "frontend_url" {
  value = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "backend_url" {
  value = aws_apprunner_service.backend.service_url
}

output "backend_ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "opensearch_collection_endpoint" {
  value = aws_opensearchserverless_collection.vector.collection_endpoint
}

output "opensearch_index" {
  value = var.opensearch_index_name
}

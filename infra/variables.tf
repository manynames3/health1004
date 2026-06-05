variable "project_name" {
  description = "Short name used for AWS resource names."
  type        = string
  default     = "health1004"
}

variable "aws_region" {
  description = "AWS Region used for all regional resources and Bedrock runtime calls."
  type        = string
  default     = "us-east-1"
}

variable "corpus_bucket_name" {
  description = "Optional globally unique S3 bucket name for PDFs and extracted artifacts."
  type        = string
  default     = ""
}

variable "bedrock_embed_model_id" {
  description = "Bedrock embedding model id."
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "bedrock_chat_model_id" {
  description = "Primary Bedrock chat model id used by the backend."
  type        = string
  default     = "anthropic.claude-haiku-4-5-20251001-v1:0"
}

variable "bedrock_fallback_chat_model_id" {
  description = "Fallback Bedrock chat model id used when the primary answer model fails."
  type        = string
  default     = "amazon.nova-2-lite-v1:0"
}

variable "metadata_key" {
  description = "S3 key for the document metadata manifest."
  type        = string
  default     = "metadata/documents.json"
}

variable "vector_bundle_key" {
  description = "S3 key for the gzipped exact-search vector bundle."
  type        = string
  default     = "vector-index/chunks.json.gz"
}

variable "taxonomy_vector_bundle_key" {
  description = "S3 key for the taxonomy-enriched vector bundle."
  type        = string
  default     = "vector-index/chunks.taxonomy.json.gz"
}

variable "taxonomy_report_key" {
  description = "S3 key for the taxonomy report."
  type        = string
  default     = "ingestion-reports/taxonomy_report.json"
}

variable "deploy_api" {
  description = "Whether to deploy the low-cost Lambda Function URL API."
  type        = bool
  default     = false
}

variable "lambda_package_path" {
  description = "Path to the prebuilt Lambda zip package. Required when deploy_api is true."
  type        = string
  default     = "../outputs/health1004-api-lambda.zip"
}

variable "lambda_memory_mb" {
  description = "Memory allocated to the API Lambda."
  type        = number
  default     = 1024
}

variable "lambda_timeout_seconds" {
  description = "Timeout for the API Lambda."
  type        = number
  default     = 900
}

variable "lambda_admin_upload_limit_bytes" {
  description = "Request size limit advertised by the Lambda-hosted admin API."
  type        = number
  default     = 5242880
}

variable "frontend_base_url" {
  description = "Public frontend origin."
  type        = string
  default     = "https://health1004.pages.dev"
}

variable "cors_allow_origins" {
  description = "Comma-separated origins allowed to call the API. Use * for Pages direct-upload previews."
  type        = string
  default     = "*"
}

variable "admin_token" {
  description = "Shared secret for admin ingestion endpoints."
  type        = string
  sensitive   = true
  default     = ""
}

variable "admin_password" {
  description = "Shared secret for tag review endpoints."
  type        = string
  sensitive   = true
  default     = ""
}

variable "database_url" {
  description = "Optional Postgres connection string for structured archive state."
  type        = string
  sensitive   = true
  default     = ""
}

variable "min_tag_confidence" {
  description = "Minimum confidence score for deterministic taxonomy tagging."
  type        = number
  default     = 0.65
}

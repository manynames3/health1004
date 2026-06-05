variable "project_name" {
  description = "Short name used for AWS resource names."
  type        = string
  default     = "korean-health-rag"
}

variable "aws_region" {
  description = "AWS Region used for all regional resources and Bedrock runtime calls."
  type        = string
}

variable "corpus_bucket_name" {
  description = "Optional globally unique S3 bucket name for PDFs and extracted artifacts."
  type        = string
  default     = ""
}

variable "frontend_bucket_name" {
  description = "Optional globally unique S3 bucket name for static frontend assets."
  type        = string
  default     = ""
}

variable "opensearch_collection_name" {
  description = "OpenSearch Serverless vector collection name."
  type        = string
  default     = "korean-health-rag"
}

variable "opensearch_index_name" {
  description = "OpenSearch index name created by scripts/ingest.py --rebuild-index."
  type        = string
  default     = "korean-health-chunks"
}

variable "opensearch_vector_dimension" {
  description = "Embedding vector dimension. Cohere Embed Multilingual v3 is 1024."
  type        = number
  default     = 1024
}

variable "bedrock_embed_model_id" {
  description = "Bedrock embedding model id."
  type        = string
  default     = "cohere.embed-multilingual-v3"
}

variable "bedrock_chat_model_id" {
  description = "Bedrock chat model id used by the backend."
  type        = string
}

variable "frontend_base_url" {
  description = "Public frontend URL. Leave blank before CloudFront exists; update App Runner env after deployment if needed."
  type        = string
  default     = ""
}

variable "backend_image_identifier" {
  description = "Optional ECR image identifier for App Runner. Defaults to the created ECR repo with :latest."
  type        = string
  default     = ""
}

variable "ingestion_principal_arns" {
  description = "IAM principal ARNs allowed to create indexes and write documents during local manual ingestion."
  type        = list(string)
  default     = []
}

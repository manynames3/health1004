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
  default     = "cohere.embed-multilingual-v3"
}

variable "bedrock_chat_model_id" {
  description = "Bedrock chat model id used by the backend. Leave as * for broad attachable policy output, or set a specific model id for tighter IAM."
  type        = string
  default     = "*"
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

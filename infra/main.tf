data "aws_caller_identity" "current" {}

resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  name_prefix        = lower(replace(var.project_name, "_", "-"))
  corpus_bucket_name = var.corpus_bucket_name != "" ? var.corpus_bucket_name : "${local.name_prefix}-corpus-${random_id.suffix.hex}"
}

resource "aws_s3_bucket" "corpus" {
  bucket = local.corpus_bucket_name

  tags = {
    Project = var.project_name
    Purpose = "korean-pdf-rag-corpus"
  }
}

resource "aws_s3_bucket_versioning" "corpus" {
  bucket = aws_s3_bucket.corpus.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "corpus" {
  bucket = aws_s3_bucket.corpus.id

  depends_on = [aws_s3_bucket_versioning.corpus]

  rule {
    id     = "keep-storage-small"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "corpus" {
  bucket = aws_s3_bucket.corpus.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "corpus" {
  bucket                  = aws_s3_bucket.corpus.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

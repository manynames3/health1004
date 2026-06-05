locals {
  api_function_name = "${local.name_prefix}-api"
  cors_origins      = [for origin in split(",", var.cors_allow_origins) : trimspace(origin) if trimspace(origin) != ""]
}

data "aws_iam_policy_document" "api_lambda_assume_role" {
  count = var.deploy_api ? 1 : 0

  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "api_lambda" {
  count = var.deploy_api ? 1 : 0

  name               = "${local.api_function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.api_lambda_assume_role[0].json

  tags = {
    Project = var.project_name
    Purpose = "health1004-api-runtime"
  }
}

resource "aws_iam_role_policy_attachment" "api_lambda_basic" {
  count = var.deploy_api ? 1 : 0

  role       = aws_iam_role.api_lambda[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "api_lambda_runtime" {
  count = var.deploy_api ? 1 : 0

  role       = aws_iam_role.api_lambda[0].name
  policy_arn = aws_iam_policy.runtime.arn
}

resource "aws_s3_object" "api_lambda_package" {
  count = var.deploy_api ? 1 : 0

  bucket       = aws_s3_bucket.corpus.bucket
  key          = "deployments/${local.api_function_name}-${filemd5(var.lambda_package_path)}.zip"
  source       = var.lambda_package_path
  etag         = filemd5(var.lambda_package_path)
  content_type = "application/zip"
}

resource "aws_cloudwatch_log_group" "api_lambda" {
  count = var.deploy_api ? 1 : 0

  name              = "/aws/lambda/${local.api_function_name}"
  retention_in_days = 14

  tags = {
    Project = var.project_name
    Purpose = "health1004-api-logs"
  }
}

resource "aws_lambda_function" "api" {
  count = var.deploy_api ? 1 : 0

  function_name    = local.api_function_name
  role             = aws_iam_role.api_lambda[0].arn
  package_type     = "Zip"
  runtime          = "python3.12"
  architectures    = ["x86_64"]
  handler          = "app.lambda_handler.handler"
  s3_bucket        = aws_s3_object.api_lambda_package[0].bucket
  s3_key           = aws_s3_object.api_lambda_package[0].key
  source_code_hash = filebase64sha256(var.lambda_package_path)
  memory_size      = var.lambda_memory_mb
  timeout          = var.lambda_timeout_seconds

  environment {
    variables = {
      S3_BUCKET                  = aws_s3_bucket.corpus.bucket
      VECTOR_BUNDLE_KEY          = var.vector_bundle_key
      VECTOR_DIMENSION           = "1024"
      TAXONOMY_VECTOR_BUNDLE_KEY = var.taxonomy_vector_bundle_key
      TAXONOMY_REPORT_KEY        = var.taxonomy_report_key
      DATABASE_URL               = var.database_url
      BEDROCK_EMBED_MODEL_ID     = var.bedrock_embed_model_id
      BEDROCK_CHAT_MODEL_ID      = var.bedrock_chat_model_id
      FRONTEND_BASE_URL          = var.frontend_base_url
      CORS_ALLOW_ORIGINS         = var.cors_allow_origins
      METADATA_KEY               = var.metadata_key
      EXTRACTED_PREFIX           = "extracted/"
      REPORTS_PREFIX             = "ingestion-reports/"
      PRESIGNED_URL_TTL_SECONDS  = "3600"
      REQUEST_BODY_LIMIT_BYTES   = "16384"
      ADMIN_UPLOAD_LIMIT_BYTES   = tostring(var.lambda_admin_upload_limit_bytes)
      ADMIN_TOKEN                = var.admin_token
      ADMIN_PASSWORD             = var.admin_password
      TAXONOMY_SEED_PATH         = "data/taxonomy.seed.yaml"
      ENABLE_LLM_TAGGING         = "false"
      ENABLE_NORI_ANALYZER       = "false"
      OPENSEARCH_USE_HYBRID      = "true"
      OPENSEARCH_ENDPOINT        = ""
      OPENSEARCH_INDEX           = "health1004-passages"
      MIN_TAG_CONFIDENCE         = tostring(var.min_tag_confidence)
      RATE_LIMIT_PER_MINUTE      = "30"
      LOG_LEVEL                  = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.api_lambda,
    aws_iam_role_policy_attachment.api_lambda_basic,
    aws_iam_role_policy_attachment.api_lambda_runtime,
  ]

  tags = {
    Project = var.project_name
    Purpose = "health1004-api-runtime"
  }
}

resource "aws_lambda_function_url" "api" {
  count = var.deploy_api ? 1 : 0

  function_name      = aws_lambda_function.api[0].function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_headers     = ["*"]
    allow_methods     = ["*"]
    allow_origins     = local.cors_origins
    max_age           = 3600
  }
}

locals {
  bedrock_embed_model_arn = "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_embed_model_id}"
  bedrock_chat_model_arn  = "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_chat_model_id}"
  bedrock_profile_arn     = "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/*"
}

data "aws_iam_policy_document" "ingestion" {
  statement {
    sid    = "ListCorpusBucket"
    effect = "Allow"
    actions = [
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.corpus.arn
    ]
  }

  statement {
    sid    = "WriteCorpusArtifacts"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = [
      "${aws_s3_bucket.corpus.arn}/*"
    ]
  }

  statement {
    sid    = "InvokeEmbeddingModel"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel"
    ]
    resources = [
      local.bedrock_embed_model_arn
    ]
  }
}

resource "aws_iam_policy" "ingestion" {
  name        = "${local.name_prefix}-ingestion"
  description = "Manual ingestion access for the ${var.project_name} Korean PDF corpus."
  policy      = data.aws_iam_policy_document.ingestion.json
}

data "aws_iam_policy_document" "runtime" {
  statement {
    sid    = "ListCorpusBucket"
    effect = "Allow"
    actions = [
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.corpus.arn
    ]
  }

  statement {
    sid    = "ReadCorpusArtifacts"
    effect = "Allow"
    actions = [
      "s3:GetObject"
    ]
    resources = [
      "${aws_s3_bucket.corpus.arn}/*"
    ]
  }

  statement {
    sid    = "InvokeAnswerModels"
    effect = "Allow"
    actions = [
      "bedrock:Converse",
      "bedrock:InvokeModel"
    ]
    resources = [
      local.bedrock_embed_model_arn,
      local.bedrock_chat_model_arn,
      local.bedrock_profile_arn
    ]
  }
}

resource "aws_iam_policy" "runtime" {
  name        = "${local.name_prefix}-runtime"
  description = "Runtime read and Bedrock access for the ${var.project_name} Korean PDF RAG API."
  policy      = data.aws_iam_policy_document.runtime.json
}

data "aws_iam_policy_document" "apprunner_task_assume" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["tasks.apprunner.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "backend_task" {
  name               = "${local.name_prefix}-backend-task"
  assume_role_policy = data.aws_iam_policy_document.apprunner_task_assume.json
}

data "aws_iam_policy_document" "backend_task" {
  statement {
    sid    = "ReadCorpusArtifacts"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.corpus.arn,
      "${aws_s3_bucket.corpus.arn}/*"
    ]
  }

  statement {
    sid    = "InvokeConfiguredBedrockModels"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:Converse"
    ]
    resources = [
      "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_embed_model_id}",
      "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_chat_model_id}",
      "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/*"
    ]
  }

  statement {
    sid    = "OpenSearchServerlessApi"
    effect = "Allow"
    actions = [
      "aoss:APIAccessAll"
    ]
    resources = [aws_opensearchserverless_collection.vector.arn]
  }
}

resource "aws_iam_policy" "backend_task" {
  name   = "${local.name_prefix}-backend-task"
  policy = data.aws_iam_policy_document.backend_task.json
}

resource "aws_iam_role_policy_attachment" "backend_task" {
  role       = aws_iam_role.backend_task.name
  policy_arn = aws_iam_policy.backend_task.arn
}

data "aws_iam_policy_document" "apprunner_ecr_assume" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["build.apprunner.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "apprunner_ecr_access" {
  name               = "${local.name_prefix}-apprunner-ecr"
  assume_role_policy = data.aws_iam_policy_document.apprunner_ecr_assume.json
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr_access" {
  role       = aws_iam_role.apprunner_ecr_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

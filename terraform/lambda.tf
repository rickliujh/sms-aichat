locals {
  lambda_function_name           = "sms-aichat-webhook"
  lambda_function_log_level      = "DEBUG"
  aws_region                     = "us-east-1"
  aws_ssm_name_hgf_key           = "/sms-chat/hgf_key"
  aws_ssm_name_twilio_accountsid = "/sms-chat/twilio_accountsid"
  aws_ssm_name_twilio_token      = "/sms-chat/twilio_token"
}

# Lambda
# TODO: should be public
data "aws_iam_policy_document" "chat_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "iam_for_chat" {
  name               = "iam_for_lambda"
  assume_role_policy = data.aws_iam_policy_document.chat_assume_role.json
  tags               = local.tags
}

data "aws_ssm_parameter" "hgf_key" {
  name = local.aws_ssm_name_hgf_key
}

data "aws_ssm_parameter" "twilio_accountsid" {
  name = local.aws_ssm_name_twilio_accountsid
}

data "aws_ssm_parameter" "twilio_token" {
  name = local.aws_ssm_name_twilio_token
}

resource "aws_lambda_function" "chat" {
  function_name = local.lambda_function_name
  role          = aws_iam_role.iam_for_chat.arn
  image_uri     = "${aws_ecr_repository.chat.repository_url}:${var.image_tag}"
  package_type  = "Image"

  logging_config {
    log_format            = "JSON"
    application_log_level = local.lambda_function_log_level
  }

  environment {
    variables = {
      POWERTOOLS_LOG_LEVEL = local.lambda_function_log_level
      HGF_KEY              = data.aws_ssm_parameter.hgf_key.value
      TWILIO_ACCOUNTSID    = data.aws_ssm_parameter.twilio_accountsid.value
      TWILIO_TOKEN         = data.aws_ssm_parameter.twilio_token.value
      LAMBDA_URI           = aws_lambda_function_url.chat_lambda_pub.function_url
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.chat_logs,
    aws_cloudwatch_log_group.chat,
    aws_ecr_repository.chat,
  ]

  tags = local.tags
}

resource "aws_lambda_function_url" "chat_lambda_pub" {
  function_name      = local.lambda_function_name
  authorization_type = "NONE"
}

resource "aws_lambda_permission" "chat_public_access" {
  statement_id  = "AllowPublicAccess"
  action        = "lambda:InvokeFunction"
  function_name = local.lambda_function_name
  principal     = "*"
}

resource "aws_cloudwatch_log_group" "chat" {
  name              = "/aws/lambda/${local.lambda_function_name}"
  retention_in_days = 14

  tags = local.tags
}

data "aws_iam_policy_document" "chat_logging" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_policy" "chat_logging" {
  name        = "sms_aichat_logging"
  path        = "/"
  description = "IAM policy for logging from a lambda"
  policy      = data.aws_iam_policy_document.chat_logging.json

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "chat_logs" {
  role       = aws_iam_role.iam_for_chat.name
  policy_arn = aws_iam_policy.chat_logging.arn
}


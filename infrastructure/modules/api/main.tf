# The FastAPI app as one Lambda, exposed through a function URL that only CloudFront calls
# (docs/spec.md, 4.1). A function URL instead of API Gateway because it's free forever,
# whereas API Gateway's free allowance is 12 months / sign-up credits only.

# --- Lambda -------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.name_prefix}-api"
  retention_in_days = var.log_retention_days
}

resource "aws_iam_role" "lambda" {
  name = "${var.name_prefix}-api"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# Least privilege: only the item operations the app performs, only on its own tables.
resource "aws_iam_role_policy" "lambda" {
  name = "app"
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Tables"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:BatchWriteItem",
        ]
        Resource = [
          var.polls_table.arn,
          "${var.polls_table.arn}/index/admin_token_hash-index",
          var.votes_table.arn,
        ]
      },
      {
        Sid      = "Logs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.lambda.arn}:*"
      },
    ]
  })
}

resource "aws_lambda_function" "api" {
  function_name    = "${var.name_prefix}-api"
  role             = aws_iam_role.lambda.arn
  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)
  handler          = "lambda_handler.handler"
  runtime          = "python3.13"
  architectures    = ["arm64"]
  memory_size      = 512
  timeout          = 10

  environment {
    variables = {
      APP_URL              = var.app_url
      POLLS_TABLE          = var.polls_table.name
      VOTES_TABLE          = var.votes_table.name
      CORS_ORIGINS         = "" # same origin via CloudFront; no CORS in production
      CLIENT_IP_HEADER     = "CloudFront-Viewer-Address"
      ORIGIN_VERIFY_SECRET = var.origin_verify_secret
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.lambda.name
  }

  depends_on = [aws_iam_role_policy.lambda]
}

# --- Function URL -------------------------------------------------------------

# Public (auth NONE) because CloudFront calls it as a plain HTTPS origin. The app rejects
# any request without CloudFront's X-Origin-Verify secret, so calling it directly gets 403.
# With NONE, the provider adds the lambda:InvokeFunctionUrl and lambda:InvokeFunction
# (InvokedViaFunctionUrl) permissions AWS requires for new function URLs.
resource "aws_lambda_function_url" "api" {
  function_name      = aws_lambda_function.api.function_name
  authorization_type = "NONE"
}

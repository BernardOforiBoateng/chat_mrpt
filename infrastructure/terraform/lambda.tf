# Lambda Functions Configuration for ChatMRPT

# Lambda execution role
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_execution.name
}

# Lambda VPC access policy (if needed)
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = aws_iam_role.lambda_execution.name
}

# Custom policy for Lambda functions
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy-${var.environment}"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data.arn,
          "${aws_s3_bucket.data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.users.arn,
          aws_dynamodb_table.analyses.arn,
          aws_dynamodb_table.sessions.arn,
          aws_dynamodb_table.audit_log.arn,
          "${aws_dynamodb_table.users.arn}/index/*",
          "${aws_dynamodb_table.analyses.arn}/index/*",
          "${aws_dynamodb_table.sessions.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminGetUser",
          "cognito-idp:AdminAddUserToGroup",
          "cognito-idp:AdminRemoveUserFromGroup"
        ]
        Resource = aws_cognito_user_pool.main.arn
      },
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = "arn:aws:states:${var.aws_region}:${data.aws_caller_identity.current.account_id}:stateMachine:*"
      },
      {
        Effect = "Allow"
        Action = [
          "execute-api:ManageConnections"
        ]
        Resource = "arn:aws:execute-api:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${aws_apigatewayv2_api.websocket.id}/*"
      }
    ]
  })
}

# Lambda Layer for shared dependencies
resource "aws_lambda_layer_version" "shared_deps" {
  filename            = "${path.module}/../lambdas/layers/shared_deps.zip"
  layer_name          = "${var.project_name}-shared-deps-${var.environment}"
  compatible_runtimes = ["python3.10", "python3.11"]
  description         = "Shared dependencies for Lambda functions"
}

# ==================== Auth Lambda Functions ====================

# Pre-signup Lambda
resource "aws_lambda_function" "pre_signup" {
  filename         = "${path.module}/../lambdas/auth/dist/pre_signup.zip"
  function_name    = "${var.project_name}-pre-signup-${var.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "pre_signup.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/auth/dist/pre_signup.zip")
  runtime         = "python3.10"
  timeout         = 10
  memory_size     = 128

  environment {
    variables = {
      ENVIRONMENT = var.environment
      USERS_TABLE = aws_dynamodb_table.users.name
    }
  }

  layers = [aws_lambda_layer_version.shared_deps.arn]
}

# Post-confirmation Lambda
resource "aws_lambda_function" "post_confirmation" {
  filename         = "${path.module}/../lambdas/auth/dist/post_confirmation.zip"
  function_name    = "${var.project_name}-post-confirmation-${var.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "post_confirmation.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/auth/dist/post_confirmation.zip")
  runtime         = "python3.10"
  timeout         = 10
  memory_size     = 128

  environment {
    variables = {
      ENVIRONMENT = var.environment
      USERS_TABLE = aws_dynamodb_table.users.name
    }
  }

  layers = [aws_lambda_layer_version.shared_deps.arn]
}

# Pre-authentication Lambda
resource "aws_lambda_function" "pre_authentication" {
  filename         = "${path.module}/../lambdas/auth/dist/pre_authentication.zip"
  function_name    = "${var.project_name}-pre-authentication-${var.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "pre_authentication.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/auth/dist/pre_authentication.zip")
  runtime         = "python3.10"
  timeout         = 10
  memory_size     = 128

  environment {
    variables = {
      ENVIRONMENT = var.environment
      USERS_TABLE = aws_dynamodb_table.users.name
      AUDIT_TABLE = aws_dynamodb_table.audit_log.name
    }
  }

  layers = [aws_lambda_layer_version.shared_deps.arn]
}

# ==================== Core Lambda Functions ====================

# Analysis Lambda
resource "aws_lambda_function" "analysis" {
  filename         = "${path.module}/../lambdas/analysis/dist/handler.zip"
  function_name    = "${var.project_name}-analysis-${var.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/analysis/dist/handler.zip")
  runtime         = "python3.10"
  timeout         = 300  # 5 minutes
  memory_size     = 1024

  environment {
    variables = {
      ENVIRONMENT     = var.environment
      DATA_BUCKET     = aws_s3_bucket.data.id
      ANALYSES_TABLE  = aws_dynamodb_table.analyses.name
      SESSIONS_TABLE  = aws_dynamodb_table.sessions.name
    }
  }

  layers = [aws_lambda_layer_version.shared_deps.arn]
}

# Data Processing Lambda
resource "aws_lambda_function" "data_processing" {
  filename         = "${path.module}/../lambdas/data_processing/dist/handler.zip"
  function_name    = "${var.project_name}-data-processing-${var.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/data_processing/dist/handler.zip")
  runtime         = "python3.10"
  timeout         = 300  # 5 minutes
  memory_size     = 2048  # More memory for data processing

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      DATA_BUCKET    = aws_s3_bucket.data.id
      SESSIONS_TABLE = aws_dynamodb_table.sessions.name
    }
  }

  layers = [aws_lambda_layer_version.shared_deps.arn]
}

# Visualization Lambda
resource "aws_lambda_function" "visualization" {
  filename         = "${path.module}/../lambdas/visualization/dist/handler.zip"
  function_name    = "${var.project_name}-visualization-${var.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/visualization/dist/handler.zip")
  runtime         = "python3.10"
  timeout         = 300  # 5 minutes
  memory_size     = 2048  # More memory for visualization generation

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      DATA_BUCKET    = aws_s3_bucket.data.id
      ANALYSES_TABLE = aws_dynamodb_table.analyses.name
    }
  }

  layers = [aws_lambda_layer_version.shared_deps.arn]
}

# Reports Lambda
resource "aws_lambda_function" "reports" {
  filename         = "${path.module}/../lambdas/reports/dist/handler.zip"
  function_name    = "${var.project_name}-reports-${var.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/reports/dist/handler.zip")
  runtime         = "python3.10"
  timeout         = 300  # 5 minutes
  memory_size     = 1024

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      DATA_BUCKET    = aws_s3_bucket.data.id
      ANALYSES_TABLE = aws_dynamodb_table.analyses.name
    }
  }

  layers = [aws_lambda_layer_version.shared_deps.arn]
}

# ==================== WebSocket Lambda Functions ====================

# WebSocket Connect Lambda
resource "aws_lambda_function" "websocket_connect" {
  filename         = "${path.module}/../lambdas/websocket/dist/connect.zip"
  function_name    = "${var.project_name}-ws-connect-${var.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "connect.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/websocket/dist/connect.zip")
  runtime         = "python3.10"
  timeout         = 10
  memory_size     = 128

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      SESSIONS_TABLE = aws_dynamodb_table.sessions.name
    }
  }
}

# WebSocket Disconnect Lambda
resource "aws_lambda_function" "websocket_disconnect" {
  filename         = "${path.module}/../lambdas/websocket/dist/disconnect.zip"
  function_name    = "${var.project_name}-ws-disconnect-${var.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "disconnect.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/websocket/dist/disconnect.zip")
  runtime         = "python3.10"
  timeout         = 10
  memory_size     = 128

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      SESSIONS_TABLE = aws_dynamodb_table.sessions.name
    }
  }
}

# WebSocket Message Lambda
resource "aws_lambda_function" "websocket_message" {
  filename         = "${path.module}/../lambdas/websocket/dist/message.zip"
  function_name    = "${var.project_name}-ws-message-${var.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "message.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/websocket/dist/message.zip")
  runtime         = "python3.10"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      SESSIONS_TABLE = aws_dynamodb_table.sessions.name
      WS_ENDPOINT    = "https://${aws_apigatewayv2_api.websocket.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}"
    }
  }
}

# ==================== S3 Event Triggers ====================

# S3 event notification for data uploads
resource "aws_s3_bucket_notification" "data_upload" {
  bucket = aws_s3_bucket.data.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.data_processing.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
    filter_suffix       = ".csv"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.data_processing.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
    filter_suffix       = ".xlsx"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.data_processing.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
    filter_suffix       = ".zip"
  }

  depends_on = [aws_lambda_permission.s3_invoke]
}

# Lambda permission for S3
resource "aws_lambda_permission" "s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_processing.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data.arn
}

# ==================== CloudWatch Log Groups ====================

resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = {
    pre_signup        = aws_lambda_function.pre_signup.function_name
    post_confirmation = aws_lambda_function.post_confirmation.function_name
    pre_authentication = aws_lambda_function.pre_authentication.function_name
    analysis          = aws_lambda_function.analysis.function_name
    data_processing   = aws_lambda_function.data_processing.function_name
    visualization     = aws_lambda_function.visualization.function_name
    reports           = aws_lambda_function.reports.function_name
    ws_connect        = aws_lambda_function.websocket_connect.function_name
    ws_disconnect     = aws_lambda_function.websocket_disconnect.function_name
    ws_message        = aws_lambda_function.websocket_message.function_name
  }

  name              = "/aws/lambda/${each.value}"
  retention_in_days = 30
}

# ==================== Outputs ====================

output "lambda_function_arns" {
  value = {
    pre_signup        = aws_lambda_function.pre_signup.arn
    post_confirmation = aws_lambda_function.post_confirmation.arn
    pre_authentication = aws_lambda_function.pre_authentication.arn
    analysis          = aws_lambda_function.analysis.arn
    data_processing   = aws_lambda_function.data_processing.arn
    visualization     = aws_lambda_function.visualization.arn
    reports           = aws_lambda_function.reports.arn
  }
}
# CloudWatch Monitoring and Alarms for ChatMRPT

# SNS Topic for Alarms
resource "aws_sns_topic" "alarms" {
  name = "${var.project_name}-alarms-${var.environment}"

  tags = {
    Name        = "${var.project_name}-alarms-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "alarm_email" {
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# ==================== Lambda Alarms ====================

# Lambda Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = {
    analysis        = aws_lambda_function.analysis.function_name
    data_processing = aws_lambda_function.data_processing.function_name
    visualization   = aws_lambda_function.visualization.function_name
    reports         = aws_lambda_function.reports.function_name
  }

  alarm_name          = "${each.key}-lambda-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "Errors"
  namespace          = "AWS/Lambda"
  period             = "300"
  statistic          = "Sum"
  threshold          = "10"
  alarm_description  = "Lambda function ${each.key} error rate is too high"

  dimensions = {
    FunctionName = each.value
  }

  alarm_actions = [aws_sns_topic.alarms.arn]

  tags = {
    Function    = each.key
    Environment = var.environment
  }
}

# Lambda Throttles Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  for_each = {
    analysis        = aws_lambda_function.analysis.function_name
    data_processing = aws_lambda_function.data_processing.function_name
  }

  alarm_name          = "${each.key}-lambda-throttles-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name        = "Throttles"
  namespace          = "AWS/Lambda"
  period             = "300"
  statistic          = "Sum"
  threshold          = "5"
  alarm_description  = "Lambda function ${each.key} is being throttled"

  dimensions = {
    FunctionName = each.value
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# Lambda Duration Alarm (for timeout detection)
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  for_each = {
    analysis        = { name = aws_lambda_function.analysis.function_name, threshold = 250000 }
    data_processing = { name = aws_lambda_function.data_processing.function_name, threshold = 250000 }
    visualization   = { name = aws_lambda_function.visualization.function_name, threshold = 250000 }
  }

  alarm_name          = "${split("_", each.key)[0]}-lambda-duration-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "Duration"
  namespace          = "AWS/Lambda"
  period             = "300"
  statistic          = "Average"
  threshold          = each.value.threshold
  alarm_description  = "Lambda function ${each.key} is taking too long"

  dimensions = {
    FunctionName = each.value.name
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# Lambda Concurrent Executions Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_concurrent_executions" {
  alarm_name          = "lambda-concurrent-executions-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "ConcurrentExecutions"
  namespace          = "AWS/Lambda"
  period             = "60"
  statistic          = "Maximum"
  threshold          = "900"  # 90% of default 1000 limit
  alarm_description  = "Lambda concurrent executions approaching limit"

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# ==================== DynamoDB Alarms ====================

# DynamoDB User Errors
resource "aws_cloudwatch_metric_alarm" "dynamodb_user_errors" {
  for_each = {
    users     = aws_dynamodb_table.users.name
    analyses  = aws_dynamodb_table.analyses.name
    sessions  = aws_dynamodb_table.sessions.name
  }

  alarm_name          = "${each.key}-dynamodb-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "UserErrors"
  namespace          = "AWS/DynamoDB"
  period             = "300"
  statistic          = "Sum"
  threshold          = "10"
  alarm_description  = "DynamoDB table ${each.key} has user errors"

  dimensions = {
    TableName = each.value
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# DynamoDB Throttled Requests
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttles" {
  for_each = {
    users     = aws_dynamodb_table.users.name
    analyses  = aws_dynamodb_table.analyses.name
  }

  alarm_name          = "${each.key}-dynamodb-throttles-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "ReadThrottleEvents"
  namespace          = "AWS/DynamoDB"
  period             = "300"
  statistic          = "Sum"
  threshold          = "5"
  alarm_description  = "DynamoDB table ${each.key} is being throttled"

  dimensions = {
    TableName = each.value
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# ==================== API Gateway Alarms ====================

# API Gateway 4xx Errors
resource "aws_cloudwatch_metric_alarm" "api_gateway_4xx" {
  alarm_name          = "api-gateway-4xx-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "4XXError"
  namespace          = "AWS/ApiGateway"
  period             = "300"
  statistic          = "Sum"
  threshold          = "50"
  alarm_description  = "API Gateway 4xx errors are high"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.main.name
    Stage   = var.environment
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# API Gateway 5xx Errors
resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx" {
  alarm_name          = "api-gateway-5xx-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name        = "5XXError"
  namespace          = "AWS/ApiGateway"
  period             = "60"
  statistic          = "Sum"
  threshold          = "10"
  alarm_description  = "API Gateway 5xx errors detected"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.main.name
    Stage   = var.environment
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# API Gateway Latency
resource "aws_cloudwatch_metric_alarm" "api_gateway_latency" {
  alarm_name          = "api-gateway-latency-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "Latency"
  namespace          = "AWS/ApiGateway"
  period             = "300"
  statistic          = "Average"
  threshold          = "1000"  # 1 second
  alarm_description  = "API Gateway latency is high"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.main.name
    Stage   = var.environment
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# ==================== Step Functions Alarms ====================

# Step Functions Failed Executions
resource "aws_cloudwatch_metric_alarm" "step_functions_failed" {
  alarm_name          = "step-functions-failed-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name        = "ExecutionsFailed"
  namespace          = "AWS/States"
  period             = "300"
  statistic          = "Sum"
  threshold          = "3"
  alarm_description  = "Step Functions executions are failing"

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.composite_scoring.arn
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# Step Functions Execution Time
resource "aws_cloudwatch_metric_alarm" "step_functions_duration" {
  alarm_name          = "step-functions-duration-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "ExecutionTime"
  namespace          = "AWS/States"
  period             = "300"
  statistic          = "Average"
  threshold          = "600000"  # 10 minutes in milliseconds
  alarm_description  = "Step Functions executions taking too long"

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.composite_scoring.arn
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# ==================== S3 Alarms ====================

# S3 Bucket Size Alarm
resource "aws_cloudwatch_metric_alarm" "s3_bucket_size" {
  alarm_name          = "s3-bucket-size-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name        = "BucketSizeBytes"
  namespace          = "AWS/S3"
  period             = "86400"  # Daily
  statistic          = "Average"
  threshold          = "107374182400"  # 100 GB in bytes
  alarm_description  = "S3 bucket size exceeds 100GB"

  dimensions = {
    BucketName = aws_s3_bucket.data.id
    StorageType = "StandardStorage"
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# ==================== CloudWatch Dashboard ====================

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-dashboard-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          title   = "Lambda Invocations"
          metrics = [
            ["AWS/Lambda", "Invocations", { stat = "Sum", label = "Analysis" }, { "FunctionName" = aws_lambda_function.analysis.function_name }],
            [".", ".", { stat = "Sum", label = "Data Processing" }, { "FunctionName" = aws_lambda_function.data_processing.function_name }],
            [".", ".", { stat = "Sum", label = "Visualization" }, { "FunctionName" = aws_lambda_function.visualization.function_name }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          yAxis = {
            left = {
              min = 0
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          title   = "Lambda Errors"
          metrics = [
            ["AWS/Lambda", "Errors", { stat = "Sum" }, { "FunctionName" = aws_lambda_function.analysis.function_name }],
            [".", ".", { stat = "Sum" }, { "FunctionName" = aws_lambda_function.data_processing.function_name }],
            [".", ".", { stat = "Sum" }, { "FunctionName" = aws_lambda_function.visualization.function_name }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
        }
      },
      {
        type = "metric"
        properties = {
          title   = "API Gateway Requests"
          metrics = [
            ["AWS/ApiGateway", "Count", { stat = "Sum", label = "Total Requests" }, { "ApiName" = aws_api_gateway_rest_api.main.name, "Stage" = var.environment }],
            [".", "4XXError", { stat = "Sum", label = "4xx Errors" }, { "ApiName" = aws_api_gateway_rest_api.main.name, "Stage" = var.environment }],
            [".", "5XXError", { stat = "Sum", label = "5xx Errors" }, { "ApiName" = aws_api_gateway_rest_api.main.name, "Stage" = var.environment }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
        }
      },
      {
        type = "metric"
        properties = {
          title   = "DynamoDB Consumed Capacity"
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", { stat = "Sum" }, { "TableName" = aws_dynamodb_table.users.name }],
            [".", "ConsumedWriteCapacityUnits", { stat = "Sum" }, { "TableName" = aws_dynamodb_table.users.name }],
            [".", "ConsumedReadCapacityUnits", { stat = "Sum" }, { "TableName" = aws_dynamodb_table.analyses.name }],
            [".", "ConsumedWriteCapacityUnits", { stat = "Sum" }, { "TableName" = aws_dynamodb_table.analyses.name }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
        }
      },
      {
        type = "metric"
        properties = {
          title   = "Step Functions Executions"
          metrics = [
            ["AWS/States", "ExecutionsStarted", { stat = "Sum", label = "Started" }, { "StateMachineArn" = aws_sfn_state_machine.composite_scoring.arn }],
            [".", "ExecutionsSucceeded", { stat = "Sum", label = "Succeeded" }, { "StateMachineArn" = aws_sfn_state_machine.composite_scoring.arn }],
            [".", "ExecutionsFailed", { stat = "Sum", label = "Failed" }, { "StateMachineArn" = aws_sfn_state_machine.composite_scoring.arn }]
          ]
          period = 3600
          stat   = "Sum"
          region = var.aws_region
        }
      },
      {
        type = "log"
        properties = {
          title  = "Recent Lambda Errors"
          query  = "SOURCE '/aws/lambda/${aws_lambda_function.analysis.function_name}' | SOURCE '/aws/lambda/${aws_lambda_function.data_processing.function_name}' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20"
          region = var.aws_region
        }
      }
    ]
  })
}

# ==================== Variables ====================

variable "alarm_email" {
  description = "Email address for CloudWatch alarms"
  type        = string
  default     = "ops@chatmrpt.com"
}

variable "enable_waf" {
  description = "Enable WAF for CloudFront"
  type        = bool
  default     = false
}

# ==================== Outputs ====================

output "dashboard_url" {
  value = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "sns_topic_arn" {
  value = aws_sns_topic.alarms.arn
}
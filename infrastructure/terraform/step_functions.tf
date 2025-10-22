# Step Functions for orchestrating analysis workflows

# IAM Role for Step Functions
resource "aws_iam_role" "step_functions" {
  name = "${var.project_name}-step-functions-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

# Step Functions policy
resource "aws_iam_role_policy" "step_functions" {
  name = "${var.project_name}-step-functions-policy-${var.environment}"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.analysis.arn,
          aws_lambda_function.data_processing.arn,
          aws_lambda_function.visualization.arn,
          aws_lambda_function.reports.arn,
          "${aws_lambda_function.analysis.arn}:*",
          "${aws_lambda_function.data_processing.arn}:*",
          "${aws_lambda_function.visualization.arn}:*",
          "${aws_lambda_function.reports.arn}:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = [
          aws_dynamodb_table.analyses.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# Composite Scoring Workflow
resource "aws_sfn_state_machine" "composite_scoring" {
  name     = "${var.project_name}-composite-scoring-${var.environment}"
  role_arn = aws_iam_role.step_functions.arn

  definition = jsonencode({
    Comment = "Composite scoring analysis workflow"
    StartAt = "ValidateInput"
    States = {
      ValidateInput = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.data_processing.arn
          Payload = {
            "action" = "validate_data"
            "session_id.$" = "$.session_id"
            "analysis_id.$" = "$.analysis_id"
          }
        }
        ResultPath = "$.validation"
        Next = "CheckValidation"
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException"]
            IntervalSeconds = 2
            MaxAttempts = 3
            BackoffRate = 2
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next = "AnalysisFailed"
            ResultPath = "$.error"
          }
        ]
      }

      CheckValidation = {
        Type = "Choice"
        Choices = [
          {
            Variable = "$.validation.Payload.valid"
            BooleanEquals = true
            Next = "ProcessData"
          }
        ]
        Default = "ValidationFailed"
      }

      ProcessData = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.data_processing.arn
          Payload = {
            "action" = "process_data"
            "session_id.$" = "$.session_id"
            "analysis_id.$" = "$.analysis_id"
            "parameters.$" = "$.parameters"
          }
        }
        ResultPath = "$.processed_data"
        Next = "RunAnalysis"
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException"]
            IntervalSeconds = 2
            MaxAttempts = 3
            BackoffRate = 2
          }
        ]
      }

      RunAnalysis = {
        Type = "Parallel"
        Branches = [
          {
            StartAt = "ComputeScores"
            States = {
              ComputeScores = {
                Type = "Task"
                Resource = "arn:aws:states:::lambda:invoke"
                Parameters = {
                  FunctionName = aws_lambda_function.analysis.arn
                  Payload = {
                    "action" = "compute_scores"
                    "session_id.$" = "$.session_id"
                    "analysis_id.$" = "$.analysis_id"
                    "data.$" = "$.processed_data.Payload"
                  }
                }
                End = true
              }
            }
          },
          {
            StartAt = "ComputeRankings"
            States = {
              ComputeRankings = {
                Type = "Task"
                Resource = "arn:aws:states:::lambda:invoke"
                Parameters = {
                  FunctionName = aws_lambda_function.analysis.arn
                  Payload = {
                    "action" = "compute_rankings"
                    "session_id.$" = "$.session_id"
                    "analysis_id.$" = "$.analysis_id"
                    "data.$" = "$.processed_data.Payload"
                  }
                }
                End = true
              }
            }
          }
        ]
        ResultPath = "$.analysis_results"
        Next = "GenerateVisualizations"
      }

      GenerateVisualizations = {
        Type = "Parallel"
        Branches = [
          {
            StartAt = "CreateMap"
            States = {
              CreateMap = {
                Type = "Task"
                Resource = "arn:aws:states:::lambda:invoke"
                Parameters = {
                  FunctionName = aws_lambda_function.visualization.arn
                  Payload = {
                    "visualization_type" = "risk_map"
                    "session_id.$" = "$.session_id"
                    "analysis_id.$" = "$.analysis_id"
                  }
                }
                End = true
              }
            }
          },
          {
            StartAt = "CreateChart"
            States = {
              CreateChart = {
                Type = "Task"
                Resource = "arn:aws:states:::lambda:invoke"
                Parameters = {
                  FunctionName = aws_lambda_function.visualization.arn
                  Payload = {
                    "visualization_type" = "ranking_chart"
                    "session_id.$" = "$.session_id"
                    "analysis_id.$" = "$.analysis_id"
                  }
                }
                End = true
              }
            }
          },
          {
            StartAt = "CreateDashboard"
            States = {
              CreateDashboard = {
                Type = "Task"
                Resource = "arn:aws:states:::lambda:invoke"
                Parameters = {
                  FunctionName = aws_lambda_function.visualization.arn
                  Payload = {
                    "visualization_type" = "composite_dashboard"
                    "session_id.$" = "$.session_id"
                    "analysis_id.$" = "$.analysis_id"
                  }
                }
                End = true
              }
            }
          }
        ]
        ResultPath = "$.visualizations"
        Next = "GenerateReport"
      }

      GenerateReport = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.reports.arn
          Payload = {
            "format" = "pdf"
            "session_id.$" = "$.session_id"
            "analysis_id.$" = "$.analysis_id"
            "user_id.$" = "$.user_id"
          }
        }
        ResultPath = "$.report"
        Next = "UpdateAnalysisStatus"
      }

      UpdateAnalysisStatus = {
        Type = "Task"
        Resource = "arn:aws:states:::dynamodb:updateItem"
        Parameters = {
          TableName = aws_dynamodb_table.analyses.name
          Key = {
            "user_id" = {"S.$" = "$.user_id"}
            "analysis_id" = {"S.$" = "$.analysis_id"}
          }
          UpdateExpression = "SET #status = :status, #updated = :updated, #results = :results"
          ExpressionAttributeNames = {
            "#status" = "status"
            "#updated" = "updated_at"
            "#results" = "results"
          }
          ExpressionAttributeValues = {
            ":status" = {"S" = "completed"}
            ":updated" = {"N.$" = "$$.State.EnteredTime"}
            ":results" = {
              "M" = {
                "visualizations" = {"S.$" = "States.JsonToString($.visualizations)"}
                "report_url" = {"S.$" = "$.report.Payload.url"}
              }
            }
          }
        }
        ResultPath = "$.update_result"
        Next = "NotifyCompletion"
      }

      NotifyCompletion = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.websocket_message.arn
          Payload = {
            "action" = "analysis_complete"
            "session_id.$" = "$.session_id"
            "analysis_id.$" = "$.analysis_id"
            "status" = "completed"
            "results.$" = "$.analysis_results"
          }
        }
        End = true
      }

      ValidationFailed = {
        Type = "Task"
        Resource = "arn:aws:states:::dynamodb:updateItem"
        Parameters = {
          TableName = aws_dynamodb_table.analyses.name
          Key = {
            "user_id" = {"S.$" = "$.user_id"}
            "analysis_id" = {"S.$" = "$.analysis_id"}
          }
          UpdateExpression = "SET #status = :status, #error = :error"
          ExpressionAttributeNames = {
            "#status" = "status"
            "#error" = "error_message"
          }
          ExpressionAttributeValues = {
            ":status" = {"S" = "failed"}
            ":error" = {"S" = "Data validation failed"}
          }
        }
        Next = "AnalysisFailed"
      }

      AnalysisFailed = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.websocket_message.arn
          Payload = {
            "action" = "analysis_failed"
            "session_id.$" = "$.session_id"
            "analysis_id.$" = "$.analysis_id"
            "error.$" = "$.error"
          }
        }
        End = true
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.step_functions.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tags = {
    Name = "${var.project_name}-composite-scoring-${var.environment}"
    Type = "analysis-workflow"
  }
}

# PCA Analysis Workflow
resource "aws_sfn_state_machine" "pca_analysis" {
  name     = "${var.project_name}-pca-analysis-${var.environment}"
  role_arn = aws_iam_role.step_functions.arn

  definition = jsonencode({
    Comment = "PCA analysis workflow"
    StartAt = "ValidateData"
    States = {
      ValidateData = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.data_processing.arn
          Payload = {
            "action" = "validate_for_pca"
            "session_id.$" = "$.session_id"
            "analysis_id.$" = "$.analysis_id"
          }
        }
        Next = "RunPCA"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next = "HandleError"
          }
        ]
      }

      RunPCA = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.analysis.arn
          Payload = {
            "action" = "run_pca"
            "session_id.$" = "$.session_id"
            "analysis_id.$" = "$.analysis_id"
            "n_components.$" = "$.parameters.n_components"
          }
        }
        Next = "CreatePCAVisualizations"
      }

      CreatePCAVisualizations = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.visualization.arn
          Payload = {
            "visualization_type" = "pca_plots"
            "session_id.$" = "$.session_id"
            "analysis_id.$" = "$.analysis_id"
          }
        }
        Next = "Success"
      }

      Success = {
        Type = "Succeed"
      }

      HandleError = {
        Type = "Fail"
        Error = "AnalysisError"
        Cause = "PCA analysis failed"
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.step_functions.arn}:*"
    include_execution_data = true
    level                  = "ERROR"
  }

  tags = {
    Name = "${var.project_name}-pca-analysis-${var.environment}"
    Type = "analysis-workflow"
  }
}

# CloudWatch Log Group for Step Functions
resource "aws_cloudwatch_log_group" "step_functions" {
  name              = "/aws/stepfunctions/${var.project_name}-${var.environment}"
  retention_in_days = 30
}

# Outputs
output "composite_scoring_arn" {
  value = aws_sfn_state_machine.composite_scoring.arn
}

output "pca_analysis_arn" {
  value = aws_sfn_state_machine.pca_analysis.arn
}
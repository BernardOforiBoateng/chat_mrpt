# DynamoDB Tables for ChatMRPT

# Users Table
resource "aws_dynamodb_table" "users" {
  name           = "${var.project_name}-users-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"  # On-demand pricing
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  # Global secondary index for email lookup
  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Enable encryption
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-users-${var.environment}"
    Description = "User profiles and settings"
  }
}

# Analyses Table
resource "aws_dynamodb_table" "analyses" {
  name           = "${var.project_name}-analyses-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "analysis_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "analysis_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "N"
  }

  attribute {
    name = "status"
    type = "S"
  }

  # Global secondary index for time-based queries
  global_secondary_index {
    name            = "created-at-index"
    hash_key        = "user_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  # Global secondary index for status queries
  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    range_key       = "created_at"
    projection_type = "INCLUDE"
    non_key_attributes = ["user_id", "analysis_id", "analysis_type"]
  }

  # TTL for auto-deletion of old analyses
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-analyses-${var.environment}"
    Description = "Analysis metadata and results"
  }
}

# Sessions Table (replaces Flask sessions)
resource "aws_dynamodb_table" "sessions" {
  name           = "${var.project_name}-sessions-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "session_token"

  attribute {
    name = "session_token"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  # Global secondary index for user session lookup
  global_secondary_index {
    name            = "user-sessions-index"
    hash_key        = "user_id"
    projection_type = "ALL"
  }

  # TTL for automatic session expiry
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-sessions-${var.environment}"
    Description = "User session management"
  }
}

# Audit Log Table (for compliance)
resource "aws_dynamodb_table" "audit_log" {
  name           = "${var.project_name}-audit-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "timestamp"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  attribute {
    name = "action_type"
    type = "S"
  }

  # Global secondary index for action type queries
  global_secondary_index {
    name            = "action-type-index"
    hash_key        = "action_type"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  # Keep audit logs for 7 years (compliance)
  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-audit-${var.environment}"
    Description = "Audit trail for compliance"
  }
}

# State Lock Table for Terraform (if not exists)
resource "aws_dynamodb_table" "terraform_locks" {
  count = var.environment == "prod" ? 1 : 0

  name           = "chatmrpt-terraform-locks"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "chatmrpt-terraform-locks"
    Description = "Terraform state locking"
  }
}

# Outputs
output "users_table_name" {
  value = aws_dynamodb_table.users.name
}

output "users_table_arn" {
  value = aws_dynamodb_table.users.arn
}

output "analyses_table_name" {
  value = aws_dynamodb_table.analyses.name
}

output "analyses_table_arn" {
  value = aws_dynamodb_table.analyses.arn
}

output "sessions_table_name" {
  value = aws_dynamodb_table.sessions.name
}

output "sessions_table_arn" {
  value = aws_dynamodb_table.sessions.arn
}
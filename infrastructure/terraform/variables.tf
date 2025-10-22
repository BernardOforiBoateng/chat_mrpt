# Terraform Variables for ChatMRPT Infrastructure

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "chatmrpt"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-2"
}

variable "domain_name" {
  description = "Domain name for production environment"
  type        = string
  default     = "chatmrpt.com"
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for domain"
  type        = string
  default     = ""
}

# Lambda Configuration
variable "lambda_memory_size" {
  description = "Memory sizes for Lambda functions"
  type = map(number)
  default = {
    auth            = 128
    analysis        = 1024
    data_processing = 2048
    visualization   = 2048
    reports         = 1024
    websocket       = 256
  }
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions (seconds)"
  type = map(number)
  default = {
    auth            = 10
    analysis        = 300
    data_processing = 300
    visualization   = 300
    reports         = 300
    websocket       = 30
  }
}

# DynamoDB Configuration
variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PAY_PER_REQUEST or PROVISIONED)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "dynamodb_ttl_days" {
  description = "TTL for temporary data in days"
  type        = number
  default     = 30
}

# S3 Configuration
variable "s3_lifecycle_days" {
  description = "Days before transitioning to IA storage"
  type        = number
  default     = 30
}

variable "s3_expiration_days" {
  description = "Days before deleting old data"
  type        = number
  default     = 365
}

# Cognito Configuration
variable "cognito_mfa" {
  description = "MFA configuration for Cognito"
  type        = string
  default     = "OPTIONAL"
}

variable "cognito_password_minimum_length" {
  description = "Minimum password length"
  type        = number
  default     = 12
}

# CloudFront Configuration
variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"  # Use PriceClass_All for production
}

variable "enable_waf" {
  description = "Enable WAF for CloudFront"
  type        = bool
  default     = false  # Enable for production
}

# Monitoring Configuration
variable "alarm_email" {
  description = "Email for CloudWatch alarms"
  type        = string
  default     = "ops@chatmrpt.com"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# Tags
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "ChatMRPT"
    ManagedBy   = "Terraform"
    CostCenter  = "Engineering"
    Compliance  = "HIPAA-Eligible"
  }
}

# Data Source for current AWS account
data "aws_caller_identity" "current" {}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}
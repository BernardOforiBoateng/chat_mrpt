# AWS Cognito Configuration for ChatMRPT

# User Pool
resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-users-${var.environment}"

  # Password policy
  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true

    temporary_password_validity_days = 7
  }

  # User attributes
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Email configuration
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # Custom attributes for user metadata
  schema {
    name                     = "organization"
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    required                 = false

    string_attribute_constraints {
      min_length = 1
      max_length = 100
    }
  }

  schema {
    name                     = "role"
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    required                 = false

    string_attribute_constraints {
      min_length = 1
      max_length = 50
    }
  }

  schema {
    name                     = "region"
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    required                 = false

    string_attribute_constraints {
      min_length = 1
      max_length = 100
    }
  }

  # MFA Configuration
  mfa_configuration = "OPTIONAL"

  software_token_mfa_configuration {
    enabled = true
  }

  # User pool add-ons
  user_pool_add_ons {
    advanced_security_mode = "ENFORCED"
  }

  # Device tracking
  device_configuration {
    challenge_required_on_new_device      = true
    device_only_remembered_on_user_prompt = true
  }

  # Lambda triggers
  lambda_config {
    pre_sign_up       = aws_lambda_function.pre_signup.arn
    post_confirmation = aws_lambda_function.post_confirmation.arn
    pre_authentication = aws_lambda_function.pre_authentication.arn
  }

  tags = {
    Name        = "${var.project_name}-users-${var.environment}"
    Description = "User authentication pool"
  }
}

# User Pool Domain
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${var.project_name}-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id
}

# User Pool Client for Web Application
resource "aws_cognito_user_pool_client" "web" {
  name         = "${var.project_name}-web-client-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id

  # OAuth settings
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code", "implicit"]
  allowed_oauth_scopes                 = ["phone", "email", "openid", "profile"]

  callback_urls = var.environment == "dev" ?
    ["http://localhost:3000/callback"] :
    ["https://${aws_cloudfront_distribution.frontend.domain_name}/callback"]

  logout_urls = var.environment == "dev" ?
    ["http://localhost:3000/logout"] :
    ["https://${aws_cloudfront_distribution.frontend.domain_name}/logout"]

  # Security settings
  prevent_user_existence_errors = "ENABLED"
  enable_token_revocation       = true

  # Token validity
  refresh_token_validity = 30  # days
  access_token_validity  = 1   # hours
  id_token_validity      = 1   # hours

  token_validity_units {
    refresh_token = "days"
    access_token  = "hours"
    id_token      = "hours"
  }

  # Supported identity providers
  supported_identity_providers = ["COGNITO"]

  # Read/write attributes
  read_attributes = [
    "email",
    "email_verified",
    "name",
    "custom:organization",
    "custom:role",
    "custom:region"
  ]

  write_attributes = [
    "email",
    "name",
    "custom:organization",
    "custom:role",
    "custom:region"
  ]

  # Explicit auth flows
  explicit_auth_flows = [
    "ALLOW_CUSTOM_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  generate_secret = false  # For web clients
}

# User Pool Client for Backend/Admin Operations
resource "aws_cognito_user_pool_client" "backend" {
  name         = "${var.project_name}-backend-client-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id

  # This client can be used for server-side operations
  generate_secret = true

  explicit_auth_flows = [
    "ALLOW_ADMIN_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]
}

# Identity Pool for AWS Resource Access
resource "aws_cognito_identity_pool" "main" {
  identity_pool_name               = "${var.project_name}_${var.environment}_identity_pool"
  allow_unauthenticated_identities = false
  allow_classic_flow               = false

  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.web.id
    provider_name           = aws_cognito_user_pool.main.endpoint
    server_side_token_check = false
  }

  tags = {
    Name        = "${var.project_name}-identity-${var.environment}"
    Description = "Identity pool for AWS resource access"
  }
}

# IAM Role for Authenticated Users
resource "aws_iam_role" "authenticated_users" {
  name = "${var.project_name}-cognito-authenticated-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.main.id
          }
          "ForAnyValue:StringLike" = {
            "cognito-identity.amazonaws.com:amr" = "authenticated"
          }
        }
      }
    ]
  })
}

# IAM Policy for Authenticated Users
resource "aws_iam_role_policy" "authenticated_users" {
  name = "${var.project_name}-cognito-authenticated-policy-${var.environment}"
  role = aws_iam_role.authenticated_users.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.data.arn}/uploads/$${cognito-identity.amazonaws.com:sub}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.data.arn}/results/$${cognito-identity.amazonaws.com:sub}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "execute-api:Invoke"
        ]
        Resource = "${aws_api_gateway_rest_api.main.execution_arn}/*"
      }
    ]
  })
}

# Attach roles to Identity Pool
resource "aws_cognito_identity_pool_roles_attachment" "main" {
  identity_pool_id = aws_cognito_identity_pool.main.id

  roles = {
    authenticated = aws_iam_role.authenticated_users.arn
  }
}

# User Groups
resource "aws_cognito_user_group" "admin" {
  name         = "Administrators"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "System administrators with full access"
  precedence   = 1
}

resource "aws_cognito_user_group" "researcher" {
  name         = "Researchers"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Health researchers and analysts"
  precedence   = 10
}

resource "aws_cognito_user_group" "field_officer" {
  name         = "FieldOfficers"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Field health officers"
  precedence   = 20
}

# Outputs
output "user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  value = aws_cognito_user_pool.main.arn
}

output "web_client_id" {
  value = aws_cognito_user_pool_client.web.id
}

output "identity_pool_id" {
  value = aws_cognito_identity_pool.main.id
}

output "user_pool_domain" {
  value = aws_cognito_user_pool_domain.main.domain
}
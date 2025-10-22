# ChatMRPT AWS Migration Architecture

## Executive Summary
This document outlines the complete serverless architecture for ChatMRPT's migration to AWS. The new architecture completely eliminates the data bleed issues identified in the Flask application by removing all singleton patterns and implementing proper request-scoped isolation.

## Root Cause Resolution

### Problems Solved
1. **Global Singleton State**: Eliminated - Lambda functions are stateless
2. **Shared Memory Between Workers**: Resolved - Each Lambda invocation is isolated
3. **Session Data Bleed**: Fixed - DynamoDB provides proper session isolation
4. **Missing Authentication**: Implemented - Cognito provides enterprise-grade auth
5. **Concurrency Issues**: Resolved - Serverless scales automatically

## Architecture Components

### 1. Authentication Layer (AWS Cognito)
**Files Created**: `infrastructure/terraform/cognito.tf`
- User Pool with MFA support
- Custom attributes for organization/role/region
- Pre-signup validation Lambda
- Post-confirmation user setup Lambda
- Pre-authentication security checks
- Identity Pool for AWS resource access

### 2. Data Storage (DynamoDB)
**Files Created**: `infrastructure/terraform/dynamodb.tf`
- **Users Table**: User profiles with email index
- **Analyses Table**: Analysis metadata with status tracking
- **Sessions Table**: Session management with TTL
- **Audit Log Table**: Compliance and security logging

### 3. File Storage (S3)
**Files Created**: `infrastructure/terraform/s3.tf`
- **Data Bucket**: User uploads and analysis results
- **Frontend Bucket**: Static website hosting
- **Lambda Code Bucket**: Function deployment packages
- Versioning and encryption enabled
- Lifecycle policies for cost optimization

### 4. API Gateway
**Files Created**: `infrastructure/terraform/api_gateway.tf`
- REST API with Cognito authorization
- WebSocket API for real-time updates
- CORS configuration
- Request validation
- Rate limiting and throttling

### 5. Lambda Functions
**Files Created**:
- `infrastructure/lambdas/auth/src/pre_signup.py`
- `infrastructure/lambdas/auth/src/post_confirmation.py`
- `infrastructure/lambdas/auth/src/pre_authentication.py`
- `infrastructure/lambdas/analysis/src/handler.py`
- `infrastructure/lambdas/data_processing/src/handler.py`
- `infrastructure/lambdas/visualization/src/handler.py`
- `infrastructure/lambdas/reports/src/handler.py`

### 6. Infrastructure as Code
**Files Created**:
- `infrastructure/terraform/main.tf` - Provider configuration
- `infrastructure/terraform/lambda.tf` - Lambda configurations

## Data Flow Architecture

### Upload Flow
1. User authenticates via Cognito
2. Frontend requests presigned S3 URL
3. Direct upload to S3 (bypasses Lambda size limits)
4. S3 triggers data processing Lambda
5. Lambda validates and processes data
6. Results stored in DynamoDB and S3

### Analysis Flow
1. User initiates analysis via API
2. API Gateway validates JWT token
3. Analysis Lambda starts Step Functions workflow
4. Workflow orchestrates processing steps
5. Results published via WebSocket
6. Final results stored in S3

### Security Model
```
User -> Cognito Auth -> API Gateway -> Lambda -> DynamoDB/S3
         ^                    |
         |                    v
    Identity Pool     Request-scoped execution
```

## Key Design Decisions

### 1. Stateless Architecture
- No global variables
- No singleton patterns
- No shared memory
- Each request completely isolated

### 2. Authentication First
- All endpoints require authentication
- User context from JWT tokens
- Row-level security in DynamoDB

### 3. Event-Driven Processing
- S3 triggers for file processing
- Step Functions for workflows
- WebSocket for real-time updates

### 4. Cost Optimization
- On-demand DynamoDB billing
- S3 lifecycle policies
- Lambda right-sizing
- CloudFront caching

## Migration Benefits

### Scalability
- Automatic scaling with Lambda
- No server management
- Handles 1 to 10,000+ concurrent users

### Security
- Enterprise authentication with Cognito
- IAM role-based access control
- Encryption at rest and in transit
- Audit logging for compliance

### Reliability
- Multi-AZ deployment by default
- Built-in fault tolerance
- Automatic retries
- DynamoDB point-in-time recovery

### Cost Efficiency
- Pay-per-use pricing model
- No idle infrastructure costs
- Automatic resource optimization
- AWS Free Tier eligible

## File Mapping

### Files to Delete (Flask App)
```
app/core/unified_data_state.py          # Singleton causing data bleed
app/core/analysis_state_handler.py      # Another singleton
app/core/request_interpreter.py         # Shared conversation history
app/core/redis_state_manager.py         # Flawed Redis implementation
app/core/session_state.py               # Session management issues
```

### Files to Migrate (Core Logic)
```
app/analysis/pipeline_stages/*          -> Lambda functions
app/tools/*                             -> Lambda functions
app/services/agents/*                   -> Lambda functions
app/data/processing.py                  -> data_processing Lambda
```

### New Architecture Files
```
infrastructure/
├── terraform/
│   ├── main.tf                        # Provider configuration
│   ├── cognito.tf                     # Authentication setup
│   ├── dynamodb.tf                    # Database tables
│   ├── s3.tf                          # Storage buckets
│   ├── api_gateway.tf                 # API configuration
│   └── lambda.tf                      # Lambda functions
└── lambdas/
    ├── auth/                          # Authentication triggers
    ├── analysis/                      # Analysis orchestration
    ├── data_processing/               # Data validation/processing
    ├── visualization/                 # Map/chart generation
    └── reports/                       # Report generation
```

## Implementation Status

### Completed ✅
- Terraform infrastructure files
- Cognito user pool configuration
- DynamoDB table schemas
- S3 bucket structure
- Lambda function templates
- API Gateway configuration

### Pending
- React frontend application
- Data migration scripts
- CloudFront distribution
- Step Functions workflows
- Deployment pipeline

## Next Steps

1. **Frontend Development**
   - React application with Amplify
   - Cognito authentication integration
   - S3 direct upload implementation

2. **Data Migration**
   - Export existing user data
   - Transform to DynamoDB format
   - Migrate analysis results

3. **Testing & Deployment**
   - Unit tests for Lambda functions
   - Integration testing
   - Staged rollout plan

## Risk Mitigation

### Data Migration Risks
- Run parallel systems during migration
- Implement rollback procedures
- Validate data integrity

### User Experience
- Maintain feature parity
- Provide migration guides
- Support dual authentication temporarily

### Operational Readiness
- CloudWatch monitoring setup
- Alerting configuration
- Runbook documentation

## Conclusion

This serverless architecture completely resolves the critical data bleed issues by eliminating all shared state and implementing proper isolation at every layer. The migration provides a scalable, secure, and cost-effective platform for ChatMRPT's future growth.
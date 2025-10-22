#!/bin/bash

# ChatMRPT AWS Deployment Script
# This script deploys the serverless infrastructure to AWS

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-prod}
AWS_REGION=${AWS_REGION:-us-east-2}
PROJECT_NAME="chatmrpt"

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}ChatMRPT AWS Deployment Script${NC}"
echo -e "${GREEN}==========================================${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "AWS Region: ${YELLOW}$AWS_REGION${NC}"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    # Check for AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}AWS CLI is not installed. Please install it first.${NC}"
        exit 1
    fi

    # Check for Terraform
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}Terraform is not installed. Please install it first.${NC}"
        exit 1
    fi

    # Check for Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Node.js is not installed. Please install it first.${NC}"
        exit 1
    fi

    # Check for Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 is not installed. Please install it first.${NC}"
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}AWS credentials are not configured. Please run 'aws configure'.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ All prerequisites met${NC}"
    echo ""
}

# Function to package Lambda functions
package_lambda_functions() {
    echo -e "${YELLOW}Packaging Lambda functions...${NC}"

    cd infrastructure/lambdas

    # Package each Lambda function
    for func_dir in auth analysis data_processing visualization reports; do
        if [ -d "$func_dir" ]; then
            echo -e "Packaging $func_dir..."

            # Create dist directory
            mkdir -p "$func_dir/dist"

            # Copy source files
            cp -r "$func_dir/src"/* "$func_dir/dist/"

            # Install dependencies if requirements.txt exists
            if [ -f "$func_dir/requirements.txt" ]; then
                pip3 install -r "$func_dir/requirements.txt" -t "$func_dir/dist/" --quiet
            fi

            # Create ZIP
            cd "$func_dir/dist"
            zip -r "../dist/${func_dir}.zip" . -q
            cd ../..

            echo -e "${GREEN}✓ Packaged $func_dir${NC}"
        fi
    done

    # Package Lambda layer
    echo -e "Creating shared dependencies layer..."
    mkdir -p layers
    cd layers

    # Create requirements file for layer
    cat > requirements.txt << EOF
boto3>=1.28.0
pandas>=2.0.0
geopandas>=0.14.0
numpy>=1.24.0
folium>=0.14.0
plotly>=5.15.0
reportlab>=4.0.0
python-docx>=0.8.11
openpyxl>=3.1.0
xlsxwriter>=3.1.0
EOF

    # Install layer dependencies
    mkdir -p python
    pip3 install -r requirements.txt -t python/ --quiet
    zip -r shared_deps.zip python -q

    cd ../..
    echo -e "${GREEN}✓ Lambda functions packaged${NC}"
    echo ""
}

# Function to build React frontend
build_frontend() {
    echo -e "${YELLOW}Building React frontend...${NC}"

    cd frontend/chatmrpt-react

    # Install dependencies
    echo "Installing dependencies..."
    npm ci --silent

    # Create AWS configuration
    cat > src/aws-exports.js << EOF
const awsconfig = {
    region: '${AWS_REGION}',
    userPoolId: '\${COGNITO_USER_POOL_ID}',
    userPoolWebClientId: '\${COGNITO_CLIENT_ID}',
    apiGatewayUrl: '\${API_GATEWAY_URL}',
    websocketUrl: '\${WEBSOCKET_URL}',
    s3BucketName: '${PROJECT_NAME}-data-${ENVIRONMENT}'
};

export default awsconfig;
EOF

    # Build production bundle
    echo "Building production bundle..."
    npm run build

    cd ../..
    echo -e "${GREEN}✓ Frontend built${NC}"
    echo ""
}

# Function to deploy Terraform infrastructure
deploy_terraform() {
    echo -e "${YELLOW}Deploying Terraform infrastructure...${NC}"

    cd infrastructure/terraform

    # Initialize Terraform
    echo "Initializing Terraform..."
    terraform init

    # Create workspace for environment
    terraform workspace select $ENVIRONMENT 2>/dev/null || terraform workspace new $ENVIRONMENT

    # Plan deployment
    echo "Planning deployment..."
    terraform plan -var="environment=$ENVIRONMENT" -out=tfplan

    # Apply deployment
    echo -e "${YELLOW}Applying Terraform changes...${NC}"
    read -p "Do you want to proceed with deployment? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${RED}Deployment cancelled${NC}"
        exit 1
    fi

    terraform apply tfplan

    # Save outputs
    terraform output -json > outputs.json

    # Extract important values
    export COGNITO_USER_POOL_ID=$(terraform output -raw user_pool_id)
    export COGNITO_CLIENT_ID=$(terraform output -raw web_client_id)
    export API_GATEWAY_URL=$(terraform output -raw api_gateway_url)
    export WEBSOCKET_URL=$(terraform output -raw websocket_url)
    export CLOUDFRONT_URL=$(terraform output -raw cloudfront_url 2>/dev/null || echo "")

    cd ../..
    echo -e "${GREEN}✓ Infrastructure deployed${NC}"
    echo ""
}

# Function to upload frontend to S3
upload_frontend() {
    echo -e "${YELLOW}Uploading frontend to S3...${NC}"

    # Update AWS exports with actual values
    cd frontend/chatmrpt-react

    cat > src/aws-exports.js << EOF
const awsconfig = {
    region: '${AWS_REGION}',
    userPoolId: '${COGNITO_USER_POOL_ID}',
    userPoolWebClientId: '${COGNITO_CLIENT_ID}',
    apiGatewayUrl: '${API_GATEWAY_URL}',
    websocketUrl: '${WEBSOCKET_URL}',
    s3BucketName: '${PROJECT_NAME}-data-${ENVIRONMENT}'
};

export default awsconfig;
EOF

    # Rebuild with actual config
    npm run build

    # Upload to S3
    aws s3 sync build/ s3://${PROJECT_NAME}-frontend-${ENVIRONMENT}/ \
        --delete \
        --cache-control "public, max-age=3600"

    # Upload index.html with no-cache
    aws s3 cp build/index.html s3://${PROJECT_NAME}-frontend-${ENVIRONMENT}/index.html \
        --cache-control "no-cache, no-store, must-revalidate"

    cd ../..
    echo -e "${GREEN}✓ Frontend uploaded${NC}"
    echo ""
}

# Function to run post-deployment tasks
post_deployment() {
    echo -e "${YELLOW}Running post-deployment tasks...${NC}"

    # Create CloudFront invalidation if exists
    if [ ! -z "$CLOUDFRONT_URL" ]; then
        echo "Creating CloudFront invalidation..."
        DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?DomainName=='${CLOUDFRONT_URL}'].Id" --output text)
        if [ ! -z "$DISTRIBUTION_ID" ]; then
            aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"
        fi
    fi

    # Run database migrations if needed
    if [ -f "scripts/migrate_to_aws.py" ]; then
        echo "Running data migration..."
        python3 scripts/migrate_to_aws.py --env $ENVIRONMENT --dry-run
        echo -e "${YELLOW}Note: Run without --dry-run to perform actual migration${NC}"
    fi

    echo -e "${GREEN}✓ Post-deployment tasks completed${NC}"
    echo ""
}

# Function to display deployment summary
show_summary() {
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
    echo -e "Region: ${YELLOW}$AWS_REGION${NC}"
    echo ""
    echo -e "${YELLOW}Access URLs:${NC}"
    echo -e "API Gateway: ${GREEN}$API_GATEWAY_URL${NC}"
    echo -e "WebSocket: ${GREEN}$WEBSOCKET_URL${NC}"

    if [ ! -z "$CLOUDFRONT_URL" ]; then
        echo -e "CloudFront: ${GREEN}https://$CLOUDFRONT_URL${NC}"
    else
        echo -e "S3 Website: ${GREEN}http://${PROJECT_NAME}-frontend-${ENVIRONMENT}.s3-website-${AWS_REGION}.amazonaws.com${NC}"
    fi

    echo ""
    echo -e "${YELLOW}Resources Created:${NC}"
    echo -e "• Cognito User Pool: ${COGNITO_USER_POOL_ID}"
    echo -e "• DynamoDB Tables: users, analyses, sessions, audit"
    echo -e "• S3 Buckets: data, frontend, lambda-code"
    echo -e "• Lambda Functions: 7 functions deployed"
    echo -e "• API Gateway: REST and WebSocket APIs"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "1. Run data migration: ${GREEN}python3 scripts/migrate_to_aws.py --env $ENVIRONMENT${NC}"
    echo -e "2. Update DNS records to point to CloudFront/S3"
    echo -e "3. Configure monitoring and alerting"
    echo -e "4. Test the deployment thoroughly"
    echo ""
}

# Main deployment flow
main() {
    echo -e "${YELLOW}Starting deployment...${NC}"
    echo ""

    check_prerequisites
    package_lambda_functions
    build_frontend
    deploy_terraform
    upload_frontend
    post_deployment
    show_summary
}

# Run main function
main
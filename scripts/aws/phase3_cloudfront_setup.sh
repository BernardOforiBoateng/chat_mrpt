#!/bin/bash

# =====================================================
# Phase 3: CloudFront CDN Configuration
# =====================================================
# Purpose: Set up CloudFront distribution for staging ALB
# Date: August 27, 2025
# =====================================================

set -e

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
STAGING_IP="3.21.167.170"
ALB_DNS="chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
AWS_REGION="us-east-2"
DISTRIBUTION_COMMENT="ChatMRPT Staging-to-Production CDN"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================================"
echo "   PHASE 3: CLOUDFRONT CDN SETUP"
echo "   $(date)"
echo "======================================================"
echo ""

# Function to create CloudFront configuration
create_cloudfront_config() {
    echo -e "${YELLOW}Creating CloudFront Configuration...${NC}"
    
    cat > /tmp/cloudfront-config.json << EOF
{
    "CallerReference": "chatmrpt-staging-$(date +%s)",
    "Comment": "$DISTRIBUTION_COMMENT",
    "Enabled": true,
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "staging-alb",
                "DomainName": "$ALB_DNS",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only",
                    "OriginSslProtocols": {
                        "Quantity": 3,
                        "Items": ["TLSv1", "TLSv1.1", "TLSv1.2"]
                    },
                    "OriginReadTimeout": 60,
                    "OriginKeepaliveTimeout": 5
                },
                "ConnectionAttempts": 3,
                "ConnectionTimeout": 10
            }
        ]
    },
    "DefaultRootObject": "",
    "DefaultCacheBehavior": {
        "TargetOriginId": "staging-alb",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 7,
            "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
        },
        "ForwardedValues": {
            "QueryString": true,
            "Cookies": {
                "Forward": "all"
            },
            "Headers": {
                "Quantity": 7,
                "Items": [
                    "Accept",
                    "Accept-Language",
                    "Authorization",
                    "Content-Type",
                    "Host",
                    "Origin",
                    "Referer"
                ]
            }
        },
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000,
        "Compress": true,
        "SmoothStreaming": false
    },
    "CacheBehaviors": {
        "Quantity": 3,
        "Items": [
            {
                "PathPattern": "/static/*",
                "TargetOriginId": "staging-alb",
                "ViewerProtocolPolicy": "https-only",
                "AllowedMethods": {
                    "Quantity": 2,
                    "Items": ["GET", "HEAD"],
                    "CachedMethods": {
                        "Quantity": 2,
                        "Items": ["GET", "HEAD"]
                    }
                },
                "ForwardedValues": {
                    "QueryString": false,
                    "Cookies": {
                        "Forward": "none"
                    },
                    "Headers": {
                        "Quantity": 0
                    }
                },
                "TrustedSigners": {
                    "Enabled": false,
                    "Quantity": 0
                },
                "MinTTL": 86400,
                "DefaultTTL": 604800,
                "MaxTTL": 31536000,
                "Compress": true,
                "SmoothStreaming": false
            },
            {
                "PathPattern": "/upload*",
                "TargetOriginId": "staging-alb",
                "ViewerProtocolPolicy": "https-only",
                "AllowedMethods": {
                    "Quantity": 7,
                    "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
                    "CachedMethods": {
                        "Quantity": 2,
                        "Items": ["GET", "HEAD"]
                    }
                },
                "ForwardedValues": {
                    "QueryString": true,
                    "Cookies": {
                        "Forward": "all"
                    },
                    "Headers": {
                        "Quantity": 1,
                        "Items": ["*"]
                    }
                },
                "TrustedSigners": {
                    "Enabled": false,
                    "Quantity": 0
                },
                "MinTTL": 0,
                "DefaultTTL": 0,
                "MaxTTL": 0,
                "Compress": false,
                "SmoothStreaming": false
            },
            {
                "PathPattern": "/api/*",
                "TargetOriginId": "staging-alb",
                "ViewerProtocolPolicy": "https-only",
                "AllowedMethods": {
                    "Quantity": 7,
                    "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
                    "CachedMethods": {
                        "Quantity": 2,
                        "Items": ["GET", "HEAD"]
                    }
                },
                "ForwardedValues": {
                    "QueryString": true,
                    "Cookies": {
                        "Forward": "all"
                    },
                    "Headers": {
                        "Quantity": 1,
                        "Items": ["*"]
                    }
                },
                "TrustedSigners": {
                    "Enabled": false,
                    "Quantity": 0
                },
                "MinTTL": 0,
                "DefaultTTL": 0,
                "MaxTTL": 300,
                "Compress": true,
                "SmoothStreaming": false
            }
        ]
    },
    "CustomErrorResponses": {
        "Quantity": 2,
        "Items": [
            {
                "ErrorCode": 404,
                "ErrorCachingMinTTL": 10
            },
            {
                "ErrorCode": 500,
                "ErrorCachingMinTTL": 5
            }
        ]
    },
    "PriceClass": "PriceClass_100",
    "WebACLId": "",
    "HttpVersion": "http2",
    "IsIPV6Enabled": true
}
EOF
    
    echo "✅ Configuration file created"
}

# Function to create CloudFront distribution via AWS CLI
create_distribution() {
    echo -e "${YELLOW}Creating CloudFront Distribution...${NC}"
    echo ""
    
    ssh -i $KEY_PATH ec2-user@$STAGING_IP << 'EOF' 2>/dev/null
        export AWS_DEFAULT_REGION=us-east-1  # CloudFront is global, use us-east-1
        
        # Create the distribution
        aws cloudfront create-distribution \
            --distribution-config file:///tmp/cloudfront-config.json \
            --output json > /tmp/cf_result.json 2>&1
        
        if [ $? -eq 0 ]; then
            DIST_ID=$(cat /tmp/cf_result.json | jq -r '.Distribution.Id')
            DOMAIN_NAME=$(cat /tmp/cf_result.json | jq -r '.Distribution.DomainName')
            STATUS=$(cat /tmp/cf_result.json | jq -r '.Distribution.Status')
            
            echo "✅ CloudFront Distribution Created!"
            echo "  Distribution ID: $DIST_ID"
            echo "  Domain Name: $DOMAIN_NAME"
            echo "  Status: $STATUS"
            
            # Save distribution info
            echo "$DIST_ID" > /tmp/cf_distribution_id.txt
            echo "$DOMAIN_NAME" > /tmp/cf_domain_name.txt
        else
            echo "❌ Failed to create distribution"
            cat /tmp/cf_result.json
            exit 1
        fi
EOF
}

# Function to check if distribution already exists
check_existing_distribution() {
    echo -e "${YELLOW}Checking for existing distributions...${NC}"
    
    ssh -i $KEY_PATH ec2-user@$STAGING_IP << 'EOF' 2>/dev/null
        export AWS_DEFAULT_REGION=us-east-1
        
        # List all distributions
        aws cloudfront list-distributions \
            --query "DistributionList.Items[?Comment=='ChatMRPT Staging-to-Production CDN'].{Id:Id,Domain:DomainName,Status:Status}" \
            --output table 2>/dev/null || echo "No existing distributions found"
EOF
    
    echo ""
    read -p "Do you want to create a new CloudFront distribution? (y/n): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping CloudFront creation"
        return 1
    fi
    
    return 0
}

# Function to wait for distribution deployment
wait_for_deployment() {
    local dist_id=$1
    echo -e "${YELLOW}Waiting for distribution deployment (this may take 15-20 minutes)...${NC}"
    
    local max_attempts=40  # 20 minutes max
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        STATUS=$(ssh -i $KEY_PATH ec2-user@$STAGING_IP "export AWS_DEFAULT_REGION=us-east-1; aws cloudfront get-distribution --id $dist_id --query 'Distribution.Status' --output text" 2>/dev/null)
        
        if [ "$STATUS" = "Deployed" ]; then
            echo -e "${GREEN}✅ Distribution deployed successfully!${NC}"
            return 0
        else
            echo "  Status: $STATUS (attempt $((attempt+1))/$max_attempts)"
            sleep 30
            attempt=$((attempt + 1))
        fi
    done
    
    echo -e "${YELLOW}⚠️  Distribution still deploying. Check AWS Console for status.${NC}"
    return 1
}

# Function to create Route 53 health check
create_health_check() {
    echo -e "${YELLOW}Creating Route 53 Health Check...${NC}"
    
    ssh -i $KEY_PATH ec2-user@$STAGING_IP << EOF 2>/dev/null
        export AWS_DEFAULT_REGION=us-east-1
        
        # Create health check configuration
        cat > /tmp/health-check.json << 'HC'
{
    "Type": "HTTPS",
    "ResourcePath": "/ping",
    "FullyQualifiedDomainName": "$ALB_DNS",
    "Port": 443,
    "RequestInterval": 30,
    "FailureThreshold": 3,
    "MeasureLatency": true,
    "Inverted": false,
    "Disabled": false,
    "EnableSNI": true
}
HC
        
        # Create the health check
        aws route53 create-health-check \
            --caller-reference "chatmrpt-staging-$(date +%s)" \
            --health-check-config file:///tmp/health-check.json \
            --output json > /tmp/hc_result.json 2>&1
        
        if [ $? -eq 0 ]; then
            HC_ID=$(cat /tmp/hc_result.json | jq -r '.HealthCheck.Id')
            echo "✅ Health Check Created: $HC_ID"
        else
            echo "❌ Failed to create health check"
            cat /tmp/hc_result.json
        fi
EOF
}

# Main execution
echo "======================================================"
echo "   STARTING CLOUDFRONT CONFIGURATION"
echo "======================================================"
echo ""

# Step 1: Check for existing distributions
if ! check_existing_distribution; then
    echo "Exiting without creating CloudFront distribution"
    exit 0
fi

# Step 2: Copy configuration to staging server
create_cloudfront_config
scp -i $KEY_PATH /tmp/cloudfront-config.json ec2-user@$STAGING_IP:/tmp/ 2>/dev/null

# Step 3: Create the distribution
create_distribution

# Step 4: Get distribution details
DIST_ID=$(ssh -i $KEY_PATH ec2-user@$STAGING_IP 'cat /tmp/cf_distribution_id.txt 2>/dev/null' || echo "")
DOMAIN_NAME=$(ssh -i $KEY_PATH ec2-user@$STAGING_IP 'cat /tmp/cf_domain_name.txt 2>/dev/null' || echo "")

if [ -z "$DIST_ID" ]; then
    echo -e "${RED}❌ Failed to create CloudFront distribution${NC}"
    exit 1
fi

echo ""
echo "======================================================"
echo -e "${GREEN}   CLOUDFRONT DISTRIBUTION CREATED!${NC}"
echo "======================================================"
echo ""
echo "Distribution Details:"
echo "--------------------"
echo "ID: $DIST_ID"
echo "Domain: $DOMAIN_NAME"
echo "Origin: $ALB_DNS"
echo ""
echo "The distribution is being deployed globally."
echo "This process typically takes 15-20 minutes."
echo ""
echo "Once deployed, you can access ChatMRPT via:"
echo "  https://$DOMAIN_NAME"
echo ""
echo "Next Steps:"
echo "-----------"
echo "1. Wait for distribution deployment"
echo "2. Test access via CloudFront URL"
echo "3. Configure Route 53 for DNS management"
echo "4. Set up weighted routing for gradual migration"
echo ""
echo "To check deployment status:"
echo "  aws cloudfront get-distribution --id $DIST_ID --query 'Distribution.Status'"
echo ""
echo "======================================================"

# Optionally wait for deployment
read -p "Do you want to wait for deployment to complete? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    wait_for_deployment "$DIST_ID"
fi

echo ""
echo "CloudFront setup completed at $(date)"
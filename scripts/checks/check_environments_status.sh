#!/bin/bash

# Environment Status Check Script
# Provides quick overview of staging and production environments

echo "====================================================="
echo "     ChatMRPT ENVIRONMENT STATUS CHECK"
echo "     $(date)"
echo "====================================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check endpoint health
check_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    printf "%-30s" "$name:"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✅ OK${NC} (HTTP $response)"
    else
        echo -e "${RED}❌ FAILED${NC} (HTTP $response)"
    fi
}

echo "🌍 STAGING ENVIRONMENT"
echo "======================"
echo ""
echo "📡 Endpoints:"
check_endpoint "ALB Health" "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ping"
check_endpoint "Instance 1 (3.21.167.170)" "http://3.21.167.170:8080/ping"
check_endpoint "Instance 2 (18.220.103.20)" "http://18.220.103.20:8080/ping"

echo ""
echo "🔧 Configuration:"
echo "  - Instances: 2 (t3.large)"
echo "  - Redis: chatmrpt-redis-staging"
echo "  - Region: us-east-2"
echo "  - Security Groups: sg-0b21586985a0bbfbe, sg-0a003f4d6500485b9"

echo ""
echo "=================================================="
echo ""

echo "🚀 PRODUCTION ENVIRONMENT"
echo "========================="
echo ""
echo "📡 Endpoints:"
check_endpoint "CloudFront CDN" "https://d225ar6c86586s.cloudfront.net/ping"
check_endpoint "ALB Health" "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/ping"

echo ""
echo "🔧 Configuration:"
echo "  - Instances: 2 (t3.large) - No public IPs"
echo "  - Redis: chatmrpt-redis-production"
echo "  - Region: us-east-2"
echo "  - CloudFront: d225ar6c86586s.cloudfront.net"

echo ""
echo "=================================================="
echo ""

echo "💰 COST ANALYSIS"
echo "================"
echo ""
echo "Current Setup (Monthly):"
echo "  Staging:    ~\$235"
echo "  Production: ~\$255"
echo -e "  ${YELLOW}TOTAL:      ~\$490${NC}"
echo ""
echo "After Consolidation:"
echo -e "  ${GREEN}New Total:  ~\$260${NC}"
echo -e "  ${GREEN}Savings:    ~\$230/month (\$2,760/year)${NC}"

echo ""
echo "=================================================="
echo ""

echo "📊 RESOURCE SUMMARY"
echo "==================="
echo ""
printf "%-20s %-15s %-15s\n" "Resource" "Current" "After Transition"
printf "%-20s %-15s %-15s\n" "--------" "-------" "----------------"
printf "%-20s %-15s %-15s\n" "EC2 Instances" "4" "2"
printf "%-20s %-15s %-15s\n" "Load Balancers" "2" "1"
printf "%-20s %-15s %-15s\n" "Redis Clusters" "2" "1"
printf "%-20s %-15s %-15s\n" "CloudFront" "1" "1"

echo ""
echo "=================================================="
echo ""

# Check if AWS CLI is available for more details
if command -v aws &> /dev/null; then
    echo "📈 LIVE METRICS (requires AWS credentials)"
    echo "==========================================="
    echo ""
    
    # Try to get instance states
    echo "Checking EC2 instance states..."
    aws ec2 describe-instances \
        --instance-ids i-0994615951d0b9563 i-0f3b25b72f18a5037 i-06d3edfcc85a1f1c7 i-0183aaf795bf8f24e \
        --query "Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key=='Name'].Value|[0]]" \
        --output table 2>/dev/null || echo "  (AWS CLI not configured)"
else
    echo "ℹ️  Install AWS CLI for live metrics"
fi

echo ""
echo "=================================================="
echo ""
echo "✅ RECOMMENDATION: Proceed with staging-to-production transition"
echo "   Estimated savings: \$230/month (\$2,760/year)"
echo ""
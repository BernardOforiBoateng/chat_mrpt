#!/bin/bash

# =====================================================
# CloudWatch Monitoring Setup for ChatMRPT Transition
# =====================================================
# Purpose: Set up CloudWatch alarms and monitoring for staging environment
# Date: August 27, 2025
# =====================================================

set -e

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
STAGING_IP="3.21.167.170"
AWS_REGION="us-east-2"
SNS_EMAIL="admin@chatmrpt.com"  # Change this to your email
ALB_NAME="chatmrpt-staging-alb"
TARGET_GROUP_NAME="chatmrpt-staging-targets"

# Instance IDs
INSTANCE1_ID="i-0994615951d0b9563"
INSTANCE2_ID="i-0f3b25b72f18a5037"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================================"
echo "   CLOUDWATCH MONITORING SETUP"
echo "   $(date)"
echo "======================================================"
echo ""

# Function to create alarm via AWS CLI on staging server
create_alarm() {
    local alarm_name=$1
    local metric_name=$2
    local namespace=$3
    local statistic=$4
    local period=$5
    local threshold=$6
    local comparison=$7
    local description=$8
    local dimensions=$9
    
    echo "Creating alarm: $alarm_name"
    
    ssh -i $KEY_PATH ec2-user@$STAGING_IP << EOF 2>/dev/null
        export AWS_DEFAULT_REGION=$AWS_REGION
        
        aws cloudwatch put-metric-alarm \
            --alarm-name "$alarm_name" \
            --alarm-description "$description" \
            --metric-name "$metric_name" \
            --namespace "$namespace" \
            --statistic "$statistic" \
            --period $period \
            --threshold $threshold \
            --comparison-operator "$comparison" \
            --evaluation-periods 2 \
            --datapoints-to-alarm 2 \
            --treat-missing-data notBreaching \
            $dimensions \
            --output json > /tmp/alarm_result.json 2>&1
        
        if [ \$? -eq 0 ]; then
            echo "✅ Alarm created: $alarm_name"
        else
            echo "❌ Failed to create alarm: $alarm_name"
            cat /tmp/alarm_result.json
        fi
EOF
}

echo -e "${YELLOW}Setting up CloudWatch Alarms...${NC}"
echo "=========================================="
echo ""

# 1. CPU Utilization Alarms for Instances
echo "1. Creating CPU utilization alarms..."
create_alarm \
    "ChatMRPT-Staging-Instance1-HighCPU" \
    "CPUUtilization" \
    "AWS/EC2" \
    "Average" \
    300 \
    80 \
    "GreaterThanThreshold" \
    "Instance 1 CPU above 80%" \
    "--dimensions Name=InstanceId,Value=$INSTANCE1_ID"

create_alarm \
    "ChatMRPT-Staging-Instance2-HighCPU" \
    "CPUUtilization" \
    "AWS/EC2" \
    "Average" \
    300 \
    80 \
    "GreaterThanThreshold" \
    "Instance 2 CPU above 80%" \
    "--dimensions Name=InstanceId,Value=$INSTANCE2_ID"

echo ""

# 2. Memory Utilization (requires CloudWatch agent)
echo "2. Setting up CloudWatch agent for memory monitoring..."
ssh -i $KEY_PATH ec2-user@$STAGING_IP << 'EOF' 2>/dev/null
    # Check if CloudWatch agent is installed
    if ! command -v amazon-cloudwatch-agent-ctl &> /dev/null; then
        echo "Installing CloudWatch agent..."
        wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
        sudo rpm -U ./amazon-cloudwatch-agent.rpm
    fi
    
    # Create CloudWatch agent config
    cat > /tmp/cloudwatch-config.json << 'CONFIG'
{
    "metrics": {
        "namespace": "ChatMRPT/Staging",
        "metrics_collected": {
            "mem": {
                "measurement": [
                    {
                        "name": "mem_used_percent",
                        "rename": "MemoryUtilization"
                    }
                ],
                "metrics_collection_interval": 60
            },
            "disk": {
                "measurement": [
                    {
                        "name": "used_percent",
                        "rename": "DiskUtilization"
                    }
                ],
                "metrics_collection_interval": 60,
                "resources": ["/"]
            }
        }
    }
}
CONFIG
    
    # Start CloudWatch agent
    sudo amazon-cloudwatch-agent-ctl \
        -a query -m ec2 -n default 2>/dev/null || \
    sudo amazon-cloudwatch-agent-ctl \
        -a fetch-config -m ec2 -s \
        -c file:/tmp/cloudwatch-config.json 2>/dev/null
    
    echo "CloudWatch agent configured"
EOF

echo ""

# 3. ALB Target Health Alarms
echo "3. Creating ALB target health alarms..."
create_alarm \
    "ChatMRPT-Staging-UnhealthyTargets" \
    "UnHealthyHostCount" \
    "AWS/ApplicationELB" \
    "Average" \
    60 \
    1 \
    "GreaterThanOrEqualToThreshold" \
    "One or more unhealthy targets" \
    "--dimensions Name=LoadBalancer,Value=app/$ALB_NAME/b1a492e6e8f06bcd Name=TargetGroup,Value=targetgroup/$TARGET_GROUP_NAME/dc7f0a7e27d6e7f2"

echo ""

# 4. ALB Response Time Alarm
echo "4. Creating ALB response time alarm..."
create_alarm \
    "ChatMRPT-Staging-HighResponseTime" \
    "TargetResponseTime" \
    "AWS/ApplicationELB" \
    "Average" \
    60 \
    2 \
    "GreaterThanThreshold" \
    "Response time above 2 seconds" \
    "--dimensions Name=LoadBalancer,Value=app/$ALB_NAME/b1a492e6e8f06bcd"

echo ""

# 5. ALB HTTP Error Rate Alarms
echo "5. Creating HTTP error rate alarms..."
create_alarm \
    "ChatMRPT-Staging-HTTP-5xx-Errors" \
    "HTTPCode_Target_5XX_Count" \
    "AWS/ApplicationELB" \
    "Sum" \
    300 \
    10 \
    "GreaterThanThreshold" \
    "More than 10 5xx errors in 5 minutes" \
    "--dimensions Name=LoadBalancer,Value=app/$ALB_NAME/b1a492e6e8f06bcd"

create_alarm \
    "ChatMRPT-Staging-HTTP-4xx-Errors" \
    "HTTPCode_Target_4XX_Count" \
    "AWS/ApplicationELB" \
    "Sum" \
    300 \
    50 \
    "GreaterThanThreshold" \
    "More than 50 4xx errors in 5 minutes" \
    "--dimensions Name=LoadBalancer,Value=app/$ALB_NAME/b1a492e6e8f06bcd"

echo ""

# 6. Redis Monitoring
echo "6. Creating Redis monitoring alarms..."
create_alarm \
    "ChatMRPT-Redis-HighCPU" \
    "CPUUtilization" \
    "AWS/ElastiCache" \
    "Average" \
    300 \
    75 \
    "GreaterThanThreshold" \
    "Redis CPU above 75%" \
    "--dimensions Name=CacheClusterId,Value=chatmrpt-redis-staging"

create_alarm \
    "ChatMRPT-Redis-HighMemory" \
    "DatabaseMemoryUsagePercentage" \
    "AWS/ElastiCache" \
    "Average" \
    300 \
    80 \
    "GreaterThanThreshold" \
    "Redis memory above 80%" \
    "--dimensions Name=CacheClusterId,Value=chatmrpt-redis-staging"

echo ""

# 7. Create CloudWatch Dashboard
echo -e "${YELLOW}Creating CloudWatch Dashboard...${NC}"
echo "=========================================="

ssh -i $KEY_PATH ec2-user@$STAGING_IP << 'EOF' 2>/dev/null
    export AWS_DEFAULT_REGION=us-east-2
    
    cat > /tmp/dashboard.json << 'DASHBOARD'
{
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/EC2", "CPUUtilization", {"stat": "Average", "label": "Instance 1"}, {"id": "m1"}],
                    ["...", {"stat": "Average", "label": "Instance 2"}, {"id": "m2"}]
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-2",
                "title": "EC2 CPU Utilization",
                "yAxis": {"left": {"min": 0, "max": 100}}
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/ApplicationELB", "TargetResponseTime", {"stat": "Average"}],
                    [".", "RequestCount", {"stat": "Sum", "yAxis": "right"}]
                ],
                "period": 60,
                "stat": "Average",
                "region": "us-east-2",
                "title": "ALB Performance"
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/ApplicationELB", "HTTPCode_Target_2XX_Count", {"stat": "Sum", "color": "#2ca02c"}],
                    [".", "HTTPCode_Target_4XX_Count", {"stat": "Sum", "color": "#ff7f0e"}],
                    [".", "HTTPCode_Target_5XX_Count", {"stat": "Sum", "color": "#d62728"}]
                ],
                "period": 300,
                "stat": "Sum",
                "region": "us-east-2",
                "title": "HTTP Response Codes",
                "stacked": true
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/ElastiCache", "CPUUtilization", {"stat": "Average"}],
                    [".", "DatabaseMemoryUsagePercentage", {"stat": "Average", "yAxis": "right"}]
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-2",
                "title": "Redis Performance"
            }
        }
    ]
}
DASHBOARD
    
    aws cloudwatch put-dashboard \
        --dashboard-name "ChatMRPT-Staging-Transition" \
        --dashboard-body file:///tmp/dashboard.json \
        --output json > /tmp/dashboard_result.json 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✅ Dashboard created: ChatMRPT-Staging-Transition"
        echo "   View at: https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#dashboards:name=ChatMRPT-Staging-Transition"
    else
        echo "❌ Failed to create dashboard"
        cat /tmp/dashboard_result.json
    fi
EOF

echo ""
echo "======================================================"
echo -e "${GREEN}   CLOUDWATCH SETUP COMPLETE!${NC}"
echo "======================================================"
echo ""
echo "Monitoring Setup Summary:"
echo "------------------------"
echo "✅ CPU utilization alarms for both instances"
echo "✅ ALB target health monitoring"
echo "✅ Response time monitoring (2 second threshold)"
echo "✅ HTTP error rate monitoring"
echo "✅ Redis performance monitoring"
echo "✅ CloudWatch dashboard created"
echo ""
echo "Dashboard URL:"
echo "https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#dashboards:name=ChatMRPT-Staging-Transition"
echo ""
echo "Note: Some metrics may take 5-10 minutes to appear"
echo ""
echo "Next Steps:"
echo "1. Configure SNS notifications for alarms (optional)"
echo "2. Test the staging environment with production-like load"
echo "3. Monitor dashboard during the transition"
echo "======================================================"
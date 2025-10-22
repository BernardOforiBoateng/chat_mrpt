#!/bin/bash

echo "================================================"
echo "    AWS EC2 Instance Cost Analysis for ChatMRPT"
echo "================================================"

REGION="us-east-2"

# Get all running instances
echo -e "\n📊 CURRENT RUNNING INSTANCES:"
echo "----------------------------------------"

aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].[
        Tags[?Key==`Name`]|[0].Value,
        InstanceId,
        InstanceType,
        State.Name,
        PublicIpAddress,
        PrivateIpAddress,
        LaunchTime
    ]' \
    --output table

echo -e "\n💰 INSTANCE TYPE PRICING (On-Demand, us-east-2):"
echo "----------------------------------------"

# Production and Staging instances
echo "t3.medium (Current staging/prod): $0.0416/hour = $30.37/month"
echo "t3.large: $0.0832/hour = $60.74/month"
echo "t3.xlarge: $0.1664/hour = $121.47/month"

echo -e "\n🎮 GPU INSTANCE PRICING:"
echo "----------------------------------------"
echo "g4dn.xlarge (T4 GPU, 16GB): $0.526/hour = $384.08/month"
echo "g4dn.2xlarge (T4 GPU, 16GB): $0.752/hour = $548.96/month"
echo "g5.xlarge (A10G GPU, 24GB): $1.006/hour = $734.38/month"
echo "g5.2xlarge (A10G GPU, 24GB): $1.212/hour = $884.76/month"
echo "p3.2xlarge (V100 GPU, 16GB): $3.06/hour = $2,233.80/month"

echo -e "\n📦 STORAGE COSTS:"
echo "----------------------------------------"
echo "EBS gp3: $0.08/GB/month"
echo "EBS gp2: $0.10/GB/month"

# Check for GPU instances specifically
echo -e "\n🖥️ GPU INSTANCES (if any):"
echo "----------------------------------------"

aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=instance-state-name,Values=running,stopped" \
    --query 'Reservations[*].Instances[?contains(InstanceType, `g`) || contains(InstanceType, `p`)].[
        Tags[?Key==`Name`]|[0].Value,
        InstanceId,
        InstanceType,
        State.Name,
        PublicIpAddress,
        PrivateIpAddress
    ]' \
    --output table

# Check total monthly cost estimate
echo -e "\n💵 ESTIMATED MONTHLY COSTS:"
echo "----------------------------------------"

# Count instances by type
t3_medium_count=$(aws ec2 describe-instances --region $REGION --filters "Name=instance-state-name,Values=running" "Name=instance-type,Values=t3.medium" --query 'Reservations[*].Instances[*].[InstanceId]' --output text | wc -w)
t3_large_count=$(aws ec2 describe-instances --region $REGION --filters "Name=instance-state-name,Values=running" "Name=instance-type,Values=t3.large" --query 'Reservations[*].Instances[*].[InstanceId]' --output text | wc -w)
gpu_count=$(aws ec2 describe-instances --region $REGION --filters "Name=instance-state-name,Values=running" --query 'Reservations[*].Instances[?contains(InstanceType, `g`) || contains(InstanceType, `p`)].[InstanceId]' --output text | wc -w)

echo "Current Running Instances:"
echo "  t3.medium: $t3_medium_count instances = \$$(echo "$t3_medium_count * 30.37" | bc -l | cut -d. -f1-2)/month"
echo "  t3.large: $t3_large_count instances = \$$(echo "$t3_large_count * 60.74" | bc -l | cut -d. -f1-2)/month"

if [ $gpu_count -gt 0 ]; then
    echo "  GPU instances: $gpu_count (check specific types above for pricing)"
fi

# Total for non-GPU instances
total_monthly=$(echo "($t3_medium_count * 30.37) + ($t3_large_count * 60.74)" | bc -l | cut -d. -f1-2)
echo -e "\nTotal (excluding GPU): \$$total_monthly/month"

echo -e "\n📝 COST OPTIMIZATION TIPS:"
echo "----------------------------------------"
echo "1. Use Spot Instances for dev/test (up to 70% savings)"
echo "2. Reserved Instances for production (up to 40% savings)"
echo "3. Stop instances when not in use"
echo "4. Use AWS Lambda for intermittent workloads"
echo "5. Consider Savings Plans for predictable usage"

echo -e "\n🔧 RECOMMENDED SETUP FOR ARENA MODE:"
echo "----------------------------------------"
echo "Option 1 - Budget (~\$450/month):"
echo "  • 2x t3.medium (staging/prod): \$60.74"
echo "  • 1x g4dn.xlarge (vLLM GPU): \$384.08"
echo "  • Total: ~\$445/month"
echo ""
echo "Option 2 - Performance (~\$795/month):"
echo "  • 2x t3.large (staging/prod): \$121.48"
echo "  • 1x g5.xlarge (better GPU): \$734.38"
echo "  • Total: ~\$856/month"
echo ""
echo "Option 3 - Cost-Optimized (~\$250/month):"
echo "  • 2x t3.medium: \$60.74"
echo "  • g4dn.xlarge Spot (12hrs/day): ~\$115"
echo "  • Use Ollama for light queries"
echo "  • Total: ~\$176/month"
#!/bin/bash

# Complete State Management Fix Deployment
# Deploys all phases of the state management solution

echo "🚀 Deploying Complete State Management Solution..."
echo "================================================"
echo ""
echo "This deployment includes:"
echo "✅ Phase 1: Immediate stabilization fixes"
echo "✅ Phase 2: Centralized WorkflowStateManager"
echo "✅ Proper workflow transitions and marker cleanup"
echo "✅ State validation and recovery mechanisms"
echo ""

# Files to deploy
FILES=(
    # Core state management
    "app/core/workflow_state_manager.py"  # NEW centralized state manager
    "app/core/request_interpreter.py"     # Updated to use state manager
    
    # Route updates
    "app/web/routes/data_analysis_v3_routes.py"  # Proper workflow transitions
    
    # Workflow handlers
    "app/data_analysis_v3/core/tpr_workflow_handler.py"  # Uses state manager
    
    # Tools
    "app/tools/complete_analysis_tools.py"  # Sets workflow stage properly
)

# Check if deploying to staging or production
if [[ "$1" == "production" ]]; then
    echo "📦 Deploying to PRODUCTION (2 instances)..."
    INSTANCES=("172.31.44.52" "172.31.43.200")
    ENVIRONMENT="production"
elif [[ "$1" == "staging" ]]; then
    echo "📦 Deploying to STAGING (2 instances)..."
    # Updated staging IPs as of Jan 7, 2025
    INSTANCES=("3.21.167.170" "18.220.103.20")
    ENVIRONMENT="staging"
else
    echo "❌ Usage: $0 [staging|production]"
    echo ""
    echo "Examples:"
    echo "  ./deploy_complete_state_fix.sh staging    # Deploy to staging first"
    echo "  ./deploy_complete_state_fix.sh production # Deploy to production"
    exit 1
fi

# SSH key location
SSH_KEY="/tmp/chatmrpt-key2.pem"
if [ ! -f "$SSH_KEY" ]; then
    # Try to copy from standard location
    if [ -f "aws_files/chatmrpt-key.pem" ]; then
        cp aws_files/chatmrpt-key.pem "$SSH_KEY"
        chmod 600 "$SSH_KEY"
        echo "✅ SSH key prepared"
    else
        echo "❌ SSH key not found at aws_files/chatmrpt-key.pem"
        exit 1
    fi
fi

# Track deployment status
FAILED_INSTANCES=()

# Deploy to each instance
for INSTANCE in "${INSTANCES[@]}"; do
    echo ""
    echo "🔄 Deploying to instance: $INSTANCE"
    echo "═══════════════════════════════════"
    
    # Test SSH connectivity first
    echo "  🔌 Testing connectivity..."
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
        "ec2-user@$INSTANCE" "echo '  ✅ Connected successfully'" 2>/dev/null
    
    if [ $? -ne 0 ]; then
        echo "  ❌ Cannot connect to $INSTANCE"
        FAILED_INSTANCES+=("$INSTANCE")
        continue
    fi
    
    # Create necessary directories
    echo "  📁 Ensuring directories exist..."
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
        "mkdir -p /home/ec2-user/ChatMRPT/app/core \
                 /home/ec2-user/ChatMRPT/app/web/routes \
                 /home/ec2-user/ChatMRPT/app/data_analysis_v3/core \
                 /home/ec2-user/ChatMRPT/app/tools"
    
    # Copy files with progress indication
    COPY_FAILED=false
    for FILE in "${FILES[@]}"; do
        echo -n "  📄 Copying $(basename $FILE)... "
        
        scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -q \
            "$FILE" "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/$FILE" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "✅"
        else
            echo "❌"
            echo "     Failed to copy $FILE to $INSTANCE"
            COPY_FAILED=true
            FAILED_INSTANCES+=("$INSTANCE")
            break
        fi
    done
    
    if [ "$COPY_FAILED" = true ]; then
        continue
    fi
    
    echo "  ✅ All files copied successfully"
    
    # Restart the service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
        "sudo systemctl restart chatmrpt" 2>/dev/null
    
    # Wait a moment for service to start
    sleep 2
    
    # Check service status
    echo "  📊 Verifying service status..."
    SERVICE_STATUS=$(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
        "sudo systemctl is-active chatmrpt" 2>/dev/null)
    
    if [ "$SERVICE_STATUS" = "active" ]; then
        echo "  ✅ Service is running on $INSTANCE"
        
        # Check for startup errors in logs
        echo "  📋 Checking recent logs..."
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
            "sudo journalctl -u chatmrpt -n 20 --no-pager | grep -E '(ERROR|CRITICAL|Failed)' | head -5" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "  ⚠️  Some errors found in logs (see above)"
        else
            echo "  ✅ No critical errors in recent logs"
        fi
    else
        echo "  ❌ Service is not running properly on $INSTANCE"
        FAILED_INSTANCES+=("$INSTANCE")
    fi
done

echo ""
echo "════════════════════════════════════════════"

# Report deployment status
if [ ${#FAILED_INSTANCES[@]} -eq 0 ]; then
    echo "✅ DEPLOYMENT SUCCESSFUL to all instances in $ENVIRONMENT!"
else
    echo "⚠️  PARTIAL DEPLOYMENT to $ENVIRONMENT"
    echo "Failed instances: ${FAILED_INSTANCES[@]}"
    echo "Please check these instances manually."
fi

echo ""
echo "📋 What This Deployment Fixed:"
echo "────────────────────────────────"
echo "1. ✅ Stale marker files causing false 'analysis complete' messages"
echo "2. ✅ Workflow transitions not clearing previous state properly"
echo "3. ✅ Multiple competing state storage mechanisms"
echo "4. ✅ Session state contamination across workflows"
echo "5. ✅ Worker inconsistencies in multi-instance deployment"
echo ""
echo "🏗️ Architecture Improvements:"
echo "────────────────────────────────"
echo "• WorkflowStateManager: Single source of truth for all state"
echo "• Automatic validation and cleanup of inconsistent states"
echo "• Proper workflow transitions with marker cleanup"
echo "• State versioning for future migrations"
echo "• Comprehensive logging of state transitions"
echo ""
echo "🧪 Testing Checklist:"
echo "────────────────────────────────"
echo "□ 1. Upload file via Data Analysis tab"
echo "□ 2. Complete TPR analysis"
echo "□ 3. Transition to main workflow (should be seamless)"
echo "□ 4. Request risk analysis (should NOT say 'already completed')"
echo "□ 5. Complete the risk analysis"
echo "□ 6. Upload new data (should start fresh, no stale state)"
echo "□ 7. Test with multiple concurrent sessions"
echo ""

if [[ "$ENVIRONMENT" == "staging" ]]; then
    echo "🌐 Test URL: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
    echo ""
    echo "📝 Next Steps:"
    echo "1. Test thoroughly in staging"
    echo "2. Monitor logs: ssh to instance and run: sudo journalctl -u chatmrpt -f"
    echo "3. If all tests pass, deploy to production:"
    echo "   ./deploy_complete_state_fix.sh production"
elif [[ "$ENVIRONMENT" == "production" ]]; then
    echo "🌐 Production URL: https://d225ar6c86586s.cloudfront.net"
    echo ""
    echo "⚠️  POST-DEPLOYMENT MONITORING:"
    echo "1. Monitor CloudWatch logs for any errors"
    echo "2. Test the complete workflow immediately"
    echo "3. Monitor user sessions for the next hour"
fi

echo ""
echo "📊 Verification Commands:"
echo "────────────────────────────────"
echo "Check logs:    ssh -i $SSH_KEY ec2-user@<instance> 'sudo journalctl -u chatmrpt -f'"
echo "Check state:   ssh -i $SSH_KEY ec2-user@<instance> 'ls -la /home/ec2-user/ChatMRPT/instance/uploads/*/'"
echo "Check markers: ssh -i $SSH_KEY ec2-user@<instance> 'find /home/ec2-user/ChatMRPT/instance/uploads -name \".*\" -type f'"
echo ""
echo "Deployment completed at: $(date)"
#!/bin/bash

# Phase 2 State Management Fix Deployment
# Deploys centralized WorkflowStateManager implementation

echo "🚀 Deploying Phase 2 State Management Fixes (Centralized State Manager)..."
echo "========================================"
echo "Changes:"
echo "1. Add WorkflowStateManager class as single source of truth"
echo "2. Update request_interpreter.py to use WorkflowStateManager"
echo "3. Update data_analysis_v3_routes.py for proper transitions"
echo "4. Update tpr_workflow_handler.py to use centralized transitions"
echo ""

# Files to deploy
FILES=(
    "app/core/workflow_state_manager.py"  # NEW centralized state manager
    "app/core/request_interpreter.py"
    "app/web/routes/data_analysis_v3_routes.py"
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
    "app/tools/complete_analysis_tools.py"
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

# Deploy to each instance
for INSTANCE in "${INSTANCES[@]}"; do
    echo ""
    echo "🔄 Deploying to instance: $INSTANCE"
    echo "-----------------------------------"
    
    # Copy files
    for FILE in "${FILES[@]}"; do
        echo "  📄 Copying $FILE..."
        
        # Check if it's a new file that needs directory creation
        if [[ "$FILE" == "app/core/workflow_state_manager.py" ]]; then
            # Ensure directory exists first
            ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
                "mkdir -p /home/ec2-user/ChatMRPT/app/core"
        fi
        
        scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
            "$FILE" "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/$FILE"
        
        if [ $? -ne 0 ]; then
            echo "  ❌ Failed to copy $FILE to $INSTANCE"
            exit 1
        fi
    done
    
    echo "  ✅ Files copied successfully"
    
    # Restart the service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
        "sudo systemctl restart chatmrpt && echo '  ✅ Service restarted'"
    
    # Check service status
    echo "  📊 Checking service status..."
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
        "sudo systemctl is-active chatmrpt" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Service is running on $INSTANCE"
    else
        echo "  ⚠️  Service may not be running properly on $INSTANCE"
    fi
done

echo ""
echo "✅ Phase 2 deployment complete to $ENVIRONMENT!"
echo ""
echo "📋 Key improvements in this phase:"
echo "• Single source of truth for workflow state (WorkflowStateManager)"
echo "• Automatic validation and cleanup of inconsistent states"
echo "• Proper workflow transitions with marker cleanup"
echo "• State versioning for future migrations"
echo "• Comprehensive state tracking with transition history"
echo ""
echo "📋 Testing recommendations:"
echo "1. Upload file via Data Analysis tab → Complete TPR → Transition to main"
echo "2. Verify no 'already completed' messages when requesting new analysis"
echo "3. Complete risk analysis → Upload new data → Verify clean slate"
echo "4. Check logs for state validation and transition messages"
echo "5. Test with multiple concurrent sessions"
echo ""

if [[ "$ENVIRONMENT" == "staging" ]]; then
    echo "🌐 Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
elif [[ "$ENVIRONMENT" == "production" ]]; then
    echo "🌐 Test at: https://d225ar6c86586s.cloudfront.net"
fi

echo ""
echo "📚 State Manager API:"
echo "  • WorkflowStateManager(session_id) - Initialize for session"
echo "  • get_state() - Get full state dictionary"
echo "  • update_state(updates, reason) - Update with validation"
echo "  • transition_workflow(from, to, stage, markers) - Clean transitions"
echo "  • is_analysis_complete() - Context-aware completion check"
echo "  • validate_state() - Check for inconsistencies"
echo "  • reset() - Clean slate for testing/recovery"
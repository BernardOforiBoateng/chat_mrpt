#!/bin/bash
# Deployment script for Issue #2: Multi-Level Visualization Toggles
# Deploys to BOTH production instances

set -e  # Exit on error

echo "========================================"
echo "Multi-Level Visualization Deployment"
echo "Issue #2: Geographic Level Toggles"
echo "========================================"
echo ""

# Production instances
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"
KEY="/tmp/chatmrpt-key.pem"

# Files to deploy
BACKEND_FILES=(
    "app/services/geographic_aggregation_service.py"
    "app/tools/variable_distribution.py"
    "app/tools/visualization_maps_tools.py"
    "app/services/agents/visualizations/composite_visualizations.py"
    "app/tools/itn_planning_tools.py"
    "app/analysis/itn_pipeline.py"
    "app/web/routes/visualization_routes.py"
    "app/reference_data/nga_lga_boundaries.gpkg"
)

FRONTEND_SRC_FILES=(
    "frontend/src/components/Visualization/VisualizationControls.tsx"
    "frontend/src/components/Visualization/VisualizationContainer.tsx"
)

TEST_FILES=(
    "tests/test_multilevel_visualization_integration.py"
)

# Function to deploy to a single instance
deploy_to_instance() {
    local INSTANCE=$1
    echo ""
    echo "========================================"
    echo "Deploying to Instance: $INSTANCE"
    echo "========================================"

    # Deploy backend files
    echo "📦 Deploying backend files..."
    for file in "${BACKEND_FILES[@]}"; do
        echo "  - $file"
        scp -i "$KEY" "$file" "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/$file"
    done

    # Deploy frontend source files (for reference)
    echo "📦 Deploying frontend source files..."
    for file in "${FRONTEND_SRC_FILES[@]}"; do
        echo "  - $file"
        scp -i "$KEY" "$file" "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/$file"
    done

    # Deploy compiled React build (CRITICAL - this is what the browser loads)
    echo "📦 Deploying compiled React build..."
    echo "  - Removing old build on remote..."
    ssh -i "$KEY" "ec2-user@$INSTANCE" "rm -rf /home/ec2-user/ChatMRPT/app/static/react/*"
    echo "  - Uploading new build..."
    scp -i "$KEY" -r app/static/react/* "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/app/static/react/"

    # Deploy test files
    echo "📦 Deploying test files..."
    for file in "${TEST_FILES[@]}"; do
        echo "  - $file"
        scp -i "$KEY" "$file" "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/$file"
    done

    # Restart service
    echo "🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY" "ec2-user@$INSTANCE" "sudo systemctl restart chatmrpt"

    # Wait for service to start
    echo "⏳ Waiting for service to start..."
    sleep 5

    # Check service status
    echo "✅ Checking service status..."
    ssh -i "$KEY" "ec2-user@$INSTANCE" "sudo systemctl status chatmrpt --no-pager | head -20"

    echo ""
    echo "✅ Deployment to $INSTANCE complete!"
}

# Deploy to both instances
echo "Starting deployment to BOTH production instances..."
echo ""

deploy_to_instance "$INSTANCE1"
deploy_to_instance "$INSTANCE2"

echo ""
echo "========================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "========================================"
echo ""
echo "Deployed to:"
echo "  - Instance 1: $INSTANCE1"
echo "  - Instance 2: $INSTANCE2"
echo ""
echo "Files deployed:"
echo "  - Backend: ${#BACKEND_FILES[@]} files"
echo "  - Frontend: ${#FRONTEND_SRC_FILES[@]} source files + compiled React build"
echo "  - Tests: ${#TEST_FILES[@]} files"
echo ""
echo "Next steps:"
echo "  1. Test visualization level toggles in production"
echo "  2. Verify LGA filter functionality"
echo "  3. Monitor logs for any errors"
echo ""
echo "CloudFront URL: https://d225ar6c86586s.cloudfront.net"
echo ""

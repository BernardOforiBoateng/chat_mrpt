#\!/bin/bash
# Deploy fuzzy matching and ITN export fixes to AWS
# This includes ward name matching, ITN colors, and export download fixes

set -e

echo "🚀 Deploying fuzzy matching and ITN export fixes to AWS..."

# AWS instance details
AWS_HOST="ec2-3-137-158-17.us-east-2.compute.amazonaws.com"
AWS_KEY="~/Downloads/chatmrpt-aws-key.pem"
AWS_USER="ubuntu"

# Files to deploy
FILES_TO_DEPLOY=(
    "app/data/unified_dataset_builder.py"
    "app/data/population_data/itn_population_loader.py"
    "app/analysis/itn_pipeline.py"
    "app/tools/export_tools.py"
    "app/web/routes/export_routes.py"
    "requirements.txt"
)

echo "📦 Creating deployment package..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
DEPLOY_PACKAGE="$TEMP_DIR/fuzzy_matching_deploy.tar.gz"

# Copy files to temp directory preserving structure
for file in "${FILES_TO_DEPLOY[@]}"; do
    mkdir -p "$TEMP_DIR/$(dirname $file)"
    cp "$file" "$TEMP_DIR/$file"
done

# Create tarball
cd "$TEMP_DIR"
tar -czf fuzzy_matching_deploy.tar.gz *
cd -

echo "📤 Uploading to AWS..."
scp -i "$AWS_KEY" "$TEMP_DIR/fuzzy_matching_deploy.tar.gz" "$AWS_USER@$AWS_HOST:/tmp/"

echo "🔧 Applying fixes on AWS..."
ssh -i "$AWS_KEY" "$AWS_USER@$AWS_HOST" << 'ENDSSH'
set -e

echo "📂 Extracting files..."
cd /home/ubuntu/ChatMRPT
tar -xzf /tmp/fuzzy_matching_deploy.tar.gz

echo "🐍 Installing new requirements..."
source chatmrpt_venv_new/bin/activate
pip install fuzzywuzzy python-Levenshtein

echo "🔄 Restarting application..."
sudo systemctl restart chatmrpt

echo "✅ Deployment complete\!"

# Check service status
sleep 5
sudo systemctl status chatmrpt --no-pager

# Clean up
rm /tmp/fuzzy_matching_deploy.tar.gz
ENDSSH

# Clean up local temp files
rm -rf "$TEMP_DIR"

echo "✨ Fuzzy matching fixes deployed successfully\!"
echo "🔍 Key changes deployed:"
echo "   - Ward name fuzzy matching (80% similarity threshold)"
echo "   - ITN map colors changed to purple/yellow (Plasma)"
echo "   - Export download link added to messages"
echo "   - ITN population loader updated for new format"
echo "   - Export routes fixed for multiple directory patterns"
EOF < /dev/null

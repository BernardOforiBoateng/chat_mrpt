#!/bin/bash
# Deploy fuzzy matching fixes to AWS using specific environment

set -e

echo "🚀 Deploying fuzzy matching and ITN export fixes to AWS..."

# AWS instance details
AWS_HOST="ec2-3-137-158-17.us-east-2.compute.amazonaws.com"
AWS_KEY="~/Downloads/chatmrpt-aws-key.pem"
AWS_USER="ubuntu"

# Navigate to project directory
cd /mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT

# Activate virtual environment
source chatmrpt_venv_new/bin/activate

# Set environment variables
export FLASK_ENV=development
export ADMIN_KEY=temp_admin_key

echo "📦 Creating deployment package..."

# Files to deploy with fuzzy matching fixes
FILES_TO_DEPLOY=(
    "app/data/unified_dataset_builder.py"
    "app/data/population_data/itn_population_loader.py" 
    "app/analysis/itn_pipeline.py"
    "app/tools/export_tools.py"
    "app/web/routes/export_routes.py"
)

# Create deployment package
tar -czf fuzzy_fix_deploy.tar.gz "${FILES_TO_DEPLOY[@]}"

echo "📤 Uploading to AWS..."
scp -i "$AWS_KEY" fuzzy_fix_deploy.tar.gz "$AWS_USER@$AWS_HOST:/tmp/"

echo "🔧 Applying fixes on AWS..."
ssh -i "$AWS_KEY" "$AWS_USER@$AWS_HOST" << 'ENDSSH'
set -e

echo "📂 Backing up current files..."
cd /home/ubuntu/ChatMRPT
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp -r app/data backups/$(date +%Y%m%d_%H%M%S)/
cp -r app/analysis backups/$(date +%Y%m%d_%H%M%S)/
cp -r app/tools backups/$(date +%Y%m%d_%H%M%S)/
cp -r app/web/routes backups/$(date +%Y%m%d_%H%M%S)/

echo "📥 Extracting new files..."
tar -xzf /tmp/fuzzy_fix_deploy.tar.gz

echo "🐍 Installing fuzzy matching dependencies..."
source chatmrpt_venv_new/bin/activate
pip install fuzzywuzzy python-Levenshtein

echo "🔄 Restarting service..."
sudo systemctl restart chatmrpt

echo "✅ Deployment complete!"
sleep 5

# Check service status
echo "📊 Service status:"
sudo systemctl status chatmrpt --no-pager | head -20

# Check for errors
echo "📋 Recent logs:"
sudo journalctl -u chatmrpt -n 50 --no-pager | grep -E "(ERROR|WARNING|Starting|Started|fuzzy|ward|ITN)"

# Clean up
rm /tmp/fuzzy_fix_deploy.tar.gz

echo "✨ Fuzzy matching fixes are now live!"
ENDSSH

# Clean up local file
rm fuzzy_fix_deploy.tar.gz

echo "
🎉 Deployment successful!

✅ Changes deployed:
   - Ward name fuzzy matching (80% threshold)  
   - ITN map colors (purple/yellow)
   - Export download links
   - ITN population loader updates
   - Export route fixes

🌐 Test the changes at: http://3.137.158.17
"
#!/bin/bash
set -e

echo "=== FIXING TPR RACE CONDITION ON PRODUCTION ==="
echo "Adding delay before session verification to allow Redis to save"
echo ""

PRODUCTION_IP="172.31.44.52"
SSH_KEY="/tmp/chatmrpt-key2.pem"

# Connect through staging to production
ssh -i $SSH_KEY ec2-user@18.117.115.217 << 'EOF'
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PROD_EOF'
cd /home/ec2-user/ChatMRPT

echo "1. Backing up file-uploader.js..."
cp app/static/js/modules/upload/file-uploader.js app/static/js/modules/upload/file-uploader.js.backup_race_fix

echo "2. Applying race condition fix..."
cat > /tmp/fix_race.py << 'PYFIX'
import re

with open('app/static/js/modules/upload/file-uploader.js', 'r') as f:
    content = f.read()

# Find the verifyTPRSessionState call and wrap it in setTimeout
old_pattern = r'(\s+// CRITICAL: Verify TPR workflow is active in backend session \(multi-worker fix\)\s+)(this\.verifyTPRSessionState\(\);)'
new_pattern = r'\1// Add delay to allow Redis session save to complete\n\1setTimeout(() => {\n\1    this.verifyTPRSessionState();\n\1}, 2000); // 2 second delay'

content = re.sub(old_pattern, new_pattern, content)

with open('app/static/js/modules/upload/file-uploader.js', 'w') as f:
    f.write(content)

print("Race condition fix applied!")
PYFIX

python3 /tmp/fix_race.py

echo "3. Verifying the fix was applied..."
grep -A5 "CRITICAL: Verify TPR" app/static/js/modules/upload/file-uploader.js

echo "4. Clearing browser cache might be needed..."
echo "Note: Users may need to hard refresh (Ctrl+F5) to get the updated JavaScript"

echo ""
echo "✅ Race condition fix applied!"
echo "The verification now waits 2 seconds before checking session state"
echo "This gives Redis time to save the session across all workers"
PROD_EOF
EOF

echo ""
echo "=== FIX COMPLETE ==="
echo "Test at: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
echo "Users should hard refresh (Ctrl+F5) to ensure they get the updated JavaScript"
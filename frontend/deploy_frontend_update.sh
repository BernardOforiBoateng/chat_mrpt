#!/bin/bash
# Deploy updated React frontend to AWS production instances

echo "🚀 Deploying updated React frontend to AWS..."

# Production Instance IPs
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# Key location
KEY="/tmp/chatmrpt-key2.pem"

# Files to deploy
FILES=(
    "app/static/react/index.html"
    "app/static/react/assets/index-Bo82ll8a.js"
    "app/static/react/assets/index-DJBuK1M4.css"
)

# Copy key if not already there
if [ ! -f "$KEY" ]; then
    echo "📋 Copying SSH key..."
    cp aws_files/chatmrpt-key.pem "$KEY"
    chmod 600 "$KEY"
fi

# Deploy to both instances
for INSTANCE in "$INSTANCE1" "$INSTANCE2"; do
    echo ""
    echo "📦 Deploying to Instance ($INSTANCE)..."
    for FILE in "${FILES[@]}"; do
        echo "  - Copying $FILE"
        scp -i "$KEY" "$FILE" "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/$FILE"
        if [ $? -ne 0 ]; then
            echo "❌ Failed to copy $FILE to $INSTANCE"
            exit 1
        fi
    done
    ssh -i "$KEY" "ec2-user@$INSTANCE" "sudo systemctl restart chatmrpt"
    echo "✅ Deployed to $INSTANCE"
done

echo ""
echo "🎉 Frontend updated!"
echo "Changed: 'Multi-Agent Data Analysis' → 'Advanced Data Analysis'"
echo "Changed: Description to reflect actual ChatMRPT capabilities"

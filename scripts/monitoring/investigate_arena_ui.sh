#!/bin/bash

echo "🔍 COMPREHENSIVE ARENA UI INVESTIGATION"
echo "========================================"
echo ""

KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE="3.21.167.170"

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    if [ -f "aws_files/chatmrpt-key.pem" ]; then
        cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
        chmod 600 /tmp/chatmrpt-key2.pem
    fi
fi

echo "1️⃣ CHECKING CSS FILES ON AWS SERVER"
echo "-----------------------------------"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$INSTANCE << 'EOF'
echo "📁 CSS files in app/static/css/:"
ls -la /home/ec2-user/ChatMRPT/app/static/css/

echo ""
echo "📏 File sizes:"
wc -l /home/ec2-user/ChatMRPT/app/static/css/*.css 2>/dev/null | head -10

echo ""
echo "🔍 Checking for Arena styles in modern-minimalist-theme.css:"
grep -c "voting-buttons" /home/ec2-user/ChatMRPT/app/static/css/modern-minimalist-theme.css || echo "NOT FOUND"
grep -c "vote-btn" /home/ec2-user/ChatMRPT/app/static/css/modern-minimalist-theme.css || echo "NOT FOUND"
grep -c "dual-response" /home/ec2-user/ChatMRPT/app/static/css/modern-minimalist-theme.css || echo "NOT FOUND"

echo ""
echo "🔍 Checking if arena.css exists:"
if [ -f /home/ec2-user/ChatMRPT/app/static/css/arena.css ]; then
    echo "✅ arena.css exists"
    echo "Lines in arena.css: $(wc -l < /home/ec2-user/ChatMRPT/app/static/css/arena.css)"
else
    echo "❌ arena.css NOT found"
fi

echo ""
echo "🔍 Last 10 lines of modern-minimalist-theme.css:"
tail -10 /home/ec2-user/ChatMRPT/app/static/css/modern-minimalist-theme.css
EOF

echo ""
echo "2️⃣ CHECKING JAVASCRIPT FILES ON AWS"
echo "-----------------------------------"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$INSTANCE << 'EOF'
echo "📁 JS structure:"
find /home/ec2-user/ChatMRPT/app/static/js/modules/chat -name "*.js" | sort

echo ""
echo "🔍 Checking message-handler.js:"
grep -n "voting-buttons" /home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/message-handler.js | head -3
grep -n "vote-btn" /home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/message-handler.js | head -3
grep -n "Assistant A" /home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/message-handler.js | head -1
grep -n "Left is Better" /home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/message-handler.js | head -1
EOF

echo ""
echo "3️⃣ CHECKING HTML TEMPLATE ON AWS"
echo "-----------------------------------"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$INSTANCE << 'EOF'
echo "🔍 CSS imports in index.html:"
grep -E "css|style" /home/ec2-user/ChatMRPT/app/templates/index.html | grep -E "link|url_for" | head -10

echo ""
echo "❓ Is arena.css referenced in index.html?"
grep -c "arena.css" /home/ec2-user/ChatMRPT/app/templates/index.html || echo "NOT REFERENCED"
EOF

echo ""
echo "4️⃣ CHECKING LOCAL FILES"
echo "-----------------------------------"
echo "📁 Local CSS files:"
ls -la app/static/css/ | grep ".css"

echo ""
echo "📏 Local file sizes:"
wc -l app/static/css/*.css 2>/dev/null | head -10

echo ""
echo "🔍 Arena styles in local modern-minimalist-theme.css:"
echo "voting-buttons count: $(grep -c "voting-buttons" app/static/css/modern-minimalist-theme.css || echo 0)"
echo "vote-btn count: $(grep -c "vote-btn" app/static/css/modern-minimalist-theme.css || echo 0)"

echo ""
echo "5️⃣ COMPARING LOCAL vs AWS"
echo "-----------------------------------"
LOCAL_SIZE=$(wc -l < app/static/css/modern-minimalist-theme.css)
echo "📊 Local modern-minimalist-theme.css: $LOCAL_SIZE lines"

AWS_SIZE=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$INSTANCE "wc -l < /home/ec2-user/ChatMRPT/app/static/css/modern-minimalist-theme.css")
echo "📊 AWS modern-minimalist-theme.css: $AWS_SIZE lines"

if [ "$LOCAL_SIZE" -eq "$AWS_SIZE" ]; then
    echo "✅ Files are same size"
else
    echo "❌ FILES ARE DIFFERENT SIZES!"
    echo "   Difference: $((LOCAL_SIZE - AWS_SIZE)) lines"
fi

echo ""
echo "6️⃣ CHECKING FOR CSS CONFLICTS"
echo "-----------------------------------"
echo "🔍 Looking for other CSS files that might override Arena styles..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$INSTANCE << 'EOF'
grep -r "voting-buttons\|vote-btn" /home/ec2-user/ChatMRPT/app/static/css/ --include="*.css" | grep -v arena.css | head -10
EOF

echo ""
echo "7️⃣ CHECKING ACTUAL HTML GENERATION"
echo "-----------------------------------"
echo "🔍 Checking how voting buttons are generated in message-handler.js..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$INSTANCE << 'EOF'
echo "Lines containing 'votingButtons':"
grep -n "votingButtons" /home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/message-handler.js | head -5

echo ""
echo "Lines with class='voting-buttons':"
grep -n "class.*voting-buttons" /home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/message-handler.js | head -3

echo ""
echo "Lines with class='vote-btn':"
grep -n "class.*vote-btn" /home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/message-handler.js | head -3
EOF

echo ""
echo "📋 INVESTIGATION COMPLETE"
echo "========================"
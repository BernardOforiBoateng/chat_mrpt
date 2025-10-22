#!/bin/bash
# Verify vision is working through the ALB by testing multiple requests

echo "🧪 Testing Vision API through ALB..."
echo ""  
echo "This will make multiple requests to ensure both instances respond correctly"
echo ""

ALB_URL="http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

# Create test HTML file locally
cat > /tmp/test_vision.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Test Map</title></head>
<body style="background:linear-gradient(red,yellow,green); width:800px; height:600px;">
    <h1>Malaria Risk Test Map</h1>
    <div style="background:#ff0000; padding:20px; color:white; font-size:24px;">Kano State: 89.5% TPR (CRITICAL)</div>
    <div style="background:#ffaa00; padding:20px; font-size:24px;">Jigawa: 62.3% TPR (HIGH)</div> 
    <div style="background:#00ff00; padding:20px; font-size:24px;">Lagos: 12.7% TPR (LOW)</div>
</body>
</html>
EOF

echo "Test HTML created with specific data points:"
echo "  - Kano State: 89.5% (CRITICAL)"
echo "  - Jigawa: 62.3% (HIGH)"
echo "  - Lagos: 12.7% (LOW)"
echo ""

# Function to test through ALB
test_alb_vision() {
    echo "Test $1:"
    
    # Start a session and upload the test file
    SESSION_ID="test_vision_$(date +%s)_$1"
    
    # Make the API call
    RESPONSE=$(curl -s -X POST "$ALB_URL/explain_visualization" \
        -H "Content-Type: application/json" \
        -H "Cookie: session=$SESSION_ID" \
        -d '{
            "visualization_path": "/tmp/test_vision.html",
            "viz_type": "tpr_map",
            "title": "Test Vision Map"
        }' 2>/dev/null)
    
    # Check if we got AI-powered response
    if echo "$RESPONSE" | grep -q "89.5%\|Kano State\|62.3%\|Jigawa\|12.7%"; then
        echo "  ✅ AI-POWERED: Found specific test data in response"
        echo "  Instance recognized: Kano State, Jigawa, or percentage values"
    elif echo "$RESPONSE" | grep -q "This visualization shows malaria risk analysis"; then
        echo "  ❌ FALLBACK: Still getting generic explanation"
    else
        echo "  ⚠️ UNKNOWN: Different response type"
        echo "  Response preview: ${RESPONSE:0:200}..."
    fi
    echo ""
}

# Run 4 tests to hit both instances multiple times
for i in 1 2 3 4; do
    test_alb_vision $i
    sleep 1
done

echo "Summary:"
echo "--------"
echo "If you see:"
echo "  ✅ AI-POWERED - Vision is working correctly!"
echo "  ❌ FALLBACK - Vision is still not working"
echo ""
echo "Note: The ALB distributes requests between instances,"
echo "so we test multiple times to ensure both are working."

# Clean up
rm -f /tmp/test_vision.html
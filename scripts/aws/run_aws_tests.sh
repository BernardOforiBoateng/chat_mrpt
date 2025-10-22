#!/bin/bash

# Run comprehensive tests on AWS instances for Intent Clarification System
# This script deploys and runs pytest on both production instances

echo "================================================"
echo "Testing Intent Clarification System on AWS"
echo "================================================"
echo ""

# Production instances
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

# Key file location
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

echo "📦 Deploying test suite to both instances..."
echo "------------------------------------------------"

# Copy test file to both instances
for INSTANCE in $INSTANCE_1 $INSTANCE_2; do
    echo "Copying tests to $INSTANCE..."
    scp -i /tmp/chatmrpt-key2.pem \
        tests/test_intent_clarification.py \
        ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/tests/
done

echo ""
echo "🧪 Running tests on Instance 1: $INSTANCE_1"
echo "================================================"

ssh -i /tmp/chatmrpt-key2.pem ec2-user@$INSTANCE_1 << 'EOF'
cd /home/ec2-user/ChatMRPT

# Activate virtual environment
source chatmrpt_env/bin/activate

# Install pytest if not already installed
pip install pytest pytest-cov pytest-html --quiet

echo ""
echo "Running Intent Clarification Tests..."
echo "--------------------------------------"

# Run the tests with detailed output and coverage
python -m pytest tests/test_intent_clarification.py -v \
    --tb=short \
    --cov=app.core.intent_clarifier \
    --cov=app.web.routes.analysis_routes \
    --cov-report=term-missing \
    --html=tests/intent_clarification_report_instance1.html \
    --self-contained-html \
    2>&1 | tee tests/test_results_instance1.txt

# Check test result
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo "✅ All tests passed on Instance 1!"
else
    echo ""
    echo "❌ Some tests failed on Instance 1. Check the report for details."
fi

# Show summary
echo ""
echo "Test Summary for Instance 1:"
echo "----------------------------"
grep -E "(passed|failed|error|skipped)" tests/test_results_instance1.txt | tail -1
EOF

echo ""
echo "🧪 Running tests on Instance 2: $INSTANCE_2"
echo "================================================"

ssh -i /tmp/chatmrpt-key2.pem ec2-user@$INSTANCE_2 << 'EOF'
cd /home/ec2-user/ChatMRPT

# Activate virtual environment
source chatmrpt_env/bin/activate

# Install pytest if not already installed
pip install pytest pytest-cov pytest-html --quiet

echo ""
echo "Running Intent Clarification Tests..."
echo "--------------------------------------"

# Run the tests with detailed output and coverage
python -m pytest tests/test_intent_clarification.py -v \
    --tb=short \
    --cov=app.core.intent_clarifier \
    --cov=app.web.routes.analysis_routes \
    --cov-report=term-missing \
    --html=tests/intent_clarification_report_instance2.html \
    --self-contained-html \
    2>&1 | tee tests/test_results_instance2.txt

# Check test result
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo "✅ All tests passed on Instance 2!"
else
    echo ""
    echo "❌ Some tests failed on Instance 2. Check the report for details."
fi

# Show summary
echo ""
echo "Test Summary for Instance 2:"
echo "----------------------------"
grep -E "(passed|failed|error|skipped)" tests/test_results_instance2.txt | tail -1
EOF

echo ""
echo "📊 Retrieving test reports..."
echo "------------------------------------------------"

# Create local test reports directory
mkdir -p tests/aws_reports

# Download test reports from both instances
for INSTANCE in $INSTANCE_1 $INSTANCE_2; do
    INSTANCE_NAME=$(echo $INSTANCE | tr '.' '_')
    echo "Downloading reports from $INSTANCE..."
    
    scp -i /tmp/chatmrpt-key2.pem \
        ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/tests/intent_clarification_report_*.html \
        tests/aws_reports/ 2>/dev/null || echo "No HTML report found on $INSTANCE"
    
    scp -i /tmp/chatmrpt-key2.pem \
        ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/tests/test_results_*.txt \
        tests/aws_reports/ 2>/dev/null || echo "No text report found on $INSTANCE"
done

# Clean up
rm -f /tmp/chatmrpt-key2.pem

echo ""
echo "================================================"
echo "✅ Testing Complete!"
echo "================================================"
echo ""
echo "📁 Test reports saved in: tests/aws_reports/"
echo ""
echo "View reports:"
echo "  - tests/aws_reports/intent_clarification_report_instance1.html"
echo "  - tests/aws_reports/intent_clarification_report_instance2.html"
echo ""
echo "Test Scenarios Covered:"
echo "  ✓ Intent detection without data"
echo "  ✓ Intent detection with uploaded data"
echo "  ✓ Ambiguous request handling"
echo "  ✓ Clarification prompt generation"
echo "  ✓ Clarification response processing"
echo "  ✓ Arena mode activation"
echo "  ✓ Tools mode activation"
echo "  ✓ TPR workflow bypass"
echo "  ✓ End-to-end user scenarios"
echo ""
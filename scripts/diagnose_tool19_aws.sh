#!/bin/bash
# Diagnostic Script: Check Tool #19 Status on AWS
# Run this on AWS production instances

echo "=========================================="
echo "Tool #19 Diagnostic Check"
echo "=========================================="
echo ""

echo "1. Checking fallbacks in request_interpreter.py..."
echo "---"
grep -A 10 "fallbacks=" /home/ec2-user/ChatMRPT/app/core/request_interpreter.py
echo ""

echo "2. Checking Tool #19 registration..."
echo "---"
grep -B 2 -A 2 "analyze_data_with_python" /home/ec2-user/ChatMRPT/app/core/request_interpreter.py | head -20
echo ""

echo "3. Checking if legacy methods still exist..."
echo "---"
echo "execute_data_query method:"
grep -n "def _execute_data_query" /home/ec2-user/ChatMRPT/app/core/request_interpreter.py
echo ""
echo "execute_sql_query method:"
grep -n "def _execute_sql_query" /home/ec2-user/ChatMRPT/app/core/request_interpreter.py
echo ""

echo "4. Checking tool_runner.py..."
echo "---"
if [ -f /home/ec2-user/ChatMRPT/app/core/tool_runner.py ]; then
    echo "✅ tool_runner.py EXISTS"
    echo "First 50 lines:"
    head -50 /home/ec2-user/ChatMRPT/app/core/tool_runner.py
else
    echo "❌ tool_runner.py NOT FOUND"
fi
echo ""

echo "5. Checking DataExplorationAgent..."
echo "---"
if [ -f /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/data_exploration_agent.py ]; then
    echo "✅ DataExplorationAgent EXISTS"
    echo "File size:"
    wc -l /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/data_exploration_agent.py
else
    echo "❌ DataExplorationAgent NOT FOUND"
fi
echo ""

echo "6. Checking Tool #19 docstring..."
echo "---"
grep -A 25 "def _analyze_data_with_python" /home/ec2-user/ChatMRPT/app/core/request_interpreter.py | grep -A 20 '"""'
echo ""

echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="

#!/bin/bash

echo "Testing Data Analysis Module on Staging"
echo "========================================"

# Test with a simple query
echo ""
echo "Testing with NMEP file..."

curl -X POST http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/api/data-analysis/analyze \
  -F "file=@www/NMEP TPR and LLIN 2024_16072025.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
  -F "query=Show me the first 5 rows of data" \
  --max-time 60

echo ""
echo "========================================"
echo "Test complete"
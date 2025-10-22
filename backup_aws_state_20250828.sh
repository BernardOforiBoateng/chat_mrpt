#!/bin/bash
# Backup script for AWS production state - August 28, 2025
# This captures the working ITN distribution with urban percentage fixes

echo "=== ChatMRPT AWS Production State Backup ==="
echo "Date: $(date)"
echo ""

# Production Instances (Active)
echo "=== PRODUCTION INSTANCES (ACTIVE) ==="
echo "Instance 1: i-0994615951d0b9563 (IP: 3.21.167.170)"
echo "Instance 2: i-0f3b25b72f18a5037 (IP: 18.220.103.20)"
echo ""

# Key fixes deployed
echo "=== KEY FIXES DEPLOYED ==="
echo "✅ Urban percentage extraction in TPR analysis (all geopolitical zones)"
echo "✅ ITN pipeline handles urban_percentage, urbanPercentage, and UrbanPercent columns"
echo "✅ DataHandler loading methods fixed (_attempt_data_reload + load_session_state)"
echo "✅ Population data fuzzy matching with 75% threshold"
echo "✅ Distribution array added for backward compatibility"
echo ""

# Test session with working ITN
echo "=== VERIFIED WORKING SESSION ==="
echo "Session ID: 4e21ce78-66e6-4ef4-b13e-23e994846de8"
echo "State: Adamawa"
echo "Wards: 226 total, 140 allocated"
echo "Coverage: 57.9% (2M nets)"
echo "Urban data: 226/226 wards with urban_percentage"
echo ""

# Files modified
echo "=== CRITICAL FILES MODIFIED ==="
echo "app/analysis/itn_pipeline.py - Urban column detection and distribution field"
echo "app/web/routes/itn_routes.py - DataHandler loading fix"
echo "app/data_analysis_v3/tools/tpr_analysis_tool.py - Urban_extent extraction"
echo ""

# Services status
echo "=== SERVICE STATUS ==="
echo "Application: Gunicorn with 6 workers"
echo "Redis: chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379"
echo "ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "CloudFront: https://d225ar6c86586s.cloudfront.net"
echo ""

# Backup commands for quick restore
echo "=== QUICK RESTORE COMMANDS ==="
echo "# To restore ITN pipeline:"
echo "scp -i ~/.ssh/chatmrpt-key.pem app/analysis/itn_pipeline.py ec2-user@3.21.167.170:/home/ec2-user/ChatMRPT/app/analysis/"
echo "scp -i ~/.ssh/chatmrpt-key.pem app/analysis/itn_pipeline.py ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT/app/analysis/"
echo ""
echo "# To restore ITN routes:"
echo "scp -i ~/.ssh/chatmrpt-key.pem app/web/routes/itn_routes.py ec2-user@3.21.167.170:/home/ec2-user/ChatMRPT/app/web/routes/"
echo "scp -i ~/.ssh/chatmrpt-key.pem app/web/routes/itn_routes.py ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT/app/web/routes/"
echo ""
echo "# To restart services:"
echo "ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@3.21.167.170 'sudo systemctl restart chatmrpt'"
echo "ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20 'sudo systemctl restart chatmrpt'"
echo ""

echo "=== BACKUP COMPLETE ==="
echo "GitHub branch: backup/itn-urban-fix-20250828"
echo "Commits: c086d25 and deb3e4f"
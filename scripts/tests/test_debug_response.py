#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
session = requests.Session()

# Quick TPR test to see full response
with open('adamawa_tpr_cleaned.csv', 'rb') as f:
    files = {'file': ('adamawa_tpr_cleaned.csv', f, 'text/csv')}
    r = session.post(f"{BASE_URL}/api/data-analysis/upload", files=files)
    session_id = r.json()['session_id']
    print(f"Session: {session_id}")

# Run workflow
for msg in ["2", "primary", "Under 5 Years"]:
    r = session.post(f"{BASE_URL}/api/v1/data-analysis/chat",
                     json={'message': msg, 'session_id': session_id})
    if "TPR Calculation Complete" in r.json().get('message', ''):
        response = r.json()
        print("\nFull response message:")
        print(response.get('message'))
        print("\n---Files created?---")
        # SSH to check files
        import subprocess
        cmd = f"ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 \"ls -la /home/ec2-user/ChatMRPT/instance/uploads/{session_id}/\"'"
        subprocess.run(cmd, shell=True)

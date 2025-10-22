#!/usr/bin/env python3
import requests
import time

BASE_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
session = requests.Session()

# Upload
with open('adamawa_tpr_cleaned.csv', 'rb') as f:
    files = {'file': ('adamawa_tpr_cleaned.csv', f, 'text/csv')}
    r = session.post(f"{BASE_URL}/api/data-analysis/upload", files=files)
    session_id = r.json()['session_id']
    print(f"Session: {session_id}")

# Select options quickly
for msg in ["2", "primary", "Under 5 Years"]:
    r = session.post(f"{BASE_URL}/api/v1/data-analysis/chat", 
                     json={'message': msg, 'session_id': session_id})
    print(f"Sent: {msg}")
    time.sleep(1)

print("Check logs now!")

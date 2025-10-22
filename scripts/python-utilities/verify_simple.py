#!/usr/bin/env python3
import requests
import re
from datetime import datetime

PRODUCTION_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

print("\n" + "="*60)
print("   DATA ANALYSIS TAB - VERIFICATION")
print("="*60)

response = requests.get(PRODUCTION_URL, timeout=10)
html = response.text

# Check for Data Analysis tab
has_data_analysis = 'id="data-analysis-tab"' in html and "Data Analysis" in html
has_old_tpr = "TPR Analysis" in html

print(f"\n✅ Data Analysis tab found: {has_data_analysis}")
print(f"❌ Old TPR Analysis text found: {has_old_tpr}")

if has_data_analysis and not has_old_tpr:
    print("\n🎉 SUCCESS! The tab now shows 'Data Analysis'")
else:
    print("\n⚠️ Issue detected - please check the deployment")

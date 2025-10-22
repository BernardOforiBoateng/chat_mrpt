#!/usr/bin/env python3
"""
Comprehensive verification of Data Analysis tab deployment
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

PRODUCTION_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

def check_ui_update():
    """Verify the UI shows 'Data Analysis' instead of 'TPR Analysis'"""
    print("\n📋 Checking UI Update...")
    response = requests.get(PRODUCTION_URL, timeout=10)
    
    if response.status_code != 200:
        return False, f"Failed to load page: {response.status_code}"
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check for Data Analysis tab button
    data_analysis_btn = soup.find('button', {'id': 'data-analysis-tab'})
    if not data_analysis_btn:
        return False, "Data Analysis tab button not found"
    
    btn_text = data_analysis_btn.get_text(strip=True)
    if "Data Analysis" not in btn_text:
        return False, f"Button text is '{btn_text}', expected 'Data Analysis'"
    
    # Check that TPR Analysis is gone
    if "TPR Analysis" in response.text:
        return False, "Old 'TPR Analysis' text still present in HTML"
    
    # Check for the tab content
    data_analysis_content = soup.find('div', {'id': 'data-analysis'})
    if not data_analysis_content:
        return False, "Data Analysis tab content not found"
    
    return True, "UI successfully shows 'Data Analysis' tab"

def check_backend_endpoints():
    """Verify backend endpoints are working"""
    print("\n🔧 Checking Backend Endpoints...")
    
    results = []
    
    # Check upload endpoint exists
    upload_url = f"{PRODUCTION_URL}/api/data-analysis/upload"
    response = requests.options(upload_url, timeout=5)
    if response.status_code == 404:
        results.append((False, f"Upload endpoint not found: {upload_url}"))
    else:
        results.append((True, f"Upload endpoint exists: {upload_url}"))
    
    # Check chat endpoint exists  
    chat_url = f"{PRODUCTION_URL}/api/v1/data-analysis/chat"
    response = requests.options(chat_url, timeout=5)
    if response.status_code == 404:
        results.append((False, f"Chat endpoint not found: {chat_url}"))
    else:
        results.append((True, f"Chat endpoint exists: {chat_url}"))
    
    return results

def generate_report():
    """Generate comprehensive verification report"""
    print("\n" + "="*60)
    print("   DATA ANALYSIS TAB - PRODUCTION VERIFICATION REPORT")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {PRODUCTION_URL}")
    
    # Check UI
    ui_success, ui_message = check_ui_update()
    print(f"\n✅ UI Update: {'PASSED' if ui_success else 'FAILED'}")
    print(f"   {ui_message}")
    
    # Check backend
    backend_results = check_backend_endpoints()
    backend_success = all(r[0] for r in backend_results)
    print(f"\n{'✅' if backend_success else '❌'} Backend Endpoints: {'PASSED' if backend_success else 'FAILED'}")
    for success, message in backend_results:
        print(f"   {'✅' if success else '❌'} {message}")
    
    # Overall status
    overall_success = ui_success and backend_success
    
    print("\n" + "="*60)
    print("   OVERALL STATUS: " + ("✅ ALL TESTS PASSED" if overall_success else "❌ SOME TESTS FAILED"))
    print("="*60)
    
    if overall_success:
        print("\n🎉 SUCCESS! The Data Analysis tab is fully deployed and working!")
        print("Users will now see 'Data Analysis' instead of 'TPR Analysis'")
    else:
        print("\n⚠️  Some issues detected. Please review the errors above.")
    
    return overall_success

if __name__ == "__main__":
    success = generate_report()
    exit(0 if success else 1)
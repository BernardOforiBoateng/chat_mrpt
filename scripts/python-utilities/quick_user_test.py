#!/usr/bin/env python3
"""
Quick User Interaction Test for ChatMRPT
Tests key scenarios with the Data Analysis V3 endpoint
"""

import requests
import json
import time
import datetime

BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

def test_general_conversation():
    """Test general conversation without data"""
    print("\n" + "="*60)
    print("TEST 1: General Conversation (No Data Required)")
    print("="*60)
    
    test_cases = [
        ("Hello, who are you?", "greeting"),
        ("What can you do?", "capabilities"),
        ("What is malaria?", "knowledge"),
        ("How can we prevent malaria?", "prevention")
    ]
    
    results = []
    session_id = f"test_general_{int(time.time())}"
    
    for message, test_type in test_cases:
        print(f"\n💬 Testing: {message}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/data-analysis/chat",
                json={
                    'message': message,
                    'session_id': session_id
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                msg = data.get('message', '')[:150]
                
                # Check if response doesn't require data upload
                requires_upload = 'upload' in msg.lower() and 'data' in msg.lower() and 'first' in msg.lower()
                
                if success and not requires_upload:
                    print(f"✅ PASS - Got response without requiring data upload")
                    print(f"   Response: {msg}...")
                    results.append((test_type, True))
                else:
                    print(f"❌ FAIL - Required data upload or failed")
                    print(f"   Response: {msg}...")
                    results.append((test_type, False))
            else:
                print(f"❌ FAIL - HTTP {response.status_code}")
                results.append((test_type, False))
                
        except Exception as e:
            print(f"❌ FAIL - {str(e)}")
            results.append((test_type, False))
    
    return results

def test_tpr_workflow():
    """Test TPR to risk analysis workflow"""
    print("\n" + "="*60)
    print("TEST 2: TPR Workflow with Adamawa Data")
    print("="*60)
    
    session_id = f"test_tpr_{int(time.time())}"
    results = []
    
    # Step 1: Upload Adamawa TPR data
    print("\n📤 Uploading Adamawa TPR data...")
    
    # Create simple test data
    csv_data = """WardName,State,LGA,HealthFacility,MonthYear,u5_rdt_tested,u5_rdt_positive,o5_rdt_tested,o5_rdt_positive
Yola North,Adamawa,Yola North,General Hospital,2024-01,100,25,200,30
Yola South,Adamawa,Yola South,PHC,2024-01,150,40,180,35
Girei,Adamawa,Girei,District Hospital,2024-01,120,28,210,42"""
    
    files = {'file': ('adamawa_tpr.csv', csv_data, 'text/csv')}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/data-analysis/upload",
            files=files,
            data={'session_id': session_id},
            timeout=15
        )
        
        if response.status_code == 200:
            print("✅ Data uploaded successfully")
            results.append(('upload', True))
        else:
            print(f"❌ Upload failed: HTTP {response.status_code}")
            results.append(('upload', False))
            return results
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        results.append(('upload', False))
        return results
    
    # Step 2: Request TPR analysis
    print("\n💬 Requesting TPR analysis...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={
                'message': "I want to calculate TPR",
                'session_id': session_id
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ TPR analysis initiated")
                print(f"   Response: {data.get('message', '')[:150]}...")
                results.append(('tpr_request', True))
            else:
                print(f"❌ TPR analysis failed")
                results.append(('tpr_request', False))
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            results.append(('tpr_request', False))
    except Exception as e:
        print(f"❌ Failed: {e}")
        results.append(('tpr_request', False))
    
    return results

def test_direct_analysis():
    """Test direct data analysis"""
    print("\n" + "="*60)
    print("TEST 3: Direct Data Analysis")
    print("="*60)
    
    session_id = f"test_analysis_{int(time.time())}"
    results = []
    
    # Upload sample health data
    print("\n📤 Uploading health data...")
    
    csv_data = """Facility,District,Cases,Tests,Date
Hospital A,North District,45,200,2024-01
Hospital B,South District,30,150,2024-01
Clinic C,East District,60,180,2024-01
Clinic D,West District,25,120,2024-01"""
    
    files = {'file': ('health_data.csv', csv_data, 'text/csv')}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/data-analysis/upload",
            files=files,
            data={'session_id': session_id},
            timeout=15
        )
        
        if response.status_code == 200:
            print("✅ Data uploaded")
            results.append(('upload', True))
        else:
            print(f"❌ Upload failed: HTTP {response.status_code}")
            results.append(('upload', False))
            return results
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        results.append(('upload', False))
        return results
    
    # Analyze data
    print("\n💬 Requesting analysis...")
    
    queries = [
        "Show me what's in this data",
        "Which districts have the highest case rates?"
    ]
    
    for query in queries:
        print(f"\n📊 Query: {query}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/data-analysis/chat",
                json={
                    'message': query,
                    'session_id': session_id
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Analysis successful")
                    print(f"   Response: {data.get('message', '')[:150]}...")
                    results.append((f'analysis_{query[:20]}', True))
                else:
                    print(f"❌ Analysis failed")
                    results.append((f'analysis_{query[:20]}', False))
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                results.append((f'analysis_{query[:20]}', False))
        except Exception as e:
            print(f"❌ Failed: {e}")
            results.append((f'analysis_{query[:20]}', False))
    
    return results

def generate_summary(all_results):
    """Generate test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total_tests = sum(len(results) for results in all_results.values())
    passed_tests = sum(1 for results in all_results.values() for _, passed in results if passed)
    
    print(f"\n📊 Overall Results:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    print(f"   Pass Rate: {(passed_tests/total_tests*100):.1f}%")
    
    print(f"\n📝 By Scenario:")
    for scenario, results in all_results.items():
        passed = sum(1 for _, p in results if p)
        total = len(results)
        print(f"   {scenario}: {passed}/{total} passed ({passed/total*100:.0f}%)")
        
    # Generate HTML report
    report_file = f"quick_test_report_{int(time.time())}.html"
    with open(report_file, 'w') as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>ChatMRPT Quick Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .pass { color: green; font-weight: bold; }
        .fail { color: red; font-weight: bold; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>ChatMRPT Quick Test Report</h1>
    <p>Generated: """ + datetime.datetime.now().isoformat() + """</p>
    <h2>Summary</h2>
    <p>Total Tests: """ + str(total_tests) + """</p>
    <p>Passed: """ + str(passed_tests) + """</p>
    <p>Failed: """ + str(total_tests - passed_tests) + """</p>
    <p>Pass Rate: """ + f"{(passed_tests/total_tests*100):.1f}%" + """</p>
    <h2>Test Results</h2>
    <table>
        <tr><th>Scenario</th><th>Test</th><th>Result</th></tr>
""")
        
        for scenario, results in all_results.items():
            for test_name, passed in results:
                status = "PASS" if passed else "FAIL"
                css_class = "pass" if passed else "fail"
                f.write(f'        <tr><td>{scenario}</td><td>{test_name}</td><td class="{css_class}">{status}</td></tr>\n')
        
        f.write("""
    </table>
</body>
</html>
""")
    
    print(f"\n📄 HTML report saved: {report_file}")

def main():
    """Run all tests"""
    print("\n🚀 Starting ChatMRPT Quick User Tests")
    print(f"   Target: {BASE_URL}")
    print(f"   Time: {datetime.datetime.now().isoformat()}")
    
    all_results = {}
    
    # Run tests
    all_results['General Conversation'] = test_general_conversation()
    time.sleep(2)  # Brief pause between test scenarios
    
    all_results['TPR Workflow'] = test_tpr_workflow()
    time.sleep(2)
    
    all_results['Direct Analysis'] = test_direct_analysis()
    
    # Generate summary
    generate_summary(all_results)
    
    print("\n✅ Testing complete!")

if __name__ == "__main__":
    main()
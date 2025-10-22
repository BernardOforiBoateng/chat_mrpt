"""
Comprehensive test showing actual agent responses
Tests the complete fix including top 10 queries
"""

import requests
import time
import os
import re
from datetime import datetime

# Direct to staging instance
STAGING_URL = "http://3.21.167.170:8080"

def run_comprehensive_test():
    """Run comprehensive test with real user queries."""
    
    print("\n" + "="*70)
    print("COMPREHENSIVE DATA ANALYSIS V3 TEST")
    print("Testing Top 10 Query Fix & No Hallucination")
    print("="*70)
    
    session_id = f'comprehensive_{int(time.time())}'
    all_results = []
    
    # Step 1: Upload data
    print("\n1. UPLOADING DATA")
    print("-" * 40)
    
    with open('www/adamawa_tpr_cleaned.csv', 'rb') as f:
        files = {'file': ('test_data.csv', f, 'text/csv')}
        data = {'session_id': session_id}
        
        response = requests.post(
            f"{STAGING_URL}/api/data-analysis/upload",
            files=files,
            data=data,
            timeout=60
        )
        
        if response.status_code == 200:
            print("✅ Data uploaded successfully")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return
    
    time.sleep(3)
    
    # Test queries focusing on the main issues
    test_queries = [
        {
            'name': 'Column Discovery',
            'query': 'List all the columns in the dataset',
            'check': lambda r: 'healthfacility' in r.lower() or 'columns' in r.lower()
        },
        {
            'name': 'Top 10 Facilities',
            'query': 'Show me the top 10 health facilities by total testing volume. I need to see all 10 facilities listed.',
            'check': lambda r: count_numbered_items(r) >= 8
        },
        {
            'name': 'Top 5 Wards',  
            'query': 'What are the top 5 wards with highest testing? List all 5.',
            'check': lambda r: count_numbered_items(r) >= 5
        },
        {
            'name': 'Statistical Summary',
            'query': 'Calculate the total number of tests performed across all facilities',
            'check': lambda r: any(word in r.lower() for word in ['total', 'sum', 'tests'])
        }
    ]
    
    # Run each test
    for i, test in enumerate(test_queries, 1):
        print(f"\n{i+1}. {test['name'].upper()}")
        print("-" * 40)
        print(f"Query: {test['query']}")
        
        start_time = time.time()
        response = requests.post(
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={
                'message': test['query'],
                'session_id': session_id
            },
            timeout=120
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            success = result.get('success', False)
            message = result.get('message', '')
            
            # Basic checks
            print(f"Response Time: {response_time:.2f}s")
            print(f"Success: {success}")
            
            # Specific checks for this test
            if 'Top' in test['name']:
                # Count numbered items
                num_items = count_numbered_items(message)
                print(f"Items Found: {num_items}")
                
                # Check for hallucinations
                has_hallucination = check_hallucinations(message)
                if has_hallucination:
                    print("❌ HALLUCINATION DETECTED!")
                else:
                    print("✅ No hallucinations")
                
                # Show actual items found
                show_numbered_items(message)
            
            # Check test condition
            if test['check'](message):
                print("✅ TEST PASSED")
            else:
                print("❌ TEST FAILED")
                print(f"Response preview: {message[:300]}...")
            
            all_results.append({
                'test': test['name'],
                'query': test['query'],
                'success': success,
                'passed': test['check'](message),
                'response': message,
                'response_time': response_time
            })
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            all_results.append({
                'test': test['name'],
                'query': test['query'],
                'success': False,
                'passed': False,
                'response': f"HTTP {response.status_code}",
                'response_time': response_time
            })
    
    # Generate report
    generate_detailed_report(session_id, all_results)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in all_results if r['passed'])
    total = len(all_results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    # Specific issue checks
    top_10_test = next((r for r in all_results if 'Top 10' in r['test']), None)
    if top_10_test:
        if top_10_test['passed']:
            print("✅ TOP 10 ISSUE: FIXED!")
        else:
            print("❌ TOP 10 ISSUE: Still broken")
    
    # Check for hallucinations in any response
    any_hallucination = any(check_hallucinations(r['response']) for r in all_results)
    if any_hallucination:
        print("❌ HALLUCINATION ISSUE: Still present")
    else:
        print("✅ HALLUCINATION ISSUE: FIXED!")

def count_numbered_items(text):
    """Count numbered items in response."""
    # Look for patterns like "1.", "2.", etc.
    numbered = re.findall(r'^\s*\d+\.', text, re.MULTILINE)
    return len(numbered)

def check_hallucinations(text):
    """Check for common hallucination patterns."""
    hallucination_patterns = [
        'Facility A', 'Facility B', 'Facility C',
        'Item 1', 'Item 2', 'Entity A', 'Entity B',
        'Test Facility', 'Sample Ward'
    ]
    return any(pattern in text for pattern in hallucination_patterns)

def show_numbered_items(text):
    """Extract and show numbered items."""
    lines = text.split('\n')
    numbered_lines = [line for line in lines if re.match(r'^\s*\d+\.', line)]
    
    if numbered_lines:
        print("\nActual items returned:")
        for line in numbered_lines[:10]:  # Show first 10
            print(f"  {line.strip()}")

def generate_detailed_report(session_id, results):
    """Generate detailed HTML report."""
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Comprehensive Test Report - {session_id}</title>
    <style>
        body {{
            font-family: -apple-system, system-ui, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f0f2f5;
        }}
        .header {{
            background: linear-gradient(135deg, #6b46c1, #4338ca);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        h1 {{ margin: 0 0 10px 0; }}
        .test-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .test-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .test-card.passed {{
            border-left: 5px solid #10b981;
        }}
        .test-card.failed {{
            border-left: 5px solid #ef4444;
        }}
        .test-name {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .query {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 6px;
            margin: 15px 0;
            font-size: 14px;
            color: #495057;
        }}
        .response {{
            background: #f1f3f5;
            padding: 15px;
            border-radius: 6px;
            white-space: pre-wrap;
            font-family: 'Monaco', monospace;
            font-size: 13px;
            max-height: 400px;
            overflow-y: auto;
            margin: 15px 0;
        }}
        .metrics {{
            display: flex;
            gap: 20px;
            margin-top: 15px;
            font-size: 14px;
        }}
        .metric {{
            padding: 5px 10px;
            background: #e9ecef;
            border-radius: 4px;
        }}
        .passed {{ color: #10b981; font-weight: 600; }}
        .failed {{ color: #ef4444; font-weight: 600; }}
        .summary {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-top: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .summary h2 {{
            margin-top: 0;
            color: #1e293b;
        }}
        .issue-status {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }}
        .issue {{
            padding: 15px;
            border-radius: 8px;
            font-weight: 500;
        }}
        .issue.fixed {{
            background: #d1fae5;
            color: #065f46;
        }}
        .issue.broken {{
            background: #fee2e2;
            color: #991b1b;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Comprehensive Data Analysis V3 Test Report</h1>
        <p>Session: {session_id}</p>
        <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Endpoint: {STAGING_URL}</p>
    </div>
    
    <div class="test-grid">
"""
    
    # Add test cards
    for result in results:
        status_class = "passed" if result['passed'] else "failed"
        status_text = "✅ PASSED" if result['passed'] else "❌ FAILED"
        
        html += f"""
        <div class="test-card {status_class}">
            <div class="test-name">{result['test']}</div>
            <div class="query">Query: {result['query']}</div>
            <div class="response">{result['response'][:500]}...</div>
            <div class="metrics">
                <span class="metric {status_class}">{status_text}</span>
                <span class="metric">⏱️ {result['response_time']:.2f}s</span>
            </div>
        </div>
"""
    
    # Add summary
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    # Check specific issues
    top_10_passed = any(r['passed'] for r in results if 'Top 10' in r['test'])
    no_hallucinations = not any(check_hallucinations(r['response']) for r in results)
    
    html += f"""
    </div>
    
    <div class="summary">
        <h2>Test Summary</h2>
        <p style="font-size: 24px; font-weight: bold;">
            {passed}/{total} Tests Passed ({(passed/total*100):.1f}%)
        </p>
        
        <div class="issue-status">
            <div class="issue {'fixed' if top_10_passed else 'broken'}">
                Top 10 Query Issue: {'✅ FIXED' if top_10_passed else '❌ Still Broken'}
            </div>
            <div class="issue {'fixed' if no_hallucinations else 'broken'}">
                Hallucination Issue: {'✅ FIXED' if no_hallucinations else '❌ Still Present'}
            </div>
        </div>
    </div>
    
    <div style="margin-top: 30px; padding: 20px; background: white; border-radius: 10px;">
        <h3>Full Responses</h3>
"""
    
    # Add full responses
    for i, result in enumerate(results, 1):
        html += f"""
        <div style="margin-bottom: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <h4>Test {i}: {result['test']}</h4>
            <p><strong>Query:</strong> {result['query']}</p>
            <div style="background: white; padding: 15px; border-radius: 6px; margin-top: 10px;">
                <pre style="white-space: pre-wrap; font-family: monospace; font-size: 13px;">{result['response']}</pre>
            </div>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    # Save report
    report_path = f"tests/comprehensive_report_{session_id}.html"
    os.makedirs("tests", exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n📄 Detailed HTML report saved to: {report_path}")

if __name__ == "__main__":
    run_comprehensive_test()
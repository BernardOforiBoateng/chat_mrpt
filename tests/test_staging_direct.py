"""
Direct test against staging instance (bypassing ALB)
Tests actual agent responses and generates HTML report
"""

import requests
import time
import os
from datetime import datetime

# Test directly against staging instance
STAGING_URL = "http://3.21.167.170:8080"  # Direct to instance, port 8080

def test_data_analysis_v3():
    """Test Data Analysis V3 with real interactions."""
    
    print(f"\n{'='*60}")
    print("TESTING DATA ANALYSIS V3 ON STAGING")
    print(f"{'='*60}")
    print(f"Endpoint: {STAGING_URL}")
    
    # Unique session
    session_id = f'test_{int(time.time())}'
    interactions = []
    
    # 1. Upload data
    print("\n1. Uploading Adamawa TPR data...")
    data_file = 'www/adamawa_tpr_cleaned.csv'
    
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        return
    
    with open(data_file, 'rb') as f:
        files = {'file': ('test.csv', f, 'text/csv')}
        data = {'session_id': session_id}
        
        try:
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
                print(f"   Response: {response.text[:500]}")
                return
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return
    
    time.sleep(3)
    
    # Test queries
    queries = [
        "What's in the uploaded data? Give me a quick overview.",
        "Show me the top 10 health facilities by total testing volume. List all 10.",
        "Generate a statistical summary of the testing data.",
        "Create a visualization showing the distribution of testing."
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Testing: {query[:50]}...")
        
        start_time = time.time()
        try:
            response = requests.post(
                f"{STAGING_URL}/api/v1/data-analysis/chat",
                json={
                    'message': query,
                    'session_id': session_id
                },
                timeout=120
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                message = result.get('message', 'No response')
                
                print(f"   ✅ Success: {success}")
                print(f"   Response time: {response_time:.2f}s")
                print(f"   Response preview: {message[:200]}...")
                
                # Check for top 10 specifics
                if "top 10" in query.lower():
                    import re
                    numbered_items = re.findall(r'^\s*\d+\.', message, re.MULTILINE)
                    print(f"   Number of items found: {len(numbered_items)}")
                    
                    # Check for hallucinations
                    if "Facility A" in message or "Facility B" in message:
                        print("   ❌ HALLUCINATION DETECTED!")
                    else:
                        print("   ✅ No hallucinations")
                
                interactions.append({
                    'query': query,
                    'response': message,
                    'success': success,
                    'response_time': response_time,
                    'timestamp': datetime.now().isoformat()
                })
                
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Generate HTML report
    print(f"\n{'='*60}")
    print("GENERATING HTML REPORT")
    print(f"{'='*60}")
    
    html = generate_html_report(session_id, interactions)
    
    report_path = f"tests/staging_test_{session_id}.html"
    os.makedirs("tests", exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML report saved to: {report_path}")
    print(f"   Open this file in a browser to view the complete interactions")
    
    # Summary
    successful = sum(1 for i in interactions if i.get('success'))
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total queries: {len(interactions)}")
    print(f"Successful: {successful}/{len(interactions)}")
    print(f"Success rate: {(successful/len(interactions)*100):.1f}%" if interactions else "N/A")

def generate_html_report(session_id, interactions):
    """Generate HTML report of interactions."""
    
    total = len(interactions)
    successful = sum(1 for i in interactions if i.get('success'))
    avg_time = sum(i['response_time'] for i in interactions) / total if total > 0 else 0
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Data Analysis V3 Test - {session_id}</title>
    <style>
        body {{
            font-family: -apple-system, system-ui, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .interaction {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .query {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            border-left: 4px solid #2196f3;
        }}
        .response {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 6px;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 14px;
            max-height: 500px;
            overflow-y: auto;
        }}
        .metadata {{
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 14px;
        }}
        .success {{ color: #4caf50; }}
        .failed {{ color: #f44336; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Data Analysis V3 Test Report</h1>
        <p>Session: {session_id}</p>
        <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Endpoint: {STAGING_URL}</p>
    </div>
    
    <div class="stats">
        <div class="stat">
            <h3>Total Queries</h3>
            <p style="font-size: 24px; font-weight: bold;">{total}</p>
        </div>
        <div class="stat">
            <h3>Successful</h3>
            <p style="font-size: 24px; font-weight: bold;">{successful}/{total}</p>
        </div>
        <div class="stat">
            <h3>Success Rate</h3>
            <p style="font-size: 24px; font-weight: bold;">{(successful/total*100):.1f}%</p>
        </div>
        <div class="stat">
            <h3>Avg Response Time</h3>
            <p style="font-size: 24px; font-weight: bold;">{avg_time:.2f}s</p>
        </div>
    </div>
    
    <h2>Interaction Details</h2>
"""
    
    for i, interaction in enumerate(interactions, 1):
        status = "success" if interaction.get('success') else "failed"
        status_icon = "✅" if interaction.get('success') else "❌"
        
        html += f"""
    <div class="interaction">
        <h3>Query {i}</h3>
        <div class="query">
            <strong>User:</strong> {interaction['query']}
        </div>
        <div class="response">
            <strong>Agent Response:</strong>
{interaction.get('response', 'No response')}
        </div>
        <div class="metadata">
            <span class="{status}">{status_icon} {status.title()}</span> | 
            Response Time: {interaction['response_time']:.2f}s | 
            {interaction['timestamp']}
        </div>
    </div>
"""
    
    html += """
</body>
</html>
"""
    return html

if __name__ == "__main__":
    test_data_analysis_v3()
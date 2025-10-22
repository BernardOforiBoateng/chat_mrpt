#!/usr/bin/env python3
"""
Quick test of user simulation with just 3 queries
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import html

# Configuration
STAGING_URL = "http://3.21.167.170:8080"
DATA_FILE = "www/adamawa_tpr_cleaned.csv"
OUTPUT_FILE = "quick_test_report.html"

# Just 3 test queries
TEST_QUERIES = [
    {
        "category": "Data Exploration",
        "query": "How many rows and columns are in my data?",
        "intent": "Basic statistics"
    },
    {
        "category": "Facility Analysis",
        "query": "Show me the top 5 health facilities by total testing volume",
        "intent": "High-performing facilities"
    },
    {
        "category": "Testing Analysis",
        "query": "What's the total number of malaria tests conducted?",
        "intent": "Overall testing volume"
    }
]


class QuickSimulator:
    def __init__(self):
        self.base_url = STAGING_URL
        self.session_id = f"quick_test_{int(time.time())}"
        self.conversations = []
        self.start_time = datetime.now()
        
    def upload_data(self):
        """Upload the test data file."""
        print(f"📤 Uploading data (session: {self.session_id})...")
        
        with open(DATA_FILE, 'rb') as f:
            files = {'file': ('adamawa_tpr_cleaned.csv', f)}
            data = {'session_id': self.session_id}
            
            response = requests.post(
                f"{self.base_url}/api/data-analysis/upload",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Data uploaded successfully")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return False
    
    def ask_question(self, query_info):
        """Send a query and get response."""
        query = query_info["query"]
        print(f"\n💬 Asking: {query}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/data-analysis/chat",
                json={
                    "message": query,
                    "session_id": self.session_id
                },
                timeout=60
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", "")
                
                # Store conversation
                self.conversations.append({
                    "category": query_info["category"],
                    "intent": query_info["intent"],
                    "query": query,
                    "response": message,
                    "success": True,
                    "elapsed_time": elapsed
                })
                
                print(f"✅ Response received ({elapsed:.1f}s)")
                print(f"   Preview: {message[:100]}...")
                return True
            else:
                print(f"❌ Request failed: {response.status_code}")
                self.conversations.append({
                    "category": query_info["category"],
                    "intent": query_info["intent"],
                    "query": query,
                    "response": f"HTTP {response.status_code}: {response.text[:200]}",
                    "success": False,
                    "elapsed_time": elapsed
                })
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            self.conversations.append({
                "category": query_info["category"],
                "intent": query_info["intent"],
                "query": query,
                "response": str(e),
                "success": False,
                "elapsed_time": 0
            })
            return False
    
    def run_test(self):
        """Run the quick test."""
        print("🚀 Starting Quick Simulation Test")
        print("=" * 60)
        
        # Upload data
        if not self.upload_data():
            print("Failed to upload data, aborting")
            return False
        
        # Wait for processing
        time.sleep(3)
        
        # Ask questions
        for i, query_info in enumerate(TEST_QUERIES, 1):
            print(f"\n[{i}/{len(TEST_QUERIES)}] Category: {query_info['category']}")
            self.ask_question(query_info)
            time.sleep(2)
        
        print("\n" + "=" * 60)
        print("✅ Quick Test Complete!")
        
        # Generate report
        self.generate_report()
        return True
    
    def generate_report(self):
        """Generate HTML report."""
        
        # Calculate stats
        total = len(self.conversations)
        successful = sum(1 for c in self.conversations if c['success'])
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Quick Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .stats {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .conversation {{
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }}
        .user-msg {{
            background: #e3f2fd;
            padding: 15px;
            border-left: 4px solid #2196f3;
        }}
        .agent-msg {{
            background: white;
            padding: 15px;
            border-left: 4px solid #4caf50;
        }}
        .meta {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        .content {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .success {{
            color: #4caf50;
            font-weight: bold;
        }}
        .error {{
            color: #f44336;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Quick Simulation Test Report</h1>
        
        <div class="stats">
            <h2>Statistics</h2>
            <p><strong>Session ID:</strong> {self.session_id}</p>
            <p><strong>Success Rate:</strong> {successful}/{total} ({(successful/total*100):.0f}%)</p>
            <p><strong>Test Time:</strong> {(datetime.now() - self.start_time).total_seconds():.1f} seconds</p>
            <p><strong>Server:</strong> {self.base_url}</p>
        </div>
        
        <h2>Conversations</h2>
"""
        
        for conv in self.conversations:
            status_class = "success" if conv['success'] else "error"
            status_text = "✅ Success" if conv['success'] else "❌ Failed"
            
            html_content += f"""
        <div class="conversation">
            <div class="user-msg">
                <div class="meta">
                    <strong>👤 User Query</strong> | Category: {conv['category']} | Intent: {conv['intent']}
                </div>
                <div class="content">{html.escape(conv['query'])}</div>
            </div>
            <div class="agent-msg">
                <div class="meta">
                    <strong>🤖 Agent Response</strong> | 
                    <span class="{status_class}">{status_text}</span> | 
                    Time: {conv['elapsed_time']:.1f}s
                </div>
                <div class="content">{html.escape(conv['response'][:1000])}{'...' if len(conv['response']) > 1000 else ''}</div>
            </div>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        # Save report
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n📄 Report saved to: {OUTPUT_FILE}")
        abs_path = Path(OUTPUT_FILE).absolute()
        print(f"   Open in browser: file:///{abs_path}")


def main():
    """Run the quick test."""
    print("=" * 60)
    print("ChatMRPT Data Analysis V3 - Quick Test")
    print("=" * 60)
    
    # Check if data file exists
    if not Path(DATA_FILE).exists():
        print(f"❌ Data file not found: {DATA_FILE}")
        return False
    
    # Run test
    simulator = QuickSimulator()
    return simulator.run_test()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
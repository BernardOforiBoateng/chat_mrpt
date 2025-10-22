#!/usr/bin/env python3
"""
Simulate real user interactions with the Data Analysis V3 agent
Generates an HTML report showing the complete conversation
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
OUTPUT_FILE = "user_simulation_report.html"

# Realistic user queries covering various analysis types
USER_QUERIES = [
    # Basic exploration
    {
        "category": "Data Exploration",
        "query": "What kind of data do I have? Give me a summary of this dataset",
        "intent": "Understanding the data"
    },
    {
        "category": "Data Exploration", 
        "query": "How many rows and columns are in my data?",
        "intent": "Basic statistics"
    },
    {
        "category": "Data Exploration",
        "query": "What time period does this data cover?",
        "intent": "Temporal understanding"
    },
    
    # Facility analysis
    {
        "category": "Facility Analysis",
        "query": "Show me the top 10 health facilities by total testing volume",
        "intent": "High-performing facilities"
    },
    {
        "category": "Facility Analysis",
        "query": "Which facilities have the highest test positivity rates?",
        "intent": "Disease burden identification"
    },
    {
        "category": "Facility Analysis",
        "query": "How many unique health facilities are in the dataset?",
        "intent": "Coverage assessment"
    },
    
    # Geographic analysis
    {
        "category": "Geographic Analysis",
        "query": "Which LGA has the most malaria cases?",
        "intent": "Geographic hotspots"
    },
    {
        "category": "Geographic Analysis",
        "query": "Compare testing volumes across different LGAs",
        "intent": "Regional comparison"
    },
    {
        "category": "Geographic Analysis",
        "query": "Which wards have the lowest testing coverage?",
        "intent": "Gap identification"
    },
    
    # Testing analysis
    {
        "category": "Testing Analysis",
        "query": "What's the total number of malaria tests conducted?",
        "intent": "Overall testing volume"
    },
    {
        "category": "Testing Analysis",
        "query": "Compare RDT vs Microscopy testing volumes",
        "intent": "Testing method comparison"
    },
    {
        "category": "Testing Analysis",
        "query": "What percentage of tests are for children under 5?",
        "intent": "Age group analysis"
    },
    
    # Positivity rates
    {
        "category": "Positivity Rates",
        "query": "Calculate the overall test positivity rate",
        "intent": "Disease prevalence"
    },
    {
        "category": "Positivity Rates",
        "query": "What's the positivity rate for pregnant women?",
        "intent": "Vulnerable group analysis"
    },
    {
        "category": "Positivity Rates",
        "query": "Compare positivity rates between children and adults",
        "intent": "Age-based comparison"
    },
    
    # LLIN distribution
    {
        "category": "LLIN Distribution",
        "query": "How many bed nets (LLINs) were distributed in total?",
        "intent": "Prevention coverage"
    },
    {
        "category": "LLIN Distribution",
        "query": "Which facilities distributed the most LLINs to children?",
        "intent": "Distribution effectiveness"
    },
    
    # Complex analysis
    {
        "category": "Complex Analysis",
        "query": "Show me facilities with high testing volume but low positivity rate",
        "intent": "Efficiency analysis"
    },
    {
        "category": "Complex Analysis",
        "query": "Create a summary report of key malaria indicators by LGA",
        "intent": "Executive summary"
    },
    {
        "category": "Complex Analysis",
        "query": "What patterns do you see in the data that I should know about?",
        "intent": "Insight discovery"
    }
]


class UserSimulator:
    def __init__(self, base_url=STAGING_URL):
        self.base_url = base_url
        self.session_id = f"simulation_{int(time.time())}"
        self.conversations = []
        self.start_time = datetime.now()
        
    def upload_data(self):
        """Upload the test data file."""
        print("📤 Uploading data file...")
        
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
                return False
    
    def ask_question(self, query_info):
        """Send a query and get response."""
        query = query_info["query"]
        print(f"\n💬 Asking: {query[:60]}...")
        
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
                    "elapsed_time": elapsed,
                    "has_error": self._check_for_errors(message),
                    "has_numbers": self._check_for_numbers(message),
                    "response_length": len(message)
                })
                
                print(f"✅ Response received ({elapsed:.1f}s)")
                return True
            else:
                self.conversations.append({
                    "category": query_info["category"],
                    "intent": query_info["intent"],
                    "query": query,
                    "response": f"HTTP {response.status_code}",
                    "success": False,
                    "elapsed_time": elapsed,
                    "has_error": True,
                    "has_numbers": False,
                    "response_length": 0
                })
                print(f"❌ Request failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.conversations.append({
                "category": query_info["category"],
                "intent": query_info["intent"],
                "query": query,
                "response": str(e),
                "success": False,
                "elapsed_time": 0,
                "has_error": True,
                "has_numbers": False,
                "response_length": 0
            })
            print(f"❌ Error: {e}")
            return False
    
    def _check_for_errors(self, message):
        """Check if response contains error indicators."""
        error_words = ['error', 'issue', 'problem', 'difficulty', 'trouble', 'failed']
        return any(word in message.lower() for word in error_words)
    
    def _check_for_numbers(self, message):
        """Check if response contains numeric data."""
        return any(char.isdigit() for char in message)
    
    def run_simulation(self):
        """Run the full simulation."""
        print("🚀 Starting User Simulation")
        print("=" * 60)
        
        # Upload data
        if not self.upload_data():
            print("Failed to upload data, aborting simulation")
            return
        
        # Wait for processing
        time.sleep(3)
        
        # Ask all questions
        for i, query_info in enumerate(USER_QUERIES, 1):
            print(f"\n[{i}/{len(USER_QUERIES)}] Category: {query_info['category']}")
            self.ask_question(query_info)
            time.sleep(2)  # Be nice to the server
        
        print("\n" + "=" * 60)
        print("✅ Simulation Complete!")
        
        # Calculate statistics
        self.calculate_stats()
        
        # Generate HTML report
        self.generate_html_report()
    
    def calculate_stats(self):
        """Calculate simulation statistics."""
        total = len(self.conversations)
        successful = sum(1 for c in self.conversations if c['success'])
        with_errors = sum(1 for c in self.conversations if c['has_error'])
        with_numbers = sum(1 for c in self.conversations if c['has_numbers'])
        
        avg_time = sum(c['elapsed_time'] for c in self.conversations) / total if total > 0 else 0
        avg_length = sum(c['response_length'] for c in self.conversations) / total if total > 0 else 0
        
        self.stats = {
            'total_queries': total,
            'successful': successful,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'with_errors': with_errors,
            'with_numbers': with_numbers,
            'avg_response_time': avg_time,
            'avg_response_length': avg_length,
            'total_time': (datetime.now() - self.start_time).total_seconds()
        }
        
        print(f"\n📊 Statistics:")
        print(f"  Success Rate: {self.stats['success_rate']:.1f}%")
        print(f"  Avg Response Time: {self.stats['avg_response_time']:.1f}s")
        print(f"  Responses with Numbers: {with_numbers}/{total}")
        print(f"  Responses with Errors: {with_errors}/{total}")
    
    def generate_html_report(self):
        """Generate an HTML report of the conversation."""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatMRPT User Simulation Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .conversations {{
            padding: 30px;
        }}
        
        .category-section {{
            margin-bottom: 40px;
        }}
        
        .category-header {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 10px 10px 0 0;
            font-size: 1.3em;
            font-weight: 500;
        }}
        
        .conversation {{
            background: white;
            border: 1px solid #e9ecef;
            border-top: none;
            margin-bottom: 20px;
        }}
        
        .conversation:last-child {{
            border-radius: 0 0 10px 10px;
        }}
        
        .user-message {{
            background: #f8f9fa;
            padding: 20px;
            border-left: 4px solid #667eea;
        }}
        
        .user-label {{
            color: #667eea;
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .intent {{
            font-size: 0.85em;
            color: #6c757d;
            font-weight: normal;
            font-style: italic;
        }}
        
        .agent-message {{
            padding: 20px;
            background: white;
        }}
        
        .agent-label {{
            color: #764ba2;
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .message-meta {{
            font-size: 0.85em;
            color: #6c757d;
            font-weight: normal;
        }}
        
        .message-content {{
            color: #495057;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .success-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        
        .success {{
            background: #28a745;
        }}
        
        .error {{
            background: #dc3545;
        }}
        
        .warning {{
            background: #ffc107;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}
        
        .chart-container {{
            padding: 30px;
            background: white;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.3s ease;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 ChatMRPT User Simulation Report</h1>
            <div class="subtitle">Data Analysis V3 Agent - Adamawa TPR Dataset</div>
            <div class="subtitle">{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{self.stats['success_rate']:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.stats['successful']}/{self.stats['total_queries']}</div>
                <div class="stat-label">Successful Queries</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.stats['avg_response_time']:.1f}s</div>
                <div class="stat-label">Avg Response Time</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.stats['with_numbers']}</div>
                <div class="stat-label">Responses with Data</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2 style="margin-bottom: 20px;">Overall Performance</h2>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {self.stats['success_rate']}%">
                    {self.stats['success_rate']:.1f}% Success Rate
                </div>
            </div>
        </div>
        
        <div class="conversations">
            <h2 style="margin-bottom: 30px;">📝 Conversation Log</h2>
"""
        
        # Group conversations by category
        from collections import defaultdict
        grouped = defaultdict(list)
        for conv in self.conversations:
            grouped[conv['category']].append(conv)
        
        # Generate HTML for each category
        for category, convs in grouped.items():
            html_content += f"""
            <div class="category-section">
                <div class="category-header">{category}</div>
"""
            
            for conv in convs:
                # Determine status indicator
                if conv['success'] and not conv['has_error']:
                    indicator_class = "success"
                elif conv['has_error']:
                    indicator_class = "warning"
                else:
                    indicator_class = "error"
                
                # Escape HTML in responses
                response = html.escape(conv['response'])
                
                html_content += f"""
                <div class="conversation">
                    <div class="user-message">
                        <div class="user-label">
                            <span><span class="success-indicator {indicator_class}"></span>👤 User</span>
                            <span class="intent">Intent: {conv['intent']}</span>
                        </div>
                        <div class="message-content">{html.escape(conv['query'])}</div>
                    </div>
                    <div class="agent-message">
                        <div class="agent-label">
                            <span>🤖 Agent</span>
                            <span class="message-meta">
                                {conv['elapsed_time']:.1f}s | {conv['response_length']} chars
                                {' | ⚠️ Error' if conv['has_error'] else ''}
                                {' | 📊 Data' if conv['has_numbers'] else ''}
                            </span>
                        </div>
                        <div class="message-content">{response[:1000]}{'...' if len(response) > 1000 else ''}</div>
                    </div>
                </div>
"""
            
            html_content += """
            </div>
"""
        
        # Add footer
        html_content += f"""
        </div>
        
        <div class="footer">
            <p>Generated by ChatMRPT Test Suite | Session: {self.session_id}</p>
            <p>Total simulation time: {self.stats['total_time']:.1f} seconds</p>
            <p>Column Sanitization: ✅ Enabled | Server: {self.base_url}</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Save to file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n📄 HTML report saved to: {OUTPUT_FILE}")
        print(f"   Open in browser: file://{Path(OUTPUT_FILE).absolute()}")


def main():
    """Run the user simulation."""
    print("=" * 60)
    print("ChatMRPT Data Analysis V3 - User Simulation")
    print("=" * 60)
    
    # Check if data file exists
    if not Path(DATA_FILE).exists():
        print(f"❌ Data file not found: {DATA_FILE}")
        return
    
    # Create simulator and run
    simulator = UserSimulator()
    simulator.run_simulation()
    
    print("\n✨ Simulation complete! Check the HTML report for detailed results.")


if __name__ == "__main__":
    main()
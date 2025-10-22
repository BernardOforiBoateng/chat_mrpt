"""
Evaluated Ultimate Stress Test
Tests agent with comprehensive quality evaluation
"""

import requests
import time
import json
from datetime import datetime
from pathlib import Path
import sys
sys.path.append('/tmp')
from response_evaluator import ResponseEvaluator

BASE_URL = "https://d225ar6c86586s.cloudfront.net"

class EvaluatedStressTest:
    def __init__(self):
        self.session = requests.Session()
        self.session_id = None
        self.interactions = []
        self.test_start = datetime.now()
        self.evaluator = ResponseEvaluator()

    def upload_real_tpr_data(self):
        """Upload real 1.37 MB Adamawa TPR data"""
        tpr_file = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/adamawa_tpr_cleaned.csv"

        print(f"\n{'='*80}")
        print("📤 UPLOADING REAL TPR DATA")
        print(f"{'='*80}")
        print(f"File: {tpr_file}")

        with open(tpr_file, 'rb') as f:
            files = {'file': ('adamawa_tpr_cleaned.csv', f, 'text/csv')}
            response = self.session.post(f"{BASE_URL}/api/v1/data-analysis/upload", files=files)

        if response.status_code == 200:
            data = response.json()
            self.session_id = data.get('session_id')
            print(f"✅ Upload successful")
            print(f"📊 Session ID: {self.session_id}")
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return False

    def test_scenario(self, category, num, title, query, timeout=60):
        """Run a single test scenario with comprehensive evaluation"""
        print(f"\n{'='*80}")
        print(f"[{category} #{num}] {title}")
        print(f"{'='*80}")
        print(f"User says: \"{query}\"")

        chat_url = f"{BASE_URL}/api/v1/data-analysis/chat"

        start = time.time()

        try:
            response = self.session.post(chat_url, json={
                "message": query,
                "session_id": self.session_id
            }, timeout=timeout)

            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                message = data.get('message', '')
                visualizations = data.get('visualizations', [])

                print(f"\n💬 Agent Response ({len(message)} chars):")
                print(f"{message[:300]}{'...' if len(message) > 300 else ''}")

                # EVALUATE RESPONSE QUALITY
                print(f"\n📊 EVALUATING RESPONSE QUALITY...")
                evaluation = self.evaluator.evaluate_response(
                    user_query=query,
                    agent_response=message,
                    category=category,
                    use_llm=True  # Use GPT-4 as judge
                )

                print(f"\n{evaluation['grade_emoji']} QUALITY SCORE: {evaluation['final_score']}/100 ({evaluation['grade']})")
                print(f"   Automated: {evaluation['automated_score']}/40")
                print(f"   LLM Judge: {evaluation['llm_score']}/50")
                print(f"   Length Bonus: {evaluation['length_bonus']}/10")

                if evaluation['automated_reasons']:
                    print(f"\n   Automated Checks:")
                    for reason in evaluation['automated_reasons']:
                        print(f"      {reason}")

                # Get benchmark for this category
                benchmark = self.evaluator.get_category_benchmark(category)
                if evaluation['final_score'] >= benchmark['excellent']:
                    benchmark_status = "✅ EXCEEDS EXCELLENT BENCHMARK"
                elif evaluation['final_score'] >= benchmark['good']:
                    benchmark_status = "✅ MEETS GOOD BENCHMARK"
                elif evaluation['final_score'] >= benchmark['acceptable']:
                    benchmark_status = "⚠️ MEETS MINIMUM ACCEPTABLE"
                else:
                    benchmark_status = "❌ BELOW ACCEPTABLE THRESHOLD"

                print(f"\n   Benchmark: {benchmark_status}")
                print(f"   ⏱️  Duration: {duration:.2f}s")

                # Store interaction with evaluation
                self.interactions.append({
                    'category': category,
                    'num': num,
                    'title': title,
                    'query': query,
                    'message': message,
                    'visualizations': visualizations,
                    'duration': duration,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'evaluation': evaluation,
                    'benchmark': benchmark,
                    'benchmark_status': benchmark_status
                })

                return data
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return None

    def run_ultimate_tests(self):
        """Run all test scenarios"""

        # Upload data
        if not self.upload_real_tpr_data():
            print("Failed to upload data. Exiting.")
            return

        time.sleep(2)

        # ==================== CATEGORY 1: BEGINNERS ====================
        print("\n\n" + "👶 "*20)
        print("CATEGORY 1: COMPLETE BEGINNERS")
        print("👶 "*20)

        self.test_scenario("BEGINNER", 1,
            "User has no idea what they're doing",
            "I have data about malaria but I don't know what to do with it")
        time.sleep(3)

        self.test_scenario("BEGINNER", 2,
            "User doesn't know what TPR is",
            "What is TPR and why should I care?")
        time.sleep(3)

        self.test_scenario("BEGINNER", 3,
            "User wants instant results without understanding",
            "Can you just analyze my malaria data and tell me which areas are bad?")
        time.sleep(3)

        self.test_scenario("BEGINNER", 4,
            "User wants complete autonomy",
            "I'm not technical. Can you just do the analysis and give me results without me having to choose anything?")
        time.sleep(3)

        # ==================== CATEGORY 2: NATURAL LANGUAGE ====================
        print("\n\n" + "💬 "*20)
        print("CATEGORY 2: COMPLEX NATURAL LANGUAGE REQUESTS")
        print("💬 "*20)

        self.test_scenario("NATURAL", 1,
            "Multi-step request in one sentence",
            "Calculate TPR for primary facilities, focus on children under 5, and export the results to PDF with maps")
        time.sleep(3)

        self.test_scenario("NATURAL", 2,
            "Vague request with implied intent",
            "Show me where malaria is worst so we can send bed nets there")
        time.sleep(3)

        self.test_scenario("NATURAL", 3,
            "Request using different terminology",
            "Give me the infection rate percentages broken down by hospital type and patient demographics")
        time.sleep(3)

        # ==================== CATEGORY 3: BIZARRE ====================
        print("\n\n" + "🤪 "*20)
        print("CATEGORY 3: BIZARRE, UNREALISTIC, CHALLENGING")
        print("🤪 "*20)

        self.test_scenario("BIZARRE", 1,
            "User asks for impossible request",
            "Can you predict next year's malaria rates using AI and machine learning?")
        time.sleep(3)

        self.test_scenario("BIZARRE", 2,
            "User asks question in middle of nowhere",
            "What's the capital of Nigeria?")
        time.sleep(3)

        # ==================== CATEGORY 4: EXPORT ====================
        print("\n\n" + "📤 "*20)
        print("CATEGORY 4: EXPORT, OUTPUT, DOWNLOAD REQUESTS")
        print("📤 "*20)

        self.test_scenario("EXPORT", 1,
            "PDF export request",
            "Export everything to PDF")
        time.sleep(3)

        self.test_scenario("EXPORT", 2,
            "Specific output format",
            "Give me a CSV file with all the TPR data by ward that I can open in Excel")
        time.sleep(3)

        # ==================== CATEGORY 5: WORKFLOW IGNORANCE ====================
        print("\n\n" + "🚫 "*20)
        print("CATEGORY 5: USERS WHO IGNORE/DON'T KNOW THE WORKFLOW")
        print("🚫 "*20)

        self.test_scenario("WORKFLOW", 1,
            "Demands results immediately",
            "Just give me the TPR results now")
        time.sleep(3)

        self.test_scenario("WORKFLOW", 2,
            "User doesn't want to make choices",
            "I don't care about facility types or age groups, just show me the data")
        time.sleep(3)

        # ==================== CATEGORY 6: EXTREME EDGE CASES ====================
        print("\n\n" + "🔥 "*20)
        print("CATEGORY 6: EXTREME EDGE CASES")
        print("🔥 "*20)

        self.test_scenario("EDGE", 1,
            "Multiple questions barrage",
            "What's TPR? How is it calculated? Why is it important? What do the numbers mean? How do I use this tool?")
        time.sleep(3)

        # ==================== CATEGORY 7: HELP SYSTEM ====================
        print("\n\n" + "❓ "*20)
        print("CATEGORY 7: HELP SYSTEM")
        print("❓ "*20)

        self.test_scenario("HELP", 1,
            "Basic help request",
            "help")
        time.sleep(3)

        self.test_scenario("HELP", 2,
            "User is lost",
            "I'm lost, what do I do?")
        time.sleep(3)

        self.test_scenario("HELP", 3,
            "Explain like I'm 5",
            "Can you walk me through this step by step like I'm 5 years old?")
        time.sleep(3)

        print("\n\n" + "="*80)
        print("🏁 ALL TESTS COMPLETE")
        print("="*80)

    def generate_scored_html(self, output_file="/tmp/evaluated_stress_test_report.html"):
        """Generate HTML report with quality scores and visualizations"""

        total_tests = len(self.interactions)
        if total_tests == 0:
            print("No interactions to report")
            return None

        # Calculate statistics
        total_score = sum(i['evaluation']['final_score'] for i in self.interactions)
        avg_score = total_score / total_tests

        # Count by grade
        grades = {}
        for interaction in self.interactions:
            grade = interaction['evaluation']['grade']
            grades[grade] = grades.get(grade, 0) + 1

        # Category averages
        category_scores = {}
        for interaction in self.interactions:
            cat = interaction['category']
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(interaction['evaluation']['final_score'])

        category_averages = {cat: sum(scores)/len(scores) for cat, scores in category_scores.items()}

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Evaluated Stress Test Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 20px;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #1e293b;
            padding: 25px;
            border-radius: 12px;
            border-left: 4px solid #10b981;
        }}
        .stat-card .label {{
            color: #94a3b8;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #10b981;
        }}
        .category-section {{
            margin-bottom: 40px;
        }}
        .category-header {{
            background: #1e293b;
            padding: 20px;
            border-radius: 12px 12px 0 0;
            border-left: 6px solid #10b981;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .category-header h2 {{
            color: #10b981;
            font-size: 1.5em;
        }}
        .category-score {{
            font-size: 1.8em;
            font-weight: bold;
            color: #10b981;
        }}
        .test-card {{
            background: #1e293b;
            margin-bottom: 20px;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #334155;
        }}
        .test-header {{
            background: #0f172a;
            padding: 20px;
            border-bottom: 1px solid #334155;
        }}
        .test-title {{
            font-size: 1.2em;
            color: #10b981;
            margin-bottom: 10px;
        }}
        .test-query {{
            background: #334155;
            padding: 15px;
            border-radius: 8px;
            font-style: italic;
            color: #cbd5e1;
            border-left: 3px solid #10b981;
        }}
        .test-body {{
            padding: 20px;
        }}
        .score-banner {{
            background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .score-banner.excellent {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }}
        .score-banner.good {{
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        }}
        .score-banner.acceptable {{
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        }}
        .score-banner.needs-work {{
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        }}
        .score-main {{
            font-size: 3em;
            font-weight: bold;
        }}
        .score-details {{
            text-align: right;
        }}
        .evaluation-breakdown {{
            background: #0f172a;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        .evaluation-breakdown h4 {{
            color: #3b82f6;
            margin-bottom: 10px;
        }}
        .check-item {{
            padding: 8px;
            margin: 5px 0;
            background: #1e293b;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        .response-section {{
            background: #0f172a;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }}
        .response-section h4 {{
            color: #10b981;
            margin-bottom: 15px;
            font-size: 1.1em;
        }}
        .response-text {{
            background: #1e293b;
            padding: 15px;
            border-radius: 6px;
            line-height: 1.6;
            color: #cbd5e1;
            max-height: 400px;
            overflow-y: auto;
        }}
        .llm-justification {{
            background: #1e293b;
            padding: 15px;
            border-radius: 6px;
            border-left: 3px solid #3b82f6;
            margin-top: 10px;
            font-style: italic;
            color: #cbd5e1;
        }}
        .metadata {{
            display: flex;
            gap: 20px;
            margin-top: 15px;
            color: #94a3b8;
            font-size: 0.9em;
        }}
        .summary-section {{
            background: #1e293b;
            padding: 30px;
            border-radius: 12px;
            margin-top: 40px;
        }}
        .summary-section h2 {{
            color: #10b981;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 EVALUATED STRESS TEST REPORT</h1>
            <p>Comprehensive Quality Assessment with Benchmarks</p>
            <p style="margin-top: 10px; opacity: 0.9;">{self.test_start.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="label">Total Tests</div>
                <div class="value">{total_tests}</div>
            </div>
            <div class="stat-card">
                <div class="label">Average Score</div>
                <div class="value">{avg_score:.1f}/100</div>
            </div>
            <div class="stat-card">
                <div class="label">Excellent Ratings</div>
                <div class="value">{grades.get('EXCELLENT', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Good Ratings</div>
                <div class="value">{grades.get('GOOD', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Acceptable</div>
                <div class="value">{grades.get('ACCEPTABLE', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Needs Work</div>
                <div class="value">{grades.get('NEEDS WORK', 0)}</div>
            </div>
        </div>
"""

        # Group by category
        categories = {}
        for interaction in self.interactions:
            cat = interaction['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(interaction)

        for cat_name, tests in categories.items():
            cat_avg = category_averages[cat_name]
            html += f"""
        <div class="category-section">
            <div class="category-header">
                <h2>{cat_name} ({len(tests)} tests)</h2>
                <div class="category-score">{cat_avg:.1f}/100</div>
            </div>
"""

            for test in tests:
                eval_data = test['evaluation']
                grade_class = eval_data['grade'].lower().replace(' ', '-')

                html += f"""
            <div class="test-card">
                <div class="test-header">
                    <div class="test-title">
                        {test['title']}
                    </div>
                    <div class="test-query">
                        "{test['query']}"
                    </div>
                </div>
                <div class="test-body">
                    <div class="score-banner {grade_class}">
                        <div>
                            <div style="font-size: 1.2em; margin-bottom: 5px;">{eval_data['grade_emoji']} {eval_data['grade']}</div>
                            <div style="font-size: 0.9em; opacity: 0.9;">{test['benchmark_status']}</div>
                        </div>
                        <div class="score-main">{eval_data['final_score']}/100</div>
                        <div class="score-details">
                            <div>Automated: {eval_data['automated_score']}/40</div>
                            <div>LLM Judge: {eval_data['llm_score']}/50</div>
                            <div>Length: {eval_data['length_bonus']}/10</div>
                        </div>
                    </div>

                    <div class="evaluation-breakdown">
                        <h4>🔍 Evaluation Details</h4>
"""

                if eval_data['automated_reasons']:
                    for reason in eval_data['automated_reasons']:
                        html += f"""
                        <div class="check-item">{reason}</div>
"""

                html += f"""
                    </div>

                    <div class="evaluation-breakdown">
                        <h4>🤖 LLM Judge Assessment</h4>
                        <div class="llm-justification">
                            {eval_data['llm_justification'][:500]}{'...' if len(eval_data['llm_justification']) > 500 else ''}
                        </div>
                    </div>

                    <div class="response-section">
                        <h4>💬 Agent Response ({eval_data['response_length']} characters)</h4>
                        <div class="response-text">
                            {test['message']}
                        </div>
                    </div>

                    <div class="metadata">
                        <span>⏱️ {test['duration']:.2f}s</span>
                        <span>🕐 {test['timestamp']}</span>
                    </div>
                </div>
            </div>
"""

            html += """
        </div>
"""

        # Summary section
        html += f"""
        <div class="summary-section">
            <h2>📈 Overall Assessment</h2>
            <p style="font-size: 1.2em; margin-bottom: 20px;">
                Average Score: <strong style="color: #10b981;">{avg_score:.1f}/100</strong>
            </p>
            <h3 style="color: #3b82f6; margin: 20px 0 10px 0;">Category Performance:</h3>
            <ul style="line-height: 2;">
"""

        for cat, avg in category_averages.items():
            if avg >= 80:
                indicator = "🌟 EXCELLENT"
            elif avg >= 70:
                indicator = "✅ GOOD"
            elif avg >= 60:
                indicator = "⚠️ ACCEPTABLE"
            else:
                indicator = "❌ NEEDS WORK"

            html += f"""
                <li><strong>{cat}:</strong> {avg:.1f}/100 {indicator}</li>
"""

        html += """
            </ul>
        </div>
    </div>
</body>
</html>
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n✅ Evaluated HTML report: {output_file}")
        return output_file

if __name__ == "__main__":
    tester = EvaluatedStressTest()
    tester.run_ultimate_tests()
    report = tester.generate_scored_html()

    # Copy to ChatMRPT tests folder
    if report:
        import shutil
        dest = f"/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tests/evaluated_stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        shutil.copy(report, dest)
        print(f"\n📁 Report saved to: tests/{Path(dest).name}")
    else:
        print("\n❌ No report generated")

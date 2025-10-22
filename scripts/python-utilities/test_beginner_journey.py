#!/usr/bin/env python3
"""
Test the complete beginner journey on AWS
Simulates a newcomer who knows nothing about ChatMRPT
"""

import requests
import json
import time
from datetime import datetime

# Test against ALB since CloudFront has issues
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

class BeginnerJourneyTest:
    def __init__(self):
        self.session = requests.Session()
        self.results = []
        self.test_count = 0
        self.pass_count = 0

    def test_question(self, category, question, expected_keywords=None, check_suggestions=False):
        """Test a single beginner question"""
        self.test_count += 1
        print(f"\n{'='*60}")
        print(f"Test {self.test_count}: {category}")
        print(f"Question: '{question}'")
        print("-" * 60)

        try:
            response = self.session.post(
                f"{BASE_URL}/analysis/send_message",
                json={"message": question},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '').lower()

                # Check if we got a meaningful response
                if len(response_text) > 50:
                    print(f"✅ Got response ({len(response_text)} chars)")
                    self.pass_count += 1

                    # Check for expected keywords
                    if expected_keywords:
                        found = [kw for kw in expected_keywords if kw.lower() in response_text]
                        if found:
                            print(f"✅ Found keywords: {', '.join(found)}")
                        else:
                            print(f"⚠️ Missing expected keywords")

                    # Check suggestions if requested
                    if check_suggestions:
                        suggestions = data.get('suggestions', [])
                        if suggestions:
                            print(f"✅ Got {len(suggestions)} suggestions:")
                            for sug in suggestions[:3]:
                                print(f"   • {sug.get('text', 'N/A')}")
                        else:
                            print("⚠️ No suggestions provided")

                    # Show response snippet
                    print(f"\nResponse preview: {response_text[:200]}...")

                    self.results.append({
                        'category': category,
                        'question': question,
                        'status': 'PASS',
                        'response_length': len(response_text)
                    })
                else:
                    print(f"❌ Response too short ({len(response_text)} chars)")
                    self.results.append({
                        'category': category,
                        'question': question,
                        'status': 'FAIL',
                        'error': 'Short response'
                    })

            else:
                print(f"❌ HTTP {response.status_code}")
                self.results.append({
                    'category': category,
                    'question': question,
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}'
                })

        except Exception as e:
            print(f"❌ Error: {e}")
            self.results.append({
                'category': category,
                'question': question,
                'status': 'ERROR',
                'error': str(e)
            })

        time.sleep(1)  # Be nice to the server

    def run_complete_beginner_journey(self):
        """Run the complete test suite simulating a total beginner"""

        print("=" * 70)
        print("COMPLETE BEGINNER JOURNEY TEST")
        print("Simulating a user who knows NOTHING about ChatMRPT")
        print(f"Target: {BASE_URL}")
        print(f"Started: {datetime.now()}")
        print("=" * 70)

        # PHASE 1: Discovery - "What is this thing?"
        print("\n\n📌 PHASE 1: DISCOVERY")
        print("A complete newcomer discovering ChatMRPT for the first time")

        self.test_question(
            "1.1 Basic Identity",
            "What is this?",
            expected_keywords=["chatmrpt", "malaria", "risk", "tool"],
            check_suggestions=True
        )

        self.test_question(
            "1.2 Purpose",
            "What does ChatMRPT do?",
            expected_keywords=["analyze", "malaria", "risk", "nigeria", "intervention"]
        )

        self.test_question(
            "1.3 Who Uses It",
            "Who is this for?",
            expected_keywords=["health", "officials", "nmep", "public health"]
        )

        # PHASE 2: Getting Started - "How do I begin?"
        print("\n\n📌 PHASE 2: GETTING STARTED")
        print("User wants to start but doesn't know how")

        self.test_question(
            "2.1 How to Start",
            "How do I start using this?",
            expected_keywords=["upload", "data", "csv", "file"],
            check_suggestions=True
        )

        self.test_question(
            "2.2 What Data Needed",
            "What kind of data do I need?",
            expected_keywords=["ward", "csv", "columns", "variables"]
        )

        self.test_question(
            "2.3 Data Format",
            "How should my data be formatted?",
            expected_keywords=["csv", "excel", "columns", "ward", "rows"]
        )

        self.test_question(
            "2.4 Required Columns",
            "What columns must my CSV have?",
            expected_keywords=["wardname", "statecode", "numeric", "required"]
        )

        # PHASE 3: Upload Process - "How do I upload?"
        print("\n\n📌 PHASE 3: UPLOAD PROCESS")
        print("User has data and wants to upload")

        self.test_question(
            "3.1 Where to Upload",
            "Where do I upload my file?",
            expected_keywords=["button", "sidebar", "left", "upload"],
            check_suggestions=True
        )

        self.test_question(
            "3.2 Upload Types",
            "Should I upload CSV or shapefile or both?",
            expected_keywords=["both", "csv", "shapefile", "map", "geographic"]
        )

        self.test_question(
            "3.3 Shapefile Format",
            "What is a shapefile and do I need it?",
            expected_keywords=["geographic", "boundaries", "map", "zip", "optional"]
        )

        # PHASE 4: Analysis - "What analysis should I run?"
        print("\n\n📌 PHASE 4: ANALYSIS")
        print("User has uploaded data and needs to analyze")

        self.test_question(
            "4.1 After Upload",
            "I uploaded my data, what next?",
            expected_keywords=["analyze", "run", "analysis", "button"],
            check_suggestions=True
        )

        self.test_question(
            "4.2 Analysis Types",
            "What's the difference between composite and PCA analysis?",
            expected_keywords=["composite", "pca", "weighted", "principal", "component"]
        )

        self.test_question(
            "4.3 Which Analysis",
            "Which analysis should I choose for malaria risk?",
            expected_keywords=["composite", "quick", "both", "recommend"]
        )

        self.test_question(
            "4.4 How Long",
            "How long does the analysis take?",
            expected_keywords=["seconds", "minute", "wait", "time"]
        )

        # PHASE 5: Understanding Results - "What do these results mean?"
        print("\n\n📌 PHASE 5: UNDERSTANDING RESULTS")
        print("User has results but doesn't understand them")

        self.test_question(
            "5.1 Interpret Results",
            "What do the analysis results mean?",
            expected_keywords=["risk", "score", "high", "low", "ward"]
        )

        self.test_question(
            "5.2 Risk Scores",
            "What does a high risk score mean?",
            expected_keywords=["malaria", "intervention", "priority", "vulnerable"]
        )

        self.test_question(
            "5.3 Map Colors",
            "What do the different colors on the map mean?",
            expected_keywords=["red", "high", "risk", "green", "low", "color"]
        )

        self.test_question(
            "5.4 Rankings",
            "How do I see which wards are highest risk?",
            expected_keywords=["ranking", "table", "sorted", "top", "list"]
        )

        # PHASE 6: Taking Action - "What should I do with this?"
        print("\n\n📌 PHASE 6: TAKING ACTION")
        print("User wants to use results for intervention planning")

        self.test_question(
            "6.1 Interventions",
            "What interventions should I plan based on these results?",
            expected_keywords=["itn", "nets", "high risk", "target", "intervention"]
        )

        self.test_question(
            "6.2 ITN Planning",
            "How do I plan ITN distribution?",
            expected_keywords=["itn", "tool", "distribution", "coverage", "nets"]
        )

        self.test_question(
            "6.3 Export Results",
            "How do I download or share these results?",
            expected_keywords=["download", "export", "csv", "report", "button"]
        )

        self.test_question(
            "6.4 Generate Report",
            "Can I create a report for stakeholders?",
            expected_keywords=["report", "word", "document", "generate", "summary"]
        )

        # PHASE 7: Troubleshooting - "Something went wrong"
        print("\n\n📌 PHASE 7: TROUBLESHOOTING")
        print("User encounters common problems")

        self.test_question(
            "7.1 Upload Error",
            "I'm getting an error uploading my file, what's wrong?",
            expected_keywords=["format", "check", "csv", "columns", "required"]
        )

        self.test_question(
            "7.2 Missing Columns",
            "It says missing WardName column but I have ward names",
            expected_keywords=["column", "name", "exact", "case", "rename"]
        )

        self.test_question(
            "7.3 No Map",
            "Why isn't the map showing?",
            expected_keywords=["shapefile", "geographic", "boundaries", "upload"]
        )

        self.test_question(
            "7.4 Analysis Failed",
            "The analysis failed, how do I fix it?",
            expected_keywords=["data", "variables", "numeric", "check", "minimum"]
        )

        # PHASE 8: Advanced Features - "What else can it do?"
        print("\n\n📌 PHASE 8: ADVANCED FEATURES")
        print("User exploring additional capabilities")

        self.test_question(
            "8.1 TPR Analysis",
            "What is TPR analysis and how do I use it?",
            expected_keywords=["test", "positivity", "rate", "nmep", "excel"]
        )

        self.test_question(
            "8.2 Available Tools",
            "What other tools are available?",
            expected_keywords=["visualization", "chart", "map", "analysis", "tools"]
        )

        self.test_question(
            "8.3 Customization",
            "Can I customize the analysis parameters?",
            expected_keywords=["weight", "variable", "parameter", "custom", "adjust"]
        )

        # Print final summary
        self.print_summary()

    def print_summary(self):
        """Print test results summary"""
        print("\n\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        print(f"\nTotal Tests: {self.test_count}")
        print(f"Passed: {self.pass_count}")
        print(f"Success Rate: {(self.pass_count/self.test_count)*100:.1f}%")

        # Group results by category
        print("\n📊 Results by Phase:")
        categories = {}
        for result in self.results:
            cat = result['category'].split('.')[0]
            if cat not in categories:
                categories[cat] = {'pass': 0, 'fail': 0}

            if result['status'] == 'PASS':
                categories[cat]['pass'] += 1
            else:
                categories[cat]['fail'] += 1

        for cat in sorted(categories.keys()):
            total = categories[cat]['pass'] + categories[cat]['fail']
            pass_rate = (categories[cat]['pass'] / total) * 100
            status = "✅" if pass_rate >= 70 else "⚠️" if pass_rate >= 40 else "❌"
            print(f"  {status} Phase {cat}: {categories[cat]['pass']}/{total} ({pass_rate:.0f}%)")

        # Check beginner friendliness
        print("\n🎯 Beginner Friendliness Assessment:")
        if self.pass_count / self.test_count >= 0.8:
            print("✅ EXCELLENT - Beginners can use ChatMRPT without external help!")
        elif self.pass_count / self.test_count >= 0.6:
            print("⚠️ GOOD - Most beginners can navigate, some areas need improvement")
        else:
            print("❌ NEEDS WORK - Beginners would struggle without help")

        print("\n" + "=" * 70)
        print(f"Test completed: {datetime.now()}")
        print("=" * 70)

if __name__ == "__main__":
    tester = BeginnerJourneyTest()
    tester.run_complete_beginner_journey()
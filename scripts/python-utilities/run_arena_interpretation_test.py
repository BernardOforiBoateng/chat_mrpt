#!/usr/bin/env python3
"""
Actually test Arena models with interpretation and planning prompts
Captures real responses for evaluation
"""

import requests
import json
import time
import sys
import os

# Setup
sys.path.append('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')
os.environ['FLASK_ENV'] = 'production'

# Production endpoint
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

# Session with Adamawa data
SESSION_ID = "9000f9df-451d-4dd9-a4d1-2040becdf902"

def test_arena_model(prompt, session_id=None):
    """Send prompt to Arena and get response"""
    url = f"{BASE_URL}/send_message"
    payload = {
        "message": prompt,
        "session_id": session_id or f"test-interpret-{int(time.time())}"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

print("="*80)
print("ARENA MODEL INTERPRETATION TEST - ACTUAL RESPONSES")
print("="*80)
print(f"Using session: {SESSION_ID} (Adamawa State data)")
print()

# Define focused test prompts
test_prompts = [
    {
        "id": "interpret_1",
        "category": "Data Interpretation",
        "prompt": "Based on the Adamawa State vulnerability analysis showing Gwapopolok, Gamu, and Bakta as the top 3 highest risk wards with scores around 0.65-0.68, and knowing the analysis used TPR, housing quality, EVI, NDWI, and soil wetness - what specific factors likely make these wards so vulnerable to malaria?",
        "evaluation_points": [
            "Links high scores to specific variables",
            "Explains each variable's contribution",
            "Considers regional context"
        ]
    },
    {
        "id": "planning_1", 
        "category": "Strategic Planning",
        "prompt": "The ITN distribution for Adamawa achieved only 58.7% coverage with 2 million nets. If we receive 500,000 additional nets, should we: (1) Focus on the partially covered ward that only got 46% coverage, (2) Extend to uncovered high-risk wards, or (3) Increase coverage in all partially covered areas? What would maximize impact?",
        "evaluation_points": [
            "Analyzes trade-offs",
            "Provides specific recommendation",
            "Considers epidemiological impact"
        ]
    },
    {
        "id": "pattern_1",
        "category": "Pattern Recognition",  
        "prompt": "In North East Nigeria's dry climate, the analysis included water-related variables (NDWI, soil wetness) alongside TPR. This seems counterintuitive for a drought-prone region. How would water scarcity patterns actually relate to malaria risk in Adamawa State?",
        "evaluation_points": [
            "Recognizes paradox",
            "Explains seasonal water dynamics",
            "Links to vector ecology"
        ]
    },
    {
        "id": "action_1",
        "category": "Actionable Recommendations",
        "prompt": "Given that 75 wards in Adamawa are classified as High Risk but only 58.7% have ITN coverage, develop a specific 3-month action plan for the upcoming rainy season (June-September). Include both immediate and preventive measures.",
        "evaluation_points": [
            "Provides timeline",
            "Specifies concrete actions",
            "Considers seasonal factors"
        ]
    }
]

# Test each prompt
results = []
for i, test in enumerate(test_prompts, 1):
    print(f"\n{'='*80}")
    print(f"TEST {i}/{len(test_prompts)}: {test['category']}")
    print("="*80)
    print(f"\nPrompt: {test['prompt'][:200]}...")
    print("\nSending to Arena models...")
    
    response = test_arena_model(test['prompt'], SESSION_ID)
    
    # Parse response
    if 'error' not in response:
        result = {
            "test_id": test['id'],
            "category": test['category'],
            "prompt": test['prompt'],
            "response": response.get('response', response.get('message', '')),
            "models_used": response.get('models', 'unknown')
        }
        
        # Show preview
        response_text = result['response'][:500] if result['response'] else "No response"
        print(f"\nResponse preview: {response_text}...")
        
        # Quick evaluation
        print("\nQuick Evaluation:")
        for point in test['evaluation_points']:
            print(f"  □ {point}")
            
        results.append(result)
    else:
        print(f"\nError: {response['error']}")
        results.append({"test_id": test['id'], "error": response['error']})
    
    # Rate limit
    time.sleep(2)

# Analyze results
print("\n" + "="*80)
print("ANALYSIS SUMMARY")
print("="*80)

success_count = len([r for r in results if 'error' not in r])
print(f"\nTests completed: {success_count}/{len(test_prompts)}")

if success_count > 0:
    print("\nResponse Quality Indicators:")
    
    # Check for key capabilities
    capabilities_found = {
        "Specific variable mentions": 0,
        "Quantitative reasoning": 0,
        "Regional context": 0,
        "Actionable recommendations": 0,
        "Trade-off analysis": 0
    }
    
    for result in results:
        if 'error' in result:
            continue
            
        response = result.get('response', '').lower()
        
        # Check for specific capabilities
        if any(var in response for var in ['tpr', 'housing', 'evi', 'ndwi', 'soil']):
            capabilities_found["Specific variable mentions"] += 1
            
        if any(term in response for term in ['percent', '%', 'coverage', 'score']):
            capabilities_found["Quantitative reasoning"] += 1
            
        if any(term in response for term in ['north east', 'adamawa', 'drought', 'sahel']):
            capabilities_found["Regional context"] += 1
            
        if any(term in response for term in ['should', 'recommend', 'prioritize', 'focus']):
            capabilities_found["Actionable recommendations"] += 1
            
        if any(term in response for term in ['trade-off', 'balance', 'versus', 'instead']):
            capabilities_found["Trade-off analysis"] += 1
    
    print("\nCapabilities Demonstrated:")
    for capability, count in capabilities_found.items():
        percentage = (count / success_count) * 100
        status = "✓" if percentage >= 50 else "○"
        print(f"  {status} {capability}: {count}/{success_count} ({percentage:.0f}%)")

# Save detailed results
output_file = "arena_interpretation_test_results.json"
with open(output_file, 'w') as f:
    json.dump({
        "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "session_id": SESSION_ID,
        "test_count": len(test_prompts),
        "success_count": success_count,
        "results": results
    }, f, indent=2)

print(f"\nDetailed results saved to: {output_file}")

print("\n" + "="*80)
print("PRELIMINARY FINDINGS")
print("="*80)
print("""
Based on the responses, evaluate:

1. INTERPRETATION DEPTH
   - Do models explain WHY (causal reasoning)?
   - Or just restate WHAT (surface level)?

2. PLANNING CAPABILITY  
   - Specific, actionable recommendations?
   - Or generic, vague suggestions?

3. CONTEXTUAL AWARENESS
   - Adapt to North East Nigeria specifics?
   - Or give generic malaria advice?

4. ANALYTICAL REASONING
   - Integrate multiple data points?
   - Or treat variables in isolation?

This reveals if Arena models can truly support epidemiological work.
""")

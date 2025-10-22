#!/usr/bin/env python3
"""
Test Arena models' ability to interpret analysis results and support planning
Beyond simple Q&A - testing real data interpretation and strategic planning
"""

import sys
import os
import json
import pandas as pd

# Setup paths
sys.path.append('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')
os.environ['FLASK_ENV'] = 'production'

# Load the arena system prompt
from app.core.arena_system_prompt import get_compact_arena_prompt

# Session with real Adamawa State analysis data
SESSION_ID = "9000f9df-451d-4dd9-a4d1-2040becdf902"
SESSION_PATH = f"instance/uploads/{SESSION_ID}"

# Load actual analysis data
print("="*80)
print("ARENA MODELS INTERPRETATION & PLANNING CAPABILITY TEST")
print("="*80)
print(f"\nTest Session: {SESSION_ID}")
print("Location: Adamawa State, North East Nigeria")
print("\nAvailable Analysis Data:")
print("-" * 40)

# Load vulnerability rankings
rankings = pd.read_csv(f"{SESSION_PATH}/analysis_vulnerability_rankings.csv")
print(f"✓ Vulnerability rankings for {len(rankings)} wards")
print(f"  - High Risk: {len(rankings[rankings['vulnerability_category'] == 'High Risk'])} wards")
print(f"  - Top 3 highest risk: {', '.join(rankings['WardName'].head(3).tolist())}")

# Load ITN distribution results
with open(f"{SESSION_PATH}/itn_distribution_results.json", 'r') as f:
    itn_results = json.load(f)
print(f"\n✓ ITN Distribution Plan")
print(f"  - Total nets: {itn_results['stats']['total_nets']:,}")
print(f"  - Coverage achieved: {itn_results['stats']['coverage_percent']}%")
print(f"  - Fully covered wards: {itn_results['stats']['fully_covered_wards']}")

# Load variable metadata
with open(f"{SESSION_PATH}/unified_variable_metadata.json", 'r') as f:
    metadata = json.load(f)
print(f"\n✓ Analysis Variables")
print(f"  - Variables used: {', '.join(metadata['selected_variables'])}")
print(f"  - Regional focus: {metadata['zone_metadata']['priority_focus']}")

print("\n" + "="*80)
print("TEST PROMPTS - BEYOND SIMPLE Q&A")
print("="*80)

# Define test categories and prompts
test_cases = [
    {
        "category": "1. DATA INTERPRETATION",
        "prompts": [
            {
                "prompt": "Looking at the Adamawa State analysis results, the top 3 highest risk wards are Gwapopolok (score 0.676), Gamu (0.649), and Bakta (0.632). All are classified as High Risk. What specific factors likely drive their high vulnerability scores given that the analysis included TPR, housing quality, EVI, NDWI, and soil wetness variables?",
                "expected_capabilities": [
                    "Link high scores to specific risk factors",
                    "Explain role of each variable (TPR = disease burden, housing = protection, EVI/NDWI/soil = environmental conditions)",
                    "Consider North East climate context (drought, water scarcity)",
                    "Provide plausible interpretation without seeing raw data"
                ]
            },
            {
                "prompt": "The ITN distribution achieved only 58.7% coverage with 2 million nets for Adamawa State's population of 6.13 million. 125 wards got full coverage but 1 ward only got 46.1% coverage. What does this coverage gap tell us about the resource allocation challenge?",
                "expected_capabilities": [
                    "Calculate coverage shortfall (~1.4 million nets needed for 80% target)",
                    "Explain prioritization trade-offs",
                    "Identify implications of partial coverage",
                    "Suggest resource optimization strategies"
                ]
            }
        ]
    },
    {
        "category": "2. PATTERN RECOGNITION & REASONING",
        "prompts": [
            {
                "prompt": "In this North East Nigeria analysis, the system selected water-related variables (NDWI, soil wetness) alongside TPR and housing quality. Given that North East Nigeria faces drought conditions and water scarcity, how might water stress patterns correlate with malaria risk differently here compared to southern Nigeria?",
                "expected_capabilities": [
                    "Recognize counterintuitive relationship (less water but still malaria risk)",
                    "Explain seasonal water pooling and vector breeding",
                    "Compare to southern Nigeria's year-round moisture",
                    "Connect to regional epidemiology"
                ]
            },
            {
                "prompt": "Looking at the ward rankings, there's a clear gradient from 0.676 (highest) to lower scores. If similar wards cluster geographically, what intervention strategies would you recommend for spatial targeting?",
                "expected_capabilities": [
                    "Suggest cluster-based interventions",
                    "Recommend buffer zones around high-risk areas",
                    "Propose coordinated vector control",
                    "Consider spillover effects"
                ]
            }
        ]
    },
    {
        "category": "3. STRATEGIC PLANNING SUPPORT",
        "prompts": [
            {
                "prompt": "Given that only 58.7% ITN coverage was achieved and 126 wards were prioritized based on composite risk scores, how would you recommend reprioritizing if we received an additional 500,000 nets? Consider both epidemiological impact and equity.",
                "expected_capabilities": [
                    "Calculate coverage improvement (58.7% → ~73%)",
                    "Balance high-risk vs partially covered areas",
                    "Consider equity (rural/urban disparities)",
                    "Propose phased distribution strategy"
                ]
            },
            {
                "prompt": "The analysis shows housing quality as a key variable in Adamawa State. If you had to choose between distributing 1 million ITNs or improving housing in the top 50 high-risk wards, how would you evaluate the trade-offs for malaria control?",
                "expected_capabilities": [
                    "Compare immediate vs long-term impact",
                    "Consider cost-effectiveness",
                    "Evaluate sustainability",
                    "Suggest integrated approach"
                ]
            }
        ]
    },
    {
        "category": "4. ACTIONABLE RECOMMENDATIONS",
        "prompts": [
            {
                "prompt": "Based on the vulnerability rankings showing 19 wards in the highest risk category with scores above 0.55, develop a 3-phase intervention timeline for the next 12 months. Include specific actions for the rainy season (June-September).",
                "expected_capabilities": [
                    "Create time-bound action plan",
                    "Prioritize seasonal interventions",
                    "Allocate resources across phases",
                    "Include monitoring checkpoints"
                ]
            },
            {
                "prompt": "The partially covered ward received only 46.1% ITN coverage. What complementary interventions would you recommend for this ward to compensate for the coverage gap?",
                "expected_capabilities": [
                    "Suggest IRS (indoor residual spraying)",
                    "Recommend larviciding for breeding sites",
                    "Propose community mobilization",
                    "Include case management strengthening"
                ]
            }
        ]
    },
    {
        "category": "5. CONTEXTUAL UNDERSTANDING",
        "prompts": [
            {
                "prompt": "This analysis used climate stress indicators (EVI, NDWI, soil wetness) specific to North East Nigeria's Sudan/Sahel environment. How should the interpretation of these variables differ from their use in tropical rainforest zones?",
                "expected_capabilities": [
                    "Explain regional climate differences",
                    "Adapt variable interpretation",
                    "Consider seasonal variations",
                    "Link to vector ecology"
                ]
            }
        ]
    }
]

print("\nTest Design Summary:")
print("-" * 40)
for i, category in enumerate(test_cases, 1):
    print(f"{i}. {category['category'].split('. ')[1]}: {len(category['prompts'])} prompts")

# Generate the actual test script
print("\n" + "="*80)
print("EVALUATION FRAMEWORK")
print("="*80)

evaluation_criteria = {
    "Level 1: Basic Understanding": [
        "Can identify what the numbers mean",
        "Recognizes high vs low risk",
        "Understands coverage percentages"
    ],
    "Level 2: Analytical Interpretation": [
        "Links variables to outcomes",
        "Explains causal relationships",
        "Identifies patterns and trends"
    ],
    "Level 3: Strategic Planning": [
        "Proposes evidence-based interventions",
        "Considers trade-offs and constraints",
        "Develops phased approaches"
    ],
    "Level 4: Contextual Expertise": [
        "Adapts to regional specifics",
        "Integrates epidemiological knowledge",
        "Provides nuanced recommendations"
    ]
}

for level, criteria in evaluation_criteria.items():
    print(f"\n{level}:")
    for criterion in criteria:
        print(f"  □ {criterion}")

print("\n" + "="*80)
print("SIMULATED TEST WITH COMPACT ARENA PROMPT")
print("="*80)

# Get the arena prompt
arena_prompt = get_compact_arena_prompt()
print(f"Arena prompt loaded: {len(arena_prompt)} characters")

# Simulate with one test case
test_prompt = test_cases[0]['prompts'][0]['prompt']
print(f"\nTest Prompt:\n{test_prompt}")

print("\n" + "-"*40)
print("Expected Model Capabilities:")
for capability in test_cases[0]['prompts'][0]['expected_capabilities']:
    print(f"  • {capability}")

print("\n" + "="*80)
print("KEY QUESTIONS FOR INVESTIGATION:")
print("="*80)
print("""
1. Can models move beyond stating facts to explaining WHY patterns exist?
2. Do they provide actionable recommendations vs generic advice?
3. Can they reason about trade-offs and resource constraints?
4. Do they adapt interpretations to regional context (North East Nigeria)?
5. Can they integrate multiple data points into coherent strategies?

These tests will reveal whether Arena models can truly support epidemiological
analysis and planning, or if they're limited to general Q&A responses.
""")

# Save test data context for models
context_data = {
    "session_id": SESSION_ID,
    "location": "Adamawa State, North East Nigeria",
    "key_findings": {
        "highest_risk_wards": rankings[['WardName', 'median_score']].head(5).to_dict('records'),
        "risk_categories": {
            "high": len(rankings[rankings['vulnerability_category'] == 'High Risk']),
            "medium": len(rankings[rankings['vulnerability_category'] == 'Medium Risk']),
            "low": len(rankings[rankings['vulnerability_category'] == 'Low Risk'])
        },
        "itn_coverage": {
            "achieved": itn_results['stats']['coverage_percent'],
            "nets_distributed": itn_results['stats']['total_nets'],
            "population_covered": itn_results['stats']['covered_population']
        },
        "analysis_variables": metadata['selected_variables']
    }
}

print("\nContext data prepared for model testing:")
print(json.dumps(context_data, indent=2)[:500] + "...")

print("\n" + "="*80)
print("NEXT STEPS:")
print("="*80)
print("""
1. Run these prompts through Arena models (Mistral, Llama, Phi, Gemma, Qwen)
2. Score responses on the 4-level evaluation framework
3. Compare model performance across interpretation vs planning tasks
4. Identify specific strengths and limitations
5. Document which models excel at which types of support

This investigation will determine if Arena models can provide meaningful
epidemiological analysis support beyond simple Q&A.
""")

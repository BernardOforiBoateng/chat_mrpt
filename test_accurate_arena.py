#!/usr/bin/env python3
"""
Test if arena models now provide accurate ChatMRPT information
"""

import requests
import json
import sys
import os

# Get the enhanced prompt
sys.path.append('/home/ec2-user/ChatMRPT')
os.environ['FLASK_ENV'] = 'production'
os.environ['OPENAI_API_KEY'] = 'dummy'

from app.core.arena_system_prompt import get_arena_system_prompt

# Get the prompt
prompt = get_arena_system_prompt()
print(f"System prompt loaded: {len(prompt)} characters")
print("="*70)

# Test questions to verify accuracy
test_cases = [
    {
        "question": "How do I upload data to ChatMRPT?",
        "expected": ["paperclip", "attachment", "icon", "standard upload", "data analysis"],
        "wrong": ["sidebar", "left sidebar", "upload csv button"]
    },
    {
        "question": "What are the two upload methods?",
        "expected": ["standard upload", "data analysis", "tab"],
        "wrong": ["drag and drop"]
    },
    {
        "question": "What happens after I upload data through Data Analysis tab?",
        "expected": ["option", "explore", "tpr", "overview", "1", "2", "3"],
        "wrong": ["automatic analysis"]
    },
    {
        "question": "How do I calculate TPR?",
        "expected": ["data analysis tab", "option 2", "state", "facility", "age group"],
        "wrong": ["tpr button", "automatic"]
    },
    {
        "question": "What's in the sidebar?",
        "expected": ["history", "samples", "recent files", "kano"],
        "wrong": ["upload button", "analysis button"]
    }
]

ollama_url = "http://172.31.45.157:11434/v1/chat/completions"

print("Testing Arena Model Accuracy")
print("="*70)

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test['question']}")
    print("-" * 60)
    
    payload = {
        "model": "mistral:7b",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": test['question']}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(ollama_url, json=payload, timeout=30)
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            answer_lower = answer.lower()
            
            # Check for expected keywords
            found_expected = [kw for kw in test['expected'] if kw.lower() in answer_lower]
            found_wrong = [kw for kw in test['wrong'] if kw.lower() in answer_lower]
            
            print(f"Response preview: {answer[:200]}...")
            
            if found_expected and not found_wrong:
                print(f"✅ ACCURATE - Found: {', '.join(found_expected)}")
            elif found_wrong:
                print(f"❌ INACCURATE - Contains wrong info: {', '.join(found_wrong)}")
            else:
                print(f"⚠️ UNCLEAR - Missing expected keywords")
                print(f"   Expected any of: {', '.join(test['expected'])}")
                
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("Check results above to verify arena models are now accurate.")
print("All responses should mention:")
print("- Paperclip/attachment icon (not sidebar) for upload")
print("- Two tabs: Standard Upload and Data Analysis")
print("- Options 1/2/3 after Data Analysis upload")
print("- TPR workflow through Data Analysis tab")
print("- Sidebar contains History and Samples (not upload buttons)")
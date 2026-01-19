#!/usr/bin/env python3
"""
Test if the compact prompt fixes Arena model responses
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

# Get the prompt that should be sent
prompt = get_arena_system_prompt()
print(f"System prompt loaded: {len(prompt)} characters")
if len(prompt) < 10000:
    print("✅ Prompt is compact (<10k chars)")
else:
    print("⚠️ Prompt is still large")

print("="*70)

# Test questions
test_questions = [
    "What is ChatMRPT?",
    "How do I upload my data?",
    "What's the difference between Composite and PCA analysis?",
    "What do the colors on the map mean?",
    "How do I plan ITN distribution?"
]

# Call Ollama with the same setup as arena_routes.py
ollama_url = "http://172.31.45.157:11434/v1/chat/completions"

for question in test_questions:
    print(f"\nQuestion: {question}")
    print("-" * 60)
    
    payload = {
        "model": "mistral:7b",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(ollama_url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            
            # Show first 300 chars of response
            print(f"Response: {answer[:300]}...")
            
            # Check accuracy
            if question == "What is ChatMRPT?":
                keywords = ['malaria', 'risk', 'prioritization', 'tool', 'nigeria']
                accurate = any(kw.lower() in answer.lower() for kw in keywords)
                if accurate:
                    print("✅ CORRECT - Mentions malaria risk tool")
                else:
                    print("❌ WRONG - Doesn't describe ChatMRPT correctly")
            
            elif "upload" in question.lower():
                if "csv" in answer.lower() and "sidebar" in answer.lower():
                    print("✅ CORRECT - Mentions CSV upload in sidebar")
                else:
                    print("⚠️ Partial - Check if mentions upload process")
                    
            elif "composite" in question.lower() and "pca" in question.lower():
                if "composite" in answer.lower() and "pca" in answer.lower():
                    print("✅ CORRECT - Explains both analysis types")
                else:
                    print("⚠️ Partial - Check explanation quality")
                    
            elif "colors" in question.lower():
                if "red" in answer.lower() and "risk" in answer.lower():
                    print("✅ CORRECT - Explains risk color coding")
                else:
                    print("⚠️ Partial - Check color explanation")
                    
            elif "itn" in question.lower():
                if "net" in answer.lower() or "itn" in answer.lower():
                    print("✅ CORRECT - Discusses ITN distribution")
                else:
                    print("⚠️ Partial - Check ITN planning explanation")
                    
        else:
            print(f"Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Error calling Ollama: {e}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("If models are now giving accurate answers about ChatMRPT,")
print("the compact prompt fix is working!")
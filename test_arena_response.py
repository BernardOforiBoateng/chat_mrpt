#!/usr/bin/env python3
"""
Test what Arena models actually respond with for 'What is ChatMRPT?'
"""

import requests
import sys
import os

sys.path.append('/home/ec2-user/ChatMRPT')
os.environ['FLASK_ENV'] = 'production'
os.environ['OPENAI_API_KEY'] = 'dummy'

from app.core.arena_system_prompt import get_arena_system_prompt

# Get the arena prompt
prompt = get_arena_system_prompt()

# Test with Mistral
ollama_url = "http://172.31.45.157:11434/v1/chat/completions"

payload = {
    "model": "mistral:7b",
    "messages": [
        {"role": "system", "content": prompt},
        {"role": "user", "content": "What is ChatMRPT?"}
    ],
    "max_tokens": 500
}

print("Testing: 'What is ChatMRPT?'")
print("="*60)

response = requests.post(ollama_url, json=payload, timeout=30)
if response.status_code == 200:
    answer = response.json()['choices'][0]['message']['content']
    print("Response:")
    print(answer)
    print("\n" + "="*60)
    
    # Check for tool need indicators from the code
    tool_need_indicators = [
        "i need to see", "upload", "provide the", "i would need",
        "cannot analyze without", "don't have access", "no data available",
        "please share", "i require", "unable to access", "can't see your"
    ]
    
    answer_lower = answer.lower()
    found_indicators = [ind for ind in tool_need_indicators if ind in answer_lower]
    
    if found_indicators:
        print("\n❌ PROBLEM FOUND!")
        print("Arena model is asking for uploads/data when it shouldn't!")
        print(f"Problematic phrases found: {found_indicators}")
        print("\nThis would trigger fallback to GPT-4o instead of Arena!")
    else:
        print("\n✅ No problematic phrases found")
        print("This response should stay in Arena mode")
else:
    print(f"Error: {response.status_code}")
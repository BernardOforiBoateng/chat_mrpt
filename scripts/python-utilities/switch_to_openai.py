#!/usr/bin/env python3
"""
Emergency switch from VLLM/Llama to OpenAI for proper function calling support.
This fixes the issue where risk analysis won't run after TPR transition.
"""

import os

# Read the current llm_manager.py
llm_manager_path = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/core/llm_manager.py'

with open(llm_manager_path, 'r') as f:
    content = f.read()

# Replace VLLM configuration with OpenAI
replacements = [
    # Change default model from Llama to GPT-4o
    ('model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"', 
     'model: str = "gpt-4o"'),
    
    # Use real OpenAI API key instead of dummy
    ('self.api_key = "dummy"  # VLLM doesn\'t need a real API key',
     'self.api_key = api_key or self._get_api_key_from_config()'),
    
    # Comment out VLLM client initialization
    ('        try:\n            self.client = openai.OpenAI(\n                api_key="dummy",\n                base_url=f"{vllm_base}/v1"\n            )\n            logger.info(f"🧠 Pure LLM Manager initialized with {self.model} at {vllm_base}")\n        except Exception as e:\n            logger.error(f"Error initializing VLLM client: {str(e)}")\n            self.client = None',
     '''        try:
            if self.api_key:
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info(f"🧠 Pure LLM Manager initialized with {self.model} (OpenAI)")
            else:
                logger.warning("No OpenAI API key found - will try to get from config later")
                self.client = None
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            self.client = None'''),
]

# Apply replacements
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f"✅ Replaced: {old[:50]}...")
    else:
        print(f"⚠️ Not found: {old[:50]}...")

# Write the modified content back
with open(llm_manager_path, 'w') as f:
    f.write(content)

print("\n✅ Switched from VLLM/Llama to OpenAI GPT-4o for proper function calling support")
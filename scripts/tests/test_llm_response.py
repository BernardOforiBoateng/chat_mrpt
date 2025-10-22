#!/usr/bin/env python3
"""
Test script to see what the LLM is actually generating
Run this on staging to diagnose the issue
"""

import sys
import os
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

from app import create_app
from app.core.llm_manager import LLMManager

def test_llm_response():
    """Test what the LLM actually generates."""
    app = create_app()
    
    with app.app_context():
        # Initialize LLM
        llm_manager = LLMManager()
        
        # Test prompts
        prompts = [
            # Simple code generation
            "Generate Python code only: print('Hello World')",
            
            # Data analysis prompt
            """You are a Python code executor. Generate ONLY executable Python code.
# Task: Analyze data
# Available variables: df (a pandas DataFrame)

Generate Python code that:
print("Analysis starting")
print(df.shape)
""",
            
            # Direct instruction
            "print(1+1)",
        ]
        
        print("=" * 60)
        print("Testing LLM Response Generation")
        print("=" * 60)
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n--- Test {i} ---")
            print(f"Prompt: {prompt[:100]}...")
            
            try:
                response = llm_manager.generate_response(
                    prompt, 
                    max_tokens=500,
                    temperature=0.1
                )
                
                print(f"Response type: {type(response)}")
                print(f"Response length: {len(response)}")
                print("Response (first 300 chars):")
                print(response[:300])
                
                # Check if it's code or text
                if "```" in response:
                    print("WARNING: Contains markdown code blocks!")
                if "**" in response:
                    print("WARNING: Contains markdown bold!")
                if not any(kw in response for kw in ['print', 'import', '=', 'def', 'class']):
                    print("WARNING: Doesn't look like Python code!")
                    
            except Exception as e:
                print(f"ERROR: {e}")
        
        print("\n" + "=" * 60)
        print("Test complete")

if __name__ == "__main__":
    test_llm_response()
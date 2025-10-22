#!/usr/bin/env python3
"""Test that the streaming fix works with vLLM backend."""

import os
import sys

# Set environment for vLLM
os.environ['USE_VLLM'] = 'true'
os.environ['USE_OLLAMA'] = 'false'
os.environ['VLLM_BASE_URL'] = 'http://localhost:8000'  # Adjust if needed
os.environ['VLLM_MODEL'] = 'Qwen/Qwen3-8B'

print("\n" + "="*60)
print("TESTING TPR STREAMING FIX")
print("="*60)

# Test 1: Import and create the container
print("\n1. Testing service container with LLMManagerWrapper...")
try:
    from app.services.container import ServiceContainer
    from flask import Flask
    
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'instance/uploads'
    app.config['INTERACTIONS_DB_FILE'] = 'instance/interactions.db'
    
    container = ServiceContainer(app)
    llm_manager = container.get('llm_manager')
    
    if llm_manager:
        print("   ✅ LLM Manager created successfully")
        print(f"   ✅ Backend: {llm_manager.adapter.backend}")
        print(f"   ✅ Model: {llm_manager.adapter.model}")
    else:
        print("   ❌ LLM Manager is None - check vLLM connection")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Check if streaming method exists
print("\n2. Testing generate_with_functions_streaming method...")
try:
    if llm_manager and hasattr(llm_manager, 'generate_with_functions_streaming'):
        print("   ✅ generate_with_functions_streaming method exists")
        
        # Test the method
        messages = [{"role": "user", "content": "What areas have high malaria risk?"}]
        system_prompt = "You are a malaria expert analyzing TPR data."
        functions = []
        
        chunks = []
        for chunk in llm_manager.generate_with_functions_streaming(
            messages=messages,
            system_prompt=system_prompt,
            functions=functions,
            temperature=0.7
        ):
            chunks.append(chunk)
            
        print(f"   ✅ Streaming returned {len(chunks)} chunks")
        if chunks:
            print(f"   ✅ Sample chunk: {chunks[0]}")
    else:
        print("   ❌ generate_with_functions_streaming method NOT found")
        
except Exception as e:
    print(f"   ❌ Error testing streaming: {e}")

# Test 3: Test TPR file encoding fix
print("\n3. Testing TPR file encoding fix...")
try:
    from app.tpr_module.data.nmep_parser import NMEPParser
    
    parser = NMEPParser()
    print("   ✅ NMEPParser imported successfully")
    
    # Check if the parse_file method has our encoding fix
    import inspect
    source = inspect.getsource(parser.parse_file)
    if 'openpyxl' in source:
        print("   ✅ Encoding fix with openpyxl is present")
    else:
        print("   ⚠️ Encoding fix might not be applied")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
print("\nNOTE: If vLLM is not running locally, the streaming test will fail.")
print("The important thing is that the method exists and doesn't crash.")
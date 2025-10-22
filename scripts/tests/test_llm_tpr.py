#!/usr/bin/env python3
"""
Test the LLM-first TPR implementation.
"""

import os
import sys

# Enable LLM mode
os.environ['USE_LLM_TPR'] = 'true'

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all LLM components import correctly."""
    print("Testing LLM-first imports...")
    
    try:
        from app.tpr_module.conversation import TPRConversation
        print("✅ TPRConversation imported")
    except ImportError as e:
        print(f"❌ Failed to import TPRConversation: {e}")
        return False
    
    try:
        from app.tpr_module.sandbox import CodeSandbox, create_tpr_sandbox
        print("✅ Sandbox imported")
    except ImportError as e:
        print(f"❌ Failed to import sandbox: {e}")
        return False
    
    try:
        from app.tpr_module.integration.llm_tpr_handler import LLMTPRHandler
        print("✅ LLMTPRHandler imported")
    except ImportError as e:
        print(f"❌ Failed to import LLMTPRHandler: {e}")
        return False
    
    try:
        from app.tpr_module.prompts import (
            TPR_CALCULATION_PROMPT,
            WARD_MATCHING_PROMPT,
            ZONE_VARIABLE_EXTRACTION_PROMPT
        )
        print("✅ Prompts imported")
    except ImportError as e:
        print(f"❌ Failed to import prompts: {e}")
        return False
    
    return True

def test_sandbox():
    """Test the code sandbox."""
    print("\nTesting code sandbox...")
    
    try:
        from app.tpr_module.sandbox import create_tpr_sandbox
        
        sandbox = create_tpr_sandbox()
        
        # Test simple code execution (no imports allowed in sandbox)
        code = """
result = {'success': True, 'value': 42}
"""
        result = sandbox.execute(code, {})
        
        if result['success']:
            # Check if result was captured correctly
            if 'result' in result['output'] and result['output']['result'].get('value') == 42:
                print("✅ Sandbox execution works")
                return True
            else:
                print(f"❌ Sandbox output unexpected: {result['output']}")
                return False
        else:
            print(f"❌ Sandbox execution failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Sandbox test failed: {e}")
        return False

def test_prompts():
    """Test that prompts have correct content."""
    print("\nTesting prompt content...")
    
    from app.tpr_module.prompts import TPR_CALCULATION_PROMPT
    
    # Check for correct TPR formula
    if 'max(RDT_Positive, Microscopy_Positive)' in TPR_CALCULATION_PROMPT:
        print("✅ TPR formula is correct (uses max, not sum)")
    else:
        print("❌ TPR formula is incorrect")
        return False
    
    # Check for zone variables
    from app.tpr_module.prompts import ZONE_VARIABLE_EXTRACTION_PROMPT
    if 'North_East' in ZONE_VARIABLE_EXTRACTION_PROMPT and 'housing_quality' in ZONE_VARIABLE_EXTRACTION_PROMPT:
        print("✅ Zone variables are correct")
    else:
        print("❌ Zone variables are incorrect")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("LLM-First TPR Implementation Test")
    print("=" * 60)
    
    print(f"\nEnvironment: USE_LLM_TPR = {os.environ.get('USE_LLM_TPR', 'not set')}")
    
    success = True
    success = test_imports() and success
    success = test_sandbox() and success
    success = test_prompts() and success
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        print("\nTo use in production:")
        print("1. Set environment variable: export USE_LLM_TPR=true")
        print("2. Start Flask app: python run.py")
        print("3. Upload TPR file")
        print("4. The LLM will dynamically generate analysis code")
    else:
        print("❌ Some tests failed")
    print("=" * 60)

if __name__ == "__main__":
    main()
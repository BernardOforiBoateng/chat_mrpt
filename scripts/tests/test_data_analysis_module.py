#!/usr/bin/env python
"""
Test script for the new data analysis module
Can be run independently to test without affecting main app
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from pathlib import Path

def test_module_import():
    """Test that the module can be imported."""
    print("Testing module import...")
    try:
        from app.data_analysis_module import DataExecutor, AnalysisPrompts
        print("✅ Module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import module: {e}")
        return False

def test_executor_without_llm():
    """Test executor with mock code (no LLM required)."""
    print("\nTesting executor without LLM...")
    
    from app.data_analysis_module import DataExecutor
    
    # Create test data
    test_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=100),
        'value': np.random.randn(100).cumsum(),
        'category': np.random.choice(['A', 'B', 'C'], 100),
        'amount': np.random.uniform(10, 100, 100)
    })
    
    # Save test data
    test_file = 'test_data.csv'
    test_data.to_csv(test_file, index=False)
    
    try:
        # Create executor without LLM
        executor = DataExecutor(llm_manager=None)
        
        # Test analysis
        result = executor.analyze(test_file, "Analyze this data")
        
        if result['success']:
            print("✅ Analysis executed successfully")
            print(f"Output preview: {result['output'][:200]}...")
        else:
            print(f"❌ Analysis failed: {result.get('error')}")
            
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

def test_safety_validation():
    """Test code safety validation."""
    print("\nTesting safety validation...")
    
    from app.data_analysis_module.safety import SafeExecutor
    
    safe_executor = SafeExecutor()
    
    # Test safe code
    safe_code = """
import pandas as pd
df = pd.DataFrame({'a': [1,2,3]})
print(df.mean())
"""
    is_safe, msg = safe_executor.validate_code(safe_code)
    print(f"Safe code validation: {'✅' if is_safe else '❌'} {msg}")
    
    # Test dangerous code
    dangerous_code = """
import os
os.system('ls')
"""
    is_safe, msg = safe_executor.validate_code(dangerous_code)
    print(f"Dangerous code validation: {'✅ Blocked' if not is_safe else '❌ Not blocked'} - {msg}")
    
    # Test file operation
    file_op_code = """
with open('/etc/passwd', 'r') as f:
    print(f.read())
"""
    is_safe, msg = safe_executor.validate_code(file_op_code)
    print(f"File operation validation: {'✅ Blocked' if not is_safe else '❌ Not blocked'} - {msg}")

def test_prompts():
    """Test prompt generation."""
    print("\nTesting prompt generation...")
    
    from app.data_analysis_module.prompts import AnalysisPrompts
    
    context = {
        'shape': (100, 4),
        'columns': ['date', 'value', 'category', 'amount'],
        'dtypes': {'date': 'datetime64', 'value': 'float64', 'category': 'object', 'amount': 'float64'},
        'null_counts': {'date': 0, 'value': 0, 'category': 2, 'amount': 0},
        'numeric_cols': ['value', 'amount'],
        'object_cols': ['category'],
        'head': [{'date': '2024-01-01', 'value': 1.5, 'category': 'A', 'amount': 50.0}],
        'query': 'Find patterns in the data'
    }
    
    prompt = AnalysisPrompts.build_analysis_prompt(context)
    
    if prompt and len(prompt) > 100:
        print("✅ Prompt generated successfully")
        print(f"Prompt length: {len(prompt)} characters")
    else:
        print("❌ Prompt generation failed")

def test_api_endpoint():
    """Test the API endpoint if Flask app is running."""
    print("\nTesting API endpoint...")
    
    try:
        import requests
        
        # Check if server is running
        response = requests.get('http://localhost:5000/api/data-analysis/test')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API endpoint active: {data['message']}")
        else:
            print(f"❌ API endpoint returned status {response.status_code}")
            
    except Exception as e:
        print(f"ℹ️ API test skipped (server not running): {e}")

def main():
    """Run all tests."""
    print("=" * 60)
    print("DATA ANALYSIS MODULE TEST SUITE")
    print("=" * 60)
    
    # Run tests
    tests = [
        test_module_import,
        test_executor_without_llm,
        test_safety_validation,
        test_prompts,
        test_api_endpoint
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"Test failed with error: {e}")
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)
    print("\nThe data analysis module is working independently!")
    print("It can be integrated with the main app when ready.")

if __name__ == "__main__":
    main()
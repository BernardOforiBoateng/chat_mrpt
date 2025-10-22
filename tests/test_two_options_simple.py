#!/usr/bin/env python
"""
Simple test for Data Analysis V3 two-option response
"""

import sys
sys.path.insert(0, '.')

import os
import shutil
import pandas as pd
import asyncio
import logging

# Set logging to WARNING to reduce noise
logging.basicConfig(level=logging.WARNING)

async def test_two_options():
    """Test that Data Analysis V3 shows exactly TWO options."""
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    # Setup test session
    session_id = 'test_two_options_simple'
    upload_dir = f'instance/uploads/{session_id}'
    
    # Cleanup and create directory
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create test CSV
    df = pd.DataFrame({
        'wardname': ['Ikeja', 'Surulere', 'Yaba', 'Victoria Island', 'Lekki'],
        'healthfacility': ['General Hospital Ikeja', 'Surulere Health Center', 
                          'Yaba Clinic', 'Victoria Medical Center', 'Lekki Primary Care'],
        'total_tested': [250, 180, 320, 150, 290],
        'confirmed_cases': [45, 28, 62, 18, 51]
    })
    df.to_csv(f'{upload_dir}/test_data.csv', index=False)
    
    print("=" * 60)
    print("Testing Data Analysis V3 Two-Option Response")
    print("=" * 60)
    
    try:
        # Create agent and test
        agent = DataAnalysisAgent(session_id)
        
        # Send initial upload message
        print("\n📤 Sending: 'Show me what's in the uploaded data'")
        result = await agent.analyze("Show me what's in the uploaded data")
        
        # Check result
        success = result.get('success', False)
        message = result.get('message', '')
        
        print(f"\n✅ Success: {success}")
        
        if success:
            print("\n📋 Response:")
            print("-" * 40)
            print(message[:800] + "..." if len(message) > 800 else message)
            print("-" * 40)
            
            # Validate options
            print("\n🔍 Validation:")
            
            # Check for Option 1
            has_option_1 = any(x in message for x in ['Option 1', '1.', 'Guided TPR Analysis'])
            print(f"  ✅ Has Option 1 (TPR): {has_option_1}")
            
            # Check for Option 2  
            has_option_2 = any(x in message for x in ['Option 2', '2.', 'Flexible Data Exploration'])
            print(f"  ✅ Has Option 2 (Exploration): {has_option_2}")
            
            # Check NO Option 3 or 4
            has_option_3 = 'Option 3' in message or ('3.' in message and 'Option' in message)
            has_option_4 = 'Option 4' in message or ('4.' in message and 'Option' in message)
            print(f"  ✅ No Option 3: {not has_option_3}")
            print(f"  ✅ No Option 4: {not has_option_4}")
            
            # Check for key terms
            has_tpr = 'TPR' in message or 'Test Positivity Rate' in message
            has_risk = 'risk' in message.lower() or 'assessment' in message.lower()
            print(f"  ✅ Mentions TPR: {has_tpr}")
            print(f"  ✅ Mentions risk assessment: {has_risk}")
            
            # Final verdict
            if has_option_1 and has_option_2 and not has_option_3 and not has_option_4:
                print("\n🎉 TEST PASSED: Two options displayed correctly!")
                return True
            else:
                print("\n❌ TEST FAILED: Options not displayed correctly")
                return False
        else:
            print(f"\n❌ Analysis failed: {message}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)


if __name__ == "__main__":
    # Run test with timeout
    try:
        success = asyncio.run(asyncio.wait_for(test_two_options(), timeout=15))
        exit(0 if success else 1)
    except asyncio.TimeoutError:
        print("\n❌ TEST TIMEOUT: Test took too long (>15 seconds)")
        exit(1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        exit(1)
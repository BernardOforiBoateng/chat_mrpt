#!/usr/bin/env python3
"""
Test that the model can answer general malaria questions without asking for data uploads.
"""

import requests
import json
import time

def test_general_knowledge():
    """Test general knowledge responses."""
    
    print("=" * 60)
    print("Testing General Knowledge Responses")
    print("=" * 60)
    
    # Test questions that should NOT require data uploads
    test_questions = [
        "According to WHO, what are the countries most affected by malaria?",
        "How many people die from malaria each year globally?",
        "What is the economic impact of malaria in Africa?",
        "Tell me about malaria prevention strategies",
        "What are the symptoms of severe malaria?"
    ]
    
    base_url = "http://127.0.0.1:5000"
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*50}")
        print(f"Test {i}: {question}")
        print("-" * 50)
        
        try:
            response = requests.post(
                f"{base_url}/send_message",
                json={"message": question},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('response', data.get('message', ''))
                
                # Check if model is asking for data upload
                if any(phrase in answer.lower() for phrase in [
                    "upload", "please upload", "need to access", "dataset", 
                    "could you please upload", "once the data is uploaded"
                ]):
                    print("❌ FAIL: Model asked for data upload")
                    print(f"Response: {answer[:200]}...")
                else:
                    print("✅ PASS: Model answered without requiring data")
                    print(f"Response preview: {answer[:300]}...")
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(1)  # Rate limiting
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    print("\nExpected Results:")
    print("✅ All questions should be answered with WHO/general knowledge")
    print("✅ No requests for data uploads")
    print("✅ Specific statistics and information provided")

if __name__ == "__main__":
    test_general_knowledge()
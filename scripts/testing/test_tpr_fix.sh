#!/bin/bash

echo "=========================================="
echo "Testing TPR to Risk Analysis Transition"
echo "=========================================="

# Create and run test on AWS server
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'cat > /tmp/test_tpr_fix.py << '\''EOF'\''
import requests
import json
import time

SESSION_ID = f"test_fix_{int(time.time())}"
BASE_URL = "http://localhost:8000"

print(f"Testing session: {SESSION_ID}")
print("-" * 50)

try:
    # Create test data
    test_data = """ward,state,month,year,u5_positive,o5_positive,pw_positive,u5_tested,o5_tested,pw_tested,facility_level
Ward A,Adamawa,Jan,2023,150,200,50,1000,1200,300,primary
Ward B,Adamawa,Jan,2023,280,350,90,1400,1500,400,primary
Ward C,Adamawa,Jan,2023,120,140,30,900,950,250,primary"""
    
    with open("/tmp/test_data.csv", "w") as f:
        f.write(test_data)
    
    # 1. Upload data
    print("1. Uploading data...")
    with open("/tmp/test_data.csv", "rb") as f:
        files = {"files": ("test.csv", f, "text/csv")}
        response = requests.post(f"{BASE_URL}/api/data-analysis/upload", 
                                files=files, 
                                data={"session_id": SESSION_ID})
    
    if response.status_code != 200:
        print(f"   ERROR: Upload failed: {response.text}")
        exit(1)
    
    session_id = response.json().get("session_id", SESSION_ID)
    print(f"   ✓ Uploaded, session: {session_id}")
    
    # 2. Trigger data analysis
    print("2. Starting data analysis...")
    response = requests.post(f"{BASE_URL}/api/v1/data-analysis/chat",
                            json={"message": "__DATA_UPLOADED__", "session_id": session_id})
    print("   ✓ Data analysis triggered")
    
    # 3. Start TPR
    print("3. Starting TPR workflow...")
    response = requests.post(f"{BASE_URL}/api/v1/data-analysis/chat",
                            json={"message": "2", "session_id": session_id})
    print(f"   ✓ TPR started")
    
    # 4. Select facility
    print("4. Selecting facility...")
    response = requests.post(f"{BASE_URL}/api/v1/data-analysis/chat",
                            json={"message": "1", "session_id": session_id})
    print("   ✓ Facility selected")
    
    # 5. Select age
    print("5. Selecting age group...")
    response = requests.post(f"{BASE_URL}/api/v1/data-analysis/chat",
                            json={"message": "1", "session_id": session_id})
    stage = response.json().get("stage", "")
    print(f"   ✓ Age selected, stage: {stage}")
    
    time.sleep(2)
    
    # 6. THE CRITICAL TEST
    print("\n6. CRITICAL TEST: Sending '\''yes'\''...")
    response = requests.post(f"{BASE_URL}/api/v1/data-analysis/chat",
                            json={"message": "yes", "session_id": session_id})
    
    result = response.json()
    
    # Analyze response
    print("\n" + "="*50)
    print("RESPONSE ANALYSIS:")
    print("="*50)
    
    exit_mode = result.get("exit_data_analysis_mode")
    message = result.get("message", "")
    redirect = result.get("redirect_message")
    
    print(f"exit_data_analysis_mode: {exit_mode}")
    print(f"redirect_message: {redirect}")
    print(f"Has risk menu: {'\''risk analysis'\'' in message.lower()}")
    
    if message:
        print(f"\nMessage preview: {message[:150]}...")
    
    # Success check
    success = (exit_mode == True and "risk analysis" in message.lower())
    
    print("\n" + "="*50)
    if success:
        print("✅✅✅ TEST PASSED! Transition works correctly!")
    else:
        print("❌❌❌ TEST FAILED!")
        print("\nFull response:")
        print(json.dumps(result, indent=2))
    print("="*50)
    
    exit(0 if success else 1)
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF
cd /home/ec2-user/ChatMRPT && source /home/ec2-user/chatmrpt_env/bin/activate && python /tmp/test_tpr_fix.py
'

RESULT=$?
echo ""
if [ $RESULT -eq 0 ]; then
    echo "✅ TEST SUITE PASSED - Fix is working!"
else
    echo "❌ TEST SUITE FAILED - Fix did not work"
fi
exit $RESULT
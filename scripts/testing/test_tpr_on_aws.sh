#!/bin/bash

# Test TPR transition directly on AWS server
echo "=========================================="
echo "TPR Transition Test on AWS Production"
echo "=========================================="

# Use the first production instance
SERVER_IP="3.21.167.170"
KEY_PATH="/tmp/chatmrpt-key2.pem"

echo "Testing on server: $SERVER_IP"

# Create test script on server
ssh -i $KEY_PATH ec2-user@$SERVER_IP 'cat > /tmp/test_tpr.py << '\''EOF'\''
import requests
import json
import time
import sys

SESSION_ID = f"test_aws_{int(time.time())}"
BASE_URL = "http://localhost:5000"

print(f"Testing with session: {SESSION_ID}")

try:
    # Step 1: Create test data file
    print("\n1. Creating test data...")
    test_data = """ward,state,month,year,u5_positive,o5_positive,pw_positive,u5_tested,o5_tested,pw_tested,population,facility_level
    Ward A,Adamawa,January,2023,150,200,50,1000,1200,300,12500,primary
    Ward B,Adamawa,January,2023,280,350,90,1400,1500,400,28000,primary
    Ward C,Adamawa,January,2023,120,140,30,900,950,250,9500,primary"""
    
    with open("/tmp/test_data.csv", "w") as f:
        f.write(test_data)
    
    # Step 2: Upload data
    print("2. Uploading data...")
    with open("/tmp/test_data.csv", "rb") as f:
        files = {"files": ("test_data.csv", f, "text/csv")}
        data = {"session_id": SESSION_ID}
        response = requests.post(f"{BASE_URL}/api/data-analysis/upload", files=files, data=data)
    
    if response.status_code != 200:
        print(f"   ERROR: Upload failed: {response.status_code}")
        sys.exit(1)
    
    result = response.json()
    session_id = result.get("session_id", SESSION_ID)
    print(f"   SUCCESS: Data uploaded, session: {session_id}")
    
    # Step 3: Trigger data analysis
    print("3. Triggering data analysis...")
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={"message": "__DATA_UPLOADED__", "session_id": session_id}
    )
    print("   Data analysis triggered")
    
    # Step 4: Start TPR
    print("4. Starting TPR workflow...")
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={"message": "2", "session_id": session_id}
    )
    result = response.json()
    print(f"   TPR started, stage: {result.get('\''stage'\'', '\''unknown'\'')}")
    
    # Step 5: Select facility
    print("5. Selecting facility level...")
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={"message": "1", "session_id": session_id}
    )
    print("   Facility selected")
    
    # Step 6: Select age group
    print("6. Selecting age group...")
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={"message": "1", "session_id": session_id}
    )
    result = response.json()
    print(f"   Age group selected, stage: {result.get('\''stage'\'', '\''unknown'\'')}")
    
    # Wait for TPR to complete
    time.sleep(2)
    
    # Step 7: THE CRITICAL TEST - Send yes
    print("\n7. CRITICAL TEST: Sending '\''yes'\'' to transition...")
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={"message": "yes", "session_id": session_id}
    )
    
    result = response.json()
    
    # Check results
    print("\n" + "="*50)
    print("TRANSITION RESPONSE ANALYSIS:")
    print("="*50)
    
    exit_mode = result.get("exit_data_analysis_mode")
    trigger = result.get("trigger_analysis")
    has_message = bool(result.get("message"))
    message = result.get("message", "")
    
    print(f"exit_data_analysis_mode: {exit_mode}")
    print(f"trigger_analysis: {trigger}")
    print(f"has_message: {has_message}")
    print(f"redirect_message: {result.get('\''redirect_message'\'')}")
    
    if "risk analysis" in message.lower() or "what would you like" in message.lower():
        print("\n✓ Risk analysis menu found in message!")
    else:
        print("\n✗ Risk analysis menu NOT found")
    
    print(f"\nMessage preview: {message[:200]}...")
    
    # Check success
    success = exit_mode or trigger or "risk analysis" in message.lower()
    
    print("\n" + "="*50)
    if success:
        print("✓✓✓ TEST PASSED! Transition is working!")
    else:
        print("✗✗✗ TEST FAILED! Transition did not occur")
    print("="*50)
    
    sys.exit(0 if success else 1)
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF'

echo ""
echo "Running test on AWS server..."
echo "=========================================="

# Run the test
ssh -i $KEY_PATH ec2-user@$SERVER_IP 'cd /home/ec2-user/ChatMRPT && source chatmrpt_env/bin/activate && python /tmp/test_tpr.py'

TEST_RESULT=$?

echo ""
echo "=========================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "✓ TEST SUITE PASSED"
else
    echo "✗ TEST SUITE FAILED"
fi
echo "=========================================="

exit $TEST_RESULT
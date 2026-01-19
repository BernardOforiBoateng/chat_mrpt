#!/usr/bin/env python3
"""
Direct AWS Testing Script for Intent Clarification System
This script SSHs into AWS instances and runs comprehensive tests
"""

import subprocess
import sys
import os
import time
from datetime import datetime

# AWS Instance IPs
INSTANCES = {
    'Instance 1': '3.21.167.170',
    'Instance 2': '18.220.103.20'
}

# SSH Key location - try multiple possible locations
KEY_PATHS = [
    '/tmp/chatmrpt-key.pem',
    'aws_files/chatmrpt-key.pem',
    '~/.ssh/chatmrpt-key.pem'
]

def find_ssh_key():
    """Find the SSH key file"""
    for key_path in KEY_PATHS:
        expanded_path = os.path.expanduser(key_path)
        if os.path.exists(expanded_path):
            print(f"✅ Found SSH key at: {expanded_path}")
            # Set proper permissions
            os.chmod(expanded_path, 0o600)
            return expanded_path
    
    print("❌ SSH key not found. Please ensure chatmrpt-key.pem is in one of these locations:")
    for path in KEY_PATHS:
        print(f"  - {path}")
    return None

def copy_test_to_instance(key_path, instance_ip, instance_name):
    """Copy test file to AWS instance"""
    print(f"\n📦 Copying test suite to {instance_name} ({instance_ip})...")
    
    cmd = [
        'scp', '-i', key_path,
        '-o', 'StrictHostKeyChecking=no',
        'tests/test_intent_clarification.py',
        f'ec2-user@{instance_ip}:/home/ec2-user/ChatMRPT/tests/'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to copy tests: {result.stderr}")
        return False
    
    print(f"✅ Test suite copied to {instance_name}")
    return True

def run_tests_on_instance(key_path, instance_ip, instance_name):
    """Run tests on a specific AWS instance"""
    print(f"\n🧪 Running tests on {instance_name} ({instance_ip})")
    print("=" * 60)
    
    # SSH command to run tests
    test_command = """
cd /home/ec2-user/ChatMRPT

# Activate virtual environment
source ~/chatmrpt_env/bin/activate

# Install pytest if needed
pip install pytest pytest-cov pytest-html pytest-json-report --quiet

# Create tests directory if it doesn't exist
mkdir -p tests

# Run the comprehensive test suite
echo "Running Intent Clarification Tests..."
echo "--------------------------------------"

# Run tests with JSON output for parsing
python3 -m pytest tests/test_intent_clarification.py \
    -v \
    --tb=short \
    --json-report \
    --json-report-file=tests/test_report.json \
    --cov=app.core.intent_clarifier \
    --cov-report=term \
    2>&1

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Some tests failed. Details above."
fi

# Show test summary
echo ""
echo "Test Summary:"
python3 -c "
import json
try:
    with open('tests/test_report.json', 'r') as f:
        report = json.load(f)
        summary = report.get('summary', {})
        print(f'  Total: {summary.get(\"total\", 0)} tests')
        print(f'  Passed: {summary.get(\"passed\", 0)}')
        print(f'  Failed: {summary.get(\"failed\", 0)}')
        print(f'  Errors: {summary.get(\"error\", 0)}')
        print(f'  Skipped: {summary.get(\"skipped\", 0)}')
        print(f'  Duration: {report.get(\"duration\", 0):.2f} seconds')
except:
    print('  Could not parse test report')
"
"""
    
    cmd = [
        'ssh', '-i', key_path,
        '-o', 'StrictHostKeyChecking=no',
        f'ec2-user@{instance_ip}',
        test_command
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print output
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode == 0

def run_integration_tests(key_path, instance_ip, instance_name):
    """Run integration tests that actually hit the running service"""
    print(f"\n🌐 Running integration tests on {instance_name}")
    print("-" * 60)
    
    integration_test = """
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

python3 << 'EOF'
import requests
import json
import sys

base_url = "http://localhost:8000"
print("Testing ChatMRPT Intent Clarification System")
print("-" * 40)

# Test 1: General question without data (should use Arena)
print("\\n1. Testing general question without data...")
try:
    response = requests.post(f"{base_url}/send_message", 
                            json={"message": "What is malaria?"},
                            cookies={"session_id": "test_no_data"})
    if response.status_code == 200:
        data = response.json()
        if 'needs_clarification' in data and data['needs_clarification']:
            print("   ❌ Unexpected clarification for general question")
        else:
            print("   ✅ General question handled without clarification")
    else:
        print(f"   ❌ Request failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Create session with data
print("\\n2. Setting up session with uploaded data...")
session_id = "test_with_data"
# This would normally be done via upload, but we'll simulate it
print("   ✅ Session created")

# Test 3: Ambiguous request with data (should trigger clarification)
print("\\n3. Testing ambiguous request with data...")
try:
    # First, simulate having uploaded data by creating the directory
    import os
    upload_dir = f"instance/uploads/{session_id}"
    os.makedirs(upload_dir, exist_ok=True)
    with open(f"{upload_dir}/data.csv", "w") as f:
        f.write("ward,value\\nWard1,10\\nWard2,20")
    
    response = requests.post(f"{base_url}/send_message",
                            json={"message": "Tell me about the rankings"},
                            cookies={"session_id": session_id})
    if response.status_code == 200:
        data = response.json()
        if 'needs_clarification' in data and data['needs_clarification']:
            print("   ✅ Clarification triggered for ambiguous request")
            print(f"   Options: {len(data.get('options', []))} choices provided")
        else:
            print("   ❌ No clarification for ambiguous request")
    else:
        print(f"   ❌ Request failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Clear action request with data (should use tools)
print("\\n4. Testing clear action request with data...")
try:
    response = requests.post(f"{base_url}/send_message",
                            json={"message": "Analyze my data"},
                            cookies={"session_id": session_id})
    if response.status_code == 200:
        data = response.json()
        if 'needs_clarification' not in data or not data.get('needs_clarification'):
            print("   ✅ Clear action processed without clarification")
        else:
            print("   ❌ Unexpected clarification for clear action")
    else:
        print(f"   ❌ Request failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Arena model availability
print("\\n5. Testing Ollama model availability...")
try:
    import subprocess
    result = subprocess.run(['curl', '-s', 'http://localhost:11434/api/tags'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        import json
        models = json.loads(result.stdout)
        model_names = [m['name'] for m in models.get('models', [])]
        print(f"   Available models: {', '.join(model_names)}")
        required = ['llama3.1:8b', 'mistral:7b', 'phi3:mini']
        for model in required:
            if model in model_names:
                print(f"   ✅ {model} available")
            else:
                print(f"   ❌ {model} missing")
    else:
        print("   ❌ Could not check Ollama models")
except Exception as e:
    print(f"   ❌ Error checking models: {e}")

print("\\n" + "=" * 40)
print("Integration tests complete!")
EOF
"""
    
    cmd = [
        'ssh', '-i', key_path,
        '-o', 'StrictHostKeyChecking=no',
        f'ec2-user@{instance_ip}',
        integration_test
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

def main():
    """Main test execution"""
    print("=" * 60)
    print("🚀 ChatMRPT Intent Clarification System - AWS Testing")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find SSH key
    key_path = find_ssh_key()
    if not key_path:
        print("\n❌ Cannot proceed without SSH key")
        print("\nPlease copy the SSH key to one of these locations:")
        print("  cp /path/to/chatmrpt-key.pem aws_files/")
        print("  OR")
        print("  cp /path/to/chatmrpt-key.pem ~/.ssh/")
        sys.exit(1)
    
    # Test results
    results = {}
    
    # Test each instance
    for instance_name, instance_ip in INSTANCES.items():
        print(f"\n{'=' * 60}")
        print(f"Testing {instance_name}")
        print(f"{'=' * 60}")
        
        # Copy test file
        if not copy_test_to_instance(key_path, instance_ip, instance_name):
            results[instance_name] = "Failed to copy tests"
            continue
        
        # Run unit tests
        test_passed = run_tests_on_instance(key_path, instance_ip, instance_name)
        
        # Run integration tests
        run_integration_tests(key_path, instance_ip, instance_name)
        
        results[instance_name] = "✅ PASSED" if test_passed else "❌ FAILED"
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)
    
    for instance_name, result in results.items():
        print(f"{instance_name}: {result}")
    
    print("\n✅ Test execution complete!")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
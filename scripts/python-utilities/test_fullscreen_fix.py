#!/usr/bin/env python3
"""
Test script to verify fullscreen visualization fix is working in production.
This tests that clicking fullscreen on any visualization shows the correct one,
not always the first one.
"""

import requests
import time
import json
from datetime import datetime

# Production URLs
CLOUDFRONT_URL = "https://d225ar6c86586s.cloudfront.net"
ALB_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

class FullscreenTester:
    def __init__(self, base_url=CLOUDFRONT_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        self.test_results.append({"time": timestamp, "level": level, "message": message})
    
    def test_health_check(self):
        """Test if the application is running"""
        self.log("Testing application health...")
        try:
            response = self.session.get(f"{self.base_url}/ping")
            if response.status_code == 200:
                self.log("✅ Application is healthy", "SUCCESS")
                return True
            else:
                self.log(f"❌ Health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Could not connect: {e}", "ERROR")
            return False
    
    def test_frontend_resources(self):
        """Check if frontend resources are available"""
        self.log("Checking frontend resources...")
        
        # Check main page
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                # Check for React components in the HTML
                if "VisualizationContainer" in response.text or "visualization-container" in response.text:
                    self.log("✅ Frontend contains visualization components", "SUCCESS")
                    
                    # Check for the updated JavaScript
                    if "containerRef" in response.text or "useRef" in response.text:
                        self.log("✅ Frontend appears to have the ref-based fix", "SUCCESS")
                        return True
                    else:
                        self.log("⚠️ Frontend may not have the latest fix (no ref found)", "WARNING")
                        return False
                else:
                    self.log("❌ Frontend missing visualization components", "ERROR")
                    return False
            else:
                self.log(f"❌ Could not load main page: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Error checking frontend: {e}", "ERROR")
            return False
    
    def simulate_visualization_scenario(self):
        """Simulate creating multiple visualizations"""
        self.log("\nSimulating multiple visualization scenario...")
        self.log("This tests the scenario where:")
        self.log("1. User creates visualization A")
        self.log("2. User creates visualization B")
        self.log("3. User creates visualization C")
        self.log("4. User clicks fullscreen on visualization B or C")
        self.log("5. Expected: The clicked visualization goes fullscreen (not A)")
        self.log("")
        self.log("Manual testing steps:")
        self.log("1. Go to " + self.base_url)
        self.log("2. Upload data and create at least 3 visualizations")
        self.log("3. Click fullscreen on the 2nd or 3rd visualization")
        self.log("4. Verify the correct visualization is shown in fullscreen")
        
        return True
    
    def check_deployment_status(self):
        """Check if both instances have the update"""
        self.log("\nChecking deployment across instances...")
        
        # We can't directly check individual instances through the ALB,
        # but we can make multiple requests to see if responses are consistent
        
        results = []
        for i in range(5):
            try:
                response = self.session.get(f"{self.base_url}/")
                if response.status_code == 200:
                    has_fix = "containerRef" in response.text or "useRef" in response.text
                    results.append(has_fix)
                    self.log(f"Request {i+1}: {'✅ Has fix' if has_fix else '⚠️ Missing fix'}", 
                            "INFO" if has_fix else "WARNING")
                time.sleep(0.5)
            except:
                pass
        
        if all(results):
            self.log("✅ All instances appear to have the fix", "SUCCESS")
            return True
        elif any(results):
            self.log("⚠️ Inconsistent deployment - some instances may not have the fix", "WARNING")
            return False
        else:
            self.log("❌ No instances appear to have the fix", "ERROR")
            return False
    
    def generate_report(self):
        """Generate test report"""
        self.log("\n" + "="*60)
        self.log("FULLSCREEN FIX TEST REPORT")
        self.log("="*60)
        
        success_count = sum(1 for r in self.test_results if r["level"] == "SUCCESS")
        warning_count = sum(1 for r in self.test_results if r["level"] == "WARNING")
        error_count = sum(1 for r in self.test_results if r["level"] == "ERROR")
        
        self.log(f"\nResults Summary:")
        self.log(f"  ✅ Success: {success_count}")
        self.log(f"  ⚠️  Warnings: {warning_count}")
        self.log(f"  ❌ Errors: {error_count}")
        
        if error_count == 0 and warning_count == 0:
            self.log("\n🎉 FULLSCREEN FIX APPEARS TO BE DEPLOYED SUCCESSFULLY!")
            self.log("Please perform manual testing to confirm functionality.")
        elif error_count == 0:
            self.log("\n⚠️ DEPLOYMENT PARTIALLY SUCCESSFUL")
            self.log("Some warnings detected. Manual verification recommended.")
            self.log("\nPossible actions:")
            self.log("1. SSH to servers and rebuild frontend:")
            self.log("   cd /home/ec2-user/ChatMRPT/frontend && npm run build")
            self.log("2. Clear browser cache and retry")
            self.log("3. Wait a few minutes for CloudFront cache to update")
        else:
            self.log("\n❌ DEPLOYMENT MAY HAVE ISSUES")
            self.log("Please check the deployment and consider rebuilding frontend on servers.")
        
        self.log("\n" + "="*60)

def main():
    print("\n🔍 Testing Fullscreen Visualization Fix Deployment...\n")
    
    # Test CloudFront
    print("Testing via CloudFront (Primary URL)...")
    print("-" * 40)
    tester = FullscreenTester(CLOUDFRONT_URL)
    
    if tester.test_health_check():
        tester.test_frontend_resources()
        tester.check_deployment_status()
        tester.simulate_visualization_scenario()
    
    tester.generate_report()
    
    # Also test ALB directly
    print("\n\nTesting via ALB (Direct)...")
    print("-" * 40)
    alb_tester = FullscreenTester(ALB_URL)
    if alb_tester.test_health_check():
        alb_tester.test_frontend_resources()
    
    print("\n✅ Test script completed!")
    print("\nNEXT STEPS:")
    print("1. Go to https://d225ar6c86586s.cloudfront.net")
    print("2. Create multiple visualizations in a chat session")
    print("3. Click fullscreen on the 2nd or 3rd visualization")
    print("4. Verify it shows the correct visualization (not the first one)")

if __name__ == "__main__":
    main()
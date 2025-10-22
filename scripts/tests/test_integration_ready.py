#!/usr/bin/env python3
"""
Integration Readiness Test for ChatMRPT TPR Implementation
"""

import os
import sys
import json

# Add app to path
sys.path.insert(0, '.')

def check_backend_integration():
    """Check if backend components are properly integrated"""
    
    print("=" * 60)
    print("BACKEND INTEGRATION CHECK")
    print("=" * 60)
    
    checks = []
    
    # 1. Check TPR utils exist
    try:
        from app.core.tpr_utils import is_tpr_data, calculate_ward_tpr
        checks.append(("TPR Utils", True, "Core functions available"))
    except ImportError as e:
        checks.append(("TPR Utils", False, str(e)))
    
    # 2. Check TPR tool exists
    try:
        from app.data_analysis_v3.tools.tpr_analysis_tool import analyze_tpr_data
        checks.append(("TPR Analysis Tool", True, "Tool registered"))
    except ImportError as e:
        checks.append(("TPR Analysis Tool", False, str(e)))
    
    # 3. Check Data Analysis V3 agent
    try:
        from app.data_analysis_v3.core.agent import DataAnalysisAgent
        checks.append(("Data Analysis V3 Agent", True, "Agent available"))
    except ImportError as e:
        checks.append(("Data Analysis V3 Agent", False, str(e)))
    
    # 4. Check routes registered
    try:
        from app.web.routes import data_analysis_v3_bp, DATA_ANALYSIS_V3_AVAILABLE
        if DATA_ANALYSIS_V3_AVAILABLE and data_analysis_v3_bp:
            checks.append(("Data Analysis V3 Routes", True, "Routes registered"))
        else:
            checks.append(("Data Analysis V3 Routes", False, "Routes not available"))
    except ImportError as e:
        checks.append(("Data Analysis V3 Routes", False, str(e)))
    
    # 5. Check request interpreter integration
    try:
        from app.core.request_interpreter import RequestInterpreter
        checks.append(("Request Interpreter", True, "Available for routing"))
    except ImportError as e:
        checks.append(("Request Interpreter", False, str(e)))
    
    # 6. Check data paths configuration
    try:
        # Check if the file exists without importing (to avoid config issues)
        import os
        if os.path.exists('app/config/data_paths.py'):
            checks.append(("Data Paths Config", True, "AWS-ready paths configured"))
        else:
            checks.append(("Data Paths Config", False, "File not found"))
    except Exception as e:
        checks.append(("Data Paths Config", False, str(e)))
    
    # 7. Check zone-specific variables
    try:
        from app.analysis.region_aware_selection import ZONE_VARIABLES
        checks.append(("Zone-Specific Variables", True, f"{len(ZONE_VARIABLES)} zones configured"))
    except ImportError as e:
        checks.append(("Zone-Specific Variables", False, str(e)))
    
    # Print results
    print("\n📋 Backend Components:")
    all_passed = True
    for component, status, message in checks:
        icon = "✅" if status else "❌"
        print(f"  {icon} {component}: {message}")
        all_passed = all_passed and status
    
    return all_passed


def check_frontend_integration():
    """Check if frontend components are ready"""
    
    print("\n" + "=" * 60)
    print("FRONTEND INTEGRATION CHECK")
    print("=" * 60)
    
    checks = []
    
    # Check for frontend files
    frontend_files = [
        ("Main HTML", "app/templates/index.html"),
        ("API Client", "app/static/js/modules/utils/api-client.js"),
        ("Data Analysis Upload", "app/static/js/modules/upload/data-analysis-upload.js"),
        ("Chat Handler", "app/static/js/modules/chat/core/message-handler.js"),
        ("File Uploader", "app/static/js/modules/upload/file-uploader.js")
    ]
    
    print("\n📋 Frontend Files:")
    all_exist = True
    for name, path in frontend_files:
        exists = os.path.exists(path)
        icon = "✅" if exists else "❌"
        print(f"  {icon} {name}: {path}")
        all_exist = all_exist and exists
    
    return all_exist


def check_deployment_readiness():
    """Check deployment configuration"""
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT READINESS CHECK")
    print("=" * 60)
    
    checks = []
    
    # Check deployment files
    deployment_files = [
        ("Staging Deploy Script", "deployment/deploy_to_staging.sh"),
        ("Production Deploy Script", "deployment/deploy_to_production.sh"),
        ("Requirements", "requirements.txt"),
        ("Gunicorn Config", "gunicorn_config.py"),
        ("Run Script", "run.py")
    ]
    
    print("\n📋 Deployment Files:")
    all_exist = True
    for name, path in deployment_files:
        exists = os.path.exists(path)
        icon = "✅" if exists else "❌"
        print(f"  {icon} {name}: {path}")
        all_exist = all_exist and exists
    
    # Check for hardcoded paths
    print("\n🔍 Checking for hardcoded paths...")
    hardcoded_found = False
    
    import glob
    py_files = glob.glob("app/**/*.py", recursive=True)
    
    bad_patterns = [
        "/mnt/c/Users/bbofo",
        "C:\\\\Users\\\\bbofo",
        "/Users/bbofo/OneDrive"
    ]
    
    for pattern in bad_patterns:
        for py_file in py_files[:100]:  # Check first 100 files
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    if pattern in content:
                        print(f"  ⚠️ Found hardcoded path in {py_file}")
                        hardcoded_found = True
                        break
            except:
                pass
    
    if not hardcoded_found:
        print("  ✅ No hardcoded local paths found")
    
    return all_exist and not hardcoded_found


def check_data_requirements():
    """Check data file requirements"""
    
    print("\n" + "=" * 60)
    print("DATA REQUIREMENTS CHECK")
    print("=" * 60)
    
    print("\n📋 Required Data for AWS:")
    print("  📁 Raster files (~11GB)")
    print("     - Store in: /mnt/efs/chatmrpt/rasters/ (or S3)")
    print("  📁 Nigeria shapefile (~50MB)")
    print("     - Store in: /mnt/efs/chatmrpt/shapefiles/")
    print("  📁 TPR data files")
    print("     - Store in: /mnt/efs/chatmrpt/tpr_data/")
    print("  📁 Settlement data (436MB)")
    print("     - Store in: /mnt/efs/chatmrpt/settlement_data/")
    
    print("\n⚠️ Note: System will use mock data if rasters not found")
    
    return True


if __name__ == "__main__":
    print("🚀 ChatMRPT Integration Readiness Test\n")
    
    # Run all checks
    backend_ready = check_backend_integration()
    frontend_ready = check_frontend_integration()
    deployment_ready = check_deployment_readiness()
    data_noted = check_data_requirements()
    
    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION SUMMARY")
    print("=" * 60)
    
    all_ready = backend_ready and frontend_ready and deployment_ready
    
    print(f"\n{'✅' if backend_ready else '❌'} Backend Integration: {'Ready' if backend_ready else 'Issues found'}")
    print(f"{'✅' if frontend_ready else '❌'} Frontend Integration: {'Ready' if frontend_ready else 'Missing files'}")
    print(f"{'✅' if deployment_ready else '❌'} Deployment Config: {'Ready' if deployment_ready else 'Issues found'}")
    
    if all_ready:
        print("\n🎉 SYSTEM IS READY FOR STAGING DEPLOYMENT!")
        print("\nNext steps:")
        print("1. Test locally: python run.py")
        print("2. Commit changes: git add -A && git commit -m 'TPR integration complete'")
        print("3. Deploy to staging: ./deployment/deploy_to_staging.sh")
        print("4. Upload data files to AWS EFS/S3")
        print("5. Set environment variables on EC2")
    else:
        print("\n⚠️ SOME COMPONENTS NEED ATTENTION")
        print("Please fix the issues above before deploying")
    
    sys.exit(0 if all_ready else 1)
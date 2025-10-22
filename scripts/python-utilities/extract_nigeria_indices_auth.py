"""
Quick script to help authenticate Earth Engine
"""
import ee
import os

print("Attempting to authenticate Earth Engine...")
print("=" * 60)

# Method 1: Try to get project from environment or config
try:
    # Check if there's a default project in config
    ee.Initialize()
    print("✓ Successfully initialized with default settings")
except:
    print("Default initialization failed. Trying other methods...")
    
    # Method 2: Try common project names
    common_projects = ['earthengine-legacy', 'ee-' + os.environ.get('USER', 'user')]
    
    for project in common_projects:
        try:
            ee.Initialize(project=project)
            print(f"✓ Successfully initialized with project: {project}")
            break
        except:
            continue
    else:
        print("\nAuthentication failed. You need to:")
        print("1. Run: earthengine authenticate --force")
        print("2. When prompted, create or select a Google Cloud Project")
        print("3. Or run: gcloud auth application-default login")
        print("\nFor more info: https://developers.google.com/earth-engine/guides/auth")
        
        # Try to get existing credentials info
        import json
        from pathlib import Path
        
        cred_path = Path.home() / '.config' / 'earthengine' / 'credentials'
        if cred_path.exists():
            print(f"\nCredentials file exists at: {cred_path}")
            try:
                with open(cred_path, 'r') as f:
                    creds = json.load(f)
                    if 'project_id' in creds:
                        print(f"Found project ID in credentials: {creds['project_id']}")
                        print(f"\nTry running the script with:")
                        print(f"ee.Initialize(project='{creds['project_id']}')")
            except:
                pass
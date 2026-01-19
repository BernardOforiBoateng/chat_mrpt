#!/usr/bin/env python3
"""Check for missing packages between requirements.txt and installed packages"""

import subprocess
import sys

def get_requirements():
    """Parse requirements.txt"""
    packages = {}
    with open('requirements.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Handle different requirement formats
                if '>=' in line:
                    name, version = line.split('>=')
                    packages[name.lower()] = f">={version}"
                elif '==' in line:
                    name, version = line.split('==')
                    packages[name.lower()] = f"=={version}"
                elif '>' in line:
                    name, version = line.split('>')
                    packages[name.lower()] = f">{version}"
                elif '<' in line:
                    name, version = line.split('<')
                    packages[name.lower()] = f"<{version}"
                else:
                    packages[line.lower()] = ""
    return packages

def get_installed():
    """Get installed packages"""
    result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=freeze'], 
                          capture_output=True, text=True)
    installed = {}
    for line in result.stdout.strip().split('\n'):
        if '==' in line:
            name, version = line.split('==')
            installed[name.lower().replace('_', '-')] = version
    return installed

def main():
    print("Checking package discrepancies...")
    print("=" * 50)
    
    required = get_requirements()
    installed = get_installed()
    
    # Normalize package names (handle underscore vs dash)
    installed_normalized = {}
    for name, version in installed.items():
        installed_normalized[name.replace('_', '-')] = version
        installed_normalized[name.replace('-', '_')] = version
    
    missing = []
    outdated = []
    
    for package, req_version in required.items():
        # Check various name formats
        normalized_name = package.replace('_', '-')
        alt_name = package.replace('-', '_')
        
        found = False
        for check_name in [package, normalized_name, alt_name]:
            if check_name in installed or check_name in installed_normalized:
                found = True
                break
        
        if not found:
            missing.append(f"{package}{req_version}")
    
    if missing:
        print("\n🚨 MISSING PACKAGES:")
        print("-" * 30)
        for pkg in missing:
            print(f"  - {pkg}")
        
        print("\n📦 Install command:")
        print("-" * 30)
        print(f"pip install {' '.join(missing)}")
    else:
        print("\n✅ All required packages are installed!")
    
    # Check for critical packages specifically
    print("\n🔍 Critical package check:")
    print("-" * 30)
    critical = ['openai', 'flask', 'pandas', 'geopandas', 'numpy', 'scikit-learn', 
                'duckdb', 'flask-login', 'gunicorn', 'psycopg2-binary']
    
    for pkg in critical:
        normalized = pkg.replace('_', '-')
        if pkg in installed or normalized in installed or pkg in installed_normalized:
            print(f"  ✓ {pkg} - installed")
        else:
            print(f"  ✗ {pkg} - MISSING")

if __name__ == "__main__":
    main()
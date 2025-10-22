#!/usr/bin/env python3
"""Test if CSP allows OpenStreetMap subdomains"""

import requests

url = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/"
response = requests.head(url)

if 'Content-Security-Policy' in response.headers:
    csp = response.headers['Content-Security-Policy']
    print("CSP Header:")
    print(csp)
    print("\n")
    
    if 'https://*.tile.openstreetmap.org' in csp:
        print("✓ CSP includes wildcard for OpenStreetMap subdomains")
    else:
        print("✗ CSP does NOT include wildcard for OpenStreetMap subdomains")
        
    print("\nConnect-src part:")
    # Extract connect-src part
    parts = csp.split(';')
    for part in parts:
        if 'connect-src' in part:
            print(part.strip())
else:
    print("No CSP header found!")
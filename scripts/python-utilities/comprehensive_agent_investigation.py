#!/usr/bin/env python3
"""
Comprehensive investigation of all agent files
Find redundancy, hardcoding, and issues
"""

import os
import re

print("=" * 60)
print("COMPREHENSIVE AGENT INVESTIGATION")
print("=" * 60)

# All agent files
agent_files = [
    "app/data_analysis_v3/core/agent.py",
    "app/data_analysis_v3/core/agent_backup.py",
    "app/data_analysis_v3/core/agent_fixed.py",
    "app/data_analysis_v3/core/executor.py",
    "app/data_analysis_v3/core/data_validator.py",
    "app/data_analysis_v3/core/column_sanitizer.py",
    "app/data_analysis_v3/core/encoding_handler.py",
    "app/data_analysis_v3/formatters/response_formatter.py",
    "app/data_analysis_v3/prompts/system_prompt.py",
    "app/data_analysis_v3/tools/python_tool.py"
]

issues_found = {
    "truncation": [],
    "hardcoding": [],
    "redundancy": [],
    "hallucination": []
}

def analyze_file(filepath):
    """Analyze a file for issues."""
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    file_issues = {
        "truncation": [],
        "hardcoding": [],
        "redundancy": [],
        "hallucination": [],
        "line_count": len(lines)
    }
    
    # Check for truncation patterns
    truncation_patterns = [
        (r'\.head\((\d+)\)', 'head limit'),
        (r'\[:(\d+)\]', 'slice limit'),
        (r'\.iloc\[:(\d+)\]', 'iloc limit'),
        (r'range\((\d+)\)', 'range limit'),
        (r'for .* in .*\[:(\d+)\]', 'loop limit'),
        (r'insights\[:(\d+)\]', 'insights limit')
    ]
    
    for pattern, desc in truncation_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            limit_val = match.group(1) if match.groups() else 'N/A'
            file_issues["truncation"].append(f"Line {line_num}: {desc} = {limit_val}")
    
    # Check for hardcoding
    hardcoding_patterns = [
        (r'["\']facility["\']', 'hardcoded facility'),
        (r'["\']hospital["\']', 'hardcoded hospital'),
        (r'["\']clinic["\']', 'hardcoded clinic'),
        (r'["\']TPR["\']', 'hardcoded TPR'),
        (r'["\']wardname["\']', 'hardcoded ward'),
        (r'["\']healthfacility["\']', 'hardcoded healthfacility'),
        (r'Facility [A-Z]', 'generic facility name')
    ]
    
    for pattern, desc in hardcoding_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            file_issues["hardcoding"].append(f"Line {line_num}: {desc}")
    
    # Check for hallucination patterns
    hallucination_patterns = [
        (r'Facility [A-Z]\b', 'Facility A/B/C pattern'),
        (r'Item [A-Z]\b', 'Item A/B/C pattern'),
        (r'Entity [A-Z]\b', 'Entity A/B/C pattern')
    ]
    
    for pattern, desc in hallucination_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            file_issues["hallucination"].append(f"Line {line_num}: {desc}")
    
    return file_issues

# Analyze each file
for filepath in agent_files:
    filename = os.path.basename(filepath)
    print(f"\n{'='*40}")
    print(f"FILE: {filename}")
    print(f"{'='*40}")
    
    result = analyze_file(filepath)
    
    if result is None:
        print("   [File not found]")
        continue
    
    print(f"   Lines of code: {result['line_count']}")
    
    if result['truncation']:
        print(f"\n   TRUNCATION ISSUES ({len(result['truncation'])}):")
        for issue in result['truncation'][:5]:
            print(f"      - {issue}")
        issues_found["truncation"].append((filename, result['truncation']))
    
    if result['hardcoding']:
        print(f"\n   HARDCODING ISSUES ({len(result['hardcoding'])}):")
        for issue in result['hardcoding'][:5]:
            print(f"      - {issue}")
        issues_found["hardcoding"].append((filename, result['hardcoding']))
    
    if result['hallucination']:
        print(f"\n   HALLUCINATION PATTERNS ({len(result['hallucination'])}):")
        for issue in result['hallucination'][:5]:
            print(f"      - {issue}")
        issues_found["hallucination"].append((filename, result['hallucination']))

# Check for redundant files
print("\n" + "="*60)
print("REDUNDANCY CHECK")
print("="*60)

backup_files = [f for f in agent_files if 'backup' in f or 'fixed' in f]
if backup_files:
    print("\nREDUNDANT BACKUP FILES:")
    for f in backup_files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(f"   - {os.path.basename(f)} ({size} bytes)")

# Summary
print("\n" + "="*60)
print("CRITICAL FINDINGS SUMMARY")
print("="*60)

print("\n1. TRUNCATION ISSUES (causing 'top 10 shows 3'):")
for filename, issues in issues_found["truncation"]:
    if any('5' in issue or '3' in issue or '10' in issue for issue in issues):
        print(f"   - {filename}: {len(issues)} limits found")
        critical = [i for i in issues if '5' in i or '3' in i]
        for c in critical[:2]:
            print(f"     * {c}")

print("\n2. HARDCODING (domain-specific, not scalable):")
total_hardcoding = sum(len(issues) for _, issues in issues_found["hardcoding"])
print(f"   Total: {total_hardcoding} hardcoded references")
for filename, issues in issues_found["hardcoding"][:3]:
    print(f"   - {filename}: {len(issues)} instances")

print("\n3. HALLUCINATION PATTERNS:")
for filename, issues in issues_found["hallucination"]:
    print(f"   - {filename}: {len(issues)} patterns that could cause 'Facility A' output")

print("\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)

print("""
1. IMMEDIATE FIXES NEEDED:
   - response_formatter.py: Remove [:5] slice on insights
   - agent.py: Check [:15] and [:10] slices
   - executor.py: Remove Facility A/B/C detection patterns
   
2. FILES TO DELETE (redundant):
   - agent_backup.py
   - agent_fixed.py
   
3. HARDCODING TO MAKE DYNAMIC:
   - Replace hardcoded column names with dynamic detection
   - Remove health-specific patterns from core agent
   
4. ROOT CAUSE OF "FACILITY A":
   - executor.py has patterns checking for these
   - But this is AFTER the LLM generates them!
   - Need to fix WHERE they're generated, not just detect them
""")
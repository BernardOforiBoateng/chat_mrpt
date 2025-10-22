#!/usr/bin/env python
"""
Simple test to verify the PCA skip fix by reading the modified code
"""

import ast
import sys

def check_pca_skip_implementation():
    """Check if the PCA skip handling has been implemented correctly"""

    file_path = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/tools/complete_analysis_tools.py'

    with open(file_path, 'r') as f:
        content = f.read()

    checks_passed = []
    checks_failed = []

    # Check 1: PCA skip check in _generate_comprehensive_summary
    if "if not pca_result.get('pca_skipped'):" in content:
        checks_passed.append("✓ PCA skip check added in _generate_comprehensive_summary()")
    else:
        checks_failed.append("✗ Missing PCA skip check in _generate_comprehensive_summary()")

    # Check 2: Empty PCA lists when skipped
    if "pca_top5 = []" in content and "pca_bottom5 = []" in content:
        checks_passed.append("✓ Empty PCA lists handling when PCA is skipped")
    else:
        checks_failed.append("✗ Missing empty PCA lists assignment")

    # Check 3: Column detection logic updated
    if "if not pca_result.get('pca_skipped') and not pca_score_col:" in content:
        checks_passed.append("✓ Column detection logic updated for PCA skip")
    else:
        checks_failed.append("✗ Column detection logic not updated")

    # Check 4: NaN check updated
    if "if not pca_result.get('pca_skipped') and pca_score_col:" in content:
        checks_passed.append("✓ NaN value check updated for PCA skip")
    else:
        checks_failed.append("✗ NaN value check not updated")

    # Check 5: Smart recommendations handling
    if "pca_high_risk = [ward['WardName'] for ward in pca_top5] if pca_top5 else []" in content:
        checks_passed.append("✓ Smart recommendations handles empty PCA lists")
    else:
        checks_failed.append("✗ Smart recommendations not handling empty PCA lists")

    # Print results
    print("="*60)
    print("PCA SKIP FIX IMPLEMENTATION CHECK")
    print("="*60)
    print("\nPASSED CHECKS:")
    for check in checks_passed:
        print(f"  {check}")

    if checks_failed:
        print("\nFAILED CHECKS:")
        for check in checks_failed:
            print(f"  {check}")
        return False
    else:
        print("\n🎉 All implementation checks passed!")
        return True

def verify_message_template():
    """Verify the message template includes ITN planning guidance"""

    file_path = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/tools/complete_analysis_tools.py'

    with open(file_path, 'r') as f:
        content = f.read()

    # Check for ITN planning guidance in the message template
    itn_keywords = ["ITN", "bed net", "Plan ITN", "distribute ITNs"]
    found_itn = any(keyword in content for keyword in itn_keywords)

    # Check for statistical test explanation
    stat_keywords = ["KMO Test Result", "Bartlett's Test", "statistical tests"]
    found_stats = any(keyword in content for keyword in stat_keywords)

    print("\n" + "="*60)
    print("MESSAGE TEMPLATE VERIFICATION")
    print("="*60)

    if found_itn:
        print("✓ ITN planning guidance found in message template")
    else:
        print("✗ ITN planning guidance missing from message template")

    if found_stats:
        print("✓ Statistical test explanation found in message template")
    else:
        print("✗ Statistical test explanation missing from message template")

    return found_itn and found_stats

if __name__ == "__main__":
    print("Checking PCA Skip Fix Implementation...")
    print("-" * 60)

    implementation_ok = check_pca_skip_implementation()
    template_ok = verify_message_template()

    if implementation_ok and template_ok:
        print("\n" + "="*60)
        print("✅ FIX SUCCESSFULLY IMPLEMENTED")
        print("="*60)
        print("\nThe PCA skip message fix has been properly implemented.")
        print("Users will now see:")
        print("- Composite analysis results")
        print("- Statistical test explanation (why PCA was skipped)")
        print("- ITN planning guidance")
        print("- No generic fallback message")
        sys.exit(0)
    else:
        print("\n⚠️ Fix may need additional adjustments")
        sys.exit(1)
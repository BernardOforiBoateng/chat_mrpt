#!/usr/bin/env python
"""
Test that Data Analysis V3 is configured for two-option response
Following CLAUDE.md standards for unit testing
"""

import pytest
import sys
sys.path.insert(0, '.')


class TestTwoOptionsConfiguration:
    """Test suite for verifying two-option configuration in Data Analysis V3."""
    
    def test_system_prompt_has_two_options(self):
        """Verify system prompt is configured for exactly TWO options."""
        from app.data_analysis_v3.prompts.system_prompt import MAIN_SYSTEM_PROMPT
        
        # Check for TWO options mention
        assert 'TWO options' in MAIN_SYSTEM_PROMPT, \
            "System prompt should explicitly mention TWO options"
        
        # Check Option 1 exists (TPR)
        assert 'Guided TPR Analysis' in MAIN_SYSTEM_PROMPT, \
            "Option 1 (Guided TPR Analysis) not found in prompt"
        
        # Check Option 2 exists (Exploration)
        assert 'Flexible Data Exploration' in MAIN_SYSTEM_PROMPT, \
            "Option 2 (Flexible Data Exploration) not found in prompt"
        
        # Ensure NO Option 3
        assert 'Option 3' not in MAIN_SYSTEM_PROMPT, \
            "Found Option 3 - should only have 2 options"
        assert 'Generate Summary Statistics' not in MAIN_SYSTEM_PROMPT, \
            "Found old Option 3 content - should be removed"
        
        # Ensure NO Option 4
        assert 'Option 4' not in MAIN_SYSTEM_PROMPT, \
            "Found Option 4 - should only have 2 options"
        assert 'Data Quality Report' not in MAIN_SYSTEM_PROMPT.replace('quality report', ''), \
            "Found old Option 4 content - should be removed"
        
        print("✅ System prompt correctly configured for TWO options")
    
    def test_initial_upload_instructions(self):
        """Verify prompt has instructions for initial data upload response."""
        from app.data_analysis_v3.prompts.system_prompt import MAIN_SYSTEM_PROMPT
        
        # Check for initial upload trigger instructions
        assert 'Show me what\'s in the uploaded data' in MAIN_SYSTEM_PROMPT or \
               'Show me what' in MAIN_SYSTEM_PROMPT, \
            "Prompt should have instructions for initial upload message"
        
        # Check that it mentions presenting options after summary
        assert 'present a brief summary followed by these TWO options' in MAIN_SYSTEM_PROMPT or \
               'ALWAYS present these TWO options' in MAIN_SYSTEM_PROMPT, \
            "Prompt should instruct to present options after summary"
        
        print("✅ Initial upload instructions present")
    
    def test_risk_assessment_workflow_mentioned(self):
        """Verify that risk assessment workflow is mentioned in Option 1."""
        from app.data_analysis_v3.prompts.system_prompt import MAIN_SYSTEM_PROMPT
        
        # Check that Option 1 mentions risk assessment
        assert 'risk assessment' in MAIN_SYSTEM_PROMPT.lower(), \
            "Option 1 should mention risk assessment workflow"
        
        # Check that TPR is linked to risk assessment
        prompt_lower = MAIN_SYSTEM_PROMPT.lower()
        tpr_section = prompt_lower[prompt_lower.find('guided tpr'):prompt_lower.find('guided tpr')+200]
        assert 'risk' in tpr_section, \
            "TPR option should be linked to risk assessment"
        
        print("✅ Risk assessment workflow properly linked to Option 1")
    
    def test_template_variables_escaped(self):
        """Verify all template variables are properly escaped."""
        from app.data_analysis_v3.prompts.system_prompt import MAIN_SYSTEM_PROMPT
        
        # Check for unescaped template variables
        import re
        
        # Pattern for potential unescaped variables
        unescaped = re.findall(r'{(?!{)[^}]+}(?!})', MAIN_SYSTEM_PROMPT)
        
        # Filter out valid Python f-string patterns that might be in code examples
        problematic = []
        for match in unescaped:
            # Skip if it looks like a valid format string in code example
            if not any(x in match for x in ['len(', 'df.', 'i', 'total', 'facility']):
                continue
            problematic.append(match)
        
        assert len(problematic) == 0, \
            f"Found unescaped template variables: {problematic}"
        
        print("✅ All template variables properly escaped")
    
    def test_no_hallucination_instructions(self):
        """Verify instructions against hallucinated names."""
        from app.data_analysis_v3.prompts.system_prompt import MAIN_SYSTEM_PROMPT
        
        # Check for anti-hallucination rules
        assert 'NEVER use generic names like "Facility A"' in MAIN_SYSTEM_PROMPT or \
               'only use real names from data' in MAIN_SYSTEM_PROMPT, \
            "Should have explicit instructions against generic/hallucinated names"
        
        assert 'make up or hallucinate' in MAIN_SYSTEM_PROMPT.lower(), \
            "Should have explicit anti-hallucination rule"
        
        print("✅ Anti-hallucination instructions present")


def run_all_tests():
    """Run all configuration tests."""
    print("=" * 60)
    print("Testing Data Analysis V3 Two-Option Configuration")
    print("=" * 60)
    
    test_suite = TestTwoOptionsConfiguration()
    
    tests = [
        ('System Prompt Has Two Options', test_suite.test_system_prompt_has_two_options),
        ('Initial Upload Instructions', test_suite.test_initial_upload_instructions),
        ('Risk Assessment Workflow', test_suite.test_risk_assessment_workflow_mentioned),
        ('Template Variables Escaped', test_suite.test_template_variables_escaped),
        ('Anti-Hallucination Rules', test_suite.test_no_hallucination_instructions)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n🧪 Testing: {name}")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
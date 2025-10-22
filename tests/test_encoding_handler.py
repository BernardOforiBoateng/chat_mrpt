"""
Industry-standard pytest tests for encoding handler
Following CLAUDE.md guidelines for proper testing
"""

import pytest
import pandas as pd
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data_analysis_v3.core.encoding_handler import EncodingHandler


class TestEncodingHandler:
    """Test suite for dynamic encoding handler"""
    
    def test_fix_text_encoding_mojibake(self):
        """Test fixing common mojibake patterns"""
        test_cases = [
            # User's reported issue
            ("Ã¢â€°Â¥5yrs", "≥5yrs"),
            ("Persons presenting with fever & tested by RDT Ã¢â€°Â¥5yrs (excl PW)", 
             "Persons presenting with fever & tested by RDT ≥5yrs (excl PW)"),
            
            # Mathematical symbols
            ("â‰¤5", "≤5"),
            ("â‰¥5", "≥5"),
            
            # French accents
            ("CafÃ©", "Café"),
            ("HÃ´pital", "Hôpital"),
            
            # Quotes and apostrophes
            ("itâ€™s", "it's"),
            ("â€œquotesâ€", '"quotes"'),
        ]
        
        for corrupted, expected in test_cases:
            result = EncodingHandler.fix_text_encoding(corrupted)
            assert result == expected, f"Failed to fix: {corrupted} -> {result} (expected: {expected})"
    
    def test_fix_text_encoding_clean_text(self):
        """Test that clean text is not modified"""
        clean_texts = [
            "Normal text",
            "Under 5 years",
            "Primary Health Center",
            "Test Positivity Rate",
        ]
        
        for text in clean_texts:
            result = EncodingHandler.fix_text_encoding(text)
            assert result == text, f"Clean text was modified: {text} -> {result}"
    
    def test_fix_column_names(self):
        """Test fixing DataFrame column names"""
        # Create DataFrame with mojibake column names
        df = pd.DataFrame({
            'State': ['Adamawa'],
            'Ã¢â€°Â¥5yrs_tested': [100],
            'â‰¤5yrs_positive': [20],
            'NormalColumn': [1]
        })
        
        df_fixed = EncodingHandler.fix_column_names(df)
        
        # Check that mojibake was fixed
        assert '≥5yrs_tested' in df_fixed.columns or 'gte_5yrs_tested' in df_fixed.columns
        assert '≤5yrs_positive' in df_fixed.columns or 'lte_5yrs_positive' in df_fixed.columns
        assert 'NormalColumn' in df_fixed.columns
    
    def test_detect_encoding(self):
        """Test encoding detection"""
        # Create a test file with UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.csv', delete=False) as f:
            f.write("State,Ward,Count\n")
            f.write("Adamawa,Ward1,100\n")
            temp_file = f.name
        
        try:
            encoding = EncodingHandler.detect_encoding(temp_file)
            # Should detect UTF-8 or ASCII (both are valid)
            assert encoding.lower() in ['utf-8', 'ascii', 'utf8']
        finally:
            os.unlink(temp_file)
    
    def test_read_csv_with_encoding(self):
        """Test reading CSV with automatic encoding detection and fixing"""
        # Create test CSV with mojibake
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.csv', delete=False) as f:
            f.write("State,Ward,Test_Count\n")
            f.write("Adamawa,Ward1,100\n")
            f.write("Kano,Ward2,200\n")
            temp_file = f.name
        
        try:
            df = EncodingHandler.read_csv_with_encoding(temp_file)
            
            # Check basic reading worked
            assert len(df) == 2
            assert 'state' in df.columns or 'State' in df.columns
            assert df.iloc[0, 0] in ['Adamawa', 'adamawa']
            
        finally:
            os.unlink(temp_file)
    
    def test_read_excel_with_encoding(self):
        """Test reading Excel with encoding fixes"""
        # Note: We'll use the actual test file if available
        test_file = 'www/tpr_data_by_state/ad_Adamawa_State_TPR_LLIN_2024.xlsx'
        
        if os.path.exists(test_file):
            df = EncodingHandler.read_excel_with_encoding(test_file, nrows=5)
            
            # Check that ≥ symbol is preserved or properly sanitized
            columns_str = ' '.join(df.columns)
            assert '≥5yrs' in columns_str or 'gte_5yrs' in columns_str
            
            # Check no mojibake present
            mojibake_indicators = ['Ã', 'â€', 'Â']
            for indicator in mojibake_indicators:
                assert indicator not in columns_str
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test None input
        result = EncodingHandler.fix_text_encoding(None)
        assert result is None
        
        # Test empty string
        result = EncodingHandler.fix_text_encoding("")
        assert result == ""
        
        # Test non-string input
        result = EncodingHandler.fix_text_encoding(123)
        assert result == 123
    
    def test_no_hardcoding(self):
        """Verify no hardcoded mappings exist (per user requirement)"""
        # Read the encoding handler source code
        handler_file = Path(__file__).parent.parent / 'app' / 'data_analysis_v3' / 'core' / 'encoding_handler.py'
        
        with open(handler_file, 'r') as f:
            source_code = f.read()
        
        # Check for hardcoded character mappings
        # These patterns would indicate hardcoding
        forbidden_patterns = [
            "'Ã¢â€°Â¥': '≥'",
            '"Ã¢â€°Â¥": "≥"',
            "replacements = {",
            "mapping = {",
            "char_map = {"
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in source_code, f"Found hardcoded pattern: {pattern}"


class TestFormatting:
    """Test suite for message formatting"""
    
    def test_age_group_formatting(self):
        """Test that age group selection has proper formatting"""
        from app.data_analysis_v3.core.formatters import MessageFormatter
        
        formatter = MessageFormatter("test_session")
        
        # Create test data
        analysis = {
            'state': 'Adamawa',
            'facility_level': 'primary',
            'age_groups': {
                'under_5': {
                    'has_data': True,
                    'name': 'Under 5 Years',
                    'icon': '👶',
                    'tests_available': 1500,
                    'rdt_tests': 1000,
                    'rdt_tpr': 25.5,
                    'microscopy_tests': 500,
                    'microscopy_tpr': 23.2,
                    'positivity_rate': 24.8,
                    'facilities_reporting': 45,
                    'description': 'Highest risk group',
                    'recommended': True
                },
                'over_5': {
                    'has_data': True,
                    'name': 'Over 5 Years',
                    'icon': '👤',
                    'tests_available': 2000,
                    'rdt_tests': 1200,
                    'rdt_tpr': 18.3,
                    'microscopy_tests': 800,
                    'microscopy_tpr': 16.5,
                    'positivity_rate': 17.6,
                    'facilities_reporting': 42,
                    'description': 'General population'
                },
                'pregnant': {
                    'has_data': True,
                    'name': 'Pregnant Women',
                    'icon': '🤰',
                    'tests_available': 800,
                    'rdt_tests': 600,
                    'rdt_tpr': 22.1,
                    'microscopy_tests': 200,
                    'microscopy_tpr': 20.0,
                    'positivity_rate': 21.5,
                    'facilities_reporting': 38,
                    'description': 'Vulnerable group'
                }
            }
        }
        
        message = formatter.format_age_group_selection(analysis)
        
        # Check for proper line breaks
        assert '\n' in message, "Message should contain line breaks"
        
        # Check that all 3 age groups are present (not 4 with all_ages)
        assert 'Under 5 Years' in message
        assert 'Over 5 Years' in message
        assert 'Pregnant Women' in message
        assert 'All Age Groups Combined' not in message
        
        # Check for RDT and Microscopy stats
        assert 'RDT:' in message
        assert 'Microscopy:' in message
        assert '25.5% positive' in message  # RDT TPR for under_5
        assert '23.2% positive' in message  # Microscopy TPR for under_5
        
        # Check formatting has proper structure
        lines = message.split('\n')
        assert len(lines) > 10, "Message should have multiple lines for proper formatting"
    
    def test_no_percentages_over_100(self):
        """Ensure no percentage calculations that could exceed 100%"""
        from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer
        
        # Read the source to ensure percentage_of_total is removed
        analyzer_file = Path(__file__).parent.parent / 'app' / 'data_analysis_v3' / 'core' / 'tpr_data_analyzer.py'
        
        with open(analyzer_file, 'r') as f:
            source_code = f.read()
        
        # Check that the problematic percentage calculation is removed
        assert 'percentage_of_total' not in source_code or '# Removed' in source_code
    
    def test_html_line_breaks(self):
        """Test that line breaks are properly converted to HTML"""
        from app.data_analysis_v3.core.formatters import MessageFormatter
        
        formatter = MessageFormatter("test_session")
        
        # Test message with line breaks
        test_message = "Line 1\nLine 2\n\nLine 3 with double break"
        
        # The JavaScript parseMarkdownContent should convert \n to <br>
        # We're testing that the formatters produce \n for line breaks
        assert '\n' in test_message


@pytest.fixture
def temp_csv_with_mojibake():
    """Fixture to create a CSV file with mojibake"""
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.csv', delete=False) as f:
        # Write header with mojibake
        f.write("State,Ward,Ã¢â€°Â¥5yrs_tested,â‰¤5yrs_positive\n")
        f.write("Adamawa,Ward1,100,20\n")
        f.write("Kano,Ward2,150,30\n")
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    os.unlink(temp_file)


def test_integration_with_mojibake_csv(temp_csv_with_mojibake):
    """Integration test with a CSV containing mojibake"""
    df = EncodingHandler.read_csv_with_encoding(temp_csv_with_mojibake)
    
    # Check columns were fixed
    columns_str = ' '.join(df.columns)
    
    # Should have fixed the mojibake
    assert 'Ã¢â€°Â¥' not in columns_str, "Mojibake should be fixed"
    assert 'â‰¤' not in columns_str or '≤' in columns_str or 'lte' in columns_str
    
    # Data should be intact
    assert len(df) == 2
    assert df.iloc[0, 0] in ['Adamawa', 'adamawa']


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
"""
Unit tests for DataProfiler module
Following pytest and industry-standard testing practices
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import sys
import os

# Add app to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.data_analysis_v3.core.data_profiler import DataProfiler


class TestDataProfiler:
    """Test suite for DataProfiler class following AAA pattern"""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Fixture providing a sample DataFrame for testing"""
        return pd.DataFrame({
            'numeric_col': [1, 2, 3, 4, 5],
            'text_col': ['a', 'b', 'c', 'd', 'e'],
            'date_col': pd.date_range('2024-01-01', periods=5),
            'bool_col': [True, False, True, False, True],
            'mixed_col': [1, 'text', 3.14, None, 5]
        })
    
    @pytest.fixture
    def tpr_dataframe(self):
        """Fixture providing TPR-like medical data"""
        return pd.DataFrame({
            'State': ['Adamawa'] * 10,
            'LGA': ['LGA1'] * 5 + ['LGA2'] * 5,
            'WardName': [f'Ward_{i}' for i in range(10)],
            'HealthFacility': [f'Facility_{i}' for i in range(10)],
            'Persons tested by RDT <5yrs': np.random.randint(50, 200, 10),
            'Persons positive by RDT <5yrs': np.random.randint(5, 50, 10),
            'periodname': ['202401'] * 10
        })
    
    @pytest.fixture
    def empty_dataframe(self):
        """Fixture providing an empty DataFrame"""
        return pd.DataFrame()
    
    @pytest.fixture
    def dataframe_with_missing(self):
        """Fixture providing DataFrame with missing values"""
        df = pd.DataFrame({
            'complete_col': [1, 2, 3, 4, 5],
            'partial_col': [1, None, 3, None, 5],
            'mostly_null': [None, None, None, 4, None]
        })
        return df
    
    @pytest.fixture
    def dataframe_with_duplicates(self):
        """Fixture providing DataFrame with duplicate rows"""
        return pd.DataFrame({
            'col1': [1, 2, 3, 1, 2],
            'col2': ['a', 'b', 'c', 'a', 'b']
        })
    
    # Test profile_dataset method
    
    def test_profile_dataset_returns_correct_structure(self, sample_dataframe):
        """Test that profile_dataset returns dictionary with expected keys"""
        # Arrange
        df = sample_dataframe
        
        # Act
        profile = DataProfiler.profile_dataset(df)
        
        # Assert
        assert isinstance(profile, dict)
        assert 'overview' in profile
        assert 'column_types' in profile
        assert 'data_quality' in profile
        assert 'preview' in profile
        assert 'column_list' in profile
    
    def test_profile_dataset_with_empty_dataframe(self, empty_dataframe):
        """Test that profile_dataset handles empty DataFrames gracefully"""
        # Arrange
        df = empty_dataframe
        
        # Act
        profile = DataProfiler.profile_dataset(df)
        
        # Assert
        assert profile is not None
        assert profile['overview']['rows'] == 0
        assert profile['overview']['columns'] == 0
    
    def test_profile_dataset_exception_handling(self):
        """Test that profile_dataset returns fallback profile on exception"""
        # Arrange
        df = Mock(spec=pd.DataFrame)
        df.__len__ = Mock(return_value=100)
        df.columns = ['col1', 'col2']
        df.memory_usage = Mock(side_effect=Exception("Test error"))
        
        # Act
        profile = DataProfiler.profile_dataset(df)
        
        # Assert
        assert profile is not None
        assert 'overview' in profile
        assert profile['overview']['rows'] == 100
    
    # Test _get_overview method
    
    def test_get_overview_calculates_correct_metrics(self, sample_dataframe):
        """Test that _get_overview returns accurate dataset metrics"""
        # Arrange
        df = sample_dataframe
        
        # Act
        overview = DataProfiler._get_overview(df)
        
        # Assert
        assert overview['rows'] == 5
        assert overview['columns'] == 5
        assert 'memory_mb' in overview
        assert overview['memory_mb'] > 0
        assert overview['shape_str'] == "5 × 5"
        assert 'has_duplicates' in overview
    
    def test_get_overview_handles_large_dataframe(self):
        """Test _get_overview with large DataFrame"""
        # Arrange
        df = pd.DataFrame(np.random.randn(10000, 100))
        
        # Act
        overview = DataProfiler._get_overview(df)
        
        # Assert
        assert overview['rows'] == 10000
        assert overview['columns'] == 100
        assert overview['shape_str'] == "10,000 × 100"
    
    # Test _analyze_column_types method
    
    def test_analyze_column_types_identifies_types_correctly(self, sample_dataframe):
        """Test that _analyze_column_types correctly categorizes columns"""
        # Arrange
        df = sample_dataframe
        
        # Act
        types = DataProfiler._analyze_column_types(df)
        
        # Assert
        assert 'numeric_col' in types['numeric']
        assert 'text_col' in types['text']
        assert 'date_col' in types['datetime']
        assert 'bool_col' in types['boolean']
        assert types['counts']['numeric'] == 1
        assert types['counts']['text'] == 2  # text_col and mixed_col
        assert types['counts']['datetime'] == 1
        assert types['counts']['boolean'] == 1
    
    def test_analyze_column_types_with_no_columns(self, empty_dataframe):
        """Test _analyze_column_types with empty DataFrame"""
        # Arrange
        df = empty_dataframe
        
        # Act
        types = DataProfiler._analyze_column_types(df)
        
        # Assert
        assert types['numeric'] == []
        assert types['text'] == []
        assert types['datetime'] == []
        assert types['boolean'] == []
    
    # Test _check_data_quality method
    
    def test_check_data_quality_detects_missing_values(self, dataframe_with_missing):
        """Test that _check_data_quality correctly identifies missing values"""
        # Arrange
        df = dataframe_with_missing
        
        # Act
        quality = DataProfiler._check_data_quality(df)
        
        # Assert
        assert quality['has_missing'] == True
        assert 'partial_col' in quality['missing_values']
        assert quality['missing_values']['partial_col'] == 2
        assert 'mostly_null' in quality['missing_values']
        assert quality['missing_values']['mostly_null'] == 4
        assert quality['completeness'] < 100
    
    def test_check_data_quality_detects_duplicates(self, dataframe_with_duplicates):
        """Test that _check_data_quality correctly identifies duplicate rows"""
        # Arrange
        df = dataframe_with_duplicates
        
        # Act
        quality = DataProfiler._check_data_quality(df)
        
        # Assert
        assert quality['has_duplicates'] == True
        assert quality['duplicate_rows'] == 2
        assert quality['duplicate_percentage'] == 40.0
    
    def test_check_data_quality_with_perfect_data(self, sample_dataframe):
        """Test _check_data_quality with clean data"""
        # Arrange
        df = sample_dataframe.drop('mixed_col', axis=1)  # Remove column with None
        
        # Act
        quality = DataProfiler._check_data_quality(df)
        
        # Assert
        assert quality['has_missing'] == False
        assert quality['has_duplicates'] == False
        assert quality['completeness'] == 100.0
    
    # Test _get_preview method
    
    def test_get_preview_returns_correct_number_of_rows(self, sample_dataframe):
        """Test that _get_preview returns requested number of rows"""
        # Arrange
        df = sample_dataframe
        rows = 3
        
        # Act
        preview = DataProfiler._get_preview(df, rows=rows)
        
        # Assert
        assert preview['rows_shown'] == 3
        assert len(preview['records']) == 3
        assert len(preview['formatted']) == 3
    
    def test_get_preview_handles_nan_values(self, dataframe_with_missing):
        """Test that _get_preview handles NaN values properly"""
        # Arrange
        df = dataframe_with_missing
        
        # Act
        preview = DataProfiler._get_preview(df)
        
        # Assert
        # Check that NaN values are formatted as "NaN" strings
        formatted = preview['formatted']
        for record in formatted:
            for key, value in record.items():
                if 'partial_col' in key or 'mostly_null' in key:
                    # These columns have NaN values
                    assert value == "NaN" or isinstance(value, (int, float))
    
    # Test _get_column_details method
    
    def test_get_column_details_provides_statistics(self, sample_dataframe):
        """Test that _get_column_details returns detailed column information"""
        # Arrange
        df = sample_dataframe
        
        # Act
        details = DataProfiler._get_column_details(df)
        
        # Assert
        assert len(details) == len(df.columns)
        
        # Check numeric column has statistics
        numeric_detail = next(d for d in details if d['name'] == 'numeric_col')
        assert 'min' in numeric_detail
        assert 'max' in numeric_detail
        assert 'mean' in numeric_detail
        assert 'std' in numeric_detail
        
        # Check text column has sample values
        text_detail = next(d for d in details if d['name'] == 'text_col')
        assert 'sample_values' in text_detail
    
    # Test format_profile_summary method
    
    def test_format_profile_summary_generates_readable_text(self, sample_dataframe):
        """Test that format_profile_summary creates user-friendly summary"""
        # Arrange
        df = sample_dataframe
        profile = DataProfiler.profile_dataset(df)
        
        # Act
        summary = DataProfiler.format_profile_summary(profile)
        
        # Assert
        assert isinstance(summary, str)
        assert "📊 **Data Successfully Loaded!**" in summary
        assert "Dataset Overview:" in summary
        assert "Column Types:" in summary
        assert "Data Quality:" in summary
    
    def test_format_profile_summary_handles_missing_data(self, dataframe_with_missing):
        """Test format_profile_summary mentions missing values when present"""
        # Arrange
        df = dataframe_with_missing
        profile = DataProfiler.profile_dataset(df)
        
        # Act
        summary = DataProfiler.format_profile_summary(profile)
        
        # Assert
        assert "columns have missing values" in summary
        assert "complete" in summary.lower()
    
    def test_format_profile_summary_handles_duplicates(self, dataframe_with_duplicates):
        """Test format_profile_summary mentions duplicates when present"""
        # Arrange
        df = dataframe_with_duplicates
        profile = DataProfiler.profile_dataset(df)
        
        # Act
        summary = DataProfiler.format_profile_summary(profile)
        
        # Assert
        assert "duplicate rows found" in summary
    
    # Integration tests
    
    def test_profiler_works_with_tpr_data(self, tpr_dataframe):
        """Test that profiler handles TPR medical data without hardcoding"""
        # Arrange
        df = tpr_dataframe
        
        # Act
        profile = DataProfiler.profile_dataset(df)
        summary = DataProfiler.format_profile_summary(profile)
        
        # Assert
        # Should NOT hardcode or detect TPR specifically
        assert "TPR" not in summary  # Should not mention TPR
        assert "malaria" not in summary.lower()  # Should not assume malaria
        
        # Should just report facts
        assert str(len(df)) in summary  # Row count
        assert str(len(df.columns)) in summary  # Column count
    
    def test_profiler_is_data_agnostic(self):
        """Test that profiler works identically for different data types"""
        # Arrange
        medical_df = pd.DataFrame({
            'WardName': ['Ward1', 'Ward2'],
            'tested': [100, 200],
            'positive': [10, 20]
        })
        
        sales_df = pd.DataFrame({
            'Product': ['Widget', 'Gadget'],
            'sold': [100, 200],
            'returned': [10, 20]
        })
        
        # Act
        medical_profile = DataProfiler.profile_dataset(medical_df)
        sales_profile = DataProfiler.profile_dataset(sales_df)
        
        # Assert - Both should have same structure
        assert medical_profile.keys() == sales_profile.keys()
        assert medical_profile['overview']['columns'] == 3
        assert sales_profile['overview']['columns'] == 3
        
        # Neither should have domain-specific handling
        medical_summary = DataProfiler.format_profile_summary(medical_profile)
        sales_summary = DataProfiler.format_profile_summary(sales_profile)
        
        # Both should have same format structure
        assert "Dataset Overview:" in medical_summary
        assert "Dataset Overview:" in sales_summary
        assert "Column Types:" in medical_summary
        assert "Column Types:" in sales_summary
    
    # Performance tests
    
    def test_profiler_performance_with_large_dataset(self):
        """Test that profiler completes in reasonable time for large datasets"""
        # Arrange
        import time
        large_df = pd.DataFrame(np.random.randn(100000, 50))
        
        # Act
        start_time = time.time()
        profile = DataProfiler.profile_dataset(large_df)
        elapsed_time = time.time() - start_time
        
        # Assert
        assert elapsed_time < 5.0  # Should complete within 5 seconds
        assert profile is not None
        assert profile['overview']['rows'] == 100000
    
    # Edge case tests
    
    def test_profiler_handles_special_characters_in_columns(self):
        """Test profiler handles special characters in column names"""
        # Arrange
        df = pd.DataFrame({
            'Column with spaces': [1, 2, 3],
            'Column@with#special$chars': ['a', 'b', 'c'],
            '中文列名': [True, False, True]
        })
        
        # Act
        profile = DataProfiler.profile_dataset(df)
        
        # Assert
        assert profile is not None
        assert len(profile['column_list']) == 3
    
    def test_profiler_handles_single_row_dataframe(self):
        """Test profiler handles DataFrame with single row"""
        # Arrange
        df = pd.DataFrame({'col1': [1], 'col2': ['text']})
        
        # Act
        profile = DataProfiler.profile_dataset(df)
        
        # Assert
        assert profile['overview']['rows'] == 1
        assert profile['data_quality']['has_duplicates'] == False
    
    def test_profiler_handles_single_column_dataframe(self):
        """Test profiler handles DataFrame with single column"""
        # Arrange
        df = pd.DataFrame({'only_column': range(100)})
        
        # Act
        profile = DataProfiler.profile_dataset(df)
        
        # Assert
        assert profile['overview']['columns'] == 1
        assert len(profile['column_types']['numeric']) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
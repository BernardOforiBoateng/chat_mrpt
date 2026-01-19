#!/usr/bin/env python3
"""
Test script for metadata caching performance improvements
"""

import os
import sys
import time
import json
import pandas as pd

# Add ChatMRPT to path
sys.path.insert(0, '.')

def test_metadata_extraction():
    """Test metadata extraction for large files."""
    from app.data_analysis_v3.core.metadata_cache import MetadataCache
    
    print("Testing Metadata Cache...")
    print("-" * 60)
    
    # Test with the large NMEP file if it exists
    test_file = "www/NMEP TPR and LLIN 2024_16072025.xlsx"
    
    if os.path.exists(test_file):
        print(f"Testing with large file: {test_file}")
        print(f"File size: {os.path.getsize(test_file) / (1024*1024):.2f} MB")
        
        # Time metadata extraction
        start = time.time()
        metadata = MetadataCache.extract_file_metadata(test_file, "NMEP_TPR_2024.xlsx")
        elapsed = time.time() - start
        
        print(f"\nMetadata extraction time: {elapsed:.2f} seconds")
        print(f"Rows: {metadata.get('rows', 'Unknown')}")
        print(f"Columns: {metadata.get('columns', 'Unknown')}")
        print(f"Is sampled: {metadata.get('is_sampled', False)}")
        
        if metadata.get('rows_estimated'):
            print(f"Row count is estimated from file size")
        
        # Show column names if available
        if metadata.get('column_names'):
            print(f"\nFirst 5 columns: {metadata['column_names'][:5]}")
    else:
        print(f"Large test file not found: {test_file}")
        print("Creating a test file...")
        
        # Create a test file
        test_data = pd.DataFrame({
            f'col_{i}': range(10000) 
            for i in range(50)
        })
        test_csv = "test_large_data.csv"
        test_data.to_csv(test_csv, index=False)
        
        print(f"Created test file: {test_csv}")
        print(f"File size: {os.path.getsize(test_csv) / (1024*1024):.2f} MB")
        
        # Test metadata extraction
        start = time.time()
        metadata = MetadataCache.extract_file_metadata(test_csv, test_csv)
        elapsed = time.time() - start
        
        print(f"\nMetadata extraction time: {elapsed:.2f} seconds")
        print(f"Rows: {metadata.get('rows', 'Unknown')}")
        print(f"Columns: {metadata.get('columns', 'Unknown')}")
        
        # Clean up
        os.remove(test_csv)

def test_cache_performance():
    """Test cache read performance."""
    from app.data_analysis_v3.core.metadata_cache import MetadataCache
    
    print("\n" + "=" * 60)
    print("Testing Cache Performance...")
    print("-" * 60)
    
    session_id = "test_session"
    
    # Create test cache
    test_cache = {
        'files': {
            'data1.csv': {
                'filename': 'data1.csv',
                'rows': 337774,
                'columns': 45,
                'file_size_mb': 25.3,
                'is_sampled': True
            },
            'data2.xlsx': {
                'filename': 'data2.xlsx',
                'rows': 150000,
                'columns': 30,
                'file_size_mb': 12.5,
                'is_sampled': False
            }
        },
        'last_updated': '2025-01-08T10:00:00'
    }
    
    # Save cache
    cache_dir = f"instance/uploads/{session_id}"
    os.makedirs(cache_dir, exist_ok=True)
    MetadataCache.save_cache(session_id, test_cache)
    
    # Time cache read
    start = time.time()
    summary = MetadataCache.get_summary_from_cache(session_id)
    elapsed = time.time() - start
    
    print(f"Cache read time: {elapsed*1000:.2f} ms")
    print(f"\nGenerated summary:\n{summary}")
    
    # Clean up
    import shutil
    shutil.rmtree(cache_dir, ignore_errors=True)

def test_lazy_loading():
    """Test lazy loading functionality."""
    from app.data_analysis_v3.core.lazy_loader import LazyDataLoader
    
    print("\n" + "=" * 60)
    print("Testing Lazy Loading...")
    print("-" * 60)
    
    session_id = "test_lazy"
    data_dir = f"instance/uploads/{session_id}"
    os.makedirs(data_dir, exist_ok=True)
    
    # Create test files
    test_data1 = pd.DataFrame({'A': range(1000), 'B': range(1000, 2000)})
    test_data2 = pd.DataFrame({'X': range(500), 'Y': range(500, 1000)})
    
    test_data1.to_csv(os.path.join(data_dir, "test1.csv"), index=False)
    test_data2.to_csv(os.path.join(data_dir, "test2.csv"), index=False)
    
    # Test lazy loader
    loader = LazyDataLoader(session_id)
    
    print(f"Available variables: {loader.get_available_variables()}")
    
    # Test lazy context
    context = loader.get_lazy_context()
    
    print("\nTesting lazy access...")
    start = time.time()
    # This should trigger loading
    df1 = context['test1']
    elapsed = time.time() - start
    print(f"First access of 'test1': {elapsed*1000:.2f} ms, shape: {df1.shape}")
    
    start = time.time()
    # This should be cached
    df1_again = context['test1']
    elapsed = time.time() - start
    print(f"Second access of 'test1': {elapsed*1000:.2f} ms (should be instant)")
    
    # Clean up
    import shutil
    shutil.rmtree(data_dir, ignore_errors=True)

if __name__ == "__main__":
    print("=" * 60)
    print("METADATA CACHE PERFORMANCE TEST")
    print("=" * 60)
    
    test_metadata_extraction()
    test_cache_performance()
    test_lazy_loading()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
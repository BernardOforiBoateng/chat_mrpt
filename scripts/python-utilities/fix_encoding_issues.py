#!/usr/bin/env python3
"""
Fix encoding issues in Data Analysis V3
This script updates all files to use the EncodingHandler
"""

import os
import re

def fix_agent_py():
    """Fix agent.py to use EncodingHandler"""
    file_path = 'app/data_analysis_v3/core/agent.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import at the top with other imports
    if 'from .encoding_handler import EncodingHandler' not in content:
        # Find the imports section
        import_pattern = r'(from \.formatters import MessageFormatter\n)'
        content = re.sub(import_pattern, r'\1from .encoding_handler import EncodingHandler\n', content)
    
    # Replace pd.read_csv calls
    content = re.sub(
        r'df_full = pd\.read_csv\(data_path\)\s*# Read FULL data',
        'df_full = EncodingHandler.read_csv_with_encoding(data_path)  # Read with encoding fix',
        content
    )
    
    content = re.sub(
        r'df_full = pd\.read_excel\(data_path\)\s*# Read FULL data',
        'df_full = EncodingHandler.read_excel_with_encoding(data_path)  # Read with encoding fix',
        content
    )
    
    # Fix in _check_and_add_tpr_tool method
    content = re.sub(
        r'df = pd\.read_csv\(data_file\)',
        'df = EncodingHandler.read_csv_with_encoding(data_file)',
        content
    )
    
    content = re.sub(
        r'df = pd\.read_excel\(data_file\)',
        'df = EncodingHandler.read_excel_with_encoding(data_file)',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def fix_python_tool():
    """Fix python_tool.py to use EncodingHandler"""
    file_path = 'app/data_analysis_v3/tools/python_tool.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import
    if 'from ..core.encoding_handler import EncodingHandler' not in content:
        import_line = 'from ..core.lazy_loader import LazyDataLoader\n'
        if import_line in content:
            content = content.replace(import_line, import_line + 'from ..core.encoding_handler import EncodingHandler\n')
    
    # Replace pd.read_csv calls
    content = re.sub(
        r'current_data\[var_name\] = pd\.read_csv\(data_path\)',
        'current_data[var_name] = EncodingHandler.read_csv_with_encoding(data_path)',
        content
    )
    
    content = re.sub(
        r'current_data\[var_name\] = pd\.read_excel\(data_path\)',
        'current_data[var_name] = EncodingHandler.read_excel_with_encoding(data_path)',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def fix_tpr_workflow_handler():
    """Fix tpr_workflow_handler.py"""
    file_path = 'app/data_analysis_v3/core/tpr_workflow_handler.py'
    
    if not os.path.exists(file_path):
        print(f"⚠️ {file_path} not found, skipping")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import
    if 'from .encoding_handler import EncodingHandler' not in content:
        # Find a good place to add the import
        if 'import pandas as pd' in content:
            content = content.replace('import pandas as pd', 'import pandas as pd\nfrom .encoding_handler import EncodingHandler')
    
    # Replace pd.read_csv calls
    content = re.sub(
        r'df = pd\.read_csv\(([^)]+)\)',
        r'df = EncodingHandler.read_csv_with_encoding(\1)',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def fix_lazy_loader():
    """Fix lazy_loader.py"""
    file_path = 'app/data_analysis_v3/core/lazy_loader.py'
    
    if not os.path.exists(file_path):
        print(f"⚠️ {file_path} not found, skipping")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import
    if 'from .encoding_handler import EncodingHandler' not in content:
        if 'import pandas as pd' in content:
            content = content.replace('import pandas as pd', 'import pandas as pd\nfrom .encoding_handler import EncodingHandler')
    
    # Replace pd.read_csv calls
    content = re.sub(
        r'df = pd\.read_csv\(filepath\)',
        r'df = EncodingHandler.read_csv_with_encoding(filepath)',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def fix_metadata_cache():
    """Fix metadata_cache.py"""
    file_path = 'app/data_analysis_v3/core/metadata_cache.py'
    
    if not os.path.exists(file_path):
        print(f"⚠️ {file_path} not found, skipping")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import
    if 'from .encoding_handler import EncodingHandler' not in content:
        if 'import pandas as pd' in content:
            content = content.replace('import pandas as pd', 'import pandas as pd\nfrom .encoding_handler import EncodingHandler')
    
    # Replace pd.read_csv calls
    content = re.sub(
        r'df = pd\.read_csv\(filepath\)',
        r'df = EncodingHandler.read_csv_with_encoding(filepath)',
        content
    )
    
    content = re.sub(
        r'df_sample = pd\.read_csv\(filepath, nrows=MetadataCache\.SAMPLE_ROWS\)',
        r'df_sample = EncodingHandler.read_csv_with_encoding(filepath, nrows=MetadataCache.SAMPLE_ROWS)',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def fix_tpr_analysis_tool():
    """Fix tpr_analysis_tool.py"""
    file_path = 'app/data_analysis_v3/tools/tpr_analysis_tool.py'
    
    if not os.path.exists(file_path):
        print(f"⚠️ {file_path} not found, skipping")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import
    if 'from ..core.encoding_handler import EncodingHandler' not in content:
        if 'import pandas as pd' in content:
            content = content.replace('import pandas as pd', 'import pandas as pd\nfrom ..core.encoding_handler import EncodingHandler')
    
    # Replace pd.read_csv calls
    content = re.sub(
        r'df = pd\.read_csv\(data_file\)',
        r'df = EncodingHandler.read_csv_with_encoding(data_file)',
        content
    )
    
    content = re.sub(
        r'tpr_results = pd\.read_csv\(tpr_results_file\)',
        r'tpr_results = EncodingHandler.read_csv_with_encoding(tpr_results_file)',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

if __name__ == '__main__':
    print("🔧 Fixing encoding issues in Data Analysis V3...")
    
    # Fix all files
    fix_agent_py()
    fix_python_tool()
    fix_tpr_workflow_handler()
    fix_lazy_loader()
    fix_metadata_cache()
    fix_tpr_analysis_tool()
    
    print("\n✅ All files updated to use EncodingHandler!")
    print("\n📝 Next steps:")
    print("1. Test the changes locally")
    print("2. Deploy to staging")
    print("3. Verify the agent no longer hallucinates when encountering encoding issues")
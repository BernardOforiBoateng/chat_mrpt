#!/usr/bin/env python3
"""
Add comprehensive debug logging to risk analysis flow
This will track all requests and responses to identify where visualizations fail
"""

import os
import sys

def add_debug_logging():
    """Add debug logging to key risk analysis files"""
    
    print("=" * 60)
    print("ADDING DEBUG LOGGING TO RISK ANALYSIS FLOW")
    print("=" * 60)
    
    # 1. Update request_interpreter.py for detailed request/response logging
    request_interpreter_file = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/core/request_interpreter.py'
    
    with open(request_interpreter_file, 'r') as f:
        content = f.read()
    
    # Add debug logging imports if not present
    if 'import json' not in content[:500]:
        content = 'import json\n' + content
    
    # Find the process_message method and add debug logging
    process_message_start = content.find('def process_message(self, user_message: str, session_id: str')
    if process_message_start > 0:
        # Find the try block
        try_block = content.find('try:', process_message_start)
        if try_block > 0:
            # Insert debug logging right after try:
            insert_pos = content.find('\n', try_block) + 1
            indent = '            '
            debug_code = f'''{indent}# 🔍 DEBUG: Log incoming request
{indent}logger.info("=" * 60)
{indent}logger.info(f"🔍 DEBUG REQUEST INTERPRETER: Processing request")
{indent}logger.info(f"🔍 Session ID: {{session_id}}")
{indent}logger.info(f"🔍 User Message: {{user_message}}")
{indent}logger.info(f"🔍 Session Data Keys: {{list(session_data.keys()) if session_data else 'None'}}")
{indent}logger.info(f"🔍 Kwargs: {{kwargs}}")
{indent}logger.info("=" * 60)
'''
            content = content[:insert_pos] + debug_code + content[insert_pos:]
    
    # Add debug logging to _llm_with_tools method
    llm_with_tools_pos = content.find('def _llm_with_tools(self, user_message: str')
    if llm_with_tools_pos > 0:
        # Find the method body
        method_start = content.find(':', llm_with_tools_pos)
        next_line = content.find('\n', method_start) + 1
        
        # Check indentation
        indent = '        '
        
        debug_code = f'''{indent}"""LLM with tools execution - DEBUG VERSION"""
{indent}logger.info("🔍 DEBUG LLM_WITH_TOOLS: Starting tool selection")
{indent}logger.info(f"🔍 Available tools: {{list(self.tools.keys())}}")
{indent}logger.info(f"🔍 Session context data_loaded: {{session_context.get('data_loaded')}}")
'''
        
        # Find where to insert (after docstring if exists)
        docstring_end = content.find('"""', next_line)
        if docstring_end > next_line:
            docstring_end = content.find('"""', docstring_end + 3) + 3
            insert_pos = content.find('\n', docstring_end) + 1
        else:
            insert_pos = next_line
        
        content = content[:insert_pos] + debug_code + content[insert_pos:]
    
    # Add debug logging for tool execution results
    tool_execution_marker = 'if tool_name in self.tools:'
    tool_exec_pos = content.find(tool_execution_marker)
    if tool_exec_pos > 0:
        # Find the result assignment
        result_line = content.find('result = self.tools[tool_name]', tool_exec_pos)
        if result_line > 0:
            next_line = content.find('\n', result_line) + 1
            indent = '                '
            debug_code = f'''{indent}logger.info(f"🔍 DEBUG: Executing tool {{tool_name}} with params: {{params}}")
{indent}tool_result = self.tools[tool_name](**params)
{indent}logger.info(f"🔍 DEBUG: Tool result - Success: {{tool_result.get('success') if isinstance(tool_result, dict) else 'N/A'}}")
{indent}logger.info(f"🔍 DEBUG: Tool result keys: {{list(tool_result.keys()) if isinstance(tool_result, dict) else type(tool_result)}}")
{indent}if isinstance(tool_result, dict) and not tool_result.get('success'):
{indent}    logger.error(f"🔍 DEBUG: Tool failed - Error: {{tool_result.get('error_details', tool_result.get('message', 'Unknown error'))}}")
{indent}result = tool_result
'''
            # Replace the original line
            original_line_end = content.find('\n', result_line)
            content = content[:result_line] + debug_code.rstrip() + content[original_line_end:]
    
    with open(request_interpreter_file, 'w') as f:
        f.write(content)
    print(f"✅ Updated {request_interpreter_file}")
    
    # 2. Update complete_analysis_tools.py for execution tracking
    analysis_tools_file = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/tools/complete_analysis_tools.py'
    
    with open(analysis_tools_file, 'r') as f:
        content = f.read()
    
    # Find the _execute method
    execute_pos = content.find('def _execute(self, **kwargs) -> ToolExecutionResult:')
    if execute_pos > 0:
        # Add debug at the start
        try_pos = content.find('try:', execute_pos)
        if try_pos > 0:
            next_line = content.find('\n', try_pos) + 1
            indent = '            '
            debug_code = f'''{indent}# 🔍 DEBUG: Complete Analysis Execution
{indent}logger.info("=" * 60)
{indent}logger.info("🔍 DEBUG COMPLETE ANALYSIS: Starting execution")
{indent}logger.info(f"🔍 Session ID: {{session_id}}")
{indent}logger.info(f"🔍 Composite variables: {{composite_variables}}")
{indent}logger.info(f"🔍 PCA variables: {{pca_variables}}")
{indent}logger.info(f"🔍 Create unified dataset: {{kwargs.get('create_unified_dataset', True)}}")
{indent}
{indent}# Check what files exist before analysis
{indent}session_dir = f'instance/uploads/{{session_id}}'
{indent}if os.path.exists(session_dir):
{indent}    files = os.listdir(session_dir)
{indent}    logger.info(f"🔍 Files in session BEFORE analysis: {{files[:10]}}")
{indent}    
{indent}    # Check for key files
{indent}    for key_file in ['raw_data.csv', 'raw_shapefile.zip', 'unified_dataset.csv', 'tpr_results.csv']:
{indent}        file_path = os.path.join(session_dir, key_file)
{indent}        if os.path.exists(file_path):
{indent}            size = os.path.getsize(file_path)
{indent}            logger.info(f"🔍   ✅ {{key_file}} exists ({{size:,}} bytes)")
{indent}        else:
{indent}            logger.info(f"🔍   ❌ {{key_file}} NOT found")
{indent}logger.info("=" * 60)
'''
            content = content[:next_line] + debug_code + content[next_line:]
    
    # Add debug logging at the end of analysis
    success_return = 'return ToolExecutionResult(success=True'
    success_pos = content.find(success_return, execute_pos)
    if success_pos > 0:
        # Insert debug before return
        indent = '            '
        debug_code = f'''{indent}# 🔍 DEBUG: Analysis completed successfully
{indent}logger.info("=" * 60)
{indent}logger.info("🔍 DEBUG COMPLETE ANALYSIS: Finished successfully")
{indent}if os.path.exists(session_dir):
{indent}    files = os.listdir(session_dir)
{indent}    logger.info(f"🔍 Files in session AFTER analysis: {{len(files)}} files")
{indent}    
{indent}    # Check for output files
{indent}    for pattern in ['unified_dataset', 'analysis_', 'vulnerability_map', '.html']:
{indent}        matching = [f for f in files if pattern in f]
{indent}        if matching:
{indent}            logger.info(f"🔍   Found {{len(matching)}} files with '{{pattern}}'")
{indent}            for f in matching[:3]:
{indent}                logger.info(f"🔍     - {{f}}")
{indent}
{indent}    # Specifically check unified dataset
{indent}    unified_path = os.path.join(session_dir, 'unified_dataset.csv')
{indent}    if os.path.exists(unified_path):
{indent}        logger.info(f"🔍 ✅ UNIFIED DATASET CREATED: {{unified_path}}")
{indent}    else:
{indent}        logger.error(f"🔍 ❌ UNIFIED DATASET NOT CREATED")
{indent}logger.info("=" * 60)
{indent}
'''
        content = content[:success_pos] + debug_code + content[success_pos:]
    
    with open(analysis_tools_file, 'w') as f:
        f.write(content)
    print(f"✅ Updated {analysis_tools_file}")
    
    # 3. Update visualization_maps_tools.py
    viz_maps_file = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/tools/visualization_maps_tools.py'
    
    if os.path.exists(viz_maps_file):
        with open(viz_maps_file, 'r') as f:
            content = f.read()
        
        # Add debug at execute method for CreateVulnerabilityMap
        vuln_execute = content.find('class CreateVulnerabilityMap')
        if vuln_execute > 0:
            execute_method = content.find('def execute(self, session_id: str)', vuln_execute)
            if execute_method > 0:
                try_pos = content.find('try:', execute_method)
                if try_pos > 0:
                    next_line = content.find('\n', try_pos) + 1
                    indent = '            '
                    debug_code = f'''{indent}# 🔍 DEBUG: Vulnerability Map Creation
{indent}logger.info("=" * 60)
{indent}logger.info("🔍 DEBUG VULNERABILITY MAP: Starting")
{indent}logger.info(f"🔍 Session ID: {{session_id}}")
{indent}logger.info(f"🔍 Risk categories: {{self.risk_categories}}")
{indent}logger.info(f"🔍 Classification method: {{self.classification_method}}")
{indent}
{indent}# Check for unified dataset
{indent}unified_path = f'instance/uploads/{{session_id}}/unified_dataset.csv'
{indent}raw_path = f'instance/uploads/{{session_id}}/raw_data.csv'
{indent}
{indent}logger.info(f"🔍 Checking for unified dataset at: {{unified_path}}")
{indent}if os.path.exists(unified_path):
{indent}    logger.info(f"🔍 ✅ Unified dataset EXISTS")
{indent}else:
{indent}    logger.error(f"🔍 ❌ Unified dataset NOT FOUND")
{indent}    if os.path.exists(raw_path):
{indent}        logger.info(f"🔍 💡 raw_data.csv EXISTS - could use as fallback")
{indent}logger.info("=" * 60)
'''
                    content = content[:next_line] + debug_code + content[next_line:]
        
        with open(viz_maps_file, 'w') as f:
            f.write(content)
        print(f"✅ Updated {viz_maps_file}")
    
    # 4. Update variable_distribution.py
    var_dist_file = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/tools/variable_distribution.py'
    
    if os.path.exists(var_dist_file):
        with open(var_dist_file, 'r') as f:
            content = f.read()
        
        # Add debug at execute method
        execute_pos = content.find('def execute(self, session_id: str) -> ToolExecutionResult:')
        if execute_pos > 0:
            try_pos = content.find('try:', execute_pos)
            if try_pos > 0:
                next_line = content.find('\n', try_pos) + 1
                indent = '            '
                debug_code = f'''{indent}# 🔍 DEBUG: Variable Distribution Execution
{indent}logger.info("=" * 60)
{indent}logger.info(f"🔍 DEBUG VARIABLE DISTRIBUTION: Starting for variable '{{self.variable_name}}'")
{indent}logger.info(f"🔍 Session ID: {{session_id}}")
{indent}
{indent}# Check what data files exist
{indent}session_dir = f'instance/uploads/{{session_id}}'
{indent}raw_csv = os.path.join(session_dir, 'raw_data.csv')
{indent}unified_csv = os.path.join(session_dir, 'unified_dataset.csv')
{indent}shapefile_zip = os.path.join(session_dir, 'raw_shapefile.zip')
{indent}
{indent}logger.info(f"🔍 Checking data files:")
{indent}logger.info(f"🔍   raw_data.csv: {{'EXISTS' if os.path.exists(raw_csv) else 'NOT FOUND'}}")
{indent}logger.info(f"🔍   unified_dataset.csv: {{'EXISTS' if os.path.exists(unified_csv) else 'NOT FOUND'}}")
{indent}logger.info(f"🔍   raw_shapefile.zip: {{'EXISTS' if os.path.exists(shapefile_zip) else 'NOT FOUND'}}")
{indent}logger.info("=" * 60)
'''
                content = content[:next_line] + debug_code + content[next_line:]
        
        # Add debug in _load_data method
        load_data_pos = content.find('def _load_data(self, session_id: str)')
        if load_data_pos > 0:
            # Add debug at start of method
            method_body = content.find(':', load_data_pos)
            next_line = content.find('\n', method_body) + 1
            
            # Skip docstring if exists
            if '"""' in content[next_line:next_line+10]:
                docstring_end = content.find('"""', next_line)
                docstring_end = content.find('"""', docstring_end + 3) + 3
                next_line = content.find('\n', docstring_end) + 1
            
            indent = '        '
            debug_code = f'''{indent}# 🔍 DEBUG: Loading data for variable distribution
{indent}logger.info("🔍 DEBUG _load_data: Starting data load")
{indent}logger.info(f"🔍 Session ID: {{session_id}}")
'''
            content = content[:next_line] + debug_code + content[next_line:]
        
        # Add debug when CSV is loaded
        csv_loaded = content.find('csv_data = pd.read_csv(csv_path)')
        if csv_loaded > 0:
            next_line = content.find('\n', csv_loaded) + 1
            indent = '            '
            debug_code = f'''{indent}logger.info(f"🔍 DEBUG: CSV loaded successfully")
{indent}logger.info(f"🔍   Shape: {{csv_data.shape}}")
{indent}logger.info(f"🔍   Columns: {{list(csv_data.columns)[:10]}}")
{indent}if self.variable_name in csv_data.columns:
{indent}    logger.info(f"🔍   ✅ Variable '{{self.variable_name}}' FOUND in CSV")
{indent}else:
{indent}    logger.error(f"🔍   ❌ Variable '{{self.variable_name}}' NOT in CSV")
{indent}    # Check case-insensitive
{indent}    matching = [col for col in csv_data.columns if col.lower() == self.variable_name.lower()]
{indent}    if matching:
{indent}        logger.info(f"🔍   💡 Case-insensitive match found: {{matching}}")
'''
            content = content[:next_line] + debug_code + content[next_line:]
        
        with open(var_dist_file, 'w') as f:
            f.write(content)
        print(f"✅ Updated {var_dist_file}")
    
    # 5. Create a deployment script
    deploy_script = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/deploy_debug_logging.sh'
    
    deploy_content = '''#!/bin/bash
# Deploy debug logging to AWS production instances

echo "========================================"
echo "DEPLOYING DEBUG LOGGING TO PRODUCTION"
echo "========================================"

# Production IPs
PROD_IP1="3.21.167.170"
PROD_IP2="18.220.103.20"

# Files to deploy
FILES=(
    "app/core/request_interpreter.py"
    "app/tools/complete_analysis_tools.py"
    "app/tools/visualization_maps_tools.py"
    "app/tools/variable_distribution.py"
)

echo "Deploying to Production Instance 1 ($PROD_IP1)..."
for file in "${FILES[@]}"; do
    echo "  Copying $file..."
    scp -i ~/.ssh/chatmrpt-key.pem "$file" ec2-user@$PROD_IP1:/home/ec2-user/ChatMRPT/$file
done

echo "Deploying to Production Instance 2 ($PROD_IP2)..."
for file in "${FILES[@]}"; do
    echo "  Copying $file..."
    scp -i ~/.ssh/chatmrpt-key.pem "$file" ec2-user@$PROD_IP2:/home/ec2-user/ChatMRPT/$file
done

echo ""
echo "Restarting services..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'sudo systemctl restart chatmrpt'
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP2 'sudo systemctl restart chatmrpt'

echo ""
echo "✅ Debug logging deployed successfully!"
echo ""
echo "Now you can:"
echo "1. Test the risk analysis flow"
echo "2. Try visualization commands"
echo "3. Check logs with: sudo journalctl -u chatmrpt -f"
echo ""
echo "Look for lines starting with '🔍 DEBUG:' in the logs"
'''
    
    with open(deploy_script, 'w') as f:
        f.write(deploy_content)
    os.chmod(deploy_script, 0o755)
    print(f"✅ Created deployment script: {deploy_script}")
    
    print("\n" + "=" * 60)
    print("DEBUG LOGGING ADDED SUCCESSFULLY!")
    print("=" * 60)
    print("\nThe debug logging will track:")
    print("  1. All incoming requests and their parameters")
    print("  2. Tool selection and execution")
    print("  3. File existence checks before/after analysis")
    print("  4. Success/failure of each tool")
    print("  5. Creation of unified_dataset.csv")
    print("\nTo deploy, run:")
    print("  chmod +x deploy_debug_logging.sh")
    print("  ./deploy_debug_logging.sh")

if __name__ == "__main__":
    add_debug_logging()
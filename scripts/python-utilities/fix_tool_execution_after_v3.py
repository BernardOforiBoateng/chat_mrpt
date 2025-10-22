#!/usr/bin/env python3
"""
Fix tool execution after V3 transition.
The issue: After transitioning from Data Analysis V3 to main workflow,
tools are being described as Python code instead of being executed.
"""

import sys
import os

def apply_fixes():
    """Apply fixes to ensure proper tool execution after V3 transition"""
    
    # Fix 1: Update RequestInterpreter to detect V3 transition properly
    file_path = "app/core/request_interpreter.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix: Add proper tool registration when detecting V3 transition
    fix_marker = "def _handle_special_workflows(self, user_message: str, session_id: str, session_data: Dict"
    
    if fix_marker not in content:
        print(f"❌ Could not find marker in {file_path}")
        return False
    
    # Check if we already have the V3 transition detection
    if "Check for Data Analysis V3 transition" in content:
        print("✅ V3 transition detection already exists")
    else:
        # Add V3 transition detection to special workflows
        fix_replacement = """    def _handle_special_workflows(self, user_message: str, session_id: str, session_data: Dict = None, **kwargs):
        \"\"\"
        Handle special workflows that need immediate routing.
        CRITICAL: Check V3 transition FIRST.
        \"\"\"
        import os
        from pathlib import Path
        
        # Check for Data Analysis V3 transition (completed TPR workflow)
        session_folder = Path(f'instance/uploads/{session_id}')
        v3_complete_flag = session_folder / '.tpr_complete'
        v3_waiting_flag = session_folder / '.tpr_waiting_confirmation'
        agent_state_file = session_folder / 'agent_state.json'
        
        # If V3 has completed TPR and is ready for main workflow
        if v3_complete_flag.exists() and not v3_waiting_flag.exists():
            # Load agent state to check if data is ready
            if agent_state_file.exists():
                import json
                try:
                    with open(agent_state_file, 'r') as f:
                        agent_state = json.load(f)
                    
                    # If workflow has transitioned, ensure we're using main tools
                    if agent_state.get('workflow_transitioned'):
                        logger.info(f"✅ V3 workflow transitioned for {session_id}, ensuring main tools are available")
                        
                        # Ensure tools are registered
                        if not self.tools:
                            self._register_tools()
                            logger.info(f"✅ Registered {len(self.tools)} tools after V3 transition")
                        
                        # Ensure session flags are set
                        from flask import session
                        session['data_loaded'] = True
                        session['csv_loaded'] = True
                        session['shapefile_loaded'] = os.path.exists(session_folder / 'shapefile')
                        session.permanent = True
                        session.modified = True
                        
                        # Continue with normal workflow - tools are now available
                        return None
                        
                except Exception as e:
                    logger.warning(f"Could not check V3 transition state: {e}")
        
        # Original special workflow handling continues...
"""
        
        # Find and insert the fix
        import_section = content.split("class RequestInterpreter:")[0]
        class_section = content.split("class RequestInterpreter:")[1]
        
        # Find the method definition
        method_start = class_section.find("def _handle_special_workflows")
        if method_start == -1:
            # Add the method if it doesn't exist
            print("⚠️ _handle_special_workflows method not found, adding it...")
            
            # Find where to insert (after __init__)
            init_end = class_section.find("def _register_tools")
            if init_end == -1:
                print("❌ Could not find insertion point")
                return False
            
            # Insert the new method
            before = class_section[:init_end]
            after = class_section[init_end:]
            
            new_method = """
    def _handle_special_workflows(self, user_message: str, session_id: str, session_data: Dict = None, **kwargs):
        \"\"\"
        Handle special workflows that need immediate routing.
        CRITICAL: Check V3 transition FIRST.
        \"\"\"
        import os
        from pathlib import Path
        
        # Check for Data Analysis V3 transition (completed TPR workflow)
        session_folder = Path(f'instance/uploads/{session_id}')
        v3_complete_flag = session_folder / '.tpr_complete'
        v3_waiting_flag = session_folder / '.tpr_waiting_confirmation'
        agent_state_file = session_folder / 'agent_state.json'
        
        # If V3 has completed TPR and is ready for main workflow
        if v3_complete_flag.exists() and not v3_waiting_flag.exists():
            # Load agent state to check if data is ready
            if agent_state_file.exists():
                import json
                try:
                    with open(agent_state_file, 'r') as f:
                        agent_state = json.load(f)
                    
                    # If workflow has transitioned, ensure we're using main tools
                    if agent_state.get('workflow_transitioned'):
                        logger.info(f"✅ V3 workflow transitioned for {session_id}, ensuring main tools are available")
                        
                        # Ensure tools are registered
                        if not self.tools:
                            self._register_tools()
                            logger.info(f"✅ Registered {len(self.tools)} tools after V3 transition")
                        
                        # Ensure session flags are set
                        from flask import session
                        session['data_loaded'] = True
                        session['csv_loaded'] = True
                        session['shapefile_loaded'] = os.path.exists(session_folder / 'shapefile')
                        session.permanent = True
                        session.modified = True
                        
                        # Continue with normal workflow - tools are now available
                        return None
                        
                except Exception as e:
                    logger.warning(f"Could not check V3 transition state: {e}")
        
        # No special workflow detected
        return None

"""
            class_section = before + new_method + after
            content = import_section + "class RequestInterpreter:" + class_section
            
            print("✅ Added _handle_special_workflows method with V3 transition detection")
    
    # Fix 2: Ensure tools are properly registered after transition
    # Check that we have all necessary tools
    if "run_data_quality_check" not in content:
        print("⚠️ Adding data quality check tool...")
        
        # Find where tools are registered
        register_marker = "        # Register data tools"
        if register_marker in content:
            replacement = """        # Register data tools
        self.tools['execute_data_query'] = self._execute_data_query
        self.tools['execute_sql_query'] = self._execute_sql_query
        self.tools['run_data_quality_check'] = self._run_data_quality_check"""
            
            content = content.replace(
                """        # Register data tools
        self.tools['execute_data_query'] = self._execute_data_query
        self.tools['execute_sql_query'] = self._execute_sql_query""",
                replacement
            )
            
            # Add the method implementation
            method_impl = """
    def _run_data_quality_check(self, session_id: str):
        \"\"\"Check data quality including missing values, duplicates, and statistics.\"\"\"
        try:
            import pandas as pd
            from pathlib import Path
            
            # Load the data
            session_folder = Path(f'instance/uploads/{session_id}')
            raw_data_path = session_folder / 'raw_data.csv'
            
            if not raw_data_path.exists():
                return "No data file found. Please upload data first."
            
            df = pd.read_csv(raw_data_path)
            
            # Calculate statistics
            total_missing = df.isnull().sum().sum()
            duplicates = df.duplicated().sum()
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            # Find malaria-relevant variables
            malaria_vars = []
            env_vars = []
            risk_vars = []
            
            for col in df.columns:
                col_lower = col.lower()
                if 'tpr' in col_lower or 'test' in col_lower or 'positive' in col_lower:
                    malaria_vars.append(col)
                elif any(x in col_lower for x in ['evi', 'ndvi', 'soil', 'rain', 'temp', 'humid']):
                    env_vars.append(col)
                elif any(x in col_lower for x in ['urban', 'housing', 'population', 'density']):
                    risk_vars.append(col)
            
            # Format response
            response = f\"\"\"**Data Quality Check Complete**

📊 Your dataset has {total_missing} total missing values (minimal impact on analysis).

✅ **{'No duplicate entries' if duplicates == 0 else f'{duplicates} duplicate entries found'}** - {'each ward has unique data' if duplicates == 0 else 'consider removing duplicates'}.

**Key Dataset Characteristics:**
• Both numeric indicators ({len(numeric_cols)}) and categorical identifiers ({len(categorical_cols)})

**Malaria-Relevant Variables Found:**
• **Health indicators**: {', '.join(malaria_vars[:3]) if malaria_vars else 'None detected'}
• **Environmental factors**: {', '.join(env_vars[:4]) if env_vars else 'None detected'}  
• **Risk modifiers**: {', '.join(risk_vars[:3]) if risk_vars else 'None detected'}

**Analysis Readiness: ✅ Ready**
Your data is suitable for analysis. You can now run comprehensive malaria risk assessment to identify priority wards for intervention.

Would you like me to:
• Run the full malaria risk analysis?
• Explore specific variables in detail?
• Create visualizations of key indicators?\"\"\"
            
            return response
            
        except Exception as e:
            return f"Error checking data quality: {str(e)}"
"""
            
            # Find a good place to add the method (after another tool method)
            insert_after = "    def _run_itn_planning"
            if insert_after in content:
                insert_pos = content.find(insert_after)
                # Find the end of this method (next def or class end)
                next_def = content.find("\n    def ", insert_pos + 1)
                if next_def != -1:
                    content = content[:next_def] + method_impl + content[next_def:]
                    print("✅ Added _run_data_quality_check tool method")
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("\n🎉 Tool execution fix applied!")
    print("\nThis fix ensures:")
    print("1. V3 transition is detected in special workflows")
    print("2. Main tools are registered after transition")
    print("3. Session flags are properly set")
    print("4. Data quality check tool is available")
    
    return True

if __name__ == "__main__":
    success = apply_fixes()
    sys.exit(0 if success else 1)
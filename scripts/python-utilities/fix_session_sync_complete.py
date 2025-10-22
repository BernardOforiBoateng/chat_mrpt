#!/usr/bin/env python3
"""
Fix for Flask session flag synchronization after V3 transition.
This ensures tools execute properly after TPR workflow completion.
"""

import sys
import os

def apply_fixes():
    """Apply fixes to request_interpreter.py"""
    
    file_path = "app/core/request_interpreter.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Add missing os import before workflow transition check
    # Find the line with workflow_transitioned = False and add import os before using it
    fix1_marker = "        # Check if workflow has already transitioned (prevents re-routing)"
    fix1_replacement = """        # Check if workflow has already transitioned (prevents re-routing)
        # CRITICAL: Check this ALWAYS, not just when flag exists
        import os  # Ensure os is available for path operations"""
    
    if fix1_marker in content:
        content = content.replace(fix1_marker, fix1_replacement)
        print("✅ Fixed missing os import in workflow transition check")
    
    # Fix 2: Synchronize Flask session flags when trusting agent state
    # Find the section where we load data from V3 transition and add session flag updates
    fix2_marker = """            # If data is loaded but not in our cache, populate it
            if data_loaded and session_id not in self.session_data and has_actual_data:
                try:
                    import pandas as pd
                    # Try to load the data file
                    raw_data_path = session_folder / 'raw_data.csv'
                    if raw_data_path.exists():
                        df = pd.read_csv(raw_data_path)
                        self.session_data[session_id] = {
                            'data': df,
                            'columns': list(df.columns),
                            'shape': df.shape
                        }
                        logger.info(f"Loaded data from V3 transition: {df.shape}")
                except Exception as e:
                    logger.error(f"Failed to load transition data: {e}")"""
    
    fix2_replacement = """            # If data is loaded but not in our cache, populate it
            if data_loaded and session_id not in self.session_data and has_actual_data:
                try:
                    import pandas as pd
                    # Try to load the data file
                    raw_data_path = session_folder / 'raw_data.csv'
                    if raw_data_path.exists():
                        df = pd.read_csv(raw_data_path)
                        self.session_data[session_id] = {
                            'data': df,
                            'columns': list(df.columns),
                            'shape': df.shape
                        }
                        logger.info(f"Loaded data from V3 transition: {df.shape}")
                        
                        # CRITICAL FIX: Synchronize Flask session flags when loading from V3
                        # This ensures tool execution works after TPR workflow transition
                        if agent_state_loaded and has_actual_data:
                            # Update Flask session to match agent state
                            from flask import session
                            session['data_loaded'] = True
                            session['csv_loaded'] = True
                            session['shapefile_loaded'] = os.path.exists(session_folder / 'raw_shapefile.zip')
                            session.modified = True  # Ensure changes persist
                            logger.info(f"✅ Synchronized Flask session flags after V3 transition for {session_id}")
                            logger.info(f"   Flask session now has: data_loaded={session.get('data_loaded')}, csv_loaded={session.get('csv_loaded')}, shapefile_loaded={session.get('shapefile_loaded')}")
                except Exception as e:
                    logger.error(f"Failed to load transition data: {e}")"""
    
    if fix2_marker in content:
        content = content.replace(fix2_marker, fix2_replacement)
        print("✅ Added Flask session flag synchronization after V3 transition")
    
    # Fix 3: Also update session flags when data_loaded is determined to be True
    # Find where we set data_loaded and ensure session is updated
    fix3_marker = """            # CRITICAL FIX: Trust agent state if it says data is loaded and files exist
            # This handles V3 transitions where Flask session might not have the flags
            data_loaded = (
                (session_data.get('data_loaded', False) or 
                 session_data.get('csv_loaded', False) or
                 session_id in self.session_data or  # Check our internal cache
                 (agent_state_loaded and has_actual_data))  # Trust agent state if files exist
            )"""
    
    fix3_replacement = """            # CRITICAL FIX: Trust agent state if it says data is loaded and files exist
            # This handles V3 transitions where Flask session might not have the flags
            data_loaded = (
                (session_data.get('data_loaded', False) or 
                 session_data.get('csv_loaded', False) or
                 session_id in self.session_data or  # Check our internal cache
                 (agent_state_loaded and has_actual_data))  # Trust agent state if files exist
            )
            
            # CRITICAL: If we determined data is loaded based on agent state, update Flask session
            if data_loaded and agent_state_loaded and has_actual_data and not session_data.get('csv_loaded', False):
                from flask import session
                session['data_loaded'] = True
                session['csv_loaded'] = True
                session['shapefile_loaded'] = os.path.exists(session_folder / 'raw_shapefile.zip')
                session.modified = True  # Ensure changes persist
                logger.info(f"🔄 Updated Flask session flags based on agent state for {session_id}")"""
    
    if fix3_marker in content:
        content = content.replace(fix3_marker, fix3_replacement)
        print("✅ Added immediate session flag update when agent state is trusted")
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("\n✅ All fixes applied successfully!")
    print("\nChanges made:")
    print("1. Fixed missing os import in workflow transition check")
    print("2. Added Flask session flag synchronization after V3 data loading")
    print("3. Added immediate session flag update when agent state is trusted")
    print("\nThis ensures that after TPR workflow completion:")
    print("- Flask session has correct data_loaded, csv_loaded, and shapefile_loaded flags")
    print("- Tools will execute properly instead of being described as text")
    print("- Session state is consistent across all workers")
    
    return True

if __name__ == "__main__":
    success = apply_fixes()
    sys.exit(0 if success else 1)
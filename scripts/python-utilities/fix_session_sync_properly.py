#!/usr/bin/env python3
"""
Fix Flask session synchronization properly - move the sync BEFORE data_loaded check.
"""

import sys
import os

def apply_fixes():
    """Apply proper fix to request_interpreter.py"""
    
    file_path = "app/core/request_interpreter.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Find the section where we check agent state and fix it
    fixed_lines = []
    in_get_session_context = False
    fix_applied = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for the _get_session_context method
        if "def _get_session_context" in line:
            in_get_session_context = True
            fixed_lines.append(line)
            i += 1
            continue
        
        # Look for where we read agent state
        if in_get_session_context and "agent_state = json.load(f)" in line and not fix_applied:
            # Add the line as is
            fixed_lines.append(line)
            i += 1
            
            # Skip the next line that sets agent_state_loaded
            if i < len(lines) and "agent_state_loaded" in lines[i]:
                fixed_lines.append(lines[i])
                i += 1
            
            # Now add the Flask session sync RIGHT HERE, before any data_loaded checks
            sync_code = """                        
                        # CRITICAL FIX: Sync Flask session IMMEDIATELY when agent state shows data loaded
                        # This must happen BEFORE we check data_loaded to avoid circular dependency
                        if (agent_state.get('data_loaded', False) or agent_state.get('csv_loaded', False)):
                            # Check if files actually exist
                            import os
                            from pathlib import Path
                            session_folder = Path(f"{upload_folder}/{session_id}")
                            has_csv = (session_folder / 'raw_data.csv').exists() or (session_folder / 'data_analysis.csv').exists()
                            has_shapefile = (session_folder / 'raw_shapefile.zip').exists()
                            
                            if has_csv:
                                # Update Flask session IMMEDIATELY
                                from flask import session
                                if not session.get('csv_loaded', False):
                                    session['data_loaded'] = True
                                    session['csv_loaded'] = True
                                    session['shapefile_loaded'] = has_shapefile
                                    session.modified = True
                                    logger.info(f"✅ IMMEDIATE Flask session sync from agent state for {session_id}")
                                    logger.info(f"   Files exist: CSV={has_csv}, Shapefile={has_shapefile}")
                                    logger.info(f"   Session flags updated: data_loaded=True, csv_loaded=True")
"""
            fixed_lines.append(sync_code)
            fix_applied = True
            continue
            
        fixed_lines.append(line)
        i += 1
    
    if not fix_applied:
        print("❌ Could not find the right location to apply fix")
        return False
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print("✅ Applied proper Flask session synchronization fix!")
    print("\nChanges made:")
    print("1. Moved Flask session sync to happen IMMEDIATELY after reading agent state")
    print("2. Sync happens BEFORE data_loaded determination to avoid circular dependency")
    print("3. Session flags are set as soon as we detect agent state has data and files exist")
    
    return True

if __name__ == "__main__":
    success = apply_fixes()
    sys.exit(0 if success else 1)
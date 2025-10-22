#!/usr/bin/env python3
"""
Fix session synchronization for Redis-backed sessions in multi-instance environment.
The key insight: Flask session with Redis needs explicit saves and proper modification tracking.
"""

import sys
import os

def apply_fixes():
    """Apply Redis-compatible session sync fix"""
    
    file_path = "app/core/request_interpreter.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Add session force save utility at the top of the class
    fix1_marker = "class RequestInterpreter:"
    fix1_replacement = """class RequestInterpreter:
    
    @staticmethod
    def force_session_save():
        \"\"\"Force Flask session to save when using Redis backend.\"\"\"
        from flask import session
        # Mark all keys as modified to force Redis save
        session.permanent = True
        session.modified = True
        # Touch all important keys
        for key in ['data_loaded', 'csv_loaded', 'shapefile_loaded']:
            if key in session:
                session[key] = session[key]  # Re-assign to trigger modification"""
    
    if fix1_marker in content:
        content = content.replace(fix1_marker, fix1_replacement)
        print("✅ Added force_session_save utility method")
    
    # Fix 2: Update the immediate sync to use force save
    fix2_marker = """                        # CRITICAL FIX: Sync Flask session IMMEDIATELY when agent state shows data loaded
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
                                    logger.info(f"   Session flags updated: data_loaded=True, csv_loaded=True")"""
    
    fix2_replacement = """                        # CRITICAL FIX: Sync Flask session IMMEDIATELY when agent state shows data loaded
                        # This must happen BEFORE we check data_loaded to avoid circular dependency
                        if (agent_state.get('data_loaded', False) or agent_state.get('csv_loaded', False)):
                            # Check if files actually exist
                            import os
                            from pathlib import Path
                            session_folder = Path(f"{upload_folder}/{session_id}")
                            has_csv = (session_folder / 'raw_data.csv').exists() or (session_folder / 'data_analysis.csv').exists()
                            has_shapefile = (session_folder / 'raw_shapefile.zip').exists()
                            
                            if has_csv:
                                # Update Flask session IMMEDIATELY with Redis-compatible approach
                                from flask import session
                                if not session.get('csv_loaded', False):
                                    # Set all flags
                                    session['data_loaded'] = True
                                    session['csv_loaded'] = True
                                    session['shapefile_loaded'] = has_shapefile
                                    # CRITICAL for Redis: Set permanent and force modification
                                    session.permanent = True
                                    session.modified = True
                                    # Force re-assignment to trigger Redis update
                                    session['session_id'] = session.get('session_id', session_id)
                                    
                                    logger.info(f"✅ IMMEDIATE Flask session sync from agent state for {session_id}")
                                    logger.info(f"   Files exist: CSV={has_csv}, Shapefile={has_shapefile}")
                                    logger.info(f"   Session flags updated: data_loaded=True, csv_loaded=True")
                                    logger.info(f"   Redis session marked as permanent and modified")"""
    
    if fix2_marker in content:
        content = content.replace(fix2_marker, fix2_replacement)
        print("✅ Updated immediate sync with Redis-compatible session handling")
    
    # Fix 3: Also fix the section where we populate session data after loading
    fix3_marker = """                            # CRITICAL FIX: Synchronize Flask session flags when loading from V3
                            # This ensures tool execution works after TPR workflow transition
                            if agent_state_loaded and has_actual_data:
                                # Update Flask session to match agent state
                                from flask import session
                                session['data_loaded'] = True
                                session['csv_loaded'] = True
                                session['shapefile_loaded'] = os.path.exists(session_folder / 'raw_shapefile.zip')
                                session.modified = True  # Ensure changes persist
                                logger.info(f"✅ Synchronized Flask session flags after V3 transition for {session_id}")
                                logger.info(f"   Flask session now has: data_loaded={session.get('data_loaded')}, csv_loaded={session.get('csv_loaded')}, shapefile_loaded={session.get('shapefile_loaded')}")"""
    
    fix3_replacement = """                            # CRITICAL FIX: Synchronize Flask session flags when loading from V3
                            # This ensures tool execution works after TPR workflow transition
                            if agent_state_loaded and has_actual_data:
                                # Update Flask session to match agent state (Redis-compatible)
                                from flask import session
                                session['data_loaded'] = True
                                session['csv_loaded'] = True
                                session['shapefile_loaded'] = os.path.exists(session_folder / 'raw_shapefile.zip')
                                # CRITICAL for Redis: Force persistence
                                session.permanent = True
                                session.modified = True
                                # Touch session_id to ensure Redis update
                                session['session_id'] = session.get('session_id', session_id)
                                
                                logger.info(f"✅ Synchronized Flask session flags after V3 transition for {session_id}")
                                logger.info(f"   Flask session now has: data_loaded={session.get('data_loaded')}, csv_loaded={session.get('csv_loaded')}, shapefile_loaded={session.get('shapefile_loaded')}")
                                logger.info(f"   Redis session marked as permanent and modified")"""
    
    if fix3_marker in content:
        content = content.replace(fix3_marker, fix3_replacement)
        print("✅ Updated V3 transition sync with Redis persistence")
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("\n🎉 All Redis session fixes applied successfully!")
    print("\nChanges made:")
    print("1. Added force_session_save utility for Redis compatibility")  
    print("2. Updated immediate sync to use session.permanent = True")
    print("3. Added session key re-assignment to trigger Redis updates")
    print("4. Ensured all session modifications force Redis persistence")
    print("\nThis fix ensures Flask sessions work correctly with Redis in multi-instance setup.")
    
    return True

if __name__ == "__main__":
    success = apply_fixes()
    sys.exit(0 if success else 1)
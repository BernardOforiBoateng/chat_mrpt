#!/usr/bin/env python3
"""
Fix TPR Redis serialization by ensuring all data is JSON-serializable
"""

import json

def create_patch():
    patch_content = '''# Patch for app/tpr_module/core/tpr_state_manager.py
# Add this import at the top
import json

# Replace the to_dict method in ConversationState class with:
def to_dict(self) -> Dict:
    """Convert to dictionary for Redis serialization."""
    # Custom serialization to ensure Redis compatibility
    data = {}
    
    # Handle each field explicitly
    data['session_id'] = self.session_id
    data['start_time'] = self.start_time.isoformat() if self.start_time else None
    data['current_stage'] = self.current_stage
    data['file_path'] = self.file_path
    data['file_metadata'] = self.file_metadata if isinstance(self.file_metadata, dict) else {}
    data['selected_state'] = self.selected_state
    data['selected_facility_level'] = self.selected_facility_level
    data['selected_age_group'] = self.selected_age_group
    data['alternative_calculation_requested'] = bool(self.alternative_calculation_requested)
    data['threshold_violations_found'] = bool(self.threshold_violations_found)
    data['tpr_results'] = self.tpr_results if isinstance(self.tpr_results, list) else []
    data['environmental_variables'] = self.environmental_variables if isinstance(self.environmental_variables, dict) else {}
    data['output_files'] = self.output_files if isinstance(self.output_files, dict) else {}
    data['interaction_count'] = int(self.interaction_count)
    data['clarification_count'] = int(self.clarification_count)
    data['workflow_stage'] = self.workflow_stage
    
    # Include extra attrs if any
    if self._extra_attrs and isinstance(self._extra_attrs, dict):
        data.update(self._extra_attrs)
    
    # Ensure everything is JSON serializable
    try:
        json.dumps(data)  # Test serialization
        return data
    except TypeError as e:
        # If serialization fails, convert problematic values to strings
        for key, value in data.items():
            try:
                json.dumps(value)
            except TypeError:
                data[key] = str(value)
        return data

# Also update the __init__ method in TPRStateManager to better handle deserialization:
# In the try block where it loads from session, after creating ConversationState:

                # Restore other attributes safely
                for key, value in saved_state.items():
                    if hasattr(self.state, key) and key not in ['session_id', 'start_time', 'current_stage']:
                        try:
                            setattr(self.state, key, value)
                        except Exception as e:
                            logger.warning(f"Could not restore {key}: {e}")
                            setattr(self.state, key, None)
'''
    
    print("TPR Redis Fix Created")
    print("=" * 50)
    print("This fix ensures all TPR state data is JSON-serializable")
    print("Apply by updating the to_dict() method in ConversationState class")
    
    return patch_content

if __name__ == "__main__":
    create_patch()
#!/usr/bin/env python3
"""
Fix TPR Redis serialization issue
Patches the TPR state manager to properly serialize for Redis
"""

patch_content = '''
# Add this method to TPRStateManager class in tpr_state_manager.py

def _serialize_for_redis(self, state_dict):
    """Convert state dict to Redis-compatible format."""
    import json
    from datetime import datetime
    
    def serialize_value(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (list, dict, str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    # Deep copy and convert
    serialized = {}
    for key, value in state_dict.items():
        if isinstance(value, dict):
            serialized[key] = {k: serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            serialized[key] = [serialize_value(v) for v in value]
        else:
            serialized[key] = serialize_value(value)
    
    return serialized

def _deserialize_from_redis(self, state_dict):
    """Convert Redis data back to proper types."""
    from datetime import datetime
    
    # Handle datetime strings
    if 'start_time' in state_dict and isinstance(state_dict['start_time'], str):
        try:
            state_dict['start_time'] = datetime.fromisoformat(state_dict['start_time'])
        except:
            pass
    
    return state_dict
'''

print("TPR Redis Serialization Fix")
print("=" * 50)
print("This fix ensures TPR state data is properly serialized for Redis storage")
print()
print("The issue: Complex objects (datetime, dataclasses) aren't JSON serializable")
print("The fix: Convert all data to Redis-compatible types before storing")
print()
print("To apply this fix:")
print("1. Add the methods above to TPRStateManager class")
print("2. Update save_state() to use _serialize_for_redis()")
print("3. Update get_state() to use _deserialize_from_redis()")
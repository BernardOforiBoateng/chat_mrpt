#!/usr/bin/env python3
"""
Fix TPR handler for multi-worker environments
Makes TPR handler stateless by always loading from session
"""

# Original problematic code:
# _tpr_handlers = {}
# 
# def get_tpr_handler(session_id: str) -> TPRHandler:
#     if session_id not in _tpr_handlers:
#         _tpr_handlers[session_id] = TPRHandler(session_id)
#     return _tpr_handlers[session_id]

# Fixed code for multi-worker:
fixed_code = '''
# Remove global dictionary - don't cache handlers in memory
# _tpr_handlers = {}  # REMOVE THIS LINE

def get_tpr_handler(session_id: str) -> TPRHandler:
    """
    Get TPR handler for a session.
    Always creates new instance to ensure session state is loaded from Redis.
    """
    # Always create new handler - it will load state from session
    return TPRHandler(session_id)

def cleanup_tpr_handler(session_id: str):
    """Clean up TPR handler for a session."""
    # No longer needed since we don't cache handlers
    pass
'''

print("TPR Multi-Worker Fix")
print("=" * 50)
print("Problem: Global _tpr_handlers dictionary doesn't work with multiple workers")
print("Solution: Always create new TPRHandler that loads state from Redis session")
print()
print("To apply this fix:")
print("1. Comment out or remove the '_tpr_handlers = {}' line")
print("2. Update get_tpr_handler() to always return new TPRHandler(session_id)")
print("3. This ensures each worker loads the latest state from Redis")
print()
print("File to modify: app/tpr_module/integration/tpr_handler.py")
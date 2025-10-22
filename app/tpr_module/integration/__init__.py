"""
TPR Integration Module.

This module handles the integration of TPR workflow with the main ChatMRPT application.
"""

import os
import logging
from .tpr_handler import TPRHandler
from .upload_detector import TPRUploadDetector
from .tpr_workflow_router import TPRWorkflowRouter

logger = logging.getLogger(__name__)

# Handler management functions
_tpr_handlers = {}

def get_tpr_handler(session_id: str):
    """
    Get or create a TPR handler for a session.
    
    Args:
        session_id: Session ID
        
    Returns:
        TPR handler instance (LLM-based ONLY - no fallback)
    """
    if session_id not in _tpr_handlers:
        print(f"\n{'='*60}")
        print(f"🎯 CREATING TPR HANDLER")
        print(f"{'='*60}")
        
        # ALWAYS use LLM mode when vLLM is configured
        use_vllm = os.environ.get('USE_VLLM', 'false').lower() == 'true'
        use_llm = use_vllm or os.environ.get('USE_LLM_TPR', 'false').lower() == 'true'
        
        print(f"USE_VLLM env var: {os.environ.get('USE_VLLM', 'not set')}")
        print(f"USE_LLM_TPR env var: {os.environ.get('USE_LLM_TPR', 'not set')}")
        print(f"Decision: {'LLM Mode' if use_llm else 'Legacy Mode'}")
        
        if use_llm or use_vllm:  # Force LLM mode when vLLM is enabled
            # FORCE LLM mode - NO FALLBACK
            from .llm_tpr_handler import LLMTPRHandler
            _tpr_handlers[session_id] = LLMTPRHandler(session_id)
            print(f"✅ Created LLMTPRHandler (using vLLM/Qwen3)")
            logger.info(f"Created LLMTPRHandler for session {session_id}")
        else:
            # COMMENTED OUT - NO FALLBACK TO OLD IMPLEMENTATION
            print(f"❌ ERROR: Legacy mode disabled - LLM mode is required!")
            raise ValueError("Legacy TPR handler is disabled. Set USE_VLLM=true or USE_LLM_TPR=true")
            # from .tpr_handler import TPRHandler
            # _tpr_handlers[session_id] = TPRHandler(session_id)
            # logger.info(f"Created legacy TPRHandler for session {session_id}")
        
        print(f"{'='*60}\n")
    
    return _tpr_handlers[session_id]

def cleanup_tpr_handler(session_id: str):
    """
    Clean up TPR handler for a session.
    
    Args:
        session_id: Session ID
    """
    if session_id in _tpr_handlers:
        del _tpr_handlers[session_id]
        logger.info(f"Cleaned up TPR handler for session {session_id}")

__all__ = [
    'TPRHandler',
    'TPRUploadDetector',
    'TPRWorkflowRouter',
    'get_tpr_handler',
    'cleanup_tpr_handler'
]
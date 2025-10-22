"""
TPR (Test Positivity Rate) Module for ChatMRPT

This module provides a conversational interface for processing NMEP Excel files,
calculating TPR values, and generating analysis-ready datasets with environmental variables.

Key Features:
- Interactive TPR calculation with user guidance
- Zone-aware environmental variable extraction
- Three output files: TPR analysis, main CSV, and shapefile
- Seamless integration with main ChatMRPT pipeline
"""

__version__ = '1.0.0'
__author__ = 'ChatMRPT Team'

# Module exports
from .core.tpr_conversation_manager import TPRConversationManager
from .data.nmep_parser import NMEPParser
from .data.geopolitical_zones import get_zone_for_state, get_variables_for_state

__all__ = [
    'TPRConversationManager',
    'NMEPParser', 
    'get_zone_for_state',
    'get_variables_for_state'
]
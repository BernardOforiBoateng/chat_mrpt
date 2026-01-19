"""
Data Analysis V3 Module
Clean implementation following AgenticDataAnalysis architecture
"""

from .core.agent import DataAnalysisAgent
from .core.state import DataAnalysisState
from .tools.python_tool import analyze_data

__all__ = [
    'DataAnalysisAgent',
    'DataAnalysisState', 
    'analyze_data'
]

# Module version
__version__ = '3.0.0'
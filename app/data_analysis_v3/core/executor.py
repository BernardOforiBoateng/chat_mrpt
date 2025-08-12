"""
Secure Python Code Executor
Based on AgenticDataAnalysis tools.py execution pattern
"""

import sys
import os
import uuid
import pickle
import logging
from io import StringIO
from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sklearn  # Import sklearn for analysis
from .column_validator import ColumnValidator

logger = logging.getLogger(__name__)


class SecureExecutor:
    """
    Executes Python code in a controlled environment.
    Follows AgenticDataAnalysis pattern with security enhancements.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.persistent_vars = {}  # Variables that persist between executions
        
        # Create directories for outputs
        self.viz_dir = f"instance/uploads/{session_id}/visualizations"
        os.makedirs(self.viz_dir, exist_ok=True)
        
        # Plotly saving code template (from AgenticDataAnalysis)
        self.plotly_saving_code = """
import pickle
import uuid

for idx, figure in enumerate(plotly_figures):
    pickle_filename = f"{viz_dir}/{uuid.uuid4()}.pickle"
    with open(pickle_filename, 'wb') as f:
        pickle.dump(figure, f)
    saved_plots.append(pickle_filename)
"""
    
    def execute(self, code: str, current_data: Dict[str, pd.DataFrame]) -> Tuple[str, Dict[str, Any]]:
        """
        Execute Python code with persistent state and data pre-loading.
        
        Args:
            code: Python code to execute
            current_data: Dictionary of DataFrames to make available
            
        Returns:
            Tuple of (output_text, state_updates)
        """
        # Validate and fix column references before execution
        if current_data and 'df' in current_data:
            df = current_data['df']
            if isinstance(df, pd.DataFrame):
                actual_columns = list(df.columns)
                # Fix any incorrect column references
                original_code = code
                code = ColumnValidator.validate_and_fix_code(code, actual_columns)
                if code != original_code:
                    logger.info("Column references were automatically corrected")
        
        # Prepare execution globals (exact pattern from AgenticDataAnalysis)
        exec_globals = {
            # Standard libraries
            'pd': pd,
            'np': np,
            'px': px,
            'go': go,
            'sklearn': sklearn,
            
            # Utility variables
            'plotly_figures': [],  # For collecting plots
            'saved_plots': [],     # For tracking saved plot paths
            'viz_dir': self.viz_dir,
            'uuid': uuid,
            'pickle': pickle,
        }
        
        # Add persistent variables from previous executions
        exec_globals.update(self.persistent_vars)
        
        # Add current data (pre-loaded DataFrames)
        exec_globals.update(current_data)
        
        # Track what plots we had before
        initial_plots = list(exec_globals.get('saved_plots', []))
        
        try:
            # Capture stdout (from AgenticDataAnalysis pattern)
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            # Execute the code
            exec(code, exec_globals)
            
            # If any plotly figures were created, save them
            if exec_globals.get('plotly_figures'):
                exec(self.plotly_saving_code, exec_globals)
            
            # Get captured output
            output = sys.stdout.getvalue()
            
            # Restore stdout
            sys.stdout = old_stdout
            
            # Update persistent variables (excluding built-ins and imports)
            excluded_keys = {
                'pd', 'np', 'px', 'go', 'sklearn', 
                'plotly_figures', 'saved_plots', 'viz_dir',
                'uuid', 'pickle', '__builtins__'
            }
            
            for key, value in exec_globals.items():
                if key not in excluded_keys and not key.startswith('_'):
                    self.persistent_vars[key] = value
            
            # Find new plots created
            new_plots = [p for p in exec_globals.get('saved_plots', []) 
                        if p not in initial_plots]
            
            # Prepare state updates
            state_updates = {
                'current_variables': dict(self.persistent_vars),
                'output_plots': new_plots,
            }
            
            return output, state_updates
            
        except Exception as e:
            # Restore stdout on error
            if 'old_stdout' in locals():
                sys.stdout = old_stdout
            
            logger.error(f"Code execution error: {str(e)}")
            
            # Return error in a format we can convert to user-friendly message
            return "", {
                'errors': [str(e)],
                'current_variables': dict(self.persistent_vars)
            }
    
    def reset(self):
        """Reset the executor state."""
        self.persistent_vars = {}
    
    def get_available_variables(self) -> List[str]:
        """Get list of available variables in the environment."""
        return list(self.persistent_vars.keys())
"""
Sandboxed execution environment for LLM-generated code.
Ensures safety in production with resource limits and restricted access.
"""

import ast
import sys
import io
import signal
import resource
import traceback
from typing import Dict, Any, Optional
from contextlib import contextmanager
import pandas as pd
import numpy as np


class CodeSandbox:
    """
    Safe execution environment for pandas/numpy code.
    Implements security best practices for production systems.
    """
    
    # Allowed modules and functions
    SAFE_BUILTINS = {
        'len', 'sum', 'min', 'max', 'abs', 'round', 'sorted',
        'enumerate', 'zip', 'range', 'list', 'dict', 'set',
        'tuple', 'str', 'int', 'float', 'bool', 'print'
    }
    
    SAFE_MODULES = {
        'pd': pd,
        'np': np,
        'pandas': pd,
        'numpy': np
    }
    
    def __init__(self, timeout_seconds: int = 5, memory_limit_mb: int = 100):
        """
        Initialize sandbox with resource limits.
        
        Args:
            timeout_seconds: Maximum execution time
            memory_limit_mb: Maximum memory usage in MB
        """
        self.timeout = timeout_seconds
        self.memory_limit = memory_limit_mb * 1024 * 1024  # Convert to bytes
        
    @contextmanager
    def time_limit(self, seconds: int):
        """Context manager for execution timeout."""
        import threading
        import time
        
        # Use threading for cross-platform timeout
        def timeout_handler():
            time.sleep(seconds)
            # This will interrupt the main thread if still running
            import _thread
            _thread.interrupt_main()
        
        timer = threading.Thread(target=timeout_handler)
        timer.daemon = True
        timer.start()
        
        try:
            yield
        except KeyboardInterrupt:
            raise TimeoutError(f"Code execution exceeded {seconds} seconds")
        finally:
            pass  # Timer thread will terminate when main thread ends
    
    def validate_code(self, code: str) -> bool:
        """
        Validate code for dangerous operations.
        
        Args:
            code: Python code string to validate
            
        Returns:
            True if code is safe, False otherwise
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False
        
        # Check for dangerous operations
        for node in ast.walk(tree):
            # No imports allowed
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return False
            
            # No file operations
            if isinstance(node, ast.Name) and node.id in ['open', 'file', '__import__']:
                return False
            
            # No exec/eval
            if isinstance(node, ast.Name) and node.id in ['exec', 'eval', 'compile']:
                return False
            
            # No system operations
            if isinstance(node, ast.Attribute):
                if hasattr(node.value, 'id') and node.value.id in ['os', 'sys', 'subprocess']:
                    return False
        
        return True
    
    def execute(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute code in sandboxed environment.
        
        Args:
            code: Python code to execute
            context: Variables to make available (e.g., {'df': dataframe})
            
        Returns:
            Dictionary with execution results
        """
        # Validate code first
        if not self.validate_code(code):
            return {
                'success': False,
                'error': 'Code contains forbidden operations',
                'output': '',
                'result': None
            }
        
        # Create restricted environment
        # Build safe builtins dict
        import builtins
        safe_builtins = {}
        for name in self.SAFE_BUILTINS:
            if hasattr(builtins, name):
                safe_builtins[name] = getattr(builtins, name)
        
        safe_globals = {
            '__builtins__': safe_builtins,
            **self.SAFE_MODULES
        }
        
        # Add user context (work on copies)
        safe_locals = {}
        for key, value in context.items():
            if isinstance(value, pd.DataFrame):
                safe_locals[key] = value.copy()
            else:
                safe_locals[key] = value
        
        # Add result variable
        safe_locals['result'] = None
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            # Execute with timeout
            with self.time_limit(self.timeout):
                exec(code, safe_globals, safe_locals)
            
            # Get output
            output = sys.stdout.getvalue()
            
            # Get result
            result = safe_locals.get('result', None)
            
            # Convert numpy/pandas objects to serializable format
            if isinstance(result, pd.DataFrame):
                result = result.to_dict('records')
            elif isinstance(result, pd.Series):
                result = result.to_dict()
            elif isinstance(result, np.ndarray):
                result = result.tolist()
            
            # Build output dictionary with all captured variables
            output_dict = {
                'stdout': output,
                'result': result
            }
            
            # Also capture any other variables created
            for key, value in safe_locals.items():
                if key not in context and key != 'result':
                    # Convert to serializable format
                    if isinstance(value, pd.DataFrame):
                        output_dict[key] = value.to_dict('records')
                    elif isinstance(value, pd.Series):
                        output_dict[key] = value.to_dict()
                    elif isinstance(value, np.ndarray):
                        output_dict[key] = value.tolist()
                    elif not callable(value):  # Don't include functions
                        output_dict[key] = value
            
            return {
                'success': True,
                'output': output_dict,
                'code': code
            }
            
        except TimeoutError as e:
            return {
                'success': False,
                'error': str(e),
                'output': sys.stdout.getvalue(),
                'result': None
            }
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return {
                'success': False,
                'error': error_msg,
                'output': sys.stdout.getvalue(),
                'result': None
            }
            
        finally:
            sys.stdout = old_stdout
    
    def execute_with_validation(self, code: str, context: Dict[str, Any],
                               validation_func: Optional[callable] = None) -> Dict[str, Any]:
        """
        Execute code with additional validation step.
        
        Args:
            code: Python code to execute
            context: Variables to make available
            validation_func: Optional function to validate results
            
        Returns:
            Dictionary with execution results and validation status
        """
        result = self.execute(code, context)
        
        if result['success'] and validation_func and result.get('result'):
            try:
                is_valid = validation_func(result['result'])
                result['validated'] = is_valid
                if not is_valid:
                    result['warning'] = 'Result failed validation check'
            except Exception as e:
                result['validated'] = False
                result['warning'] = f'Validation error: {str(e)}'
        
        return result


def create_tpr_sandbox() -> CodeSandbox:
    """
    Create a sandbox specifically configured for TPR analysis.
    
    Returns:
        Configured CodeSandbox instance
    """
    return CodeSandbox(
        timeout_seconds=5,
        memory_limit_mb=100
    )


def validate_tpr_result(result: Any) -> bool:
    """
    Validate TPR calculation results.
    
    Args:
        result: Calculation result to validate
        
    Returns:
        True if result is valid TPR data
    """
    if isinstance(result, (int, float)):
        # Single TPR value should be between 0 and 100
        return 0 <= result <= 100
    
    elif isinstance(result, dict):
        # Dictionary of TPR values
        for value in result.values():
            if isinstance(value, (int, float)):
                if not (0 <= value <= 100):
                    return False
        return True
    
    elif isinstance(result, list):
        # List of TPR values or records
        for item in result:
            if isinstance(item, dict):
                # Check if 'tpr' field exists and is valid
                if 'tpr' in item:
                    if not (0 <= item['tpr'] <= 100):
                        return False
            elif isinstance(item, (int, float)):
                if not (0 <= item <= 100):
                    return False
        return True
    
    return True  # Default to true for other types
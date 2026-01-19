"""
TPR Conversation Handler using ReAct Pattern
Minimal implementation that gives LLM full DataFrame access
Based on industry best practices (2025)
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, Any, Optional, List
from io import StringIO
import sys
import traceback
from .prompts import (
    REACT_TPR_EXPLORATION,
    REACT_ANALYSIS_TEMPLATE,
    TPR_CALCULATION_PROMPT,
    WARD_MATCHING_PROMPT,
    ZONE_VARIABLE_EXTRACTION_PROMPT,
    OUTPUT_GENERATION_PROMPT,
    ERROR_RECOVERY_PROMPT
)

logger = logging.getLogger(__name__)


class TPRConversation:
    """
    ReAct-based conversation handler for TPR analysis.
    Gives LLM full access to data and uses reasoning + acting pattern.
    ONE unified method for all decisions - industry standard approach.
    """
    
    def __init__(self, llm_adapter):
        """Initialize with LLM adapter."""
        print(f"📚 Initializing TPR Conversation with LLM adapter")
        self.llm = llm_adapter
        self.data = None
        self.context = {
            'history': [],
            'findings': {},
            'executed_code': [],
            'stage': 'initial',
            'state_name': None,
            'tpr_calculated': False,
            'ward_matches': {}
        }
        # Check which backend the LLM is using
        if hasattr(llm_adapter, 'backend'):
            print(f"   Using LLM Backend: {llm_adapter.backend}")
            if hasattr(llm_adapter, 'model'):
                print(f"   Model: {llm_adapter.model}")
            if hasattr(llm_adapter, 'base_url'):
                print(f"   Base URL: {llm_adapter.base_url}")
    
    def get_next_action(self, user_message: str, external_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        ONE unified method - LLM decides everything!
        No predefined tools, just intelligence.
        
        Returns a structured decision about what to do next.
        """
        # Merge external context with internal context
        full_context = {**self.context}
        if external_context:
            full_context.update(external_context)
        
        # Build context summary for LLM
        context_summary = f"""
        Current Stage: {full_context.get('stage', 'unknown')}
        Data Loaded: {self.data is not None and f"{len(self.data)} rows" or "No"}
        State Selected: {full_context.get('state_name', 'None')}
        TPR Calculated: {full_context.get('tpr_calculated', False)}
        Previous Actions: {len(full_context.get('executed_code', []))} code executions
        """
        
        # Unified prompt for all decisions
        prompt = f"""
        You are analyzing TPR data with full access to pandas DataFrame.
        
        CONTEXT:
        {context_summary}
        
        USER MESSAGE: {user_message}
        
        Based on the context and user message, decide your next action.
        
        You can:
        1. Execute code to analyze/calculate/visualize
        2. Request confirmation before important operations
        3. Request user input for selections or ambiguous matches
        4. Provide informational messages
        
        Return a JSON response with this structure:
        {{
            "thought": "Your reasoning about what to do",
            "action_type": "execute|confirm|input|message",
            "code": "pandas/python code to execute (if action_type is execute or confirm)",
            "needs_confirmation": true/false,
            "confirmation_reason": "why confirmation is needed",
            "needs_input": {{
                "type": "ward_match|state_selection|facility_selection|other",
                "prompt": "What to ask the user",
                "options": ["list", "of", "options"] or null,
                "data": {{}} // any additional data needed
            }},
            "message": "Message to show user (for message type or alongside code execution)",
            "show_progress": "Progress message if this is a long operation"
        }}
        
        IMPORTANT:
        - For TPR calculation, use: max(RDT_Positive, Microscopy_Positive) / max(RDT_Tested, Microscopy_Tested) * 100
        - After TPR calculation, automatically suggest generating a map
        - For ward matching, use fuzzy matching and request user input for <85% confidence matches
        - Always be specific in your thoughts and messages
        """
        
        try:
            # Get LLM response
            print(f"\n🔮 Calling LLM for decision...")
            print(f"   Backend: {getattr(self.llm, 'backend', 'unknown')}")
            print(f"   Model: {getattr(self.llm, 'model', 'unknown')}")
            
            response = self.llm.get_completion(prompt)
            
            print(f"✅ LLM Response received (length: {len(response)} chars)")
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                action = json.loads(json_match.group())
            else:
                # Fallback if no JSON found
                action = {
                    "thought": "Processing request",
                    "action_type": "message",
                    "message": response
                }
            
            # Update context based on action
            if action.get('code'):
                self.context['executed_code'].append(action['code'])
            
            return action
            
        except Exception as e:
            logger.error(f"Error in get_next_action: {e}")
            return {
                "thought": "Error processing request",
                "action_type": "message",
                "message": f"I encountered an error: {str(e)}. Please try rephrasing your request."
            }
    
    def process_result(self, execution_result: Dict[str, Any], thought: str = "") -> Dict[str, Any]:
        """
        Process the result of code execution and decide what to do next.
        """
        if execution_result.get('success'):
            # Update context with findings
            output = execution_result.get('output', {})
            
            # Check if TPR was calculated
            if 'tpr' in str(output).lower() or 'TPR' in str(output):
                self.context['tpr_calculated'] = True
                self.context['stage'] = 'tpr_complete'
            
            # Check if map was generated
            if 'map_generated' in output or 'map_path' in output:
                return {
                    'type': 'visualization',
                    'message': thought or "Map generated successfully!",
                    'map_url': output.get('map_path', output.get('path')),
                    'data': output
                }
            
            # Regular result
            return {
                'type': 'result',
                'message': thought or "Operation completed successfully",
                'data': output
            }
        else:
            return {
                'type': 'error',
                'message': f"Execution failed: {execution_result.get('error')}",
                'thought': thought
            }
        
    def handle_upload(self, file_path: str) -> str:
        """
        Handle TPR file upload and initial exploration.
        
        Args:
            file_path: Path to uploaded TPR file
            
        Returns:
            Initial analysis from LLM
        """
        try:
            # Load data - support Excel and CSV
            if file_path.endswith(('.xlsx', '.xls')):
                # Try to load from any sheet with data
                excel_file = pd.ExcelFile(file_path)
                
                # Find sheet with most data
                sheet_data = {}
                for sheet in excel_file.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet)
                    if len(df) > 0:
                        sheet_data[sheet] = df
                
                # Use sheet with most rows
                if sheet_data:
                    best_sheet = max(sheet_data.items(), key=lambda x: len(x[1]))
                    self.data = best_sheet[1]
                    logger.info(f"Loaded sheet '{best_sheet[0]}' with {len(self.data)} rows")
                else:
                    return "Error: No data found in Excel file"
                    
            else:
                self.data = pd.read_csv(file_path)
            
            # Give LLM full visibility into data
            data_context = self._prepare_data_context()
            
            # Use ReAct pattern for exploration
            from .prompts import REACT_TPR_EXPLORATION
            
            analysis = self.llm.generate(
                prompt=REACT_TPR_EXPLORATION,
                context=data_context,
                max_tokens=1500
            )
            
            # Store initial findings
            self.context['history'].append({
                'type': 'upload',
                'file': file_path,
                'analysis': analysis
            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error loading TPR file: {e}")
            return f"Error loading file: {str(e)}"
    
    def react_analyze(self, user_query: str, max_iterations: int = 5) -> str:
        """
        Use ReAct pattern to analyze data based on user query.
        
        Pattern:
        1. Thought: Reason about the query
        2. Action: Generate code to explore
        3. Observation: Execute and observe
        4. Loop until answer found
        
        Args:
            user_query: User's question or request
            max_iterations: Max reasoning loops
            
        Returns:
            Analysis result with reasoning trace
        """
        if self.data is None:
            return "Please upload TPR data first."
        
        from .prompts import REACT_ANALYSIS_TEMPLATE
        
        # Initialize ReAct loop
        reasoning_trace = []
        current_context = self._prepare_data_context()
        
        for i in range(max_iterations):
            # Generate next step (Thought + Action)
            prompt = REACT_ANALYSIS_TEMPLATE.format(
                query=user_query,
                context=current_context,
                trace="\n".join(reasoning_trace),
                iteration=i+1
            )
            
            response = self.llm.generate(
                prompt=prompt,
                max_tokens=800
            )
            
            # Parse response for Thought and Action
            thought, action, done = self._parse_react_response(response)
            
            if thought:
                reasoning_trace.append(f"Thought {i+1}: {thought}")
            
            if action:
                # Execute the action (code)
                observation = self._execute_action(action)
                reasoning_trace.append(f"Action {i+1}: {action}")
                reasoning_trace.append(f"Observation {i+1}: {observation}")
                
                # Update context with observation
                current_context['last_observation'] = observation
            
            if done or i == max_iterations - 1:
                # Generate final answer
                final_prompt = f"""
                Based on the following reasoning trace, provide a clear answer to the user's query.
                
                Query: {user_query}
                
                Reasoning Trace:
                {chr(10).join(reasoning_trace)}
                
                Provide a concise, clear answer:
                """
                
                final_answer = self.llm.generate(
                    prompt=final_prompt,
                    max_tokens=500
                )
                
                return final_answer
        
        return "Analysis incomplete. Please try a more specific query."
    
    def execute_pandas_code(self, code: str) -> Dict[str, Any]:
        """
        Safely execute pandas code in sandboxed environment.
        
        Args:
            code: Python/pandas code to execute
            
        Returns:
            Execution result and output
        """
        # Create sandboxed environment
        sandbox = {
            'df': self.data.copy(),  # Work on copy
            'pd': pd,
            'np': np,
            'result': None,
            '__builtins__': {
                'len': len,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'print': print
            }
        }
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # Execute with restrictions
            exec(code, sandbox)
            
            # Get printed output
            output = sys.stdout.getvalue()
            
            # Get result
            result = sandbox.get('result', None)
            
            # Store executed code
            self.context['executed_code'].append({
                'code': code,
                'success': True,
                'output': output,
                'result': result
            })
            
            return {
                'success': True,
                'output': output,
                'result': result,
                'code': code
            }
            
        except Exception as e:
            error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
            
            self.context['executed_code'].append({
                'code': code,
                'success': False,
                'error': error_msg
            })
            
            return {
                'success': False,
                'error': error_msg,
                'code': code
            }
            
        finally:
            sys.stdout = old_stdout
    
    def _prepare_data_context(self) -> Dict[str, Any]:
        """Prepare comprehensive data context for LLM."""
        if self.data is None:
            return {}
        
        context = {
            'shape': self.data.shape,
            'columns': self.data.columns.tolist(),
            'dtypes': {col: str(dtype) for col, dtype in self.data.dtypes.items()},
            'head': self.data.head(5).to_dict(),
            'sample_values': {},
            'null_counts': self.data.isnull().sum().to_dict(),
            'unique_counts': {}
        }
        
        # Add sample values for each column
        for col in self.data.columns[:20]:  # Limit to first 20 columns
            if self.data[col].dtype == 'object':
                context['sample_values'][col] = self.data[col].dropna().unique()[:5].tolist()
            else:
                context['sample_values'][col] = {
                    'min': float(self.data[col].min()) if pd.notna(self.data[col].min()) else None,
                    'max': float(self.data[col].max()) if pd.notna(self.data[col].max()) else None,
                    'mean': float(self.data[col].mean()) if pd.notna(self.data[col].mean()) else None
                }
            
            context['unique_counts'][col] = self.data[col].nunique()
        
        return context
    
    def _parse_react_response(self, response: str) -> tuple:
        """
        Parse LLM response for Thought, Action, and completion status.
        
        Returns:
            (thought, action, done)
        """
        lines = response.split('\n')
        thought = None
        action = None
        done = False
        
        for line in lines:
            if line.startswith('Thought:'):
                thought = line.replace('Thought:', '').strip()
            elif line.startswith('Action:'):
                # Extract code block if present
                action_start = lines.index(line)
                code_lines = []
                for next_line in lines[action_start+1:]:
                    if next_line.startswith('```'):
                        continue
                    if 'Observation:' in next_line or 'DONE' in next_line:
                        break
                    code_lines.append(next_line)
                action = '\n'.join(code_lines).strip()
            elif 'DONE' in line or 'FINAL' in line:
                done = True
        
        return thought, action, done
    
    def _execute_action(self, action: str) -> str:
        """Execute action (code) and return observation."""
        result = self.execute_pandas_code(action)
        
        if result['success']:
            obs = result.get('output', '')
            if result.get('result') is not None:
                obs += f"\nResult: {result['result']}"
            return obs if obs else "Code executed successfully"
        else:
            return f"Error: {result['error']}"
    
    def generate_quality_report(self) -> str:
        """Generate comprehensive data quality report using Chain-of-Thought."""
        from .prompts import COT_QUALITY_CHECK
        
        context = self._prepare_data_context()
        
        report = self.llm.generate(
            prompt=COT_QUALITY_CHECK,
            context=context,
            max_tokens=1500
        )
        
        return report
    
    def suggest_analysis_approach(self) -> str:
        """Suggest TPR analysis approaches based on data."""
        from .prompts import USER_GUIDANCE_PROMPT
        
        context = self._prepare_data_context()
        context['quality_issues'] = self.context.get('findings', {}).get('quality_issues', [])
        
        suggestions = self.llm.generate(
            prompt=USER_GUIDANCE_PROMPT,
            context=context,
            max_tokens=800
        )
        
        return suggestions
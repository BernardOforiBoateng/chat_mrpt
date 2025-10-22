"""
Ollama Manager for Local LLM Integration - TPR Analysis Focus

This module provides local LLM functionality using Ollama for complete data privacy.
Designed specifically for TPR (Test Positivity Rate) analysis where sensitive health
data must remain on-premises.
"""

import json
import requests
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class OllamaManager:
    """
    Local LLM manager using Ollama for privacy-sensitive TPR analysis.
    
    This manager provides full data access to the model while ensuring
    all processing happens locally without any external API calls.
    """
    
    def __init__(self, model: str = "qwen3:8b", base_url: str = "http://localhost:11434", 
                 interaction_logger=None):
        """Initialize Ollama manager with specified model."""
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.interaction_logger = interaction_logger
        
        # Test connection
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                if self.model in model_names:
                    logger.info(f"🔒 Ollama Manager initialized with {self.model} (LOCAL)")
                else:
                    logger.warning(f"Model {self.model} not found. Available: {model_names}")
            else:
                logger.warning(f"Ollama API returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Could not connect to Ollama: {e}")
    
    def generate_response(self, prompt: str, context: Optional[Any] = None, 
                         system_message: Optional[str] = None, temperature: float = 0.7,
                         max_tokens: int = 1000, session_id: Optional[str] = None) -> str:
        """Generate response with full data context for TPR analysis."""
        
        # Build comprehensive prompt
        full_prompt = ""
        
        if system_message:
            full_prompt += f"System: {system_message}\n\n"
        else:
            # Default TPR-focused system message
            full_prompt += """System: You are a malaria epidemiologist analyzing Test Positivity Rate (TPR) data.
You have FULL access to the data. Provide detailed insights, identify trends, and make recommendations.
Focus on actionable findings for public health intervention.\n\n"""
        
        # Include full TPR data context if available
        if context:
            if isinstance(context, pd.DataFrame):
                # Direct DataFrame access - the key advantage!
                full_prompt += "=== COMPLETE TPR DATA ===\n"
                full_prompt += f"Shape: {context.shape[0]} rows × {context.shape[1]} columns\n"
                full_prompt += f"Columns: {', '.join(context.columns)}\n"
                full_prompt += f"Date Range: {context.index.min()} to {context.index.max()}\n" if hasattr(context.index, 'min') else ""
                full_prompt += "\nFirst 5 rows:\n"
                full_prompt += context.head().to_string()
                full_prompt += "\n\nSummary statistics:\n"
                full_prompt += context.describe().to_string()
                full_prompt += "\n\n"
            elif isinstance(context, dict):
                if 'tpr_data' in context:
                    # TPR-specific context
                    full_prompt += "=== TPR DATA CONTEXT ===\n"
                    full_prompt += json.dumps(context['tpr_data'], indent=2, default=str)[:5000]
                    full_prompt += "\n\n"
                else:
                    # General context
                    full_prompt += f"Context: {json.dumps(context, indent=2, default=str)[:2000]}\n\n"
            else:
                full_prompt += f"Context: {str(context)[:2000]}\n\n"
        
        full_prompt += f"User Query: {prompt}"
        
        # Log the query for audit (no external transmission)
        logger.info(f"Local query: prompt_len={len(full_prompt)}, model={self.model}")
        
        start_time = datetime.now()
        
        try:
            # Call Ollama API (LOCAL only)
            response = requests.post(
                f"{self.api_url}/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('response', '')
                
                # Remove thinking tags if present (Qwen3 feature)
                if '<think>' in llm_response:
                    # Extract only the actual response
                    parts = llm_response.split('</think>')
                    if len(parts) > 1:
                        llm_response = parts[-1].strip()
                
                # Log interaction locally
                if self.interaction_logger and session_id:
                    latency = (datetime.now() - start_time).total_seconds()
                    self.interaction_logger.log_llm_interaction(
                        session_id=session_id,
                        prompt_type="ollama_tpr",
                        prompt=prompt,
                        prompt_context=f"Local model: {self.model}",
                        response=llm_response,
                        tokens_used=None,  # Ollama doesn't report tokens in same way
                        latency=latency
                    )
                
                return llm_response
            else:
                error_msg = f"Ollama API error: {response.status_code}"
                logger.error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"Error calling Ollama: {str(e)}"
            logger.error(error_msg)
            
            if self.interaction_logger and session_id:
                self.interaction_logger.log_error(
                    session_id=session_id,
                    error_type="ollama_api_error",
                    error_message=str(e)
                )
            
            return f"Local processing error: {str(e)}"
    
    def analyze_tpr_data(self, tpr_df: pd.DataFrame, query: str, 
                        session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze TPR data with structured output.
        
        This method gives the model FULL access to the TPR dataset
        for comprehensive analysis.
        """
        
        # Prepare comprehensive data summary
        data_context = {
            "shape": tpr_df.shape,
            "columns": list(tpr_df.columns),
            "dtypes": {col: str(dtype) for col, dtype in tpr_df.dtypes.items()},
            "sample_rows": tpr_df.head(10).to_dict('records'),
            "statistics": tpr_df.describe().to_dict(),
            "null_counts": tpr_df.isnull().sum().to_dict()
        }
        
        # Add TPR-specific analysis if columns are detected
        tpr_columns = [col for col in tpr_df.columns if 'test' in col.lower() or 'positive' in col.lower()]
        if tpr_columns:
            data_context['tpr_columns'] = tpr_columns
            for col in tpr_columns[:3]:  # Analyze first 3 TPR columns
                if pd.api.types.is_numeric_dtype(tpr_df[col]):
                    data_context[f'{col}_stats'] = {
                        'mean': float(tpr_df[col].mean()),
                        'median': float(tpr_df[col].median()),
                        'std': float(tpr_df[col].std()),
                        'min': float(tpr_df[col].min()),
                        'max': float(tpr_df[col].max()),
                        'q25': float(tpr_df[col].quantile(0.25)),
                        'q75': float(tpr_df[col].quantile(0.75))
                    }
        
        # Build prompt for structured analysis
        prompt = f"""
You have access to a TPR dataset with {tpr_df.shape[0]} rows and {tpr_df.shape[1]} columns.

Dataset Overview:
{json.dumps(data_context, indent=2, default=str)}

FULL DATA ACCESS - First 100 rows:
{tpr_df.head(100).to_string()}

User Query: {query}

Provide a comprehensive JSON response with the following structure:
{{
    "answer": "Direct answer to the query",
    "analysis": "Detailed analysis of the data",
    "key_findings": ["finding1", "finding2", "finding3"],
    "trends": "Identified trends in the data",
    "high_risk_areas": ["area1", "area2"] if applicable,
    "recommendations": ["recommendation1", "recommendation2"],
    "data_quality_notes": "Any data quality issues observed",
    "follow_up_questions": ["question1", "question2"]
}}

Ensure your response is valid JSON.
"""
        
        # Get response with full data access
        response = self.generate_response(
            prompt=prompt,
            temperature=0.3,  # Lower temperature for structured output
            max_tokens=2000,
            session_id=session_id
        )
        
        # Parse JSON response
        try:
            # Clean response if needed
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            result = json.loads(response.strip())
            
            # Ensure all expected fields exist
            default_structure = {
                "answer": "Analysis complete",
                "analysis": "",
                "key_findings": [],
                "trends": "",
                "high_risk_areas": [],
                "recommendations": [],
                "data_quality_notes": "",
                "follow_up_questions": []
            }
            
            for key, default_value in default_structure.items():
                if key not in result:
                    result[key] = default_value
            
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Return structured fallback
            return {
                "answer": response,
                "analysis": "Response was not in expected JSON format",
                "key_findings": [],
                "trends": "",
                "high_risk_areas": [],
                "recommendations": [],
                "data_quality_notes": "",
                "follow_up_questions": []
            }
    
    def generate_with_functions(self, messages: List[Dict], system_prompt: str,
                              functions: List[Dict], temperature: float = 0.7,
                              session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Compatibility method for function calling interface.
        
        Since Ollama doesn't support OpenAI-style function calling,
        we simulate it through prompt engineering.
        """
        
        # Build prompt that encourages function selection
        full_prompt = f"{system_prompt}\n\n"
        
        # Add function descriptions
        full_prompt += "Available functions:\n"
        for func in functions:
            full_prompt += f"- {func['name']}: {func['description']}\n"
            if 'parameters' in func and 'properties' in func['parameters']:
                full_prompt += f"  Parameters: {', '.join(func['parameters']['properties'].keys())}\n"
        
        full_prompt += "\n"
        
        # Add conversation history
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            full_prompt += f"{role.capitalize()}: {content}\n"
        
        full_prompt += """
If you need to call a function, respond with:
FUNCTION_CALL: function_name
ARGUMENTS: {"param1": "value1", "param2": "value2"}

Otherwise, provide a direct response.
"""
        
        response = self.generate_response(
            prompt=full_prompt,
            temperature=temperature,
            session_id=session_id
        )
        
        # Parse response for function calls
        if "FUNCTION_CALL:" in response:
            lines = response.split('\n')
            function_name = None
            arguments = {}
            
            for i, line in enumerate(lines):
                if "FUNCTION_CALL:" in line:
                    function_name = line.split("FUNCTION_CALL:")[1].strip()
                elif "ARGUMENTS:" in line:
                    try:
                        arg_str = line.split("ARGUMENTS:")[1].strip()
                        # Also check next lines in case JSON is multiline
                        if i + 1 < len(lines) and not lines[i + 1].startswith("FUNCTION_CALL"):
                            arg_str += '\n'.join(lines[i + 1:])
                        arguments = json.loads(arg_str)
                    except:
                        arguments = {}
            
            if function_name:
                return {
                    'content': None,
                    'function_call': {
                        'name': function_name,
                        'arguments': json.dumps(arguments)
                    }
                }
        
        # Regular response
        return {
            'content': response,
            'function_call': None
        }
    
    def validate_connection(self) -> bool:
        """Check if Ollama is accessible and model is available."""
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(m['name'] == self.model for m in models)
        except:
            pass
        return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        try:
            response = requests.post(
                f"{self.api_url}/show",
                json={"name": self.model},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {}


# Compatibility function for service container
def get_ollama_manager(interaction_logger=None) -> OllamaManager:
    """Factory function to create Ollama manager."""
    import os
    model = os.environ.get('OLLAMA_MODEL', 'qwen3:8b')
    base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    return OllamaManager(model=model, base_url=base_url, interaction_logger=interaction_logger)
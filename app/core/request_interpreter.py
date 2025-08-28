"""
True py-sidebot Implementation for ChatMRPT

Clean implementation following py-sidebot's actual pattern:
1. Create chat session with system prompt
2. Register actual Python functions as tools
3. Pass user messages directly to chat session
4. Let LLM handle tool selection and execution

Key components preserved:
- Memory integration
- Visualization explanation
- Data schema handling
- Conversational data access
- Streaming support
- Special workflows (permissions, forks)
"""

import logging
import json
import time
import os
import pandas as pd
from typing import Dict, Any, List, Optional
from flask import current_app

logger = logging.getLogger(__name__)


class RequestInterpreter:
    
    @staticmethod
    def force_session_save():
        """Force Flask session to save when using Redis backend."""
        from flask import session
        # Mark all keys as modified to force Redis save
        session.permanent = True
        session.modified = True
        # Touch all important keys
        for key in ['data_loaded', 'csv_loaded', 'shapefile_loaded']:
            if key in session:
                session[key] = session[key]  # Re-assign to trigger modification
    """
    True py-sidebot inspired request interpreter for ChatMRPT.
    
    Simple approach: register Python functions as tools and let LLM choose.
    """
    
    def __init__(self, llm_manager, data_service, analysis_service, visualization_service):
        self.llm_manager = llm_manager
        self.data_service = data_service
        self.analysis_service = analysis_service
        self.visualization_service = visualization_service
        
        # py-sidebot approach: Simple conversation storage
        self.conversation_history = {}
        self.session_data = {}  # Store session data for access
        
        # Initialize memory system if available
        try:
            from app.services.memory_service import get_memory_service
            self.memory = get_memory_service()
        except Exception as e:
            logger.debug(f"Memory service not available: {e}")
            self.memory = None
        
        # Initialize conversational data access
        self.conversational_data_access = None
        
        # py-sidebot pattern: Register tools as actual Python functions
        self.tools = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register actual Python functions as tools - true py-sidebot style."""
        logger.info("Registering tools - py-sidebot pattern")
        
        # Register analysis tools
        self.tools['run_complete_analysis'] = self._run_complete_analysis
        self.tools['run_composite_analysis'] = self._run_composite_analysis
        self.tools['run_pca_analysis'] = self._run_pca_analysis
        
        # Register visualization tools
        self.tools['create_vulnerability_map'] = self._create_vulnerability_map
        self.tools['create_box_plot'] = self._create_box_plot
        self.tools['create_pca_map'] = self._create_pca_map
        self.tools['create_variable_distribution'] = self._create_variable_distribution
        
        # Register settlement visualization tools
        self.tools['create_settlement_map'] = self._create_settlement_map
        self.tools['show_settlement_statistics'] = self._show_settlement_statistics
        
        # Register data tools
        self.tools['execute_data_query'] = self._execute_data_query
        self.tools['execute_sql_query'] = self._execute_sql_query
        self.tools['run_data_quality_check'] = self._run_data_quality_check
        
        # Register explanation tools
        self.tools['explain_analysis_methodology'] = self._explain_analysis_methodology
        
        # NEW: ITN Planning Tool
        self.tools['run_itn_planning'] = self._run_itn_planning
        
        logger.info(f"Registered {len(self.tools)} tools")
    
    def process_message(self, user_message: str, session_id: str, session_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """py-sidebot pattern: Pass message directly to LLM with tools."""
        start_time = time.time()
        
        try:
            logger.info(f"📌 Processing message for session {session_id}: {user_message[:100]}...")
            
            # Handle special workflows first (pass kwargs for context flags)
            logger.info(f"🔄 Checking special workflows for: {user_message[:50]}...")
            special_result = self._handle_special_workflows(user_message, session_id, session_data, **kwargs)
            if special_result:
                return special_result
            
            # Get session context
            session_context = self._get_session_context(session_id, session_data)
            
            # Simple routing: no data = conversational, with data = tools available
            if not session_context.get('data_loaded', False):
                return self._simple_conversational_response(user_message, session_context)
            
            # py-sidebot approach: LLM with all tools
            result = self._llm_with_tools(user_message, session_context, session_id)
            
            # Store conversation
            self._store_conversation(session_id, user_message, result.get('response', ''))
            
            result['total_time'] = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"Error in py-sidebot processing: {e}")
            return {
                'status': 'error',
                'response': f'I encountered an issue: {str(e)}',
                'tools_used': []
            }
    
    def process_message_streaming(self, user_message: str, session_id: str, session_data: Dict[str, Any] = None, **kwargs):
        """Streaming version for better UX."""
        try:
            # Handle special workflows (pass kwargs for context flags)
            special_result = self._handle_special_workflows(user_message, session_id, session_data, **kwargs)
            if special_result:
                # CRITICAL: Include visualizations if present
                yield {
                    'content': special_result.get('response', ''),
                    'status': special_result.get('status', 'success'),
                    'visualizations': special_result.get('visualizations', []),
                    'tools_used': special_result.get('tools_used', []),
                    'done': True
                }
                return
            
            # Get session context
            session_context = self._get_session_context(session_id, session_data)
            
            logger.info(f"🔍 Session context for {session_id}:")
            logger.info(f"   data_loaded: {session_context.get('data_loaded', False)}")
            logger.info(f"   has_csv: {session_context.get('csv_loaded', False)}")
            logger.info(f"   has_shapefile: {session_context.get('shapefile_loaded', False)}")
            logger.info(f"   current_data: {str(session_context.get('current_data', 'None'))[:100]}")
            logger.info(f"   session_data param keys: {list(session_data.keys())[:10] if session_data else 'None'}")
            logger.info(f"   kwargs: {kwargs}")
            
            if not session_context.get('data_loaded', False):
                logger.info(f"❌ No data loaded, using conversational streaming")
                # Use streaming for conversational responses too
                if self.llm_manager and hasattr(self.llm_manager, 'generate_with_functions_streaming'):
                    system_prompt = self._build_system_prompt(session_context, session_id)
                    
                    # Stream the response
                    for chunk in self.llm_manager.generate_with_functions_streaming(
                        messages=[{"role": "user", "content": user_message}],
                        system_prompt=system_prompt,
                        functions=[],  # No tools for simple conversation
                        temperature=0.7,
                        session_id=session_id
                    ):
                        # Handle OpenAI streaming format (no 'type' field)
                        content = chunk.get('content', '')
                        if content:  # Only yield if there's actual content
                            yield {
                                'content': content,
                                'status': 'success',
                                'done': False
                            }
                    
                    # Send final done signal
                    yield {
                        'content': '',
                        'status': 'success',
                        'done': True
                    }
                else:
                    # Fallback to non-streaming
                    response = self._simple_conversational_response(user_message, session_context, session_id)
                    yield {
                        'content': response.get('response', ''),
                        'status': 'success',
                        'done': True
                    }
                return
            
            # Stream with tools
            logger.info(f"✅ Data loaded! Calling _stream_with_tools")
            logger.info(f"   Message: {user_message[:100]}...")
            yield from self._stream_with_tools(user_message, session_context, session_id)
            
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            yield {
                'content': f'I encountered an issue: {str(e)}',
                'status': 'error',
                'done': True
            }
    
    def _llm_with_tools(self, user_message: str, session_context: Dict, session_id: str) -> Dict[str, Any]:
        """py-sidebot pattern: Pass message to LLM with all tools available."""
        system_prompt = self._build_system_prompt(session_context, session_id)
        
        # Convert tools to OpenAI function format
        functions = []
        for tool_name, tool_func in self.tools.items():
            func_def = {
                'name': tool_name,
                'description': tool_func.__doc__ or f"Execute {tool_name}",
                'parameters': self._get_tool_parameters(tool_name)
            }
            functions.append(func_def)
        
        # Single LLM call
        response = self.llm_manager.generate_with_functions(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            functions=functions,
            temperature=0.7,
            session_id=session_id
        )
        
        # Process response
        return self._process_llm_response(response, user_message, session_id)
    
    def _stream_with_tools(self, user_message: str, session_context: Dict, session_id: str):
        """Stream LLM response with tools."""
        logger.info(f"🔧 _stream_with_tools called for session {session_id}")
        logger.info(f"📊 Data loaded status: {session_context.get('data_loaded', False)}")
        logger.info(f"📦 Session data cache has session: {session_id in self.session_data}")
        
        # CRITICAL FIX: Ensure data is loaded in session_data before tools are called
        # This is needed for tools to access the data after V3 transition
        if session_context.get('data_loaded', False) and session_id not in self.session_data:
            try:
                import pandas as pd
                from pathlib import Path
                session_folder = Path(f'instance/uploads/{session_id}')
                raw_data_path = session_folder / 'raw_data.csv'
                
                if raw_data_path.exists():
                    df = pd.read_csv(raw_data_path)
                    self.session_data[session_id] = {
                        'data': df,
                        'columns': list(df.columns),
                        'shape': df.shape
                    }
                    logger.info(f"✅ Loaded data for tools: {df.shape} from {raw_data_path}")
                    logger.info(f"📋 Columns loaded: {list(df.columns)[:5]}...")
            except Exception as e:
                logger.error(f"Failed to load data for tools: {e}")
        
        # Check if LLM manager is available
        if self.llm_manager is None:
            logger.error("LLM manager is not initialized for streaming")
            yield {
                'content': "I'm having trouble connecting to the language model. Please try again in a moment.",
                'status': 'error',
                'done': True
            }
            return
        
        system_prompt = self._build_system_prompt(session_context, session_id)
        
        functions = []
        for tool_name, tool_func in self.tools.items():
            func_def = {
                'name': tool_name,
                'description': tool_func.__doc__ or f"Execute {tool_name}",
                'parameters': self._get_tool_parameters(tool_name)
            }
            functions.append(func_def)
        
        logger.info(f"🛠️ Passing {len(functions)} tools to LLM for streaming")
        logger.info(f"📝 Tool names: {[f['name'] for f in functions[:3]]}...")
        logger.info(f"🎯 User message: {user_message[:100]}...")
        
        # Track accumulated content for conversation storage
        accumulated_content = []
        
        for chunk in self.llm_manager.generate_with_functions_streaming(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            functions=functions,
            temperature=0.7,
            session_id=session_id
        ):
            if chunk.get('function_call'):
                # Execute tool
                function_name = chunk['function_call']['name']
                # Tool call detected - log quietly
                logger.debug(f"Tool call detected: {function_name} with args: {chunk['function_call']['arguments']}")
                
                if function_name in self.tools:
                    try:
                        # CRITICAL FIX: Handle empty or malformed function arguments
                        args_str = chunk['function_call']['arguments'] or '{}'
                        args = json.loads(args_str) if args_str.strip() else {}
                        args['session_id'] = session_id  # Ensure session_id is included
                        
                        logger.debug(f"Executing tool: {function_name} with args: {args}")
                        
                        # Debug logging to understand parameter issues
                        if function_name == 'execute_sql_query' and 'query' not in args:
                            logger.error(f"SQL query parameter missing! Args: {args}")
                            # Don't add fallback - let it fail properly
                        
                        if function_name == 'create_variable_distribution' and 'variable_name' not in args:
                            logger.error(f"variable_name parameter missing! Args: {args}")
                            # Don't add fallback - let it fail properly
                        
                        result = self.tools[function_name](**args)
                        logger.debug(f"Tool {function_name} completed")
                        
                        ######################## NEW: AUTOMATIC INTERPRETATION ########################
                        # If the tool returned data (either as a structured dict or raw string),
                        # automatically ask the LLM to interpret the results before finalising
                        # the streaming response. This prevents raw, unexplained outputs from
                        # reaching the user.
                        #############################################################################

                        # Flag to toggle interpretation (easy to disable if needed)
                        ENABLE_INTERPRETATION = True

                        def _yield_interpretation(raw_output: str, tools_used_list: list):
                            """Utility to generate and yield interpretation chunks."""
                            if not ENABLE_INTERPRETATION:
                                yield {'content': '', 'status': 'success', 'tools_used': tools_used_list, 'done': True}
                                return
                            try:
                                interpretation = self._interpret_raw_output(
                                    raw_output=raw_output,
                                    user_message=user_message,
                                    session_context=session_context,
                                    session_id=session_id
                                )
                                if interpretation:
                                    yield {
                                        'content': interpretation,
                                        'status': 'success',
                                        'tools_used': tools_used_list,
                                        'done': True
                                    }
                                else:
                                    yield {'content': '', 'status': 'success', 'tools_used': tools_used_list, 'done': True}
                            except Exception as interp_err:
                                logger.error(f"Error during interpretation: {interp_err}")
                                yield {
                                    'content': f"⚠️ Interpretation failed: {interp_err}",
                                    'status': 'error',
                                    'tools_used': tools_used_list,
                                    'done': True
                                }

                        # Handle structured dict response
                        if isinstance(result, dict) and 'response' in result:
                            tools_list = result.get('tools_used', [function_name])
                            yield {
                                'content': result['response'],
                                'status': result.get('status', 'success'),
                                'visualizations': result.get('visualizations', []),
                                'tools_used': tools_list,
                                'done': False
                            }
                            yield from _yield_interpretation(result['response'], tools_list)
                            self._store_conversation(session_id, user_message, result['response'])
                            return

                        # Handle raw string response
                        else:
                            raw_output = result if isinstance(result, str) else str(result)
                            tools_list = [function_name]
                            yield {
                                'content': raw_output,
                                'status': 'success',
                                'tools_used': tools_list,
                                'done': False
                            }
                            yield from _yield_interpretation(raw_output, tools_list)
                            self._store_conversation(session_id, user_message, raw_output)
                            return
                        # ---------------------------------------------------------------------------
                    except Exception as e:
                        yield {
                            'content': f"Error executing {function_name}: {str(e)}",
                            'status': 'error',
                            'done': True
                        }
                        return
            
            # Handle text chunks from streaming (OpenAI format has no 'type' field)
            content = chunk.get('content', '')
            if content:  # Only process if there's actual content
                accumulated_content.append(content)
                yield {
                    'content': content,
                    'status': 'success',
                    'done': False
                }
            elif chunk.get('done'):
                content = chunk.get('content', '')
                if content:
                    accumulated_content.append(content)
                yield {
                    'content': content,
                    'status': 'success',
                    'done': True
                }
                # Store the full conversation
                full_response = ''.join(accumulated_content)
                self._store_conversation(session_id, user_message, full_response)
                return
            else:
                # Handle other chunk types
                content = chunk.get('content', '')
                if content:
                    accumulated_content.append(content)
                yield {
                    'content': content,
                    'status': 'success',
                    'done': False
                }
        
        # If we got here without a done signal, send one
        if accumulated_content:
            yield {
                'content': '',
                'status': 'success',
                'done': True
            }
            full_response = ''.join(accumulated_content)
            self._store_conversation(session_id, user_message, full_response)
    
    def _process_llm_response(self, response: Dict, user_message: str, session_id: str) -> Dict[str, Any]:
        """Process LLM response and execute tools if needed."""
        if 'function_call' in response and response['function_call']:
            function_name = response['function_call']['name']
            
            if function_name in self.tools:
                try:
                    # CRITICAL FIX: Handle empty or malformed function arguments
                    args_str = response['function_call']['arguments'] or '{}'
                    args = json.loads(args_str) if args_str.strip() else {}
                    args['session_id'] = session_id  # Ensure session_id is included
                    
                    # Special handling for execute_data_query missing arguments
                    if function_name == 'execute_data_query' and 'query' not in args:
                        # Extract intent from the user message as fallback
                        args['query'] = user_message
                    
                    result = self.tools[function_name](**args)
                    
                    # Handle structured responses from tools
                    if isinstance(result, dict) and 'response' in result:
                        # Tool returned structured response with visualizations
                        return {
                            'response': result['response'],
                            'visualizations': result.get('visualizations', []),
                            'tools_used': result.get('tools_used', [function_name]),
                            'status': result.get('status', 'success')
                        }
                    else:
                        # Tool returned simple string response
                        return {
                            'response': result,
                            'tools_used': [function_name],
                            'status': 'success'
                        }
                except Exception as e:
                    return {
                        'response': f"Error executing {function_name}: {str(e)}",
                        'tools_used': [],
                        'status': 'error'
                    }
        
        # Pure conversational response
        return {
            'response': response.get('content', 'No response'),
            'tools_used': [],
            'status': 'success'
        }
    
    # Tool Functions - These are the actual functions registered as tools
    def _run_complete_analysis(self, session_id: str, variables: Optional[List[str]] = None):
        """Run complete dual-method malaria risk analysis (composite scoring + PCA).
        Use ONLY when analysis has NOT been run yet. DO NOT use if analysis is already complete.
        For ITN planning after analysis, use run_itn_planning instead."""
        try:
            # Use the tool directly to get the comprehensive summary
            from app.tools.complete_analysis_tools import RunCompleteAnalysis
            tool = RunCompleteAnalysis()
            
            # Execute the tool with proper parameters
            tool_result = tool.execute(
                session_id=session_id,
                composite_variables=variables,  # Use same variables for both methods if provided
                pca_variables=variables
            )
            
            # Update session to mark analysis as complete on success
            if tool_result.success:
                try:
                    from flask import session
                    session['analysis_complete'] = True
                    session.modified = True
                except:
                    # If not in request context, update conversation history
                    if session_id not in self.conversation_history:
                        self.conversation_history[session_id] = []
                    self.conversation_history[session_id].append({
                        'analysis_complete': True
                    })
            
            # Get the comprehensive message from tool result
            message = tool_result.message  # This contains the custom summary
            
            # Auto-explain any visualizations
            visualizations = tool_result.data.get('visualizations', []) if tool_result.data else []
            if visualizations:
                explanations = []
                for viz in visualizations:
                    if viz.get('file_path'):
                        explanation = self._explain_visualization_universally(
                            viz['file_path'], viz.get('type', 'visualization'), session_id
                        )
                        explanations.append(explanation)
                if explanations:
                    message += "\n\n" + "\n\n".join(explanations)

            # Return structured response to bypass interpretation layer
            return {
                'response': message,
                'status': 'success' if tool_result.success else 'error',
                'tools_used': ['run_complete_analysis'],
                'visualizations': visualizations
            }
        except Exception as e:
            return f"Error running complete analysis: {str(e)}"
    
    def _run_composite_analysis(self, session_id: str, variables: Optional[List[str]] = None):
        """Run composite scoring malaria risk analysis with equal weights."""
        try:
            result = self.analysis_service.run_composite_analysis(session_id, variables=variables)
            
            if isinstance(result, dict) and result.get('status') == 'success':
                # Update session to mark analysis as complete
                try:
                    from flask import session
                    session['analysis_complete'] = True
                    session.modified = True
                except:
                    # If not in request context, update conversation history
                    if session_id not in self.conversation_history:
                        self.conversation_history[session_id] = []
                    self.conversation_history[session_id].append({
                        'analysis_complete': True
                    })
                
                # Run PCA analysis too for comprehensive comparison
                pca_result = self.analysis_service.run_pca_analysis(session_id, variables=variables)
                
                # Use your proper summary function
                try:
                    from app.tools.complete_analysis_tools import RunCompleteAnalysis
                    
                    analysis_tool = RunCompleteAnalysis()
                    summary = analysis_tool._generate_comprehensive_summary(
                        result, pca_result, {}, 0.0, session_id
                    )
                    
                    return summary
                        
                except Exception as summary_error:
                    logger.error(f"Error calling _generate_summary_from_analysis_results: {summary_error}")
                    logger.error(f"Composite result structure: {result.keys() if result else 'None'}")
                    logger.error(f"PCA result structure: {pca_result.keys() if pca_result else 'None'}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    return "✅ Composite analysis completed successfully. Results are available - please ask for detailed rankings."
            else:
                # Use your existing error formatter
                from app.services.response_formatter import response_formatter
                return response_formatter.format_error_message(
                    result.get('message', 'Composite analysis failed'),
                    'composite_analysis',
                    ['Check data quality', 'Verify variable selection', 'Review analysis parameters']
                )
        except Exception as e:
            from app.services.response_formatter import response_formatter
            return response_formatter.format_error_message(
                str(e),
                'composite_analysis_execution',
                ['Check data upload', 'Verify system configuration', 'Review error logs']
            )
    
    def _run_pca_analysis(self, session_id: str, variables: Optional[List[str]] = None):
        """Run PCA malaria risk analysis."""
        try:
            result = self.analysis_service.run_pca_analysis(session_id, variables=variables)
            
            # Update session to mark analysis as complete on success
            if result.get('status') == 'success':
                try:
                    from flask import session
                    session['analysis_complete'] = True
                    session.modified = True
                except:
                    # If not in request context, update conversation history
                    if session_id not in self.conversation_history:
                        self.conversation_history[session_id] = []
                    self.conversation_history[session_id].append({
                        'analysis_complete': True
                    })
            
            # Format PCA results properly
            from app.services.response_formatter import response_formatter
            
            if isinstance(result, dict):
                formatted_result = response_formatter.format_analysis_result(result, 'pca')
                return formatted_result
            else:
                return result.get('message', 'PCA analysis completed successfully')
        except Exception as e:
            return f"Error running PCA analysis: {str(e)}"
    
    def _create_vulnerability_map(self, session_id: str, method: str = None):
        """Create vulnerability choropleth map for malaria risk visualization.
        
        If method is not specified, creates a side-by-side comparison of both methods.
        If method is specified ('composite' or 'pca'), creates a single map for that method.
        """
        try:
            # If no method specified, use the comparison tool
            if method is None:
                # Use the new comparison tool from the tool registry
                from app.core.tool_registry import get_tool_registry
                tool_registry = get_tool_registry()
                
                # Execute the comparison tool
                result = tool_registry.execute_tool(
                    'create_vulnerability_map_comparison',
                    session_id=session_id,
                    include_statistics=True
                )
                
                if result.get('status') == 'success':
                    # Convert tool result to expected format
                    return {
                        'response': result.get('message', 'Created side-by-side vulnerability map comparison'),
                        'visualizations': [{
                            'type': 'vulnerability_comparison',
                            'file_path': result.get('data', {}).get('file_path', ''),
                            'path': result.get('data', {}).get('web_path', ''),
                            'url': result.get('data', {}).get('web_path', ''),
                            'title': "Vulnerability Assessment Comparison",
                            'description': "Side-by-side comparison of Composite and PCA vulnerability methods"
                        }],
                        'tools_used': ['create_vulnerability_map_comparison'],
                        'status': 'success'
                    }
                else:
                    return f"Error creating vulnerability comparison: {result.get('message', 'Unknown error')}"
            
            # Otherwise use the specific method requested
            else:
                result = self.visualization_service.create_vulnerability_map(session_id, method=method)
                message = result.get('message', f'Vulnerability map created using {method} method')
                
                # Auto-explain the visualization if file_path exists
                if result.get('file_path'):
                    explanation = self._explain_visualization_universally(
                        result['file_path'], 'vulnerability_map', session_id
                    )
                    message += f"\\n\\n{explanation}"
                
                # Return structured response if successful
                if result.get('status') == 'success' and result.get('web_path'):
                    return {
                        'response': message,
                        'visualizations': [{
                            'type': result.get('visualization_type', 'vulnerability_map'),
                            'file_path': result.get('file_path', ''),
                            'path': result.get('web_path', ''),
                            'url': result.get('web_path', ''),
                            'title': f"Vulnerability Map ({method.title()} Method)",
                            'description': f"Ward vulnerability classification using {method} method"
                        }],
                        'tools_used': ['create_vulnerability_map'],
                        'status': 'success'
                    }
                else:
                    return f"Error creating vulnerability map: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error creating vulnerability map: {str(e)}"
    
    def _create_box_plot(self, session_id: str, method: str = 'composite'):
        """Create box plots showing vulnerability score distributions."""
        try:
            result = self.visualization_service.create_box_plot(session_id, method=method)
            message = result.get('message', f'Box plot created for {method} scores')
            
            # Auto-explain the visualization if file_path exists
            if result.get('file_path'):
                explanation = self._explain_visualization_universally(
                    result['file_path'], 'box_plot', session_id
                )
                message += f"\\n\\n{explanation}"
            
            # Return structured response if successful
            if result.get('status') == 'success' and result.get('web_path'):
                return {
                    'response': message,
                    'visualizations': [{
                        'type': result.get('visualization_type', 'box_plot'),
                        'file_path': result.get('file_path', ''),
                        'path': result.get('web_path', ''),
                        'url': result.get('web_path', ''),
                        'title': f"Box Plot ({method.title()} Method)",
                        'description': f"Vulnerability score distribution using {method} method"
                    }],
                    'tools_used': ['create_box_plot'],
                    'status': 'success'
                }
            else:
                return f"Error creating box plot: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error creating box plot: {str(e)}"
    
    def _create_pca_map(self, session_id: str):
        """Create PCA-based vulnerability map."""
        try:
            result = self.visualization_service.create_pca_map(session_id)
            message = result.get('message', 'PCA vulnerability map created')
            
            # Auto-explain the visualization if file_path exists
            if result.get('file_path'):
                explanation = self._explain_visualization_universally(
                    result['file_path'], 'pca_map', session_id
                )
                message += f"\\n\\n{explanation}"
            
            # Return structured response if successful
            if result.get('status') == 'success' and result.get('web_path'):
                return {
                    'response': message,
                    'visualizations': [{
                        'type': result.get('visualization_type', 'pca_map'),
                        'file_path': result.get('file_path', ''),
                        'path': result.get('web_path', ''),
                        'url': result.get('web_path', ''),
                        'title': "PCA Vulnerability Map",
                        'description': "Ward vulnerability classification using PCA method"
                    }],
                    'tools_used': ['create_pca_map'],
                    'status': 'success'
                }
            else:
                return f"Error creating PCA map: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error creating PCA map: {str(e)}"
    
    def _create_variable_distribution(self, session_id: str, variable_name: str):
        """Create an interactive choropleth map showing the spatial distribution of any variable.
        REQUIRES: 'variable_name' parameter with the exact column name to visualize.
        Use this when users ask to 'map', 'plot', 'show distribution' or 'visualize' a variable.
        User asks: 'plot the map distribution for mean_rainfall' -> Use variable_name: 'mean_rainfall'
        User asks: 'show pfpr on map' -> Use variable_name: 'pfpr'"""
        try:
            from app.tools.variable_distribution import VariableDistribution
            
            # Create the tool instance
            tool = VariableDistribution(variable_name=variable_name)
            
            # Execute the tool
            result = tool.execute(session_id)
            
            if result.success:
                message = result.message
                
                # Auto-explain the visualization if it was created
                if result.data and result.data.get('file_path'):
                    explanation = self._explain_visualization_universally(
                        result.data['file_path'], 'variable_distribution', session_id
                    )
                    message += f"\n\n{explanation}"
                
                # Return structured response with visualization data
                return {
                    'response': message,
                    'visualizations': [{
                        'type': result.data.get('chart_type', 'variable_distribution'),
                        'file_path': result.data.get('file_path', ''),
                        'path': result.data.get('web_path', ''),  # Frontend expects 'path' key
                        'url': result.data.get('web_path', ''),   # Also provide 'url' for compatibility
                        'title': f"{result.data.get('variable', 'Variable')} Distribution",
                        'description': f"Spatial distribution of {result.data.get('variable', 'variable')} across study area"
                    }] if result.data else [],
                    'tools_used': ['create_variable_distribution'],
                    'status': 'success'
                }
            else:
                return f"Error creating variable distribution: {result.message}"
        except Exception as e:
            return f"Error creating variable distribution: {str(e)}"
    
    def _execute_data_query(self, session_id: str, query: str, code: Optional[str] = None):
        """Execute complex data analysis using Python code. Use for statistics, correlations, or advanced analysis.
        The 'query' parameter is REQUIRED and should describe what analysis to perform.
        Examples: query='check data quality', query='correlation between rainfall and malaria', query='statistical summary'"""
        try:
            # Check if data is available via data service first
            data_handler = self.data_service.get_handler(session_id)
            if not data_handler or not hasattr(data_handler, 'csv_data') or data_handler.csv_data is None:
                return "Error executing query: No data available. Please upload data first."
            
            # Initialize conversational data access for this session
            # Always create a new instance to ensure proper session context
            logger.info(f"Creating ConversationalDataAccess for session: {session_id}")
            from app.services.conversational_data_access import ConversationalDataAccess
            conversational_data_access = ConversationalDataAccess(session_id, self.llm_manager)
            
            if code:
                logger.info(f"Executing provided code: {code}")
                result = conversational_data_access.execute_code(code)
            else:
                logger.info(f"Processing query: {query}")
                result = conversational_data_access.process_query(query)
            
            if result.get('success'):
                # Get the formatted output from the executed code
                output = result.get('output', '').strip()
                plot_data = result.get('plot_data')
                
                # Return structured response with visualizations
                response_data = {
                    'response': output if output else f"Query executed successfully: {query}",
                    'visualizations': [],
                    'tools_used': ['execute_data_query'],
                    'status': 'success'
                }
                
                # Add visualization if plot was generated
                if plot_data:
                    # Determine specific chart type from query context
                    viz_type = self._determine_chart_type_from_query(query)
                    response_data['visualizations'].append({
                        'type': viz_type,
                        'data': plot_data,
                        'title': f'Analysis Visualization - {query[:50]}...' if len(query) > 50 else f'Analysis Visualization - {query}'
                    })
                
                return response_data
            else:
                error_msg = f"Error executing query: {result.get('error', 'Unknown error')}"
                return error_msg
        except Exception as e:
            return f"Error in data query: {str(e)}"
    
    def _execute_sql_query(self, session_id: str, query: str):
        """Execute SQL queries on the dataset.
        REQUIRES: 'query' parameter with a valid SQL string. The table name is always 'df'.
        Use this when users ask to see data, list columns, or filter records.
        User asks: 'what are the variables in my data?' -> Use query: 'SELECT * FROM df LIMIT 1'
        User asks: 'show top 5 wards by pfpr' -> Use query: 'SELECT * FROM df ORDER BY pfpr DESC LIMIT 5'"""
        try:
            # For now, continue using the conversational data access
            # The interpretation will happen in the streaming handler
            logger.info(f"Executing SQL query: {query}")
            from app.services.conversational_data_access import ConversationalDataAccess
            conversational_data_access = ConversationalDataAccess(session_id, self.llm_manager)
            
            # Use the process_sql_query method which handles all stages properly
            result = conversational_data_access.process_sql_query(query)
            
            if result.get('success'):
                return result.get('output', 'Query executed successfully')
            else:
                return f"Error executing SQL: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"SQL query error: {e}")
            return f"Error executing SQL query: {str(e)}"
    
    def _determine_chart_type_from_query(self, query: str) -> str:
        """Determine specific chart type from user query to avoid visualization conflicts."""
        query_lower = query.lower()
        
        # Check for specific chart types mentioned in the query
        if 'scatter' in query_lower:
            return 'scatter_plot'
        elif 'histogram' in query_lower or 'hist' in query_lower:
            return 'histogram'
        elif ('distribution' in query_lower and 'plot' in query_lower) or 'distplot' in query_lower:
            return 'histogram'  # Most distribution plots are histograms
        elif 'box plot' in query_lower or 'boxplot' in query_lower:
            return 'box_plot'
        elif 'bar chart' in query_lower or 'bar plot' in query_lower or 'barplot' in query_lower:
            return 'bar_chart'
        elif 'line chart' in query_lower or 'line plot' in query_lower or 'lineplot' in query_lower:
            return 'line_plot'
        elif 'pie chart' in query_lower or 'pie plot' in query_lower:
            return 'pie_chart'
        elif 'heatmap' in query_lower or 'heat map' in query_lower:
            return 'heatmap'
        elif 'density' in query_lower and 'plot' in query_lower:
            return 'density_plot'
        elif 'violin' in query_lower:
            return 'violin_plot'
        elif 'correlation' in query_lower and 'plot' in query_lower:
            return 'scatter_plot'  # Correlation plots are usually scatter plots
        else:
            # Return a unique type for each general plot to prevent conflicts
            import time
            return f'conversational_plot_{int(time.time())}'
    
    def _explain_analysis_methodology(self, session_id: str, method: str = 'both'):
        """Explain how malaria risk analysis methodologies work (composite scoring, PCA, or both)."""
        try:
            # Use LLM to generate methodology explanation
            if method == 'composite':
                explanation = """**Composite Scoring Methodology**

Composite scoring combines multiple malaria risk indicators into a single vulnerability score:

1. **Variable Selection**: Selects scientifically-validated variables based on Nigerian geopolitical zones
2. **Normalization**: Standardizes all variables to 0-1 scale for fair comparison
3. **Equal Weighting**: All variables contribute equally to the final score
4. **Aggregation**: Sums normalized values to create composite vulnerability score
5. **Ranking**: Ranks wards from highest to lowest risk for intervention targeting

This method is transparent, interpretable, and follows WHO guidelines for malaria stratification."""
            
            elif method == 'pca':
                explanation = """**Principal Component Analysis (PCA) Methodology**

PCA reduces dimensionality while preserving variance in malaria risk data:

1. **Data Standardization**: Centers and scales all variables
2. **Covariance Analysis**: Identifies relationships between variables
3. **Component Extraction**: Finds principal components that explain maximum variance
4. **Weight Calculation**: Automatically determines variable importance
5. **Score Generation**: Creates data-driven vulnerability scores
6. **Interpretation**: First component typically captures overall malaria risk

This method is statistically robust and reveals hidden patterns in the data."""
            
            else:  # both
                explanation = """**Dual-Method Malaria Risk Analysis**

ChatMRPT uses both composite scoring and PCA for comprehensive assessment:

**Composite Scoring**: Transparent, equal-weighted approach following WHO guidelines
- Pros: Interpretable, policy-friendly, scientifically grounded
- Use when: Clear intervention priorities needed

**PCA Analysis**: Statistical approach revealing data patterns
- Pros: Objective, captures complex relationships, statistically robust
- Use when: Exploring underlying risk structures

**Comparison**: Both methods often agree on high-risk areas but may differ in rankings. Use both for robust decision-making and to validate findings."""
            
            return explanation
        except Exception as e:
            return f"Error explaining methodology: {str(e)}"
    
    def _create_settlement_map(self, session_id: str, ward_name: str = None, zoom_level: int = 11, **kwargs):
        """Create interactive settlement map showing building types for specific wards."""
        try:
            # Filter out any invalid parameters that LLM might pass
            valid_params = {'session_id': session_id}
            if ward_name:
                valid_params['ward_name'] = ward_name
            if zoom_level:
                valid_params['zoom_level'] = zoom_level
            
            from app.tools.settlement_visualization_tools import create_settlement_map
            
            result = create_settlement_map(**valid_params)
            
            if result.get('status') == 'success':
                message = result.get('message', f'Settlement map created')
                
                # Add ward-specific information
                if ward_name:
                    message += f" for {ward_name} ward"
                
                # Auto-explain the visualization if file_path exists
                if result.get('file_path'):
                    explanation = self._explain_visualization_universally(
                        result['file_path'], 'settlement_map', session_id
                    )
                    message += f"\n\n{explanation}"
                
                # Return structured response
                if result.get('web_path'):
                    return {
                        'response': message,
                        'visualizations': [{
                            'type': 'settlement_map',
                            'file_path': result.get('file_path', ''),
                            'path': result.get('web_path', ''),
                            'url': result.get('web_path', ''),
                            'title': f"Settlement Map{' - ' + ward_name if ward_name else ''}",
                            'description': f"Building classification map showing settlement types{' for ' + ward_name + ' ward' if ward_name else ''}"
                        }],
                        'tools_used': ['create_settlement_map'],
                        'status': 'success'
                    }
                else:
                    return message
            else:
                return f"Error creating settlement map: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error creating settlement map: {str(e)}"
    
    def _show_settlement_statistics(self, session_id: str):
        """Show comprehensive statistics about available settlement data."""
        try:
            from app.tools.settlement_visualization_tools import show_settlement_statistics
            
            result = show_settlement_statistics(session_id)
            
            if result.get('status') == 'success':
                message = result.get('message', 'Settlement statistics retrieved')
                
                # Enhance with AI explanation if available
                if result.get('ai_response'):
                    message = result['ai_response']
                
                return {
                    'response': message,
                    'tools_used': ['show_settlement_statistics'],
                    'status': 'success',
                    'data': result.get('data', {})
                }
            else:
                return f"Error getting settlement statistics: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error getting settlement statistics: {str(e)}"
    
    # NEW: ITN Planning Tool
    def _run_itn_planning(self, session_id: str, total_nets: Optional[int] = 10000, avg_household_size: Optional[float] = 5.0, urban_threshold: Optional[float] = 30.0, method: str = 'composite'):
        """Plan ITN (Insecticide-Treated Net) distribution AFTER analysis is complete.
        Use this tool when user wants to plan ITN distribution, allocate bed nets, or create intervention plans.
        This tool uses existing analysis rankings - DO NOT run analysis again if already complete.
        Keywords: ITN, bed nets, net distribution, intervention planning, allocate nets."""
        try:
            # Check if analysis is complete first
            session_context = self._get_session_context(session_id)
            analysis_complete = session_context.get('analysis_complete', False)
            
            # CRITICAL FIX: Also check for physical evidence (marker file)
            if not analysis_complete:
                from pathlib import Path
                marker_file = Path(f"instance/uploads/{session_id}/.analysis_complete")
                if marker_file.exists():
                    analysis_complete = True
                    logger.info(f"✅ Found .analysis_complete marker, overriding flag for ITN planning in {session_id}")
                    
                    # Update state to match evidence
                    try:
                        from app.core.workflow_state_manager import WorkflowStateManager
                        state_manager = WorkflowStateManager(session_id)
                        state_manager.update_state({
                            'analysis_complete': True
                        }, transition_reason="ITN tool found analysis evidence")
                    except Exception as e:
                        logger.warning(f"Could not update state: {e}")
            
            data_handler = self.data_service.get_handler(session_id)
            if not data_handler:
                return 'No data available. Please run analysis first.'
            
            ######################## NEW: DIRECT RANKINGS CHECK ########################
            # Just check the unified dataset - it has everything we need
            if hasattr(data_handler, 'unified_dataset') and data_handler.unified_dataset is not None:
                has_rankings = 'composite_rank' in data_handler.unified_dataset.columns or 'overall_rank' in data_handler.unified_dataset.columns
            else:
                # Try to load unified dataset
                data_handler._load_unified_dataset()
                has_rankings = (data_handler.unified_dataset is not None and 
                               ('composite_rank' in data_handler.unified_dataset.columns or 'overall_rank' in data_handler.unified_dataset.columns))
            
            if has_rankings:
                analysis_complete = True  # Override flag if rankings exist
                logger.info(f"Overrode analysis_complete to True based on unified dataset rankings for session {session_id}")
            ############################################################################
            
            if not analysis_complete:
                return 'Analysis has not been completed yet. Please run the malaria risk analysis first before planning ITN distribution.'
            
            from app.analysis.itn_pipeline import calculate_itn_distribution
            data_handler = self.data_service.get_handler(session_id)
            if not data_handler:
                return 'No data available. Please run analysis first.'
            
            # Check if unified dataset exists (it has all the rankings we need)
            if not hasattr(data_handler, 'unified_dataset') or data_handler.unified_dataset is None:
                # Try to load it
                data_handler._load_unified_dataset()
                if data_handler.unified_dataset is None:
                    return 'Analysis rankings not found. Please run the malaria risk analysis first to generate vulnerability rankings.'
            
            # If user didn't specify total_nets, ask for it
            if total_nets == 10000:  # Default value
                return {
                    'response': "I'm ready to help you plan ITN distribution! To create an optimal allocation plan, I need to know:\n\n1. **How many bed nets do you have available?** (e.g., 50000, 100000)\n2. **What's the average household size in your area?** (default is 5 people)\n\nFor example, you can say: 'I have 100000 nets and average household size is 6'",
                    'status': 'info',
                    'tools_used': ['run_itn_planning']
                }
            
            result = calculate_itn_distribution(data_handler, session_id, total_nets, avg_household_size, urban_threshold, method)
            if result['status'] != 'success':
                return f"Error: {result.get('message', 'Unknown error')}"
            
            # Format response with embed
            embed_url = f'/itn_embed/{session_id}'
            message = f"""**ITN Distribution Plan Generated**

📊 **Distribution Summary:**
- Total Nets Available: {result['stats']['total_nets']:,}
- Nets Allocated: {result['stats']['allocated']:,} 
- Wards with Full Coverage (100%): {result['stats']['fully_covered_wards']}
- Wards with Partial Coverage: {result['stats']['partially_covered_wards']}
- Total Wards Receiving Nets: {result['stats']['prioritized_wards']}

📈 **Population Impact:**
- Total Population: {result['stats']['total_population']:,}
- Population Covered: {result['stats']['covered_population']:,} ({result['stats']['coverage_percent']:.1f}%)

The map below shows ITN allocation focusing on complete coverage of highest-risk wards."""
            
            return {
                'response': message,
                'visualizations': [{'type': 'itn_map', 'path': result['map_path'], 'url': embed_url}],
                'status': 'success'
            }
        except Exception as e:
            return f"Error planning ITN: {str(e)}"
    
    # Helper Methods
    def _run_data_quality_check(self, session_id: str):
        """Check data quality including missing values, duplicates, and statistics."""
        try:
            import pandas as pd
            from pathlib import Path
            
            # Load the data
            session_folder = Path(f'instance/uploads/{session_id}')
            raw_data_path = session_folder / 'raw_data.csv'
            
            if not raw_data_path.exists():
                return "No data file found. Please upload data first."
            
            df = pd.read_csv(raw_data_path)
            
            # Calculate statistics
            total_missing = df.isnull().sum().sum()
            duplicates = df.duplicated().sum()
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            # Find malaria-relevant variables
            malaria_vars = []
            env_vars = []
            risk_vars = []
            
            for col in df.columns:
                col_lower = col.lower()
                if 'tpr' in col_lower or 'test' in col_lower or 'positive' in col_lower:
                    malaria_vars.append(col)
                elif any(x in col_lower for x in ['evi', 'ndvi', 'soil', 'rain', 'temp', 'humid']):
                    env_vars.append(col)
                elif any(x in col_lower for x in ['urban', 'housing', 'population', 'density']):
                    risk_vars.append(col)
            
            # Format response
            response = f"""**Data Quality Check Complete**

📊 Your dataset has {total_missing} total missing values (minimal impact on analysis).

✅ **{'No duplicate entries' if duplicates == 0 else f'{duplicates} duplicate entries found'}** - {'each ward has unique data' if duplicates == 0 else 'consider removing duplicates'}.

**Key Dataset Characteristics:**
• Both numeric indicators ({len(numeric_cols)}) and categorical identifiers ({len(categorical_cols)})

**Malaria-Relevant Variables Found:**
• **Health indicators**: {', '.join(malaria_vars[:3]) if malaria_vars else 'None detected'}
• **Environmental factors**: {', '.join(env_vars[:4]) if env_vars else 'None detected'}  
• **Risk modifiers**: {', '.join(risk_vars[:3]) if risk_vars else 'None detected'}

**Analysis Readiness: ✅ Ready**
Your data is suitable for analysis. You can now run comprehensive malaria risk assessment to identify priority wards for intervention.

Would you like me to:
• Run the full malaria risk analysis?
• Explore specific variables in detail?
• Create visualizations of key indicators?"""
            
            return response
            
        except Exception as e:
            return f"Error checking data quality: {str(e)}"

    def _get_tool_parameters(self, tool_name: str) -> Dict[str, Any]:
        """Get parameter schema for a tool."""
        base_params = {
            'type': 'object',
            'properties': {
                'session_id': {'type': 'string', 'description': 'Session identifier'}
            },
            'required': ['session_id']
        }
        
        if 'analysis' in tool_name:
            base_params['properties']['variables'] = {
                'type': 'array',
                'items': {'type': 'string'},
                'description': 'Optional custom variables for analysis. When specified, these will override automatic region-based selection.'
            }
        
        if 'map' in tool_name or 'plot' in tool_name:
            if tool_name == 'create_vulnerability_map':
                # For vulnerability map, method is optional - defaults to side-by-side comparison
                base_params['properties']['method'] = {
                    'type': 'string',
                    'enum': ['composite', 'pca'],
                    'description': 'Analysis method to visualize. If not specified, shows side-by-side comparison of both methods.'
                }
            else:
                base_params['properties']['method'] = {
                    'type': 'string',
                    'enum': ['composite', 'pca'],
                    'description': 'Analysis method to visualize'
                }
        
        if tool_name == 'execute_data_query':
            base_params['properties'].update({
                'query': {'type': 'string', 'description': 'Natural language query about the data'},
                'code': {'type': 'string', 'description': 'Optional Python code to execute'}
            })
            base_params['required'].append('query')
        
        if tool_name == 'execute_sql_query':
            base_params['properties'].update({
                'query': {
                    'type': 'string', 
                    'description': 'The SQL query string to execute on the dataframe. The table is always named "df". This parameter is REQUIRED and must contain a valid SQL query.',
                }
            })
            base_params['required'].append('query')
        
        if tool_name == 'explain_analysis_methodology':
            base_params['properties']['method'] = {
                'type': 'string',
                'enum': ['composite', 'pca', 'both'],
                'description': 'Which methodology to explain'
            }
        
        if tool_name == 'create_variable_distribution':
            base_params['properties']['variable_name'] = {
                'type': 'string',
                'description': 'The exact column name from the dataset to visualize on the map. This parameter is REQUIRED. Extract the variable name from the user request.',
            }
            base_params['required'].append('variable_name')
        
        if tool_name == 'create_settlement_map':
            base_params['properties'].update({
                'ward_name': {
                    'type': 'string',
                    'description': 'Optional specific ward name to highlight and focus on'
                },
                'zoom_level': {
                    'type': 'integer',
                    'description': 'Map zoom level (11=city view, 13=ward view, 15=detailed)',
                    'default': 11
                }
            })
        
        if tool_name == 'show_settlement_statistics':
            # No additional parameters needed - just session_id
            pass
        
        if tool_name == 'run_itn_planning':
            base_params['properties'].update({
                'total_nets': {
                    'type': 'integer',
                    'description': 'Total number of bed nets available for distribution (e.g., 50000, 100000)'
                },
                'avg_household_size': {
                    'type': 'number',
                    'description': 'Average household size in the area (default: 5.0)'
                },
                'urban_threshold': {
                    'type': 'number',
                    'description': 'Urban percentage threshold for prioritization (default: 30.0)'
                },
                'method': {
                    'type': 'string',
                    'enum': ['composite', 'pca'],
                    'description': 'Ranking method to use (default: composite)'
                }
            })
        
        return base_params
    
    

    def _build_system_prompt(self, session_context: Dict, session_id: str = None) -> str:
        """Build system prompt with industry best practices."""
        base_prompt = """You are ChatMRPT, an AI-powered malaria risk assessment assistant with epidemiological expertise.

## CONTEXT & OBJECTIVE
You help public health professionals analyze malaria risk data and plan interventions. Your responses combine WHO-verified knowledge with data-driven insights when user data is available.

## SAFETY GUIDELINES
- You provide epidemiological analysis, NOT medical diagnosis or treatment advice
- Always clarify you're an AI tool, not a replacement for healthcare professionals  
- When discussing interventions, emphasize consultation with local health authorities
- Flag any data anomalies or concerning patterns for human review

## CAPABILITIES FRAMEWORK

### 1. GENERAL KNOWLEDGE MODE (No upload required)
When users ask about malaria epidemiology, statistics, or general information:

**Approach**: Provide comprehensive, evidence-based information
**Sources**: WHO data, peer-reviewed research, established epidemiological principles
**Examples**:
- "What countries are most affected?" → Cite WHO World Malaria Report statistics
- "How many deaths annually?" → Provide latest global burden estimates (2022: ~608,000 deaths)
- "Prevention strategies?" → Explain ITNs, IRS, chemoprevention, vaccines

### 2. DATA ANALYSIS MODE (Requires user data)
When users request analysis of their specific dataset:

**Approach**: Use Chain-of-Thought reasoning
**Process**:
1. Verify data availability and structure
2. Query to understand data distribution
3. Calculate relevant statistics
4. Interpret in epidemiological context
5. Provide actionable recommendations

**Examples**:
- "Analyze my ward data" → Check data, run analysis, interpret
- "Which areas need intervention?" → Query risk scores, rank, recommend

## RESPONSE STRUCTURE

### For General Questions:
1. **Direct Answer**: Provide the requested information immediately
2. **Context**: Add relevant epidemiological context
3. **Statistics**: Include specific numbers when available
4. **Implications**: Explain what this means for malaria control

### For Data Analysis:
1. **Data Verification**: Confirm what data you're analyzing
2. **Methodology**: Briefly explain your analytical approach
3. **Key Findings**: Present main results with interpretations
4. **Risk Factors**: Identify driving factors
5. **Recommendations**: Suggest evidence-based interventions

## CHAIN-OF-THOUGHT REASONING
For complex queries, break down your thinking:
- Step 1: Understand the question scope
- Step 2: Determine if data is needed
- Step 3: Execute appropriate analysis
- Step 4: Interpret results in context
- Step 5: Formulate actionable insights

## TONE & STYLE
- **Professional**: Use epidemiological terminology appropriately
- **Accessible**: Explain complex concepts clearly
- **Action-oriented**: Focus on practical applications
- **Evidence-based**: Ground statements in data or citations

## ERROR HANDLING
- If data is corrupted: "I notice potential data quality issues in [column]. Please verify..."
- If analysis fails: "I encountered an error analyzing [aspect]. Let me try an alternative approach..."
- If question unclear: "To provide the most accurate response, could you clarify..."

## QUALITY ASSURANCE
Before responding, verify:
✓ Is my response grounded in evidence?
✓ Have I distinguished between general knowledge and user data insights?
✓ Are my recommendations appropriate for the context?
✓ Is my response actionable and clear?

## Current Session"""
        
        context_info = f"""
- Geographic Area: {session_context.get('state_name', 'Not specified')}
- Data Status: {session_context.get('current_data', 'No data uploaded')}
- Analysis Complete: {session_context.get('analysis_complete', False)}
"""
        
        if session_context.get('data_schema'):
            context_info += f"- {session_context['data_schema']}\\n"
        
        # Add stage-specific guidance based on data and analysis state
        if session_context.get('analysis_complete', False):
            # POST-ANALYSIS STAGE
            
            # Get actual column names from context
            columns = session_context.get('columns', [])
            ward_col = session_context.get('ward_column', 'WardName')
            
            # Build column schema string (py-sidebot style but domain-aware)
            column_info = ""
            
            # Get dataframe from context
            df = None
            try:
                from ..core.unified_data_state import get_data_state
                data_state = get_data_state(session_id)
                df = data_state.current_data
            except:
                pass
            
            # Initialize variables_used outside the conditional block
            variables_used = session_context.get('variables_used', [])
                
            if columns and df is not None:
                # Separate computed vs original columns
                computed_cols = ['composite_score', 'composite_rank', 'composite_category', 
                               'pca_score', 'pca_rank', 'vulnerability_category', 'overall_rank']
                
                column_info = f"""
## TABLE SCHEMA: df
### Analysis Results (ALWAYS PRESENT):
- {ward_col} (TEXT) - Ward identifier
- composite_score (FLOAT) - Range: {df['composite_score'].min():.3f} to {df['composite_score'].max():.3f}
- composite_rank (INTEGER) - Range: 1 to {len(df)}
- composite_category (TEXT) - Values: 'High Risk', 'Medium Risk', 'Low Risk'
- pca_score (FLOAT) - Range: {df['pca_score'].min():.3f} to {df['pca_score'].max():.3f}
- pca_rank (INTEGER) - Range: 1 to {len(df)}
- vulnerability_category (TEXT) - Values: 'High Risk', 'Medium Risk', 'Low Risk'

### Key Risk Factors Used in Analysis:
"""
                # Add the variables that were actually used in the analysis
                if variables_used:
                    for var in variables_used[:7]:  # Show up to 7 key variables
                        if var in df.columns:
                            if pd.api.types.is_numeric_dtype(df[var]):
                                column_info += f"- {var} (FLOAT) - Range: {df[var].min():.3f} to {df[var].max():.3f}\n"
                            else:
                                unique_vals = df[var].nunique()
                                if unique_vals <= 10:
                                    vals = df[var].unique()[:5]
                                    column_info += f"- {var} (TEXT) - Values: {', '.join(map(str, vals))}\n"
                                else:
                                    column_info += f"- {var} (TEXT) - {unique_vals} unique values\n"
                
                # Count remaining columns
                shown_cols = set([ward_col] + computed_cols + variables_used[:7])
                remaining = len(columns) - len(shown_cols)
                if remaining > 0:
                    column_info += f"\n... and {remaining} more columns available for detailed queries"
            
            # Build dynamic SQL example for "Why is X ward ranked high?"
            # Include analysis columns plus any numeric variables that were used
            detail_columns = [ward_col, 'composite_score', 'composite_rank', 'pca_score', 'pca_rank']
            if variables_used and df is not None:
                # Add up to 5 numeric variables that were actually used in the analysis
                for var in variables_used[:5]:
                    if var in df.columns and pd.api.types.is_numeric_dtype(df[var]):
                        detail_columns.append(var)
            detail_columns_str = ', '.join(detail_columns)
            
            stage_guidance = f"""
## DATA ACCESS: Post-Analysis Stage
You now have access to the UNIFIED DATASET with all computed results.
{column_info}

IMPORTANT: Users want to see RESULTS, not column names:
- ❌ WRONG: "Let me check the data structure" → SELECT * FROM df LIMIT 1
- ✅ RIGHT: "Here are the top 10 highest risk wards" → SELECT {ward_col}, composite_score, vulnerability_category FROM df ORDER BY composite_score DESC LIMIT 10

Example queries for common questions (using actual column names from schema above):
- "Show top vulnerable wards" → SELECT {ward_col}, composite_score, vulnerability_category FROM df ORDER BY composite_score DESC LIMIT 10
- "Why is X ward ranked high?" → SELECT {detail_columns_str} FROM df WHERE {ward_col} = 'X'
- "High risk areas" → SELECT {ward_col}, composite_score, vulnerability_category FROM df WHERE vulnerability_category = 'High Risk'
- "Compare methods" → SELECT {ward_col}, composite_rank, pca_rank, ABS(composite_rank - pca_rank) as rank_diff FROM df ORDER BY rank_diff DESC LIMIT 20
- "Summary statistics" → Use execute_data_query: "provide summary statistics of analysis results"

FOCUS ON INSIGHTS: When showing rankings, include only the most relevant columns for the user's question.
"""
        elif session_context.get('data_loaded', False):
            # PRE-ANALYSIS STAGE
            
            # Get actual column names from context
            columns = session_context.get('columns', [])
            ward_col = session_context.get('ward_column', 'WardName')
            
            column_list = ""
            
            # Get dataframe for schema
            df = None
            try:
                from ..core.unified_data_state import get_data_state
                data_state = get_data_state(session_id)
                df = data_state.current_data
            except:
                pass
                
            if columns and df is not None:
                column_list = f"""
## TABLE SCHEMA: df ({len(df)} rows, {len(columns)} columns)
### Ward Identifier: {ward_col}
### Sample Columns:
"""
                # Show first 10-15 columns with type info
                for col in columns[:15]:
                    if col in df.columns:
                        if pd.api.types.is_numeric_dtype(df[col]):
                            col_min = df[col].min()
                            col_max = df[col].max()
                            column_list += f"- {col} (FLOAT) - Range: {col_min:.3f} to {col_max:.3f}\n"
                        else:
                            unique_vals = df[col].nunique()
                            if unique_vals <= 10:
                                vals = df[col].unique()[:5]
                                column_list += f"- {col} (TEXT) - Values: {', '.join(map(str, vals))}\n"
                            else:
                                column_list += f"- {col} (TEXT) - {unique_vals} unique values\n"
                
                if len(columns) > 15:
                    column_list += f"\n... and {len(columns) - 15} more columns available"
            
            stage_guidance = f"""
## DATA ACCESS: Pre-Analysis Stage  
You have access to the RAW uploaded data.
{column_list}

For ANY data question - use the actual column names:
- "What variables are in my data?" → List the columns shown above
- "Show me sample data" → SELECT {', '.join(columns[:5]) if columns else '*'} FROM df LIMIT 5
- "Data summary" → Use execute_data_query for statistics

After exploring, suggest: "Would you like me to run malaria risk analysis on this data?"
"""
        else:
            # NO DATA STAGE
            stage_guidance = """
## DATA ACCESS: No Data Uploaded
No data is currently loaded. Guide the user to upload their CSV data and shapefile.
"""
        
        # Get ward column for examples
        ward_col = session_context.get('ward_column', 'WardName')
        
        # Build dynamic detail columns based on what's available
        if session_context.get('analysis_complete', False):
            # Post-analysis: use the same detail columns from above
            detail_example = detail_columns_str if 'detail_columns_str' in locals() else f"{ward_col}, composite_score, composite_rank, pca_score, pca_rank"
        else:
            # Pre-analysis: just show ward column
            detail_example = ward_col
        
        tool_guidance = f"""{stage_guidance}
## Tool Selection Guide

CRITICAL: Understand user INTENT before selecting tools:

**INTENT: Get Specific Data (rankings, filtering, top/bottom)**
Use execute_sql_query with FOCUSED queries (NEVER use SELECT * - always specify columns):
- "Show top 10 highest risk wards" → query="SELECT {ward_col}, composite_score, vulnerability_category FROM df ORDER BY composite_score DESC LIMIT 10"
- "List high risk areas" → query="SELECT {ward_col}, composite_score FROM df WHERE vulnerability_category = 'High Risk'"
- "Why is X ward ranked high?" → query="SELECT {detail_example} FROM df WHERE {ward_col} = 'X'"
- "Average composite score" → query="SELECT AVG(composite_score) as avg_score FROM df"

**INTENT: Analyze Relationships or Complex Statistics**
Use execute_data_query with Python code, then INTERPRET the results:
- "Correlation between X and Y" → query="correlation analysis between [column1] and [column2]" → Explain what correlation means
- "Compare PCA vs composite methods" → query="compare ranking methods PCA vs composite" → Interpret which method better captures risk
- "Distribution of risk scores" → query="analyze distribution of composite scores" → Explain what the distribution reveals about risk patterns
- "Statistical summary" → query="comprehensive statistical analysis" → Interpret key findings for malaria control

**INTENT: Check Schema/Structure (ONLY when explicitly asked)**
- "What columns do I have?" → execute_sql_query with query="SELECT * FROM df LIMIT 1"
- "Tell me about my variables" → execute_sql_query with query="SELECT * FROM df LIMIT 1"

**INTENT: Create Visualizations**
- "Map the rainfall" → create_variable_distribution with variable_name="rainfall"
- "Show vulnerability map" → create_vulnerability_map (NO method parameter - shows side-by-side comparison)
- "Show composite vulnerability map" → create_vulnerability_map with method="composite"
- "Show PCA vulnerability map" → create_vulnerability_map with method="pca"
- "Box plot of scores" → create_box_plot with method="composite"

**INTENT: Plan Interventions (ITN Distribution)**
CRITICAL: Check analysis_complete status FIRST!

If analysis_complete = True and user mentions ITN/nets/distribution:
- "Plan ITN distribution" → run_itn_planning (DO NOT run analysis again!)
- "I want to distribute bed nets" → run_itn_planning 
- "Help with net distribution" → run_itn_planning
- "ITN allocation based on rankings" → run_itn_planning
- "Intervention planning" → run_itn_planning

PARAMETER EXTRACTION for run_itn_planning:
- "I have 100000 nets" → extract total_nets=100000
- "50000 bed nets available" → extract total_nets=50000
- "average household size is 4" → extract avg_household_size=4
- "household size of 6" → extract avg_household_size=6
- "I have 100000 nets and average household size is 4" → extract BOTH parameters
- Always extract numbers from the user's message and pass them as parameters

If analysis_complete = False but user asks about ITN:
- First run_complete_analysis, THEN automatically proceed to run_itn_planning
- Don't ask for confirmation if user already expressed intent

NEVER run_complete_analysis if analysis is already complete!

REMEMBER: 
1. For RANKING/FILTERING questions → Jump straight to the data query
2. For ANALYSIS questions → Use Python for complex operations
3. ONLY check schema when user explicitly asks about columns/variables
4. Extract exact parameter values from user's message
5. For ITN/distribution planning → Check if analysis is complete first

## CRITICAL: INTERPRETIVE REASONING FOR ALL RESPONSES

**MANDATORY: After EVERY data operation (SQL, Python, or any analysis), you MUST provide interpretation:**

1. NEVER just show raw results from ANY tool (SQL queries, Python code, data analysis, etc.)
2. ALWAYS explain what the values mean epidemiologically  
3. For "why" questions, identify the PRIMARY drivers of risk
4. Connect ALL data outputs to real-world malaria transmission factors
5. After Python analysis, explain the findings in context, not just show numbers
6. For visualizations, describe what patterns indicate about malaria risk

When showing ward rankings or data values, don't just list numbers. EXPLAIN what they mean:

### Response Structure:
1. **Present the data** (query results)
2. **Interpret the values** - explain what the numbers mean epidemiologically
3. **Explain the "why"** - connect values to malaria transmission risk
4. **Provide insights** - actionable recommendations based on the data

### Malaria Risk Interpretation Guide:
- **Malaria prevalence (pfpr)**: >50% = very high transmission, 20-50% = high, 5-20% = moderate, <5% = low
- **Housing quality**: Lower scores = poor construction allowing mosquito entry
- **Rainfall**: >800mm/year = high mosquito breeding potential
- **Temperature**: 20-30°C = optimal for mosquito survival and parasite development
- **Population density**: Higher density = more transmission opportunities
- **Healthcare access**: Lower access = delayed treatment, maintaining transmission
- **Poverty indicators**: Higher poverty = limited prevention resources

### Example Response Patterns:

❌ **WRONG** (data dump):
"Gwale: composite_score: 0.823, pfpr: 0.67, housing_quality: 0.21"

✅ **RIGHT** (interpretive):
"Gwale ward has the highest malaria risk (score: 0.823) due to:
- Very high malaria prevalence (67% pfpr) indicating intense ongoing transmission
- Poor housing conditions (0.21 quality score) that allow easy mosquito entry
- These factors create ideal conditions for sustained malaria transmission"

❌ **WRONG** (just listing):
"Top 5 wards: Gwale, Kumbotso, Tarauni, Nasarawa, Dala"

✅ **RIGHT** (explaining):
"The top 5 highest-risk wards for ITN distribution are:
1. Gwale - Very high transmission (67% pfpr) with poor housing
2. Kumbotso - High child vulnerability (45% under-5) with moderate transmission
3. Tarauni - Dense population with limited healthcare access
4. Nasarawa - High poverty levels limiting prevention resources
5. Dala - Environmental factors (flooding) creating breeding sites"

❌ **WRONG** (Python analysis dump):
"Correlation matrix:
pfpr vs rainfall: 0.67
pfpr vs housing: -0.82"

✅ **RIGHT** (interpretive analysis):
"The correlation analysis reveals key malaria transmission patterns:
- Strong positive correlation (0.67) between rainfall and malaria prevalence, confirming that increased precipitation creates mosquito breeding sites
- Strong negative correlation (-0.82) between housing quality and malaria, showing poor housing allows mosquito entry
These relationships validate targeting areas with high rainfall and poor housing for ITN distribution."

### For "Why" Questions:
When users ask "why is X ward ranked high/low?", provide comprehensive explanations:
1. Show the specific risk factor values
2. Explain how each factor contributes to malaria risk
3. Identify the PRIMARY drivers of the ranking
4. Compare to ward averages when relevant
5. **Use the METHOD to explain the ranking:**

**Composite Score Interpretation:**
- High composite = "Multiple combined risk factors" (it's in the name - COMPOSITE)
- The ward has problems across MANY dimensions simultaneously
- Example: "Kafin Dabga ranks #1 by composite because it combines moderate-high values across pfpr (30%), poor housing (0.043), high rainfall (73.9mm), creating a perfect storm of risk factors"

**PCA Score Interpretation:**
- High PCA = "Strongly matches the dominant malaria risk pattern in your data"
- The ward aligns with the main axis of variation (PC1) 
- Example: "This ward ranks high in PCA because it exemplifies the typical high-risk profile: environmental vulnerability + poor infrastructure"

**When Methods Disagree:**
- Composite high, PCA low = "Broad but moderate risk" - consistently bad but not extreme
- PCA high, Composite low = "Specific severe vulnerabilities" - extreme in key correlated factors
- Agreement = "Clear priority" - both broad AND severe risk

ALWAYS aim to help users understand not just WHAT the data shows, but WHY it matters for malaria control.

## FINAL REMINDER: NO RAW DATA DUMPS

After EVERY tool use (SQL, Python, visualizations, analysis):
1. Present the data/results
2. IMMEDIATELY provide epidemiological interpretation
3. Explain implications for malaria control
4. NEVER end a response with just numbers or raw output

Your expertise adds value through interpretation, not just data retrieval."""
        
        return f"{base_prompt}{context_info}{tool_guidance}"
    
    def _simple_conversational_response(self, user_message: str, session_context: Dict, session_id: str = None) -> Dict[str, Any]:
        """Simple conversational response when no data available."""
        # Check if LLM manager is available
        if self.llm_manager is None:
            logger.error("LLM manager is not initialized")
            return {
                'response': "I'm having trouble connecting to the language model. Please try again in a moment.",
                'tools_used': [],
                'status': 'error'
            }
        
        system_prompt = self._build_system_prompt(session_context, session_id)
        
        response = self.llm_manager.generate_response(
            prompt=user_message,
            system_message=system_prompt,
            temperature=0.7
        )
        
        return {
            'response': response,
            'tools_used': [],
            'status': 'success'
        }
    
    def _get_session_context(self, session_id: str, session_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get comprehensive session context using centralized state manager."""
        try:
            # Use provided session data or try to get from Flask session
            if session_data is None:
                try:
                    from flask import session
                    session_data = dict(session)
                except RuntimeError:
                    # Working outside of request context, use empty session
                    session_data = {}
            
            # Use WorkflowStateManager as single source of truth
            from .workflow_state_manager import WorkflowStateManager
            state_manager = WorkflowStateManager(session_id)
            workflow_info = state_manager.get_workflow_info()
            
            # Check data availability from state manager
            import os
            from pathlib import Path
            
            upload_folder = os.environ.get('UPLOAD_FOLDER', 'instance/uploads')
            session_folder = Path(upload_folder) / session_id
            
            # Check if folder exists and has data files
            has_actual_data = False
            if session_folder.exists():
                # Check for actual data files
                raw_data = session_folder / 'raw_data.csv'
                processed_data = session_folder / 'processed_data.csv'
                has_actual_data = raw_data.exists() or processed_data.exists()
            
            # Consider data loaded if:
            # 1. Session flags say so AND files exist, OR
            # 2. We have data in our session_data cache, OR
            # 3. Agent state file says data is loaded (from V3 system)
            agent_state_loaded = False
            agent_state_file = session_folder / '.agent_state.json'
            if agent_state_file.exists():
                try:
                    import json
                    with open(agent_state_file, 'r') as f:
                        agent_state = json.load(f)
                        agent_state_loaded = agent_state.get('data_loaded', False) or agent_state.get('csv_loaded', False)
                        
                        # CRITICAL FIX: Sync Flask session IMMEDIATELY when agent state shows data loaded
                        # This must happen BEFORE we check data_loaded to avoid circular dependency
                        if (agent_state.get('data_loaded', False) or agent_state.get('csv_loaded', False)):
                            # Check if files actually exist
                            import os
                            from pathlib import Path
                            session_folder = Path(f"{upload_folder}/{session_id}")
                            has_csv = (session_folder / 'raw_data.csv').exists() or (session_folder / 'data_analysis.csv').exists()
                            has_shapefile = (session_folder / 'raw_shapefile.zip').exists()
                            
                            if has_csv:
                                # Update Flask session IMMEDIATELY with Redis-compatible approach
                                from flask import session
                                if not session.get('csv_loaded', False):
                                    # Set all flags
                                    session['data_loaded'] = True
                                    session['csv_loaded'] = True
                                    session['shapefile_loaded'] = has_shapefile
                                    # CRITICAL for Redis: Set permanent and force modification
                                    session.permanent = True
                                    session.modified = True
                                    # Force re-assignment to trigger Redis update
                                    session['session_id'] = session.get('session_id', session_id)
                                    
                                    logger.info(f"✅ IMMEDIATE Flask session sync from agent state for {session_id}")
                                    logger.info(f"   Files exist: CSV={has_csv}, Shapefile={has_shapefile}")
                                    logger.info(f"   Session flags updated: data_loaded=True, csv_loaded=True")
                                    logger.info(f"   Redis session marked as permanent and modified")
                except Exception as e:
                    logger.debug(f"Could not read agent state: {e}")
            
            # CRITICAL FIX: Trust agent state if it says data is loaded and files exist
            # This handles V3 transitions where Flask session might not have the flags
            data_loaded = (
                (session_data.get('data_loaded', False) or 
                 session_data.get('csv_loaded', False) or
                 session_id in self.session_data or  # Check our internal cache
                 (agent_state_loaded and has_actual_data))  # Trust agent state if files exist
            )
            
            # CRITICAL: If we determined data is loaded based on agent state, update Flask session
            if data_loaded and agent_state_loaded and has_actual_data and not session_data.get('csv_loaded', False):
                from flask import session
                session['data_loaded'] = True
                session['csv_loaded'] = True
                session['shapefile_loaded'] = os.path.exists(session_folder / 'raw_shapefile.zip')
                session.modified = True  # Ensure changes persist
                logger.info(f"🔄 Updated Flask session flags based on agent state for {session_id}")
            
            # If data is loaded but not in our cache, populate it
            if data_loaded and session_id not in self.session_data and has_actual_data:
                try:
                    import pandas as pd
                    # Try to load the data file
                    raw_data_path = session_folder / 'raw_data.csv'
                    if raw_data_path.exists():
                        df = pd.read_csv(raw_data_path)
                        self.session_data[session_id] = {
                            'data': df,
                            'columns': list(df.columns),
                            'shape': df.shape
                        }
                        logger.info(f"Loaded data from V3 transition: {df.shape}")
                        
                        # CRITICAL FIX: Synchronize Flask session flags when loading from V3
                        # This ensures tool execution works after TPR workflow transition
                        if agent_state_loaded and has_actual_data:
                            # Update Flask session to match agent state
                            from flask import session
                            session['data_loaded'] = True
                            session['csv_loaded'] = True
                            session['shapefile_loaded'] = os.path.exists(session_folder / 'raw_shapefile.zip')
                            session.modified = True  # Ensure changes persist
                            logger.info(f"✅ Synchronized Flask session flags after V3 transition for {session_id}")
                            logger.info(f"   Flask session now has: data_loaded={session.get('data_loaded')}, csv_loaded={session.get('csv_loaded')}, shapefile_loaded={session.get('shapefile_loaded')}")
                except Exception as e:
                    logger.error(f"Failed to load transition data: {e}")
            
            # Use state manager for analysis_complete check with proper validation
            analysis_complete = workflow_info['analysis_complete']
            data_loaded = workflow_info['data_loaded']
            
            # Validate state and FIX inconsistencies (trust evidence!)
            validation_issues = state_manager.validate_state()
            if validation_issues:
                logger.warning(f"⚠️ State validation issues for {session_id}: {validation_issues}")
                
                # FIX: Trust marker files as evidence, update state to match
                if "Marker file exists but state flag is False" in validation_issues:
                    marker_file = session_folder / ".analysis_complete"
                    if marker_file.exists():
                        # UPDATE STATE to match evidence, don't delete evidence!
                        state_manager.update_state({
                            'analysis_complete': True
                        }, transition_reason="Syncing state with marker evidence")
                        logger.info(f"✅ Updated state to match .analysis_complete marker for {session_id}")
                        
                        # Also update the context we're building
                        analysis_complete = True
            
            context = {
                'data_loaded': data_loaded,
                'state_name': session_data.get('state_name', 'Not specified'),
                'current_data': f"CSV loaded: {session_data.get('csv_loaded', False)}, Shapefile: {session_data.get('shapefile_loaded', False)}" if data_loaded else "No data uploaded",
                'analysis_complete': analysis_complete,
                'ward_column': session_data.get('ward_column', 'Not identified'),
                'variables_used': session_data.get('variables_used', []),
                'conversation_history': self.conversation_history.get(session_id, [])
            }
            
            # Add detailed data schema if available (py-sidebot pattern)
            if data_loaded and self.data_service:
                try:
                    # Get the appropriate dataset based on analysis stage
                    from ..core.unified_data_state import get_data_state
                    data_state = get_data_state(session_id)
                    df = data_state.current_data
                    
                    if df is not None:
                        # Basic info
                        context['data_schema'] = f"Dataset: {len(df)} rows, {len(df.columns)} columns"
                        
                        # Detailed column information for SQL generation
                        context['columns'] = list(df.columns)
                        
                        # Identify key columns
                        ward_cols = [col for col in df.columns if 'ward' in col.lower()]
                        if ward_cols:
                            context['ward_column'] = ward_cols[0]
                        
                        # Post-analysis specific columns
                        if session_data.get('analysis_complete', False):
                            score_cols = [col for col in df.columns if 'score' in col or 'rank' in col]
                            context['analysis_columns'] = score_cols
                            
                            # Sample data for context
                            if 'composite_score' in df.columns:
                                context['score_range'] = {
                                    'min': float(df['composite_score'].min()),
                                    'max': float(df['composite_score'].max())
                                }
                                
                except Exception as e:
                    logger.debug(f"Could not get detailed schema: {e}")
            
            # Add memory context if available
            if self.memory:
                try:
                    memory_context = self.memory.get_context(session_id)
                    if memory_context:
                        context['recent_topics'] = getattr(memory_context, 'entities_mentioned', [])[:5]
                except Exception as e:
                    logger.debug(f"Memory context error: {e}")
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting session context: {e}")
            return {'data_loaded': False, 'state_name': 'Not specified'}
    
    def _is_data_analysis_query(self, message: str) -> bool:
        """
        Detect if the message is a data analysis query.
        
        Data analysis indicators:
        - Questions about data exploration
        - Statistical analysis requests
        - Trend analysis
        - Comparisons and correlations
        - Summary statistics
        """
        message_lower = message.lower()
        
        # Data analysis keywords
        data_keywords = [
            'how many', 'what is the', 'show me', 'analyze', 'compare',
            'trend', 'pattern', 'distribution', 'correlation', 'average',
            'mean', 'median', 'sum', 'count', 'unique', 'values',
            'highest', 'lowest', 'maximum', 'minimum', 'range',
            'group by', 'filter', 'where', 'sort', 'top', 'bottom',
            'statistics', 'summary', 'describe', 'overview', 'insights',
            'what are', 'list', 'show', 'display', 'which', 'how much'
        ]
        
        # Check for data analysis indicators
        return any(keyword in message_lower for keyword in data_keywords)
    
    def _handle_special_workflows(self, user_message: str, session_id: str, session_data: Dict[str, Any] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Handle special workflows like permissions, forks, data analysis, and TPR."""
        if session_data is None:
            try:
                from flask import session
                session_data = dict(session)
            except RuntimeError:
                # Working outside of request context
                session_data = {}
        
        # Priority 1: Check if Data Analysis tab is ACTIVE and has uploaded data
        # CRITICAL: Only activate V3 when user is explicitly in Data Analysis tab
        # This prevents V3 from intercepting normal chat messages
        
        # Check if user is in Data Analysis tab (sent from frontend)
        is_data_analysis_request = kwargs.get('is_data_analysis', False)
        tab_context = kwargs.get('tab_context', '')
        
        logger.info(f"🔍 Data Analysis check: is_data_analysis={is_data_analysis_request}, tab_context={tab_context}, session_id={session_id}")
        
        # Also check file-based flag for cross-worker compatibility
        has_data_analysis_flag = False
        if session_id and is_data_analysis_request:  # Only check flag if in data analysis context
            import os
            from flask import current_app
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
            upload_folder = str(upload_folder)
            flag_file = os.path.join(upload_folder, session_id, '.data_analysis_mode')
            
            logger.info(f"🔍 Data Analysis tab active, checking for flag: {flag_file}")
            has_data_analysis_flag = os.path.exists(flag_file)
            logger.info(f"🔍 Flag exists: {has_data_analysis_flag}")
            
            # If not found locally, try to sync from other instances
            if not has_data_analysis_flag:
                try:
                    from app.core.simple_instance_check import check_and_sync_session
                    if check_and_sync_session(session_id):
                        has_data_analysis_flag = True
                        logger.info(f"🔄 Session {session_id} retrieved from another instance")
                except Exception as e:
                    logger.debug(f"Could not check other instance: {e}")
        
        # Check if workflow has already transitioned (prevents re-routing)
        # CRITICAL: Check this ALWAYS, not just when flag exists
        import os  # Ensure os is available for path operations
        # CRITICAL: Check this ALWAYS, not just when flag exists
        workflow_transitioned = False
        if session_id:  # Check for ANY session, not just ones with flag
            try:
                # Check the agent state file for workflow transition
                state_file = os.path.join(upload_folder, session_id, '.agent_state.json')
                if os.path.exists(state_file):
                    import json
                    with open(state_file, 'r') as f:
                        state = json.load(f)
                        workflow_transitioned = state.get('workflow_transitioned', False)
                        if workflow_transitioned:
                            logger.info(f"🚫 Workflow has transitioned - NOT routing to Data Analysis V3")
            except Exception as e:
                logger.debug(f"Could not check workflow transition state: {e}")
        
        # Only route to V3 if EXPLICITLY in Data Analysis context AND not transitioned
        if is_data_analysis_request and not workflow_transitioned and (session_data.get('has_data_analysis_file', False) or session_data.get('use_data_analysis_v3', False) or has_data_analysis_flag):
            logger.info(f"📊 Data Analysis V3 mode active - routing ALL queries to V3")
            logger.info(f"📊 Message: '{user_message[:50]}...'")
            
            # Don't check for data analysis keywords - route everything to V3
            if user_message != "__DATA_UPLOADED__":
                try:
                    # Check if data is available - look for uploaded files directly
                    import os
                    from flask import current_app
                    
                    # Get absolute path to upload directory
                    if current_app and hasattr(current_app, 'config'):
                        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
                    else:
                        upload_folder = 'instance/uploads'
                    
                    upload_dir = os.path.join(upload_folder, session_id)
                    has_data = False
                    
                    logger.info(f"📁 Checking for data in: {upload_dir}")
                    
                    if os.path.exists(upload_dir):
                        # Check for any data files
                        files = os.listdir(upload_dir)
                        data_files = [f for f in files if f.endswith(('.csv', '.xlsx', '.xls', '.json'))]
                        has_data = len(data_files) > 0
                        
                        logger.info(f"📊 Found {len(data_files)} data files: {data_files}")
                        
                        # Also check for standard data analysis files
                        if not has_data:
                            standard_files = ['data_analysis.csv', 'data_analysis.xlsx', 'data_analysis.json']
                            has_data = any(os.path.exists(os.path.join(upload_dir, f)) for f in standard_files)
                            if has_data:
                                logger.info(f"📊 Found standard data analysis file")
                    else:
                        logger.info(f"⚠️ Upload directory does not exist: {upload_dir}")
                    
                    if has_data:
                        logger.info("✅ Routing to Data Analysis V3 agent")
                        from app.data_analysis_v3 import DataAnalysisAgent
                        
                        # Create agent for this session
                        agent = DataAnalysisAgent(session_id)
                        
                        # Run analysis (synchronously for now)
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(agent.analyze(user_message))
                        loop.close()
                        
                        # Format response
                        response = {
                            'success': result.get('success', True),
                            'response': result.get('message', 'Analysis complete'),
                            'status': 'success',
                            'requires_permission': False,
                            'is_fork': False,
                            'analysis_type': 'data_analysis_v3',
                            'session_id': session_id,
                            'tools_used': ['analyze_data']
                        }
                        
                        # Add visualizations if present (check both keys for compatibility)
                        if result.get('visualization_data'):
                            response['visualizations'] = result['visualization_data']
                            logger.info(f"📊 Adding {len(result['visualization_data'])} visualizations from visualization_data")
                        elif result.get('visualizations'):
                            response['visualizations'] = result['visualizations']
                            logger.info(f"📊 Adding {len(result['visualizations'])} visualizations from visualizations")
                        
                        return response
                    else:
                        logger.info("❌ No data found for Data Analysis V3 - prompting for upload")
                        return {
                            'success': True,
                            'response': "Please upload your data file first. Click the upload button to select a CSV, Excel, or JSON file for analysis.",
                            'status': 'info',
                            'requires_permission': False
                        }
                        
                except Exception as e:
                    logger.error(f"Data Analysis V3 error: {str(e)}")
                    # Fall through to regular processing
                    pass
        
        # Handle data upload completion trigger
        if user_message == "__DATA_UPLOADED__":
            # Get data info from the actual uploaded files
            try:
                import pandas as pd
                from pathlib import Path
                
                upload_folder = os.environ.get('UPLOAD_FOLDER', 'instance/uploads')
                session_folder = Path(upload_folder) / session_id
                
                # Try to read the actual data file
                raw_data_path = session_folder / 'raw_data.csv'
                if raw_data_path.exists():
                    df = pd.read_csv(raw_data_path)
                    rows = len(df)
                    cols = len(df.columns)
                    
                    # Store in session for later access
                    self.session_data[session_id] = {
                        'data': df,
                        'columns': list(df.columns),
                        'shape': (rows, cols)
                    }
                else:
                    # Fallback to TPR results if available
                    tpr_results_path = session_folder / 'tpr_results.csv'
                    if tpr_results_path.exists():
                        df = pd.read_csv(tpr_results_path)
                        rows = len(df)
                        cols = len(df.columns)
                        
                        self.session_data[session_id] = {
                            'data': df,
                            'columns': list(df.columns),
                            'shape': (rows, cols)
                        }
                    else:
                        rows = 0
                        cols = 0
            except Exception as e:
                logger.warning(f"Could not load data for session {session_id}: {e}")
                rows = 0
                cols = 0
            except:
                rows = 0
                cols = 0
            
            state = session_data.get('state_name', 'your region')
            geopolitical_zone = session_data.get('geopolitical_zone', '')
            
            response = f"""I've loaded your data from {state}. It has {rows} rows and {cols} columns.

What would you like to do?
• I can help you map variable distribution
• Check data quality
• Explore specific variables
• Run malaria risk analysis to rank wards for ITN distribution
• Something else

Just tell me what you're interested in."""
            
            # Clear the permission flag
            if 'should_ask_analysis_permission' in session_data:
                try:
                    from flask import session as flask_session
                    flask_session['should_ask_analysis_permission'] = False
                except:
                    pass
            
            return {
                'response': response,
                'status': 'success',
                'tools_used': []
            }
        
        # Original permission workflow - only if user responds yes/no to permission question
        # Check all three places for the permission flag
        should_ask_permission = session_data.get('should_ask_analysis_permission', False)
        
        if not should_ask_permission:
            try:
                from flask import session as flask_session
                should_ask_permission = flask_session.get('should_ask_analysis_permission', False)
            except:
                pass
        
        # CRITICAL FIX: Also check session state manager
        if not should_ask_permission:
            try:
                # Skip session state check for now
                should_ask_permission = False
            except Exception as e:
                logger.debug(f"Session state check error: {e}")
        
        # Log once after all checks
        if should_ask_permission:
            logger.info(f"🎯 Permission flag found! User message: '{user_message}'")
        
        if should_ask_permission:
            # Check if this is a confirmation message
            logger.debug(f"Checking if '{user_message}' is a confirmation message")
            if self._is_confirmation_message(user_message):
                logger.info(f"✅ Confirmed! '{user_message}' detected as confirmation")
                logger.info("✅ User confirmed with 'yes' - executing automatic analysis...")
                # User said yes - run analysis
                result = self._execute_automatic_analysis(session_id)
                
                # Clear the permission flag in all places
                try:
                    from flask import session as flask_session
                    flask_session['should_ask_analysis_permission'] = False
                except:
                    pass
                
                try:
                    # Skip session state update for now
                    pass
                except:
                    pass
                
                return result
            else:
                # User said no or something else - clear flag and continue normally
                try:
                    from flask import session as flask_session
                    flask_session['should_ask_analysis_permission'] = False
                except:
                    pass
                # Continue with normal message processing
                return None
        
        # Data description workflow
        if session_data.get('should_describe_data', False):
            result = self._generate_automatic_data_description(session_id)
            self._store_conversation(session_id, user_message, result.get('response', ''))
            return result
        
        # Fork detection for what-if scenarios
        if 'what if' in user_message.lower() or 'suppose' in user_message.lower():
            fork_id = f"{session_id}_fork_{int(time.time())}"
            return {
                'response': f"🔀 **Exploring scenario**: {user_message}\\n\\nLet me help you explore this what-if scenario...",
                'status': 'success',
                'forked': True,
                'fork_id': fork_id
            }
        
        return None
    
    def _store_conversation(self, session_id: str, user_message: str, response: str):
        """Store conversation with memory integration."""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append({
            'user': user_message,
            'assistant': response,
            'timestamp': time.time()
        })
        
        # Keep only last 10 exchanges
        if len(self.conversation_history[session_id]) > 10:
            self.conversation_history[session_id] = self.conversation_history[session_id][-10:]
        
        # Store in memory if available
        if self.memory:
            try:
                self.memory.store_conversation_turn(
                    session_id=session_id,
                    user_message=user_message,
                    assistant_response=response,
                    timestamp=time.time()
                )
            except Exception as e:
                logger.debug(f"Memory storage error: {e}")
    
    def _explain_visualization_universally(self, viz_path: str, viz_type: str, session_id: str) -> str:
        """Universal visualization explanation."""
        try:
            from app.services.universal_viz_explainer import get_universal_viz_explainer
            explainer = get_universal_viz_explainer(llm_manager=self.llm_manager)
            return explainer.explain_visualization(viz_path, viz_type, session_id)
        except Exception as e:
            logger.error(f"Visualization explanation error: {e}")
            viz_name = viz_type.replace('_', ' ').title()
            return f"📊 **{viz_name} Created** - This visualization shows malaria risk analysis results for intervention planning."
    
    def _is_confirmation_message(self, message: str) -> bool:
        """Check if message is confirmation using dynamic detection."""
        msg = message.lower().strip()
        
        # Core confirmation words
        confirmation_words = {'yes', 'y', 'ok', 'okay', 'sure', 'proceed', 'continue', 'go', 'yep', 'yeah', 'affirmative'}
        negative_words = {'no', 'not', 'dont', "don't", 'cancel', 'stop', 'wait', 'hold'}
        
        # Split message into words
        words = msg.split()
        
        # Check if any word in the message is a confirmation word
        has_confirmation = any(word in confirmation_words for word in words)
        has_negative = any(word in negative_words for word in words)
        
        # If there's a negative word, it's not a confirmation
        if has_negative:
            return False
            
        # If there's at least one confirmation word and no negatives, it's a confirmation
        return has_confirmation
    
    def _execute_automatic_analysis(self, session_id: str) -> Dict[str, Any]:
        """Execute automatic analysis after permission."""
        try:
            # Use the RunCompleteAnalysis tool to get the comprehensive summary
            from app.tools.complete_analysis_tools import RunCompleteAnalysis
            tool = RunCompleteAnalysis()
            tool_result = tool.execute(session_id=session_id)
            
            if tool_result.success:
                return {
                    'response': tool_result.message,
                    'status': 'success',
                    'tools_used': ['runcompleteanalysis'],
                    'visualizations': tool_result.data.get('visualizations', []) if tool_result.data else []
                }
            else:
                return {
                    'response': tool_result.message,
                    'status': 'error',
                    'tools_used': ['runcompleteanalysis'],
                    'error_details': tool_result.error_details
                }
        except Exception as e:
            return {
                'response': f'Error running automatic analysis: {str(e)}',
                'status': 'error',
                'tools_used': []
            }
    
    def _generate_automatic_data_description(self, session_id: str) -> Dict[str, Any]:
        """Generate automatic data description."""
        try:
            result = self._execute_data_query(session_id, "Describe the uploaded dataset including number of wards, variables, and data quality")
            return {
                'response': result,
                'status': 'success',
                'tools_used': ['execute_data_query']
            }
        except Exception as e:
            return {
                'response': f'Error describing data: {str(e)}',
                'status': 'error',
                'tools_used': []
            }

    def _interpret_raw_output(self, raw_output: str, user_message: str, session_context: Dict, session_id: str) -> str:
        """Generate concise epidemiological interpretation of raw tool output."""
        try:
            if not raw_output.strip():
                return ""
            interpretation_prompt = f"""
User query: {user_message}
Raw results:
{raw_output.strip()[:1000]}
Interpret briefly in malaria context: explain key values, compare to dataset, suggest 1 action.
≤150 words.
"""
            system_prompt = self._build_system_prompt(session_context, session_id)
            return self.llm_manager.generate_response(
                prompt=interpretation_prompt,
                system_message=system_prompt,
                temperature=0.3,
                max_tokens=300,
                session_id=session_id
            ).strip()
        except Exception as e:
            logger.error(f"Interpretation failed: {e}")
            return ""
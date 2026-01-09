"""Streaming utilities for the request interpreter."""

from __future__ import annotations

import json
import logging
import time
import traceback
from typing import Any, Dict, Generator, Iterable

from flask import Response, current_app, jsonify, session

logger = logging.getLogger(__name__)

class StreamingMixin:
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
                    'download_links': special_result.get('download_links', []),
                    'tools_used': special_result.get('tools_used', []),
                    'done': True
                }
                return

            # Get session context
            session_context = self._get_session_context(session_id, session_data)
            session_context = self._enrich_session_context_with_memory(session_id, session_context)

            logger.info(f"🔍 Session context for {session_id}:")
            logger.info(f"   data_loaded: {session_context.get('data_loaded', False)}")
            logger.info(f"   has_csv: {session_context.get('csv_loaded', False)}")
            logger.info(f"   has_shapefile: {session_context.get('shapefile_loaded', False)}")
            logger.info(f"   current_data: {str(session_context.get('current_data', 'None'))[:100]}")
            logger.info(f"   session_data param keys: {list(session_data.keys())[:10] if session_data else 'None'}")
            logger.info(f"   kwargs: {kwargs}")

            direct_result = self._attempt_direct_tool_resolution(
                user_message,
                session_id,
                session_context,
            )
            if direct_result:
                self._store_conversation(session_id, user_message, direct_result.get('response', ''))
                yield {
                    'content': direct_result.get('response', ''),
                    'status': direct_result.get('status', 'success'),
                    'visualizations': direct_result.get('visualizations', []),
                    'download_links': direct_result.get('download_links', []),
                    'tools_used': direct_result.get('tools_used', []),
                    'debug': direct_result.get('debug'),
                    'done': True
                }
                return

            if not session_context.get('data_loaded', False):
                logger.info(f"❌ No data loaded, using conversational streaming")
                # Use streaming for conversational responses too
                if self.llm_manager and hasattr(self.llm_manager, 'generate_with_functions_streaming'):
                    system_prompt = self._build_system_prompt_refactored(session_context, session_id)

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

            # Stream with tools via orchestrator when available
            logger.info(f"✅ Data loaded! Streaming with tools")
            if self.tool_runner and self.orchestrator:
                system_prompt = self._build_system_prompt_refactored(session_context, session_id)
                function_schemas = self.tool_runner.get_function_schemas()
                yield from self.orchestrator.stream_with_tools(
                    self.llm_manager,
                    system_prompt,
                    user_message,
                    function_schemas,
                    session_id,
                    self.tool_runner,
                    interpretation_cb=lambda raw, _msg: self._interpret_raw_output(raw, _msg, session_context, session_id),
                )
            else:
                yield from self._stream_with_tools(user_message, session_context, session_id)

        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            yield {
                'content': f'I encountered an issue: {str(e)}',
                'status': 'error',
                'done': True
            }

    def _llm_with_tools(self, user_message: str, session_context: Dict, session_id: str) -> Dict[str, Any]:
        """Back-compat shim: delegate to orchestrator + tool_runner when available."""
        system_prompt = self._build_system_prompt_refactored(session_context, session_id)
        if self.tool_runner and self.orchestrator:
            schemas = self.tool_runner.get_function_schemas()
            return self.orchestrator.run_with_tools(
                self.llm_manager,
                system_prompt,
                user_message,
                schemas,
                session_id,
                self.tool_runner,
            )
        # Legacy path
        functions = []
        for tool_name, tool_func in self.tools.items():
            functions.append({
                'name': tool_name,
                'description': tool_func.__doc__ or f"Execute {tool_name}",
                'parameters': self._get_tool_parameters(tool_name)
            })
        response = self.llm_manager.generate_with_functions(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            functions=functions,
            temperature=0.7,
            session_id=session_id
        )
        return self._process_llm_response(response, user_message, session_id)

    def _stream_with_tools(self, user_message: str, session_context: Dict, session_id: str):
        """Stream LLM response with tools."""
        logger.info(f"🔧 _stream_with_tools called for session {session_id}")
        logger.info(f"📊 Data loaded status: {session_context.get('data_loaded', False)}")
        logger.info(f"📦 Session data cache has session: {session_id in self.session_data}")

        # CRITICAL FIX: Ensure data is loaded in session_data before tools are called
        # Load the appropriate dataset based on analysis completion status
        if session_context.get('data_loaded', False) and session_id not in self.session_data:
            try:
                import pandas as pd
                from pathlib import Path
                session_folder = Path(f'instance/uploads/{session_id}')

                # Check if analysis is complete and load appropriate file
                analysis_complete = session_context.get('analysis_complete', False)
                marker_file = session_folder / '.analysis_complete'

                # Prioritize unified dataset if analysis is complete
                if analysis_complete or marker_file.exists():
                    # Try unified dataset first
                    unified_path = session_folder / 'unified_dataset.csv'
                    if unified_path.exists():
                        df = pd.read_csv(unified_path)
                        logger.info(f"✅ Loaded unified dataset for tools: {df.shape} from {unified_path}")
                    else:
                        # Fall back to raw data if unified not found
                        raw_data_path = session_folder / 'raw_data.csv'
                        if raw_data_path.exists():
                            df = pd.read_csv(raw_data_path)
                            logger.info(f"⚠️ Analysis complete but unified dataset not found, loaded raw data: {df.shape}")
                else:
                    # Load raw data for pre-analysis stage
                    raw_data_path = session_folder / 'raw_data.csv'
                    if raw_data_path.exists():
                        df = pd.read_csv(raw_data_path)
                        logger.info(f"✅ Loaded raw data for tools: {df.shape} from {raw_data_path}")

                if 'df' in locals():
                    self.session_data[session_id] = {
                        'data': df,
                        'columns': list(df.columns),
                        'shape': df.shape
                    }
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

        system_prompt = self._build_system_prompt_refactored(session_context, session_id)

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
                logger.info(f"🔧 Tool call detected: {function_name} with args: {chunk['function_call']['arguments'][:100]}...")

                # BROWSER CONSOLE DEBUG: Send tool selection info to frontend
                debug_msg = f"🔧 TOOL SELECTED: {function_name}"
                logger.info(debug_msg)
                yield {
                    "content": f"<!-- DEBUG: {debug_msg} -->",
                    "status": "success",
                    "debug_tool_call": {
                        "tool_selected": function_name,
                        "tool_args": chunk["function_call"]["arguments"][:200] if chunk["function_call"].get("arguments") else "{}"
                    },
                    "done": False
                }

                # CRITICAL FIX: Use tool_runner for fuzzy name matching instead of direct dict lookup
                # This allows OpenAI to call tools with variations like "runmalariariskanalysis"
                # which will match "run_malaria_risk_analysis" via fuzzy matching
                if self.tool_runner:
                    try:
                        args_str = chunk['function_call']['arguments'] or '{}'
                        logger.info(f"🎯 Executing via tool_runner: {function_name}")
                        result_dict = self.tool_runner.execute(function_name, args_str)

                        # tool_runner.execute returns normalized dict with response/status/tools_used
                        # Convert to format expected by streaming code
                        if result_dict.get('status') == 'error':
                            logger.error(f"❌ Tool execution error: {result_dict.get('response')}")
                            yield {
                                'content': result_dict.get('response', 'Tool execution failed'),
                                'status': 'error',
                                'done': True
                            }
                            return

                        # Success - convert normalized result back to expected format
                        result = {
                            'response': result_dict.get('response', ''),
                            'status': result_dict.get('status', 'success'),
                            'visualizations': result_dict.get('visualizations', []),
                            'download_links': result_dict.get('download_links', []),
                            'tools_used': result_dict.get('tools_used', [function_name])
                        }
                    except Exception as e:
                        logger.error(f"❌ Tool runner execution failed: {e}")
                        yield {
                            'content': f'Tool execution error: {str(e)}',
                            'status': 'error',
                            'done': True
                        }
                        return

                elif function_name in self.tools:
                    try:
                        # Fallback to legacy direct execution if tool_runner not available
                        args_str = chunk['function_call']['arguments'] or '{}'
                        args = json.loads(args_str) if args_str.strip() else {}
                        args['session_id'] = session_id  # Ensure session_id is included

                        logger.debug(f"Executing tool (legacy): {function_name} with args: {args}")

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
                                    # Add proper spacing and section header for clarity
                                    formatted_interpretation = f"\n\n**Analysis:**\n{interpretation}"
                                    yield {
                                        'content': formatted_interpretation,
                                        'status': 'success',
                                        'tools_used': tools_used_list,
                                        'done': True
                                    }
                                else:
                                    yield {'content': '', 'status': 'success', 'tools_used': tools_used_list, 'done': True}
                            except Exception as interp_err:
                                logger.error(f"Error during interpretation: {interp_err}")
                                yield {
                                    'content': f"\n\n⚠️ Interpretation failed: {interp_err}",
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
                                'download_links': result.get('download_links', []),
                                'tools_used': tools_list,
                                'done': False
                            }
                            yield from _yield_interpretation(result['response'], tools_list)
                            self._store_conversation(session_id, user_message, result['response'])
                            return

                        # Handle raw string response OR ToolExecutionResult
                        else:
                            # Check if it's a ToolExecutionResult with visualization data
                            visualizations = []
                            if hasattr(result, 'data') and result.data and 'web_path' in result.data:
                                # Extract visualization information from ToolExecutionResult
                                viz_data = {
                                    'type': result.data.get('map_type', result.data.get('chart_type', 'visualization')),
                                    'path': result.data.get('web_path', ''),
                                    'url': result.data.get('web_path', ''),
                                    'file_path': result.data.get('file_path', ''),
                                    'title': result.data.get('title', 'Visualization')
                                }
                                visualizations = [viz_data]
                                raw_output = result.message if hasattr(result, 'message') else str(result)
                            elif isinstance(result, dict) and result.get('data') and result['data'].get('web_path'):
                                # Handle dict format with visualization data
                                viz_data = {
                                    'type': result['data'].get('map_type', result['data'].get('chart_type', 'visualization')),
                                    'path': result['data'].get('web_path', ''),
                                    'url': result['data'].get('web_path', ''),
                                    'file_path': result['data'].get('file_path', ''),
                                    'title': result.get('message', 'Visualization')
                                }
                                visualizations = [viz_data]
                                raw_output = result.get('message', str(result))
                            else:
                                raw_output = result if isinstance(result, str) else str(result)

                            tools_list = [function_name]
                            yield {
                                'content': raw_output,
                                'status': 'success',
                                'visualizations': visualizations,
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
                else:
                    # Tool not found in either tool_runner or self.tools
                    logger.error(f"❌ Unknown function requested: {function_name}")
                    logger.error(f"   Available in self.tools: {list(self.tools.keys())[:5]}...")
                    if self.tool_runner:
                        available_tools = self.tool_runner.registry.list_tools()
                        logger.error(f"   Available in tool_runner: {available_tools[:5] if available_tools else 'None'}...")
                    yield {
                        'content': f"I don't have access to the function '{function_name}'. This might be a configuration issue. Please contact support.",
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
        """Refactored: delegate function_call execution to ToolRunner."""
        func_call = response.get('function_call') or response.get('tool_call')
        if func_call and func_call.get('name'):
            if self.tool_runner:
                return self.tool_runner.execute(func_call['name'], func_call.get('arguments', '{}'))
        return {'response': response.get('content', 'No response'), 'tools_used': [], 'status': 'success'}

    # Tool Functions - These are the actual functions registered as tools
    def _simple_conversational_response(self, user_message: str, session_context: Dict, session_id: str) -> Dict:
        """Simple conversational response without tools - now with context awareness."""
        try:
            # Build system prompt with UI context
            system_prompt = self._build_system_prompt_refactored(session_context, session_id)

            # Generate response with system context
            response = self.llm_manager.generate(
                user_message,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=500
            )

            # Store conversation
            self._store_conversation(session_id, user_message, response)

            return {
                'response': response,
                'status': 'success',
                'tools_used': []
            }
        except Exception as e:
            logger.error(f"Error generating conversational response: {e}")
            return {
                'response': "I encountered an error processing your message. Please try again.",
                'status': 'error',
                'tools_used': []
            }

    def _interpret_raw_output(
        self,
        raw_output: str,
        user_message: str,
        session_context: dict,
        session_id: str
    ) -> str:
        """Interpret raw tool output and format for user display.

        This method processes raw tool execution results and converts them
        into user-friendly responses. It handles special cases like code
        execution results, data queries, and error messages.

        Args:
            raw_output: Raw output from tool execution
            user_message: Original user message
            session_context: Session context dict
            session_id: Session identifier

        Returns:
            Formatted interpretation string for user display
        """
        try:
            # If raw output is already a formatted response, return it
            if isinstance(raw_output, str):
                # Check if it's an error message
                if raw_output.startswith("Error"):
                    return raw_output

                # Check if it's a success message with data
                if any(keyword in raw_output.lower() for keyword in
                       ['successfully', 'completed', 'created', 'generated']):
                    return raw_output

                # For data query results, enhance with context
                if session_context.get('data_loaded'):
                    return raw_output

                # Default: return as-is
                return raw_output

            # If raw output is a dict (structured response), extract message
            elif isinstance(raw_output, dict):
                return raw_output.get('response', str(raw_output))

            # Fallback: convert to string
            return str(raw_output)

        except Exception as e:
            logger.error(f"Error interpreting raw output: {e}")
            # Fallback: return raw output as string
            return str(raw_output)

    # NEW: ITN Planning Tool

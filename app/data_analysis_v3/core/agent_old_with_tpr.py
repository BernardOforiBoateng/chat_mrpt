"""
LangGraph Agent for Data Analysis
Based on AgenticDataAnalysis backend.py and nodes.py
Using OpenAI gpt-4o for tool calling and analysis
"""

import os
import logging
from typing import Literal, List, Dict, Any, Optional
from enum import Enum
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI  # Using actual OpenAI API
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from .state import DataAnalysisState
from .state_manager import ConversationStage
from ..tools.python_tool import analyze_data, get_data_summary
from ..prompts.system_prompt import MAIN_SYSTEM_PROMPT, get_error_handling_prompt
from ..formatters.response_formatter import format_analysis_response
from .encoding_handler import EncodingHandler

logger = logging.getLogger(__name__)


class DataAnalysisAgent:
    """
    Main agent for data analysis using LangGraph.
    Follows AgenticDataAnalysis two-node pattern.
    Uses OpenAI gpt-4o for high-quality analysis.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.tpr_selections = {}  # Store TPR selections to avoid repetition
        
        # Initialize LLM - Using actual OpenAI API with gpt-4o
        openai_key = os.environ.get('OPENAI_API_KEY')
        if not openai_key:
            logger.error("OPENAI_API_KEY not found in environment!")
            raise ValueError("OpenAI API key required for Data Analysis V3")
            
        logger.info("Initializing Data Analysis V3 with OpenAI gpt-4o")
        
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Using gpt-4o like the original
            api_key=openai_key,  # Use actual OpenAI API key
            temperature=0.7,
            max_tokens=2000,
            timeout=50  # Keep within ALB timeout
        )
        
        # Set up tools - conditionally add TPR tool if TPR data detected
        self.tools = [analyze_data]

        # Check for TPR data and add TPR tool if detected
        self._check_and_add_tpr_tool()

        # CRITICAL: Follow AgenticDataAnalysis pattern exactly
        # First bind tools to the LLM - FORCE tool usage when appropriate
        model_with_tools = self.llm.bind_tools(
            self.tools,
            tool_choice="auto"  # Let model decide when to use tools
        )

        # Then create the template
        self.chat_template = ChatPromptTemplate.from_messages([
            ("system", MAIN_SYSTEM_PROMPT),
            ("placeholder", "{messages}"),
        ])

        # Finally chain template with the tool-bound model
        self.model = self.chat_template | model_with_tools

        # Create tool node
        self.tool_node = ToolNode(self.tools)
        
        # Build the graph
        self.graph = self._build_graph()
        
        # Track conversation history
        self.chat_history: List[BaseMessage] = []

    def _build_graph(self):
        """
        Build the LangGraph workflow.
        Exact pattern from AgenticDataAnalysis backend.py
        """
        workflow = StateGraph(DataAnalysisState)
        
        # Add nodes
        workflow.add_node('agent', self._agent_node)
        workflow.add_node('tools', self._tools_node)
        
        # Add conditional routing
        workflow.add_conditional_edges('agent', self._route_to_tools)
        
        # Add edge from tools back to agent
        workflow.add_edge('tools', 'agent')
        
        # Set entry point
        workflow.set_entry_point('agent')
        
        return workflow.compile()
    
    def _create_data_summary(self, state: DataAnalysisState) -> str:
        """
        Create a more informative data summary for the agent.
        """
        if state.get("input_data"):
            for dataset in state["input_data"]:
                var_name = dataset.get("variable_name", "df")

                # Try to get column information if available
                columns_info = ""
                shape_info = ""

                # Check if we have metadata about the dataset
                if "metadata" in dataset:
                    metadata = dataset["metadata"]
                    if "columns" in metadata:
                        columns_info = f"\nColumns: {', '.join(metadata['columns'][:10])}"
                        if len(metadata['columns']) > 10:
                            columns_info += f" ... and {len(metadata['columns']) - 10} more"
                    if "shape" in metadata:
                        shape_info = f"\nShape: {metadata['shape'][0]} rows, {metadata['shape'][1]} columns"

                # Enhanced summary with context about TPR workflow if active
                summary = f"\n\nVariable: {var_name}\nDescription: Dataset loaded with TPR malaria data"
                summary += shape_info
                summary += columns_info

                # Add TPR-specific context if in workflow
                if hasattr(self, 'state_manager') and self.state_manager:
                    stage = self.state_manager.get_workflow_stage()
                    if stage and 'TPR' in str(stage):
                        summary += "\n\nNote: You are in the TPR workflow. The data contains facility, test, and positivity information."
                        summary += "\nKey columns include: State, LGA, WardName, HealthFacility, FacilityLevel, and test/positive counts by age group."

                return summary

        return "No data loaded yet"
    
    def _agent_node(self, state: DataAnalysisState):
        """
        Agent node - EXACTLY like AgenticDataAnalysis call_model function.
        """
        logger.info(f"[DEBUG] === AGENT NODE CALLED ===")
        logger.info(f"[DEBUG] Session: {self.session_id}")

        # Create data context message
        current_data_template = """The following data is available:\n{data_summary}"""
        data_summary = self._create_data_summary(state)
        logger.info(f"[DEBUG] Data summary: {data_summary[:200]}...")

        current_data_message = HumanMessage(
            content=current_data_template.format(data_summary=data_summary)
        )

        # CRITICAL: Modify state["messages"] directly like original!
        state["messages"] = [current_data_message] + state.get("messages", [])
        logger.info(f"[DEBUG] Agent invoking model with {len(state.get('messages', []))} messages")

        # CRITICAL: Pass the ENTIRE state to model.invoke() like original!
        logger.info(f"[DEBUG] Calling model.invoke()...")
        llm_outputs = self.model.invoke(state)
        logger.info(f"[DEBUG] Model.invoke() returned: {type(llm_outputs)}")

        # Log tool calls for debugging
        if hasattr(llm_outputs, 'tool_calls') and llm_outputs.tool_calls:
            logger.info(f"✅ Model made {len(llm_outputs.tool_calls)} tool call(s)")
            for tc in llm_outputs.tool_calls:
                logger.info(f"  Tool: {tc.get('name', 'unknown')}")
        else:
            logger.warning("⚠️ Model did NOT make any tool calls")

        # Return exactly like original
        return {
            "messages": [llm_outputs],
            "intermediate_outputs": [current_data_message.content]
        }
    
    def _tools_node(self, state: DataAnalysisState):
        """
        Tools node that executes tool calls.
        Simplified to use ToolNode directly.
        """
        # Increment tool call count to prevent infinite loops
        state["tool_call_count"] = state.get("tool_call_count", 0) + 1
        
        # Add session_id to state for tool access
        state_with_session = {**state, "session_id": self.session_id}
        
        # Use ToolNode to handle execution
        result = self.tool_node.invoke(state_with_session)
        
        # Preserve the tool call count in the result
        result["tool_call_count"] = state["tool_call_count"]
        
        # Format any tool responses for user-friendliness
        if "messages" in result and result["messages"]:
            for msg in result["messages"]:
                if isinstance(msg, ToolMessage):
                    # Format the content if needed
                    if "Error" in msg.content or "error" in msg.content.lower():
                        msg.content = get_error_handling_prompt(msg.content)
                    else:
                        # Parse for any technical content and format
                        msg.content = format_analysis_response(msg.content, {})
        
        return result
    
    def _route_to_tools(self, state: DataAnalysisState) -> Literal["tools", "__end__"]:
        """
        Route to tools if the last message has tool calls.
        Based on AgenticDataAnalysis route_to_tools function.
        """
        # Check if we've made too many tool calls (prevent infinite loops)
        tool_call_count = state.get("tool_call_count", 0)
        if tool_call_count >= 5:
            logger.warning(f"Reached max tool calls ({tool_call_count}), forcing end")
            return "__end__"
        
        if messages := state.get("messages", []):
            ai_message = messages[-1]
        else:
            return "__end__"
        
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"
        return "__end__"
    
    def _check_and_add_tpr_tool(self):
        """
        Check if uploaded data is TPR data and conditionally add TPR tool.
        """
        try:
            import os
            import pandas as pd
            import glob
            from app.core.tpr_utils import is_tpr_data
            
            # Find data files in session folder
            data_dir = f"instance/uploads/{self.session_id}"
            if not os.path.exists(data_dir):
                return
            
            # Look for CSV or Excel files
            data_files = glob.glob(os.path.join(data_dir, "*.xlsx")) + \
                        glob.glob(os.path.join(data_dir, "*.csv"))
            
            if not data_files:
                return
            
            # Load and check the most recent file
            data_file = max(data_files, key=os.path.getctime)
            
            if data_file.endswith('.csv'):
                df = EncodingHandler.read_csv_with_encoding(data_file)
            else:
                df = EncodingHandler.read_excel_with_encoding(data_file)
            
            # Store the data for later use
            self.uploaded_data = df
            self.data_file_name = os.path.basename(data_file)
            
            # Generate overview summary (no menu; exploration by default)
            self.data_summary = self._generate_overview_summary(df)
            
            # Check if this is TPR data and conditionally add TPR tool
            if is_tpr_data(df):
                from ..tools.tpr_analysis_tool import analyze_tpr_data
                self.tools.append(analyze_tpr_data)
                logger.info(f"TPR data detected - added TPR analysis tool")
            
            logger.info(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")
                
        except Exception as e:
            logger.debug(f"Error preparing data summary: {e}")
            self.data_summary = None
            # Non-critical error, continue
    
    def _check_tpr_transition(self, user_query: str) -> Optional[Dict[str, Any]]:
        """
        Check if TPR is waiting for confirmation to proceed to risk analysis.
        Returns response if handling transition, None otherwise.
        """
        import os
        from pathlib import Path
        
        session_folder = f"instance/uploads/{self.session_id}"
        waiting_flag = os.path.join(session_folder, '.tpr_waiting_confirmation')
        risk_ready_flag = os.path.join(session_folder, '.risk_ready')
        
        # Check if TPR is waiting for confirmation
        if not os.path.exists(waiting_flag):
            return None
        
        # Check if user is confirming to proceed
        if self._is_confirmation_message(user_query):
            logger.info(f"User confirmed TPR transition to risk analysis: '{user_query}'")
            
            # Clear the waiting flag
            if os.path.exists(waiting_flag):
                os.remove(waiting_flag)
            
            # Let the AI handle the transition naturally
            return None  # Continue to LangGraph agent
        
        # Check if user is declining or asking something else
        if 'no' in user_query.lower() or 'not' in user_query.lower() or 'cancel' in user_query.lower():
            logger.info(f"User declined TPR transition: '{user_query}'")

            # Clear the waiting flag
            if os.path.exists(waiting_flag):
                os.remove(waiting_flag)

            # Let the AI handle the response naturally
            return None  # Continue to LangGraph agent
        
        # Not a transition response, continue normal processing
        return None
    
    def _is_confirmation_message(self, message: str) -> bool:
        """
        Check if message is a confirmation to proceed.
        Based on production implementation.
        """
        msg = message.lower().strip()
        
        # Core confirmation words (from production)
        confirmation_words = {
            'yes', 'y', 'ok', 'okay', 'sure', 'proceed', 'continue', 
            'go', 'yep', 'yeah', 'affirmative', 'ready', 'start',
            'run', 'analyze', 'risk analysis'
        }
        negative_words = {
            'no', 'not', 'dont', "don't", 'cancel', 'stop', 'wait', 
            'hold', 'later', 'skip'
        }
        
        # Check if message explicitly mentions risk analysis
        if 'risk' in msg and ('analysis' in msg or 'analyze' in msg):
            return True
        
        # Split message into words
        words = msg.split()
        
        # Check for negative words first
        has_negative = any(word in negative_words for word in words)
        if has_negative:
            return False
        
        # Check for confirmation words
        has_confirmation = any(word in confirmation_words for word in words)
        
        return has_confirmation
    


    async def analyze(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point for analysis requests.
        Based on AgenticDataAnalysis user_sent_message method.
        Always goes through LangGraph except for TPR workflow.
        """
        logger.info(f"[CLEAN AGENT] Analyzing query: '{user_query[:100]}...'")

        # Create InputData objects for uploaded files (like original)
        import os
        import pandas as pd
        data_dir = f"instance/uploads/{self.session_id}"
        input_data_list = []
        
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith(('.csv', '.xlsx', '.xls')):
                    filepath = os.path.join(data_dir, file)
                    var_name = file.split('.')[0].replace(' ', '_').replace('-', '_')

                    # Try to get metadata about the file
                    metadata = {}
                    try:
                        # Quick read to get shape and columns
                        if file.endswith('.csv'):
                            temp_df = pd.read_csv(filepath, nrows=5)
                        else:
                            temp_df = pd.read_excel(filepath, nrows=5)

                        # Get full shape by reading all data (or estimate)
                        if file.endswith('.csv'):
                            with open(filepath, 'r') as f:
                                row_count = sum(1 for line in f) - 1  # Minus header
                        else:
                            row_count = len(pd.read_excel(filepath))

                        metadata = {
                            "columns": temp_df.columns.tolist(),
                            "shape": (row_count, len(temp_df.columns)),
                            "dtypes": {col: str(dtype) for col, dtype in temp_df.dtypes.items()}
                        }
                        logger.info(f"Loaded metadata: {row_count} rows, {len(temp_df.columns)} columns")
                    except Exception as e:
                        logger.warning(f"Could not load metadata for {file}: {e}")

                    # Create InputData-like dict with metadata
                    input_data_list.append({
                        "variable_name": var_name,
                        "data_path": os.path.abspath(filepath),
                        "data_description": f"Dataset from {file}",
                        "metadata": metadata
                    })
                    logger.info(f"Added dataset: {var_name} from {filepath}")
        
        # Append TPR context to user query if present
        if tpr_message_addon:
            user_query = user_query + tpr_message_addon

        # Prepare initial state with chat history - like original, no wrapper needed!
        input_state = {
            "messages": self.chat_history + [HumanMessage(content=user_query)],
            "session_id": self.session_id,
            "input_data": input_data_list,  # Pass actual data info like original
            "intermediate_outputs": [],
            "current_variables": {},
            "output_plots": [],
            "output_image_paths": [],  # Like original
            "insights": [],
            "errors": [],
            "tool_call_count": 0,  # Track number of tool calls to prevent infinite loops
            "tpr_context": tpr_context if tpr_context else None  # Include TPR context
        }

        try:
            # Run the graph with increased recursion limit but catch timeouts
            try:
                logger.info(f"[DEBUG] === STARTING GRAPH EXECUTION ===")
                logger.info(f"[DEBUG] Query: {user_query[:100]}...")
                logger.info(f"[DEBUG] Input data list: {len(input_data_list)} files")
                logger.info(f"[DEBUG] Messages in state: {len(input_state['messages'])}")
                logger.info(f"[DEBUG] Session ID: {self.session_id}")

                result = self.graph.invoke(input_state, {"recursion_limit": 10})

                logger.info(f"[DEBUG] === GRAPH EXECUTION COMPLETE ===")
                logger.info(f"[DEBUG] Result messages: {len(result.get('messages', []))}")

            except Exception as graph_error:
                # Log the actual error instead of masking it
                logger.error(f"=== GRAPH EXECUTION FAILED ===")
                logger.error(f"Error type: {type(graph_error).__name__}")
                logger.error(f"Error message: {str(graph_error)}")
                logger.error(f"Full traceback:", exc_info=True)

                return {
                    "success": False,
                    "message": f"I encountered an error while processing your request: {str(graph_error)}. Please try rephrasing your request or contact support if this persists.",
                    "session_id": self.session_id
                }
            
            # Update chat history
            self.chat_history = result.get("messages", [])
            
            # Extract the final response
            final_message = self.chat_history[-1] if self.chat_history else None

            logger.info(f"[DEBUG] Final message type: {type(final_message)}")
            logger.info(f"[DEBUG] Has content: {hasattr(final_message, 'content') if final_message else False}")
            logger.info(f"[DEBUG] Message content preview: {str(final_message.content)[:200] if final_message and hasattr(final_message, 'content') else 'No content'}")

            # Prepare response
            response = {
                "success": True,
                "message": final_message.content if final_message else "Analysis complete.",
                "visualizations": [],  # Will be populated below
                "insights": result.get("insights", []),
                "session_id": self.session_id
            }

            logger.info(f"[DEBUG] Prepared response with message length: {len(response['message'])}")
            
            # Load and include any generated visualizations
            if result.get("output_plots"):
                import pickle
                import uuid
                viz_data = []
                
                # Create static visualizations directory if it doesn't exist
                static_viz_dir = f"app/static/visualizations"
                os.makedirs(static_viz_dir, exist_ok=True)
                
                for plot_path in result["output_plots"]:
                    if os.path.exists(plot_path):
                        try:
                            # Extract the pickle filename
                            pickle_filename = os.path.basename(plot_path)

                            # Create the pickle URL that frontend expects
                            pickle_url = f"/images/plotly_figures/pickle/{pickle_filename}"

                            # Also load and save as HTML for direct access
                            with open(plot_path, 'rb') as f:
                                fig = pickle.load(f)

                                # Generate unique filename for HTML
                                viz_id = str(uuid.uuid4())
                                html_filename = f"data_analysis_{viz_id}.html"
                                html_path = os.path.join(static_viz_dir, html_filename)

                                # Save HTML to file
                                viz_html = fig.to_html(include_plotlyjs='cdn')
                                with open(html_path, 'w') as html_file:
                                    html_file.write(viz_html)

                                # Create web-accessible path
                                web_path = f"/static/visualizations/{html_filename}"

                                # Include both pickle URL (for frontend) and HTML path (for backup)
                                viz_data.append({
                                    "type": "plotly",
                                    "path": pickle_url,  # Pickle URL that frontend expects
                                    "url": pickle_url,   # Also provide as url for compatibility
                                    "html_path": web_path,  # HTML path as backup
                                    "pickle_path": plot_path,  # Original pickle file path
                                    "title": "Data Analysis Visualization"
                                })
                                logger.info(f"Created visualization: pickle_url={pickle_url}, html_path={web_path}")
                        except Exception as e:
                            logger.error(f"Error processing visualization from {plot_path}: {e}")
                    else:
                        logger.warning(f"Visualization file not found: {plot_path}")
                
                # Add visualization data to response
                if viz_data:
                    response["visualization_data"] = viz_data
                    response["visualizations"] = viz_data  # Also add to visualizations key for compatibility
                    logger.info(f"Returning {len(viz_data)} visualizations with file paths")
            
            return response
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return {
                "success": False,
                "message": get_error_handling_prompt(str(e)),
                "session_id": self.session_id
            }
    

    def _generate_overview_summary(self, df) -> str:
        """Generate an overview summary without presenting a menu.

        Adds a top warning line clarifying that exploration starts now and
        TPR/risk analysis requires an explicit user request.
        """
        # Extract basic statistics
        n_rows = len(df)
        n_cols = len(df.columns)

        # Try to detect geographic data
        state = df['State'].iloc[0] if 'State' in df.columns else None
        n_lgas = df['LGA'].nunique() if 'LGA' in df.columns else 0
        n_wards = df['WardName'].nunique() if 'WardName' in df.columns else 0
        n_facilities = df['HealthFacility'].nunique() if 'HealthFacility' in df.columns else 0

        # Check what type of data is available
        has_test_data = any('RDT' in col or 'Microscopy' in col for col in df.columns)

        # Build summary (no menu; exploration by default with friendly guidance)
        summary = "📊 **Your data has been uploaded successfully!**\n\n"
        summary += "You can now freely explore your data. When you're ready for risk analysis, just say **'Run TPR analysis'** to start the Test Positivity Rate workflow.\n\n"
        summary += "**Data Overview:**\n"
        if state:
            summary += f"- Location: {state}\n"
        if n_wards > 0:
            summary += f"- {n_wards} wards"
            if n_lgas > 0:
                summary += f" across {n_lgas} LGAs\n"
            else:
                summary += "\n"
        if n_facilities > 0:
            summary += f"- {n_facilities} health facilities\n"
        summary += f"- {n_rows:,} total records\n"
        summary += f"- {n_cols} data columns\n"

        if has_test_data:
            test_types = []
            if any('RDT' in col for col in df.columns):
                test_types.append("RDT")
            if any('Microscopy' in col for col in df.columns):
                test_types.append("Microscopy")
            if test_types:
                summary += f"- Test data: {', '.join(test_types)} available\n"

        summary += "\nYou can ask me to:\n"
        summary += "- Explore patterns, trends, and distributions\n"
        summary += "- Create charts and maps\n"
        summary += "- Check data quality and key indicators\n\n"
        if has_test_data:
            summary += "When you're ready for risk analysis, say: \"Run TPR analysis\"."

        return summary

    def reset(self):
        """Reset the agent's conversation history."""
        self.chat_history = []

"""
LangGraph Agent for Data Analysis
Based on AgenticDataAnalysis backend.py and nodes.py
Using OpenAI gpt-4o for tool calling and analysis
"""

import os
import logging
import pandas as pd
from typing import Literal, List, Dict, Any, Optional
from enum import Enum
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI  # Using actual OpenAI API
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from .state import DataAnalysisState
from .data_profiler import DataProfiler
from .state_manager import DataAnalysisStateManager, ConversationStage
from .tpr_data_analyzer import TPRDataAnalyzer
from .tpr_workflow_handler import TPRWorkflowHandler
from .formatters import MessageFormatter
from .encoding_handler import EncodingHandler
from ..tools.python_tool import analyze_data, get_data_summary
from ..prompts.system_prompt import MAIN_SYSTEM_PROMPT, get_dynamic_prompt, get_error_handling_prompt
from ..formatters.response_formatter import format_analysis_response

logger = logging.getLogger(__name__)


class UserIntent(Enum):
    """User intent types for routing."""
    TPR_CALCULATION = "tpr_calculation"
    DATA_EXPLORATION = "data_exploration"
    QUICK_OVERVIEW = "quick_overview"
    UNCLEAR = "unclear"


class DataAnalysisAgent:
    """
    Main agent for data analysis using LangGraph.
    Follows AgenticDataAnalysis two-node pattern.
    Uses OpenAI gpt-4o for high-quality analysis.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        
        # Initialize state manager for persistent state
        self.state_manager = DataAnalysisStateManager(session_id)
        
        # Initialize TPR data analyzer
        self.tpr_analyzer = TPRDataAnalyzer()
        
        # Initialize modular components
        self.message_formatter = MessageFormatter(session_id)
        self.tpr_handler = TPRWorkflowHandler(
            session_id,
            self.state_manager,
            self.tpr_analyzer
        )
        
        # Restore state from previous interactions
        self._restore_state()
        
        # Initialize data attributes
        self.data_summary = None
        self.uploaded_data = None
        self.data_file_name = None
        
        # Initialize LLM - Using actual OpenAI API with gpt-4o
        openai_key = os.environ.get('OPENAI_API_KEY')
        if not openai_key:
            logger.error("OPENAI_API_KEY not found in environment!")
            raise ValueError("OpenAI API key required for Data Analysis V3")
            
        logger.info(f"Initializing Data Analysis V3 for session {session_id}")
        
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Using gpt-4o like the original
            api_key=openai_key,  # Use actual OpenAI API key
            temperature=0.7,
            max_tokens=4000,  # INCREASED from 2000 to prevent truncation
            timeout=50  # Keep within ALB timeout
        )
        
        # Set up tools - conditionally add TPR tool if TPR data detected
        self.tools = [analyze_data]
        
        # Check for TPR data and add TPR tool if detected
        self._check_and_add_tpr_tool()
        
        # Use the main system prompt that was working
        from ..prompts.system_prompt import MAIN_SYSTEM_PROMPT
        system_prompt = MAIN_SYSTEM_PROMPT
        
        # Create the template with simple prompt
        self.chat_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{messages}"),
        ])
        
        # Chain template with model ONCE (like original) - but AFTER tools are set up
        self.model = self.chat_template | self.llm.bind_tools(self.tools)
        
        # Create tool node
        self.tool_node = ToolNode(self.tools)
        
        # Build the graph
        self.graph = self._build_graph()
        
        # Track conversation history
        self.chat_history: List[BaseMessage] = []
    
    def _restore_state(self):
        """
        Restore state from previous interactions.
        """
        try:
            # Get current stage from state manager
            self.current_stage = self.state_manager.get_workflow_stage()
            
            # Restore TPR selections
            self.tpr_selections = self.state_manager.get_tpr_selections()
            
            # Update handler with restored state
            self.tpr_handler.tpr_selections = self.tpr_selections
            self.tpr_handler.current_stage = self.current_stage
            
            # Restore chat history (limit to recent messages)
            chat_history = self.state_manager.get_chat_history(limit=10)
            
            # Convert to LangChain messages
            self.chat_history = []
            for msg in chat_history:
                if msg['role'] == 'user':
                    self.chat_history.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    self.chat_history.append(AIMessage(content=msg['content']))
            
            if self.current_stage != ConversationStage.INITIAL:
                logger.info(f"Restored state: stage={self.current_stage.value}, selections={self.tpr_selections}")
        except Exception as e:
            logger.warning(f"Could not restore state: {e}")
            self.current_stage = ConversationStage.INITIAL
            self.tpr_selections = {}
    
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
        Create a simple summary of available data (like AgenticDataAnalysis).
        Keep it simple and clear.
        """
        summary = ""
        
        # Just list the available variables simply
        if state.get("input_data"):
            for dataset in state["input_data"]:
                var_name = dataset.get("variable_name", "df")
                description = dataset.get("data_description", "")
                
                summary += f"\n\nVariable: `{var_name}`"
                if description:
                    summary += f"\nDescription: {description}"
                
                # Try to add basic shape info
                try:
                    data_path = dataset.get("data_path", "")
                    if data_path and os.path.exists(data_path):
                        import pandas as pd
                        # Quick peek at shape without loading full columns list
                        if data_path.endswith('.csv'):
                            df_peek = pd.read_csv(data_path, nrows=1)
                        else:
                            df_peek = pd.read_excel(data_path, nrows=1)
                        summary += f"\nColumns: {len(df_peek.columns)}"
                except:
                    pass
        
        # Add any additional variables from state
        if "current_variables" in state:
            variables = [v for v in state["current_variables"] if v not in ['df', 'data_analysis']]
            for v in variables:
                summary += f"\n\nVariable: `{v}`"
        
        return summary if summary else "No datasets loaded yet."
    
    def _agent_node(self, state: DataAnalysisState):
        """
        Agent node - EXACTLY like AgenticDataAnalysis call_model function.
        """
        # Create data context message
        current_data_template = """The following data is available:\n{data_summary}"""
        current_data_message = HumanMessage(
            content=current_data_template.format(
                data_summary=self._create_data_summary(state)
            )
        )
        
        # CRITICAL: Modify state["messages"] directly like original!
        state["messages"] = [current_data_message] + state.get("messages", [])
        
        # CRITICAL: Pass the ENTIRE state to model.invoke() like original!
        llm_outputs = self.model.invoke(state)
        
        # Log the response
        logger.info(f"Agent response received")
        
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
                    # Only format errors, leave actual output as-is
                    if "Error" in msg.content or "error" in msg.content.lower():
                        msg.content = get_error_handling_prompt(msg.content)
                    # Don't format successful output - pass it through directly!
        
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
        Load uploaded data and prepare general data summary.
        TPR tool is NOT added automatically - only when user explicitly requests it.
        """
        try:
            import os
            import pandas as pd
            import glob
            
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
            
            # Also set data in TPR handler
            self.tpr_handler.set_data(df)
            
            # Generate user-choice summary (not TPR-specific)
            self.data_summary = self._generate_user_choice_summary(df)
            
            # NO AUTOMATIC TPR DETECTION - only add tool when explicitly requested
            # TPR tool will be added in _start_tpr_workflow() when user requests it
            
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
            
            # Trigger risk analysis
            return {
                'success': True,
                'message': """Great! I'll now proceed with the risk analysis using your TPR data.

I'll analyze the data using two complementary methods:
1. **Composite Scoring** - A transparent method that combines multiple risk factors
2. **PCA Analysis** - A statistical approach that identifies the main patterns of risk

This will help identify and rank the wards by their malaria vulnerability for targeted interventions.

Starting the analysis now... (this may take a moment)

Please run the complete analysis to generate ward rankings and vulnerability maps.""",
                'trigger_analysis': True
            }
        
        # Check if user is declining or asking something else
        if 'no' in user_query.lower() or 'not' in user_query.lower() or 'cancel' in user_query.lower():
            logger.info(f"User declined TPR transition: '{user_query}'")
            
            # Clear the waiting flag
            if os.path.exists(waiting_flag):
                os.remove(waiting_flag)
            
            return {
                'success': True,
                'message': """No problem! Your TPR data has been saved and is ready whenever you want to proceed with the risk analysis.

You can:
- Explore the TPR results further
- Ask questions about the data
- Come back later to run the risk analysis

Just let me know what you'd like to do next."""
            }
        
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
        Enhanced with state management and improved TPR workflow.
        """
        # Save user message to history
        self.state_manager.save_chat_message('user', user_query)
        
        # Handle TPR workflow if active
        if self.state_manager.is_tpr_workflow_active():
            response = self._handle_tpr_workflow(user_query)
            if response:
                self.state_manager.save_chat_message('assistant', response['message'])
                return response
        
        # If this is the VERY FIRST query after upload (no chat history), return our prepared summary
        # Only show summary if there's no conversation history (true first interaction)
        if self.data_summary and len(self.chat_history) == 0:
            # More specific check - only for initial data exploration requests
            if any(phrase in user_query.lower() for phrase in ['analyze uploaded', 'uploaded data', 'what\'s in', 'show me what']):
                logger.info("Returning prepared data summary for first interaction")
                response = {
                    "success": True,
                    "message": self.data_summary,
                    "session_id": self.session_id,
                    "has_data": True
                }
                self.state_manager.save_chat_message('assistant', response['message'])
                # Update stage to show we've moved past initial
                self.current_stage = ConversationStage.DATA_EXPLORING
                self.state_manager.update_workflow_stage(ConversationStage.DATA_EXPLORING)
                return response
        
        # Check if user is selecting TPR option (option 1)
        if self._is_tpr_selection(user_query):
            return self._start_tpr_workflow()
        
        # Check if user is selecting flexible exploration (option 2)
        if self._is_flexible_exploration_selection(user_query):
            # Mark that user chose flexible exploration
            self.current_stage = ConversationStage.DATA_EXPLORING
            self.state_manager.update_workflow_stage(ConversationStage.DATA_EXPLORING)
            return {
                "success": True,
                "message": "Great! You've chosen Flexible Data Exploration. You can now ask any questions about your data, request visualizations, or explore patterns. What would you like to know?",
                "session_id": self.session_id
            }
        
        # Check if user wants to prepare for risk analysis after TPR
        if self._is_risk_preparation_request(user_query):
            return self._prepare_for_risk_analysis()
        
        # Check for TPR transition confirmation
        transition_response = self._check_tpr_transition(user_query)
        if transition_response:
            return transition_response
        
        # Create InputData objects for uploaded files (like original)
        import os
        import pandas as pd
        data_dir = f"instance/uploads/{self.session_id}"
        input_data_list = []
        
        # First, check if we already have loaded data in self.uploaded_data
        if hasattr(self, 'uploaded_data') and self.uploaded_data is not None:
            # Use the already loaded data
            var_name = 'df'
            if hasattr(self, 'data_file_name') and self.data_file_name:
                var_name = self.data_file_name.split('.')[0].replace(' ', '_').replace('-', '_')
            
            input_data_list.append({
                "variable_name": var_name,
                "data_path": os.path.join(data_dir, self.data_file_name) if hasattr(self, 'data_file_name') else "",
                "data_description": f"Dataset with {len(self.uploaded_data)} rows and {len(self.uploaded_data.columns)} columns",
                "data": self.uploaded_data  # CRITICAL: Pass actual DataFrame!
            })
            logger.info(f"Added pre-loaded dataset: {var_name} with shape {self.uploaded_data.shape}")
        
        # Also load any other files in the directory
        elif os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith(('.csv', '.xlsx', '.xls')):
                    filepath = os.path.join(data_dir, file)
                    var_name = file.split('.')[0].replace(' ', '_').replace('-', '_')
                    
                    try:
                        # Load the actual data here
                        if file.endswith('.csv'):
                            df = EncodingHandler.read_csv_with_encoding(filepath)
                        else:
                            df = EncodingHandler.read_excel_with_encoding(filepath)
                        
                        # Create InputData-like dict WITH ACTUAL DATA
                        input_data_list.append({
                            "variable_name": var_name,
                            "data_path": os.path.abspath(filepath),
                            "data_description": f"Dataset from {file}",
                            "data": df  # CRITICAL: Pass actual DataFrame!
                        })
                        logger.info(f"Loaded dataset: {var_name} from {filepath} with shape {df.shape}")
                    except Exception as e:
                        logger.error(f"Failed to load {file}: {e}")
                        # Still add metadata even if loading fails
                        input_data_list.append({
                            "variable_name": var_name,
                            "data_path": os.path.abspath(filepath),
                            "data_description": f"Dataset from {file} (failed to load)"
                        })
        
        # Prepare initial state with chat history
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
            "tool_call_count": 0  # Track number of tool calls to prevent infinite loops
        }
        
        try:
            # Run the graph with increased recursion limit
            result = self.graph.invoke(input_state, {"recursion_limit": 15})
            
            # Update chat history
            self.chat_history = result.get("messages", [])
            
            # Extract the final response
            final_message = self.chat_history[-1] if self.chat_history else None
            
            # Prepare response
            response = {
                "success": True,
                "message": final_message.content if final_message else "Analysis complete.",
                "visualizations": [],  # Will be populated below
                "insights": result.get("insights", []),
                "session_id": self.session_id
            }
            
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
                                
                                viz_data.append({
                                    "type": "plotly",
                                    "path": web_path,  # Web-accessible path for iframe
                                    "url": web_path,   # Also provide url for compatibility
                                    "title": "Data Analysis Visualization"
                                })
                                logger.info(f"Saved visualization to {html_path}, web path: {web_path}")
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
    
    def _generate_user_choice_summary(self, df) -> str:
        """
        Generate a dynamic, user-choice driven summary without detection or assumptions.
        Uses DataProfiler for industry-standard data analysis.
        """
        try:
            # Get comprehensive profile using DataProfiler
            profile = DataProfiler.profile_dataset(df)
            
            # Format the basic profile summary
            summary = DataProfiler.format_profile_summary(profile)
            
            # Add user choice options - SIMPLIFIED TO 2 CLEAR PATHS
            summary += "\n**Choose your analysis approach:**\n\n"
            
            summary += "1️⃣ **Guided TPR Analysis → Risk Assessment**\n"
            summary += "   Step-by-step workflow to calculate Test Positivity Rate and prepare for risk analysis\n\n"
            
            summary += "2️⃣ **Flexible Data Exploration**\n"
            summary += "   Use AI to analyze patterns, create visualizations, and answer any questions about your data\n\n"
            
            summary += "Type **1** for guided TPR workflow or **2** for flexible exploration (or just ask your question directly)\n"
            
            # Add column preview for context (first 10 columns)
            columns = profile.get('preview', {}).get('columns', [])
            if columns:
                summary += "\n**Your columns:** "
                preview_cols = columns[:10]
                summary += ", ".join(f"`{col}`" for col in preview_cols)
                if len(columns) > 10:
                    summary += f" ... and {len(columns) - 10} more"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating user choice summary: {e}")
            # Fallback summary if profiling fails
            return self._generate_fallback_summary(df)
    
    def _generate_fallback_summary(self, df) -> str:
        """Fallback summary if profiling fails."""
        return f"""📊 **Data Successfully Loaded!**

**Dataset Overview:**
• {len(df):,} rows × {len(df.columns)} columns

**Choose your analysis approach:**

1️⃣ **Guided TPR Analysis → Risk Assessment**  
   Step-by-step workflow to calculate Test Positivity Rate and prepare for risk analysis

2️⃣ **Flexible Data Exploration**
   Use AI to analyze patterns, create visualizations, and answer any questions about your data

Type 1 for guided TPR workflow or 2 for flexible exploration (or just ask your question directly)"""
    
    def _is_tpr_selection(self, user_query: str) -> bool:
        """Check if user is explicitly selecting the guided TPR workflow (option 1)."""
        query_lower = user_query.lower().strip()
        
        # Direct selection of option 1
        if query_lower in ['1', '1.', 'option 1', 'first', 'tpr']:
            return True
        
        # Only trigger for EXPLICIT TPR workflow requests
        # Must explicitly ask for the workflow or calculation process
        if ('calculate tpr' in query_lower) or \
           ('tpr calculation' in query_lower) or \
           ('guide' in query_lower and 'tpr' in query_lower) or \
           ('tpr workflow' in query_lower) or \
           ('guided' in query_lower and 'analysis' in query_lower):
            return True
        
        # DO NOT trigger for general analysis queries that happen to mention test/positivity
        # e.g., "Show me test positivity trends" should go to general agent
        
        return False
    
    def _is_flexible_exploration_selection(self, user_query: str) -> bool:
        """Check if user is explicitly selecting flexible data exploration (option 2)."""
        query_lower = user_query.lower().strip()
        
        # Direct selection of option 2
        if query_lower in ['2', '2.', 'option 2', 'second', 'flexible', 'exploration', 'explore']:
            return True
        
        # Check for explicit flexible exploration requests
        if ('flexible' in query_lower and 'exploration' in query_lower) or \
           ('data exploration' in query_lower) or \
           ('explore data' in query_lower):
            return True
        
        return False
    
    def _is_risk_preparation_request(self, user_query: str) -> bool:
        """Check if user wants to prepare for risk analysis."""
        query_lower = user_query.lower().strip()
        
        # Check if TPR is complete first
        tpr_complete_flag = f"instance/uploads/{self.session_id}/.tpr_complete"
        if not os.path.exists(tpr_complete_flag):
            return False
        
        # Check for risk analysis preparation keywords
        if ('prepare' in query_lower and 'risk' in query_lower) or \
           ('risk' in query_lower and 'analysis' in query_lower) or \
           query_lower == '1':  # Option 1 after TPR complete
            return True
        
        return False
    
    def _prepare_for_risk_analysis(self) -> Dict[str, Any]:
        """Prepare TPR data for risk analysis pipeline."""
        logger.info("Preparing TPR data for risk analysis")
        
        try:
            # Import the TPR tool
            from ..tools.tpr_analysis_tool import analyze_tpr_data
            
            # Create graph state
            graph_state = {
                'session_id': self.session_id,
                'data_loaded': True,
                'data_file': f"instance/uploads/{self.session_id}/uploaded_data.csv"
            }
            
            # Call tool with prepare_for_risk action
            result = analyze_tpr_data.invoke({
                'thought': "Preparing TPR data for comprehensive risk analysis",
                'action': "prepare_for_risk",
                'options': "{}",
                'graph_state': graph_state
            })
            
            message = result
            
            # Add follow-up options
            if "TPR Data Prepared for Risk Analysis" in result:
                message += "\n\n✅ **Your data is ready for risk analysis!**\n"
                message += "The system can now:\n"
                message += "• Rank wards by vulnerability\n"
                message += "• Generate intervention priority maps\n"
                message += "• Create comprehensive risk reports\n\n"
                message += "Type 'run risk analysis' to proceed with the full analysis."
            
        except Exception as e:
            logger.error(f"Error preparing for risk analysis: {e}")
            message = f"Error preparing for risk analysis: {str(e)}"
        
        return {
            "success": True,
            "message": message,
            "session_id": self.session_id
        }
    

    # Delegation methods for TPR workflow
    def _start_tpr_workflow(self) -> Dict[str, Any]:
        """Start the TPR workflow - delegates to handler."""
        response = self.tpr_handler.start_workflow()
        self.current_stage = self.tpr_handler.current_stage
        self.tpr_selections = self.tpr_handler.tpr_selections
        return response
    
    def _handle_tpr_workflow(self, user_query: str) -> Optional[Dict[str, Any]]:
        """Handle TPR workflow - delegates to handler."""
        response = self.tpr_handler.handle_workflow(user_query)
        if response:
            self.current_stage = self.tpr_handler.current_stage
            self.tpr_selections = self.tpr_handler.tpr_selections
        return response
    
    def _handle_state_selection(self, user_query: str) -> Dict[str, Any]:
        """Delegates to handler - kept for compatibility."""
        return self.tpr_handler.handle_state_selection(user_query)
    
    def _handle_facility_selection(self, user_query: str) -> Dict[str, Any]:
        """Delegates to handler - kept for compatibility."""
        return self.tpr_handler.handle_facility_selection(user_query)
    
    def _handle_age_group_selection(self, user_query: str) -> Dict[str, Any]:
        """Delegates to handler - kept for compatibility."""
        return self.tpr_handler.handle_age_group_selection(user_query)
    
    def _calculate_tpr(self) -> Dict[str, Any]:
        """Delegates to handler - kept for compatibility."""
        return self.tpr_handler.calculate_tpr()
    
    def _trigger_risk_analysis(self) -> Dict[str, Any]:
        """Trigger risk analysis - delegates to handler."""
        return self.tpr_handler.trigger_risk_analysis()
    
    def _format_state_selection(self, analysis: Dict) -> str:
        """Format state selection message - delegates to formatter."""
        return self.message_formatter.format_state_selection(analysis)
    
    def _format_facility_selection(self, state: str, analysis: Dict) -> str:
        """Format facility selection message - delegates to formatter."""
        return self.message_formatter.format_facility_selection(state, analysis)
    
    def _format_facility_selection_only(self, analysis: Dict) -> str:
        """Format facility selection for single-state - delegates to formatter."""
        return self.message_formatter.format_facility_selection_only(analysis)
    
    def _format_age_group_selection(self, analysis: Dict) -> str:
        """Format age group selection - delegates to formatter."""
        return self.message_formatter.format_age_group_selection(analysis)
    
    def _format_tool_tpr_results(self, tool_output: str) -> str:
        """Format TPR tool results - delegates to formatter."""
        return self.message_formatter.format_tool_tpr_results(tool_output)
    
    def _extract_state_from_query(self, query: str) -> Optional[str]:
        """Extract state from query - delegates to handler."""
        return self.tpr_handler.extract_state_from_query(query)
    
    def _extract_facility_level(self, query: str) -> str:
        """Extract facility level - delegates to handler."""
        return self.tpr_handler.extract_facility_level(query)
    
    def _extract_age_group(self, query: str) -> str:
        """Extract age group - delegates to handler."""
        return self.tpr_handler.extract_age_group(query)
    
    def reset(self):
        """Reset the agent's conversation history and state."""
        self.chat_history = []
        self.current_stage = ConversationStage.INITIAL
        self.tpr_selections = {}
        self.state_manager.clear_state()
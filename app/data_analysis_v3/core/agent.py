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
from ..tools.python_tool import analyze_data, get_data_summary
from ..prompts.system_prompt import MAIN_SYSTEM_PROMPT, get_error_handling_prompt
from ..formatters.response_formatter import format_analysis_response

logger = logging.getLogger(__name__)


class UserIntent(Enum):
    """User intent types for routing."""
    TPR_CALCULATION = "tpr_calculation"
    DATA_EXPLORATION = "data_exploration"
    QUICK_OVERVIEW = "quick_overview"
    UNCLEAR = "unclear"


class ConversationStage(Enum):
    """Conversation stages - flexible flow."""
    INITIAL = "initial"
    TPR_AGE_GROUP = "tpr_age_group"
    TPR_TEST_METHOD = "tpr_test_method"
    TPR_FACILITY_LEVEL = "tpr_facility_level"
    TPR_CALCULATING = "tpr_calculating"
    DATA_EXPLORING = "data_exploring"
    COMPLETE = "complete"


class DataAnalysisAgent:
    """
    Main agent for data analysis using LangGraph.
    Follows AgenticDataAnalysis two-node pattern.
    Uses OpenAI gpt-4o for high-quality analysis.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_stage = ConversationStage.INITIAL
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
        
        # Create the template ONCE (like original)
        self.chat_template = ChatPromptTemplate.from_messages([
            ("system", MAIN_SYSTEM_PROMPT),
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
        Create a summary of available data with user choices.
        """
        # If we have a data summary with choices, use that
        if hasattr(self, 'data_summary') and self.data_summary:
            return self.data_summary
        
        # Create summary from input_data in state (like original)
        summaries = []
        
        if state.get("input_data"):
            for dataset in state["input_data"]:
                var_name = dataset.get("variable_name", "unknown")
                data_path = dataset.get("data_path", "")
                description = dataset.get("data_description", "")
                
                # Try to get basic info about the dataset
                try:
                    import pandas as pd
                    import os
                    if data_path and os.path.exists(data_path):
                        if data_path.endswith('.csv'):
                            df_full = pd.read_csv(data_path)  # Read FULL data
                        else:
                            df_full = pd.read_excel(data_path)  # Read FULL data
                        
                        cols = list(df_full.columns)
                        actual_rows = len(df_full)
                        actual_cols = len(df_full.columns)
                        shape = f"{actual_rows:,} rows, {actual_cols} columns"
                        summaries.append(f"- `{var_name}`: {description} ({shape})")
                        
                        # Make column names VERY clear
                        summaries.append("\n  **EXACT COLUMN NAMES TO USE:**")
                        for i, col in enumerate(cols[:15], 1):
                            summaries.append(f"    {i}. '{col}'")
                        if len(cols) > 15:
                            summaries.append(f"  ... and {len(cols) - 15} more columns")
                        
                        # Highlight important columns if they exist
                        important_cols = ['WardName', 'LGA', 'State', 'HealthFacility', 'FacilityLevel']
                        found_important = [col for col in important_cols if col in cols]
                        if found_important:
                            quoted_cols = [f"'{c}'" for c in found_important]
                            summaries.append(f"\n  **Key columns found:** {', '.join(quoted_cols)}")
                except Exception as e:
                    summaries.append(f"- `{var_name}`: {description}")
        
        if summaries:
            return "\n".join(summaries)
        else:
            return "No datasets loaded yet."
    
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
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)
            
            # Store the data for later use
            self.uploaded_data = df
            self.data_file_name = os.path.basename(data_file)
            
            # Generate user-choice summary (not TPR-specific)
            self.data_summary = self._generate_user_choice_summary(df)
            
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
        Based on AgenticDataAnalysis user_sent_message method.
        """
        # Check for TPR transition confirmation first
        transition_response = self._check_tpr_transition(user_query)
        if transition_response:
            return transition_response
        
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
                    
                    # Create InputData-like dict
                    input_data_list.append({
                        "variable_name": var_name,
                        "data_path": os.path.abspath(filepath),
                        "data_description": f"Dataset from {file}"
                    })
                    logger.info(f"Added dataset: {var_name} from {filepath}")
        
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
        """Generate a user-choice driven summary (not TPR-specific)"""
        import pandas as pd
        
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
        
        # Build summary
        summary = f"📊 **I've successfully loaded your data!**\n\n"
        summary += f"**Data Overview:**\n"
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
            # Check available test types and age groups
            test_types = []
            if any('RDT' in col for col in df.columns):
                test_types.append("RDT")
            if any('Microscopy' in col for col in df.columns):
                test_types.append("Microscopy")
            if test_types:
                summary += f"- Test data: {', '.join(test_types)} available\n"
        
        summary += "\n**What would you like to do?**\n\n"
        summary += "1️⃣ **Explore & Analyze**\n"
        summary += "   Examine patterns, create visualizations, understand your data\n\n"
        
        if has_test_data:
            summary += "2️⃣ **Calculate Test Positivity Rate (TPR)**\n"
            summary += "   I'll guide you through selecting age groups, test methods, and facility levels\n"
            summary += "   📌 *Recommended: Under 5 years, Primary facilities, Both test methods*\n\n"
        
        summary += "3️⃣ **Quick Overview**\n"
        summary += "   Show summary statistics and data quality\n\n"
        
        summary += "Just type what you'd like to do, or say \"1\", \"2\", or \"3\"\n\n"
        summary += "💡 **Tip**: For TPR, I recommend starting with Under 5 data at Primary facilities for best results!"
        
        return summary
    
    def reset(self):
        """Reset the agent's conversation history."""
        self.chat_history = []
# app/web/routes/analysis_routes.py
"""
Analysis Routes module for data analysis operations.

This module contains the analysis-related routes for the ChatMRPT web application:
- Main analysis execution (run_analysis)
- Variable selection explanation  
- AI chat message processing (send_message)
- Analysis state management
"""

import logging
import os
import time
import traceback
import json
from datetime import datetime
from flask import Blueprint, session, request, current_app, jsonify, Response, stream_with_context
from pathlib import Path

from ...core.decorators import handle_errors, log_execution_time, validate_session
from ...core.exceptions import ValidationError
from ...core.utils import convert_to_json_serializable

logger = logging.getLogger(__name__)

# Create the analysis routes blueprint
analysis_bp = Blueprint('analysis', __name__)


async def route_with_mistral(message: str, session_context: dict) -> str:
    """
    Use Mistral to intelligently route requests.
    
    Returns:
        'needs_tools' - Route to OpenAI with tools for data analysis
        'can_answer' - Let Mistral/Arena handle the response
        'needs_clarification' - Ask user for clarification
    """
    # Quick routing for obvious cases
    message_lower = message.lower().strip()
    common_greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'howdy']
    
    # Fast-track greetings to avoid unnecessary routing
    if message_lower in common_greetings or any(message_lower.startswith(g) for g in common_greetings):
        return "can_answer"
    
    # Fast-track common small talk
    if message_lower in ['thanks', 'thank you', 'bye', 'goodbye', 'ok', 'okay', 'sure', 'yes', 'no']:
        return "can_answer"
    
    # CRITICAL: Tool-specific detection BEFORE Mistral routing
    # This ensures tool requests go to tools, not Arena
    if session_context.get('has_uploaded_files', False):
        # Check for analysis tool triggers
        analysis_triggers = [
            'run the malaria risk analysis',
            'run risk analysis',
            'run analysis',
            'perform analysis',
            'analyze the data',
            'analyze my data',
            'start analysis',
            'complete analysis',
            'run the analysis'
        ]
        if any(trigger in message_lower for trigger in analysis_triggers):
            logger.info(f"Tool detection: Analysis trigger found - routing to tools")
            return "needs_tools"
        
        # Check for visualization tool triggers
        visualization_keywords = ['plot', 'map', 'chart', 'visualize', 'graph', 'show me the', 'display']
        if any(keyword in message_lower for keyword in visualization_keywords):
            # Specific visualization checks
            if 'vulnerability' in message_lower and ('map' in message_lower or 'plot' in message_lower):
                logger.info(f"Tool detection: Vulnerability map trigger - routing to tools")
                return "needs_tools"
            elif 'distribution' in message_lower:
                logger.info(f"Tool detection: Distribution visualization trigger - routing to tools")
                return "needs_tools"
            elif any(word in message_lower for word in ['box plot', 'boxplot', 'histogram', 'scatter', 'heatmap', 'bar chart']):
                logger.info(f"Tool detection: Chart type trigger - routing to tools")
                return "needs_tools"
            # General visualization with data
            elif any(keyword in message_lower for keyword in ['plot', 'map', 'chart', 'visualize']):
                logger.info(f"Tool detection: General visualization trigger - routing to tools")
                return "needs_tools"
        
        # Check for ranking/query tool triggers
        ranking_triggers = [
            'top', 'highest', 'lowest', 'rank', 'list wards', 
            'worst', 'best', 'most at risk', 'least at risk',
            'high risk wards', 'low risk wards'
        ]
        if any(trigger in message_lower for trigger in ranking_triggers) and 'ward' in message_lower:
            logger.info(f"Tool detection: Ranking query trigger - routing to tools")
            return "needs_tools"
        
        # Check for data quality and summary triggers
        data_query_triggers = [
            'check data quality',
            'data quality',
            'check quality',
            'summarize the data',
            'summary of data',
            'data summary',
            'describe the data',
            'what variables',
            'available variables'
        ]
        if any(trigger in message_lower for trigger in data_query_triggers):
            logger.info(f"Tool detection: Data query trigger - routing to tools")
            return "needs_tools"
        
        # Check for intervention planning triggers (especially ITN)
        intervention_triggers = [
            'bed net', 'bednet', 'bed-net', 'itn', 'intervention', 'plan distribution',
            'insecticide', 'spray', 'irs', 'treatment',
            'mosquito net', 'llin', 'distribute net', 'distributing net',
            'net distribution', 'nets distribution', 'distribution of net',
            'allocate net', 'allocation of net', 'plan itn', 'itn planning',
            'itn distribution', 'distribute itn', 'plan high trend', 
            'high trend distribution', 'trend distribution'
        ]
        if any(trigger in message_lower for trigger in intervention_triggers):
            logger.info(f"Tool detection: Intervention planning trigger (ITN) - routing to tools")
            return "needs_tools"
        
        # Check for ITN parameter responses (when user provides net count and household size)
        # These patterns indicate user is responding to ITN prompts
        itn_param_patterns = [
            ('have' in message_lower and 'net' in message_lower and any(char.isdigit() for char in message)),
            ('household size' in message_lower and any(char.isdigit() for char in message)),
            ('average household' in message_lower and any(char.isdigit() for char in message)),
            (any(word in message_lower for word in ['million', 'thousand', 'hundred']) and 'net' in message_lower),
            # Common response patterns
            ('i have' in message_lower and any(word in message_lower for word in ['nets', 'bed nets', 'bednets']) and any(char.isdigit() for char in message))
        ]
        if any(pattern for pattern in itn_param_patterns):
            logger.info(f"Tool detection: ITN parameter response detected - routing to tools")
            return "needs_tools"
        
        # Check for specific ward analysis
        if 'why' in message_lower and 'ward' in message_lower and ('rank' in message_lower or 'high' in message_lower or 'risk' in message_lower):
            logger.info(f"Tool detection: Ward analysis explanation trigger - routing to tools")
            return "needs_tools"
    
    try:
        # Import Ollama adapter
        from app.core.ollama_adapter import OllamaAdapter
        ollama = OllamaAdapter()
        
        # Build context information
        files_info = []
        if session_context.get('has_uploaded_files'):
            if session_context.get('csv_loaded'):
                files_info.append("CSV data")
            if session_context.get('shapefile_loaded'):
                files_info.append("Shapefile")
            if session_context.get('analysis_complete'):
                files_info.append("Analysis completed")
        
        files_str = f"Uploaded files: {', '.join(files_info)}" if files_info else "No files uploaded"
        
        # Create routing prompt
        prompt = f"""You are a routing assistant for ChatMRPT, a malaria risk analysis system.

AVAILABLE CAPABILITIES:

1. TOOLS (require uploaded data to function):
   - Analysis Tools: RunMalariaRiskAnalysis
     Purpose: Analyze uploaded malaria data, calculate risk scores, identify high-risk areas
   - Visualization Tools: CreateVulnerabilityMap, CreateBoxPlot, CreateHistogram, CreateHeatmap
     Purpose: Generate maps and charts from uploaded data
   - Export Tools: ExportResults, GenerateReport
     Purpose: Export analysis results to PDF/Excel
   - Data Query Tools: CheckDataQuality, GetSummaryStatistics
     Purpose: Query and examine uploaded data

2. KNOWLEDGE RESPONSES (no data needed):
   - Explain malaria concepts (transmission, epidemiology, prevention)
   - Describe analysis methodologies (PCA, composite scoring, risk assessment)
   - ChatMRPT help and guidance
   - General public health information
   - Answer "what is", "how does", "explain" type questions

Context:
- User has uploaded data: {session_context.get('has_uploaded_files', False)}
- {files_str}

User message: "{message}"

ROUTING DECISION PROCESS:

1. Does the user want to PERFORM AN ACTION on their uploaded data?
   Keywords: analyze, plot, visualize, calculate, generate, create, run, export, check, perform
   → If YES and data exists: Reply NEEDS_TOOLS
   
2. Does the user want INFORMATION or EXPLANATION?
   Keywords: what is, how does, explain, tell me about, describe, why
   → Reply CAN_ANSWER (even if data exists - they want knowledge, not action)

3. Is the message explicitly about their uploaded data?
   Phrases: "my data", "the data", "my file", "the csv", "uploaded"
   → If asking for action: Reply NEEDS_TOOLS
   → If asking for explanation: Reply CAN_ANSWER

CRITICAL EXAMPLES:
With data uploaded:
ANALYSIS REQUESTS → NEEDS_TOOLS:
- "Run the malaria risk analysis" → NEEDS_TOOLS (runs run_complete_analysis tool)
- "perform analysis" → NEEDS_TOOLS (analysis action)
- "run analysis" → NEEDS_TOOLS (analysis action)
- "analyze my data" → NEEDS_TOOLS (explicit data operation)
- "start the analysis" → NEEDS_TOOLS (initiate analysis)

VISUALIZATION REQUESTS → NEEDS_TOOLS:
- "plot vulnerability map" → NEEDS_TOOLS (creates vulnerability visualization)
- "plot me the map distribution of evi" → NEEDS_TOOLS (variable distribution map)
- "show me the distribution" → NEEDS_TOOLS (distribution visualization)
- "create a heatmap" → NEEDS_TOOLS (heatmap generation)
- "plot box plot" → NEEDS_TOOLS (box plot visualization)
- "visualize the data" → NEEDS_TOOLS (data visualization)

RANKING/QUERY REQUESTS → NEEDS_TOOLS:
- "show me top 10 highest risk wards" → NEEDS_TOOLS (ranking query)
- "list the worst affected areas" → NEEDS_TOOLS (ranking query)
- "which wards are at highest risk" → NEEDS_TOOLS (risk ranking)
- "why is kafin dabga ward ranked so highly" → NEEDS_TOOLS (ward analysis)

DATA OPERATIONS → NEEDS_TOOLS:
- "Check data quality" → NEEDS_TOOLS (data quality check)
- "summarize the data" → NEEDS_TOOLS (data summary)
- "what variables do we have" → NEEDS_TOOLS (variable listing)
- "describe my dataset" → NEEDS_TOOLS (dataset description)

INTERVENTION PLANNING → NEEDS_TOOLS:
- "plan bed net distribution" → NEEDS_TOOLS (ITN planning tool)
- "where should we distribute mosquito nets" → NEEDS_TOOLS (intervention targeting)
- "plan IRS campaign" → NEEDS_TOOLS (spray planning)

KNOWLEDGE QUESTIONS → CAN_ANSWER:
- "what is analysis" → CAN_ANSWER (asking for explanation)
- "how does PCA work" → CAN_ANSWER (methodology explanation)
- "what is malaria" → CAN_ANSWER (disease information)
- "explain transmission" → CAN_ANSWER (educational content)
- "who are you" → CAN_ANSWER (identity question)

Without data uploaded:
- "analyze" → CAN_ANSWER (no data to analyze, explain concept)
- "plot" → CAN_ANSWER (no data to plot, explain concept)

Reply ONLY: NEEDS_TOOLS, CAN_ANSWER, or NEEDS_CLARIFICATION"""
        
        # Get Mistral's routing decision
        import asyncio
        response = await ollama.generate_async(
            model="mistral:7b",
            prompt=prompt,
            max_tokens=20,
            temperature=0.1  # Low temperature for consistent routing
        )
        
        # Parse and validate response
        decision = response.strip().upper()
        # Routing decision made
        
        if decision == "NEEDS_TOOLS":
            return "needs_tools"
        elif decision == "CAN_ANSWER":
            return "can_answer"
        elif decision == "NEEDS_CLARIFICATION":
            return "needs_clarification"
        else:
            # Fallback if Mistral gives unexpected response
            logger.warning(f"Unexpected Mistral response: {decision}. Using fallback logic.")
            # Check if message explicitly references data
            message_lower = message.lower().strip()
            data_references = ['my data', 'the data', 'uploaded', 'my file', 'the file', 
                             'my csv', 'the csv', 'analyze this', 'plot my', 'visualize the']
            if any(ref in message_lower for ref in data_references):
                return "needs_tools"
            # Default to conversational for general questions
            return "can_answer"
            
    except Exception as e:
        logger.error(f"Error in Mistral routing: {e}. Using neutral fallback.")
        # When Mistral fails, we don't guess - we ask for clarification
        # This prevents incorrect routing when the system is uncertain
        return "needs_clarification"


@analysis_bp.route('/run_analysis', methods=['POST'])
@validate_session
@handle_errors
@log_execution_time
def run_analysis():
    """Run the analysis directly (used for API calls, not main chat flow)"""
    try:
        # Get session ID
        session_id = session.get('session_id', 'default')
        
        # Debug logging
        logger.info(f"[DEBUG] run_analysis: session_id={session_id}")
        data_service = current_app.services.data_service
        data_handler = data_service.get_handler(session_id)
        logger.info(f"[DEBUG] run_analysis: data_handler exists: {data_handler is not None}")
        if data_handler:
            has_df = hasattr(data_handler, 'df') and data_handler.df is not None
            logger.info(f"[DEBUG] run_analysis: data_handler.df exists: {has_df}")
        
        # Get custom parameters from the request
        data = request.json or {}
        selected_variables = data.get('selected_variables', None)
        use_llm_selection = data.get('use_llm_selection', True)
        
        # Get services from the container
        analysis_service = current_app.services.analysis_service
        
        if not data_handler:
            raise ValidationError('Data handler not initialized. Please upload data files first.')
        
        # Check if both files are loaded
        if not session.get('csv_loaded', False) or not session.get('shapefile_loaded', False):
            raise ValidationError('Please upload both CSV and shapefile data before running analysis')
        
        # Run the analysis using the service
        if selected_variables:
            # Run custom analysis with specified variables
            result = analysis_service.run_custom_analysis(
                data_handler=data_handler,
                selected_variables=selected_variables,
                session_id=session_id
            )
        else:
            # Run standard analysis (which will use LLM selection if configured)
            result = analysis_service.run_standard_analysis(
                data_handler=data_handler,
                session_id=session_id
            )
        
        # Process the result
        if result['status'] == 'success':
            # Store JSON-serializable data in session
            session['analysis_complete'] = True
            session['variables_used'] = result.get('variables_used', [])
            # CRITICAL: Mark session as modified for filesystem sessions
            session.modified = True
            
            # Extract risk wards from vulnerability rankings if available
            high_risk_wards = []
            medium_risk_wards = []
            low_risk_wards = []
            
            # Check if data_handler has vulnerability rankings
            if hasattr(data_handler, 'vulnerability_rankings') and data_handler.vulnerability_rankings is not None:
                rankings = data_handler.vulnerability_rankings
                
                # Extract wards by category
                if 'vulnerability_category' in rankings.columns and 'WardName' in rankings.columns:
                    high_risk_wards = rankings[rankings['vulnerability_category'] == 'High']['WardName'].tolist()
                    medium_risk_wards = rankings[rankings['vulnerability_category'] == 'Medium']['WardName'].tolist()
                    low_risk_wards = rankings[rankings['vulnerability_category'] == 'Low']['WardName'].tolist()
            
            # Use extracted wards or fall back to result wards
            high_risk_wards = high_risk_wards or result.get('high_risk_wards', [])
            medium_risk_wards = medium_risk_wards or result.get('medium_risk_wards', [])
            low_risk_wards = low_risk_wards or result.get('low_risk_wards', [])
            
            # Return success response
            return jsonify({
                'status': 'success',
                'message': 'Analysis completed successfully',
                'variables_used': result.get('variables_used', []),
                'high_risk_wards': high_risk_wards[:10],
                'medium_risk_wards': medium_risk_wards[:10],
                'low_risk_wards': low_risk_wards[:10]
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('message', 'Error running analysis')
            }), 400
    
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error running analysis: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error running analysis: {str(e)}'
        }), 500


@analysis_bp.route('/explain_variable_selection', methods=['GET'])
@validate_session
@handle_errors
@log_execution_time
def explain_variable_selection():
    """Generate an explanation for why certain variables were selected for the analysis"""
    try:
        # Get session ID
        session_id = session.get('session_id')
        if not session_id:
            raise ValidationError('No active session found')
        
        # Get services from the container
        data_service = current_app.services.data_service
        analysis_service = current_app.services.analysis_service
        
        # Get data handler via data service
        data_handler = data_service.get_handler(session_id)
        if not data_handler:
            raise ValidationError('No data available for explanation')
            
        # Check if analysis has been performed
        if not session.get('analysis_complete', False) or not session.get('variables_used'):
            raise ValidationError('Analysis not yet performed')
        
        # Get variables used in the analysis
        variables = session.get('variables_used', [])
        if not variables:
            raise ValidationError('No variables found from analysis')
        
        # Get explanation using the service
        result = analysis_service.explain_variable_selection(
            variables=variables,
            data_handler=data_handler
        )
        
        if result['status'] == 'success':
            return jsonify({
                'status': 'success',
                'message': 'Generated variable selection explanation',
                'explanation': result.get('explanations', {}),
                'variables': variables
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('message', 'Error generating explanation')
            }), 400
    
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error explaining variable selection: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error generating explanation: {str(e)}'
        }), 500


@analysis_bp.route('/send_message', methods=['POST'])
@validate_session
@handle_errors
@log_execution_time
def send_message():
    """
    Handle chat messages with Request Interpreter (NEW TOOL-BASED SYSTEM).
    """
    
    try:
        # Get the message from the request
        data = request.json
        user_message = data.get('message', '')
        if not user_message: 
            raise ValidationError('No message provided')

        # Get tab context from frontend
        tab_context = data.get('tab_context', 'standard-upload')
        is_data_analysis = data.get('is_data_analysis', False)
        
        # Store in session for persistence
        if is_data_analysis:
            session['active_tab'] = 'data-analysis'
            session['use_data_analysis_v3'] = True
            logger.info(f"📊 Data Analysis tab active - setting V3 mode")
        
        # Get session ID
        session_id = session.get('session_id')
        
        # 🎯 COMPREHENSIVE RESPONSE TIME TRACKING - CRITICAL FOR DEMO ANALYTICS
        request_start_time = time.time()
        message_start_time = time.time()
        if hasattr(current_app, 'services') and current_app.services.interaction_logger:
            interaction_logger = current_app.services.interaction_logger
            
            # Log incoming user message with metadata
            interaction_logger.log_message(
                session_id=session_id,
                sender='user',
                content=user_message,
                intent=None,  # Will be filled after request interpretation
                entities={
                    'message_length': len(user_message),
                    'timestamp': message_start_time,
                    'session_message_count': session.get('message_count', 0) + 1,
                    'request_endpoint': '/send_message'
                }
            )
            
            # Track user journey milestone
            interaction_logger.log_analysis_event(
                session_id=session_id,
                event_type='user_interaction',
                details={
                    'action': 'message_sent',
                    'message_type': 'chat_request',
                    'session_duration': time.time() - session.get('session_start_time', time.time()),
                    'is_follow_up': session.get('message_count', 0) > 0
                },
                success=True
            )
            
            # Update session message counter
            session['message_count'] = session.get('message_count', 0) + 1
        
        # Check for active TPR workflow FIRST
        if session.get('tpr_workflow_active', False):
            logger.info(f"TPR workflow active for session {session_id}, routing to TPR handler")
            
            # Import TPR workflow router
            try:
                from ...tpr_module.integration.tpr_workflow_router import TPRWorkflowRouter
                
                # Get LLM manager for intent classification
                llm_manager = None
                if hasattr(current_app, 'services') and hasattr(current_app.services, 'llm_manager'):
                    llm_manager = current_app.services.llm_manager
                
                # Create router and route the message
                router = TPRWorkflowRouter(session_id, llm_manager)
                tpr_result = router.route_message(user_message, dict(session))
                
                # Check if TPR router wants to transition to main interpreter
                if tpr_result.get('response') == '__DATA_UPLOADED__':
                    logger.info(f"TPR router requesting transition to main interpreter for __DATA_UPLOADED__")
                    # Clear TPR flags and fall through to main request interpreter
                    session.pop('tpr_workflow_active', None)
                    session.pop('tpr_session_id', None)
                    # Ensure proper flags for main workflow
                    session['csv_loaded'] = True
                    session['has_uploaded_files'] = True
                    session['analysis_complete'] = True
                    session.modified = True
                    # Set the message to trigger exploration menu
                    user_message = '__DATA_UPLOADED__'
                    # Let it fall through to normal processing
                elif tpr_result.get('status') == 'tpr_to_main_transition':
                    logger.info(f"TPR router requesting transition to main interpreter for __DATA_UPLOADED__")
                    # Clear TPR flags and fall through to main request interpreter
                    session.pop('tpr_workflow_active', None)
                    session.pop('tpr_session_id', None)
                    # Ensure proper flags for main workflow
                    session['csv_loaded'] = True
                    session['has_uploaded_files'] = True
                    session['analysis_complete'] = True
                    session.modified = True
                    # Set the message to trigger exploration menu
                    user_message = '__DATA_UPLOADED__'
                    # Let it fall through to normal processing
                else:
                    # Format response for frontend
                    formatted_response = {
                        'status': tpr_result.get('status', 'success'),
                        'message': tpr_result.get('response', ''),
                        'response': tpr_result.get('response', ''),  # Frontend expects this field
                        'tools_used': tpr_result.get('tools_used', []),
                        'workflow': tpr_result.get('workflow', 'tpr'),
                        'stage': tpr_result.get('stage'),
                        'processing_time': f"{time.time() - request_start_time:.2f}s",
                        'total_response_time': f"{time.time() - request_start_time:.2f}s",
                        'trigger_data_uploaded': tpr_result.get('trigger_data_uploaded', False)
                    }
                    
                    # Add visualizations if present
                    if tpr_result.get('visualizations'):
                        formatted_response['visualizations'] = tpr_result['visualizations']
                    
                    # Add download links if present
                    if tpr_result.get('download_links'):
                        formatted_response['download_links'] = tpr_result['download_links']
                    
                    logger.info(f"TPR response sent: status={formatted_response.get('status')}, stage={tpr_result.get('stage')}")
                    return jsonify(formatted_response)
                
            except Exception as e:
                logger.error(f"Error routing to TPR handler: {e}")
                # Fall through to normal processing if TPR routing fails
        
        # Check if user has uploaded files
        session_folder = f"instance/uploads/{session_id}"
        has_uploaded_files = False
        if os.path.exists(session_folder):
            # Check for actual data files (not just folders)
            for f in os.listdir(session_folder):
                if f.endswith(('.csv', '.xlsx', '.xls', '.shp', '.zip')) and not f.startswith('.'):
                    has_uploaded_files = True
                    break
        
        # CRITICAL: Trust session flags after TPR transition or when analysis is complete
        # TPR workflow sets these flags but may not create files in the expected location
        if session.get('csv_loaded', False) or session.get('analysis_complete', False):
            has_uploaded_files = True
        
        # Build session context for Mistral routing
        session_context = {
            'has_uploaded_files': has_uploaded_files,
            'session_id': session_id,
            'csv_loaded': session.get('csv_loaded', False),
            'shapefile_loaded': session.get('shapefile_loaded', False),
            'analysis_complete': session.get('analysis_complete', False)
        }
        
        # Check if this is a response to a clarification prompt
        if session.get('pending_clarification'):
            # User is responding to clarification - try to route again with more context
            original_context = session['pending_clarification']
            combined_message = f"{original_context['original_message']} {user_message}"
            session.pop('pending_clarification', None)
            session.modified = True
            
            # Route the combined message
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                routing_decision = loop.run_until_complete(route_with_mistral(combined_message, session_context))
            finally:
                loop.close()
            
            logger.info(f"Clarification response routing: {routing_decision}")
            user_message = original_context['original_message']  # Use original message for processing
        else:
            # Get Mistral routing decision
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                routing_decision = loop.run_until_complete(route_with_mistral(user_message, session_context))
            finally:
                loop.close()
            
            # Routing decision made
            
            # Handle clarification requests
            if routing_decision == 'needs_clarification':
                # Double-check if we really need clarification
                # Very short messages should just get responses
                if len(user_message.strip().split()) <= 3:
                    routing_decision = 'can_answer'  # Override to conversational
                    use_arena = True
                    use_tools = False
                else:
                    # Generate clarification prompt only for genuinely ambiguous cases
                    clarification = {
                        'needs_clarification': True,
                        'clarification_type': 'intent',
                        'message': "I need more information to help you. Are you looking to:",
                        'options': [
                            {
                                'id': 'analyze_data',
                                'label': 'Analyze your uploaded data',
                                'icon': '📊',
                                'value': 'tools'
                            },
                            {
                                'id': 'general_info',
                                'label': 'Get general information',
                                'icon': '📚',
                                'value': 'arena'
                            }
                        ],
                        'original_message': user_message,
                        'session_context': session_context
                    }
                    
                    # Store context for when user responds
                    session['pending_clarification'] = {
                        'original_message': user_message,
                        'context': session_context
                    }
                    session.modified = True
                    
                    logger.info(f"Returning clarification prompt")
                    return jsonify(clarification)
        
        # Route based on Mistral's decision
        use_arena = (routing_decision == 'can_answer')
        use_tools = (routing_decision == 'needs_tools')
        
        logger.info(f"Final routing: use_arena={use_arena}, use_tools={use_tools}")
        
        # Initialize timing for both paths
        processing_start_time = time.time()
        
        if use_arena:
            # Use Arena mode - get responses from 2 models for comparison
            # Using Arena mode
            
            # Import Arena manager, system prompt, and context manager
            from app.core.arena_manager import ArenaManager
            from app.core.arena_system_prompt import get_arena_system_prompt
            from app.core.arena_context_manager import get_arena_context_manager
            arena_manager = ArenaManager()
            
            # Get base Arena system prompt
            base_arena_prompt = get_arena_system_prompt()
            
            # Enhance with session context
            context_manager = get_arena_context_manager()
            session_context = context_manager.get_session_context(
                session_id=session_id,
                session_data=dict(session)
            )
            context_enhancement = context_manager.format_context_for_prompt(session_context)
            arena_system_prompt = base_arena_prompt + context_enhancement
            
            # Start battle
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Get current view index from session or default to 0
                view_index = session.get('arena_view_index', 0)
                
                # Start battle with specific view
                battle_result = loop.run_until_complete(
                    arena_manager.start_battle(user_message, session_id, view_index)
                )
                battle_id = battle_result['battle_id']
                
                # Get model pair for this view
                model_a, model_b = arena_manager.get_model_pair_for_view(view_index)
                
                # Call both models via vLLM
                import requests
                responses = {}
                latencies = {}
                
                # Model A response using Ollama API
                try:
                    start = time.time()
                    # Map model names to Ollama model names
                    # FIXED: These must match exactly what ArenaManager returns
                    ollama_model_map = {
                        'llama3.1:8b': 'llama3.1:8b',
                        'mistral:7b': 'mistral:7b',
                        'phi3:mini': 'phi3:mini',
                        'gemma2:9b': 'gemma2:9b',
                        'qwen2.5:7b': 'qwen2.5:7b'
                    }
                    
                    if model_a in ollama_model_map:
                        # Use environment variable or fallback to localhost
                        ollama_host = current_app.config.get('OLLAMA_HOST', 'localhost')
                        ollama_port = current_app.config.get('OLLAMA_PORT', '11434')
                        ollama_url = f"http://{ollama_host}:{ollama_port}/v1/chat/completions"
                        
                        # Use the comprehensive system prompt
                        ollama_payload = {
                            "model": ollama_model_map[model_a],
                            "messages": [
                                {"role": "system", "content": arena_system_prompt},
                                {"role": "user", "content": user_message}
                            ],
                            "max_tokens": 500
                        }
                        logger.info(f"Arena Model A - URL: {ollama_url}, Model: {ollama_model_map[model_a]}")
                        ollama_response = requests.post(ollama_url, json=ollama_payload, timeout=60)
                        logger.info(f"Arena Model A - Status: {ollama_response.status_code}")
                        if ollama_response.status_code == 200:
                            responses['a'] = ollama_response.json()['choices'][0]['message']['content']
                        else:
                            logger.error(f"Arena Model A - Error: {ollama_response.text[:200]}")
                            responses['a'] = f"Error from Ollama: {ollama_response.status_code}"
                    else:
                        responses['a'] = f"Model {model_a} not available in Ollama"
                    
                    latencies['a'] = (time.time() - start) * 1000
                except Exception as e:
                    logger.error(f"Error calling model A: {e}")
                    responses['a'] = f"Error: {str(e)}"
                    latencies['a'] = 0
                
                # Model B response using Ollama API
                try:
                    start = time.time()
                    # Use same model map
                    # FIXED: These must match exactly what ArenaManager returns
                    ollama_model_map = {
                        'llama3.1:8b': 'llama3.1:8b',
                        'mistral:7b': 'mistral:7b',
                        'phi3:mini': 'phi3:mini',
                        'gemma2:9b': 'gemma2:9b',
                        'qwen2.5:7b': 'qwen2.5:7b'
                    }
                    
                    if model_b in ollama_model_map:
                        # Use environment variable or fallback to localhost
                        ollama_host = current_app.config.get('OLLAMA_HOST', 'localhost')
                        ollama_port = current_app.config.get('OLLAMA_PORT', '11434')
                        ollama_url = f"http://{ollama_host}:{ollama_port}/v1/chat/completions"
                        
                        # Use the comprehensive system prompt
                        ollama_payload = {
                            "model": ollama_model_map[model_b],
                            "messages": [
                                {"role": "system", "content": arena_system_prompt},
                                {"role": "user", "content": user_message}
                            ],
                            "max_tokens": 500
                        }
                        logger.info(f"Arena Model B - URL: {ollama_url}, Model: {ollama_model_map[model_b]}")
                        ollama_response = requests.post(ollama_url, json=ollama_payload, timeout=60)
                        logger.info(f"Arena Model B - Status: {ollama_response.status_code}")
                        if ollama_response.status_code == 200:
                            responses['b'] = ollama_response.json()['choices'][0]['message']['content']
                        else:
                            logger.error(f"Arena Model B - Error: {ollama_response.text[:200]}")
                            responses['b'] = f"Error from Ollama: {ollama_response.status_code}"
                    else:
                        responses['b'] = f"Model {model_b} not available in Ollama"
                    
                    latencies['b'] = (time.time() - start) * 1000
                except Exception as e:
                    logger.error(f"Error calling model B: {e}")
                    responses['b'] = f"Error: {str(e)}"
                    latencies['b'] = 0
                
                # Check if Arena models indicate they need tools
                # This avoids hardcoding - let models self-identify!
                tool_need_indicators = [
                    "i need to see", "upload", "provide the", "i would need",
                    "cannot analyze without", "don't have access", "no data available",
                    "please share", "i require", "unable to access", "can't see your"
                ]
                
                response_a_lower = responses.get('a', '').lower()
                response_b_lower = responses.get('b', '').lower()
                
                model_a_needs_tools = any(indicator in response_a_lower for indicator in tool_need_indicators)
                model_b_needs_tools = any(indicator in response_b_lower for indicator in tool_need_indicators)
                
                # If BOTH models say they need tools, fallback to GPT-4o
                if model_a_needs_tools and model_b_needs_tools:
                    # Arena models need tools - falling back to GPT-4o
                    
                    # Close the Arena loop
                    loop.close()
                    
                    # Mark that we need to use tools for this session
                    session['last_tool_used'] = True
                    session.modified = True
                    
                    # Use Request Interpreter with GPT-4o (it has tool access)
                    from app.core.request_interpreter import RequestInterpreter
                    interpreter = RequestInterpreter()
                    result = interpreter.interpret(user_message, session, is_data_analysis=is_data_analysis)
                    
                    processing_time = time.time() - processing_start_time
                    response = {
                        'status': 'success',
                        'response': result.get('message', result.get('response', '')),
                        'message': result.get('message', result.get('response', '')),
                        'processing_time': processing_time
                    }
                    
                    # Return the GPT-4o response
                    return jsonify(response)
                
                # Only submit to arena if we're still using Arena
                if use_arena:
                    # Submit responses to arena
                    loop.run_until_complete(
                        arena_manager.submit_response(battle_id, 'a', responses['a'], latencies['a'])
                    )
                    loop.run_until_complete(
                        arena_manager.submit_response(battle_id, 'b', responses['b'], latencies['b'])
                    )
                    
                    # Return Arena-style response
                    response = {
                    'status': 'success',
                    'arena_mode': True,
                    'battle_id': battle_id,
                    'response_a': responses['a'],
                    'response_b': responses['b'],
                    'latency_a': latencies['a'],
                    'latency_b': latencies['b'],
                    'view_index': view_index,
                    'model_a': model_a,  # Don't reveal until after voting
                    'model_b': model_b,  # Don't reveal until after voting
                    'response': f"Arena comparison ready. View {view_index + 1} of 3."
                }
                
            finally:
                loop.close()
                
        else:
            # Use GPT-4o for tool-based requests
            # Get Request Interpreter service
            try:
                request_interpreter = current_app.services.request_interpreter
                if request_interpreter is None:
                    logger.error("Request Interpreter not available")
                    return jsonify({
                        'status': 'error',
                        'message': 'Request processing system not available'
                    }), 500
            except Exception as e:
                logger.error(f"Error getting Request Interpreter: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Error accessing request processing system'
                }), 500
            
            # Process message with Request Interpreter
            logger.info(f"Processing message with Request Interpreter: '{user_message[:100]}...'")
            # Pass the data analysis context flags to the request interpreter
            response = request_interpreter.process_message(
                user_message, 
                session_id,
                is_data_analysis=is_data_analysis,
                tab_context=tab_context
            )
        processing_duration = time.time() - processing_start_time
        
        # 🎯 LOG AI RESPONSE - CRITICAL FOR DEMO ANALYTICS
        if hasattr(current_app, 'services') and current_app.services.interaction_logger:
            interaction_logger = current_app.services.interaction_logger
            
            # Calculate comprehensive response timing
            total_response_time = time.time() - request_start_time
            overhead_time = total_response_time - processing_duration
            
            # Log AI response with comprehensive timing metadata
            ai_response_content = response.get('response', 'Request processed successfully')
            interaction_logger.log_message(
                session_id=session_id,
                sender='assistant',
                content=ai_response_content,
                intent=response.get('intent_type'),
                entities={
                    'response_length': len(ai_response_content),
                    'processing_time_seconds': processing_duration,
                    'total_response_time_seconds': total_response_time,
                    'overhead_time_seconds': overhead_time,
                    'response_efficiency': round(processing_duration / total_response_time * 100, 1) if total_response_time > 0 else 100,
                    'tools_used': response.get('tools_used', []),
                    'tools_count': len(response.get('tools_used', [])),
                    'visualizations_created': len(response.get('visualizations', [])),
                    'status': response.get('status', 'success'),
                    'timestamp': time.time(),
                    'performance_category': 'fast' if total_response_time < 5 else 'medium' if total_response_time < 15 else 'slow'
                }
            )
            
            # Log comprehensive response timing for demo analytics
            detailed_timing = response.get('timing_breakdown', {})
            performance_metrics = response.get('performance_metrics', {})
            
            interaction_logger.log_analysis_event(
                session_id=session_id,
                event_type='response_timing',
                details={
                    'total_response_time_seconds': total_response_time,
                    'processing_time_seconds': processing_duration,
                    'overhead_time_seconds': overhead_time,
                    'response_efficiency_percent': round(processing_duration / total_response_time * 100, 1) if total_response_time > 0 else 100,
                    'performance_category': 'fast' if total_response_time < 5 else 'medium' if total_response_time < 15 else 'slow',
                    'message_length': len(user_message),
                    'response_length': len(ai_response_content),
                    'complexity_score': len(response.get('tools_used', [])) * 2 + len(response.get('visualizations', [])),
                    'endpoint': '/send_message',
                    # Enhanced timing breakdown
                    'timing_breakdown': {
                        'context_retrieval_ms': detailed_timing.get('context_retrieval', 0) * 1000,
                        'prompt_building_ms': detailed_timing.get('prompt_building', 0) * 1000,
                        'llm_processing_ms': detailed_timing.get('llm_processing', 0) * 1000,
                        'tool_execution_ms': detailed_timing.get('tool_execution', 0) * 1000,
                        'response_formatting_ms': detailed_timing.get('response_formatting', 0) * 1000,
                        'total_duration_ms': detailed_timing.get('total_duration', 0) * 1000
                    },
                    'performance_metrics': {
                        'llm_percentage': performance_metrics.get('llm_percentage', 0),
                        'tool_percentage': performance_metrics.get('tool_percentage', 0),
                        'context_percentage': performance_metrics.get('context_percentage', 0),
                        'bottleneck': performance_metrics.get('bottleneck', 'unknown')
                    }
                },
                success=True
            )
            
            # Log tools usage for analytics
            tools_used = response.get('tools_used', [])
            if tools_used:
                interaction_logger.log_analysis_event(
                    session_id=session_id,
                    event_type='tools_execution',
                    details={
                        'tools_used': tools_used,
                        'execution_time_seconds': processing_duration,
                        'total_response_time_seconds': total_response_time,
                        'request_type': response.get('intent_type', 'unknown'),
                        'success_rate': 1.0 if response.get('status') == 'success' else 0.0,
                        'user_message_trigger': user_message[:100] + '...' if len(user_message) > 100 else user_message,
                        'performance_impact': round((processing_duration / total_response_time) * 100, 1) if total_response_time > 0 else 0
                    },
                    success=response.get('status') == 'success'
                )
        
        # Format response for frontend
        # Check if this is an Arena response
        if response.get('arena_mode'):
            # Preserve Arena-specific fields
            formatted_response = {
                'status': response.get('status', 'success'),
                'message': response.get('response', 'Arena comparison ready'),
                'response': response.get('response', 'Arena comparison ready'),
                'arena_mode': True,
                'battle_id': response.get('battle_id'),
                'response_a': response.get('response_a'),
                'response_b': response.get('response_b'),
                'latency_a': response.get('latency_a'),
                'latency_b': response.get('latency_b'),
                'view_index': response.get('view_index'),
                'model_a': response.get('model_a'),
                'model_b': response.get('model_b'),
                'processing_time': f"{processing_duration:.2f}s",
                'total_response_time': f"{total_response_time:.2f}s",
                'response_efficiency': f"{round(processing_duration / total_response_time * 100, 1) if total_response_time > 0 else 100}%"
            }
        else:
            # Standard response formatting
            formatted_response = {
                'status': response.get('status', 'success'),
                'message': response.get('response', 'Request processed successfully'),
                'response': response.get('response', 'Request processed successfully'),  # Frontend expects this field
                'explanations': response.get('explanations', []),
                'data_summary': response.get('data_summary'),
                'tools_used': response.get('tools_used', []),
                'intent_type': response.get('intent_type'),
                'processing_time': f"{processing_duration:.2f}s",
                'total_response_time': f"{total_response_time:.2f}s",
                'response_efficiency': f"{round(processing_duration / total_response_time * 100, 1) if total_response_time > 0 else 100}%"
            }
        
        # Only include visualizations if they actually exist and have valid content
        visualizations = response.get('visualizations', [])
        if visualizations and len(visualizations) > 0:
            # Filter out empty or invalid visualizations
            valid_visualizations = [
                viz for viz in visualizations 
                if isinstance(viz, dict) and (viz.get('url') or viz.get('path') or viz.get('html'))
            ]
            if valid_visualizations:
                formatted_response['visualizations'] = valid_visualizations
        
        # Update session state based on tools used
        tools_used = response.get('tools_used', [])
        
        if any(tool in tools_used for tool in ['run_composite_analysis', 'run_pca_analysis', 'runcompleteanalysis']):
            session['analysis_complete'] = True
            if 'runcompleteanalysis' in tools_used:
                session['analysis_type'] = 'dual_method'
            elif 'run_composite_analysis' in tools_used:
                session['analysis_type'] = 'composite'
            else:
                session['analysis_type'] = 'pca'
            # CRITICAL: Mark session as modified for filesystem sessions
            session.modified = True
            logger.info(f"Session {session_id}: Analysis completed via Request Interpreter ({session['analysis_type']})")
        
        # Clear any pending actions if analysis was run
        if any(tool in tools_used for tool in ['run_composite_analysis', 'run_pca_analysis', 'runcompleteanalysis']):
                session.pop('pending_action', None)
                session.pop('pending_variables', None)
                # CRITICAL: Mark session as modified after pop operations
                session.modified = True
        
        # Ensure response is JSON serializable
        formatted_response = convert_to_json_serializable(formatted_response)
        
        logger.info(f"Request Interpreter response sent: status={formatted_response.get('status')}, tools={len(tools_used)}")
        return jsonify(formatted_response)
    
    except ValidationError as e:
        # 🎯 LOG VALIDATION ERRORS - DEMO INSIGHTS
        if hasattr(current_app, 'services') and current_app.services.interaction_logger:
            interaction_logger = current_app.services.interaction_logger
            interaction_logger.log_error(
                session_id=session.get('session_id'),
                error_type='ValidationError',
                error_message=str(e),
                stack_trace=traceback.format_exc()
            )
        
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        # 🎯 LOG SYSTEM ERRORS - CRITICAL FOR DEMO MONITORING
        session_id = session.get('session_id')
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'endpoint': '/send_message',
            'user_message': locals().get('user_message', 'Unknown')[:100],
            'processing_stage': 'request_interpreter_processing',
            'timestamp': time.time()
        }
        
        if hasattr(current_app, 'services') and current_app.services.interaction_logger:
            interaction_logger = current_app.services.interaction_logger
            interaction_logger.log_error(
                session_id=session_id,
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=traceback.format_exc()
            )
            
            # Log error as analysis event for demo monitoring
            interaction_logger.log_analysis_event(
                session_id=session_id,
                event_type='system_error',
                details=error_details,
                success=False
            )
        
        logger.error(f"Error processing message with Request Interpreter: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error processing message: {str(e)}'
        }), 500


@analysis_bp.route('/api/vote_arena', methods=['POST'])
@validate_session
@handle_errors
def vote_arena():
    """
    Record user vote for Arena model comparison in tournament style.
    After voting, either returns the next matchup or final results.
    """
    try:
        data = request.json
        battle_id = data.get('battle_id')
        vote = data.get('vote')  # 'a', 'b', 'tie', or 'bad'
        session_id = session.get('session_id', 'unknown')
        
        # Log the vote
        logger.info(f"Arena vote received: battle_id={battle_id}, vote={vote}, session={session_id}")
        
        # Get Arena manager, system prompt, and context manager
        from app.core.arena_manager import ArenaManager
        from app.core.arena_system_prompt import get_arena_system_prompt
        from app.core.arena_context_manager import get_arena_context_manager
        arena_manager = ArenaManager()
        
        # Get enhanced Arena system prompt with context
        base_arena_prompt = get_arena_system_prompt()
        context_manager = get_arena_context_manager()
        session_context = context_manager.get_session_context(
            session_id=session_id,
            session_data=dict(session)
        )
        context_enhancement = context_manager.format_context_for_prompt(session_context)
        arena_system_prompt = base_arena_prompt + context_enhancement
        
        # Get the progressive battle
        battle = arena_manager.storage.get_progressive_battle(battle_id)
        if not battle:
            return jsonify({
                'success': False,
                'error': 'Battle session not found'
            }), 404
        
        # Map vote to choice for progressive battle
        if vote == 'a':
            choice = 'left'
        elif vote == 'b':
            choice = 'right'
        else:  # tie or bad - pick random winner
            import random
            choice = 'left' if random.random() > 0.5 else 'right'
        
        # Record the choice
        more_rounds = battle.record_choice(choice)
        
        # Get winner and loser from current matchup
        model_a, model_b = battle.current_pair
        winner = model_a if choice == 'left' else model_b
        loser = model_b if choice == 'left' else model_a
        
        logger.info(f"Battle {battle_id}: {winner} beat {loser}")
        
        # Check if more rounds needed
        if more_rounds and battle.current_pair:
            # Get next matchup
            next_model_a, next_model_b = battle.current_pair
            
            # Get responses for next round
            import requests
            import time
            
            responses = {}
            latencies = {}
            
            ollama_host = current_app.config.get('OLLAMA_HOST', 'localhost')
            ollama_port = current_app.config.get('OLLAMA_PORT', '11434')
            ollama_url = f"http://{ollama_host}:{ollama_port}/v1/chat/completions"
            
            for model_key, model_name in [('a', next_model_a), ('b', next_model_b)]:
                try:
                    start = time.time()
                    ollama_response = requests.post(
                        ollama_url,
                        json={
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": arena_system_prompt},
                                {"role": "user", "content": battle.user_message}
                            ],
                            "max_tokens": 500
                        },
                        timeout=60
                    )
                    
                    if ollama_response.status_code == 200:
                        responses[model_key] = ollama_response.json()['choices'][0]['message']['content']
                    else:
                        responses[model_key] = f"Error from model: {ollama_response.status_code}"
                    
                    latencies[model_key] = (time.time() - start) * 1000
                except Exception as e:
                    logger.error(f"Error calling model {model_key}: {e}")
                    responses[model_key] = f"Error: {str(e)}"
                    latencies[model_key] = 0
            
            # Store responses in battle
            battle.all_responses[next_model_a] = responses['a']
            battle.all_responses[next_model_b] = responses['b']
            battle.all_latencies[next_model_a] = latencies['a']
            battle.all_latencies[next_model_b] = latencies['b']
            
            # Save updated battle
            arena_manager.storage.update_progressive_battle(battle)
            
            # Return next matchup
            return jsonify({
                'success': True,
                'continue_battle': True,
                'round': battle.current_round,
                'model_a': next_model_a,
                'model_b': next_model_b,
                'response_a': responses['a'],
                'response_b': responses['b'],
                'latency_a': latencies['a'],
                'latency_b': latencies['b'],
                'eliminated_models': battle.eliminated_models,
                'winner_chain': battle.winner_chain,
                'remaining_models': battle.remaining_models,
                'previous_winner': winner,
                'previous_loser': loser
            })
        else:
            # Battle complete - determine final ranking
            battle.completed = True
            battle.final_ranking = battle.winner_chain + battle.eliminated_models[::-1]
            
            # Save final state
            arena_manager.storage.update_progressive_battle(battle)
            
            # Log completion
            if hasattr(current_app, 'services') and current_app.services.interaction_logger:
                current_app.services.interaction_logger.log_analysis_event(
                    session_id=session_id,
                    event_type='arena_complete',
                    details={
                        'battle_id': battle_id,
                        'final_ranking': battle.final_ranking,
                        'rounds': battle.current_round
                    },
                    success=True
                )
            
            # Return final results
            return jsonify({
                'success': True,
                'continue_battle': False,
                'final_ranking': battle.final_ranking,
                'comparison_history': battle.comparison_history,
                'message': f'Tournament complete! Ranking: {" > ".join(battle.final_ranking)}'
            })
        
    except Exception as e:
        logger.error(f"Error processing arena vote: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analysis_bp.route('/send_message_streaming', methods=['POST'])
@validate_session
@handle_errors
@log_execution_time
def send_message_streaming():
    """
    Handle chat messages with streaming response for better UX.
    """
    
    try:
        # Get the message from the request
        data = request.json
        user_message = data.get('message', '')
        
        # DEBUG LOGGING
        logger.info("="*60)
        logger.info("🔧 BACKEND: /send_message_streaming endpoint hit")
        logger.info(f"  📝 User Message: {user_message[:100] if user_message else 'EMPTY'}...")
        logger.info(f"  🆔 Session ID: {session.get('session_id', 'NO SESSION')}")
        logger.info(f"  📂 Session Keys: {list(session.keys())}")
        logger.info(f"  🎯 Analysis Complete: {session.get('analysis_complete', False)}")
        logger.info(f"  📊 Data Loaded: {session.get('data_loaded', False)}")
        logger.info(f"  🔄 TPR Complete: {session.get('tpr_workflow_complete', False)}")
        logger.info("="*60)
        
        if not user_message:
            # Return streaming error for empty message
            def generate_error():
                yield json.dumps({
                    'content': 'Please provide a message to continue.',
                    'status': 'success',  # Use success status to avoid frontend error handling
                    'done': True
                })
            
            response = Response(
                (f"data: {chunk}\n\n" for chunk in generate_error()),
                mimetype='text/event-stream'
            )
            response.headers['Cache-Control'] = 'no-cache'
            response.headers['Connection'] = 'keep-alive'
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        # Get tab context from frontend
        tab_context = data.get('tab_context', 'standard-upload')
        is_data_analysis = data.get('is_data_analysis', False)
        
        # Store in session for persistence
        if is_data_analysis:
            session['active_tab'] = 'data-analysis'
            session['use_data_analysis_v3'] = True
            logger.info(f"📊 Data Analysis tab active - setting V3 mode")
        
        # Get session ID
        session_id = session.get('session_id')
        
        # Data Analysis V2 removed - will be reimplemented properly
        
        # Check for active data analysis workflow (OLD VERSION - DEPRECATED)
        if session.get('data_analysis_active', False):
            logger.info(f"Data analysis workflow active for session {session_id}, routing to data analysis handler")
            
            # OLD DATA ANALYSIS - DEPRECATED, will be removed
            # For now, just clear the flag and fall through
            session.pop('data_analysis_active', None)
            session.modified = True
            logger.warning("Old data analysis flag detected, clearing and falling through to main chat")
        
        # Check for active TPR workflow NEXT
        elif session.get('tpr_workflow_active', False):
            logger.info(f"TPR workflow active for session {session_id}, routing to TPR handler")
            
            # Import TPR workflow router
            try:
                from ...tpr_module.integration.tpr_workflow_router import TPRWorkflowRouter
                
                # Get LLM manager for intent classification
                llm_manager = None
                if hasattr(current_app, 'services') and hasattr(current_app.services, 'llm_manager'):
                    llm_manager = current_app.services.llm_manager
                
                # Create router and route the message
                router = TPRWorkflowRouter(session_id, llm_manager)
                tpr_result = router.route_message(user_message, dict(session))
                
                # Check if TPR router wants to transition to main interpreter
                if tpr_result.get('response') == '__DATA_UPLOADED__':
                    logger.info(f"TPR router requesting transition to main interpreter for __DATA_UPLOADED__")
                    # Clear TPR flags and fall through to main request interpreter
                    session.pop('tpr_workflow_active', None)
                    session.pop('tpr_session_id', None)
                    # Ensure proper flags for main workflow
                    session['csv_loaded'] = True
                    session['has_uploaded_files'] = True
                    session['analysis_complete'] = True
                    session.modified = True
                    # Set the message to trigger exploration menu
                    user_message = '__DATA_UPLOADED__'
                    # Let it fall through to normal processing
                elif tpr_result.get('status') == 'tpr_to_main_transition':
                    logger.info(f"TPR router requesting transition to main interpreter for __DATA_UPLOADED__")
                    # Clear TPR flags and fall through to main request interpreter
                    session.pop('tpr_workflow_active', None)
                    session.pop('tpr_session_id', None)
                    # Ensure proper flags for main workflow
                    session['csv_loaded'] = True
                    session['has_uploaded_files'] = True
                    session['analysis_complete'] = True
                    session.modified = True
                    # Set the message to trigger exploration menu
                    user_message = '__DATA_UPLOADED__'
                    # Let it fall through to normal processing
                else:
                    # Convert TPR result to streaming format
                    def generate_tpr():
                        yield json.dumps({
                            'content': tpr_result.get('response', ''),
                            'status': tpr_result.get('status', 'success'),
                            'visualizations': tpr_result.get('visualizations', []),
                            'tools_used': tpr_result.get('tools_used', []),
                            'workflow': tpr_result.get('workflow', 'tpr'),
                            'stage': tpr_result.get('stage'),
                            'download_links': tpr_result.get('download_links', []),  # CRITICAL: Include download links
                            'trigger_data_uploaded': tpr_result.get('trigger_data_uploaded', False),
                            'done': True
                        })
                    
                    # Return streaming response with TPR result
                    response = Response(
                        (f"data: {chunk}\n\n" for chunk in generate_tpr()), 
                        mimetype='text/event-stream'
                    )
                    response.headers['Cache-Control'] = 'no-cache'
                    response.headers['Connection'] = 'keep-alive'
                    response.headers['Access-Control-Allow-Origin'] = '*'
                    return response
                
            except Exception as e:
                logger.error(f"Error routing to TPR handler: {e}")
                # Fall through to normal processing if TPR routing fails
        
        # ARENA INTEGRATION FOR STREAMING with Intent Clarification
        logger.info(f"🎯 Intent analysis for message: '{user_message[:50]}...'")
        
        # Check if user has uploaded files
        session_folder = f"instance/uploads/{session_id}"
        has_uploaded_files = False
        has_csv = False
        has_shapefile = False
        
        if os.path.exists(session_folder):
            # Check for actual data files (not just folders)
            for f in os.listdir(session_folder):
                if not f.startswith('.'):
                    if f.endswith(('.csv', '.xlsx', '.xls')):
                        has_csv = True
                        has_uploaded_files = True
                    elif f.endswith(('.shp', '.zip')):
                        has_shapefile = True
                        has_uploaded_files = True
        
        # Sync session flags with actual file existence
        # This handles cases where files exist but session flags aren't set
        # (e.g., different worker, session reset, or direct file placement)
        if has_csv and not session.get('csv_loaded', False):
            logger.info(f"Syncing session flag: csv_loaded=True for session {session_id}")
            session['csv_loaded'] = True
            session.modified = True
        
        if has_shapefile and not session.get('shapefile_loaded', False):
            logger.info(f"Syncing session flag: shapefile_loaded=True for session {session_id}")
            session['shapefile_loaded'] = True
            session.modified = True
        
        # CRITICAL: Trust session flags after TPR transition or when analysis is complete
        # TPR workflow sets these flags but may not create files in the expected location
        if session.get('csv_loaded', False) or session.get('analysis_complete', False):
            has_uploaded_files = True
        
        # Build session context for Mistral routing
        session_context = {
            'has_uploaded_files': has_uploaded_files,
            'session_id': session_id,
            'csv_loaded': session.get('csv_loaded', False),
            'shapefile_loaded': session.get('shapefile_loaded', False),
            'analysis_complete': session.get('analysis_complete', False)
        }
        
        # Check if this is a response to a clarification prompt
        if session.get('pending_clarification'):
            # User is responding to clarification - try to route again with more context
            original_context = session['pending_clarification']
            combined_message = f"{original_context['original_message']} {user_message}"
            session.pop('pending_clarification', None)
            session.modified = True
            
            # Route the combined message
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                routing_decision = loop.run_until_complete(route_with_mistral(combined_message, session_context))
            finally:
                loop.close()
            
            # Clarification response routing done
            user_message = original_context['original_message']  # Use original message for processing
        else:
            # Get Mistral routing decision
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                routing_decision = loop.run_until_complete(route_with_mistral(user_message, session_context))
            finally:
                loop.close()
            
            # Routing decision made
            
            if routing_decision == 'needs_clarification':
                # Double-check if we really need clarification
                # Very short messages should just get responses
                if len(user_message.strip().split()) <= 3:
                    routing_decision = 'can_answer'  # Override to conversational
                else:
                    # Generate clarification prompt for streaming
                    clarification = {
                        'needs_clarification': True,
                        'clarification_type': 'intent',
                        'message': "I need more information to help you. Are you looking to:",
                        'options': [
                            {
                                'id': 'analyze_data',
                                'label': 'Analyze your uploaded data',
                                'icon': '📊',
                                'value': 'tools'
                            },
                            {
                                'id': 'general_info',
                                'label': 'Get general information',
                                'icon': '📚',
                                'value': 'arena'
                            }
                        ],
                        'original_message': user_message,
                        'session_context': session_context
                    }
                    
                    # Store context for when user responds
                    session['pending_clarification'] = {
                        'original_message': user_message,
                        'context': session_context
                    }
                    session.modified = True
                    
                    logger.info(f"Returning clarification prompt (streaming)")
                    
                    # Return as streaming response
                    def generate_clarification():
                        yield json.dumps(clarification)
                    
                    response = Response(
                        (f"data: {chunk}\n\n" for chunk in generate_clarification()),
                        mimetype='text/event-stream'
                    )
                    response.headers['Cache-Control'] = 'no-cache'
                    response.headers['Connection'] = 'keep-alive'
                    response.headers['Access-Control-Allow-Origin'] = '*'
                    return response
        
        # Route based on Mistral's decision
        use_arena = (routing_decision == 'can_answer')
        use_tools = (routing_decision == 'needs_tools')
        
        # Final routing determined
        
        # Try Arena first for simple questions
        if use_arena:
            # Attempting Arena mode for streaming
            
            # Import Arena manager, system prompt, and context manager
            from app.core.arena_manager import ArenaManager
            from app.core.arena_system_prompt import get_arena_system_prompt
            from app.core.arena_context_manager import get_arena_context_manager
            arena_manager = ArenaManager()
            
            # Get base Arena system prompt
            base_arena_prompt = get_arena_system_prompt()
            
            # Enhance with session context
            context_manager = get_arena_context_manager()
            session_context = context_manager.get_session_context(
                session_id=session_id,
                session_data=dict(session)
            )
            context_enhancement = context_manager.format_context_for_prompt(session_context)
            arena_system_prompt = base_arena_prompt + context_enhancement
            
            # Get model responses
            import asyncio
            import requests as req
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Start progressive battle tournament
                import random
                import uuid
                from app.core.arena_manager import ProgressiveBattleSession
                
                # Create progressive battle session with all 3 models
                battle_id = str(uuid.uuid4())
                all_models = list(arena_manager.available_models.keys())
                random.shuffle(all_models)  # Randomize initial order
                
                # Create progressive battle
                battle = ProgressiveBattleSession(
                    session_id=battle_id,
                    user_message=user_message,
                    all_models=all_models,
                    remaining_models=all_models.copy()
                )
                
                # Get first matchup (2 random models)
                model_a, model_b = battle.remaining_models[0], battle.remaining_models[1]
                battle.current_pair = (model_a, model_b)
                battle.current_round = 0
                
                # Store battle in arena manager
                arena_manager.store_progressive_battle(battle)
                
                # Call both models
                responses = {}
                latencies = {}
                
                # Ollama model mapping
                # FIXED: These must match exactly what ArenaManager returns
                ollama_model_map = {
                    'llama3.1:8b': 'llama3.1:8b',
                    'mistral:7b': 'mistral:7b',
                    'phi3:mini': 'phi3:mini',
                    'gemma2:9b': 'gemma2:9b',
                    'qwen2.5:7b': 'qwen2.5:7b'
                }
                
                # Get responses from both models
                for model_key, model_name in [('a', model_a), ('b', model_b)]:
                    try:
                        if model_name in ollama_model_map:
                            ollama_host = current_app.config.get('OLLAMA_HOST', 'localhost')
                            ollama_port = current_app.config.get('OLLAMA_PORT', '11434')
                            ollama_url = f"http://{ollama_host}:{ollama_port}/v1/chat/completions"
                            
                            start = time.time()
                            ollama_response = req.post(
                                ollama_url,
                                json={
                                    "model": ollama_model_map[model_name],
                                    "messages": [
                                        {"role": "system", "content": arena_system_prompt},
                                        {"role": "user", "content": user_message}
                                    ],
                                    "max_tokens": 500
                                },
                                timeout=60
                            )
                            
                            if ollama_response.status_code == 200:
                                responses[model_key] = ollama_response.json()['choices'][0]['message']['content']
                            else:
                                responses[model_key] = f"Error from model: {ollama_response.status_code}"
                            
                            latencies[model_key] = (time.time() - start) * 1000
                        else:
                            responses[model_key] = f"Model {model_name} not available"
                            latencies[model_key] = 0
                    except Exception as e:
                        logger.error(f"Error calling model {model_key}: {e}")
                        responses[model_key] = f"Error: {str(e)}"
                        latencies[model_key] = 0
                
                # Check if Arena models indicate they need tools
                tool_need_indicators = [
                    "i need to see", "upload", "provide the", "i would need",
                    "cannot analyze without", "don't have access", "no data available",
                    "please share", "i require", "unable to access", "can't see your"
                ]
                
                response_a_lower = responses.get('a', '').lower()
                response_b_lower = responses.get('b', '').lower()
                
                model_a_needs_tools = any(indicator in response_a_lower for indicator in tool_need_indicators)
                model_b_needs_tools = any(indicator in response_b_lower for indicator in tool_need_indicators)
                
                # If BOTH models say they need tools, fallback to GPT-4o
                if model_a_needs_tools and model_b_needs_tools:
                    # Arena models need tools - falling back to GPT-4o
                    loop.close()
                    
                    # Mark that we need to use tools
                    session['last_tool_used'] = True
                    session.modified = True
                    
                    # Fall through to GPT-4o
                    use_arena = False
                else:
                    # Store responses in battle session
                    battle.all_responses[model_a] = responses['a']
                    battle.all_responses[model_b] = responses['b']
                    battle.all_latencies[model_a] = latencies['a']
                    battle.all_latencies[model_b] = latencies['b']
                    
                    # Save updated battle
                    arena_manager.storage.store_progressive_battle(battle)
                    loop.close()
                    
                    # Return Arena response as streaming format
                    def generate_arena():
                        yield json.dumps({
                            'content': '',  # No streaming content, send full response
                            'arena_mode': True,
                            'battle_id': battle_id,
                            'round': 1,  # First round
                            'model_a': model_a,
                            'model_b': model_b,
                            'response_a': responses['a'],
                            'response_b': responses['b'],
                            'latency_a': latencies['a'],
                            'latency_b': latencies['b'],
                            'remaining_models': battle.remaining_models[2:],  # The third model
                            'eliminated_models': [],
                            'winner_chain': [],
                            'done': True
                        })
                    
                    response = Response(
                        (f"data: {chunk}\n\n" for chunk in generate_arena()),
                        mimetype='text/event-stream'
                    )
                    response.headers['Cache-Control'] = 'no-cache'
                    response.headers['Connection'] = 'keep-alive'
                    response.headers['Access-Control-Allow-Origin'] = '*'
                    return response
                    
            except Exception as e:
                logger.error(f"Error in Arena mode: {e}")
                loop.close()
                # Fall through to GPT-4o on error
                use_arena = False
        
        # Get Request Interpreter service (for GPT-4o fallback or when Arena not used)
        try:
            request_interpreter = current_app.services.request_interpreter
            if request_interpreter is None:
                logger.error("Request Interpreter not available")
                return jsonify({
                    'status': 'error',
                    'message': 'Request processing system not available'
                }), 500
        except Exception as e:
            logger.error(f"Error getting Request Interpreter: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Error accessing request processing system'
            }), 500
        
        # Capture Flask context and session data for use in generator
        app = current_app._get_current_object()
        # Capture session data before entering generator (avoids request context issues)
        session_data = dict(session)
        
        # Use streaming response
        def generate():
            try:
                with app.app_context():
                    logger.info(f"Processing streaming message: '{user_message[:100]}...'")
                    
                    # Use the real streaming system for proper formatting
                    logger.info("Using real streaming system with proper line break preservation")
                    
                    # Track streaming result for logging
                    final_chunk = None
                    response_content = ""
                    tools_used = []
                    
                    # Use the actual streaming method (pass data analysis flags)
                    for chunk in request_interpreter.process_message_streaming(
                        user_message, 
                        session_id, 
                        session_data,
                        is_data_analysis=is_data_analysis,
                        tab_context=tab_context
                    ):
                        # Accumulate content for logging
                        if chunk.get('content'):
                            response_content += chunk.get('content', '')
                        
                        # Track tools used
                        if chunk.get('tools_used'):
                            tools_used.extend(chunk.get('tools_used', []))
                        
                        # Track final chunk
                        if chunk.get('done'):
                            final_chunk = chunk
                            
                        chunk_json = json.dumps(chunk)
                        logger.debug(f"Sending streaming chunk: {chunk_json}")
                        yield f"data: {chunk_json}\n\n"
                    
                    # CRITICAL: Update session state after streaming completes
                    # This must happen in the request context
                    from flask import session as flask_session
                    if tools_used:
                        # Update session state based on tools used
                        if any(tool in tools_used for tool in ['run_composite_analysis', 'run_pca_analysis', 'runcompleteanalysis']):
                            flask_session['analysis_complete'] = True
                            if 'runcompleteanalysis' in tools_used:
                                flask_session['analysis_type'] = 'dual_method'
                            elif 'run_composite_analysis' in tools_used:
                                flask_session['analysis_type'] = 'composite'
                            else:
                                flask_session['analysis_type'] = 'pca'
                            # CRITICAL: Mark session as modified
                            flask_session.modified = True
                            logger.info(f"Session {session_id}: Analysis completed via streaming, session updated")
                        
                        # Clear any pending actions if analysis was run
                        if any(tool in tools_used for tool in ['run_composite_analysis', 'run_pca_analysis', 'runcompleteanalysis']):
                            flask_session.pop('pending_action', None)
                            flask_session.pop('pending_variables', None)
                            flask_session.modified = True
                    
                    # Log completion using final chunk data
                    if final_chunk:
                        tools_used = final_chunk.get('tools_used', [])
                        if any(tool in tools_used for tool in ['run_composite_analysis', 'run_pca_analysis', 'runcompleteanalysis']):
                            if 'runcompleteanalysis' in tools_used:
                                analysis_type = 'dual_method'
                            elif 'run_composite_analysis' in tools_used:
                                analysis_type = 'composite'
                            else:
                                analysis_type = 'pca'
                            logger.info(f"Session {session_id}: Analysis completed via streaming ({analysis_type})")
                        
                        # Simplified logging for streaming
                        if hasattr(app, 'services') and app.services.interaction_logger:
                            interaction_logger = app.services.interaction_logger
                            interaction_logger.log_message(
                                session_id=session_id,
                                sender='assistant',
                                content=response_content,
                                intent=final_chunk.get('intent_type', 'streaming'),
                                entities={
                                    'streaming': True,
                                    'tools_used': tools_used,
                                    'status': final_chunk.get('status', 'success')
                                }
                            )
                            
            except Exception as e:
                logger.error(f"Error in streaming processing: {e}")
                error_json = json.dumps({'content': f'Error: {str(e)}', 'status': 'error', 'done': True})
                yield f"data: {error_json}\n\n"
        
        # Return streaming response with proper headers
        response = Response(generate(), mimetype='text/event-stream')
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
        return response
    
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error in streaming endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error processing streaming message: {str(e)}'
        }), 500


# ========================================================================
# ANALYSIS UTILITY FUNCTIONS
# ========================================================================

def validate_analysis_requirements(session_state, data_handler=None):
    """
    Validate that analysis requirements are met.
    
    Args:
        session_state: Current session state
        data_handler: Data handler instance
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not session_state.get('csv_loaded', False):
        return False, 'CSV data must be loaded before running analysis'
    
    if not session_state.get('shapefile_loaded', False):
        return False, 'Shapefile data must be loaded before running analysis'
    
    if not data_handler:
        return False, 'Data handler not available'
    
    # Check if data handler has required data
    if not hasattr(data_handler, 'df') or data_handler.df is None:
        return False, 'No CSV data found in data handler'
    
    if not hasattr(data_handler, 'shapefile_data') or data_handler.shapefile_data is None:
        return False, 'No shapefile data found in data handler'
    
    return True, ''


def get_analysis_status(session_state, data_handler=None):
    """
    Get current analysis status and progress.
    
    Args:
        session_state: Current session state
        data_handler: Data handler instance
        
    Returns:
        dict: Analysis status information
    """
    status = {
        'csv_loaded': session_state.get('csv_loaded', False),
        'shapefile_loaded': session_state.get('shapefile_loaded', False),
        'analysis_complete': session_state.get('analysis_complete', False),
        'variables_used': session_state.get('variables_used', []),
        'analysis_type': session_state.get('analysis_type', 'none'),
        'can_run_analysis': False,
        'can_view_results': False
    }
    
    # Check if analysis can be run
    if status['csv_loaded'] and status['shapefile_loaded']:
        status['can_run_analysis'] = True
    
    # Check if results can be viewed
    if status['analysis_complete'] and data_handler:
        if hasattr(data_handler, 'vulnerability_rankings') and data_handler.vulnerability_rankings is not None:
            status['can_view_results'] = True
    
    return status


def extract_risk_wards(data_handler, limit=10):
    """
    Extract high, medium, and low risk wards from analysis results.
    
    Args:
        data_handler: Data handler with analysis results
        limit: Maximum number of wards to return per category
        
    Returns:
        dict: Dictionary with high_risk, medium_risk, and low_risk ward lists
    """
    risk_wards = {
        'high_risk': [],
        'medium_risk': [],
        'low_risk': []
    }
    
    if not data_handler or not hasattr(data_handler, 'vulnerability_rankings'):
        return risk_wards
    
    rankings = data_handler.vulnerability_rankings
    if rankings is None or 'vulnerability_category' not in rankings.columns:
        return risk_wards
    
    try:
        if 'WardName' in rankings.columns:
            risk_wards['high_risk'] = rankings[
                rankings['vulnerability_category'] == 'High'
            ]['WardName'].tolist()[:limit]
            
            risk_wards['medium_risk'] = rankings[
                rankings['vulnerability_category'] == 'Medium'
            ]['WardName'].tolist()[:limit]
            
            risk_wards['low_risk'] = rankings[
                rankings['vulnerability_category'] == 'Low'
            ]['WardName'].tolist()[:limit]
            
    except Exception as e:
        logger.error(f"Error extracting risk wards: {e}")
    
    return risk_wards


def update_analysis_session_state(session, analysis_result):
    """
    Update session state based on analysis results.
    
    Args:
        session: Flask session object
        analysis_result: Analysis result dictionary
    """
    if analysis_result.get('status') == 'success':
        session['analysis_complete'] = True
        session['variables_used'] = analysis_result.get('variables_used', [])
        
        # Set analysis type if provided
        if 'analysis_type' in analysis_result:
            session['analysis_type'] = analysis_result['analysis_type']
            
        # CRITICAL: Mark session as modified for filesystem sessions
        session.modified = True
        
        # Clear any pending actions
        session.pop('pending_action', None)
        session.pop('pending_variables', None)
        
        # Update timestamp
        session['analysis_completion_time'] = datetime.utcnow().isoformat()
        
        logger.info(f"Session {session.get('session_id')}: Analysis completed with {len(session['variables_used'])} variables")


def clear_analysis_session_state(session):
    """
    Clear analysis-related session state.
    
    Args:
        session: Flask session object
    """
    # Clear analysis flags
    session.pop('analysis_complete', None)
    session.pop('variables_used', None)
    session.pop('analysis_type', None)
    session.pop('analysis_completion_time', None)
    
    # Clear pending actions
    session.pop('pending_action', None)
    session.pop('pending_variables', None)
    
    # Clear visualization state
    session.pop('last_visualization', None)
    
    # CRITICAL: Mark session as modified after clearing state
    session.modified = True
    
    logger.info(f"Session {session.get('session_id')}: Analysis state cleared") 
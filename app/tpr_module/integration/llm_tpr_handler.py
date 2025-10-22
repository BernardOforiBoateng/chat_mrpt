"""
LLM-First TPR Handler using One-Tool Pattern
Industry standard: One execution environment with LLM intelligence
"""

import os
import time
import logging
import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, Any, Optional, List
from flask import current_app, session

from ..conversation import TPRConversation
from ..sandbox import CodeSandbox, create_tpr_sandbox
from ..services.shapefile_extractor import ShapefileExtractor
from ..output.output_generator import OutputGenerator
from ..data.geopolitical_zones import get_zone_for_state, get_variables_for_zone

logger = logging.getLogger(__name__)


class LLMTPRHandler:
    """
    LLM-first TPR handler using one-tool pattern.
    No multiple tools - just one execution environment with LLM deciding everything.
    """
    
    def __init__(self, session_id: str):
        """Initialize LLM-based TPR handler."""
        print(f"\n{'='*60}")
        print(f"🚀 INITIALIZING LLM TPR HANDLER")
        print(f"{'='*60}")
        print(f"Session ID: {session_id}")
        
        self.session_id = session_id
        self.upload_dir = Path('instance/uploads') / session_id
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize LLM conversation
        llm_client = self._get_llm_client()
        if not llm_client:
            print("❌ ERROR: LLM client not available!")
            raise ValueError("LLM client required for LLM-first TPR handler")
        
        # Check which backend we're using
        backend_info = self._check_llm_backend()
        print(f"✅ LLM Backend: {backend_info}")
            
        self.conversation = TPRConversation(llm_client)
        self.sandbox = create_tpr_sandbox()
        
        # Initialize services for output
        self.shapefile_extractor = ShapefileExtractor()
        self.output_generator = OutputGenerator(session_id)
        
        # State tracking
        self.state = {
            'stage': 'initial',
            'data_path': None,
            'shapefile_path': None,
            'state_name': None,
            'tpr_results': None,
            'pending_input': None
        }
        
        print(f"✅ LLMTPRHandler initialized successfully")
        print(f"{'='*60}\n")
        logger.info(f"LLMTPRHandler initialized for session {session_id}")
    
    def _get_llm_client(self):
        """Get LLM client from app context."""
        try:
            if hasattr(current_app, 'services') and hasattr(current_app.services, 'llm_manager'):
                return current_app.services.llm_manager
        except:
            pass
        return None
    
    def _check_llm_backend(self):
        """Check which LLM backend is being used."""
        try:
            # Check if we're using vLLM
            if os.environ.get('USE_VLLM', 'false').lower() == 'true':
                vllm_url = os.environ.get('VLLM_BASE_URL', 'not set')
                vllm_model = os.environ.get('VLLM_MODEL', 'not set')
                return f"vLLM (Qwen3-8B) at {vllm_url}"
            # Check if using Ollama
            elif os.environ.get('USE_OLLAMA', 'false').lower() == 'true':
                return f"Ollama (local)"
            # Default to OpenAI
            else:
                return f"OpenAI API"
        except Exception as e:
            return f"Unknown (error: {e})"
    
    def handle_tpr_upload(self, 
                         csv_file_path: str,
                         shapefile_path: Optional[str],
                         upload_type: str,
                         detection_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle TPR file upload with LLM analysis.
        
        Args:
            csv_file_path: Path to uploaded TPR file
            shapefile_path: Optional shapefile path
            upload_type: Type of upload
            detection_info: Detection information
            
        Returns:
            Upload response with LLM analysis
        """
        try:
            # Store paths
            self.state['data_path'] = csv_file_path
            self.state['shapefile_path'] = shapefile_path
            
            # Let LLM analyze the data
            initial_response = self.conversation.handle_upload(csv_file_path)
            
            # Set session flags
            session['tpr_workflow_active'] = True
            session['tpr_session_id'] = self.session_id
            session['use_llm_tpr'] = True
            
            self.state['stage'] = 'data_loaded'
            
            return {
                'status': 'success',
                'workflow': 'tpr_llm',
                'stage': 'data_loaded',
                'response': initial_response,
                'next_step': 'I\'ve analyzed your TPR data. Ask me anything or tell me what analysis you need.'
            }
            
        except Exception as e:
            logger.error(f"Error handling TPR upload: {e}")
            return {
                'status': 'error',
                'message': f'Failed to process TPR file: {str(e)}'
            }
    
    def process_tpr_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process user message with simplified one-tool pattern.
        LLM decides everything through get_next_action.
        
        Args:
            user_message: User's message/query
            
        Returns:
            Response based on LLM's decision
        """
        try:
            print(f"\n{'='*50}")
            print(f"📝 PROCESSING TPR MESSAGE")
            print(f"User: {user_message[:100]}...")
            print(f"Current Stage: {self.state.get('stage', 'unknown')}")
            print(f"Using Backend: {self._check_llm_backend()}")
            
            # Get LLM's decision using unified method
            action = self.conversation.get_next_action(user_message, self.state)
            
            print(f"🤖 LLM Decision: {action.get('action_type', 'unknown')}")
            if action.get('thought'):
                print(f"💭 LLM Thought: {action['thought'][:200]}...")
            
            # Route based on action type
            if action.get('action_type') == 'input' or action.get('needs_input'):
                # User input needed (state selection, ward matching, etc.)
                input_data = action.get('needs_input', {})
                self.state['pending_input'] = input_data
                
                return {
                    'type': 'input_needed',
                    'status': 'waiting',
                    'prompt': input_data.get('prompt', 'Please provide input:'),
                    'input_type': input_data.get('type', 'text'),
                    'options': input_data.get('options'),
                    'data': input_data.get('data'),
                    'response': action.get('message', input_data.get('prompt'))
                }
            
            elif action.get('action_type') == 'confirm' or action.get('needs_confirmation'):
                # Confirmation needed
                return {
                    'type': 'confirmation_needed',
                    'status': 'waiting',
                    'message': action.get('confirmation_reason', 'Proceed with this operation?'),
                    'code_preview': action.get('code', '')[:500] if action.get('code') else None,
                    'response': action.get('confirmation_reason', 'Confirm to proceed')
                }
            
            elif action.get('action_type') == 'execute' or action.get('code'):
                # Execute code in sandbox
                if action.get('show_progress'):
                    logger.info(f"Progress: {action['show_progress']}")
                
                # Prepare context for sandbox
                sandbox_context = {
                    'data': self.conversation.data,
                    'df': self.conversation.data,  # Alias for convenience
                    'session_id': self.session_id,
                    'state_name': self.state.get('state_name'),
                    'upload_dir': str(self.upload_dir)
                }
                
                # Add shapefile data if available
                if self.state.get('state_name'):
                    try:
                        shapefile_gdf = self.shapefile_extractor._filter_state_data(self.state['state_name'])
                        if shapefile_gdf is not None:
                            sandbox_context['shapefile_data'] = shapefile_gdf
                    except:
                        pass
                
                # Execute the code
                result = self.sandbox.execute(action['code'], sandbox_context)
                
                # Process execution result
                processed = self.conversation.process_result(result, action.get('thought', ''))
                
                # Update state based on results
                if 'tpr' in str(result.get('output', '')).lower():
                    self.state['stage'] = 'tpr_calculated'
                    self.conversation.context['tpr_calculated'] = True
                
                # Add any message from the action
                if action.get('message'):
                    processed['response'] = action['message']
                elif processed.get('message'):
                    processed['response'] = processed['message']
                
                # Check if visualization was generated
                if processed.get('type') == 'visualization':
                    return {
                        'status': 'success',
                        'type': 'visualization',
                        'response': processed.get('response', 'Map generated successfully!'),
                        'visualization': processed.get('map_url'),
                        'data': processed.get('data')
                    }
                
                # Check for download links in output
                output = result.get('output', {})
                if isinstance(output, dict) and output.get('download_links'):
                    session['tpr_download_links'] = output['download_links']
                    self.state['stage'] = 'complete'
                    
                    return {
                        'status': 'success',
                        'stage': 'complete',
                        'response': processed.get('response', 'Analysis complete!'),
                        'download_links': output['download_links'],
                        'data': processed.get('data')
                    }
                
                return {
                    'status': 'success' if result.get('success') else 'error',
                    'response': processed.get('response', 'Operation completed'),
                    'data': processed.get('data')
                }
            
            else:
                # Just a message
                return {
                    'type': 'message',
                    'status': 'success',
                    'response': action.get('message', action.get('thought', 'Processing...'))
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'response': f'Error: {str(e)}'
            }
    
    def handle_user_input(self, user_response: str, input_type: str = None) -> Dict[str, Any]:
        """
        Handle user's response to input requests (ward matching, state selection, etc.)
        
        Args:
            user_response: User's response
            input_type: Type of input (optional, can be retrieved from state)
            
        Returns:
            Next action response
        """
        # Get input type from state if not provided
        if not input_type and self.state.get('pending_input'):
            input_type = self.state['pending_input'].get('type')
        
        # Update state based on input type
        if input_type == 'state_selection':
            self.state['state_name'] = user_response
            self.conversation.context['state_name'] = user_response
            message = f"Selected {user_response}. Now I'll analyze TPR data for this state."
            
        elif input_type == 'ward_match':
            # Store ward match decision
            if self.state.get('pending_input'):
                data = self.state['pending_input'].get('data', {})
                tpr_ward = data.get('tpr_ward')
                if tpr_ward:
                    self.conversation.context['ward_matches'][tpr_ward] = user_response
            message = "Ward match recorded. Continuing with analysis."
            
        elif input_type == 'facility_selection':
            self.conversation.context['facility_level'] = user_response
            message = f"Selected {user_response} facilities for analysis."
            
        else:
            message = f"Received your input: {user_response}"
        
        # Clear pending input
        self.state['pending_input'] = None
        
        # Continue conversation with context
        return self.process_tpr_message(message)
    
    def handle_confirmation(self, confirmed: bool) -> Dict[str, Any]:
        """
        Handle user's confirmation response.
        
        Args:
            confirmed: Whether user confirmed the action
            
        Returns:
            Next action response
        """
        if confirmed:
            # User confirmed - proceed with the action
            return self.process_tpr_message("Yes, proceed")
        else:
            # User declined
            return {
                'status': 'success',
                'response': 'Operation cancelled. What would you like to do instead?'
            }
    
    def get_tpr_status(self) -> Dict[str, Any]:
        """Get current TPR workflow status."""
        return {
            'active': self.state['stage'] not in ['complete', 'cancelled'],
            'stage': self.state['stage'],
            'has_data': self.conversation.data is not None,
            'state_selected': self.state.get('state_name'),
            'tpr_calculated': self.conversation.context.get('tpr_calculated', False),
            'pending_input': self.state.get('pending_input') is not None
        }
    
    def cancel_tpr_workflow(self) -> Dict[str, Any]:
        """Cancel the TPR workflow."""
        self.state = {'stage': 'cancelled'}
        self.conversation.context = {'stage': 'cancelled'}
        session.pop('tpr_workflow_active', None)
        session.pop('use_llm_tpr', None)
        
        return {
            'status': 'success',
            'message': 'TPR workflow cancelled'
        }
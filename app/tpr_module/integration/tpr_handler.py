"""
TPR Handler for ChatMRPT Integration.

This module handles the TPR workflow after detection, managing the conversation
flow and coordinating all TPR components.
"""

import os
import time
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from flask import current_app, session

from ..core.tpr_conversation_manager import TPRConversationManager, ConversationStage
from ..core.tpr_state_manager import TPRStateManager
from ..data.nmep_parser import NMEPParser
from ..services.state_selector import StateSelector
from ..output.output_generator import OutputGenerator

logger = logging.getLogger(__name__)

class TPRHandler:
    """Main handler for TPR workflow integration."""
    
    def __init__(self, session_id: str):
        """
        Initialize TPR handler for a session.
        
        Args:
            session_id: Session ID
        """
        self.session_id = session_id
        self.state_manager = TPRStateManager(session_id)
        
        # Initialize with LLM if available
        llm_client = self._get_llm_client()
        self.conversation_manager = TPRConversationManager(
            self.state_manager,
            llm_client=llm_client
        )
        
        # Initialize services
        self.nmep_parser = NMEPParser()
        self.state_selector = StateSelector()
        self.output_generator = OutputGenerator(session_id)
        
        # Restore parsed data if available
        self._restore_parsed_data()
        
        logger.info(f"TPRHandler initialized for session {session_id}")
    
    def _restore_parsed_data(self):
        """Restore parsed data from state manager."""
        try:
            state = self.state_manager.get_state()
            if state.get('nmep_data') is not None:
                # Restore data to parser
                self.nmep_parser.data = state['nmep_data']
                logger.info(f"Restored {len(self.nmep_parser.data)} rows of NMEP data")
                
                # CRITICAL: Also restore data to conversation manager's parser!
                self.conversation_manager.parser.data = state['nmep_data']
                logger.info(f"Restored data to conversation manager parser")
                
                # Restore to conversation manager
                self.conversation_manager.parsed_data = state.get('parsed_data')
                self.conversation_manager.selected_state = state.get('selected_state')
                self.conversation_manager.selected_facility_level = state.get('selected_facility_level')
                
                # Set the conversation stage
                stage_map = {
                    'state_selection': ConversationStage.STATE_SELECTION,
                    'facility_selection': ConversationStage.FACILITY_SELECTION,
                    'age_selection': ConversationStage.AGE_GROUP_SELECTION,
                    'calculation': ConversationStage.CALCULATION
                }
                workflow_stage = state.get('workflow_stage', 'state_selection')
                if workflow_stage in stage_map:
                    self.conversation_manager.current_stage = stage_map[workflow_stage]
                
        except Exception as e:
            logger.error(f"Error restoring parsed data: {e}")
    
    def _get_llm_client(self):
        """Get LLM client from app context if available."""
        try:
            if hasattr(current_app, 'services') and hasattr(current_app.services, 'llm_manager'):
                return current_app.services.llm_manager
        except:
            pass
        return None
    
    def handle_tpr_upload(self, 
                         csv_file_path: str,
                         shapefile_path: Optional[str],
                         upload_type: str,
                         detection_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle initial TPR file upload and setup.
        
        Args:
            csv_file_path: Path to uploaded Excel file
            shapefile_path: Path to shapefile (optional)
            upload_type: Type of upload (tpr_excel or tpr_shapefile)
            detection_info: Detection information from upload detector
            
        Returns:
            Upload handling result
        """
        try:
            # Parse the NMEP file
            parse_result = self.nmep_parser.parse_file(csv_file_path)
            
            if parse_result['status'] != 'success':
                return {
                    'status': 'error',
                    'message': f"Failed to parse TPR file: {parse_result.get('message', 'Unknown error')}"
                }
            
            # Store parsed data in state
            self.state_manager.update_state({
                'upload_type': upload_type,
                'nmep_data': parse_result['data'],
                'metadata': parse_result['metadata'],
                'shapefile_path': shapefile_path,
                'workflow_stage': 'state_selection',
                'available_states': parse_result['metadata'].get('states', [])  # Fixed: was looking for 'states_available'
            })
            
            # Set session flags
            session['tpr_workflow_active'] = True
            session['tpr_session_id'] = self.session_id
            
            # Generate initial response
            initial_response = self.conversation_manager.generate_response(
                "start", 
                {
                    'metadata': parse_result['metadata'],
                    'data': parse_result['data']  # Pass the actual data for summary generation
                }
            )
            
            # Log TPR workflow start
            if hasattr(current_app, 'services') and current_app.services.interaction_logger:
                current_app.services.interaction_logger.log_analysis_event(
                    session_id=self.session_id,
                    event_type='tpr_workflow_started',
                    details={
                        'upload_type': upload_type,
                        'file_year': parse_result['metadata'].get('year'),
                        'file_month': parse_result['metadata'].get('month'),
                        'states_count': len(parse_result['metadata'].get('states_available', [])),
                        'total_rows': len(parse_result['data'])
                    },
                    success=True
                )
            
            return {
                'status': 'success',
                'workflow': 'tpr',
                'stage': 'state_selection',
                'response': initial_response['response'],
                'available_states': parse_result['metadata'].get('states', []),  # Fixed: was looking for 'states_available'
                'metadata': {
                    'year': parse_result['metadata'].get('year'),
                    'month': parse_result['metadata'].get('month'),
                    'data_rows': len(parse_result['data'])
                },
                'next_step': 'Please select a state to analyze'
            }
            
        except Exception as e:
            logger.error(f"Error handling TPR upload: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to process TPR file: {str(e)}'
            }
    
    def process_tpr_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process a user message in the TPR workflow.
        
        Args:
            user_message: User's message
            
        Returns:
            Response with next steps
        """
        try:
            # CRITICAL: Restore parsed data before processing message
            # This ensures data is available across requests
            self._restore_parsed_data()
            
            # Get current state
            current_state = self.state_manager.get_state()
            
            # Generate response through conversation manager
            response = self.conversation_manager.process_user_input(user_message)
            
            # Check if analysis is ready to run
            if response.get('ready_for_analysis'):
                return self._run_tpr_analysis(response.get('parameters', {}))
            
            # Check if ready to generate outputs after TPR calculation
            if response.get('status') == 'ready_for_output':
                return self._generate_outputs_and_files(response)
            
            # Return conversational response
            return {
                'status': 'success',
                'workflow': 'tpr',
                'stage': current_state.get('workflow_stage', 'unknown'),
                'response': response.get('response', response.get('message', '')),
                'suggestions': response.get('suggestions', []),
                'next_step': response.get('next_step')
            }
            
        except Exception as e:
            logger.error(f"Error processing TPR message: {str(e)}")
            return {
                'status': 'error',
                'response': f'I encountered an error: {str(e)}. Please try again.'
            }
    
    def _run_tpr_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete TPR analysis.
        
        Args:
            parameters: Analysis parameters from conversation
            
        Returns:
            Analysis results
        """
        try:
            start_time = time.time()
            
            # Get current state
            state = self.state_manager.get_state()
            
            # Extract parameters
            selected_state = parameters.get('state') or state.get('selected_state')
            facility_level = parameters.get('facility_level', 'all')
            age_group = parameters.get('age_group', 'all_ages')
            
            logger.info(f"Running TPR analysis for {selected_state}")
            
            # Get state data from shapefile
            if state.get('shapefile_path'):
                # Use custom shapefile
                shapefile_path = state['shapefile_path']
            else:
                # Use master Nigerian shapefile
                shapefile_path = None
            
            # Extract state boundaries
            state_data = self.state_selector.extract_state_data(selected_state)
            
            if state_data is None or state_data.empty:
                return {
                    'status': 'error',
                    'response': f"Could not find geographic data for {selected_state}. Please ensure the shapefile contains this state."
                }
            
            # Run TPR calculation pipeline
            from ..core.tpr_pipeline import TPRPipeline
            pipeline = TPRPipeline(
                nmep_parser=self.nmep_parser,
                state_selector=self.state_selector,
                output_generator=self.output_generator
            )
            
            # Run pipeline
            pipeline_result = pipeline.run(
                nmep_data=state['nmep_data'],
                state_name=selected_state,
                state_boundaries=state_data,
                facility_level=facility_level,
                age_group=age_group,
                metadata={
                    'year': state['metadata'].get('year'),
                    'month': state['metadata'].get('month'),
                    'source_file': state['metadata'].get('filename')
                }
            )
            
            if pipeline_result['status'] != 'success':
                return {
                    'status': 'error',
                    'response': f"Analysis failed: {pipeline_result.get('message', 'Unknown error')}"
                }
            
            # Generate output files
            output_paths = pipeline_result['output_paths']
            
            # Generate TPR distribution map using existing variable distribution tool
            tpr_map_path = self._generate_tpr_map(selected_state)
            
            # Calculate analysis time
            analysis_time = time.time() - start_time
            
            # Log completion
            if hasattr(current_app, 'services') and current_app.services.interaction_logger:
                current_app.services.interaction_logger.log_analysis_event(
                    session_id=self.session_id,
                    event_type='tpr_analysis_completed',
                    details={
                        'state': selected_state,
                        'facility_level': facility_level,
                        'age_group': age_group,
                        'wards_analyzed': pipeline_result.get('wards_analyzed', 0),
                        'mean_tpr': pipeline_result.get('mean_tpr'),
                        'analysis_time': analysis_time,
                        'files_generated': len(output_paths)
                    },
                    success=True
                )
            
            # Mark workflow complete
            self.state_manager.update_state({
                'workflow_stage': 'completed',
                'analysis_results': pipeline_result,
                'output_paths': output_paths
            })
            
            # Clear TPR session flag
            session.pop('tpr_workflow_active', None)
            
            return {
                'status': 'success',
                'workflow': 'tpr',
                'stage': 'completed',
                'response': self._generate_completion_message(
                    selected_state, 
                    pipeline_result,
                    analysis_time
                ),
                'results': {
                    'state': selected_state,
                    'wards_analyzed': pipeline_result.get('wards_analyzed', 0),
                    'mean_tpr': pipeline_result.get('mean_tpr'),
                    'high_tpr_wards': pipeline_result.get('high_tpr_wards', 0),
                    'files_generated': output_paths
                },
                'download_links': self._generate_download_links(output_paths),
                'visualizations': [tpr_map_path] if tpr_map_path else [],
                'analysis_time': f"{analysis_time:.2f} seconds"
            }
            
        except Exception as e:
            logger.error(f"Error running TPR analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                'status': 'error',
                'response': f'Analysis failed: {str(e)}. Please check your data and try again.'
            }
    
    def _generate_completion_message(self, 
                                   state: str, 
                                   results: Dict[str, Any],
                                   analysis_time: float) -> str:
        """Generate a completion message for the user."""
        wards_analyzed = results.get('wards_analyzed', 0)
        mean_tpr = results.get('mean_tpr', 0)
        high_tpr_wards = results.get('high_tpr_wards', 0)
        
        message = f"""
## TPR Analysis Complete for {state}! 🎉

I've successfully analyzed the Test Positivity Rate data for **{wards_analyzed} wards** in {state}.

### Key Results:
- **Average TPR**: {mean_tpr:.1f}%
- **High TPR Wards** (>50%): {high_tpr_wards} wards
- **Analysis Time**: {analysis_time:.2f} seconds

### Generated Files:
1. **TPR Analysis CSV** - Detailed TPR calculations for each ward
2. **Main Analysis CSV** - TPR combined with environmental variables  
3. **Shapefile** - Geographic boundaries with all data

The environmental variables were selected based on {state}'s geopolitical zone, ensuring the most relevant factors for malaria risk assessment in your region.

You can download these files using the links below. The data is ready for further analysis, mapping, or integration with your existing workflows.
"""
        
        return message
    
    def _generate_download_links(self, output_paths: Dict[str, str]) -> Dict[str, str]:
        """Generate download links for output files."""
        # Return the actual file paths so they can be served correctly
        links = {}
        
        if 'tpr_analysis' in output_paths and output_paths['tpr_analysis']:
            links['tpr_analysis'] = output_paths['tpr_analysis']
            
        if 'main_analysis' in output_paths and output_paths['main_analysis']:
            links['main_analysis'] = output_paths['main_analysis']
            
        if 'shapefile' in output_paths and output_paths['shapefile']:
            links['shapefile'] = output_paths['shapefile']
            
        return links
    
    def _generate_tpr_map(self, state_name: str) -> Optional[Dict[str, Any]]:
        """
        Generate TPR distribution map using the existing variable distribution tool.
        
        Args:
            state_name: Name of the state being analyzed
            
        Returns:
            Visualization info dict or None if failed
        """
        try:
            # Import the variable distribution tool
            from app.tools.variable_distribution import VariableDistribution
            
            # Create tool instance for TPR variable
            tool = VariableDistribution(variable_name='TPR')
            
            # Execute the tool to generate the map
            result = tool.execute(self.session_id)
            
            if result.success and result.data:
                # Return visualization info in the expected format
                return {
                    'type': 'map',
                    'title': f'TPR Distribution - {state_name}',
                    'url': result.data.get('web_path'),
                    'description': f'Test Positivity Rate distribution across {state_name}'
                }
            else:
                logger.warning(f"Failed to generate TPR map: {result.message}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating TPR map: {str(e)}")
            return None
    




    def _generate_outputs_and_files(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate output files after TPR calculation completes.
        
        Args:
            response: Response from conversation manager with TPR results
            
        Returns:
            Response with file generation status and download links
        """
        try:
            # Extract data from response
            data = response.get('data', {})
            tpr_results = data.get('tpr_results', [])
            summary_stats = data.get('summary_stats', {})
            
            # Get state information
            state = self.state_manager.get_state()
            selected_state = state.get('selected_state')
            facility_level = state.get('selected_facility_level', 'All')
            age_group = state.get('selected_age_group', 'all')
            
            # Convert TPR results to DataFrame
            if isinstance(tpr_results, list):
                # If it's a list of TPRResult objects, convert to DataFrame
                tpr_df = pd.DataFrame([{
                    'WardName': result.ward_name,
                    'LGA': result.lga,  # Changed from lga_name to lga
                    'TPR': result.tpr_value,
                    'Tested': result.denominator,  # TPRResult uses denominator
                    'Positive': result.numerator,   # TPRResult uses numerator
                    'Method': result.calculation_method,
                    'DataCompleteness': result.data_completeness,
                    'FacilityCount': result.facility_count
                } for result in tpr_results])
            else:
                tpr_df = pd.DataFrame(tpr_results)
            
            # Generate outputs
            metadata = {
                'facility_level': facility_level,
                'age_group': age_group,
                'calculation_date': pd.Timestamp.now().strftime('%Y-%m-%d'),
                'summary_stats': summary_stats
            }
            
            output_paths = self.output_generator.generate_outputs(
                tpr_results=tpr_df,
                state_name=selected_state,
                metadata=metadata
            )
            
            # Generate TPR map visualization
            from ..services.tpr_visualization_service import TPRVisualizationService
            viz_service = TPRVisualizationService(self.session_id)
            
            map_path = viz_service.create_tpr_distribution_map(
                tpr_df=tpr_df,
                state_name=selected_state,
                title=f"TPR Distribution - {selected_state} ({age_group.upper()})"
            )
            
            # Create download links
            download_links = []
            
            # Add TPR analysis CSV
            if 'tpr_analysis' in output_paths:
                download_links.append({
                    'name': os.path.basename(output_paths['tpr_analysis']),
                    'path': output_paths['tpr_analysis'],
                    'type': 'TPR Analysis Data',
                    'description': 'Detailed TPR calculations by ward'
                })
            
            # Add main analysis CSV (with environmental variables)
            if 'main_analysis' in output_paths:
                download_links.append({
                    'name': os.path.basename(output_paths['main_analysis']),
                    'path': output_paths['main_analysis'],
                    'type': 'Complete Analysis',
                    'description': 'TPR data with environmental variables'
                })
            
            # Add shapefile
            if 'shapefile' in output_paths:
                download_links.append({
                    'name': f'{selected_state}_state.zip',
                    'path': output_paths['shapefile'],
                    'type': 'Shapefile',
                    'description': 'Geographic boundaries with all data'
                })
            
            # Check for valid TPR results
            if not tpr_results or len(tpr_results) == 0:
                logger.error("No TPR results generated")
                return {
                    'status': 'error',
                    'response': 'No TPR results could be calculated. Please check your data has valid test values.'
                }
            
            # Get average TPR safely
            avg_tpr = summary_stats.get('average_tpr', 0)
            if avg_tpr == 0 and summary_stats.get('total_wards', 0) > 0:
                logger.warning("Average TPR is 0 despite having wards - possible data issue")
            
            # Prepare response message
            response_message = f"""## TPR Analysis Complete! 🎉

I've successfully calculated TPR for **{selected_state}** using **{facility_level}** facilities for the **{age_group}** age group.

### Summary Results:
- **Total Wards Analyzed**: {summary_stats.get('total_wards', 0)}
- **Average TPR**: {summary_stats.get('average_tpr', 0):.1f}%
- **Highest TPR**: {summary_stats.get('max_tpr', 0):.1f}%
- **Lowest TPR**: {summary_stats.get('min_tpr', 0):.1f}%

### Generated Files:
Your analysis files are ready for download:

1. **TPR Analysis CSV** - Detailed ward-level TPR calculations
2. **Complete Analysis CSV** - TPR with environmental variables  
3. **Shapefile** - Geographic data for mapping

Your data is now ready for the next steps in malaria intervention planning! The files have been automatically prepared for risk analysis.

### Download Options:
- Visit the "Download Processed Data" tab to get your files
- All three files (TPR CSV, Complete Analysis, Shapefile) are ready
"""
            
            # Store download links in session
            session['tpr_download_links'] = download_links
            
            # Update workflow stage
            self.state_manager.update_state('workflow_stage', 'complete')
            
            # Automatically prepare for risk analysis transition
            try:
                from ..integration.risk_transition import TPRToRiskTransition
                transitioner = TPRToRiskTransition(self.session_id)
                
                # Execute transition in the background
                transition_result = transitioner.execute_transition()
                
                if transition_result['status'] == 'success':
                    logger.info(f"Successfully prepared TPR data for risk analysis - session {self.session_id}")
                else:
                    logger.warning(f"Could not prepare for risk transition: {transition_result.get('message')}")
                    
            except Exception as e:
                logger.error(f"Error preparing risk transition: {e}")
                # Don't fail the TPR completion if transition prep fails
            
            # Create visualization info for the map to display in chat
            visualization = {
                'type': 'iframe',
                'url': map_path,
                'title': f'TPR Distribution - {selected_state}',
                'height': 600
            }
            
            return {
                'status': 'success',
                'workflow': 'tpr',
                'stage': 'complete',
                'response': response_message,
                'download_links': download_links,
                'visualizations': [visualization],  # This will display the map in chat
                'next_step': 'download_or_continue',
                'risk_ready': True  # Signal that risk analysis is ready
            }
            
        except Exception as e:
            logger.error(f"Error generating outputs: {str(e)}")
            return {
                'status': 'error',
                'response': f'Error generating output files: {str(e)}. Please try again.'
            }
    
    def get_tpr_status(self) -> Dict[str, Any]:
        """Get current TPR workflow status."""
        state = self.state_manager.get_state()
        
        return {
            'active': state.get('workflow_stage') != 'completed',
            'stage': state.get('workflow_stage', 'not_started'),
            'selected_state': state.get('selected_state'),
            'parameters': {
                'facility_level': state.get('facility_level'),
                'age_group': state.get('age_group')
            },
            'available_states': state.get('available_states', [])
        }
    
    def cancel_tpr_workflow(self) -> Dict[str, Any]:
        """Cancel the current TPR workflow."""
        self.state_manager.clear_state()
        session.pop('tpr_workflow_active', None)
        
        return {
            'status': 'success',
            'message': 'TPR workflow cancelled. You can start a new analysis anytime.'
        }
    
    def is_complete(self) -> bool:
        """
        Check if TPR workflow is complete.
        
        Returns:
            bool: True if TPR analysis has been completed and files generated
        """
        state = self.state_manager.get_state()
        
        # Check for workflow completion indicators
        if state.get('workflow_stage') == 'complete':
            return True
            
        # Also check if output files exist
        output_folder = os.path.join(
            current_app.config['UPLOAD_FOLDER'], 
            self.session_id, 
            'tpr_outputs'
        )
        
        if os.path.exists(output_folder):
            # Check for required output files
            main_analysis = os.path.join(output_folder, 'main_analysis.csv')
            shapefile = os.path.join(output_folder, 'shapefile.zip')
            
            return os.path.exists(main_analysis) and os.path.exists(shapefile)
        
        return False


# Singleton instance management
_tpr_handlers = {}

def get_tpr_handler(session_id: str) -> TPRHandler:
    """Get or create TPR handler for a session."""
    if session_id not in _tpr_handlers:
        _tpr_handlers[session_id] = TPRHandler(session_id)
    return _tpr_handlers[session_id]

def cleanup_tpr_handler(session_id: str):
    """Clean up TPR handler for a session."""
    if session_id in _tpr_handlers:
        del _tpr_handlers[session_id]
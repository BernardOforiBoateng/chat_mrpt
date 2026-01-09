"""
TPR to Risk Analysis Transition Handler

Handles seamless transition from TPR analysis completion to risk analysis workflow.
Simulates standard upload process without requiring user to re-upload files.
"""

import os
import shutil
import logging
from typing import Dict, Any, Optional
from flask import session, current_app

logger = logging.getLogger(__name__)


class TPRToRiskTransition:
    """Manages transition from TPR workflow to risk analysis workflow."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.tpr_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], session_id, 'tpr_outputs')
        self.session_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], session_id)
        
    def can_transition(self) -> bool:
        """
        Check if TPR outputs are available for transition.
        
        Returns:
            bool: True if transition is possible
        """
        try:
            # Look for actual TPR output files in session folder (not tpr_outputs subfolder)
            # Files are named {state}_plus.csv and {state}_state.zip
            import glob
            
            # Find the plus.csv and state.zip files
            csv_candidates = []
            csv_candidates.extend(glob.glob(os.path.join(self.session_folder, 'raw_data.csv')))
            csv_candidates.extend(glob.glob(os.path.join(self.session_folder, '*_TPR_Analysis_*.csv')))
            csv_candidates.extend(glob.glob(os.path.join(self.session_folder, '*_plus.csv')))

            shp_candidates = []
            shp_candidates.extend(glob.glob(os.path.join(self.session_folder, 'raw_shapefile.zip')))
            shp_candidates.extend(glob.glob(os.path.join(self.session_folder, '*_state.zip')))
            
            csv_candidates = [c for c in csv_candidates if os.path.isfile(c)]
            if not csv_candidates:
                logger.warning(f"No TPR transition CSV found in {self.session_folder}")
                return False
                
            shp_candidates = [c for c in shp_candidates if os.path.isfile(c)]
            if not shp_candidates:
                logger.warning(f"No TPR transition shapefile found in {self.session_folder}")
                return False
            
            # Store the found files for later use
            self._tpr_csv = csv_candidates[0]
            self._tpr_shapefile = shp_candidates[0]
            
            logger.info(f"TPR outputs available for transition: {os.path.basename(self._tpr_csv)}, {os.path.basename(self._tpr_shapefile)}")
            return True
            
        except Exception as e:
            logger.error(f"Error checking transition availability: {e}")
            return False
    
    def prepare_files_for_risk_analysis(self) -> Dict[str, Any]:
        """
        Copy/link TPR output files to match standard upload structure.
        
        Returns:
            dict: Result with status and file information
        """
        try:
            # Check if files were found by can_transition
            if not hasattr(self, '_tpr_csv') or not hasattr(self, '_tpr_shapefile'):
                # If not found in attributes, find them again
                import glob
                csv_candidates = []
                csv_candidates.extend(glob.glob(os.path.join(self.session_folder, 'raw_data.csv')))
                csv_candidates.extend(glob.glob(os.path.join(self.session_folder, '*_TPR_Analysis_*.csv')))
                csv_candidates.extend(glob.glob(os.path.join(self.session_folder, '*_plus.csv')))

                shp_candidates = []
                shp_candidates.extend(glob.glob(os.path.join(self.session_folder, 'raw_shapefile.zip')))
                shp_candidates.extend(glob.glob(os.path.join(self.session_folder, '*_state.zip')))

                csv_candidates = [c for c in csv_candidates if os.path.isfile(c)]
                shp_candidates = [c for c in shp_candidates if os.path.isfile(c)]

                if not csv_candidates or not shp_candidates:
                    raise FileNotFoundError("TPR output files not found")

                self._tpr_csv = csv_candidates[0]
                self._tpr_shapefile = shp_candidates[0]
            
            # Target files for risk analysis (matching standard upload)
            risk_csv = os.path.join(self.session_folder, 'raw_data.csv')
            risk_shapefile = os.path.join(self.session_folder, 'raw_shapefile.zip')
            
            # Copy files (preserving TPR outputs)
            shutil.copy2(self._tpr_csv, risk_csv)
            logger.info(f"Copied {os.path.basename(self._tpr_csv)} to raw_data.csv")
            
            shutil.copy2(self._tpr_shapefile, risk_shapefile)
            logger.info(f"Copied {os.path.basename(self._tpr_shapefile)} to raw_shapefile.zip")
            
            # Get file sizes for metadata
            csv_size = os.path.getsize(risk_csv)
            shp_size = os.path.getsize(risk_shapefile)
            
            return {
                'status': 'success',
                'files_prepared': 2,
                'csv_path': risk_csv,
                'shapefile_path': risk_shapefile,
                'csv_size': csv_size,
                'shapefile_size': shp_size,
                'message': 'TPR outputs prepared for risk analysis'
            }
            
        except Exception as e:
            logger.error(f"Error preparing files for transition: {e}")
            return {
                'status': 'error',
                'message': f'Failed to prepare files: {str(e)}'
            }
    
    def setup_risk_analysis_session(self) -> Dict[str, Any]:
        """
        Configure session state to simulate standard upload completion.
        Mimics the state set by handle_full_dataset_path in upload_routes.py.
        
        Returns:
            dict: Result with session configuration details
        """
        try:
            # Mimic session state from handle_full_dataset_path
            session['upload_type'] = 'csv_shapefile'
            session['raw_data_stored'] = True
            # REMOVED: session['should_ask_analysis_permission'] = True
            # Don't set permission flag - we want to show exploration menu, not auto-run analysis
            
            # Critical flags for request interpreter
            session['csv_loaded'] = True
            session['shapefile_loaded'] = True
            session['data_loaded'] = True
            
            # Mark transition source
            session['risk_input_source'] = 'tpr_transition'
            session['risk_workflow_active'] = True
            
            # Preserve TPR context
            session['tpr_transition_complete'] = True
            session['previous_workflow'] = 'tpr'
            
            # Get TPR results if available
            tpr_results = session.get('tpr_results', {})
            if tpr_results:
                session['tpr_summary'] = {
                    'state': tpr_results.get('state'),
                    'total_wards': tpr_results.get('total_wards'),
                    'average_tpr': tpr_results.get('average_tpr')
                }
            
            # Update SessionStateManager for streaming endpoint
            try:
                from app.core.session_state import SessionStateManager
                state_manager = SessionStateManager()
                state_manager.update_state(self.session_id, {
                    # REMOVED: 'should_ask_analysis_permission': True,
                    'data_loaded': True,
                    'risk_workflow_active': True,
                    'tpr_transition_complete': True
                })
            except Exception as e:
                logger.debug(f"SessionStateManager update failed: {e}")
            
            logger.info(f"Risk analysis session configured for {self.session_id}")
            
            return {
                'status': 'success',
                'session_configured': True,
                'workflow': 'risk_analysis',
                'input_source': 'tpr_transition',
                'message': 'Session configured for risk analysis'
            }
            
        except Exception as e:
            logger.error(f"Error setting up risk session: {e}")
            return {
                'status': 'error',
                'message': f'Failed to configure session: {str(e)}'
            }
    
    def execute_transition(self) -> Dict[str, Any]:
        """
        Execute the complete transition from TPR to risk analysis.
        
        Returns:
            dict: Comprehensive result of transition process
        """
        try:
            # Step 1: Verify we can transition
            if not self.can_transition():
                return {
                    'status': 'error',
                    'message': 'TPR outputs not available for transition'
                }
            
            # Step 2: Prepare files
            file_result = self.prepare_files_for_risk_analysis()
            if file_result['status'] != 'success':
                return file_result
            
            # Step 3: Setup session
            session_result = self.setup_risk_analysis_session()
            if session_result['status'] != 'success':
                return session_result
            
            # Step 4: Generate summary (similar to upload flow)
            summary_result = self._generate_transition_summary()
            
            # Log transition event
            if hasattr(current_app, 'services') and current_app.services.interaction_logger:
                current_app.services.interaction_logger.log_analysis_event(
                    session_id=self.session_id,
                    event_type='tpr_to_risk_transition',
                    details={
                        'files_transitioned': file_result['files_prepared'],
                        'csv_size': file_result['csv_size'],
                        'shapefile_size': file_result['shapefile_size'],
                        'previous_workflow': 'tpr',
                        'new_workflow': 'risk_analysis'
                    },
                    success=True
                )
            
            return {
                'status': 'success',
                'message': 'Successfully transitioned from TPR to risk analysis',
                'files': {
                    'csv': file_result['csv_path'],
                    'shapefile': file_result['shapefile_path']
                },
                'session': session_result,
                'summary': summary_result,
                'next_step': 'Risk analysis ready to begin',
                'workflow_active': 'risk_analysis'
            }
            
        except Exception as e:
            logger.error(f"Error executing transition: {e}")
            return {
                'status': 'error',
                'message': f'Transition failed: {str(e)}'
            }
    
    def _generate_transition_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the transitioned data.
        
        Returns:
            dict: Summary information about the data
        """
        try:
            import pandas as pd
            
            # Read the transitioned CSV
            csv_path = os.path.join(self.session_folder, 'raw_data.csv')
            df = pd.read_csv(csv_path)
            
            # Extract summary info
            summary = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'has_tpr': 'TPR' in df.columns or 'tpr' in df.columns,
                'has_environmental': any(col in df.columns for col in ['rainfall', 'temperature', 'humidity', 'evi']),
                'ward_column': 'WardName' in df.columns or 'ward_name' in df.columns,
                'source': 'tpr_analysis',
                'ready_for_risk': True
            }
            
            # Add column list
            summary['columns'] = df.columns.tolist()
            
            # Get unique wards count if ward column exists
            ward_col = None
            for col in ['WardName', 'ward_name', 'Ward', 'ward']:
                if col in df.columns:
                    ward_col = col
                    break
            
            if ward_col:
                summary['unique_wards'] = df[ward_col].nunique()
            
            logger.info(f"Transition summary generated: {summary['total_rows']} rows, {summary['total_columns']} columns")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating transition summary: {e}")
            return {
                'error': str(e),
                'source': 'tpr_analysis'
            }


def transition_tpr_to_risk(session_id: str) -> Dict[str, Any]:
    """
    Convenience function to execute TPR to risk transition.
    
    Args:
        session_id: Current session ID
        
    Returns:
        dict: Transition result
    """
    transitioner = TPRToRiskTransition(session_id)
    return transitioner.execute_transition()
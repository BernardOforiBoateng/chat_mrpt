"""
TPR Upload Detector for ChatMRPT Integration.

This module detects when uploaded files are NMEP TPR files and routes them
appropriately through the TPR conversation flow.
"""

import os
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from werkzeug.datastructures import FileStorage

from ..data.nmep_parser import NMEPParser
from ..data.data_validator import DataValidator

logger = logging.getLogger(__name__)

class TPRUploadDetector:
    """Detect and handle TPR file uploads."""
    
    def __init__(self):
        """Initialize the TPR upload detector."""
        self.parser = NMEPParser()
        self.validator = DataValidator()
        logger.info("TPRUploadDetector initialized")
    
    def detect_tpr_upload(self, 
                         csv_file: Optional[FileStorage],
                         shapefile: Optional[FileStorage],
                         csv_content: Optional[bytes] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Detect if the uploaded files are TPR-related.
        
        Args:
            csv_file: Uploaded CSV/Excel file
            shapefile: Uploaded shapefile (if any)
            csv_content: Pre-read CSV content (optional)
            
        Returns:
            Tuple of (upload_type, detection_info)
            upload_type can be:
            - 'tpr_excel': NMEP TPR Excel file
            - 'tpr_shapefile': TPR Excel + Shapefile  
            - 'standard': Regular CSV/shapefile upload
        """
        detection_info = {
            'is_tpr': False,
            'file_type': None,
            'has_shapefile': shapefile is not None and shapefile.filename != '',
            'metadata': {}
        }
        
        # Check if we have a file to analyze
        if not csv_file or csv_file.filename == '':
            return 'standard', detection_info
        
        # Check file extension
        filename = csv_file.filename.lower()
        is_excel = filename.endswith(('.xlsx', '.xls'))
        
        if not is_excel:
            # Not an Excel file, likely standard CSV
            return 'standard', detection_info
        
        try:
            # Save temporarily to analyze
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                if csv_content:
                    tmp.write(csv_content)
                else:
                    csv_file.save(tmp.name)
                tmp_path = tmp.name
            
            # Try to detect TPR file
            is_tpr = self.parser.detect_tpr_file(tmp_path)
            
            if is_tpr:
                # Parse to get metadata
                parse_result = self.parser.parse_file(tmp_path)
                
                if parse_result.get('status') == 'success':
                    detection_info['is_tpr'] = True
                    detection_info['file_type'] = 'nmep_excel'
                    detection_info['metadata'] = parse_result.get('metadata', {})
                    
                    # Validate data structure
                    validation = self.validator.validate_nmep_structure(
                        parse_result.get('data')
                    )
                    detection_info['validation'] = validation
                    
                    # Determine upload type
                    if detection_info['has_shapefile']:
                        upload_type = 'tpr_shapefile'
                    else:
                        upload_type = 'tpr_excel'
                    
                    logger.info(f"TPR file detected: {filename}, type: {upload_type}")
                else:
                    # Failed to parse as TPR
                    upload_type = 'standard'
            else:
                # Not a TPR file
                upload_type = 'standard'
            
            # Clean up temp file
            os.unlink(tmp_path)
            
        except Exception as e:
            logger.error(f"Error detecting TPR upload: {str(e)}")
            upload_type = 'standard'
        
        return upload_type, detection_info
    
    def prepare_tpr_session(self, 
                           session_id: str,
                           detection_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare session for TPR workflow.
        
        Args:
            session_id: Session ID
            detection_info: Detection information from detect_tpr_upload
            
        Returns:
            Session preparation result
        """
        session_data = {
            'workflow_type': 'tpr',
            'tpr_detected': True,
            'file_metadata': detection_info.get('metadata', {}),
            'validation_status': detection_info.get('validation', {}),
            'next_step': 'state_selection',
            'conversation_state': 'awaiting_state'
        }
        
        # Extract available states from metadata if present
        if 'states_available' in detection_info.get('metadata', {}):
            session_data['available_states'] = detection_info['metadata']['states_available']
        
        return {
            'status': 'success',
            'session_data': session_data,
            'message': 'TPR file detected. Ready to start TPR analysis workflow.',
            'next_prompt': 'I see you\'ve uploaded an NMEP TPR file. Which state would you like to analyze?'
        }
    
    def get_tpr_upload_summary(self, 
                              upload_type: str,
                              detection_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate upload summary for TPR files.
        
        Args:
            upload_type: Type of upload detected
            detection_info: Detection information
            
        Returns:
            Upload summary for UI
        """
        if upload_type == 'tpr_excel':
            summary = {
                'path': 'TPR Analysis Path',
                'description': 'NMEP TPR Excel file for Test Positivity Rate calculation',
                'next_step': 'Select state and configure TPR analysis parameters',
                'features': [
                    'Test Positivity Rate calculation',
                    'Facility-level analysis',
                    'Age group filtering',
                    'Environmental variable extraction',
                    'Three output files (TPR, Main, Shapefile)'
                ]
            }
        elif upload_type == 'tpr_shapefile':
            summary = {
                'path': 'TPR + Shapefile Path',
                'description': 'NMEP TPR Excel + Custom shapefile boundaries',
                'next_step': 'Select state and configure TPR analysis with custom boundaries',
                'features': [
                    'TPR calculation with custom boundaries',
                    'Enhanced spatial analysis',
                    'All standard TPR features',
                    'Custom ward matching'
                ]
            }
        else:
            summary = {
                'path': 'Standard Analysis Path',
                'description': 'Regular data analysis workflow',
                'next_step': 'Proceed with standard analysis'
            }
        
        # Add metadata if TPR
        if detection_info.get('is_tpr'):
            metadata = detection_info.get('metadata', {})
            summary['tpr_info'] = {
                'year': metadata.get('year', 'Unknown'),
                'month': metadata.get('month', 'Unknown'),
                'states_found': len(metadata.get('states_available', [])),
                'total_rows': metadata.get('total_rows', 0)
            }
            
            # Add validation status
            validation = detection_info.get('validation', {})
            if validation.get('is_valid'):
                summary['validation_status'] = 'Valid TPR file structure'
            else:
                summary['validation_status'] = f"Issues found: {len(validation.get('issues', []))}"
        
        return summary
    
    def should_use_tpr_workflow(self, upload_type: str) -> bool:
        """
        Determine if TPR workflow should be used.
        
        Args:
            upload_type: Detected upload type
            
        Returns:
            True if TPR workflow should be used
        """
        return upload_type in ['tpr_excel', 'tpr_shapefile']


def integrate_tpr_detection(upload_type_detector):
    """
    Monkey patch the existing UploadTypeDetector to include TPR detection.
    
    This function modifies the existing upload type detection to check for
    TPR files before falling back to standard detection.
    
    Args:
        upload_type_detector: The UploadTypeDetector class to patch
    """
    # Store original method
    original_detect = upload_type_detector.detect_upload_type
    
    # Create TPR detector instance
    tpr_detector = TPRUploadDetector()
    
    def enhanced_detect_upload_type(self, files: dict, csv_content=None) -> str:
        """Enhanced upload type detection with TPR support."""
        csv_file = files.get('csv_file')
        shapefile = files.get('shapefile')
        
        # First check for TPR files
        if csv_file and csv_file.filename:
            tpr_type, tpr_info = tpr_detector.detect_tpr_upload(
                csv_file, shapefile, csv_content
            )
            
            if tpr_detector.should_use_tpr_workflow(tpr_type):
                logger.info(f"TPR workflow detected: {tpr_type}")
                # Store detection info for later use
                self._tpr_detection_info = tpr_info
                return tpr_type
        
        # Fall back to original detection
        return original_detect(self, files, csv_content)
    
    # Store original summary method
    original_get_summary = upload_type_detector.get_upload_summary
    
    def enhanced_get_upload_summary(self, upload_type: str, file_info: dict) -> dict:
        """Enhanced upload summary with TPR support."""
        # Check if this is a TPR upload
        if hasattr(self, '_tpr_detection_info') and upload_type in ['tpr_excel', 'tpr_shapefile']:
            tpr_summary = tpr_detector.get_tpr_upload_summary(
                upload_type, 
                self._tpr_detection_info
            )
            
            # Merge with file info
            return {
                'upload_type': upload_type,
                'file_info': file_info,
                **tpr_summary
            }
        
        # Fall back to original summary
        return original_get_summary(self, upload_type, file_info)
    
    # Apply patches
    upload_type_detector.detect_upload_type = enhanced_detect_upload_type
    upload_type_detector.get_upload_summary = enhanced_get_upload_summary
    
    # Add TPR detector as attribute for direct access
    upload_type_detector._tpr_detector = tpr_detector
    
    logger.info("TPR detection integrated with UploadTypeDetector")


# Helper function to check if integration is needed
def is_tpr_integration_active() -> bool:
    """Check if TPR integration is active in the current app context."""
    try:
        from flask import current_app
        return current_app.config.get('ENABLE_TPR_MODULE', True)
    except:
        return True  # Default to enabled
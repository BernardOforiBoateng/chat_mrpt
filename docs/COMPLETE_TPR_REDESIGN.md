# Complete TPR Upload System Redesign

## Current Architecture Overview

### Existing Components
1. **TPRPipeline** (`app/tpr_module/core/tpr_pipeline.py`) - Well-structured 10-step pipeline
2. **TPRHandler** - Uses the pipeline for processing
3. **LLMTPRHandler** - LLM-based conversational handler
4. **NMEPParser** - Rigid format parser (causes issues!)
5. **Frontend** - Has page refresh issue due to session verification

## Problems to Solve
1. ❌ **Page Refresh**: `window.location.reload()` when TPR workflow not detected
2. ❌ **Rigid Format**: Only accepts exact NMEP Excel format
3. ❌ **Poor Error Messages**: No guidance when format doesn't match
4. ❌ **Session Issues**: Multi-worker environment causes state problems

## New Architecture Design

### Phase 1: Quick Fix (Immediate)
Remove the refresh while we build the new system:

```javascript
// app/static/js/modules/upload/file-uploader.js
// Comment out lines 378 and 839-871

async verifyTPRSessionState() {
    // TEMPORARY: Skip verification to prevent refresh
    console.log('✅ TPR verification disabled - no refresh');
    return;
}
```

### Phase 2: New Flexible Upload System

#### A. New Flexible Parser
```python
# app/tpr_module/data/flexible_tpr_parser.py

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class FlexibleTPRParser:
    """
    Flexible TPR parser that can handle various Excel formats.
    Works alongside the existing NMEPParser for backward compatibility.
    """
    
    # Flexible column patterns
    COLUMN_PATTERNS = {
        'state': {
            'patterns': ['state', 'province', 'region', 'admin1'],
            'required': True
        },
        'lga': {
            'patterns': ['lga', 'district', 'local government', 'admin2', 'county'],
            'required': True
        },
        'ward': {
            'patterns': ['ward', 'health area', 'community', 'admin3', 'village'],
            'required': True
        },
        'facility': {
            'patterns': ['facility', 'health center', 'clinic', 'hospital', 'hf', 'health facility'],
            'required': True
        },
        'period': {
            'patterns': ['period', 'date', 'month', 'time', 'reporting period'],
            'required': True
        },
        # Test data patterns
        'tested': {
            'patterns': ['tested', 'examined', 'screened', 'test', 'total tested'],
            'required': False
        },
        'positive': {
            'patterns': ['positive', 'confirmed', 'cases', 'malaria positive'],
            'required': False
        },
        'rdt_tested': {
            'patterns': ['rdt', 'rapid diagnostic', 'rapid test', 'rdt tested'],
            'required': False
        },
        'micro_tested': {
            'patterns': ['microscopy', 'microscope', 'slide', 'micro tested'],
            'required': False
        }
    }
    
    def detect_tpr_file(self, file_path: str) -> Tuple[bool, Dict]:
        """
        Flexibly detect if file contains TPR data.
        
        Returns:
            Tuple of (is_tpr, detection_info)
        """
        try:
            # Try to read Excel file
            xl_file = pd.ExcelFile(file_path)
            
            # Check each sheet for TPR data
            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=100)
                
                # Detect columns
                detected = self._detect_columns(df)
                
                if detected['is_valid_tpr']:
                    return True, {
                        'sheet': sheet_name,
                        'columns_detected': detected['mapped_columns'],
                        'confidence': detected['confidence'],
                        'format_type': detected['format_type']
                    }
            
            # Not a TPR file, but provide helpful info
            return False, {
                'sheets_analyzed': xl_file.sheet_names,
                'reason': 'No TPR data structure detected',
                'suggestions': self._generate_format_suggestions(xl_file)
            }
            
        except Exception as e:
            logger.error(f"Error detecting TPR file: {e}")
            return False, {'error': str(e)}
    
    def _detect_columns(self, df: pd.DataFrame) -> Dict:
        """
        Intelligently detect TPR-related columns.
        """
        columns = df.columns.tolist()
        mapped = {}
        
        # Try to map each required column
        for key, config in self.COLUMN_PATTERNS.items():
            for col in columns:
                col_lower = str(col).lower().strip()
                for pattern in config['patterns']:
                    if pattern in col_lower:
                        if key not in mapped:
                            mapped[key] = []
                        mapped[key].append(col)
                        break
        
        # Check if we have minimum requirements
        has_location = all(k in mapped for k in ['state', 'lga', 'ward'])
        has_test_data = any(k in mapped for k in ['tested', 'positive', 'rdt_tested', 'micro_tested'])
        
        # Determine format type
        format_type = 'unknown'
        confidence = 0.0
        
        if 'rdt' in str(columns).lower() and 'microscopy' in str(columns).lower():
            format_type = 'nmep_standard'
            confidence = 0.9
        elif has_location and has_test_data:
            format_type = 'generic_tpr'
            confidence = 0.7
        elif has_location:
            format_type = 'location_only'
            confidence = 0.3
        
        return {
            'is_valid_tpr': has_location and has_test_data,
            'mapped_columns': mapped,
            'format_type': format_type,
            'confidence': confidence,
            'missing': self._get_missing_requirements(mapped)
        }
    
    def parse_flexible(self, file_path: str, sheet_name: str = None) -> Dict:
        """
        Parse TPR file with flexible column mapping.
        """
        try:
            # Read the file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                # Auto-detect best sheet
                xl_file = pd.ExcelFile(file_path)
                for sheet in xl_file.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet)
                    detected = self._detect_columns(df)
                    if detected['is_valid_tpr']:
                        break
            
            # Map columns to standard names
            column_mapping = self._create_column_mapping(df)
            df_mapped = df.rename(columns=column_mapping)
            
            # Standardize location names
            df_mapped = self._standardize_locations(df_mapped)
            
            # Parse dates flexibly
            df_mapped = self._parse_dates(df_mapped)
            
            # Calculate TPR if not present
            df_mapped = self._ensure_tpr_columns(df_mapped)
            
            # Extract metadata
            metadata = self._extract_metadata(df_mapped)
            
            return {
                'status': 'success',
                'data': df_mapped,
                'metadata': metadata,
                'column_mapping': column_mapping,
                'format_detected': 'flexible'
            }
            
        except Exception as e:
            logger.error(f"Error parsing flexible TPR: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _create_column_mapping(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Create mapping from detected columns to standard names.
        """
        detected = self._detect_columns(df)
        mapping = {}
        
        # Map detected columns to standard names
        standard_names = {
            'state': 'state',
            'lga': 'lga',
            'ward': 'ward',
            'facility': 'facility',
            'period': 'period',
            'tested': 'total_tested',
            'positive': 'total_positive',
            'rdt_tested': 'rdt_tested',
            'micro_tested': 'micro_tested'
        }
        
        for key, cols in detected['mapped_columns'].items():
            if cols and key in standard_names:
                # Use the first matched column
                mapping[cols[0]] = standard_names[key]
        
        return mapping
    
    def _standardize_locations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize location names (remove prefixes, clean formatting).
        """
        if 'state' in df.columns:
            df['State_clean'] = df['state'].apply(lambda x: 
                str(x).upper().replace(' STATE', '').strip() if pd.notna(x) else '')
        
        if 'ward' in df.columns:
            df['WardName'] = df['ward'].apply(lambda x: 
                str(x).strip() if pd.notna(x) else '')
        
        if 'lga' in df.columns:
            df['LGA'] = df['lga'].apply(lambda x: 
                str(x).strip() if pd.notna(x) else '')
        
        return df
    
    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Flexibly parse date columns.
        """
        date_columns = ['period', 'date', 'month', 'reporting_period']
        
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass
        
        return df
    
    def _ensure_tpr_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure TPR calculation columns exist.
        """
        # If we have component columns, calculate totals
        if 'rdt_tested' in df.columns and 'micro_tested' in df.columns:
            df['total_tested'] = df['rdt_tested'].fillna(0) + df['micro_tested'].fillna(0)
        
        if 'rdt_positive' in df.columns and 'micro_positive' in df.columns:
            df['total_positive'] = df['rdt_positive'].fillna(0) + df['micro_positive'].fillna(0)
        
        # Calculate TPR if we have the data
        if 'total_tested' in df.columns and 'total_positive' in df.columns:
            df['tpr'] = np.where(
                df['total_tested'] > 0,
                (df['total_positive'] / df['total_tested']) * 100,
                0
            )
        
        return df
    
    def _extract_metadata(self, df: pd.DataFrame) -> Dict:
        """
        Extract metadata from parsed data.
        """
        metadata = {}
        
        # Get unique states
        if 'State_clean' in df.columns:
            metadata['states_available'] = df['State_clean'].dropna().unique().tolist()
        elif 'state' in df.columns:
            metadata['states_available'] = df['state'].dropna().unique().tolist()
        
        # Get time range
        for col in ['period', 'date', 'month']:
            if col in df.columns and pd.api.types.is_datetime64_any_dtype(df[col]):
                metadata['time_range'] = {
                    'start': df[col].min().isoformat() if pd.notna(df[col].min()) else None,
                    'end': df[col].max().isoformat() if pd.notna(df[col].max()) else None
                }
                break
        
        # Count facilities
        if 'facility' in df.columns:
            metadata['facility_count'] = df['facility'].nunique()
        
        # Data quality metrics
        metadata['row_count'] = len(df)
        metadata['completeness'] = {
            col: f"{df[col].notna().sum() / len(df) * 100:.1f}%"
            for col in ['state', 'lga', 'ward', 'facility'] if col in df.columns
        }
        
        return metadata
    
    def _generate_format_suggestions(self, xl_file) -> List[str]:
        """
        Generate helpful suggestions for file formatting.
        """
        suggestions = []
        
        # Analyze what we found
        sheet_count = len(xl_file.sheet_names)
        
        if sheet_count == 0:
            suggestions.append("File appears to be empty")
        elif sheet_count > 10:
            suggestions.append(f"File has {sheet_count} sheets - consider consolidating data")
        
        suggestions.extend([
            "Ensure your Excel file contains:",
            "- Location columns: State, LGA, Ward, Facility",
            "- Test data: Number tested and positive for malaria",
            "- Time period: Month/Year of data",
            "Download our template for the correct format"
        ])
        
        return suggestions
```

#### B. Updated Frontend Without Refresh
```javascript
// app/static/js/modules/upload/file-uploader-v2.js

class TPRUploaderV2 {
    constructor() {
        this.init();
    }
    
    async uploadTPR() {
        const file = document.getElementById('tpr-file-upload').files[0];
        
        if (!file) {
            this.showError('Please select a file');
            return;
        }
        
        // Show progress immediately
        this.showProgress('Analyzing file format...');
        
        const formData = new FormData();
        formData.append('tpr_file', file);
        
        try {
            // Upload to new flexible endpoint
            const response = await fetch('/api/tpr/upload-flexible', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.handleSuccess(data);
            } else {
                this.handleError(data);
            }
        } catch (error) {
            this.handleError({ message: 'Network error: ' + error.message });
        }
    }
    
    handleSuccess(data) {
        // Update UI with success
        const statusDiv = document.getElementById('tpr-upload-status');
        statusDiv.innerHTML = `
            <div class="alert alert-success">
                <h5>✅ TPR File Uploaded Successfully!</h5>
                <div class="mt-3">
                    <strong>File Analysis:</strong>
                    <ul class="mt-2">
                        <li>Format: ${data.format_detected || 'Detected'}</li>
                        <li>States: ${data.states?.join(', ') || 'Processing...'}</li>
                        <li>Time Period: ${data.time_range || 'Processing...'}</li>
                        <li>Facilities: ${data.facility_count || 'Processing...'}</li>
                    </ul>
                </div>
                ${data.confidence < 0.7 ? `
                <div class="alert alert-warning mt-3">
                    <strong>Note:</strong> File format was partially recognized. 
                    Some features may be limited.
                </div>
                ` : ''}
            </div>
        `;
        
        // Start conversation flow
        this.startTPRConversation(data);
        
        // Store workflow info WITHOUT refresh
        this.storeWorkflowInfo(data);
    }
    
    handleError(error) {
        const statusDiv = document.getElementById('tpr-upload-status');
        
        let errorContent = `
            <div class="alert alert-danger">
                <h5>❌ Upload Failed</h5>
                <p class="mt-2">${error.message || 'Unable to process file'}</p>
        `;
        
        // Add format guidance if available
        if (error.format_issues) {
            errorContent += `
                <div class="mt-3">
                    <strong>Format Issues Detected:</strong>
                    <ul class="mt-2">
                        ${error.format_issues.map(issue => `<li>${issue}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Add suggestions
        if (error.suggestions) {
            errorContent += `
                <div class="mt-3">
                    <strong>Suggestions:</strong>
                    <ul class="mt-2">
                        ${error.suggestions.map(s => `<li>${s}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Add template download option
        errorContent += `
            <div class="mt-3">
                <button class="btn btn-info btn-sm" onclick="downloadTPRTemplate()">
                    <i class="fas fa-download"></i> Download Template
                </button>
                <button class="btn btn-secondary btn-sm ms-2" onclick="showTPRHelp()">
                    <i class="fas fa-question-circle"></i> Get Help
                </button>
            </div>
        </div>`;
        
        statusDiv.innerHTML = errorContent;
    }
    
    showProgress(message) {
        const statusDiv = document.getElementById('tpr-upload-status');
        statusDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="spinner-border text-primary me-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div>
                    <strong>${message}</strong>
                    <div class="progress mt-2" style="width: 200px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 100%"></div>
                    </div>
                </div>
            </div>
        `;
    }
    
    startTPRConversation(data) {
        // Add message to chat
        if (window.chatManager) {
            window.chatManager.addSystemMessage('TPR file uploaded successfully!');
            
            // Add analysis message
            const message = data.conversation_prompt || 
                `I've analyzed your TPR data file. I found ${data.states?.length || 'multiple'} states ` +
                `with data from ${data.time_range || 'multiple time periods'}. ` +
                `Which state would you like to analyze?`;
            
            window.chatManager.addAssistantMessage(message);
        }
    }
    
    storeWorkflowInfo(data) {
        // Store in localStorage for persistence
        localStorage.setItem('tpr_workflow', JSON.stringify({
            active: true,
            workflow_id: data.workflow_id,
            session_id: data.session_id,
            timestamp: new Date().toISOString()
        }));
        
        // Update session data
        if (window.SessionDataManager) {
            window.SessionDataManager.updateSessionData({
                tprLoaded: true,
                tprWorkflowId: data.workflow_id
            });
        }
        
        // Dispatch event for other components
        document.dispatchEvent(new CustomEvent('tprWorkflowStarted', {
            detail: data
        }));
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.tprUploader = new TPRUploaderV2();
    
    // Attach to upload button
    const uploadBtn = document.getElementById('upload-tpr-btn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            window.tprUploader.uploadTPR();
        });
    }
});
```

#### C. New Backend Route
```python
# app/web/routes/tpr_routes.py - Add new flexible upload endpoint

@tpr_bp.route('/upload-flexible', methods=['POST'])
@validate_session
@handle_errors
def upload_tpr_flexible():
    """
    Flexible TPR upload endpoint that handles various formats.
    """
    session_id = session.get('session_id')
    
    # Get file
    tpr_file = request.files.get('tpr_file')
    if not tpr_file:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    
    try:
        # Save temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tpr_file.save(tmp.name)
            temp_path = tmp.name
        
        # Try flexible parser first
        from ...tpr_module.data.flexible_tpr_parser import FlexibleTPRParser
        flexible_parser = FlexibleTPRParser()
        
        # Detect if it's a TPR file
        is_tpr, detection_info = flexible_parser.detect_tpr_file(temp_path)
        
        if is_tpr:
            # Parse with flexible parser
            result = flexible_parser.parse_flexible(temp_path)
            
            if result['status'] == 'success':
                # Store in session
                session['tpr_workflow_active'] = True
                session['tpr_data_path'] = temp_path
                session['tpr_format'] = 'flexible'
                session.modified = True
                
                # Generate workflow ID
                import uuid
                workflow_id = str(uuid.uuid4())
                
                # Store parsed data for pipeline
                session_folder = f"instance/uploads/{session_id}"
                os.makedirs(session_folder, exist_ok=True)
                
                # Save parsed data
                data_path = f"{session_folder}/tpr_data_{workflow_id}.pkl"
                result['data'].to_pickle(data_path)
                
                # Create state file for multi-worker access
                state_file = f"{session_folder}/tpr_state_{workflow_id}.json"
                with open(state_file, 'w') as f:
                    json.dump({
                        'active': True,
                        'workflow_id': workflow_id,
                        'format': result.get('format_detected', 'flexible'),
                        'metadata': result['metadata']
                    }, f)
                
                # Prepare response
                metadata = result['metadata']
                return jsonify({
                    'status': 'success',
                    'workflow_id': workflow_id,
                    'session_id': session_id,
                    'format_detected': result.get('format_detected', 'flexible'),
                    'confidence': detection_info.get('confidence', 1.0),
                    'states': metadata.get('states_available', []),
                    'time_range': metadata.get('time_range'),
                    'facility_count': metadata.get('facility_count'),
                    'conversation_prompt': generate_conversation_prompt(metadata)
                })
            else:
                # Parse failed
                return jsonify({
                    'status': 'error',
                    'message': result.get('message', 'Unable to parse file'),
                    'format_issues': ['File structure not compatible'],
                    'suggestions': [
                        'Ensure file contains location and test data',
                        'Check column names match expected format',
                        'Download template for reference'
                    ]
                }), 400
        else:
            # Not a TPR file - try standard NMEP parser as fallback
            from ...tpr_module.data.nmep_parser import NMEPParser
            nmep_parser = NMEPParser()
            
            if nmep_parser.is_tpr_file(temp_path):
                # It's a standard NMEP file, process normally
                # ... (existing NMEP processing code)
                pass
            else:
                # Not recognized as TPR
                return jsonify({
                    'status': 'error',
                    'message': 'File not recognized as TPR data',
                    'format_issues': detection_info.get('reason', ['Unknown format']),
                    'suggestions': detection_info.get('suggestions', [
                        'Ensure Excel file contains malaria test data',
                        'Include location columns (State, LGA, Ward)',
                        'Include test results (tested, positive)',
                        'Download our template for proper format'
                    ])
                }), 400
                
    except Exception as e:
        logger.error(f"TPR upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        # Clean up temp file if exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)

def generate_conversation_prompt(metadata):
    """Generate intelligent conversation prompt based on data."""
    states = metadata.get('states_available', [])
    time_range = metadata.get('time_range', {})
    facility_count = metadata.get('facility_count', 0)
    
    prompt = f"I've successfully analyzed your TPR data file. "
    
    if states:
        if len(states) == 1:
            prompt += f"The data contains information for {states[0]}. "
        else:
            prompt += f"I found data for {len(states)} states: {', '.join(states[:3])}"
            if len(states) > 3:
                prompt += f" and {len(states)-3} more"
            prompt += ". "
    
    if time_range and time_range.get('start'):
        prompt += f"The data covers the period from {time_range['start'][:10]} to {time_range.get('end', 'present')[:10]}. "
    
    if facility_count:
        prompt += f"There are {facility_count} facilities in the dataset. "
    
    prompt += "\n\nWhich state would you like to analyze for TPR calculations?"
    
    return prompt
```

### Phase 3: Integration with TPR Pipeline

The new system seamlessly integrates with the existing `TPRPipeline`:

```python
# app/tpr_module/integration/flexible_tpr_handler.py

class FlexibleTPRHandler:
    """
    Handler that works with both flexible and standard TPR formats.
    """
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.pipeline = TPRPipeline()
        self.flexible_parser = FlexibleTPRParser()
        self.nmep_parser = NMEPParser()
    
    def process_upload(self, file_path, format_type='auto'):
        """
        Process TPR upload with format detection.
        """
        if format_type == 'auto':
            # Auto-detect format
            is_flexible, _ = self.flexible_parser.detect_tpr_file(file_path)
            is_nmep = self.nmep_parser.is_tpr_file(file_path)
            
            if is_nmep:
                return self.process_nmep_format(file_path)
            elif is_flexible:
                return self.process_flexible_format(file_path)
            else:
                return self.handle_unknown_format(file_path)
        
        # ... processing logic
    
    def process_flexible_format(self, file_path):
        """
        Process flexible format through the pipeline.
        """
        # Parse with flexible parser
        result = self.flexible_parser.parse_flexible(file_path)
        
        if result['status'] == 'success':
            # Convert to format expected by pipeline
            data = self.convert_to_pipeline_format(result['data'])
            
            # Run through existing pipeline
            pipeline_result = self.pipeline.run(
                nmep_data=data,
                state_name=self.selected_state,
                state_boundaries=self.boundaries,
                facility_level=self.facility_level,
                age_group=self.age_group
            )
            
            return pipeline_result
        
        return result
```

## Implementation Plan

### Week 1: Quick Fix & Testing
- [ ] Deploy quick fix to remove refresh
- [ ] Test with existing NMEP files
- [ ] Monitor for session issues

### Week 2: Flexible Parser Development
- [ ] Implement FlexibleTPRParser
- [ ] Add column detection logic
- [ ] Create format conversion utilities
- [ ] Test with various Excel formats

### Week 3: Frontend Redesign
- [ ] Build new upload UI without refresh
- [ ] Add progress indicators
- [ ] Implement better error handling
- [ ] Create help documentation

### Week 4: Integration & Testing
- [ ] Integrate with TPRPipeline
- [ ] Test end-to-end workflow
- [ ] Handle edge cases
- [ ] Performance optimization

### Week 5: Deployment
- [ ] Deploy to staging
- [ ] User acceptance testing
- [ ] Fix any issues
- [ ] Deploy to production

## Benefits of New System

1. **No Page Refresh** ✅
   - Smooth AJAX-based upload
   - Better user experience
   
2. **Flexible Format Support** ✅
   - Handles various Excel structures
   - Intelligent column detection
   - Backward compatible with NMEP format
   
3. **Better Error Handling** ✅
   - Clear error messages
   - Format guidance
   - Template download option
   
4. **Improved Performance** ✅
   - No unnecessary reloads
   - Faster processing
   - Progress indicators
   
5. **Maintainability** ✅
   - Modular design
   - Clear separation of concerns
   - Well-documented code

## Testing Strategy

### Format Testing
Test with:
- Standard NMEP format ✓
- WHO malaria data format ✓
- Custom facility reports ✓
- Partially complete data ✓
- Different date formats ✓
- Various location hierarchies ✓

### Error Testing
- Missing required columns
- Empty files
- Corrupt Excel files
- Very large files (>100MB)
- Network interruptions

### Integration Testing
- Full pipeline execution
- Multi-state selection
- Age group filtering
- Facility level filtering
- Output generation

## Rollback Plan
If issues arise:
1. Keep existing system as fallback
2. Add feature flag for new uploader
3. Gradual rollout to users
4. Monitor error rates
5. Quick revert if needed
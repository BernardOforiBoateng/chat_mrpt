# New TPR Upload System Design

## Problems with Current System
1. **Rigid Format Requirements**: Expects exact NMEP Excel format with specific sheet names and columns
2. **Page Refresh Issue**: Forces reload when TPR workflow isn't detected
3. **Poor Error Handling**: No clear feedback when file format doesn't match
4. **Session State Issues**: Multi-worker environment causes state inconsistencies

## New System Architecture

### 1. Frontend Changes

#### A. Remove Page Refresh
```javascript
// file-uploader.js - NEW uploadTprFiles method
async uploadTprFiles() {
    const tprFile = this.tprFileInput?.files[0] || null;
    
    if (!tprFile) {
        this.setUploadStatus('Please select a file for TPR analysis', 'error', 'tpr');
        return;
    }
    
    // Show progress with better UX
    this.showTPRUploadProgress();
    
    try {
        const formData = new FormData();
        formData.append('tpr_file', tprFile);
        formData.append('upload_type', 'tpr_flexible'); // New flexible type
        
        const response = await fetch('/api/tpr/upload', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            this.handleTPRError(data);
            return;
        }
        
        // Handle success WITHOUT refresh
        this.handleTPRSuccess(data);
        
    } catch (error) {
        this.handleTPRError({ message: error.message });
    }
}

// New progress indicator
showTPRUploadProgress() {
    const progressHtml = `
        <div class="tpr-upload-progress">
            <div class="spinner-border text-primary" role="status">
                <span class="sr-only">Processing...</span>
            </div>
            <p>Analyzing file structure...</p>
            <div class="progress mt-2">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%"></div>
            </div>
        </div>
    `;
    this.tprUploadStatus.innerHTML = progressHtml;
}

// Better error handling
handleTPRError(error) {
    let errorMessage = error.message || 'Upload failed';
    let suggestions = '';
    
    if (error.format_issues) {
        errorMessage = 'File format not recognized as TPR data';
        suggestions = `
            <div class="mt-2">
                <strong>Expected format:</strong>
                <ul>
                    <li>Excel file with malaria test data</li>
                    <li>Columns for RDT/Microscopy tests and positives</li>
                    <li>State, LGA, Ward, and Facility information</li>
                </ul>
                <a href="#" class="btn btn-sm btn-info mt-2" onclick="showTPRTemplate()">
                    Download Template
                </a>
            </div>
        `;
    }
    
    this.tprUploadStatus.innerHTML = `
        <div class="alert alert-danger">
            <strong>Error:</strong> ${errorMessage}
            ${suggestions}
        </div>
    `;
}

// Success without refresh
handleTPRSuccess(data) {
    // Update UI to show success
    this.tprUploadStatus.innerHTML = `
        <div class="alert alert-success">
            <strong>Success!</strong> TPR file uploaded successfully
            <div class="mt-2">
                <strong>File Info:</strong>
                <ul>
                    <li>States found: ${data.states?.join(', ') || 'Processing...'}</li>
                    <li>Time period: ${data.time_range || 'Processing...'}</li>
                    <li>Facilities: ${data.facility_count || 'Processing...'}</li>
                </ul>
            </div>
        </div>
    `;
    
    // Start conversation flow in chat
    if (window.chatManager) {
        window.chatManager.addSystemMessage('TPR file uploaded successfully!');
        
        if (data.conversation_prompt) {
            window.chatManager.addAssistantMessage(data.conversation_prompt);
        } else {
            window.chatManager.addAssistantMessage(
                "I've received your TPR data file. Let me analyze the structure... " +
                "Which state would you like to analyze?"
            );
        }
    }
    
    // Update session WITHOUT refresh
    this.updateTPRSession(data.session_id, data.workflow_id);
}

// Update session properly
async updateTPRSession(sessionId, workflowId) {
    // Store in localStorage for persistence
    localStorage.setItem('tpr_workflow_active', 'true');
    localStorage.setItem('tpr_workflow_id', workflowId);
    
    // Notify other components
    document.dispatchEvent(new CustomEvent('tprWorkflowStarted', {
        detail: { sessionId, workflowId }
    }));
}
```

### 2. Backend Changes

#### A. New Flexible TPR Upload Endpoint
```python
# app/web/routes/tpr_routes.py

@tpr_bp.route('/upload', methods=['POST'])
@validate_session
@handle_errors
def upload_tpr_flexible():
    """
    Flexible TPR upload that handles various Excel formats.
    """
    session_id = session.get('session_id')
    
    # Get uploaded file
    tpr_file = request.files.get('tpr_file')
    if not tpr_file:
        return jsonify({
            'status': 'error',
            'message': 'No file provided'
        }), 400
    
    try:
        # Use flexible parser
        parser = FlexibleTPRParser()
        result = parser.parse_any_tpr_format(tpr_file)
        
        if result['status'] == 'success':
            # Activate TPR workflow
            session['tpr_workflow_active'] = True
            session['tpr_data'] = result['data_summary']
            session.modified = True
            
            # Store in file system for multi-worker access
            workflow_id = str(uuid.uuid4())
            workflow_file = f"instance/uploads/{session_id}/tpr_workflow_{workflow_id}.json"
            with open(workflow_file, 'w') as f:
                json.dump({
                    'active': True,
                    'workflow_id': workflow_id,
                    'data': result['data_summary']
                }, f)
            
            return jsonify({
                'status': 'success',
                'session_id': session_id,
                'workflow_id': workflow_id,
                'states': result.get('states', []),
                'time_range': result.get('time_range'),
                'facility_count': result.get('facility_count'),
                'conversation_prompt': result.get('prompt'),
                'format_detected': result.get('format_type')
            })
        else:
            # Provide helpful error with format guidance
            return jsonify({
                'status': 'error',
                'message': result.get('message', 'Unable to parse file'),
                'format_issues': result.get('format_issues', []),
                'suggestions': result.get('suggestions', [])
            }), 400
            
    except Exception as e:
        logger.error(f"TPR upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

#### B. Flexible Parser
```python
# app/tpr_module/data/flexible_parser.py

class FlexibleTPRParser:
    """
    Flexible parser that can handle various TPR Excel formats.
    """
    
    def parse_any_tpr_format(self, file):
        """
        Try multiple parsing strategies to handle different formats.
        """
        # Save temp file
        temp_path = self._save_temp_file(file)
        
        try:
            # Try different parsing strategies
            strategies = [
                self._parse_nmep_format,      # Original NMEP format
                self._parse_generic_tpr,      # Generic TPR with flexible columns
                self._parse_who_format,        # WHO standard format
                self._parse_custom_format      # User's custom format
            ]
            
            for strategy in strategies:
                result = strategy(temp_path)
                if result['status'] == 'success':
                    return result
            
            # If no strategy worked, analyze the file and provide guidance
            return self._analyze_and_guide(temp_path)
            
        finally:
            os.unlink(temp_path)
    
    def _parse_generic_tpr(self, file_path):
        """
        Parse generic TPR format with flexible column detection.
        """
        try:
            # Read all sheets
            xl_file = pd.ExcelFile(file_path)
            
            # Find the most likely data sheet
            data_sheet = self._find_data_sheet(xl_file)
            if not data_sheet:
                return {'status': 'error', 'message': 'No data sheet found'}
            
            df = pd.read_excel(file_path, sheet_name=data_sheet)
            
            # Flexible column detection
            columns_found = self._detect_tpr_columns(df)
            
            if not columns_found['has_minimum_required']:
                return {
                    'status': 'error',
                    'message': 'Missing required columns',
                    'format_issues': columns_found['missing']
                }
            
            # Map columns to standard names
            df_mapped = self._map_to_standard(df, columns_found['mapping'])
            
            # Extract metadata
            metadata = self._extract_flexible_metadata(df_mapped)
            
            return {
                'status': 'success',
                'data': df_mapped,
                'data_summary': metadata,
                'format_type': 'generic_tpr',
                'states': metadata.get('states', []),
                'time_range': metadata.get('time_range'),
                'facility_count': metadata.get('facility_count'),
                'prompt': self._generate_conversation_prompt(metadata)
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _detect_tpr_columns(self, df):
        """
        Intelligently detect TPR-related columns.
        """
        columns = df.columns.tolist()
        mapping = {}
        
        # Patterns to look for
        patterns = {
            'state': ['state', 'province', 'region'],
            'lga': ['lga', 'district', 'local government'],
            'ward': ['ward', 'health area', 'community'],
            'facility': ['facility', 'health center', 'clinic', 'hospital'],
            'tested': ['tested', 'examined', 'screened'],
            'positive': ['positive', 'confirmed', 'cases'],
            'rdt': ['rdt', 'rapid diagnostic', 'rapid test'],
            'microscopy': ['microscopy', 'microscope', 'slide']
        }
        
        # Find matching columns
        for col in columns:
            col_lower = col.lower()
            for key, patterns_list in patterns.items():
                if any(pattern in col_lower for pattern in patterns_list):
                    if key not in mapping:
                        mapping[key] = []
                    mapping[key].append(col)
        
        # Check minimum requirements
        has_location = any(k in mapping for k in ['state', 'lga', 'ward'])
        has_test_data = any(k in mapping for k in ['tested', 'positive'])
        
        return {
            'has_minimum_required': has_location and has_test_data,
            'mapping': mapping,
            'missing': self._get_missing_columns(mapping)
        }
    
    def _analyze_and_guide(self, file_path):
        """
        Analyze the file and provide guidance on how to format it.
        """
        try:
            xl_file = pd.ExcelFile(file_path)
            sheets = xl_file.sheet_names
            
            analysis = {
                'sheets_found': sheets,
                'column_analysis': {}
            }
            
            # Analyze each sheet
            for sheet in sheets[:3]:  # Check first 3 sheets
                df = pd.read_excel(file_path, sheet_name=sheet, nrows=10)
                analysis['column_analysis'][sheet] = {
                    'columns': df.columns.tolist(),
                    'row_count': len(df)
                }
            
            return {
                'status': 'error',
                'message': 'Unable to automatically parse file',
                'format_issues': ['File structure not recognized'],
                'suggestions': [
                    'Ensure your Excel file contains TPR/malaria test data',
                    'Include columns for: State/Region, LGA/District, Ward, Facility',
                    'Include test data: Number tested, Number positive',
                    'Consider downloading our template for proper formatting'
                ],
                'file_analysis': analysis
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'File reading error: {str(e)}'
            }
```

### 3. Benefits of New System

1. **No Page Refresh**: Smooth AJAX-based upload
2. **Flexible Format Support**: Handles various Excel formats
3. **Better Error Messages**: Clear guidance when format issues occur
4. **Progress Indicators**: Real-time feedback during upload
5. **Multi-Worker Compatible**: Uses file-based state storage
6. **Template Download**: Provides template for proper formatting
7. **Intelligent Column Detection**: Finds TPR data even with different column names

### 4. Implementation Steps

1. **Phase 1**: Remove the refresh (quick fix)
2. **Phase 2**: Implement flexible parser backend
3. **Phase 3**: Update frontend with new upload flow
4. **Phase 4**: Add progress indicators and better error handling
5. **Phase 5**: Test with various Excel formats
6. **Phase 6**: Deploy to staging/production

### 5. Backward Compatibility

The new system will still support the original NMEP format while also accepting:
- Generic TPR formats with different column names
- WHO standard malaria data formats
- Custom facility-level test data
- Various date/time formats
- Different location hierarchies (State/Province, LGA/District, etc.)
/**
 * Data Analysis Upload Handler
 * Handles file uploads for Data Analysis V3
 */

export class DataAnalysisUploader {
    constructor() {
        this.fileInput = null;
        this.uploadBtn = null;
        this.uploadStatus = null;
        this.init();
    }

    init() {
        console.log('📊 DataAnalysisUploader initializing...');
        this.initElements();
        this.setupEventListeners();
        console.log('✅ DataAnalysisUploader initialized');
    }

    initElements() {
        this.fileInput = document.getElementById('data-analysis-file');
        this.uploadBtn = document.getElementById('upload-data-analysis-btn');
        this.uploadStatus = document.getElementById('data-analysis-upload-status');
    }

    setupEventListeners() {
        if (this.uploadBtn) {
            this.uploadBtn.addEventListener('click', () => this.handleUpload());
            console.log('✅ Upload button listener attached');
        } else {
            console.warn('⚠️ Upload button not found');
        }

        if (this.fileInput) {
            this.fileInput.addEventListener('change', () => this.validateFile());
            console.log('✅ File input listener attached');
        } else {
            console.warn('⚠️ File input not found');
        }
    }

    validateFile() {
        const file = this.fileInput?.files[0];
        if (!file) {
            this.uploadBtn.disabled = true;
            return false;
        }

        // Check file type
        const validTypes = ['.csv', '.xlsx', '.xls', '.json'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!validTypes.includes(fileExt)) {
            this.showStatus('Please select a CSV, Excel, or JSON file', 'error');
            this.uploadBtn.disabled = true;
            return false;
        }

        // Check file size (max 50MB)
        const maxSize = 50 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showStatus('File size must be less than 50MB', 'error');
            this.uploadBtn.disabled = true;
            return false;
        }

        this.uploadBtn.disabled = false;
        this.showStatus('File ready to upload', 'success');
        return true;
    }

    async handleUpload() {
        const file = this.fileInput?.files[0];
        if (!file || !this.validateFile()) {
            return;
        }

        // Disable button during upload
        this.uploadBtn.disabled = true;
        this.showStatus('Uploading file...', 'info');

        try {
            // Create FormData for our dedicated data analysis upload
            const formData = new FormData();
            
            // Use 'file' as the field name for our new route
            formData.append('file', file);
            
            // Add session ID if available
            const sessionId = sessionStorage.getItem('session_id') || 
                             localStorage.getItem('session_id') || 
                             'session_' + Date.now();
            formData.append('session_id', sessionId);

            // Upload to our dedicated Data Analysis V3 endpoint
            const response = await fetch('/api/data-analysis/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.showStatus('✅ File uploaded successfully!', 'success');
                
                // Store session ID and Data Analysis mode flag
                if (result.session_id) {
                    sessionStorage.setItem('session_id', result.session_id);
                    sessionStorage.setItem('has_data_analysis_file', 'true');
                }
                
                // Close modal after short delay
                setTimeout(async () => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('uploadModal'));
                    if (modal) {
                        modal.hide();
                    }
                    
                    // Send message to chat
                    if (window.chatManager) {
                        window.chatManager.addSystemMessage(
                            `📊 Data file "${file.name}" uploaded successfully. Analyzing your data...`
                        );
                        
                        // Automatically trigger Data Analysis V3 agent
                        try {
                            const agentResponse = await fetch('/api/v1/data-analysis/chat', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    message: 'analyze uploaded data',
                                    session_id: result.session_id
                                })
                            });
                            
                            const agentResult = await agentResponse.json();
                            
                            if (agentResult.success && agentResult.message) {
                                // Display the comprehensive data summary from the agent
                                window.chatManager.addAssistantMessage(agentResult.message);
                            }
                        } catch (error) {
                            console.error('Error triggering data analysis:', error);
                        }
                    }
                }, 1500);

            } else {
                this.showStatus(`Error: ${result.error || 'Upload failed'}`, 'error');
                this.uploadBtn.disabled = false;
            }

        } catch (error) {
            console.error('Upload error:', error);
            this.showStatus('Upload failed. Please try again.', 'error');
            this.uploadBtn.disabled = false;
        }
    }

    showStatus(message, type = 'info') {
        if (!this.uploadStatus) return;

        // Set color based on type
        const colors = {
            'info': '#3498db',
            'success': '#27ae60',
            'error': '#e74c3c',
            'warning': '#f39c12'
        };

        this.uploadStatus.innerHTML = `
            <div style="padding: 10px; border-radius: 4px; background: ${colors[type]}20; color: ${colors[type]}; border: 1px solid ${colors[type]}40;">
                ${message}
            </div>
        `;
    }
}

// Initialize when DOM is ready
function initDataAnalysisUploader() {
    // Wait a bit for modal to be fully initialized
    setTimeout(() => {
        window.dataAnalysisUploader = new DataAnalysisUploader();
        console.log('📊 Data Analysis Uploader initialized');
        
        // Add tab switch listener to manage state
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const targetTab = e.target.getAttribute('data-bs-target');
                
                // If switching away from data analysis tab, clear the mode
                if (targetTab !== '#data-analysis') {
                    console.log('📊 Switching away from Data Analysis tab - clearing mode');
                    fetch('/api/data-analysis/clear-mode', { 
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    }).then(response => {
                        if (response.ok) {
                            console.log('✅ Data Analysis mode cleared');
                        }
                    }).catch(error => {
                        console.error('Error clearing Data Analysis mode:', error);
                    });
                } else {
                    console.log('📊 Data Analysis tab activated');
                    // Check if we have uploaded data
                    fetch('/api/data-analysis/status', {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    }).then(response => response.json())
                    .then(data => {
                        if (data.has_file) {
                            console.log('📊 Data Analysis has file - activating V3 mode');
                            // File exists, ensure V3 mode is active
                            fetch('/api/data-analysis/activate-mode', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                }
                            });
                        }
                    }).catch(error => {
                        console.error('Error checking Data Analysis status:', error);
                    });
                }
            });
        });
    }, 500);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDataAnalysisUploader);
} else {
    initDataAnalysisUploader();
}
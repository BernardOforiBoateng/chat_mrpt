/**
 * API Client Module
 * Handles all backend communication and HTTP requests
 */

class APIClient {
    constructor() {
        this.baseURL = '';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    /**
     * Send message to backend endpoint
     * @param {string} message - The message to send
     * @param {string} language - Language code
     * @returns {Promise<Object>} Response data
     */
    async sendMessage(message, language = 'en') {
        try {
            // Detect active tab for context
            const activeTab = document.querySelector('.tab-pane.active')?.id || 'standard-upload';
            const isDataAnalysis = activeTab === 'data-analysis';
            
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify({
                    message: message,
                    language: language,
                    tab_context: activeTab,
                    is_data_analysis: isDataAnalysis
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error sending message:', error);
            // Return error response instead of throwing to prevent global error handler cascade
            return { status: 'error', message: error.message, error: error.toString() };
        }
    }

    /**
     * Send message with streaming response (ChatGPT-like UX)
     * @param {string} message - The message to send
     * @param {string} language - Language code
     * @param {Function} onChunk - Callback for each chunk of response
     * @param {Function} onComplete - Callback when streaming completes
     * @returns {EventSource} Event source for streaming
     */
    sendMessageStreaming(message, language = 'en', onChunk, onComplete) {
        console.log('🔥 API CLIENT: sendMessageStreaming called');
        
        // FIXED: Add response buffering and better error handling
        let responseBuffer = '';
        let isComplete = false;
        let timeoutId = null;
        
        // FIXED: Add timeout protection to prevent hanging requests
        const REQUEST_TIMEOUT = 120000; // 120 seconds for analysis
        
        const cleanup = () => {
            if (timeoutId) {
                clearTimeout(timeoutId);
                timeoutId = null;
            }
            isComplete = true;
        };
        
        // FIXED: Set request timeout
        timeoutId = setTimeout(() => {
            if (!isComplete) {
                console.warn('🚨 Streaming request timed out');
                cleanup();
                if (onComplete) onComplete({ 
                    error: 'Request timed out', 
                    status: 'timeout',
                    content: responseBuffer || 'Request timed out. Please try again.'
                });
            }
        }, REQUEST_TIMEOUT);
        
        // Detect active tab for context
        const activeTab = document.querySelector('.tab-pane.active')?.id || 'standard-upload';
        const isDataAnalysis = activeTab === 'data-analysis';
        
        // Determine which endpoint to use based on Data Analysis mode
        let endpoint = '/send_message_streaming';
        let requestBody = {
            message: message,
            language: language,
            tab_context: activeTab,
            is_data_analysis: isDataAnalysis
        };
        
        // If Data Analysis tab is active AND we have a data file AND we haven't exited, use Data Analysis V3 endpoint
        if (isDataAnalysis && 
            sessionStorage.getItem('has_data_analysis_file') === 'true' && 
            sessionStorage.getItem('data_analysis_exited') !== 'true') {
            endpoint = '/api/v1/data-analysis/chat';
            requestBody = {
                message: message,
                session_id: sessionStorage.getItem('session_id') || localStorage.getItem('session_id')
            };
            console.log('📊 Routing to Data Analysis V3 endpoint');
        } else if (sessionStorage.getItem('data_analysis_exited') === 'true') {
            console.log('📊 Data Analysis exited, routing to main workflow');
            // Clear the exit flag for future sessions
            sessionStorage.removeItem('data_analysis_exited');
        }
        
        // Send the message to appropriate endpoint
        fetch(endpoint, {
            method: 'POST',
            headers: this.defaultHeaders,
            body: JSON.stringify(requestBody)
        }).then(async response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Check if this is Data Analysis V3 endpoint (returns JSON, not streaming)
            if (endpoint === '/api/v1/data-analysis/chat') {
                const result = await response.json();
                
                // Check if we need to exit Data Analysis mode
                if (result.exit_data_analysis_mode) {
                    console.log('📊 Exiting Data Analysis mode, switching to main workflow');
                    
                    // Clear Data Analysis mode flags PERMANENTLY
                    sessionStorage.removeItem('has_data_analysis_file');
                    sessionStorage.setItem('data_analysis_exited', 'true');
                    
                    // Also clear from localStorage to be sure
                    localStorage.removeItem('has_data_analysis_file');
                    
                    // Simulate tab switch to standard-upload
                    const standardTab = document.getElementById('standard-upload-tab');
                    if (standardTab) {
                        standardTab.click();
                    }
                    
                    // Show transition message
                    if (onChunk) {
                        onChunk({ content: result.message || 'Switching to main ChatMRPT workflow...' });
                    }
                    
                    cleanup();
                    if (onComplete) {
                        onComplete({
                            content: result.message || 'Switched to main workflow',
                            status: 'success',
                            redirect_message: result.redirect_message,
                            visualizations: result.visualizations,  // CRITICAL: Pass visualizations during transition
                            done: true
                        });
                    }
                    
                    // If there's a redirect message, handle it but don't send again
                    if (result.redirect_message === '__DATA_UPLOADED__') {
                        console.log('📊 Transition complete, data loaded message already shown');
                        // The transition response already contains the exploration menu
                        // Don't send __DATA_UPLOADED__ again to avoid duplicates
                    }
                    return;
                }
                
                // Normal Data Analysis V3 response - convert to streaming format
                if (onChunk) {
                    onChunk({ content: result.message || result.response || '' });
                }
                
                cleanup();
                if (onComplete) {
                    onComplete({
                        content: result.message || result.response || '',
                        status: result.success ? 'success' : 'error',
                        visualizations: result.visualizations,
                        done: true
                    });
                }
                return;
            }
            
            // Original streaming response handling for main endpoint
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            const processChunk = async () => {
                try {
                    const { done, value } = await reader.read();
                    
                    if (done || isComplete) {
                        cleanup();
                        if (!isComplete && onComplete) {
                            onComplete({ 
                                content: responseBuffer,
                                status: 'success'
                            });
                        }
                        return;
                    }
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                
                                // FIXED: Buffer all content to prevent cutoffs
                                if (data.content) {
                                    responseBuffer += data.content;
                                }
                                
                                // Pass chunk to handler
                                if (onChunk && !isComplete) {
                                    onChunk(data);
                                }
                                
                                // Check for completion
                                if (data.done) {
                                    cleanup();
                                    if (onComplete) {
                                        onComplete({
                                            ...data,
                                            content: responseBuffer,  // FIXED: Always send complete buffered content
                                            status: data.status || 'success'
                                        });
                                    }
                                    return;
                                }
                            } catch (e) {
                                console.error('Error parsing streaming chunk:', e, 'Line:', line);
                                // Continue processing other chunks even if one fails
                            }
                        }
                    }
                    
                    // Continue reading if not complete
                    if (!isComplete) {
                        processChunk();
                    }
                } catch (error) {
                    console.error('Error reading streaming chunk:', error);
                    cleanup();
                    if (onComplete) {
                        onComplete({ 
                            error: error.message, 
                            status: 'error',
                            content: responseBuffer || 'Error reading response'
                        });
                    }
                }
            };
            
            processChunk();
        }).catch(error => {
            console.error('Error with streaming message:', error);
            cleanup();
            if (onComplete) {
                onComplete({ 
                    error: error.message, 
                    status: 'error',
                    content: responseBuffer || 'Connection error. Please try again.'
                });
            }
        });
    }

    /**
     * Upload files to backend
     * @param {File|null} csvFile - CSV/Excel file
     * @param {File|null} shapeFile - Shapefile ZIP
     * @returns {Promise<Object>} Upload response
     */
    async uploadFiles(csvFile, shapeFile) {
        const formData = new FormData();
        
        if (csvFile) {
            formData.append('csv_file', csvFile);
        }
        if (shapeFile) {
            formData.append('shapefile', shapeFile);
        }

        try {
            const response = await fetch('/upload_both_files', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed with status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error uploading files:', error);
            return { status: 'error', message: error.message, error: error.toString() };
        }
    }

    /**
     * Load sample data
     * @returns {Promise<Object>} Sample data response
     */
    async loadSampleData() {
        try {
            const response = await fetch('/load_sample_data', {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify({})
            });

            if (!response.ok) {
                throw new Error(`Failed to load sample data: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading sample data:', error);
            return { status: 'error', message: error.message, error: error.toString() };
        }
    }

    /**
     * Run analysis with selected variables
     * @param {Array<string>|null} variables - Custom variables array
     * @returns {Promise<Object>} Analysis response
     */
    async runAnalysis(variables = null) {
        try {
            const response = await fetch('/run_analysis', {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify({
                    variables: variables
                })
            });

            if (!response.ok) {
                throw new Error(`Analysis failed with status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error running analysis:', error);
            return { status: 'error', message: error.message, error: error.toString() };
        }
    }

    /**
     * Generate report in specified format
     * @param {string} format - Report format (pdf, html, markdown)
     * @returns {Promise<void>} Downloads the report
     */
    async generateReport(format) {
        try {
            const response = await fetch('/generate_report', {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify({
                    format: format
                })
            });

            if (!response.ok) {
                throw new Error(`Report generation failed: ${response.status}`);
            }

            // Handle file download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `malaria_risk_report.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Error generating report:', error);
            // For report generation, we might want to show user feedback
            return { status: 'error', message: 'Failed to generate report: ' + error.message };
        }
    }

    /**
     * Request visualization with retry logic
     * @param {Object} vizInfo - Visualization information
     * @param {number} attempt - Current attempt number
     * @param {number} maxAttempts - Maximum attempts
     * @returns {Promise<Object>} Visualization response
     */
    async requestVisualization(vizInfo, attempt = 1, maxAttempts = 2) {
        try {
            const response = await fetch('/generate_visualization', {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify(vizInfo)
            });

            if (!response.ok) {
                if (attempt < maxAttempts) {
                    console.warn(`Visualization attempt ${attempt} failed, retrying...`);
                    return this.requestVisualization(vizInfo, attempt + 1, maxAttempts);
                }
                throw new Error(`Visualization failed after ${maxAttempts} attempts`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error requesting visualization:', error);
            return { status: 'error', message: error.message, error: error.toString() };
        }
    }

    /**
     * Fetch available variables for autocomplete
     * @returns {Promise<Array<string>>} Available variables
     */
    async fetchAvailableVariables() {
        try {
            const response = await fetch('/get_available_variables', {
                method: 'GET',
                headers: this.defaultHeaders
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch variables: ${response.status}`);
            }

            const data = await response.json();
            return data.variables || [];
        } catch (error) {
            console.error('Error fetching available variables:', error);
            return [];
        }
    }

    /**
     * Change language setting
     * @param {string} language - New language code
     * @returns {Promise<Object>} Language change response
     */
    async changeLanguage(language) {
        try {
            const response = await fetch('/change_language', {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify({
                    language: language
                })
            });

            if (!response.ok) {
                throw new Error(`Language change failed: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error changing language:', error);
            return { status: 'error', message: error.message, error: error.toString() };
        }
    }
}

// Create and export a singleton instance
const apiClient = new APIClient();

export default apiClient; 
/**
 * File Uploader Module
 * Handles file uploads, validation, and progress tracking
 */

import DOMHelpers from '../utils/dom-helpers.js';
import { SessionDataManager } from '../utils/storage.js';
import apiClient from '../utils/api-client.js';

export class FileUploader {
    constructor() {
        this.uploadModal = null;
        this.uploadButton = null;
        this.uploadFilesBtn = null;
        this.csvFileInput = null;
        this.shapefileInput = null;
        this.filesUploadStatus = null;
        this.useSampleDataBtn = null;
        
        this.allowedCsvTypes = ['.csv', '.xlsx', '.xls'];
        this.allowedShapefileTypes = ['.zip'];
        
        this.maxCsvSize = 50 * 1024 * 1024; // 50MB
        this.maxShapefileSize = 100 * 1024 * 1024; // 100MB
        
        this.chatManagerReady = false;
        
        this.init();
    }

    /**
     * Initialize file uploader
     */
    init() {
        console.log('📁 FileUploader initializing...');
        this.initElements();
        this.setupEventListeners();
        this.setupModal();
        
        this.waitForChatManager();
        
        console.log('✅ FileUploader initialized');
    }

    /**
     * Wait for chat manager to be ready before enabling full functionality
     */
    waitForChatManager() {
        if (window.chatManager && typeof window.chatManager.addSystemMessage === 'function') {
            this.chatManagerReady = true;
            console.log('✅ Chat manager is ready for file upload messages');
            return;
        }
        
        document.addEventListener('chatMRPTReady', () => {
            if (window.chatManager && typeof window.chatManager.addSystemMessage === 'function') {
                this.chatManagerReady = true;
                console.log('✅ Chat manager is ready for file upload messages');
            }
        });
        
        let attempts = 0;
        const checkInterval = setInterval(() => {
            attempts++;
            if (window.chatManager && typeof window.chatManager.addSystemMessage === 'function') {
                this.chatManagerReady = true;
                console.log('✅ Chat manager is ready for file upload messages (via polling)');
                clearInterval(checkInterval);
            } else if (attempts >= 20) {
                console.warn('⚠️ Chat manager not ready after 10 seconds, proceeding without chat messages');
                clearInterval(checkInterval);
            }
        }, 500);
    }

    /**
     * Initialize DOM elements
     */
    initElements() {
        this.uploadButton = DOMHelpers.getElementById('upload-button');
        this.uploadFilesBtn = DOMHelpers.getElementById('upload-files-btn');
        this.csvFileInput = DOMHelpers.getElementById('csv-upload');
        this.shapefileInput = DOMHelpers.getElementById('shapefile-upload');
        this.filesUploadStatus = DOMHelpers.getElementById('files-upload-status');
        this.useSampleDataBtn = DOMHelpers.getElementById('use-sample-data-btn-modal');
        
        // TPR upload elements
        this.uploadTprBtn = DOMHelpers.getElementById('upload-tpr-btn');
        this.tprFileInput = DOMHelpers.getElementById('tpr-file-upload');
        this.tprUploadStatus = DOMHelpers.getElementById('tpr-upload-status');

        // Initialize Bootstrap modal
        const uploadModalElem = DOMHelpers.getElementById('uploadModal');
        if (uploadModalElem && window.bootstrap) {
            this.uploadModal = new bootstrap.Modal(uploadModalElem);
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Show upload modal
        if (this.uploadButton) {
            this.uploadButton.addEventListener('click', () => {
                this.showUploadModal();
            });
        }

        // Upload files button
        if (this.uploadFilesBtn) {
            this.uploadFilesBtn.addEventListener('click', () => {
                this.uploadFiles();
            });
        }
        
        // TPR upload button
        if (this.uploadTprBtn) {
            this.uploadTprBtn.addEventListener('click', () => {
                this.uploadTprFiles();
            });
        }

        // Sample data button
        if (this.useSampleDataBtn) {
            this.useSampleDataBtn.addEventListener('click', () => {
                this.loadSampleData();
            });
        }

        // File input validation
        if (this.csvFileInput) {
            this.csvFileInput.addEventListener('change', () => {
                this.validateCsvFile();
            });
        }

        if (this.shapefileInput) {
            this.shapefileInput.addEventListener('change', () => {
                this.validateShapefileFile();
            });
        }


        // Handle sample data link in chat (using event delegation)
        DOMHelpers.addEventListenerWithDelegation('#use-sample-data-btn-initial', 'click', (e) => {
            e.preventDefault();
            this.loadSampleData();
        });
    }

    /**
     * Setup modal behavior
     */
    setupModal() {
        const uploadModalElem = DOMHelpers.getElementById('uploadModal');
        if (uploadModalElem) {
            uploadModalElem.addEventListener('shown.bs.modal', () => {
                // Focus on first input when modal opens
                if (this.csvFileInput) {
                    this.csvFileInput.focus();
                }
            });

            uploadModalElem.addEventListener('hidden.bs.modal', () => {
                // Clear status when modal closes
                this.clearUploadStatus();
            });
        }
    }

    /**
     * Show upload modal
     */
    showUploadModal() {
        if (this.uploadModal) {
            this.uploadModal.show();
        }
    }

    /**
     * Hide upload modal
     */
    hideUploadModal() {
        if (this.uploadModal) {
            this.uploadModal.hide();
        }
    }

    /**
     * Upload files to backend
     */
    async uploadFiles() {
        const csvFile = this.csvFileInput?.files[0] || null;
        const shapeFile = this.shapefileInput?.files[0] || null;

        // Validate that at least one file is selected
        if (!csvFile && !shapeFile) {
            this.setUploadStatus('Please select at least one file to upload', 'error');
            return;
        }

        // Validate file types
        if (csvFile && !this.isValidCsvFile(csvFile)) {
            this.setUploadStatus('Invalid file format. Please upload a CSV or Excel file', 'error');
            return;
        }

        if (shapeFile && !this.isValidShapefileFile(shapeFile)) {
            this.setUploadStatus('Invalid shapefile format. Please upload a ZIP file', 'error');
            return;
        }

        try {
            this.setUploadStatus('Uploading files...', 'info');
            
            const response = await apiClient.uploadFiles(csvFile, shapeFile);
            
            // Check if we have data even if status is error
            if (response.csv_result && response.csv_result.data && response.csv_result.data.length > 0) {
                response.csv_result.status = 'success';
            }
            
            if (response.status === 'success' || 
                (response.csv_result && response.csv_result.status === 'success') ||
                (response.shapefile_result && response.shapefile_result.status === 'success')) {
                this.handleUploadSuccess(response, csvFile, shapeFile);
            } else {
                let errorMessage = 'One or more file uploads failed';
                if (response.csv_result && response.csv_result.message) {
                    errorMessage = response.csv_result.message;
                } else if (response.shapefile_result && response.shapefile_result.message) {
                    errorMessage = response.shapefile_result.message;
                }
                this.handleUploadError(errorMessage);
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.handleUploadError(error.message || 'Failed to upload files');
        }
    }

    /**
     * Load sample data
     */
    async loadSampleData() {
        try {
            this.setUploadStatus('Loading sample data...', 'pending');
            this.disableUploadButton(true);

            const response = await apiClient.loadSampleData();

            if (response.status === 'success') {
                this.handleSampleDataSuccess(response);
            } else {
                this.handleUploadError(response.message || 'Failed to load sample data');
            }
        } catch (error) {
            this.handleUploadError(error.message || 'Failed to load sample data');
        } finally {
            this.disableUploadButton(false);
        }
    }

    /**
     * Handle upload success
     * @param {Object} response - Upload response
     * @param {File} csvFile - Uploaded CSV file
     * @param {File} shapeFile - Uploaded shapefile
     */
    handleUploadSuccess(response, csvFile, shapeFile) {
        this.setUploadStatus('Files uploaded successfully!', 'success');

        // Update session data
        const updates = {};
        if (csvFile) updates.csvLoaded = true;
        if (shapeFile) updates.shapefileLoaded = true;
        SessionDataManager.updateSessionData(updates);

        // Update UI status
        this.updateSessionStatus();

        // Add Phase 1 enhanced success message to chat
        this.addChatMessage(() => {
            // Show upload type detection results
            this.displayUploadResults(response, csvFile, shapeFile);
            
            // Send proactive trigger based on upload type
            this.sendProactiveMessage(response, csvFile, shapeFile);
        });

        // Close modal after delay
        setTimeout(() => {
            this.hideUploadModal();
            this.clearFileInputs();
        }, 2000);
    }

    /**
     * Upload TPR files
     */
    async uploadTprFiles() {
        const tprFile = this.tprFileInput?.files[0] || null;

        // Validate that TPR file is selected
        if (!tprFile) {
            this.setUploadStatus('Please select an NMEP Excel file for TPR analysis', 'error', 'tpr');
            return;
        }

        // Validate file type
        if (!this.validateFileType(tprFile, ['.xlsx', '.xls'])) {
            this.setUploadStatus('Invalid file type. Please upload an Excel file (.xlsx or .xls)', 'error', 'tpr');
            return;
        }

        // Validate file size
        if (!this.validateFileSize(tprFile, this.maxCsvSize)) {
            this.setUploadStatus(`TPR file size exceeds ${this.maxCsvSize / (1024 * 1024)}MB limit`, 'error', 'tpr');
            return;
        }


        // Show upload progress
        this.setUploadStatus('Uploading TPR files...', 'info', 'tpr');

        try {
            const formData = new FormData();
            formData.append('csv_file', tprFile);

            // Call API with TPR indicator
            const response = await this.callUploadAPI(formData);
            this.handleTprUploadSuccess(response, tprFile);
        } catch (error) {
            this.handleUploadError(error, 'tpr');
        }
    }

    /**
     * Handle TPR upload success
     * @param {Object} response - Upload response
     * @param {File} tprFile - TPR file uploaded
     */
    handleTprUploadSuccess(response, tprFile) {
        this.setUploadStatus('TPR file uploaded successfully! Starting analysis...', 'success', 'tpr');
        
        // Update session data for TPR
        SessionDataManager.updateSessionData({
            tprLoaded: true,
            uploadType: 'tpr'
        });

        // Update UI status
        this.updateSessionStatus();

        // Add TPR-specific message to chat (keeping existing conversation)
        this.addChatMessage(() => {
            window.chatManager.addSystemMessage('NMEP TPR file uploaded successfully!');
            
            // Show the data summary from the backend
            if (response.tpr_response) {
                window.chatManager.addAssistantMessage(response.tpr_response);
            } else if (response.message) {
                window.chatManager.addAssistantMessage(response.message);
            } else {
                // Default TPR message if none provided
                window.chatManager.addAssistantMessage(
                    "I've received your NMEP file for TPR analysis. " +
                    "I'll guide you through selecting the state, facility level, and age group for the analysis. " +
                    "Let's start by choosing which state to analyze."
                );
            }
            
            // CRITICAL: Verify TPR workflow is active in backend session (multi-worker fix)
            this.verifyTPRSessionState();
        });

        // Close modal after delay
        setTimeout(() => {
            this.hideUploadModal();
            this.clearFileInputs();
        }, 2000);
    }

    /**
     * Handle sample data success
     * @param {Object} response - Sample data response
     */
    handleSampleDataSuccess(response) {
        this.setUploadStatus('Sample data loaded successfully!', 'success');
        
        // Update session data
        SessionDataManager.updateSessionData({
            csvLoaded: true,
            shapefileLoaded: true
        });

        // Update UI status
        this.updateSessionStatus();

        // Add success message to chat - WITH IMPROVED SAFETY CHECK
        this.addChatMessage(() => {
            window.chatManager.addSystemMessage('Sample data loaded successfully!');
            
            if (response.message) {
                window.chatManager.addAssistantMessage(response.message);
            }
            
            // Send proactive trigger message to epidemiologist
            setTimeout(() => {
                window.chatManager.sendMessage("I've loaded the sample data. Can you analyze what's available and recommend what analysis to run?");
            }, 1000);
        });

        // Close modal after delay
        setTimeout(() => {
            this.hideUploadModal();
        }, 1500);
    }

    /**
     * Handle upload error
     * @param {string|Error} error - Error message or Error object
     * @param {string} target - Target upload type ('standard' or 'tpr')
     */
    handleUploadError(error, target = 'standard') {
        const errorMessage = error instanceof Error ? error.message : error;
        this.setUploadStatus(errorMessage, 'error', target);
        
        // Add error message to chat - WITH IMPROVED SAFETY CHECK
        this.addChatMessage(() => {
            window.chatManager.addSystemMessage(`Upload failed: ${errorMessage}`);
        });
    }

    /**
     * Safely add a message to chat when ready
     * @param {Function} messageFunction - Function to execute when chat manager is ready
     */
    addChatMessage(messageFunction) {
        if (this.chatManagerReady && window.chatManager && typeof window.chatManager.addSystemMessage === 'function') {
            try {
                messageFunction();
            } catch (error) {
                console.error('Error adding chat message:', error);
            }
        } else {
            console.warn('Chat manager not ready, retrying in 500ms...');
            // Retry after a short delay
            setTimeout(() => {
                if (window.chatManager && typeof window.chatManager.addSystemMessage === 'function') {
                    try {
                        messageFunction();
                    } catch (error) {
                        console.error('Error adding delayed chat message:', error);
                    }
                } else {
                    console.warn('Chat manager still not ready, message will be skipped');
                }
            }, 500);
        }
    }

    /**
     * Validate CSV file
     * @returns {boolean} Validation result
     */
    validateCsvFile() {
        const file = this.csvFileInput?.files[0];
        if (!file) return true;

        if (!this.isValidCsvFile(file)) {
            this.setUploadStatus('Invalid CSV/Excel file format', 'warning');
            return false;
        }

        this.clearUploadStatus();
        return true;
    }

    /**
     * Validate shapefile
     * @returns {boolean} Validation result
     */
    validateShapefileFile() {
        const file = this.shapefileInput?.files[0];
        if (!file) return true;

        if (!this.isValidShapefileFile(file)) {
            this.setUploadStatus('Invalid shapefile format. Please upload a ZIP file', 'warning');
            return false;
        }

        this.clearUploadStatus();
        return true;
    }

    /**
     * Validate file type
     * @param {File} file - File to validate
     * @param {Array} allowedTypes - Allowed file extensions
     * @returns {boolean} Validation result
     */
    validateFileType(file, allowedTypes) {
        const extension = this.getFileExtension(file.name);
        return allowedTypes.includes(extension);
    }

    /**
     * Validate file size
     * @param {File} file - File to validate
     * @param {number} maxSize - Maximum file size in bytes
     * @returns {boolean} Validation result
     */
    validateFileSize(file, maxSize) {
        return file.size <= maxSize;
    }

    /**
     * Check if file is valid CSV/Excel
     * @param {File} file - File to validate
     * @returns {boolean} Validation result
     */
    isValidCsvFile(file) {
        const extension = this.getFileExtension(file.name);
        const isValidType = this.allowedCsvTypes.includes(extension);
        const isValidSize = file.size <= this.maxCsvSize;
        
        return isValidType && isValidSize;
    }

    /**
     * Check if file is valid shapefile ZIP
     * @param {File} file - File to validate
     * @returns {boolean} Validation result
     */
    isValidShapefileFile(file) {
        const extension = this.getFileExtension(file.name);
        const isValidType = this.allowedShapefileTypes.includes(extension);
        const isValidSize = file.size <= this.maxShapefileSize;
        
        return isValidType && isValidSize;
    }

    /**
     * Get file extension
     * @param {string} filename - File name
     * @returns {string} File extension
     */
    getFileExtension(filename) {
        return filename.toLowerCase().substring(filename.lastIndexOf('.'));
    }

    /**
     * Set upload status message
     * @param {string} message - Status message
     * @param {string} type - Status type (success, error, warning, pending)
     */
    setUploadStatus(message, type, target = 'standard') {
        // Determine which status element to use
        const statusElement = target === 'tpr' ? this.tprUploadStatus : this.filesUploadStatus;
        
        if (!statusElement) return;

        statusElement.textContent = message;
        statusElement.className = `upload-status ${type}`;

        // Add spinner for pending status
        if (type === 'pending' || type === 'info') {
            const spinner = DOMHelpers.createElement('span', {
                className: 'spinner-border spinner-border-sm me-2'
            });
            statusElement.insertBefore(spinner, statusElement.firstChild);
        }
    }

    /**
     * Clear upload status
     */
    clearUploadStatus() {
        if (this.filesUploadStatus) {
            this.filesUploadStatus.textContent = '';
            this.filesUploadStatus.className = 'upload-status';
        }
        if (this.tprUploadStatus) {
            this.tprUploadStatus.textContent = '';
            this.tprUploadStatus.className = 'upload-status';
        }
    }

    /**
     * Disable/enable upload button
     * @param {boolean} disabled - Disable state
     */
    disableUploadButton(disabled) {
        if (this.uploadFilesBtn) {
            this.uploadFilesBtn.disabled = disabled;
        }
        if (this.useSampleDataBtn) {
            this.useSampleDataBtn.disabled = disabled;
        }
    }

    /**
     * Clear file inputs
     */
    clearFileInputs() {
        if (this.csvFileInput) {
            this.csvFileInput.value = '';
        }
        if (this.shapefileInput) {
            this.shapefileInput.value = '';
        }
        if (this.tprFileInput) {
            this.tprFileInput.value = '';
        }
        this.clearUploadStatus();
    }

    /**
     * Update session status indicator
     */
    updateSessionStatus() {
        if (window.statusIndicator) {
            window.statusIndicator.updateStatus();
        }
    }

    /**
     * Get upload progress
     * @returns {Object} Upload progress information
     */
    getUploadProgress() {
        const sessionData = SessionDataManager.getSessionData();
        return {
            csvLoaded: sessionData.csvLoaded,
            shapefileLoaded: sessionData.shapefileLoaded,
            bothLoaded: sessionData.csvLoaded && sessionData.shapefileLoaded,
            analysisReady: sessionData.csvLoaded && sessionData.shapefileLoaded
        };
    }

    /**
     * Display Phase 1 upload results in chat
     * @param {Object} response - Backend response with enhanced structure
     * @param {File} csvFile - Uploaded CSV file
     * @param {File} shapeFile - Uploaded shapefile
     */
    displayUploadResults(response, csvFile, shapeFile) {
        // 1. Basic confirmation
        window.chatManager.addSystemMessage(`Files uploaded successfully: ${csvFile.name} and ${shapeFile.name}`);

        // 2. Trigger backend to show conversational guidance
        // Send the special trigger to initiate the conversational flow
        window.chatManager.sendMessage("__DATA_UPLOADED__");
    }

    /**
     * Generate clean, readable data sample
     * @param {Array} previewRows - First 5 rows of data
     * @param {Array} columnNames - All column names  
     * @returns {string} Clean data sample
     */
    generateCleanDataSample(previewRows, columnNames) {
        if (!previewRows || previewRows.length === 0) return '';
        
        const sampleSize = Math.min(previewRows.length, 5);
        const rows = previewRows.slice(0, sampleSize);
        
        // Find the most meaningful columns dynamically
        const availableColumns = Object.keys(rows[0]);
        const keyColumns = this.selectKeyColumns(availableColumns);
        
        let sampleText = `**Data Sample** (${sampleSize} wards):\n\n`;
        
        rows.forEach((row, index) => {
            const wardName = row['WardName'] || row['ward_name'] || `Ward ${index + 1}`;
            const details = keyColumns.map(col => {
                const value = row[col];
                if (col === 'WardName' || col === 'ward_name') return null; // Skip ward name in details
                
                // Format numeric values nicely
                if (typeof value === 'number') {
                    return `${col}: ${value > 1 ? Math.round(value * 100) / 100 : (value * 100).toFixed(1)}`;
                }
                return `${col}: ${value || 'N/A'}`;
            }).filter(Boolean).join(', ');
            
            sampleText += `• **${wardName}** - ${details}\n`;
        });
        
        return sampleText;
    }

    /**
     * Select the most meaningful columns for preview
     * @param {Array} availableColumns - All available column names
     * @returns {Array} Selected key columns
     */
    selectKeyColumns(availableColumns) {
        // Priority columns in order of importance
        const priorityColumns = [
            'WardName', 'ward_name', 'Urban', 'urban', 'LGACode', 'tpr', 'housing_quality', 
            'population', 'pfpr', 'mean_rainfall', 'elevation', 'flood', 'Source'
        ];
        
        const selected = [];
        for (const col of priorityColumns) {
            if (availableColumns.includes(col) && selected.length < 4) {
                selected.push(col);
            }
        }
        
        // If we don't have enough, add some others
        if (selected.length < 3) {
            const remaining = availableColumns.filter(col => !selected.includes(col)).slice(0, 3);
            selected.push(...remaining);
        }
        
        return selected;
    }

    /**
     * Generate completeness information with missing variables
     * @param {Object} completenessData - Data completeness object
     * @returns {string} Completeness information
     */
    generateCompletenessInfo(completenessData) {
        if (!completenessData) return 'Your data appears complete with excellent quality.';
        
        const overall = completenessData.overall || 100;
        const byColumn = completenessData.by_column || {};
        
        // Find variables with missing data
        const missingVars = Object.entries(byColumn)
            .filter(([, completeness]) => completeness < 100)
            .sort(([, a], [, b]) => a - b)
            .slice(0, 3); // Show worst 3
        
        if (missingVars.length === 0) {
            return `Your data is **${overall}% complete** with excellent quality.`;
        }
        
        const missingList = missingVars.map(([col, completeness]) => 
            `${col} (${(100 - completeness).toFixed(1)}% missing)`
        ).join(', ');
        
        return `Your data is **${overall}% complete**. Variables with missing values: ${missingList}. During analysis, these will be imputed using spatial neighbor means.`;
    }

    /**
     * Generate variable types summary based on actual data
     * @param {Object} columnTypes - Column type mapping
     * @param {Array} columnNames - All column names
     * @returns {string} Variable types summary
     */
    generateVariableTypesSummary(columnTypes, columnNames) {
        if (!columnTypes || !columnNames) return '';
        
        const typeGroups = {
            numeric: [],
            categorical: [],
            text: []
        };
        
        Object.entries(columnTypes).forEach(([col, type]) => {
            if (typeGroups[type]) {
                typeGroups[type].push(col);
            }
        });
        
        const summary = [];
        if (typeGroups.numeric.length > 0) {
            // Show some example numeric variables
            const examples = typeGroups.numeric.slice(0, 3).join(', ');
            summary.push(`• **${typeGroups.numeric.length} quantitative variables** (${examples}${typeGroups.numeric.length > 3 ? ', ...' : ''})`);
        }
        if (typeGroups.categorical.length > 0) {
            const examples = typeGroups.categorical.slice(0, 2).join(', ');
            summary.push(`• **${typeGroups.categorical.length} categorical variables** (${examples}${typeGroups.categorical.length > 2 ? ', ...' : ''})`);
        }
        if (typeGroups.text.length > 0) {
            summary.push(`• **${typeGroups.text.length} identifier variables** (ward names, codes)`);
        }
        
        return summary.join('\n');
    }

    /**
     * Call the upload API
     * @param {FormData} formData - Form data to upload
     * @returns {Promise<Object>} Upload response
     */
    async callUploadAPI(formData) {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
            // Flask sessions are cookie-based, no need for explicit session ID header
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Upload failed');
        }

        return await response.json();
    }

    /**
     * Send proactive message based on upload type
     * @param {Object} response - Backend response
     * @param {File} csvFile - Uploaded CSV file
     * @param {File} shapeFile - Uploaded shapefile
     */
    sendProactiveMessage(response, csvFile, shapeFile) {
        const uploadType = response.upload_type;
        let proactiveMessage = '';
        
        switch (uploadType) {
            case 'csv_shapefile':
                proactiveMessage = "Data upload and analysis complete. Please proceed with comprehensive malaria risk analysis using both composite scoring and PCA methods for optimal results.";
                break;
            case 'csv_only':
                proactiveMessage = "CSV dataset processed successfully. Please begin statistical analysis - note that geographic visualization will be limited without boundary data.";
                break;
            default:
                proactiveMessage = "Dataset upload complete. Please specify your preferred analysis methodology for malaria risk assessment.";
        }
        
        // Proactive message removed - let user initiate analysis themselves
    }
    /**
     * Verify TPR session state in backend (multi-worker fix)
     * Forces a check with the backend to ensure TPR workflow flags are properly set
     */
    async verifyTPRSessionState() {
        try {
            // Make a lightweight request to check session state
            const response = await fetch('/api/session/verify-tpr', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin' // Important for session cookies
            });
            
            if (!response.ok) {
                console.warn('⚠️ Could not verify TPR session state');
                return;
            }
            
            const data = await response.json();
            
            // If TPR workflow is not active in backend, force a reload
            if (!data.tpr_workflow_active) {
                console.warn('⚠️ TPR workflow not active in backend session, forcing reload...');
                // Small delay to ensure session writes are complete
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            } else {
                console.log('✅ TPR workflow verified active in backend session');
            }
        } catch (error) {
            console.error('Error verifying TPR session state:', error);
            // Don't break the flow, just log the error
        }
    }
    /**
     * Reset uploader state
     */
    reset() {
        this.clearFileInputs();
        this.clearUploadStatus();
        this.disableUploadButton(false);
        
        // Reset session data
        SessionDataManager.updateSessionData({
            csvLoaded: false,
            shapefileLoaded: false,
            analysisComplete: false
        });
        
        this.updateSessionStatus();
    }

}

// Create and export singleton instance
const fileUploader = new FileUploader();

export default fileUploader; 
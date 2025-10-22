// Arena Loading Debug Script
// This script adds debugging and progress tracking for Arena mode

(function() {
    'use strict';

    // Store original console methods
    const originalLog = console.log;
    const originalError = console.error;

    // Add Arena loading status display
    function createLoadingIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'arena-loading-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            z-index: 10000;
            max-width: 300px;
            display: none;
        `;
        document.body.appendChild(indicator);
        return indicator;
    }

    // Update loading status
    function updateLoadingStatus(message, type = 'info') {
        const indicator = document.getElementById('arena-loading-indicator') || createLoadingIndicator();
        indicator.style.display = 'block';
        
        const color = type === 'error' ? '#ff6b6b' : type === 'success' ? '#51cf66' : '#74c0fc';
        indicator.style.borderLeft = `4px solid ${color}`;
        
        const timestamp = new Date().toLocaleTimeString();
        indicator.innerHTML = `
            <div style="margin-bottom: 5px; font-weight: bold;">Arena Status</div>
            <div style="font-size: 11px; color: #aaa;">${timestamp}</div>
            <div style="margin-top: 5px;">${message}</div>
        `;
        
        // Auto-hide after 10 seconds for non-error messages
        if (type !== 'error') {
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 10000);
        }
    }

    // Poll for loading status
    async function checkLoadingStatus(battleId) {
        try {
            const response = await fetch(`/loading_status/${battleId}`);
            const data = await response.json();
            
            if (data.error) {
                updateLoadingStatus(`Error: ${data.error}`, 'error');
                return;
            }
            
            const loadedCount = data.loaded_models.length;
            const totalCount = data.total_models;
            const percentage = Math.round(data.progress_percentage);
            
            let message = `
                Models Loaded: ${loadedCount}/${totalCount} (${percentage}%)<br>
                ✅ Ready: ${data.loaded_models.join(', ')}<br>
            `;
            
            if (data.pending_models.length > 0) {
                message += `⏳ Loading: ${data.pending_models.join(', ')}`;
            }
            
            updateLoadingStatus(message, data.all_loaded ? 'success' : 'info');
            
            // Continue polling if not all loaded
            if (!data.all_loaded) {
                setTimeout(() => checkLoadingStatus(battleId), 2000);
            }
        } catch (error) {
            console.error('Failed to check loading status:', error);
        }
    }

    // Intercept Arena-related console logs
    console.log = function(...args) {
        originalLog.apply(console, args);
        
        const message = args.join(' ');
        
        // Check for Arena-related messages
        if (message.includes('ARENA BATTLE STARTED')) {
            const battleIdMatch = message.match(/Battle ID: ([\w-]+)/);
            if (battleIdMatch) {
                const battleId = battleIdMatch[1];
                updateLoadingStatus('🎯 Arena Battle Started!<br>Loading models...', 'info');
                // Start polling for loading status
                setTimeout(() => checkLoadingStatus(battleId), 1000);
            }
        } else if (message.includes('Models:')) {
            updateLoadingStatus(`🤖 ${message}`, 'info');
        } else if (message.includes('Vote response received')) {
            updateLoadingStatus('✅ Vote recorded! Loading next round...', 'success');
        } else if (message.includes('Error submitting vote')) {
            updateLoadingStatus('❌ Vote failed! Models may still be loading. Please wait and try again.', 'error');
        } else if (message.includes('Background loading')) {
            updateLoadingStatus('⏳ Background loading additional models...', 'info');
        }
    };

    console.error = function(...args) {
        originalError.apply(console, args);
        
        const message = args.join(' ');
        if (message.includes('vote') || message.includes('Arena')) {
            updateLoadingStatus(`⚠️ ${message}`, 'error');
        }
    };

    // Add debug commands
    window.arenaDebug = {
        checkStatus: function(battleId) {
            if (!battleId) {
                console.error('Please provide a battle ID');
                return;
            }
            checkLoadingStatus(battleId);
        },
        
        showProgress: function() {
            const indicator = document.getElementById('arena-loading-indicator');
            if (indicator) {
                indicator.style.display = 'block';
            }
        },
        
        hideProgress: function() {
            const indicator = document.getElementById('arena-loading-indicator');
            if (indicator) {
                indicator.style.display = 'none';
            }
        }
    };

    console.log('🎯 Arena Debug Mode Enabled');
    console.log('Use window.arenaDebug.checkStatus(battleId) to check loading status');
    console.log('Loading indicator will appear in top-right corner');
})();
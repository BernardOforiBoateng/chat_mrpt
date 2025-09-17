/**
 * Survey Button Integration for ChatMRPT
 * Adds a survey button to the existing React interface
 */

(function() {
    'use strict';

    class SurveyButton {
        constructor() {
            console.log('🔵 SurveyButton: Constructor called');
            this.pendingSurveys = 0;
            this.chatmrptSessionId = this.getSessionId();
            this.checkInterval = null;

            this.init();
        }

        init() {
            console.log('🔵 SurveyButton: Init called, readyState:', document.readyState);
            // Wait for page to fully load
            if (document.readyState === 'loading') {
                console.log('🔵 SurveyButton: Waiting for DOMContentLoaded');
                document.addEventListener('DOMContentLoaded', () => this.setup());
            } else {
                console.log('🔵 SurveyButton: Page already loaded, calling setup');
                this.setup();
            }
        }

        setup() {
            console.log('🔵 SurveyButton: Setup called');
            // Create and inject survey button
            this.createSurveyButton();

            // Start checking for pending surveys
            this.startPolling();

            // Listen for ChatMRPT events
            this.setupEventListeners();
        }

        getSessionId() {
            // Try to get session ID from various sources
            return sessionStorage.getItem('chatmrpt_session_id') ||
                   localStorage.getItem('chatmrpt_session_id') ||
                   this.generateSessionId();
        }

        generateSessionId() {
            const id = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('chatmrpt_session_id', id);
            return id;
        }

        createSurveyButton() {
            console.log('🔵 SurveyButton: CreateSurveyButton called');
            // Wait a bit for React to render, then try multiple times to find the nav bar
            let attempts = 0;
            const maxAttempts = 10;

            const tryCreateButton = () => {
                attempts++;
                console.log(`🔵 SurveyButton: Attempt ${attempts}/${maxAttempts} to find nav bar`);

                // Try to find the ChatMRPT navigation bar - look for the area with Clear and Export buttons
                let navBar = document.querySelector('header') ||
                            document.querySelector('[class*="navbar"]') ||
                            document.querySelector('[class*="nav-bar"]') ||
                            document.querySelector('[class*="header"]') ||
                            document.querySelector('nav');

                // Find both Clear and Export buttons to locate the navbar correctly
                const clearButton = Array.from(document.querySelectorAll('button')).find(btn =>
                    btn.textContent.includes('Clear')
                );
                const exportButton = Array.from(document.querySelectorAll('button')).find(btn =>
                    btn.textContent.includes('Export')
                );

                console.log('🔵 SurveyButton: Found navBar?', !!navBar, 'Found Clear?', !!clearButton, 'Found Export?', !!exportButton);

                // Use the common parent of Clear and Export buttons as the navbar
                if (clearButton && exportButton) {
                    // Find common parent that contains both buttons
                    let commonParent = exportButton.parentElement;
                    while (commonParent && !commonParent.contains(clearButton)) {
                        commonParent = commonParent.parentElement;
                    }
                    if (commonParent) {
                        navBar = commonParent;
                    }
                } else if (exportButton) {
                    // Fallback to Export button's parent
                    navBar = exportButton.parentElement;
                }

                // If still no nav bar found and we've tried enough times, create our own
                if (!navBar && attempts >= maxAttempts) {
                    navBar = document.createElement('div');
                    navBar.style.cssText = `
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        height: 60px;
                        background: #ffffff;
                        border-bottom: 1px solid #e5e7eb;
                        display: flex;
                        align-items: center;
                        justify-content: flex-end;
                        padding: 0 20px;
                        z-index: 9998;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    `;
                    document.body.appendChild(navBar);
                    // Add padding to body to account for fixed header
                    document.body.style.paddingTop = '60px';
                } else if (!navBar) {
                    // Try again in 500ms if we haven't reached max attempts
                    setTimeout(tryCreateButton, 500);
                    return;
                }

                // Check if button already exists to avoid duplicates
                if (document.getElementById('survey-button')) {
                    return;
                }

                this.insertSurveyButton(navBar);
            }; // Arrow functions inherit this context

            // Start trying to create the button
            tryCreateButton();
        }

        insertSurveyButton(navBar) {
            // Create button container for top nav
            const buttonContainer = document.createElement('div');
            buttonContainer.id = 'survey-button-container';
            buttonContainer.style.cssText = `
                display: inline-flex;
                align-items: center;
                margin-left: 20px;
                margin-right: 10px;
            `;

            // Create button with a design that fits in the nav bar
            const button = document.createElement('button');
            button.id = 'survey-button';
            button.className = 'survey-btn';
            button.style.cssText = `
                background: transparent;
                color: #374151;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                transition: all 0.2s ease;
                position: relative;
            `;

            button.innerHTML = `
                <span style="font-size: 16px;">📋</span>
                <span>Survey</span>
                <span id="survey-badge" style="
                    display: none;
                    position: absolute;
                    top: -8px;
                    right: -8px;
                    background: #ef4444;
                    color: white;
                    border-radius: 50%;
                    width: 20px;
                    height: 20px;
                    font-size: 11px;
                    text-align: center;
                    line-height: 20px;
                    font-weight: bold;
                ">0</span>
            `;

            button.onmouseover = () => {
                button.style.background = '#2563eb';
                button.style.color = 'white';
                button.style.borderColor = '#2563eb';
            };

            button.onmouseout = () => {
                button.style.background = 'transparent';
                button.style.color = '#374151';
                button.style.borderColor = '#e5e7eb';
            };

            button.onclick = () => this.openSurvey();

            // Add a subtle separator before the survey button
            const separator = document.createElement('span');
            separator.style.cssText = `
                display: inline-block;
                width: 1px;
                height: 24px;
                background: #e5e7eb;
                margin-right: 15px;
                vertical-align: middle;
            `;
            buttonContainer.appendChild(separator);
            buttonContainer.appendChild(button);

            // Add to nav bar - insert at the END after all existing buttons
            // Find all buttons in the nav bar
            const allButtons = Array.from(navBar.querySelectorAll('button'));

            if (allButtons.length > 0) {
                // Get the last button (should be Export)
                const lastButton = allButtons[allButtons.length - 1];

                // Insert after the last button
                if (lastButton.nextSibling) {
                    lastButton.parentElement.insertBefore(buttonContainer, lastButton.nextSibling);
                } else {
                    // If last button is the final element, append to its parent
                    lastButton.parentElement.appendChild(buttonContainer);
                }
            } else {
                // No buttons found, just append to nav bar
                navBar.appendChild(buttonContainer);
            }

            // Add pulsing animation when surveys are pending
            const style = document.createElement('style');
            style.textContent = `
                @keyframes pulse-survey {
                    0% { box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
                    50% { box-shadow: 0 4px 20px rgba(37, 99, 235, 0.4); }
                    100% { box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
                }
                .survey-btn.has-pending {
                    animation: pulse-survey 2s infinite;
                }
            `;
            document.head.appendChild(style);
        }

        openSurvey() {
            // Gather current context
            const context = this.gatherContext();

            // Build survey URL
            const params = new URLSearchParams({
                session_id: this.chatmrptSessionId,
                context: JSON.stringify(context),
                trigger: context.trigger || 'manual'
            });

            const surveyUrl = `/survey?${params.toString()}`;

            // Open in new tab
            window.open(surveyUrl, '_blank');

            // Reset badge
            this.updateBadge(0);
        }

        gatherContext() {
            const context = {
                timestamp: new Date().toISOString(),
                page_url: window.location.href,
                session_id: this.chatmrptSessionId
            };

            // Check if in arena mode
            const arenaSection = document.querySelector('[class*="arena"]');
            if (arenaSection) {
                context.mode = 'arena';
                // Try to extract model names from the UI
                const modelElements = document.querySelectorAll('[class*="model-name"]');
                if (modelElements.length > 0) {
                    context.models = Array.from(modelElements).map(el => el.textContent);
                }
            }

            // Check for recent actions
            const lastAction = sessionStorage.getItem('last_chatmrpt_action');
            if (lastAction) {
                try {
                    context.last_action = JSON.parse(lastAction);
                } catch (e) {
                    context.last_action = lastAction;
                }
            }

            return context;
        }

        startPolling() {
            // Check for pending surveys every 30 seconds
            this.checkPendingSurveys();
            this.checkInterval = setInterval(() => {
                this.checkPendingSurveys();
            }, 30000);
        }

        async checkPendingSurveys() {
            try {
                const response = await fetch(`/survey/api/status/${this.chatmrptSessionId}`);
                const data = await response.json();

                if (data.success) {
                    this.updateBadge(data.pending_count);
                }
            } catch (error) {
                console.error('Failed to check survey status:', error);
            }
        }

        updateBadge(count) {
            const badge = document.getElementById('survey-badge');
            const button = document.getElementById('survey-button');

            if (count > 0) {
                badge.style.display = 'inline-block';
                badge.textContent = count;
                button.classList.add('has-pending');
            } else {
                badge.style.display = 'none';
                button.classList.remove('has-pending');
            }

            this.pendingSurveys = count;
        }

        setupEventListeners() {
            // Listen for specific ChatMRPT events that should trigger surveys

            // Monitor for arena comparisons
            this.monitorArenaComparisons();

            // Monitor for analysis completions
            this.monitorAnalysisCompletions();

            // Monitor for ITN distributions
            this.monitorITNDistributions();
        }

        monitorArenaComparisons() {
            // Override fetch to detect arena API calls
            const originalFetch = window.fetch;
            window.fetch = async (...args) => {
                const response = await originalFetch(...args);

                // Check if this is an arena comparison
                if (args[0] && args[0].includes('/api/arena/compare')) {
                    // Wait a bit for the UI to update
                    setTimeout(() => {
                        this.createSurveyTrigger('arena_comparison', {
                            models: this.extractArenaModels()
                        });
                    }, 2000);
                }

                return response;
            };
        }

        monitorAnalysisCompletions() {
            // Monitor for analysis API calls
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    // Check for analysis results being added to DOM
                    if (mutation.target.id && mutation.target.id.includes('analysis-results')) {
                        this.createSurveyTrigger('risk_analysis_complete', {
                            analysis_type: this.detectAnalysisType()
                        });
                    }
                });
            });

            // Start observing
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['class', 'id']
            });
        }

        monitorITNDistributions() {
            // Similar monitoring for ITN distribution maps
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    // Check for ITN map being added
                    if (mutation.target.id && mutation.target.id.includes('itn-map')) {
                        this.createSurveyTrigger('itn_distribution_generated', {
                            distribution_params: this.extractITNParams()
                        });
                    }
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }

        async createSurveyTrigger(triggerType, context) {
            try {
                const response = await fetch('/survey/api/trigger', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        chatmrpt_session_id: this.chatmrptSessionId,
                        trigger_type: triggerType,
                        context: context
                    })
                });

                if (response.ok) {
                    // Update badge to show new survey
                    this.checkPendingSurveys();

                    // Show notification
                    this.showNotification(`New survey available: ${this.formatTriggerType(triggerType)}`);
                }
            } catch (error) {
                console.error('Failed to create survey trigger:', error);
            }
        }

        formatTriggerType(trigger) {
            const triggerNames = {
                'arena_comparison': 'Arena Comparison',
                'risk_analysis_complete': 'Risk Analysis',
                'itn_distribution_generated': 'ITN Distribution'
            };
            return triggerNames[trigger] || trigger;
        }

        showNotification(message) {
            // Create notification
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #2563eb;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                z-index: 10000;
                animation: slideIn 0.3s ease;
            `;
            notification.textContent = message;

            document.body.appendChild(notification);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }, 5000);
        }

        extractArenaModels() {
            // Try to extract model names from the arena UI
            const models = [];
            document.querySelectorAll('[class*="model-"]').forEach(el => {
                const text = el.textContent;
                if (text && text.includes('Model')) {
                    models.push(text);
                }
            });
            return models;
        }

        detectAnalysisType() {
            // Try to detect which type of analysis was performed
            const content = document.body.textContent;
            if (content.includes('Composite Score')) return 'composite';
            if (content.includes('PCA')) return 'pca';
            return 'unknown';
        }

        extractITNParams() {
            // Try to extract ITN distribution parameters
            const params = {};
            // This would need to be adapted based on actual UI structure
            return params;
        }
    }

    // Initialize survey button
    console.log('🔵 SurveyButton: Script loaded, creating instance');
    window.surveyButton = new SurveyButton();
    console.log('🔵 SurveyButton: Instance created:', !!window.surveyButton);
})();
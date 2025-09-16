/**
 * Survey Button Integration for ChatMRPT
 * Adds a survey button to the existing React interface
 */

(function() {
    'use strict';

    class SurveyButton {
        constructor() {
            this.pendingSurveys = 0;
            this.chatmrptSessionId = this.getSessionId();
            this.checkInterval = null;

            this.init();
        }

        init() {
            // Wait for page to fully load
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.setup());
            } else {
                this.setup();
            }
        }

        setup() {
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
            // Create button container
            const buttonContainer = document.createElement('div');
            buttonContainer.id = 'survey-button-container';
            buttonContainer.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 9999;
            `;

            // Create button
            const button = document.createElement('button');
            button.id = 'survey-button';
            button.className = 'survey-btn';
            button.style.cssText = `
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 50px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            `;

            button.innerHTML = `
                <span>📋</span>
                <span>Survey</span>
                <span id="survey-badge" style="
                    display: none;
                    background: #ef4444;
                    color: white;
                    border-radius: 50%;
                    width: 20px;
                    height: 20px;
                    font-size: 12px;
                    text-align: center;
                    line-height: 20px;
                ">0</span>
            `;

            button.onmouseover = () => {
                button.style.background = '#1d4ed8';
                button.style.transform = 'scale(1.05)';
            };

            button.onmouseout = () => {
                button.style.background = '#2563eb';
                button.style.transform = 'scale(1)';
            };

            button.onclick = () => this.openSurvey();

            buttonContainer.appendChild(button);

            // Add to page
            document.body.appendChild(buttonContainer);

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
    window.surveyButton = new SurveyButton();
})();
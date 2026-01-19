/**
 * Arena Handler Module
 * Manages LLM Arena battles with model comparison and voting
 */

class ArenaHandler {
    constructor() {
        this.currentBattleId = null;
        this.currentView = 0;
        this.totalViews = 3;  // For 5 models showing 2 at a time
        this.responses = {};
        this.modelsRevealed = false;
        this.isLoading = false;
        this.battleHistory = [];
    }
    
    /**
     * Initialize arena mode
     */
    async init() {
        // Check if arena is available
        try {
            const response = await fetch('/api/arena/status');
            const data = await response.json();
            
            if (data.available) {
                console.log('Arena mode available with', data.active_models, 'models');
                this.setupEventListeners();
                return true;
            } else {
                console.warn('Arena mode not available:', data.message);
                return false;
            }
        } catch (error) {
            console.error('Failed to initialize arena:', error);
            return false;
        }
    }
    
    /**
     * Setup event listeners for arena UI
     */
    setupEventListeners() {
        // Listen for arena mode activation
        document.addEventListener('arenaMode', (e) => {
            this.handleArenaMode(e.detail);
        });
        
        // Listen for voting buttons (will be created dynamically)
        document.addEventListener('click', (e) => {
            if (e.target.matches('.arena-vote-btn')) {
                const preference = e.target.dataset.preference;
                this.vote(preference);
            }
            
            if (e.target.matches('.arena-next-btn')) {
                this.nextView();
            }
            
            if (e.target.matches('.arena-regenerate-btn')) {
                this.regenerate();
            }
        });
    }
    
    /**
     * Start a new battle with the given message
     */
    async startBattle(message, viewIndex = null) {
        if (this.isLoading) {
            console.log('Battle already in progress');
            return;
        }
        
        this.isLoading = true;
        this.modelsRevealed = false;
        
        try {
            // Start the battle
            const startResponse = await fetch('/api/arena/start_battle', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ 
                    message, 
                    view_index: viewIndex !== null ? viewIndex : this.currentView 
                })
            });
            
            if (!startResponse.ok) {
                throw new Error(`Failed to start battle: ${startResponse.status}`);
            }
            
            const battleData = await startResponse.json();
            this.currentBattleId = battleData.battle_id;
            
            // Display loading state
            this.displayLoadingState();
            
            // Get responses from both models
            await this.getResponses(message);
            
        } catch (error) {
            console.error('Failed to start battle:', error);
            this.displayError('Failed to start arena battle. Please try again.');
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * Get responses from both models
     */
    async getResponses(message) {
        try {
            const response = await fetch('/api/arena/get_responses', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    battle_id: this.currentBattleId,
                    message: message
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to get responses: ${response.status}`);
            }
            
            const data = await response.json();
            this.responses = data;
            this.displayResponses(data);
            
        } catch (error) {
            console.error('Failed to get responses:', error);
            this.displayError('Failed to get model responses. Please try again.');
        }
    }
    
    /**
     * Display loading state while waiting for responses
     */
    displayLoadingState() {
        const container = document.getElementById('chat-messages') || 
                         document.querySelector('.chat-container');
        
        if (!container) return;
        
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'arena-loading';
        loadingDiv.id = 'arena-loading';
        loadingDiv.innerHTML = `
            <div class="arena-header">
                <h3>⚔️ Arena Mode - Generating Responses...</h3>
                <div class="spinner"></div>
            </div>
            <div class="arena-models-loading">
                <div class="model-loading left">
                    <h4>Model A</h4>
                    <div class="loading-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
                <div class="model-loading right">
                    <h4>Model B</h4>
                    <div class="loading-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(loadingDiv);
    }
    
    /**
     * Display the responses from both models
     */
    displayResponses(data) {
        const container = document.getElementById('chat-messages') || 
                         document.querySelector('.chat-container');
        
        if (!container) return;
        
        // Remove loading state
        const loadingDiv = document.getElementById('arena-loading');
        if (loadingDiv) {
            loadingDiv.remove();
        }
        
        const arenaDiv = document.createElement('div');
        arenaDiv.className = 'arena-responses';
        arenaDiv.id = `arena-battle-${this.currentBattleId}`;
        
        const viewInfo = this.currentView !== null ? 
            `View ${this.currentView + 1}/${this.totalViews}` : '';
        
        arenaDiv.innerHTML = `
            <div class="arena-header">
                <h3>⚔️ Arena Mode ${viewInfo}</h3>
                <div class="arena-controls">
                    ${this.totalViews > 1 ? `
                        <button class="arena-next-btn">
                            Next Models <i class="fas fa-chevron-right"></i>
                        </button>
                    ` : ''}
                    <button class="arena-regenerate-btn" title="Regenerate responses">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </div>
            </div>
            
            <div class="arena-models">
                <div class="model-response left">
                    <div class="model-header">
                        <h4>Model A ${this.modelsRevealed && data.model_a ? 
                            `<span class="model-name">(${data.model_a})</span>` : ''}</h4>
                        <div class="response-stats">
                            <span class="latency">⚡ ${data.latency_a ? data.latency_a.toFixed(0) : 0}ms</span>
                        </div>
                    </div>
                    <div class="response-content">${this.formatResponse(data.response_a)}</div>
                </div>
                
                <div class="model-response right">
                    <div class="model-header">
                        <h4>Model B ${this.modelsRevealed && data.model_b ? 
                            `<span class="model-name">(${data.model_b})</span>` : ''}</h4>
                        <div class="response-stats">
                            <span class="latency">⚡ ${data.latency_b ? data.latency_b.toFixed(0) : 0}ms</span>
                        </div>
                    </div>
                    <div class="response-content">${this.formatResponse(data.response_b)}</div>
                </div>
            </div>
            
            <div class="arena-voting" id="voting-${this.currentBattleId}">
                <button class="arena-vote-btn vote-left" data-preference="left">
                    <i class="fas fa-arrow-left"></i> A is Better
                </button>
                <button class="arena-vote-btn vote-tie" data-preference="tie">
                    <i class="fas fa-equals"></i> Tie
                </button>
                <button class="arena-vote-btn vote-right" data-preference="right">
                    B is Better <i class="fas fa-arrow-right"></i>
                </button>
                <button class="arena-vote-btn vote-both-bad" data-preference="both_bad">
                    <i class="fas fa-thumbs-down"></i> Both Bad
                </button>
            </div>
        `;
        
        container.appendChild(arenaDiv);
        
        // Scroll to the new response
        arenaDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    /**
     * Format response text (handle markdown, code blocks, etc.)
     */
    formatResponse(text) {
        if (!text) return '<em>No response generated</em>';
        
        // Basic markdown-like formatting
        let formatted = text
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Handle code blocks
        formatted = formatted.replace(/```(.*?)```/gs, (match, code) => {
            return `<pre><code>${code}</code></pre>`;
        });
        
        return formatted;
    }
    
    /**
     * Vote for a preference
     */
    async vote(preference) {
        if (!this.currentBattleId) {
            console.error('No active battle to vote on');
            return;
        }
        
        try {
            const response = await fetch('/api/arena/vote', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    battle_id: this.currentBattleId,
                    preference: preference
                })
            });
            
            if (!response.ok) {
                throw new Error(`Vote failed: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Reveal models after voting
            this.modelsRevealed = true;
            this.revealModels(data.models_revealed);
            
            // Disable voting buttons
            this.disableVoting();
            
            // Add to history
            this.battleHistory.push({
                battle_id: this.currentBattleId,
                preference: preference,
                models: data.models_revealed,
                timestamp: new Date()
            });
            
            // Show vote confirmation
            this.showVoteConfirmation(preference, data.models_revealed);
            
        } catch (error) {
            console.error('Failed to record vote:', error);
            this.displayError('Failed to record your vote. Please try again.');
        }
    }
    
    /**
     * Reveal model names after voting
     */
    revealModels(models) {
        const battleDiv = document.getElementById(`arena-battle-${this.currentBattleId}`);
        if (!battleDiv) return;
        
        // Update Model A
        const modelAHeader = battleDiv.querySelector('.model-response.left h4');
        if (modelAHeader && models.model_a) {
            modelAHeader.innerHTML = `Model A <span class="model-name">(${models.model_a.display_name})</span>
                <span class="model-rating">ELO: ${models.model_a.rating.toFixed(0)}</span>`;
        }
        
        // Update Model B
        const modelBHeader = battleDiv.querySelector('.model-response.right h4');
        if (modelBHeader && models.model_b) {
            modelBHeader.innerHTML = `Model B <span class="model-name">(${models.model_b.display_name})</span>
                <span class="model-rating">ELO: ${models.model_b.rating.toFixed(0)}</span>`;
        }
    }
    
    /**
     * Disable voting buttons after vote
     */
    disableVoting() {
        const votingDiv = document.getElementById(`voting-${this.currentBattleId}`);
        if (!votingDiv) return;
        
        const buttons = votingDiv.querySelectorAll('.arena-vote-btn');
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
        });
    }
    
    /**
     * Show vote confirmation message
     */
    showVoteConfirmation(preference, models) {
        const votingDiv = document.getElementById(`voting-${this.currentBattleId}`);
        if (!votingDiv) return;
        
        const confirmDiv = document.createElement('div');
        confirmDiv.className = 'vote-confirmation';
        
        let message = '';
        switch(preference) {
            case 'left':
                message = `You voted for ${models.model_a.display_name}! `;
                break;
            case 'right':
                message = `You voted for ${models.model_b.display_name}! `;
                break;
            case 'tie':
                message = 'You voted for a tie! ';
                break;
            case 'both_bad':
                message = 'You voted both responses as inadequate. ';
                break;
        }
        
        confirmDiv.innerHTML = `
            <i class="fas fa-check-circle"></i> ${message}
            <span class="elo-change">
                ${models.model_a.display_name}: ${models.model_a.rating.toFixed(0)} | 
                ${models.model_b.display_name}: ${models.model_b.rating.toFixed(0)}
            </span>
        `;
        
        votingDiv.appendChild(confirmDiv);
    }
    
    /**
     * Move to next view (next pair of models)
     */
    async nextView() {
        this.currentView = (this.currentView + 1) % this.totalViews;
        
        // Get the last message
        const lastMessage = this.getLastUserMessage();
        if (lastMessage) {
            await this.startBattle(lastMessage, this.currentView);
        }
    }
    
    /**
     * Regenerate responses with same models
     */
    async regenerate() {
        const lastMessage = this.getLastUserMessage();
        if (lastMessage) {
            await this.startBattle(lastMessage, this.currentView);
        }
    }
    
    /**
     * Get the last user message from input or history
     */
    getLastUserMessage() {
        // Try to get from input field
        const input = document.querySelector('#user-input') || 
                     document.querySelector('.chat-input') ||
                     document.querySelector('textarea[name="message"]');
        
        if (input && input.value) {
            return input.value;
        }
        
        // Try to get from last user message in chat
        const userMessages = document.querySelectorAll('.message.user');
        if (userMessages.length > 0) {
            const lastMessage = userMessages[userMessages.length - 1];
            return lastMessage.textContent.trim();
        }
        
        return null;
    }
    
    /**
     * Display error message
     */
    displayError(message) {
        const container = document.getElementById('chat-messages') || 
                         document.querySelector('.chat-container');
        
        if (!container) return;
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'arena-error';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
    
    /**
     * Get arena statistics
     */
    async getStatistics() {
        try {
            const response = await fetch('/api/arena/statistics');
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Failed to get statistics:', error);
            return null;
        }
    }
    
    /**
     * Get leaderboard
     */
    async getLeaderboard() {
        try {
            const response = await fetch('/api/arena/leaderboard');
            const data = await response.json();
            return data.leaderboard;
        } catch (error) {
            console.error('Failed to get leaderboard:', error);
            return [];
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ArenaHandler;
}

// Initialize arena handler when DOM is ready
if (typeof window !== 'undefined') {
    window.arenaHandler = new ArenaHandler();
    
    // Initialize when document is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.arenaHandler.init();
        });
    } else {
        window.arenaHandler.init();
    }
}
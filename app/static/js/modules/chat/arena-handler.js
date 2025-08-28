/**
 * Arena Handler Module
 * Manages the LLM battle interface for model comparison
 */

export class ArenaHandler {
    constructor() {
        this.currentBattleId = null;
        this.isWaitingForResponse = false;
        this.conversationHistory = [];
        this.battleCount = 0;
        this.hasVoted = false;
        
        this.init();
    }

    init() {
        // Get DOM elements
        this.responseA = document.getElementById('responseA');
        this.responseB = document.getElementById('responseB');
        this.arenaInput = document.getElementById('arenaInput');
        this.sendBtn = document.getElementById('arenaSendBtn');
        this.votingArea = document.getElementById('votingArea');
        this.battleCountDisplay = document.getElementById('battleCount');
        
        // Bind events
        this.bindEvents();
        
        // Load stats
        this.loadStatistics();
        
        console.log('Arena Handler initialized');
    }

    bindEvents() {
        // Input events
        if (this.arenaInput) {
            this.arenaInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            // Auto-resize textarea
            this.arenaInput.addEventListener('input', () => {
                this.autoResizeInput();
            });
        }
        
        // Handle ESC key to cancel battle
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.currentBattleId) {
                this.cancelBattle();
            }
        });
    }

    autoResizeInput() {
        if (this.arenaInput) {
            this.arenaInput.style.height = 'auto';
            this.arenaInput.style.height = Math.min(this.arenaInput.scrollHeight, 120) + 'px';
        }
    }

    async sendMessage() {
        if (this.isWaitingForResponse) return;
        
        const message = this.arenaInput?.value?.trim();
        if (!message) return;
        
        // Clear input
        this.arenaInput.value = '';
        this.autoResizeInput();
        
        // Add to conversation history
        this.conversationHistory.push({
            role: 'user',
            content: message,
            timestamp: Date.now()
        });
        
        // Start battle if not already active
        if (!this.currentBattleId) {
            await this.startBattle(message);
        } else {
            // Continue conversation in current battle
            await this.continueConversation(message);
        }
    }

    async startBattle(message) {
        this.isWaitingForResponse = true;
        this.hasVoted = false;
        this.setLoadingState(true);
        
        try {
            // Check if query should use arena mode
            const routingCheck = await fetch('/api/arena/check_routing', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            
            const routing = await routingCheck.json();
            
            if (!routing.use_arena) {
                // Redirect to normal chat mode
                this.showNotification('This query requires advanced tools. Switching to normal mode...', 'info');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
                return;
            }
            
            // Start battle
            const startResponse = await fetch('/api/arena/start_battle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            
            const battleInfo = await startResponse.json();
            
            if (battleInfo.error) {
                this.showError(battleInfo.error);
                return;
            }
            
            this.currentBattleId = battleInfo.battle_id;
            
            // Get responses from both models
            await this.getResponses(message);
            
        } catch (error) {
            console.error('Error starting battle:', error);
            this.showError('Failed to start battle');
        } finally {
            this.isWaitingForResponse = false;
            this.setLoadingState(false);
        }
    }

    async getResponses(message) {
        // Show loading state
        this.showTypingIndicator('a');
        this.showTypingIndicator('b');
        
        try {
            // Use streaming endpoint for real-time responses
            const eventSource = new EventSource('/api/arena/get_responses_streaming', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    battle_id: this.currentBattleId,
                    message: message
                })
            });
            
            let responseA = '';
            let responseB = '';
            
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.error) {
                    this.showError(data.error);
                    eventSource.close();
                    return;
                }
                
                if (data.done) {
                    // Responses complete
                    eventSource.close();
                    this.hideTypingIndicator('a');
                    this.hideTypingIndicator('b');
                    this.showVotingArea();
                    return;
                }
                
                // Append chunks to responses
                if (data.a) {
                    responseA += data.a;
                    this.updateResponse('a', responseA);
                }
                
                if (data.b) {
                    responseB += data.b;
                    this.updateResponse('b', responseB);
                }
            };
            
            eventSource.onerror = (error) => {
                console.error('Streaming error:', error);
                eventSource.close();
                
                // Fallback to non-streaming endpoint
                this.getResponsesNonStreaming(message);
            };
            
        } catch (error) {
            console.error('Error getting responses:', error);
            this.showError('Failed to get model responses');
        }
    }

    async getResponsesNonStreaming(message) {
        try {
            const response = await fetch('/api/arena/get_responses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    battle_id: this.currentBattleId,
                    message: message
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
                return;
            }
            
            // Display responses
            this.updateResponse('a', data.response_a);
            this.updateResponse('b', data.response_b);
            
            // Hide loading and show voting
            this.hideTypingIndicator('a');
            this.hideTypingIndicator('b');
            this.showVotingArea();
            
            // Store latency info
            this.currentLatency = {
                a: data.latency_a,
                b: data.latency_b
            };
            
        } catch (error) {
            console.error('Error in non-streaming mode:', error);
            this.showError('Failed to get responses');
        }
    }

    updateResponse(panel, content) {
        const responseElement = panel === 'a' ? this.responseA : this.responseB;
        if (responseElement) {
            // Parse markdown
            const html = this.parseMarkdown(content);
            responseElement.innerHTML = `<div class="response-content">${html}</div>`;
        }
    }

    parseMarkdown(text) {
        // Use marked.js if available, otherwise basic parsing
        if (typeof marked !== 'undefined') {
            return marked.parse(text);
        }
        
        // Basic markdown parsing
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    showTypingIndicator(panel) {
        const responseElement = panel === 'a' ? this.responseA : this.responseB;
        if (responseElement) {
            responseElement.innerHTML = `
                <div class="response-loading">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            `;
        }
    }

    hideTypingIndicator(panel) {
        const responseElement = panel === 'a' ? this.responseA : this.responseB;
        if (responseElement && responseElement.querySelector('.response-loading')) {
            responseElement.innerHTML = '';
        }
    }

    showVotingArea() {
        if (this.votingArea && !this.hasVoted) {
            this.votingArea.style.display = 'flex';
        }
    }

    hideVotingArea() {
        if (this.votingArea) {
            this.votingArea.style.display = 'none';
        }
    }

    async vote(preference) {
        if (!this.currentBattleId || this.hasVoted) return;
        
        this.hasVoted = true;
        this.hideVotingArea();
        
        try {
            const response = await fetch('/api/arena/vote', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    battle_id: this.currentBattleId,
                    preference: preference
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show model reveal
                this.revealModels(result.models_revealed);
                
                // Update battle count
                this.battleCount++;
                this.updateBattleCount();
                
                // Show success notification
                this.showNotification(`Vote recorded: ${preference}`, 'success');
            }
            
        } catch (error) {
            console.error('Error recording vote:', error);
            this.showError('Failed to record vote');
        }
    }

    revealModels(models) {
        // Update panel headers to show actual models
        const panelA = document.querySelector('#panelA .model-label');
        const panelB = document.querySelector('#panelB .model-label');
        
        if (panelA && models.model_a) {
            panelA.innerHTML = `
                <span>${models.model_a.display_name}</span>
                <span class="badge bg-secondary ms-2">ELO: ${models.model_a.rating.toFixed(0)}</span>
            `;
        }
        
        if (panelB && models.model_b) {
            panelB.innerHTML = `
                <span>${models.model_b.display_name}</span>
                <span class="badge bg-secondary ms-2">ELO: ${models.model_b.rating.toFixed(0)}</span>
            `;
        }
        
        // Show modal with details
        this.showModelRevealModal(models);
    }

    showModelRevealModal(models) {
        const modalContent = document.getElementById('modelRevealContent');
        if (modalContent) {
            modalContent.innerHTML = `
                <div class="row">
                    <div class="col-6">
                        <h6>Assistant A</h6>
                        <p class="model-name-reveal">${models.model_a.display_name}</p>
                        <div class="model-stats">
                            <div class="stat-item">
                                <span class="stat-label">ELO:</span>
                                <span class="stat-value">${models.model_a.rating.toFixed(0)}</span>
                            </div>
                            ${this.currentLatency ? `
                            <div class="stat-item">
                                <span class="stat-label">Time:</span>
                                <span class="stat-value">${this.currentLatency.a.toFixed(0)}ms</span>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                    <div class="col-6">
                        <h6>Assistant B</h6>
                        <p class="model-name-reveal">${models.model_b.display_name}</p>
                        <div class="model-stats">
                            <div class="stat-item">
                                <span class="stat-label">ELO:</span>
                                <span class="stat-value">${models.model_b.rating.toFixed(0)}</span>
                            </div>
                            ${this.currentLatency ? `
                            <div class="stat-item">
                                <span class="stat-label">Time:</span>
                                <span class="stat-value">${this.currentLatency.b.toFixed(0)}ms</span>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('modelRevealModal'));
        modal.show();
    }

    async regenerateResponse(panel) {
        if (this.isWaitingForResponse) return;
        
        const lastMessage = this.conversationHistory[this.conversationHistory.length - 1];
        if (!lastMessage || lastMessage.role !== 'user') return;
        
        this.showTypingIndicator(panel);
        
        // Regenerate just one model's response
        // This would need a specific endpoint implementation
        console.log(`Regenerating response for panel ${panel}`);
        
        // For now, just remove loading after delay
        setTimeout(() => {
            this.hideTypingIndicator(panel);
        }, 2000);
    }

    copyResponse(panel) {
        const responseElement = panel === 'a' ? this.responseA : this.responseB;
        if (responseElement) {
            const text = responseElement.innerText;
            navigator.clipboard.writeText(text);
            this.showNotification('Response copied to clipboard', 'success');
        }
    }

    expandResponse(panel) {
        const panelElement = document.getElementById(`panel${panel.toUpperCase()}`);
        if (panelElement) {
            panelElement.classList.toggle('expanded');
            // Would need CSS for expanded state
        }
    }

    async newBattle() {
        // Reset state
        this.currentBattleId = null;
        this.hasVoted = false;
        this.conversationHistory = [];
        this.currentLatency = null;
        
        // Reset UI
        this.responseA.innerHTML = '<div class="response-content"><p>Hello! How can I help you today?</p></div>';
        this.responseB.innerHTML = '<div class="response-content"><p>Hello! 👋 How can I assist you today?</p></div>';
        
        // Reset model labels
        document.querySelector('#panelA .model-label').textContent = 'Assistant A';
        document.querySelector('#panelB .model-label').textContent = 'Assistant B';
        
        this.hideVotingArea();
        this.arenaInput.focus();
    }

    async showLeaderboard() {
        try {
            const response = await fetch('/api/arena/leaderboard');
            const data = await response.json();
            
            const leaderboardContent = document.getElementById('leaderboardContent');
            if (leaderboardContent) {
                let html = '<div class="leaderboard-table">';
                
                // Header
                html += `
                    <div class="leaderboard-row leaderboard-header">
                        <div>Rank</div>
                        <div>Model</div>
                        <div>ELO</div>
                        <div>Battles</div>
                        <div>Win Rate</div>
                    </div>
                `;
                
                // Rows
                data.leaderboard.forEach(model => {
                    const rankClass = model.rank === 1 ? 'rank-1' : 
                                    model.rank === 2 ? 'rank-2' : 
                                    model.rank === 3 ? 'rank-3' : 'rank-other';
                    
                    html += `
                        <div class="leaderboard-row">
                            <div><span class="rank-badge ${rankClass}">${model.rank}</span></div>
                            <div>${model.display_name}</div>
                            <div>${model.elo_rating}</div>
                            <div>${model.battles_fought}</div>
                            <div>${model.win_rate}%</div>
                        </div>
                    `;
                });
                
                html += '</div>';
                leaderboardContent.innerHTML = html;
            }
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('leaderboardModal'));
            modal.show();
            
        } catch (error) {
            console.error('Error loading leaderboard:', error);
            this.showError('Failed to load leaderboard');
        }
    }

    toggleMode() {
        // Switch between arena and normal mode
        if (confirm('Switch to normal chat mode?')) {
            window.location.href = '/';
        }
    }

    cancelBattle() {
        if (this.currentBattleId && !this.hasVoted) {
            if (confirm('Cancel current battle without voting?')) {
                this.newBattle();
            }
        }
    }

    async loadStatistics() {
        try {
            const response = await fetch('/api/arena/statistics');
            const stats = await response.json();
            
            this.battleCount = stats.completed_battles || 0;
            this.updateBattleCount();
            
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    updateBattleCount() {
        if (this.battleCountDisplay) {
            this.battleCountDisplay.textContent = this.battleCount;
        }
    }

    setLoadingState(loading) {
        if (this.sendBtn) {
            this.sendBtn.disabled = loading;
            if (loading) {
                this.sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
            } else {
                this.sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send';
            }
        }
    }

    showNotification(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Add to container
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        // Initialize and show
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove after hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    showError(message) {
        this.showNotification(message, 'error');
    }
}
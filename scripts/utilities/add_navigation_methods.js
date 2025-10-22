// Navigation methods to add to arena-handler.js

// Add these methods before the closing brace of the ArenaHandler class:

    // Navigation methods for 5 models (2 at a time)
    nextView() {
        if (!this.allResponses || Object.keys(this.allResponses).length < 5) {
            return; // Need all 5 responses first
        }
        
        this.currentViewIndex = (this.currentViewIndex + 1) % this.totalViews;
        this.loadModelPair(this.currentViewIndex);
        this.updateNavigationIndicator();
    }
    
    previousView() {
        if (!this.allResponses || Object.keys(this.allResponses).length < 5) {
            return; // Need all 5 responses first
        }
        
        this.currentViewIndex = (this.currentViewIndex - 1 + this.totalViews) % this.totalViews;
        this.loadModelPair(this.currentViewIndex);
        this.updateNavigationIndicator();
    }
    
    loadModelPair(viewIndex) {
        // Map view index to model pairs
        // View 0: Models 0 & 1 (llama vs mistral)
        // View 1: Models 2 & 3 (qwen3 vs biomistral)
        // View 2: Model 4 & 0 (gemma vs llama wrap)
        
        const modelKeys = Object.keys(this.allResponses);
        let modelA, modelB;
        
        switch(viewIndex) {
            case 0:
                modelA = modelKeys[0];
                modelB = modelKeys[1];
                break;
            case 1:
                modelA = modelKeys[2];
                modelB = modelKeys[3];
                break;
            case 2:
                modelA = modelKeys[4];
                modelB = modelKeys[0]; // Wrap around
                break;
        }
        
        // Update the displayed responses
        this.updateResponse('a', this.allResponses[modelA].content);
        this.updateResponse('b', this.allResponses[modelB].content);
        
        // Update model labels (still hidden until vote)
        if (!this.hasVoted) {
            document.querySelector('#panelA .model-label').textContent = 'Assistant A';
            document.querySelector('#panelB .model-label').textContent = 'Assistant B';
        }
        
        // Store current model mapping for voting
        this.currentModelMapping = {
            a: modelA,
            b: modelB
        };
    }
    
    updateNavigationIndicator() {
        if (this.viewIndicator) {
            this.viewIndicator.textContent = `View ${this.currentViewIndex + 1} of ${this.totalViews}`;
        }
        
        // Update button states
        if (this.prevBtn) {
            this.prevBtn.disabled = false; // Always enabled with wrap-around
        }
        
        if (this.nextBtn) {
            this.nextBtn.disabled = false; // Always enabled with wrap-around
        }
    }
    
    async getAllModelResponses(message) {
        // Fetch responses from all 5 models
        this.allResponses = {};
        this.setLoadingState(true);
        
        try {
            // Request all model responses
            const response = await fetch('/api/arena/get_all_responses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    battle_id: this.currentBattleId,
                    message: message,
                    view_index: 'all' // Get all 5 models
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.allResponses = data.responses;
                
                // Load the first pair (view 0)
                this.currentViewIndex = 0;
                this.loadModelPair(0);
                this.updateNavigationIndicator();
                
                // Enable navigation
                this.showNavigationControls();
            }
        } catch (error) {
            console.error('Error getting all model responses:', error);
            this.showError('Failed to get all model responses');
        } finally {
            this.setLoadingState(false);
        }
    }
    
    showNavigationControls() {
        const navControls = document.getElementById('navigationControls');
        if (navControls) {
            navControls.style.display = 'flex';
        }
    }
    
    hideNavigationControls() {
        const navControls = document.getElementById('navigationControls');
        if (navControls) {
            navControls.style.display = 'none';
        }
    }
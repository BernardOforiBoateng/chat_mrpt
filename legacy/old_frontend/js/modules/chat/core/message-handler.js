/**
 * Message Handler Module
 * Handles core message sending, receiving, and display
 */

import { SessionDataManager } from '../../utils/storage.js';
import apiClient from '../../utils/api-client.js';
import DOMHelpers from '../../utils/dom-helpers.js';

export class MessageHandler {
    constructor(chatContainer, messageInput, sendButton) {
        this.chatContainer = chatContainer;
        this.messageInput = messageInput;
        this.sendButton = sendButton;
        this.isWaitingForResponse = false;
        
        this.bindEvents();
    }

    bindEvents() {
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.sendMessage());
        }

        if (this.messageInput) {
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            this.messageInput.addEventListener('input', () => {
                this.autoResizeInput();
            });
        }
    }

    async sendMessage(customMessage = null) {
        if (this.isWaitingForResponse) return;

        const message = customMessage || this.messageInput?.value?.trim();
        if (!message) return;
        
        // Preserve 'this' context for nested functions
        const self = this;

        // Clear input if using default input
        if (!customMessage && this.messageInput) {
            this.messageInput.value = '';
            this.autoResizeInput();
        }

        // Check if this is the first message (welcome message is showing)
        // Clear all messages to start fresh conversation at top
        const welcomeMessage = this.chatContainer?.querySelector('.welcome-message-content');
        const isFirstMessage = !!welcomeMessage;
        if (isFirstMessage && this.chatContainer) {
            this.chatContainer.innerHTML = ''; // Clear everything to start at top
            this.chatContainer.classList.remove('has-welcome-message'); // Remove welcome styling
        }
        
        // Don't display system triggers like __DATA_UPLOADED__ in the chat
        if (!message.startsWith('__') || !message.endsWith('__')) {
            this.addUserMessage(message);
        }
        this.isWaitingForResponse = true;
        this.showTypingIndicator();
        
        // FIXED: Add loading state to send button
        if (this.sendButton) {
            this.sendButton.classList.add('loading');
            this.sendButton.disabled = true;
        }

        try {
            const sessionData = SessionDataManager.getSessionData();
            
            // Check if streaming is enabled (can be toggled via settings)
            const useStreaming = true; // Always use streaming for better UX
            console.log('🔥 STREAMING DEBUG: useStreaming =', useStreaming);
            
            if (useStreaming) {
                console.log('🔥 STREAMING DEBUG: Using streaming endpoint!');
                // Use streaming for better UX
                let streamingMessageElement = null;
                let streamingContent = '';
                let fullResponse = {};
                let chunkQueue = [];
                let isProcessingQueue = false;
                
                // Process chunks with slight delay for smooth typing effect
                // Use arrow function to preserve 'this' context
                const processChunkQueue = async () => {
                    if (isProcessingQueue || chunkQueue.length === 0) return;
                    isProcessingQueue = true;
                    
                    while (chunkQueue.length > 0) {
                        const chunkText = chunkQueue.shift();
                        const contentDiv = streamingMessageElement?.querySelector('.message-content');
                        if (contentDiv && chunkText) {
                            // Update the full streamed content and reparse ALL of it
                            // This ensures markdown that spans chunks is properly parsed
                            const fullParsedContent = self.parseMarkdownContent(streamingContent);
                            contentDiv.innerHTML = fullParsedContent;
                            
                            // Smooth scroll to show new content
                            if (this.chatContainer) {
                                this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
                            }
                            
                            // Add tiny delay between chunks for smooth flow (only if more chunks waiting)
                            if (chunkQueue.length > 0) {
                                await new Promise(resolve => setTimeout(resolve, 5)); // 5ms between chunks for responsive streaming
                            }
                        }
                    }
                    
                    isProcessingQueue = false;
                };
                
                apiClient.sendMessageStreaming(
                    message, 
                    sessionData.currentLanguage,
                    // onChunk callback
                    (chunk) => {
                        // Check if this is an Arena response
                        if (chunk.arena_mode === true) {
                            console.log('🎮 Arena mode detected in streaming chunk!');
                            this.hideTypingIndicator();
                            
                            // Create dual message element for Arena responses
                            if (chunk.response_a && chunk.response_b) {
                                console.log('🎮 Creating dual element with responses:', {
                                    response_a: chunk.response_a.substring(0, 50) + '...',
                                    response_b: chunk.response_b.substring(0, 50) + '...'
                                });
                                
                                const dualElement = this.createDualMessageElement(
                                    chunk.response_a,
                                    chunk.response_b,
                                    chunk.battle_id,
                                    chunk.view_index || 0
                                );
                                
                                console.log('🎮 Dual element created:', dualElement);
                                console.log('🎮 Chat container exists?', !!this.chatContainer);
                                
                                this.appendMessage(dualElement);
                                console.log('🎮 Dual element appended to chat');
                                
                                // Store model names for later reveal
                                if (chunk.model_a && chunk.model_b) {
                                    sessionStorage.setItem(`battle_${chunk.battle_id}_models`, JSON.stringify({
                                        model_a: chunk.model_a,
                                        model_b: chunk.model_b
                                    }));
                                }
                                
                                // Mark as Arena handled
                                fullResponse.arena_handled = true;
                            }
                            return;
                        }
                        
                        // Regular streaming content handling
                        if (!streamingMessageElement && !fullResponse.arena_handled) {
                            this.hideTypingIndicator();
                            streamingMessageElement = this.createMessageElement('assistant', '', 'assistant-message streaming');
                            this.appendMessage(streamingMessageElement);
                        }
                        
                        if (chunk.content && !fullResponse.arena_handled) {
                            streamingContent += chunk.content;
                            // Queue the chunk for smooth processing
                            chunkQueue.push(chunk.content);
                            processChunkQueue();
                        }
                        
                        // Update fullResponse with latest data
                        if (chunk.status) fullResponse.status = chunk.status;
                        if (chunk.visualizations) fullResponse.visualizations = chunk.visualizations;
                        if (chunk.tools_used) fullResponse.tools_used = chunk.tools_used;
                        if (chunk.download_links) fullResponse.download_links = chunk.download_links;
                    },
                    // onComplete callback
                    async (finalData) => {
                        // Skip regular processing if Arena was handled
                        if (fullResponse.arena_handled) {
                            this.isWaitingForResponse = false;
                            if (this.sendButton) {
                                this.sendButton.classList.remove('loading');
                                this.sendButton.disabled = false;
                            }
                            return;
                        }
                        
                        // Wait for all chunks to be processed before parsing markdown
                        while (chunkQueue.length > 0 || isProcessingQueue) {
                            await new Promise(resolve => setTimeout(resolve, 50));
                        }
                        
                        if (streamingMessageElement) {
                            streamingMessageElement.classList.remove('streaming');
                            
                            // DON'T replace the content - it's already been streamed!
                            // Just remove the streaming class to indicate completion
                        }
                        
                        // Prepare final response object
                        fullResponse.response = streamingContent;
                        fullResponse.message = streamingContent;
                        fullResponse.streaming_handled = true;  // ✅ Mark as handled via streaming
                        
                        // CRITICAL: Transfer visualizations from finalData if present
                        if (finalData.visualizations) {
                            fullResponse.visualizations = finalData.visualizations;
                            console.log('📊 Transferred visualizations from finalData:', finalData.visualizations);
                        }
                        
                        // Debug: Check if visualizations are present
                        if (fullResponse.visualizations && fullResponse.visualizations.length > 0) {
                            console.log('📊 VISUALIZATIONS PRESENT in fullResponse:', fullResponse.visualizations);
                        }
                        
                        // Emit event for other modules to handle
                        document.dispatchEvent(new CustomEvent('messageResponse', { 
                            detail: { response: fullResponse, originalMessage: message }
                        }));
                        
                        // Check if TPR analysis is complete (has download links)
                        console.log('[v2.1] Checking TPR completion. Has download_links?', !!fullResponse.download_links, 'Length:', fullResponse.download_links?.length || 0);
                        if (fullResponse.download_links && fullResponse.download_links.length > 0) {
                            console.log('[v2.1] ✅ Dispatching tprAnalysisComplete event with', fullResponse.download_links.length, 'links');
                            document.dispatchEvent(new CustomEvent('tprAnalysisComplete', {
                                detail: { download_links: fullResponse.download_links }
                            }));
                            
                            // REMOVED: Old TPR trigger logic that caused duplicates
                            // The V3 agent now handles the entire transition internally
                            // No need for frontend to send __DATA_UPLOADED__ anymore
                        }
                        
                        this.isWaitingForResponse = false;
                        
                        // FIXED: Remove loading state from send button
                        if (this.sendButton) {
                            this.sendButton.classList.remove('loading');
                            this.sendButton.disabled = false;
                        }
                    }
                );
                
                return; // Exit early for streaming
            } else {
                // Fallback to regular non-streaming
                const response = await apiClient.sendMessage(message, sessionData.currentLanguage);

                this.hideTypingIndicator();
                
                // Debug logging
                console.log('🔍 DEBUG: Raw response from backend:', response);
                console.log('🔍 DEBUG: Response has .response field:', !!response.response);
                console.log('🔍 DEBUG: Response has .message field:', !!response.message);
                
                // Emit event for other modules to handle
                document.dispatchEvent(new CustomEvent('messageResponse', { 
                    detail: { response, originalMessage: message }
                }));

                return response;
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.isWaitingForResponse = false;
            
            // FIXED: Remove loading state on error
            if (this.sendButton) {
                this.sendButton.classList.remove('loading');
                this.sendButton.disabled = false;
            }
            
            // FIXED: Better error messages based on error type
            let errorMessage = 'Sorry, there was an error processing your request.';
            
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = 'Connection failed. Please check your internet connection and try again.';
            } else if (error.message.includes('timeout')) {
                errorMessage = 'Request timed out. The server might be busy. Please try again.';
            } else if (error.message.includes('429')) {
                errorMessage = 'Too many requests. Please wait a moment and try again.';
            } else if (error.message.includes('5')) {
                errorMessage = 'Server error. Our team has been notified. Please try again in a few minutes.';
            }
            
            this.addSystemMessage(`
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>${errorMessage}</span>
                    <button class="btn btn-sm btn-outline-primary retry-btn" onclick="document.getElementById('message-input').focus()">
                        Try Again
                    </button>
                </div>
            `);
            
            console.error('Error sending message:', error);
            // Don't re-throw error to prevent global error handler spam
            return { status: 'error', message: error.message };
        }
    }

    addUserMessage(message) {
        const messageElement = this.createMessageElement('user', message, 'user-message');
        this.appendMessage(messageElement);
        // FIXED: Remove redundant scroll call - appendMessage handles it
    }

    addAssistantMessage(message) {
        const messageElement = this.createMessageElement('assistant', message, 'assistant-message');
        this.appendMessage(messageElement);
        // FIXED: Remove redundant scroll call - appendMessage handles it
        return messageElement;
    }

    addSystemMessage(message) {
        const messageElement = this.createMessageElement('system', message, 'system-message');
        this.appendMessage(messageElement);
        // FIXED: Remove redundant scroll call - appendMessage handles it
    }

    createMessageElement(sender, content, className) {
        const messageDiv = DOMHelpers.createElement('div', {
            className: `message ${className} new-message`
        });

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Enhanced markdown parsing for all content
        const parsedContent = this.parseMarkdownContent(content);
        console.log('🔍 DEBUG: Setting innerHTML to:', parsedContent.substring(0, 100));
        contentDiv.innerHTML = parsedContent;

        messageDiv.appendChild(contentDiv);
        return messageDiv;
    }
    
    createDualMessageElement(responseA, responseB, battleId, viewIndex) {
        const containerDiv = DOMHelpers.createElement('div', {
            className: 'message assistant-message dual-response-container new-message',
            'data-battle-id': battleId,
            'data-view-index': viewIndex
        });

        // Add Arena mode indicator
        const arenaHeader = document.createElement('div');
        arenaHeader.className = 'arena-header';
        arenaHeader.innerHTML = `
            <span style="color: #6b7280; font-size: 13px; font-weight: 600;">
                <i class="fas fa-random" style="margin-right: 6px;"></i>
                Arena Mode <span class="arena-badge">Blind Test</span>
            </span>
        `;
        containerDiv.appendChild(arenaHeader);

        // Create the dual response layout
        const contentDiv = document.createElement('div');
        contentDiv.className = 'dual-response-content';
        
        // Response A
        const responseADiv = document.createElement('div');
        responseADiv.className = 'response-panel response-a';
        responseADiv.innerHTML = `
            <div class="response-header">
                <span class="response-label">Assistant A</span>
                <span class="model-name hidden" data-model="a"></span>
            </div>
            <div class="response-body">${this.parseMarkdownContent(responseA)}</div>
        `;
        
        // Response B
        const responseBDiv = document.createElement('div');
        responseBDiv.className = 'response-panel response-b';
        responseBDiv.innerHTML = `
            <div class="response-header">
                <span class="response-label">Assistant B</span>
                <span class="model-name hidden" data-model="b"></span>
            </div>
            <div class="response-body">${this.parseMarkdownContent(responseB)}</div>
        `;
        
        contentDiv.appendChild(responseADiv);
        contentDiv.appendChild(responseBDiv);
        containerDiv.appendChild(contentDiv);
        
        // Add voting buttons
        const votingDiv = document.createElement('div');
        votingDiv.className = 'voting-buttons';
        votingDiv.innerHTML = `
            <button class="vote-btn" data-vote="a">
                <i class="fas fa-chevron-left"></i> Left is Better
            </button>
            <button class="vote-btn" data-vote="b">
                <i class="fas fa-chevron-right"></i> Right is Better
            </button>
            <button class="vote-btn" data-vote="tie">
                <i class="fas fa-equals"></i> It's a tie
            </button>
            <button class="vote-btn" data-vote="bad">
                <i class="fas fa-times-circle"></i> Both are bad
            </button>
        `;
        
        // Add vote handlers
        votingDiv.querySelectorAll('.vote-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleVote(e, battleId));
        });
        
        containerDiv.appendChild(votingDiv);
        
        // Add view navigation if multiple views
        if (viewIndex !== undefined) {
            const navDiv = document.createElement('div');
            navDiv.className = 'view-navigation';
            navDiv.innerHTML = `
                <span class="view-indicator">View ${viewIndex + 1} of 3</span>
            `;
            containerDiv.appendChild(navDiv);
        }
        
        return containerDiv;
    }
    
    async handleVote(event, battleId) {
        const vote = event.currentTarget.dataset.vote;
        const container = event.currentTarget.closest('.dual-response-container');
        
        // Disable voting buttons
        container.querySelectorAll('.vote-btn').forEach(btn => {
            btn.disabled = true;
        });
        
        try {
            // Send vote to backend
            const response = await fetch('/api/vote_arena', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ battle_id: battleId, vote: vote })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Reveal model names
                const modelA = container.querySelector('.model-name[data-model="a"]');
                const modelB = container.querySelector('.model-name[data-model="b"]');
                
                if (modelA && result.model_a) {
                    modelA.textContent = `(${result.model_a})`;
                    modelA.classList.remove('hidden');
                }
                
                if (modelB && result.model_b) {
                    modelB.textContent = `(${result.model_b})`;
                    modelB.classList.remove('hidden');
                }
                
                // Update session for next view
                if (result.next_view_index !== undefined) {
                    sessionStorage.setItem('arena_view_index', result.next_view_index);
                }
                
                // Visual feedback
                event.currentTarget.classList.add('selected');
            }
        } catch (error) {
            console.error('Error submitting vote:', error);
            // Re-enable buttons on error
            container.querySelectorAll('.vote-btn').forEach(btn => {
                btn.disabled = false;
            });
        }
    }
    
    /**
     * Parse markdown-like content and convert to HTML
     * Handles the specific formatting from our analysis tools
     */
    parseMarkdownContent(content) {
        if (!content) return '';
        
        let text = typeof content === 'string' ? content : String(content);
        
        console.log('🔍 MARKDOWN DEBUG: Original length:', text.length);
        console.log('🔍 MARKDOWN DEBUG: Contains headers:', /^##/gm.test(text));
        console.log('🔍 MARKDOWN DEBUG: Contains bold:', /\*\*/.test(text));
        console.log('🔍 MARKDOWN DEBUG: Contains bullets:', /^[•-]/gm.test(text));
        console.log('🔍 MARKDOWN DEBUG: Contains iframe:', /<iframe/.test(text));
        
        // Step 0: Preserve iframes and other HTML tags that should not be processed
        const iframePattern = /<iframe[^>]*>.*?<\/iframe>/gis;
        const iframes = [];
        let iframeIndex = 0;
        
        // Extract iframes temporarily
        text = text.replace(iframePattern, (match) => {
            iframes.push(match);
            return `__IFRAME_PLACEHOLDER_${iframeIndex++}__`;
        });
        
        // Step 1: Convert headers (more specific matching)
        text = text.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
        text = text.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
        text = text.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
        
        // Step 2: Convert bold text (non-greedy)
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Step 3: Convert links
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        
        // Step 4: Handle bullet points more carefully (including indented bullets)
        text = text.replace(/^\s*[•\-] (.+)$/gm, '<li>$1</li>');
        
        // Step 5: Wrap consecutive list items in ul tags
        text = text.replace(/(<li>.*?<\/li>(?:\s*<li>.*?<\/li>)*)/gs, '<ul>$1</ul>');
        
        // Step 6: Handle line breaks and paragraphs
        // First, ensure bullets are on separate lines (handle indented bullets too)
        text = text.replace(/([^\n])(\s{3,}•)/g, '$1\n$2');  // Add newline before indented bullets
        text = text.replace(/([^\n])(•)/g, '$1\n$2');  // Add newline before non-indented bullets
        
        // Split by double newlines for paragraphs
        const paragraphs = text.split(/\n\s*\n/);
        text = paragraphs.map(paragraph => {
            // Don't wrap headers, lists, iframe placeholders, or already wrapped content
            if (paragraph.includes('<h') || paragraph.includes('<ul') || 
                paragraph.includes('__IFRAME_PLACEHOLDER_') || paragraph.startsWith('<')) {
                return paragraph;  // Don't remove newlines from lists
            } else {
                // Always preserve line breaks in paragraphs
                return '<p>' + paragraph.replace(/\n/g, '<br>') + '</p>';
            }
        }).join('\n\n');
        
        // Step 7: Restore iframes
        iframes.forEach((iframe, index) => {
            text = text.replace(`__IFRAME_PLACEHOLDER_${index}__`, iframe);
        });
        
        console.log('🔍 MARKDOWN DEBUG: Final length:', text.length);
        console.log('🔍 MARKDOWN DEBUG: Final preview:', text.substring(0, 300));
        
        return text;
    }

    appendMessage(messageElement) {
        console.log('📝 appendMessage called with element:', messageElement);
        console.log('📝 chatContainer exists?', !!this.chatContainer);
        
        if (this.chatContainer) {
            console.log('📝 Appending element to chat container');
            // FIXED: Simplified scroll logic - single source of truth
            const wasScrolledToBottom = this.isScrolledToBottom();
            
            this.chatContainer.appendChild(messageElement);
            console.log('📝 Element appended successfully');
            console.log('📝 Chat container now has', this.chatContainer.children.length, 'children');
            
            // FIXED: Direct scroll control without redundant checks
            if (wasScrolledToBottom) {
                // User was at bottom, maintain that position
                DOMHelpers.scrollToBottom(this.chatContainer);
            }
            // If user was not at bottom, let them stay where they were (don't interfere)
            
            setTimeout(() => {
                DOMHelpers.removeClass(messageElement, 'new-message');
            }, 500);
        } else {
            console.error('📝 ERROR: chatContainer is null!');
        }
    }

    showTypingIndicator() {
        this.hideTypingIndicator();
        
        // FIXED: Enhanced loading indicator with better visual feedback
        const typingDiv = DOMHelpers.createElement('div', {
            id: 'typing-indicator',
            className: 'typing-indicator enhanced'
        }, `
            <div class="typing-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="typing-content">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
                <div class="typing-text">ChatMRPT is thinking...</div>
            </div>
        `);

        if (this.chatContainer) {
            this.chatContainer.appendChild(typingDiv);
            // FIXED: Don't force scroll when showing typing indicator
            // Let appendMessage handle scroll logic consistently
        }
    }

    hideTypingIndicator() {
        const typingIndicator = DOMHelpers.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    autoResizeInput() {
        if (this.messageInput) {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 200) + 'px';
        }
    }

    scrollToBottom() {
        if (this.chatContainer) {
            // FIXED: Simplified - just scroll to bottom when called
            // All logic moved to appendMessage for centralized control
            DOMHelpers.scrollToBottom(this.chatContainer);
        }
    }
    
    /**
     * CRITICAL FIX: Check if user is scrolled to bottom
     * @returns {boolean} True if scrolled to bottom
     */
    isScrolledToBottom() {
        if (!this.chatContainer) return true;
        
        const threshold = 50; // FIXED: Reduced from 100px - less aggressive auto-scroll
        const scrollTop = this.chatContainer.scrollTop;
        const scrollHeight = this.chatContainer.scrollHeight;
        const clientHeight = this.chatContainer.clientHeight;
        
        return scrollHeight - scrollTop - clientHeight < threshold;
    }

    clearChat() {
        if (this.chatContainer) {
            // CRITICAL FIX: Store reference to prevent accidental clearing
            const messages = this.chatContainer.querySelectorAll('.message');
            console.log(`🧹 Clearing ${messages.length} messages from chat`);
            DOMHelpers.clearChildren(this.chatContainer);
        }
    }

    scrollToTop() {
        if (this.chatContainer) {
            this.chatContainer.scrollTop = 0;
            console.log('🔝 Scrolled to top of chat');
        }
    }
    
    /**
     * CRITICAL FIX: Get all messages count for debugging
     * @returns {number} Number of messages in chat
     */
    getMessageCount() {
        if (!this.chatContainer) return 0;
        return this.chatContainer.querySelectorAll('.message').length;
    }
    
    /**
     * CRITICAL FIX: Debug scroll information
     */
    debugScrollInfo() {
        if (!this.chatContainer) return;
        
        console.log('📊 SCROLL DEBUG INFO:');
        console.log('- Container height:', this.chatContainer.clientHeight);
        console.log('- Scroll height:', this.chatContainer.scrollHeight);
        console.log('- Scroll top:', this.chatContainer.scrollTop);
        console.log('- Is scrolled to bottom:', this.isScrolledToBottom());
        console.log('- Messages count:', this.getMessageCount());
        console.log('- Container overflow-y:', getComputedStyle(this.chatContainer).overflowY);
    }
} 
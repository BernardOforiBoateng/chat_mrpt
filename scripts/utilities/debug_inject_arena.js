// Debug script to inject Arena response directly into the page
// Run this in browser console to test Arena display

(function() {
    console.log('🔍 Starting Arena injection test...');
    
    // Check if message handler exists
    if (typeof window.chatManager === 'undefined') {
        console.error('❌ Chat manager not found! Page may not be fully loaded.');
        return;
    }
    
    const messageHandler = window.chatManager?.messageHandler;
    if (!messageHandler) {
        console.error('❌ Message handler not found!');
        return;
    }
    
    console.log('✅ Message handler found:', messageHandler);
    
    // Check if createDualMessageElement exists
    if (typeof messageHandler.createDualMessageElement !== 'function') {
        console.error('❌ createDualMessageElement function not found!');
        console.log('Available methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(messageHandler)));
        return;
    }
    
    console.log('✅ createDualMessageElement function exists');
    
    // Test creating a dual message element
    try {
        const testResponseA = "This is a test response from Model A. It should display properly.";
        const testResponseB = "This is a test response from Model B. It should also display properly.";
        const testBattleId = "test-battle-123";
        const testViewIndex = 0;
        
        console.log('🎯 Creating dual message element...');
        const dualElement = messageHandler.createDualMessageElement(
            testResponseA,
            testResponseB,
            testBattleId,
            testViewIndex
        );
        
        if (!dualElement) {
            console.error('❌ Failed to create dual element');
            return;
        }
        
        console.log('✅ Dual element created:', dualElement);
        
        // Try to append it to the chat
        const chatContainer = document.getElementById('chatContainer');
        if (!chatContainer) {
            console.error('❌ Chat container not found');
            return;
        }
        
        console.log('📌 Appending to chat container...');
        chatContainer.appendChild(dualElement);
        
        // Scroll to the new element
        dualElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
        
        console.log('✅ Arena response injected successfully!');
        console.log('Check if you can see the dual response in the chat.');
        
        // Also test with actual Arena data format
        const mockArenaChunk = {
            arena_mode: true,
            battle_id: 'mock-battle-456',
            response_a: 'This is a mock Arena response from Model A (llama3.2-3b)',
            response_b: 'This is a mock Arena response from Model B (phi3-mini)',
            model_a: 'llama3.2-3b',
            model_b: 'phi3-mini',
            view_index: 1,
            done: true
        };
        
        console.log('\n🎮 Testing with Arena chunk format...');
        console.log('Mock chunk:', mockArenaChunk);
        
        // Simulate the onChunk callback
        if (mockArenaChunk.arena_mode === true) {
            console.log('✅ Arena mode detected');
            
            if (mockArenaChunk.response_a && mockArenaChunk.response_b) {
                const arenaElement = messageHandler.createDualMessageElement(
                    mockArenaChunk.response_a,
                    mockArenaChunk.response_b,
                    mockArenaChunk.battle_id,
                    mockArenaChunk.view_index || 0
                );
                
                if (arenaElement) {
                    chatContainer.appendChild(arenaElement);
                    console.log('✅ Arena element added to chat');
                    
                    // Store model names
                    if (mockArenaChunk.model_a && mockArenaChunk.model_b) {
                        sessionStorage.setItem(`battle_${mockArenaChunk.battle_id}_models`, JSON.stringify({
                            model_a: mockArenaChunk.model_a,
                            model_b: mockArenaChunk.model_b
                        }));
                        console.log('✅ Model names stored in sessionStorage');
                    }
                }
            }
        }
        
    } catch (error) {
        console.error('❌ Error during injection:', error);
        console.error(error.stack);
    }
})();
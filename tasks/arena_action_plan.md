# Arena System Action Plan - Step-by-Step Implementation

## Problem Summary
Your Arena system with 5 local models + OpenAI for tools is failing due to:
- Frontend assets mismatch (React build issues)
- Missing JavaScript modules 
- VLLM GPU server offline
- No proper fallback to Ollama
- Incomplete Arena UI implementation

## Step-by-Step Fix Plan

### Step 1: Fix Immediate Frontend Issues
**Problem**: React assets don't match template references
**Solution**: Update template to use correct asset files

```bash
# Deploy to both production instances
for ip in 3.21.167.170 18.220.103.20; do
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$ip '
        cd /home/ec2-user/ChatMRPT
        # Backup current template
        cp app/templates/index.html app/templates/index.html.backup
        
        # Fix asset references
        sed -i "s/index-CWTdV2HE.js/index-BzinXmdJ.js/g" app/templates/index.html
        sed -i "s/index-tn0RQdqM.css/index-Df_PMFRb.css/g" app/templates/index.html
        
        # Restart service
        sudo systemctl restart chatmrpt
    '
done
```

### Step 2: Update Arena Manager for Ollama
**Problem**: Arena expects VLLM but needs to use Ollama
**Solution**: Modify arena_routes.py to use Ollama backend

Create file: `app/core/ollama_adapter.py`
```python
import aiohttp
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class OllamaAdapter:
    """Adapter for Ollama models in Arena mode"""
    
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.model_mapping = {
            'llama3.2-3b': 'llama3.1:8b',  # Map to available model
            'phi3-mini': 'phi3:mini',
            'qwen2.5-3b': 'qwen3:8b',
            'mistral-7b': 'mistral:7b',
            'gemma2-2b': 'mistral:7b'  # Fallback since gemma not available
        }
    
    async def generate_async(self, model: str, prompt: str) -> str:
        """Generate response from Ollama model"""
        actual_model = self.model_mapping.get(model, model)
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": actual_model,
                "prompt": prompt,
                "stream": False
            }
            
            try:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('response', '')
                    else:
                        logger.error(f"Ollama error: {response.status}")
                        return f"Error: Model {actual_model} returned {response.status}"
            except Exception as e:
                logger.error(f"Ollama generation failed: {e}")
                return f"Error: {str(e)}"
```

### Step 3: Update Arena Routes
**Problem**: Routes expect VLLM, need Ollama fallback
**Solution**: Modify get_battle_responses in arena_routes.py

Update section in `app/web/routes/arena_routes.py` (lines 188-216):
```python
async def get_model_response(model_name: str, position: str):
    """Get response from a specific model."""
    start_time = time.time()
    
    try:
        # Check if it's OpenAI (for tool-calling)
        if model_name == 'gpt-4o':
            from app.core.llm_adapter import LLMAdapter
            adapter = LLMAdapter(backend='openai')
            response = await adapter.generate_async(user_message)
        else:
            # Use Ollama for local models
            from app.core.ollama_adapter import OllamaAdapter
            adapter = OllamaAdapter()
            response = await adapter.generate_async(model_name, user_message)
        
        latency = (time.time() - start_time) * 1000  # ms
        
        # Submit to arena manager
        await arena_manager.submit_response(
            battle_id, position, response, latency
        )
        
        responses[f'response_{position}'] = response
        latencies[f'latency_{position}'] = latency
        
    except Exception as e:
        logger.error(f"Error getting response from {model_name}: {e}")
        responses[f'response_{position}'] = f"Error: {str(e)}"
        latencies[f'latency_{position}'] = 0
```

### Step 4: Create Minimal Arena Frontend
**Problem**: No arena UI components
**Solution**: Create basic arena interface

Create file: `app/static/js/arena-handler.js`
```javascript
class ArenaHandler {
    constructor() {
        this.currentBattleId = null;
        this.currentView = 0;
        this.totalViews = 3;
        this.responses = [];
        this.modelsRevealed = false;
    }
    
    async startBattle(message) {
        try {
            const response = await fetch('/api/arena/start_battle', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message, view_index: this.currentView })
            });
            
            const data = await response.json();
            this.currentBattleId = data.battle_id;
            
            // Get responses
            await this.getResponses(message);
        } catch (error) {
            console.error('Failed to start battle:', error);
        }
    }
    
    async getResponses(message) {
        const response = await fetch('/api/arena/get_responses', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                battle_id: this.currentBattleId,
                message: message
            })
        });
        
        const data = await response.json();
        this.displayResponses(data);
    }
    
    displayResponses(data) {
        // Create dual response display
        const container = document.getElementById('chat-messages');
        
        const arenaDiv = document.createElement('div');
        arenaDiv.className = 'arena-responses';
        arenaDiv.innerHTML = `
            <div class="arena-header">
                <h3>Arena Mode - View ${this.currentView + 1}/${this.totalViews}</h3>
                <button onclick="arenaHandler.nextView()">Next ></button>
            </div>
            <div class="arena-models">
                <div class="model-response left">
                    <h4>Model A ${this.modelsRevealed ? '(' + data.model_a + ')' : ''}</h4>
                    <div class="response-content">${data.response_a}</div>
                    <div class="response-stats">⚡ ${data.latency_a}ms</div>
                </div>
                <div class="model-response right">
                    <h4>Model B ${this.modelsRevealed ? '(' + data.model_b + ')' : ''}</h4>
                    <div class="response-content">${data.response_b}</div>
                    <div class="response-stats">⚡ ${data.latency_b}ms</div>
                </div>
            </div>
            <div class="arena-voting">
                <button onclick="arenaHandler.vote('left')">👈 A is Better</button>
                <button onclick="arenaHandler.vote('tie')">🤝 Tie</button>
                <button onclick="arenaHandler.vote('right')">👉 B is Better</button>
                <button onclick="arenaHandler.vote('both_bad')">👎 Both Bad</button>
            </div>
        `;
        
        container.appendChild(arenaDiv);
    }
    
    async vote(preference) {
        const response = await fetch('/api/arena/vote', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                battle_id: this.currentBattleId,
                preference: preference
            })
        });
        
        const data = await response.json();
        // Reveal models after voting
        this.modelsRevealed = true;
        this.updateModelDisplay(data.models_revealed);
    }
    
    nextView() {
        this.currentView = (this.currentView + 1) % this.totalViews;
        // Start new battle with next view
        const lastMessage = document.querySelector('#user-input').value;
        this.startBattle(lastMessage);
    }
}

// Initialize
const arenaHandler = new ArenaHandler();
```

### Step 5: Add Arena CSS
Create file: `app/static/css/arena.css`
```css
.arena-responses {
    margin: 20px 0;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
}

.arena-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.arena-models {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
}

.model-response {
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 15px;
    background: #f9f9f9;
}

.model-response.left {
    border-left: 3px solid #4CAF50;
}

.model-response.right {
    border-left: 3px solid #2196F3;
}

.response-content {
    margin: 10px 0;
    line-height: 1.6;
}

.response-stats {
    font-size: 0.85em;
    color: #666;
    margin-top: 10px;
}

.arena-voting {
    display: flex;
    justify-content: center;
    gap: 10px;
}

.arena-voting button {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    background: #007bff;
    color: white;
    cursor: pointer;
    transition: background 0.3s;
}

.arena-voting button:hover {
    background: #0056b3;
}
```

### Step 6: Deploy All Fixes

Create deployment script: `deploy_arena_fixes.sh`
```bash
#!/bin/bash

# Production IPs
INSTANCES="3.21.167.170 18.220.103.20"

echo "Deploying Arena fixes to production..."

for IP in $INSTANCES; do
    echo "Deploying to $IP..."
    
    # Copy new files
    scp -i ~/.ssh/chatmrpt-key.pem \
        app/core/ollama_adapter.py \
        app/static/js/arena-handler.js \
        app/static/css/arena.css \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/
    
    # Apply on server
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$IP '
        cd /home/ec2-user/ChatMRPT
        
        # Move files to correct locations
        mv app/ollama_adapter.py app/core/
        mkdir -p app/static/js app/static/css
        mv app/arena-handler.js app/static/js/
        mv app/arena.css app/static/css/
        
        # Update arena routes (backup first)
        cp app/web/routes/arena_routes.py app/web/routes/arena_routes.py.backup
        
        # Restart service
        sudo systemctl restart chatmrpt
        
        # Check status
        sudo systemctl status chatmrpt | head -10
    '
done

echo "Deployment complete!"
```

### Step 7: Test Arena System

Test script: `test_arena.py`
```python
import requests
import json

BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test_arena():
    # Test arena status
    print("Testing arena status...")
    response = requests.get(f"{BASE_URL}/api/arena/status")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    # Test battle start
    print("\nStarting battle...")
    response = requests.post(
        f"{BASE_URL}/api/arena/start_battle",
        json={"message": "What is the capital of France?"}
    )
    battle_data = response.json()
    print(f"Battle ID: {battle_data.get('battle_id')}")
    
    # Test get responses
    print("\nGetting responses...")
    response = requests.post(
        f"{BASE_URL}/api/arena/get_responses",
        json={
            "battle_id": battle_data['battle_id'],
            "message": "What is the capital of France?"
        }
    )
    print(f"Response A length: {len(response.json().get('response_a', ''))}")
    print(f"Response B length: {len(response.json().get('response_b', ''))}")

if __name__ == "__main__":
    test_arena()
```

## Priority Order

1. **IMMEDIATE** (Do Now):
   - Fix React asset references (Step 1)
   - Create Ollama adapter (Step 2)
   - Deploy to both instances

2. **TODAY**:
   - Update arena routes (Step 3)
   - Create minimal frontend (Step 4-5)
   - Deploy and test

3. **TOMORROW**:
   - Fix VLLM GPU server OR
   - Set up new GPU instance
   - Implement model preloading

4. **THIS WEEK**:
   - Build full React arena components
   - Add streaming support
   - Implement analytics dashboard

## Success Metrics
- [ ] Arena status endpoint returns 200
- [ ] Models load and respond within 10 seconds
- [ ] Dual responses display correctly
- [ ] Voting system records preferences
- [ ] "Next >" button cycles through model pairs
- [ ] Both instances serve identical content
- [ ] CloudFront CDN properly caches static assets

## Troubleshooting Guide

If arena still doesn't work after fixes:

1. **Check Ollama models**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Check service logs**:
   ```bash
   sudo journalctl -u chatmrpt -f
   ```

3. **Verify Redis sessions**:
   ```bash
   redis-cli -h chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com ping
   ```

4. **Test model endpoints directly**:
   ```bash
   curl -X POST http://localhost:11434/api/generate \
     -d '{"model":"llama3.1:8b","prompt":"Hello"}'
   ```

5. **Check ALB health**:
   ```bash
   aws elbv2 describe-target-health \
     --target-group-arn <your-target-group-arn>
   ```

This plan will get your Arena system working with the available Ollama models while you work on restoring the VLLM GPU server.
#!/bin/bash
# Keep Arena models loaded in GPU memory to prevent slow model swapping
# Run this as a systemd service or cron job on the GPU instance

echo "Starting model warm-keeper for Arena..."
echo "This keeps all 3 models loaded in GPU memory"

# Configuration
OLLAMA_HOST="${OLLAMA_HOST:-localhost}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
MODELS=("llama3.1:8b" "mistral:7b" "qwen3:8b")
KEEP_ALIVE="72h"  # Keep models loaded for 72 hours
WARMUP_INTERVAL=300  # Ping models every 5 minutes

# Function to warm a model
warm_model() {
    local model=$1
    echo "[$(date)] Warming $model..."
    curl -s -X POST "http://${OLLAMA_HOST}:${OLLAMA_PORT}/api/generate" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"${model}\",
            \"prompt\": \"test\",
            \"stream\": false,
            \"keep_alive\": \"${KEEP_ALIVE}\",
            \"options\": {
                \"num_predict\": 1
            }
        }" > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "[$(date)] ✓ $model warmed successfully"
    else
        echo "[$(date)] ✗ Failed to warm $model"
    fi
}

# Initial load of all models
echo "[$(date)] Initial loading of all models..."
for model in "${MODELS[@]}"; do
    warm_model "$model"
done

# Check current status
echo "[$(date)] Current model status:"
ollama ps

# Main loop - keep models warm
echo "[$(date)] Starting warmup loop (every ${WARMUP_INTERVAL} seconds)..."
while true; do
    sleep $WARMUP_INTERVAL

    echo "[$(date)] Running warmup cycle..."
    for model in "${MODELS[@]}"; do
        warm_model "$model" &  # Run in parallel
    done
    wait  # Wait for all warmup requests to complete

    # Show current GPU memory usage
    if command -v nvidia-smi &> /dev/null; then
        echo "[$(date)] GPU Memory Usage:"
        nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | \
            awk '{printf "  Used: %.1f GB / %.1f GB (%.1f%%)\n", $1/1024, $2/1024, ($1/$2)*100}'
    fi
done
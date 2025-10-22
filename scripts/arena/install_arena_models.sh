#!/bin/bash

# Install Arena Models Script
# Pulls all 5 required Arena models on the GPU instance

echo "========================================="
echo "Installing Arena Models"
echo "========================================="

# Array of models to install
MODELS=(
    "llama3.1:8b"
    "mistral:7b"
    "phi3:mini"
    "gemma2:9b"
    "qwen2.5:7b"
)

# Pull each model
for model in "${MODELS[@]}"; do
    echo ""
    echo "📥 Pulling $model..."
    echo "========================================="

    if ollama pull "$model"; then
        echo "✅ Successfully pulled $model"
    else
        echo "❌ Failed to pull $model"
    fi
done

echo ""
echo "========================================="
echo "Installation Complete!"
echo "========================================="

# List all models
echo ""
echo "📋 Available models:"
ollama list

# Check GPU memory
echo ""
echo "🎮 GPU Status:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
#!/bin/bash

# Setup script for Ollama models on AWS instance
# Run this on your AWS instance to ensure all required models are available

echo "======================================"
echo "Ollama Model Setup for Arena Mode"
echo "======================================"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install it first:"
    echo "curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

echo "✅ Ollama is installed"

# Start Ollama service if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &
    sleep 5
fi

echo "✅ Ollama service is running"

# Pull the 3 required models for progressive battles
echo ""
echo "Pulling required models (this may take a while)..."
echo "======================================"

# Model 1: Llama 3.1 8B
echo ""
echo "1. Pulling Llama 3.1 8B..."
ollama pull llama3.1:8b
if [ $? -eq 0 ]; then
    echo "✅ Llama 3.1 8B ready"
else
    echo "❌ Failed to pull Llama 3.1 8B"
fi

# Model 2: Mistral 7B
echo ""
echo "2. Pulling Mistral 7B..."
ollama pull mistral:7b
if [ $? -eq 0 ]; then
    echo "✅ Mistral 7B ready"
else
    echo "❌ Failed to pull Mistral 7B"
fi

# Model 3: Phi-3 Mini
echo ""
echo "3. Pulling Phi-3 Mini..."
ollama pull phi3:mini
if [ $? -eq 0 ]; then
    echo "✅ Phi-3 Mini ready"
else
    echo "❌ Failed to pull Phi-3 Mini"
fi

# List all available models
echo ""
echo "======================================"
echo "Available Ollama Models:"
echo "======================================"
ollama list

# Test each model with a simple query
echo ""
echo "======================================"
echo "Testing Models..."
echo "======================================"

echo ""
echo "Testing Llama 3.1 8B..."
echo "Hello, how are you?" | ollama run llama3.1:8b --verbose 2>/dev/null | head -n 3
echo ""

echo "Testing Mistral 7B..."
echo "Hello, how are you?" | ollama run mistral:7b --verbose 2>/dev/null | head -n 3
echo ""

echo "Testing Phi-3 Mini..."
echo "Hello, how are you?" | ollama run phi3:mini --verbose 2>/dev/null | head -n 3
echo ""

echo "======================================"
echo "✅ Ollama setup complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Ensure Ollama is accessible from outside (check security groups)"
echo "2. Set AWS_OLLAMA_HOST in your .env file to this instance's IP"
echo "3. Test the progressive arena system with test_progressive_arena.py"
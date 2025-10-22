#!/bin/bash

echo "🚀 Setting up vLLM on CPU-only t3.xlarge instance..."
echo "Note: This will be slower than GPU but better than Ollama"

# Install vLLM CPU version
pip install vllm-cpu

# Download a smaller, CPU-optimized model
echo "Downloading CPU-optimized model (Phi-3 Mini)..."
python3 -c "from transformers import AutoModelForCausalLM, AutoTokenizer; \
tokenizer = AutoTokenizer.from_pretrained('microsoft/Phi-3-mini-4k-instruct'); \
model = AutoModelForCausalLM.from_pretrained('microsoft/Phi-3-mini-4k-instruct')"

# Create vLLM service for CPU
cat > /tmp/vllm_cpu.service << 'EOF'
[Unit]
Description=vLLM CPU Model Server
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/ChatMRPT
Environment="PATH=/home/ec2-user/chatmrpt_env/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ec2-user/chatmrpt_env/bin/python -m vllm.entrypoints.openai.api_server \
    --model microsoft/Phi-3-mini-4k-instruct \
    --device cpu \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 2048
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/vllm_cpu.service /etc/systemd/system/vllm.service
sudo systemctl daemon-reload
sudo systemctl enable vllm
sudo systemctl start vllm

echo "✅ vLLM CPU setup complete!"
echo "Testing vLLM..."
sleep 5

curl -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "microsoft/Phi-3-mini-4k-instruct",
    "prompt": "What is malaria TPR?",
    "max_tokens": 50
  }'

echo ""
echo "vLLM CPU is running on port 8000"
# Installing New Arena Models on GPU Instance

## Overview
This guide explains how to install the two new models (Gemma 2 9B and Qwen 2.5 7B) on the AWS GPU instance for Arena mode.

## Prerequisites
- SSH access to the GPU instance (172.31.45.157)
- Sufficient disk space (~20GB for both models)
- Ollama service running on the instance

## Connection Details
```bash
# GPU Instance IP (private)
GPU_INSTANCE_IP=172.31.45.157

# If connecting from outside AWS, you may need to:
# 1. Connect through bastion/jump host
# 2. Or temporarily assign public IP
```

## Installation Steps

### Step 1: SSH to GPU Instance

From one of the production instances:
```bash
# First SSH to a production instance
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@3.21.167.170

# Then SSH to GPU instance (from within AWS network)
ssh ec2-user@172.31.45.157
```

### Step 2: Check Current Models
```bash
# List currently installed models
ollama list

# Expected output should show:
# - llama3.1:8b
# - mistral:7b
# - phi3:mini
```

### Step 3: Install Gemma 2 9B
```bash
# Pull Gemma 2 9B model
ollama pull gemma2:9b

# This will download ~5.5GB
# Expected output:
# pulling manifest
# pulling sha256:... 
# verifying sha256 digest
# writing manifest
# success
```

### Step 4: Install Qwen 2.5 7B
```bash
# Pull Qwen 2.5 7B model
ollama pull qwen2.5:7b

# This will download ~4.5GB
# Expected output:
# pulling manifest
# pulling sha256:...
# verifying sha256 digest
# writing manifest
# success
```

### Step 5: Verify Installation
```bash
# List all models to confirm installation
ollama list

# Should now show 5 models:
# NAME            ID              SIZE    MODIFIED
# llama3.1:8b     ...             4.7 GB  ...
# mistral:7b      ...             4.1 GB  ...
# phi3:mini       ...             2.3 GB  ...
# gemma2:9b       ...             5.5 GB  ...
# qwen2.5:7b      ...             4.5 GB  ...
```

### Step 6: Test Each Model
```bash
# Test Gemma 2
ollama run gemma2:9b "Hello, how are you?"
# Press Ctrl+D to exit

# Test Qwen 2.5
ollama run qwen2.5:7b "Hello, how are you?"
# Press Ctrl+D to exit
```

### Step 7: Check GPU Memory
```bash
# Monitor GPU usage
nvidia-smi

# Ensure there's enough VRAM for all 5 models
# Total expected: ~21GB when all loaded
```

## Troubleshooting

### If Model Pull Fails
```bash
# Check disk space
df -h

# Check Ollama service
sudo systemctl status ollama

# Restart Ollama if needed
sudo systemctl restart ollama
```

### If Out of Memory
```bash
# Remove unused models
ollama rm <model_name>

# Or increase swap space
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Testing Arena Mode

After installation, test Arena mode from the ChatMRPT interface:

1. Go to https://d225ar6c86586s.cloudfront.net
2. Click on Arena mode
3. Ask a question
4. You should now see battles between 5 models instead of 3

## Model Information

### Gemma 2 9B
- **Creator**: Google
- **Size**: 9 billion parameters
- **Strengths**: Strong reasoning, code generation, comprehension
- **Languages**: Primarily English, some multilingual capability
- **Context**: 8K tokens

### Qwen 2.5 7B
- **Creator**: Alibaba Cloud
- **Size**: 7 billion parameters  
- **Strengths**: Excellent multilingual support (140+ languages)
- **Languages**: Strong in Chinese, English, and many others
- **Context**: 128K tokens

## Rollback Instructions

If you need to remove the new models:

```bash
# Remove Gemma 2
ollama rm gemma2:9b

# Remove Qwen 2.5
ollama rm qwen2.5:7b

# Verify removal
ollama list
```

Then redeploy the original 3-model configuration files.

## Performance Considerations

- **Memory Usage**: Each model uses 4-6GB VRAM when loaded
- **Response Time**: First call to each model may be slower (model loading)
- **Concurrent Requests**: GPU can handle all 5 models simultaneously
- **Optimal Configuration**: Models are loaded on-demand and cached

## Monitoring

```bash
# Watch GPU memory in real-time
watch -n 1 nvidia-smi

# Check Ollama logs
sudo journalctl -u ollama -f

# Monitor system resources
htop
```

## Success Criteria

✅ All 5 models listed in `ollama list`
✅ Each model responds to test queries
✅ Arena mode shows 5 model options
✅ Progressive battles work with all models
✅ No out-of-memory errors

## Support

If you encounter issues:
1. Check Ollama logs: `sudo journalctl -u ollama -n 100`
2. Verify network connectivity to Ollama registry
3. Ensure GPU drivers are up to date: `nvidia-smi`
4. Check available disk space: `df -h`
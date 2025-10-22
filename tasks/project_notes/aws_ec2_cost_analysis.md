# AWS EC2 Cost Analysis for ChatMRPT
## Date: January 2025

## Current Infrastructure

### Running EC2 Instances
| Instance Name | Instance ID | Type | Purpose | Public IP | Private IP | Monthly Cost |
|--------------|-------------|------|---------|-----------|------------|--------------|
| ChatMRPT-vLLM-GPU | i-04e982a254c260972 | **g5.xlarge** | vLLM Model Server | 18.118.171.148 | 172.31.45.157 | **$734.38** |
| ChatMRPT-Staging | i-0994615951d0b9563 | t3.xlarge | Staging Server 1 | 3.21.167.170 | 172.31.46.84 | $121.47 |
| chatmrpt-staging-2 | i-0f3b25b72f18a5037 | t3.medium | Staging Server 2 | 18.220.103.20 | 172.31.24.195 | $30.37 |
| ChatMRPT-ASG | i-06d3edfcc85a1f1c7 | t3.medium | Production 1 (ASG) | 3.144.164.25 | 172.31.44.52 | $30.37 |
| ChatMRPT-Production-Server | i-0183aaf795bf8f24e | t3.medium | Production 2 | 13.59.235.255 | 172.31.43.200 | $30.37 |

### Total Current Monthly Costs
- **GPU Instance (g5.xlarge)**: $734.38/month
- **Application Servers**: $212.58/month (1 xlarge + 3 medium)
- **Total Infrastructure**: **$946.96/month**

## Instance Type Pricing (On-Demand, us-east-2)

### Standard Compute Instances
| Instance Type | vCPUs | Memory | Hourly | Monthly (24/7) | Use Case |
|--------------|-------|--------|--------|----------------|----------|
| t3.medium | 2 | 4 GB | $0.0416 | $30.37 | Light workloads |
| t3.large | 2 | 8 GB | $0.0832 | $60.74 | Medium workloads |
| t3.xlarge | 4 | 16 GB | $0.1664 | $121.47 | Heavy workloads |
| t3.2xlarge | 8 | 32 GB | $0.3328 | $242.94 | Very heavy workloads |

### GPU Instances for ML/AI
| Instance Type | GPU | VRAM | vCPUs | Memory | Hourly | Monthly | Use Case |
|--------------|-----|------|-------|--------|--------|---------|----------|
| g4dn.xlarge | NVIDIA T4 | 16GB | 4 | 16 GB | $0.526 | $384.08 | Entry-level ML |
| g4dn.2xlarge | NVIDIA T4 | 16GB | 8 | 32 GB | $0.752 | $548.96 | Better CPU for preprocessing |
| **g5.xlarge** | **NVIDIA A10G** | **24GB** | **4** | **16 GB** | **$1.006** | **$734.38** | **Current - Good for 7B models** |
| g5.2xlarge | NVIDIA A10G | 24GB | 8 | 32 GB | $1.212 | $884.76 | Multiple models |
| g5.4xlarge | NVIDIA A10G | 24GB | 16 | 64 GB | $1.624 | $1,185.12 | Large-scale inference |
| p3.2xlarge | NVIDIA V100 | 16GB | 8 | 61 GB | $3.06 | $2,233.80 | Training & fine-tuning |

## Model Hosting Requirements

### vLLM Performance on Different GPUs
| GPU | Models Capacity | Token/sec | Concurrent Users |
|-----|----------------|-----------|------------------|
| T4 (g4dn) | 1-2x 7B models | 15-25 | 5-10 |
| **A10G (g5)** | **2-3x 7B models** | **30-50** | **15-25** |
| V100 (p3) | 3-4x 7B models | 40-60 | 20-30 |

### Current g5.xlarge Capabilities
- **Running**: Qwen3-8B model
- **Can Support**: 2-3 models simultaneously with quantization
- **Performance**: 30-50 tokens/sec
- **Memory Usage**: ~8-10GB per 7B model

## Cost Optimization Strategies

### 1. Instance Rightsizing
**Current Issue**: Using g5.xlarge ($734/month) for single model
**Recommendation**: 
- Downgrade to g4dn.xlarge ($384/month) = **Save $350/month**
- Performance impact: 30-40% slower but still acceptable

### 2. Spot Instances
**Potential Savings**: 50-70% for GPU instances
- g5.xlarge Spot: ~$0.30-0.50/hour (vs $1.006 on-demand)
- Monthly Spot: ~$220-365 (vs $734)
- **Save $370-500/month**

### 3. Time-Based Scaling
**For Development/Testing**:
- Run GPU instance 12 hours/day (business hours)
- Cost: $734 * 0.5 = $367/month
- **Save $367/month**

### 4. Reserved Instances
**For Production** (1-year commitment):
- Standard Reserved: ~30% discount
- Convertible Reserved: ~20% discount
- g5.xlarge Reserved: ~$514/month
- **Save $220/month**

## Recommended Configurations

### Option 1: Production Setup (Current)
```
Total: $946.96/month
- 1x g5.xlarge (GPU): $734.38
- 1x t3.xlarge (Staging): $121.47
- 3x t3.medium (Apps): $91.11
```

### Option 2: Cost-Optimized Production
```
Total: $535.66/month (-43%)
- 1x g4dn.xlarge (GPU): $384.08
- 4x t3.medium (Apps): $121.48
- Storage: $30.10
Savings: $411.30/month
```

### Option 3: Development/Testing
```
Total: $297.33/month (-69%)
- 1x g4dn.xlarge Spot (12hr/day): $115.22
- 4x t3.medium: $121.48
- Stop instances on weekends
Savings: $649.63/month
```

### Option 4: Hybrid Approach
```
Total: $426.75/month (-55%)
- Use Ollama for simple queries (no GPU)
- g4dn.xlarge Spot for complex queries: $192
- 4x t3.medium: $121.48
- Lambda for burst capacity: ~$113
Savings: $520.21/month
```

## Storage Costs
| Type | Price | Current Usage | Monthly Cost |
|------|-------|--------------|--------------|
| EBS gp3 | $0.08/GB | ~375 GB (5 instances × 75GB) | $30.00 |
| EBS gp2 | $0.10/GB | Legacy volumes | $0 |
| Snapshots | $0.05/GB | Backups | ~$10 |

## Data Transfer Costs
- **Inbound**: Free
- **Outbound to Internet**: $0.09/GB after 1GB free
- **Between AZs**: $0.01/GB each direction
- **Estimated Monthly**: $20-50 (depending on usage)

## Arena Mode Specific Costs

### Running 3 Models for Comparison
**Current g5.xlarge can handle**:
- Llama 3.1 8B
- Mistral 7B  
- Qwen 2.5 7B

**Memory allocation**:
- Each model: ~8GB VRAM
- Total needed: 24GB (fits in A10G's 24GB)

### Cost per Model Query
```
GPU Hour Cost: $1.006
Queries per hour: ~500-1000
Cost per query: $0.001-0.002
Cost per 1000 queries: $1-2
```

## Recommendations

### Immediate Actions (Save $350/month)
1. **Downgrade GPU**: g5.xlarge → g4dn.xlarge
2. **Impact**: 30% slower but acceptable for current load
3. **Implementation**: 1 hour downtime for migration

### Short-term (Save $500+/month)
1. **Enable Spot Instances** for GPU
2. **Implement auto-shutdown** for non-business hours
3. **Consolidate staging**: Merge t3.xlarge + t3.medium

### Long-term (Save $600+/month)
1. **Reserved Instances** for stable workloads
2. **Implement caching** to reduce GPU queries
3. **Use Lambda** for simple queries
4. **Consider Bedrock** for managed inference

## Monthly Cost Projections

### Current State
- Monthly: $946.96
- Annual: $11,363.52

### After Optimization
- Monthly: $426.75 (-55%)
- Annual: $5,121.00
- **Annual Savings: $6,242.52**

## Decision Matrix

| Factor | Keep g5.xlarge | Switch to g4dn | Spot Instances | Hybrid (Ollama+GPU) |
|--------|---------------|----------------|----------------|---------------------|
| Cost | $734/mo | $384/mo | $220-365/mo | $300/mo |
| Performance | 50 tok/s | 25 tok/s | 50 tok/s | Variable |
| Reliability | 99.99% | 99.99% | 95% | 99% |
| Models | 3 concurrent | 2 concurrent | 3 concurrent | Unlimited |
| Complexity | Low | Low | Medium | High |
| **Recommendation** | Current | ✅ Best Value | Dev/Test Only | Research |

## Conclusion

**Current monthly spend**: $946.96
**Recommended optimization**: Switch to g4dn.xlarge
**Projected monthly spend**: $596.66
**Monthly savings**: $350.30 (37%)
**Annual savings**: $4,203.60

The g5.xlarge is overpowered for current needs. A g4dn.xlarge would provide sufficient performance for Arena mode with 2-3 models while cutting GPU costs by 48%.
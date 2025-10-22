=================================================================
AWS INFRASTRUCTURE ANALYSIS - STAGING TO PRODUCTION TRANSITION
=================================================================

📊 GATHERING ENVIRONMENT DATA...

## 1. CURRENT STAGING ENVIRONMENT
=================================

### Staging Instances:
- **Instance 1**: i-0994615951d0b9563 
  - Public IP: 3.21.167.170
  - Private IP: 172.31.46.84
  - Security Group: sg-0b21586985a0bbfbe
  
- **Instance 2**: i-0f3b25b72f18a5037
  - Public IP: 18.220.103.20  
  - Private IP: 172.31.24.195
  - Security Group: sg-0a003f4d6500485b9

### Staging Infrastructure:
- **ALB**: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com
- **Redis**: chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379
- **Region**: us-east-2

## 2. CURRENT PRODUCTION ENVIRONMENT
=====================================

### Production Instances:
- **Instance 1**: i-06d3edfcc85a1f1c7
  - Private IP: 172.31.44.52
  
- **Instance 2**: i-0183aaf795bf8f24e  
  - Private IP: 172.31.43.200

### Production Infrastructure:
- **CloudFront**: https://d225ar6c86586s.cloudfront.net
- **ALB**: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com
- **Redis**: chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com:6379
- **Region**: us-east-2


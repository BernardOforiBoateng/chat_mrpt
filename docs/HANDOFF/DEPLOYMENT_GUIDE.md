# Deployment Guide (Production AWS)

Source: `CLAUDE.md` — summarized here for speed. Always deploy to ALL instances.

Active infrastructure:
- CloudFront: https://d225ar6c86586s.cloudfront.net
- ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com
- Instances: 3.21.167.170, 18.220.103.20
- Redis (ElastiCache): chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379

One-command deploy (preferred):
```bash
./deployment/deploy_to_production.sh
```

Manual deploy (both instances):
```bash
for ip in 3.21.167.170 18.220.103.20; do
  scp -i ~/.ssh/chatmrpt-key.pem -r app/ docs/ tests/ ec2-user@$ip:/home/ec2-user/ChatMRPT/
  ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$ip 'sudo systemctl restart chatmrpt'
done
```

Flags to set on instances:
- `CHATMRPT_INTENT_ROUTER=1`
- `CHATMRPT_ROUTER_OBS=1`
- `CHATMRPT_CHOICE_RESOLVER=1`
- `CHATMRPT_ANALYZE_TIMEOUT_MS=25000`
- Optional: `CHATMRPT_USE_REDIS_MEMORY=1` (+ `REDIS_HOST`, `REDIS_PORT`, credentials)

Post-deploy checks:
```bash
sudo systemctl status chatmrpt
sudo journalctl -u chatmrpt -f
curl -s http://localhost:8000/ping
```

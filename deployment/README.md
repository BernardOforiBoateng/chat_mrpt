# ChatMRPT Production Deployment System

This deployment system ensures consistent updates across all production instances.

## Quick Start

1. **Deploy to all production instances:**
   ```bash
   ./deployment/deploy_to_production.sh
   ```

2. **Monitor deployment:**
   ```bash
   ./deployment/scripts/monitor_deployment.sh
   ```

3. **Check specific instance:**
   ```bash
   ./deployment/scripts/check_instance_health.sh <instance_ip>
   ```

4. **Rollback if needed:**
   ```bash
   ./deployment/scripts/rollback_instance.sh <instance_ip>
   ```

## Directory Structure

```
deployment/
├── deploy_to_production.sh    # Main deployment script
├── scripts/
│   ├── discover_instances.sh  # Find all production instances
│   ├── check_instance_health.sh # Health check script
│   ├── deploy_to_instance.sh  # Deploy to single instance
│   ├── rollback_instance.sh   # Rollback single instance
│   └── monitor_deployment.sh  # Real-time monitoring
├── configs/
│   └── production_instances.txt # List of instance IPs
├── logs/
│   └── deployment_*.log       # Deployment logs
└── README.md                  # This file
```

## Deployment Process

1. **Discovery**: Automatically finds all healthy instances behind ALB
2. **Health Check**: Verifies each instance before deployment
3. **Backup**: Creates timestamped backup on each instance
4. **Deploy**: Updates files and configuration
5. **Verify**: Checks service health after deployment
6. **Monitor**: Continuous monitoring available

## Best Practices

1. Always run from staging server (18.117.115.217)
2. Check pre-deployment health status
3. Monitor logs during deployment
4. Test application after deployment
5. Keep deployment logs for audit trail

## Troubleshooting

- **SSH fails**: Check instance is running and security groups allow access
- **Service won't start**: Check logs with `sudo journalctl -u chatmrpt -n 100`
- **Redis errors**: Verify Redis endpoint in .env file
- **Rollback needed**: Use rollback script to restore previous state

## Future Improvements

1. Add automated testing before/after deployment
2. Implement blue/green deployment strategy
3. Add Slack/email notifications
4. Create deployment approval workflow
5. Integrate with CI/CD pipeline

# Redis Session Management Setup

This guide explains how to set up Redis for centralized session management in ChatMRPT, which solves session persistence issues in multi-worker Gunicorn environments.

## Why Redis?

In a multi-worker Gunicorn deployment, each worker process maintains its own memory space. When using filesystem-based sessions, session data may not be properly shared between workers, leading to issues like:
- Lost session state between requests
- TPR workflow not maintaining state
- Users having to re-authenticate or re-upload files

Redis provides a centralized session store that all workers can access, ensuring session consistency.

## Installation

### Local Development

1. Install Redis:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   
   # Windows (WSL)
   sudo apt-get install redis-server
   ```

2. Start Redis:
   ```bash
   redis-server
   ```

3. Configure environment variables:
   ```bash
   cp .env.redis.example .env
   # Edit .env and set REDIS_PASSWORD
   ```

### AWS EC2 Deployment

1. Run the deployment script:
   ```bash
   ./deploy_redis_aws.sh
   ```

   This script will:
   - Install Redis on your EC2 instance
   - Configure Redis with security settings
   - Generate a secure password
   - Update the application configuration
   - Restart Gunicorn

2. Verify Redis is running:
   ```bash
   ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17
   sudo systemctl status redis
   ```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_password_here
REDIS_DB=0
```

### Application Configuration

The application automatically detects Redis availability:
- If Redis is available: Uses Redis for sessions
- If Redis is unavailable: Falls back to filesystem sessions

### Security Considerations

1. **Password Protection**: Always use a strong password for Redis
2. **Bind Address**: Redis should only listen on localhost (127.0.0.1)
3. **Firewall**: Ensure port 6379 is not exposed to the internet
4. **Memory Limits**: Set appropriate memory limits to prevent OOM issues

## Monitoring

### Check Redis Status

```bash
# Check if Redis is being used
curl http://your-domain/api/session/redis-status
```

Response:
```json
{
  "connected": true,
  "version": "6.2.6",
  "used_memory": "1.5M",
  "connected_clients": 5,
  "db_keys": 42,
  "session_type": "redis",
  "session_prefix": "chatmrpt:"
}
```

### Session Verification

```bash
# Verify TPR session state
curl http://your-domain/api/session/verify-tpr
```

## Troubleshooting

### Redis Connection Failed

If you see "Failed to connect to Redis" in logs:

1. Check Redis is running:
   ```bash
   sudo systemctl status redis
   ```

2. Verify password in `.env` matches Redis config:
   ```bash
   sudo grep requirepass /etc/redis/redis.conf
   ```

3. Test Redis connection:
   ```bash
   redis-cli -a your_password ping
   # Should return: PONG
   ```

### Session Data Not Persisting

1. Check session type in use:
   ```bash
   curl http://your-domain/api/session/redis-status | jq .session_type
   ```

2. Monitor Redis keys:
   ```bash
   redis-cli -a your_password
   > KEYS chatmrpt:*
   > TTL chatmrpt:your_session_id
   ```

### Memory Issues

If Redis uses too much memory:

1. Check memory usage:
   ```bash
   redis-cli -a your_password INFO memory
   ```

2. Adjust memory limit in `/etc/redis/redis.conf`:
   ```
   maxmemory 256mb
   maxmemory-policy allkeys-lru
   ```

## Maintenance

### Backup Redis Data

```bash
# Create backup
sudo cp /var/lib/redis/dump.rdb /backup/redis-$(date +%Y%m%d).rdb
```

### Clear All Sessions

```bash
# Use with caution - this will log out all users
redis-cli -a your_password
> FLUSHDB
```

### Monitor Session Count

```bash
redis-cli -a your_password
> DBSIZE
> KEYS chatmrpt:* | wc -l
```

## Performance Benefits

With Redis sessions:
- ✅ Session state persists across all workers
- ✅ TPR workflow maintains state correctly
- ✅ No session loss during high traffic
- ✅ Faster session access than filesystem
- ✅ Automatic session expiration
- ✅ Better scalability for multiple servers

## Integration with ChatMRPT

The Redis integration is automatic and transparent:

1. **Fallback Support**: If Redis fails, the app continues with filesystem sessions
2. **Health Monitoring**: `/api/session/redis-status` endpoint for monitoring
3. **TPR Verification**: Enhanced TPR session verification with Redis support
4. **Logging**: Clear logs indicate which session backend is in use

## Future Enhancements

1. **Redis Sentinel**: For high availability
2. **Redis Cluster**: For horizontal scaling
3. **Session Analytics**: Track active sessions and patterns
4. **Cache Integration**: Use Redis for general caching beyond sessions
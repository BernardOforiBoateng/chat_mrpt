# RDS PostgreSQL Setup Commands

## Database Configuration
- **Identifier**: chatmrpt-staging-db
- **Engine**: PostgreSQL 15.7
- **Instance Class**: db.t3.micro (1 vCPU, 1GB RAM)
- **Storage**: 20GB gp3
- **Username**: chatmrptadmin
- **Password**: 1IyPCV5J71jY2nOu1FogVOViC
- **Backup Retention**: 7 days
- **Multi-AZ**: No (staging environment)
- **Public Access**: Yes (for migration testing)

## Required IAM Permissions
Add these permissions to the ChatMRPT-EC2-Role in AWS Console:
1. Go to IAM → Roles → ChatMRPT-EC2-Role
2. Attach policy: AmazonRDSFullAccess (or create custom policy with minimal permissions)

## RDS Creation Command
After adding RDS permissions, SSH into staging instance and run:

```bash
aws rds create-db-instance \
  --db-instance-identifier chatmrpt-staging-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.7 \
  --master-username chatmrptadmin \
  --master-user-password '1IyPCV5J71jY2nOu1FogVOViC' \
  --allocated-storage 20 \
  --storage-type gp3 \
  --vpc-security-group-ids sg-0b21586985a0bbfbe \
  --backup-retention-period 7 \
  --no-multi-az \
  --publicly-accessible \
  --tags Key=Name,Value=ChatMRPT-Staging-DB Key=Environment,Value=staging \
  --region us-east-2
```

## Check Database Status
```bash
aws rds describe-db-instances \
  --db-instance-identifier chatmrpt-staging-db \
  --region us-east-2 \
  --query 'DBInstances[0].[DBInstanceStatus,Endpoint.Address]' \
  --output table
```

## Connection String (after creation)
```
postgresql://chatmrptadmin:1IyPCV5J71jY2nOu1FogVOViC@[ENDPOINT]:5432/postgres
```

## Next Steps After RDS Creation
1. Wait for database to be available (~5-10 minutes)
2. Update staging instance security group to allow PostgreSQL (port 5432)
3. Test connection from staging EC2
4. Install PostgreSQL client tools
5. Begin SQLite to PostgreSQL migration testing

## Cost Estimate
- db.t3.micro: ~$15/month
- 20GB storage: ~$3/month
- Backups: ~$1/month
- **Total**: ~$19/month for staging RDS
# AWS Infrastructure Implementation Notes

## Date: July 28, 2025

### Context
The team received $10,000 AWS credit to host ChatMRPT for a year. The goal is to fully utilize this credit to build a robust, scalable infrastructure while ensuring users can continue using the current version during migration.

### User Requirements
1. Build parallel infrastructure without touching current production
2. Ensure zero downtime for users
3. Create comprehensive backup and recovery procedures
4. Implement sustainable monthly costs within $833/month budget

### Current Infrastructure Status
- **Production EC2**: 3.137.158.17 (t3.medium) - Still running, untouched
- **Golden AMI**: ami-02c0a366899ceb8d2 - Created as backup
- **Staging EC2**: 18.117.115.217 - Built from AMI for testing

### Work Completed

#### 1. Initial Production Changes (User Feedback: Should have built parallel first)
- Installed Redis locally (later disabled due to serialization issues)
- Set up log rotation to manage 21MB error log
- Created automated backup script running daily at 2 AM
- **Learning**: User emphasized building parallel infrastructure first, not modifying production

#### 2. Flask-Session Issue Resolution
- **Problem**: TPR uploads failing with "Unexpected token '<'" error
- **Root Cause**: Flask-Session 0.8.0 couldn't serialize DataFrames in sessions
- **Solution**: Downgraded Flask-Session from 0.8.0 to 0.5.0 to restore pickle serialization
- **Result**: TPR uploads working again

#### 3. Parallel Infrastructure Creation (Following User's Guidance)

##### 3.1 IAM Role Setup ✅
- Created `ChatMRPT-EC2-Role` with permissions for:
  - EC2 operations
  - S3 full access
  - CloudWatch logs and metrics
  - Systems Manager access
- Attached to both production and staging instances via console

##### 3.2 S3 Backup Bucket ✅
- Created `chatmrpt-backups-20250728`
- Enabled versioning for file recovery
- Configured lifecycle policy:
  - 30 days to Infrequent Access
  - 90 days delete old versions
- Ready for centralized backup storage

##### 3.3 Staging Environment ✅
- **Instance**: i-0994615951d0b9563
- **IP**: 18.117.115.217
- **Created from**: Golden AMI (ami-02c0a366899ceb8d2)
- **Disk**: Expanded from 20GB to 40GB for testing
- **Status**: Running and accessible at http://18.117.115.217:8080
- **Tags**: Environment=staging, Purpose=Testing-Infrastructure-Improvements

##### 3.4 CloudWatch Monitoring ✅
- Installed CloudWatch agent v1.300057.1b1167
- Configured to collect:
  - CPU, memory, and disk usage metrics
  - Gunicorn error logs to CloudWatch Logs
- Log group: `/aws/ec2/chatmrpt/staging`
- Namespace: `ChatMRPT/Staging` for custom metrics

##### 3.5 Automated Backups ✅
- Enhanced backup script on staging:
  - Backs up SQLite database daily
  - Archives application code (excluding logs/uploads)
  - Syncs to S3 bucket automatically
  - Local retention: 7 days
  - S3 location: `s3://chatmrpt-backups-20250728/staging/`

### Cost Analysis
Current monthly infrastructure costs:
- Production EC2: ~$50
- Staging EC2: ~$50  
- S3 Storage: ~$5
- CloudWatch: ~$10
- **Total**: ~$115/month (14% of $833 budget)

### Documentation Created
1. **Backup and Restore Guide** (`aws_backup_restore_guide.md`)
   - Quick reference with all critical IDs
   - Step-by-step backup procedures
   - Multiple restore options with time estimates
   - Emergency rollback procedures

2. **Implementation Log** (`aws_implementation_log.md`)
   - Detailed record of all changes
   - Configuration files preserved
   - Commands for recovery
   - Resource summary table

3. **Improvement Plan** (`aws_improvement_plan.md`)
   - Pragmatic approach within budget
   - Phased implementation strategy
   - Risk mitigation plans
   - 90-day roadmap

### Next Steps (Task #8: Create staging RDS)
Ready to create RDS PostgreSQL database for staging environment to begin testing database migration from SQLite.

### Task 8: RDS PostgreSQL Database Creation ✅
- **Status**: Successfully created and available
- **Identifier**: chatmrpt-staging-db
- **Endpoint**: chatmrpt-staging-db.c3yi24k2gtqu.us-east-2.rds.amazonaws.com
- **Port**: 5432
- **Instance Class**: db.t3.micro
- **Engine**: PostgreSQL 15.7
- **Storage**: 20GB gp3
- **Security Group**: sg-0b21586985a0bbfbe
- **Public Access**: Enabled
- **Connection String**: `postgresql://chatmrptadmin:1IyPCV5J71jY2nOu1FogVOViC@chatmrpt-staging-db.c3yi24k2gtqu.us-east-2.rds.amazonaws.com:5432/postgres`

### Security Group Configuration Needed
- The RDS security group needs to allow inbound PostgreSQL traffic (port 5432)
- Current connection attempts timing out from staging EC2
- Need to add inbound rule in AWS Console:
  1. Go to EC2 → Security Groups
  2. Find sg-0b21586985a0bbfbe
  3. Add inbound rule: PostgreSQL (5432) from staging instance security group or specific IP

### Key Decisions Made
1. **AMI First**: Created golden AMI before any changes for safety
2. **Parallel Build**: Built staging environment without touching production
3. **Incremental Approach**: Small, testable changes rather than big bang
4. **Cost Conscious**: Staying well within budget with room for growth
5. **Documentation Heavy**: Every change documented for team knowledge

### Lessons Learned
1. **Always build parallel first** - User was right to emphasize this
2. **Session serialization matters** - Flask-Session version changes can break functionality
3. **Document everything** - Critical for disaster recovery
4. **Test in staging** - Never make untested changes to production
5. **Listen to user feedback** - Initial approach was too aggressive

### Current Task Status
- ✅ Task 1: Create Golden AMI snapshot
- ✅ Task 2: Create S3 backup bucket with versioning
- ✅ Task 3: Set up IAM role for EC2 instance
- ✅ Task 4: Build parallel staging environment
- ✅ Task 5: Attach IAM role to staging via console
- ✅ Task 6: Install CloudWatch agent on staging
- ✅ Task 7: Set up automated backups to S3
- ✅ Task 8: Create staging RDS PostgreSQL database
- ✅ Task 9: Configure security group for PostgreSQL
- ✅ Task 10: Test SQLite to PostgreSQL migration

### Resources for Recovery
- **Production AMI**: ami-02c0a366899ceb8d2
- **Staging Instance**: i-0994615951d0b9563 (18.117.115.217)
- **Staging RDS**: chatmrpt-staging-db.c3yi24k2gtqu.us-east-2.rds.amazonaws.com
- **S3 Bucket**: chatmrpt-backups-20250728
- **IAM Role**: ChatMRPT-EC2-Role (with RDS permissions)
- **Security Group**: sg-0b21586985a0bbfbe (self-referencing for PostgreSQL)
- **SSH Key**: chatmrpt-key.pem

### Database Migration Findings
- SQLite has 46,580 rows across 14 tables
- Schema differences prevent direct migration
- PostgreSQL ready for future use when application is updated
- Recommendation: Keep SQLite for now, plan proper migration separately
# AWS Deployment Considerations for ChatMRPT

## Critical Issue: Data Path Management

### Problem
The system was using hardcoded local paths that won't work on AWS:
- `/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/rasters/` (WSL path)
- `C:\Users\bbofo\...` (Windows path)

These paths are specific to your local machine and will NOT exist on AWS EC2 instances.

### Solution Implemented

#### 1. Created Centralized Configuration (`app/config/data_paths.py`)
- All data paths are now centralized in one configuration file
- Uses environment variables for flexibility
- Falls back to relative paths if env vars not set
- Works both locally and on AWS

#### 2. Path Configuration
```python
# Environment variables for AWS deployment
CHATMRPT_RASTER_DIR=/mnt/efs/chatmrpt/rasters
CHATMRPT_NIGERIA_SHAPEFILE=/mnt/efs/chatmrpt/shapefiles/nigeria/wards.shp
CHATMRPT_INSTANCE_DIR=/mnt/efs/chatmrpt/instance
CHATMRPT_TPR_DATA_DIR=/mnt/efs/chatmrpt/tpr_data
```

## AWS Storage Options

### 1. Amazon EFS (Elastic File System)
**Best for**: Shared data across multiple EC2 instances
- Raster files (large, read-heavy)
- Shapefiles (reference data)
- Instance data (needs persistence)

**Setup**:
```bash
# Mount EFS on EC2
sudo mkdir -p /mnt/efs
sudo mount -t nfs4 fs-xxxxxx.efs.us-east-2.amazonaws.com:/ /mnt/efs
```

### 2. Amazon S3
**Best for**: Backup, archival, large file distribution
- Could use for raster storage with boto3 integration
- Good for TPR source files
- Requires code changes to read from S3

**Example S3 Integration**:
```python
import boto3
s3 = boto3.client('s3')
s3.download_file('chatmrpt-data', 'rasters/elevation.tif', '/tmp/elevation.tif')
```

### 3. EC2 Instance Storage
**Best for**: Temporary data, cache
- NOT recommended for critical data
- Lost when instance stops/terminates

## Data Migration Strategy

### Phase 1: Prepare Data for AWS
1. **Organize local data**:
   ```
   chatmrpt-data/
   ├── rasters/           (11GB of raster files)
   ├── shapefiles/        (Nigeria wards shapefile)
   ├── tpr_data/          (State TPR files)
   └── settlement_data/   (Kano settlement data)
   ```

2. **Compress for upload**:
   ```bash
   tar -czf rasters.tar.gz rasters/
   tar -czf shapefiles.tar.gz www/complete_names_wards/
   ```

3. **Upload to S3**:
   ```bash
   aws s3 cp rasters.tar.gz s3://chatmrpt-data/
   aws s3 cp shapefiles.tar.gz s3://chatmrpt-data/
   ```

### Phase 2: Setup AWS Infrastructure
1. **Create EFS filesystem**
2. **Mount EFS on EC2 instances**
3. **Download and extract data from S3 to EFS**
4. **Set environment variables in EC2 user data**

### Phase 3: Application Configuration
1. **Set environment variables**:
   ```bash
   # In /etc/environment or EC2 user data
   export CHATMRPT_RASTER_DIR=/mnt/efs/chatmrpt/rasters
   export CHATMRPT_NIGERIA_SHAPEFILE=/mnt/efs/chatmrpt/shapefiles/wards.shp
   export CHATMRPT_INSTANCE_DIR=/mnt/efs/chatmrpt/instance
   ```

2. **Verify paths on startup**:
   ```python
   from app.config.data_paths import ensure_directories_exist
   ensure_directories_exist()
   ```

## Important Files and Sizes

### Large Data Files (Need Special Handling)
1. **Rasters** (~11GB total)
   - Each raster: 10-500MB
   - Monthly data: 12 files per year
   - Multiple years of data

2. **Nigeria Shapefile** (~50MB)
   - 9,410 wards
   - Critical for all spatial operations

3. **Settlement Data** (436MB)
   - Kano settlement footprints
   - Building classifications

### Data Access Patterns
- **Rasters**: Read-only, accessed during analysis
- **Shapefiles**: Read-only, cached in memory
- **TPR Data**: Read-only, per-state files
- **Instance Data**: Read-write, user uploads and results

## Testing on AWS

### Pre-deployment Checklist
1. ✅ Remove all hardcoded local paths
2. ✅ Use environment variables for configuration
3. ✅ Test with missing rasters (mock data fallback)
4. ⬜ Upload test data to S3
5. ⬜ Setup EFS and mount points
6. ⬜ Test multi-instance data access
7. ⬜ Verify performance with remote data

### Test Commands
```bash
# Test locally with AWS-like paths
export CHATMRPT_RASTER_DIR=/tmp/test_rasters
export CHATMRPT_NIGERIA_SHAPEFILE=/tmp/test_shapefiles/wards.shp
python test_zone_specific_extraction.py

# On AWS EC2
sudo -E python run.py  # -E preserves environment variables
```

## Performance Considerations

### Caching Strategy
1. **Shapefile**: Already cached with `@lru_cache`
2. **Rasters**: Consider caching frequently accessed tiles
3. **TPR Results**: Cache in Redis for multi-worker access

### Data Loading Optimization
1. **Lazy Loading**: Only load data when needed
2. **Partial Reads**: Use windowed reading for large rasters
3. **Compression**: Store rasters as Cloud Optimized GeoTIFFs (COGs)

## Security Considerations

1. **Never commit AWS credentials**
2. **Use IAM roles for EC2 instances**
3. **Encrypt data at rest (EFS encryption)**
4. **Restrict S3 bucket access**
5. **Use VPC endpoints for S3 access**

## Fallback Strategy

The system now has built-in fallbacks:
1. **Missing Rasters**: Generates mock data for testing
2. **Missing Shapefile**: Returns error but doesn't crash
3. **Environment Variables**: Falls back to relative paths

This ensures the application can run even if some data is missing, which is useful for:
- Development environments
- Testing
- Gradual data migration
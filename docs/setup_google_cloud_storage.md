# Complete Guide: Setting Up Google Cloud Storage for Earth Engine

## Step 1: Create a Google Cloud Account

1. **Go to**: https://cloud.google.com/free
2. **Click**: "Get started for free"
3. **Sign in** with your Google account (same one you use for Earth Engine)
4. **You'll get**:
   - $300 free credit (valid for 90 days)
   - Free tier that continues after credits expire
   - No auto-charge after free trial

5. **Required info**:
   - Country
   - Agree to terms
   - Card info (for verification only - won't be charged)

## Step 2: Create Your First Project

1. **Go to**: https://console.cloud.google.com/
2. **At the top**, click the project dropdown → "NEW PROJECT"
3. **Enter**:
   - Project name: `nigeria-malaria-analysis` (or your choice)
   - Project ID: Will auto-generate (note this down!)
4. **Click**: "CREATE"
5. **Wait** ~30 seconds for project creation

## Step 3: Enable Required APIs

1. **Go to**: https://console.cloud.google.com/apis/library
2. **Search and enable these APIs**:
   - "Cloud Storage API" → Click → ENABLE
   - "Cloud Storage JSON API" → Click → ENABLE
3. These should be free/already enabled

## Step 4: Create a Storage Bucket

### Option A: Via Console (Easiest)

1. **Go to**: https://console.cloud.google.com/storage
2. **Click**: "CREATE BUCKET"
3. **Fill in**:
   - **Name**: `ndmi-ndwi-nigeria-2025` (must be globally unique!)
     - If taken, try: `ndmi-ndwi-nigeria-yourname`
   - **Location type**: Choose "Region"
   - **Region**: Choose closest to you (e.g., `us-central1` for US)
   - **Storage class**: "Standard"
   - **Access control**: "Uniform"
   - **Protection**: Leave unchecked (for cost savings)
4. **Click**: "CREATE"

### Option B: Via Google Colab

```python
# Run this in Google Colab
from google.colab import auth
auth.authenticate_user()

# Set your project ID (from Step 2)
PROJECT_ID = "nigeria-malaria-analysis"  # Replace with your project ID
!gcloud config set project {PROJECT_ID}

# Create bucket (choose unique name)
BUCKET_NAME = "ndmi-ndwi-nigeria-2025"  # Must be globally unique
!gsutil mb -p {PROJECT_ID} -c STANDARD -l US-CENTRAL1 gs://{BUCKET_NAME}/

# Verify it was created
!gsutil ls
```

## Step 5: Set Up Permissions for Earth Engine

1. **Go to**: https://console.cloud.google.com/storage/browser
2. **Click** on your bucket name
3. **Click**: "PERMISSIONS" tab
4. **Click**: "GRANT ACCESS"
5. **Add**:
   - New principals: `allUsers` (for public read) OR your email
   - Role: "Storage Object Viewer"
6. **Click**: "SAVE"

## Step 6: Get Your Bucket Path

Your bucket path will be:
```
gs://your-bucket-name/
```

For example:
```
gs://ndmi-ndwi-nigeria-2025/
```

## Step 7: Upload Files from Google Drive to Bucket

Use this Colab script:

```python
# Cell 1: Mount Drive and authenticate
from google.colab import drive, auth
drive.mount('/content/drive')
auth.authenticate_user()

# Cell 2: Set project and bucket
PROJECT_ID = "nigeria-malaria-analysis"  # Your project ID
BUCKET_NAME = "ndmi-ndwi-nigeria-2025"   # Your bucket name
!gcloud config set project {PROJECT_ID}

# Cell 3: Check your Drive files
DRIVE_FOLDER = "/content/drive/MyDrive/Nigeria_NDMI_NDWI_HLS"
!ls -la {DRIVE_FOLDER}/*.tif | head -5

# Cell 4: Upload to Cloud Storage (this will take time for 322GB)
!gsutil -m cp -r {DRIVE_FOLDER}/*.tif gs://{BUCKET_NAME}/

# Cell 5: Verify upload
!gsutil ls gs://{BUCKET_NAME}/ | head -10
!gsutil du -sh gs://{BUCKET_NAME}/
```

## Step 8: Use in Earth Engine

Now you can use your files in Earth Engine:

```javascript
// Your files are now accessible in Earth Engine!
var bucketPath = 'gs://ndmi-ndwi-nigeria-2025/';

function loadNDMITile(year, month, suffix) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  var filePath = bucketPath + 'NDMI_' + year + '_' + monthStr + suffix + '.tif';
  return ee.Image.loadGeoTIFF(filePath);
}
```

## Cost Estimate

For your 322GB of data:
- **Storage**: ~$6.44/month (Standard storage at $0.020/GB)
- **Upload from Drive**: FREE
- **Earth Engine reads**: FREE (same region)
- **First 90 days**: Covered by $300 credit

## Common Issues & Solutions

### "Permission denied"
- Make sure you're logged into the right Google account
- Check that APIs are enabled
- Verify project ID is correct

### "Bucket name already exists"
- Bucket names must be globally unique
- Try adding your initials or date: `ndmi-ndwi-nigeria-bb-2025`

### "Quota exceeded"
- You're unlikely to hit quotas with free tier
- If you do, wait 24 hours or upgrade

## Next Steps

1. Create your Google Cloud account (5 minutes)
2. Create project and bucket (5 minutes)
3. Start upload from Drive to bucket (let it run)
4. Update your Earth Engine script with bucket path
5. Extract DHS values!

## Need Help?

- Google Cloud Console: https://console.cloud.google.com/
- Storage Browser: https://console.cloud.google.com/storage
- Support: https://cloud.google.com/support
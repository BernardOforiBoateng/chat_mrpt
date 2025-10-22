# Move Files from Google Drive to Google Cloud Storage

## Method 1: Using Google Colab (Easiest, Free)

```python
# Cell 1: Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Cell 2: Authenticate to Google Cloud
from google.colab import auth
auth.authenticate_user()

# Cell 3: Install Google Cloud SDK
!apt-get update
!apt-get install google-cloud-sdk -y

# Cell 4: Set your project ID
import os
PROJECT_ID = "your-project-id"  # Replace with your GCP project ID
!gcloud config set project {PROJECT_ID}

# Cell 5: Create a Cloud Storage bucket (if you don't have one)
BUCKET_NAME = "nigeria-ndmi-ndwi"  # Choose a unique name
!gsutil mb gs://{BUCKET_NAME}

# Cell 6: Copy files from Drive to Cloud Storage
# Your Drive folder path
DRIVE_FOLDER = "/content/drive/MyDrive/Nigeria_NDMI_NDWI_HLS"

# Copy all TIFF files to Cloud Storage
!gsutil -m cp -r {DRIVE_FOLDER}/*.tif gs://{BUCKET_NAME}/

# Check what was uploaded
!gsutil ls gs://{BUCKET_NAME}/
```

## Method 2: Using Cloud Shell (Direct Transfer)

1. **Open Google Cloud Console**: https://console.cloud.google.com/
2. **Activate Cloud Shell** (terminal icon in top right)
3. **Mount your Google Drive in Cloud Shell**:

```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure rclone for Google Drive
rclone config
# Follow prompts:
# - New remote
# - Name: mydrive
# - Storage: drive
# - Follow OAuth steps

# List Drive contents
rclone ls mydrive:Nigeria_NDMI_NDWI_HLS

# Copy to Cloud Storage
gsutil -m cp -r mydrive:Nigeria_NDMI_NDWI_HLS/*.tif gs://your-bucket/
```

## Method 3: Using Google Transfer Service (Best for Large Files)

1. Go to: https://console.cloud.google.com/transfer
2. Click "Create Transfer Job"
3. Select:
   - Source: Google Drive
   - Destination: Cloud Storage
4. Authorize Drive access
5. Select your folder: `Nigeria_NDMI_NDWI_HLS`
6. Choose destination bucket
7. Start transfer

## After Moving to Cloud Storage

Update your GEE script to load from Cloud Storage:

```javascript
// Load from Cloud Storage instead of Drive
function loadNDMITile(year, month, suffix) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  var filePath = 'gs://nigeria-ndmi-ndwi/NDMI_' + year + '_' + monthStr + suffix + '.tif';
  return ee.Image.loadGeoTIFF(filePath);
}

function loadNDWITile(year, month, suffix) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  var filePath = 'gs://nigeria-ndmi-ndwi/NDWI_' + year + '_' + monthStr + suffix + '.tif';
  return ee.Image.loadGeoTIFF(filePath);
}
```

## Cost Considerations

- **Storage**: ~$0.02 per GB per month
- **Transfer from Drive**: FREE
- **Earth Engine access**: FREE
- Your 322GB would cost ~$6.44/month to store

## Quick Start (Colab Method)

1. Open Google Colab
2. Run the code in Method 1
3. Replace `your-project-id` with your Google Cloud project
4. Choose a unique bucket name
5. Wait for transfer to complete
6. Use the updated GEE script to access from Cloud Storage

This way, Earth Engine can directly read your files just like in your boss's code!
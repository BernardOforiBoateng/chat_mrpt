#!/bin/bash

# Fix Data Analysis V3 Storage Issue
# Solution: Implement S3-based shared storage

echo "============================================"
echo "Fixing Data Analysis V3 Storage Issue"
echo "============================================"
echo ""

KEY_PATH="/tmp/chatmrpt-key3.pem"

# Step 1: Create S3 bucket for shared uploads
echo "Step 1: Setting up S3 bucket for shared storage..."
BUCKET_NAME="chatmrpt-uploads-$(date +%s)"
REGION="us-east-2"

ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@3.21.167.170 << EOF
# Check if we can create S3 bucket
aws s3 ls 2>&1 | head -5 || echo "Note: May need IAM permissions"

# Check existing buckets
echo "Checking for existing ChatMRPT buckets..."
aws s3 ls | grep chatmrpt || echo "No existing ChatMRPT buckets found"
EOF

echo ""
echo "Step 2: Creating Python module for S3 storage..."

# Create S3 storage module
cat > /tmp/s3_storage.py << 'PYTHON'
"""
S3 Storage Module for Data Analysis V3
Provides shared storage across multiple instances
"""

import os
import boto3
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import tempfile
import shutil

logger = logging.getLogger(__name__)

class S3Storage:
    """
    S3-based storage for Data Analysis uploads.
    Allows multiple instances to share uploaded files.
    """
    
    def __init__(self, bucket_name: str = None):
        """Initialize S3 storage with optional bucket name."""
        self.bucket_name = bucket_name or os.environ.get('S3_UPLOADS_BUCKET', 'chatmrpt-uploads')
        self.s3_client = None
        self.local_cache_dir = os.path.join(tempfile.gettempdir(), 'chatmrpt_s3_cache')
        os.makedirs(self.local_cache_dir, exist_ok=True)
        
    def _get_client(self):
        """Get or create S3 client."""
        if not self.s3_client:
            try:
                # Try to use IAM role (preferred for EC2)
                self.s3_client = boto3.client('s3', region_name='us-east-2')
                # Test access
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"✅ Connected to S3 bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"❌ S3 connection failed: {e}")
                # Fall back to local storage
                return None
        return self.s3_client
    
    def upload_file(self, local_path: str, session_id: str, filename: str) -> bool:
        """
        Upload a file to S3.
        
        Args:
            local_path: Path to local file
            session_id: User session ID
            filename: Original filename
            
        Returns:
            True if successful, False otherwise
        """
        client = self._get_client()
        if not client:
            logger.warning("S3 not available, using local storage only")
            return False
            
        try:
            # S3 key format: sessions/{session_id}/{filename}
            s3_key = f"sessions/{session_id}/{filename}"
            
            # Upload file
            client.upload_file(local_path, self.bucket_name, s3_key)
            logger.info(f"✅ Uploaded to S3: {s3_key}")
            
            # Also upload metadata
            metadata = {
                'session_id': session_id,
                'filename': filename,
                'upload_time': datetime.now().isoformat(),
                'size': os.path.getsize(local_path)
            }
            
            metadata_key = f"sessions/{session_id}/.metadata.json"
            client.put_object(
                Bucket=self.bucket_name,
                Key=metadata_key,
                Body=json.dumps(metadata),
                ContentType='application/json'
            )
            
            # Create flag file for Data Analysis V3
            flag_key = f"sessions/{session_id}/.data_analysis_mode"
            client.put_object(
                Bucket=self.bucket_name,
                Key=flag_key,
                Body=f"{filename}\n{datetime.now().isoformat()}",
                ContentType='text/plain'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return False
    
    def download_file(self, session_id: str, filename: str, local_dir: str) -> Optional[str]:
        """
        Download a file from S3 to local directory.
        
        Args:
            session_id: User session ID
            filename: File to download
            local_dir: Local directory to save to
            
        Returns:
            Local path if successful, None otherwise
        """
        client = self._get_client()
        if not client:
            return None
            
        try:
            s3_key = f"sessions/{session_id}/{filename}"
            local_path = os.path.join(local_dir, filename)
            
            # Check local cache first
            cache_path = os.path.join(self.local_cache_dir, session_id, filename)
            if os.path.exists(cache_path):
                # Copy from cache
                shutil.copy2(cache_path, local_path)
                logger.info(f"✅ Retrieved from cache: {filename}")
                return local_path
            
            # Download from S3
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            client.download_file(self.bucket_name, s3_key, local_path)
            
            # Cache for future use
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            shutil.copy2(local_path, cache_path)
            
            logger.info(f"✅ Downloaded from S3: {s3_key}")
            return local_path
            
        except Exception as e:
            logger.error(f"S3 download failed: {e}")
            return None
    
    def check_session_has_data(self, session_id: str) -> bool:
        """
        Check if a session has uploaded data in S3.
        
        Args:
            session_id: User session ID
            
        Returns:
            True if data exists, False otherwise
        """
        client = self._get_client()
        if not client:
            # Fall back to local check
            local_dir = os.path.join('instance/uploads', session_id)
            return os.path.exists(os.path.join(local_dir, '.data_analysis_mode'))
        
        try:
            # Check for flag file in S3
            flag_key = f"sessions/{session_id}/.data_analysis_mode"
            client.head_object(Bucket=self.bucket_name, Key=flag_key)
            return True
        except:
            # Check local as fallback
            local_dir = os.path.join('instance/uploads', session_id)
            return os.path.exists(os.path.join(local_dir, '.data_analysis_mode'))
    
    def list_session_files(self, session_id: str) -> list:
        """
        List all files for a session.
        
        Args:
            session_id: User session ID
            
        Returns:
            List of filenames
        """
        client = self._get_client()
        if not client:
            # Fall back to local
            local_dir = os.path.join('instance/uploads', session_id)
            if os.path.exists(local_dir):
                return [f for f in os.listdir(local_dir) 
                        if not f.startswith('.') and f.endswith(('.csv', '.xlsx', '.xls', '.json'))]
            return []
        
        try:
            prefix = f"sessions/{session_id}/"
            response = client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    filename = obj['Key'].split('/')[-1]
                    if not filename.startswith('.') and filename:
                        files.append(filename)
            
            return files
            
        except Exception as e:
            logger.error(f"S3 list failed: {e}")
            return []
    
    def sync_to_local(self, session_id: str, local_dir: str) -> bool:
        """
        Sync all session files from S3 to local directory.
        
        Args:
            session_id: User session ID
            local_dir: Local directory to sync to
            
        Returns:
            True if successful, False otherwise
        """
        files = self.list_session_files(session_id)
        success = True
        
        os.makedirs(local_dir, exist_ok=True)
        
        for filename in files:
            if not self.download_file(session_id, filename, local_dir):
                success = False
        
        # Also sync flag file
        client = self._get_client()
        if client:
            try:
                flag_key = f"sessions/{session_id}/.data_analysis_mode"
                flag_path = os.path.join(local_dir, '.data_analysis_mode')
                client.download_file(self.bucket_name, flag_key, flag_path)
            except:
                pass
        
        return success

# Singleton instance
_s3_storage = None

def get_s3_storage() -> S3Storage:
    """Get or create S3 storage instance."""
    global _s3_storage
    if not _s3_storage:
        _s3_storage = S3Storage()
    return _s3_storage
PYTHON

echo "S3 storage module created at /tmp/s3_storage.py"

echo ""
echo "Step 3: Deploying S3 storage module to staging..."

# Deploy to both staging instances
for ip in 3.21.167.170 18.220.103.20; do
    echo "Deploying to $ip..."
    scp -i $KEY_PATH /tmp/s3_storage.py ec2-user@$ip:/tmp/
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$ip << 'DEPLOY'
    # Copy to app directory
    cp /tmp/s3_storage.py /home/ec2-user/ChatMRPT/app/core/s3_storage.py
    
    # Install boto3 if needed
    source /home/ec2-user/chatmrpt_env/bin/activate
    pip list | grep boto3 || pip install boto3
    
    echo "✅ S3 storage module deployed"
DEPLOY
done

echo ""
echo "============================================"
echo "S3 Storage Module Deployed!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Update upload and chat routes to use S3 storage"
echo "2. Create S3 bucket with proper IAM permissions"
echo "3. Test cross-instance file sharing"
echo ""
echo "Note: For immediate testing, you can also:"
echo "- Configure ALB sticky sessions"
echo "- Or temporarily use single instance"
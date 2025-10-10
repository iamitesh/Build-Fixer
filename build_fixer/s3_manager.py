"""
S3 Manager - Handles uploading and downloading log files from Amazon S3
"""
import os
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Manager:
    """Manages interactions with Amazon S3 for log file storage"""
    
    def __init__(self, bucket_name, region_name='us-east-1'):
        """
        Initialize S3 Manager
        
        Args:
            bucket_name (str): Name of the S3 bucket
            region_name (str): AWS region name (default: us-east-1)
        """
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name=region_name)
        logger.info(f"S3Manager initialized for bucket: {bucket_name}")
    
    def upload_log_file(self, local_file_path, s3_key=None):
        """
        Upload a log file to S3
        
        Args:
            local_file_path (str): Path to the local log file
            s3_key (str): S3 object key (if None, uses basename of file)
            
        Returns:
            str: S3 key of uploaded file or None if failed
        """
        if not os.path.exists(local_file_path):
            logger.error(f"Local file not found: {local_file_path}")
            return None
        
        if s3_key is None:
            s3_key = os.path.basename(local_file_path)
        
        try:
            self.s3_client.upload_file(local_file_path, self.bucket_name, s3_key)
            logger.info(f"Successfully uploaded {local_file_path} to s3://{self.bucket_name}/{s3_key}")
            return s3_key
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return None
    
    def download_log_file(self, s3_key, local_file_path):
        """
        Download a log file from S3
        
        Args:
            s3_key (str): S3 object key
            local_file_path (str): Path where to save the downloaded file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            
            self.s3_client.download_file(self.bucket_name, s3_key, local_file_path)
            logger.info(f"Successfully downloaded s3://{self.bucket_name}/{s3_key} to {local_file_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {e}")
            return False
    
    def get_log_content(self, s3_key):
        """
        Get log file content directly from S3 without downloading
        
        Args:
            s3_key (str): S3 object key
            
        Returns:
            str: Content of the log file or None if failed
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            logger.info(f"Successfully retrieved content from s3://{self.bucket_name}/{s3_key}")
            return content
        except ClientError as e:
            logger.error(f"Failed to get log content from S3: {e}")
            return None

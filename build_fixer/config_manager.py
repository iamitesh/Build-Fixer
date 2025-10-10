"""
Configuration Manager - Handles loading and validating configuration
"""
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration for Build Fixer"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize Configuration Manager
        
        Args:
            config_file (str): Path to configuration file (optional)
        """
        self.config = {}
        self._load_from_env()
        
        if config_file and os.path.exists(config_file):
            logger.info(f"Loading configuration from {config_file}")
            # Could extend to support config files (JSON, YAML, INI)
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        self.config = {
            # AWS Configuration
            'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            's3_bucket_name': os.getenv('S3_BUCKET_NAME'),
            'bedrock_model_id': os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
            
            # Azure DevOps Configuration
            'azure_devops_org_url': os.getenv('AZURE_DEVOPS_ORG_URL'),
            'azure_devops_pat': os.getenv('AZURE_DEVOPS_PAT'),
            'azure_devops_project': os.getenv('AZURE_DEVOPS_PROJECT'),
            
            # Work Item Configuration
            'work_item_type': os.getenv('WORK_ITEM_TYPE', 'User Story'),  # or 'Bug'
            'work_item_tags': os.getenv('WORK_ITEM_TAGS', 'build-failure,automated').split(','),
            'work_item_assigned_to': os.getenv('WORK_ITEM_ASSIGNED_TO'),
            'work_item_area_path': os.getenv('WORK_ITEM_AREA_PATH'),
            'work_item_iteration_path': os.getenv('WORK_ITEM_ITERATION_PATH'),
            
            # Build Configuration
            'build_log_path': os.getenv('BUILD_LOG_PATH'),
            'build_id': os.getenv('BUILD_BUILDID', 'unknown'),
            'build_number': os.getenv('BUILD_BUILDNUMBER', 'unknown'),
            'build_reason': os.getenv('BUILD_REASON', 'unknown'),
            'repository_name': os.getenv('BUILD_REPOSITORY_NAME', 'unknown'),
            'branch_name': os.getenv('BUILD_SOURCEBRANCHNAME', 'unknown'),
        }
        
        logger.info("Configuration loaded from environment variables")
    
    def get(self, key: str, default=None):
        """
        Get configuration value
        
        Args:
            key (str): Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def validate(self) -> tuple[bool, list]:
        """
        Validate required configuration
        
        Returns:
            tuple: (is_valid, list of missing required fields)
        """
        required_fields = [
            's3_bucket_name',
            'azure_devops_org_url',
            'azure_devops_pat',
            'azure_devops_project',
        ]
        
        missing = [field for field in required_fields if not self.config.get(field)]
        
        if missing:
            logger.error(f"Missing required configuration: {', '.join(missing)}")
            return False, missing
        
        logger.info("Configuration validation passed")
        return True, []
    
    def get_aws_credentials(self) -> Dict[str, str]:
        """Get AWS credentials from config"""
        creds = {}
        if self.config.get('aws_access_key_id'):
            creds['aws_access_key_id'] = self.config['aws_access_key_id']
        if self.config.get('aws_secret_access_key'):
            creds['aws_secret_access_key'] = self.config['aws_secret_access_key']
        return creds

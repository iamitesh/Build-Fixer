#!/usr/bin/env python3
"""
Build Fixer - Main orchestrator script

This script orchestrates the entire build failure analysis workflow:
1. Upload build log to S3
2. Analyze the log using Amazon Bedrock
3. Create a User Story/Bug in Azure DevOps with RCA and recommendations
"""

import os
import sys
import logging
import argparse
from datetime import datetime

from build_fixer.config_manager import ConfigManager
from build_fixer.s3_manager import S3Manager
from build_fixer.bedrock_analyzer import BedrockAnalyzer
from build_fixer.azure_devops_manager import AzureDevOpsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class BuildFixer:
    """Main orchestrator for build failure analysis and remediation"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize Build Fixer
        
        Args:
            config_manager (ConfigManager): Configuration manager instance
        """
        self.config = config_manager
        
        # Initialize components
        self.s3_manager = S3Manager(
            bucket_name=config_manager.get('s3_bucket_name'),
            region_name=config_manager.get('aws_region')
        )
        
        self.bedrock_analyzer = BedrockAnalyzer(
            region_name=config_manager.get('aws_region'),
            model_id=config_manager.get('bedrock_model_id')
        )
        
        self.azure_devops_manager = AzureDevOpsManager(
            organization_url=config_manager.get('azure_devops_org_url'),
            personal_access_token=config_manager.get('azure_devops_pat'),
            project_name=config_manager.get('azure_devops_project')
        )
        
        logger.info("BuildFixer initialized successfully")
    
    def process_build_failure(self, log_file_path: str) -> dict:
        """
        Process a build failure end-to-end
        
        Args:
            log_file_path (str): Path to the build log file
            
        Returns:
            dict: Results containing work_item_id, s3_key, and analysis
        """
        logger.info(f"Processing build failure for log: {log_file_path}")
        
        results = {
            'success': False,
            's3_key': None,
            'analysis': None,
            'work_item_id': None,
            'error': None
        }
        
        try:
            # Step 1: Upload log to S3
            logger.info("Step 1: Uploading log file to S3...")
            s3_key = self._upload_log_to_s3(log_file_path)
            if not s3_key:
                results['error'] = "Failed to upload log to S3"
                return results
            
            results['s3_key'] = s3_key
            logger.info(f"Log uploaded to S3: {s3_key}")
            
            # Step 2: Read log content
            logger.info("Step 2: Reading log content...")
            log_content = self._read_log_content(log_file_path)
            if not log_content:
                results['error'] = "Failed to read log content"
                return results
            
            # Step 3: Analyze with Bedrock
            logger.info("Step 3: Analyzing build failure with Amazon Bedrock...")
            analysis = self.bedrock_analyzer.analyze_build_failure(log_content)
            results['analysis'] = analysis
            logger.info("Analysis complete")
            
            # Step 4: Create work item in Azure DevOps
            logger.info("Step 4: Creating work item in Azure DevOps...")
            work_item_id = self._create_work_item(analysis, s3_key)
            if not work_item_id:
                results['error'] = "Failed to create work item"
                return results
            
            results['work_item_id'] = work_item_id
            results['success'] = True
            
            logger.info(f"Build failure processing complete. Work Item #{work_item_id} created.")
            
        except Exception as e:
            logger.error(f"Error processing build failure: {e}", exc_info=True)
            results['error'] = str(e)
        
        return results
    
    def _upload_log_to_s3(self, log_file_path: str) -> str:
        """
        Upload log file to S3 with a timestamped key
        
        Args:
            log_file_path (str): Path to log file
            
        Returns:
            str: S3 key or None if failed
        """
        build_id = self.config.get('build_id', 'unknown')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        s3_key = f"build-logs/{build_id}_{timestamp}.log"
        
        return self.s3_manager.upload_log_file(log_file_path, s3_key)
    
    def _read_log_content(self, log_file_path: str) -> str:
        """
        Read log file content
        
        Args:
            log_file_path (str): Path to log file
            
        Returns:
            str: Log content or None if failed
        """
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read log file: {e}")
            return None
    
    def _create_work_item(self, analysis: dict, s3_key: str) -> int:
        """
        Create work item in Azure DevOps
        
        Args:
            analysis (dict): Analysis results from Bedrock
            s3_key (str): S3 key of the uploaded log
            
        Returns:
            int: Work item ID or None if failed
        """
        # Build title
        build_number = self.config.get('build_number', 'unknown')
        repo_name = self.config.get('repository_name', 'unknown')
        branch_name = self.config.get('branch_name', 'unknown')
        
        title = f"Build Failure: {repo_name} - Build #{build_number} ({branch_name})"
        
        # Build description
        description = f"""
Build failed for repository {repo_name} on branch {branch_name}.

Build Number: {build_number}
Build ID: {self.config.get('build_id', 'unknown')}
Build Reason: {self.config.get('build_reason', 'unknown')}
Log File: s3://{self.config.get('s3_bucket_name')}/{s3_key}
        """
        
        # Extract RCA and recommendations
        rca = analysis.get('rca', 'No RCA available')
        recommendations = analysis.get('recommendations', 'No recommendations available')
        
        # Get work item configuration
        work_item_type = self.config.get('work_item_type', 'User Story')
        tags = self.config.get('work_item_tags', [])
        assigned_to = self.config.get('work_item_assigned_to')
        area_path = self.config.get('work_item_area_path')
        iteration_path = self.config.get('work_item_iteration_path')
        
        # Create appropriate work item type
        if work_item_type == 'Bug':
            return self.azure_devops_manager.create_bug(
                title=title,
                description=description,
                rca=rca,
                recommendations=recommendations,
                severity='2-High',
                priority=2,
                tags=tags,
                assigned_to=assigned_to
            )
        else:
            return self.azure_devops_manager.create_user_story(
                title=title,
                description=description,
                rca=rca,
                recommendations=recommendations,
                tags=tags,
                assigned_to=assigned_to,
                area_path=area_path,
                iteration_path=iteration_path
            )


def main():
    """Main entry point for the Build Fixer CLI"""
    parser = argparse.ArgumentParser(
        description='Build Fixer - Analyze build failures and create Azure DevOps work items'
    )
    parser.add_argument(
        'log_file',
        help='Path to the build log file'
    )
    parser.add_argument(
        '--config',
        help='Path to configuration file (optional, uses env vars by default)',
        default=None
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config_manager = ConfigManager(config_file=args.config)
    
    # Validate configuration
    is_valid, missing = config_manager.validate()
    if not is_valid:
        logger.error(f"Configuration validation failed. Missing: {', '.join(missing)}")
        logger.error("Please set the required environment variables and try again.")
        sys.exit(1)
    
    # Check if log file exists
    if not os.path.exists(args.log_file):
        logger.error(f"Log file not found: {args.log_file}")
        sys.exit(1)
    
    # Initialize and run Build Fixer
    build_fixer = BuildFixer(config_manager)
    results = build_fixer.process_build_failure(args.log_file)
    
    # Print results
    if results['success']:
        print(f"\n{'='*60}")
        print("Build Failure Processing Complete!")
        print(f"{'='*60}")
        print(f"S3 Log Key: {results['s3_key']}")
        print(f"Work Item ID: {results['work_item_id']}")
        print(f"\nRCA Summary:")
        print(results['analysis']['rca'][:200] + "..." if len(results['analysis']['rca']) > 200 else results['analysis']['rca'])
        print(f"{'='*60}\n")
        sys.exit(0)
    else:
        print(f"\n{'='*60}")
        print("Build Failure Processing Failed!")
        print(f"{'='*60}")
        print(f"Error: {results['error']}")
        print(f"{'='*60}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()

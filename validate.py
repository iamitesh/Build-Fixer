#!/usr/bin/env python3
"""
Validation script to verify Build-Fixer installation and configuration
Run this script to check if Build-Fixer is properly set up
"""

import sys
import os

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"{text}")
    print('='*60)

def check_python_version():
    """Check if Python version is compatible"""
    print_header("1. Python Version Check")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (Need 3.8+)")
        return False

def check_imports():
    """Check if all required modules can be imported"""
    print_header("2. Module Import Check")
    
    modules_to_check = [
        ('boto3', 'boto3'),
        ('azure.devops', 'azure-devops'),
        ('msrest', 'msrest'),
        ('build_fixer.config_manager', 'build_fixer'),
        ('build_fixer.s3_manager', 'build_fixer'),
        ('build_fixer.bedrock_analyzer', 'build_fixer'),
        ('build_fixer.azure_devops_manager', 'build_fixer'),
        ('build_fixer.main', 'build_fixer'),
    ]
    
    all_ok = True
    for module, package in modules_to_check:
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError as e:
            print(f"✗ {package} - {e}")
            all_ok = False
    
    return all_ok

def check_configuration():
    """Check if required environment variables are set"""
    print_header("3. Configuration Check")
    
    required_vars = [
        'AWS_REGION',
        'S3_BUCKET_NAME',
        'AZURE_DEVOPS_ORG_URL',
        'AZURE_DEVOPS_PAT',
        'AZURE_DEVOPS_PROJECT',
    ]
    
    optional_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'BEDROCK_MODEL_ID',
        'WORK_ITEM_TYPE',
        'WORK_ITEM_TAGS',
    ]
    
    print("\nRequired Configuration:")
    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'PAT' in var or 'KEY' in var or 'SECRET' in var:
                display_value = value[:4] + '...' + value[-4:] if len(value) > 8 else '***'
            else:
                display_value = value[:50] + '...' if len(value) > 50 else value
            print(f"✓ {var} = {display_value}")
        else:
            print(f"✗ {var} = Not Set")
            all_ok = False
    
    print("\nOptional Configuration:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            if 'PAT' in var or 'KEY' in var or 'SECRET' in var:
                display_value = value[:4] + '...' + value[-4:] if len(value) > 8 else '***'
            else:
                display_value = value[:50] + '...' if len(value) > 50 else value
            print(f"  {var} = {display_value}")
        else:
            print(f"  {var} = Not Set (using default)")
    
    return all_ok

def check_aws_connectivity():
    """Check if AWS credentials are valid (if set)"""
    print_header("4. AWS Connectivity Check")
    
    if not os.getenv('S3_BUCKET_NAME'):
        print("⊘ Skipped (S3_BUCKET_NAME not set)")
        return True
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Try to create S3 client
        s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        
        # Try to check if bucket exists
        bucket_name = os.getenv('S3_BUCKET_NAME')
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✓ S3 bucket '{bucket_name}' is accessible")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"✗ S3 bucket '{bucket_name}' does not exist")
            elif error_code == '403':
                print(f"✗ Access denied to S3 bucket '{bucket_name}'")
            else:
                print(f"✗ S3 error: {e}")
            return False
            
    except Exception as e:
        print(f"✗ AWS connectivity check failed: {e}")
        return False

def check_azure_connectivity():
    """Check if Azure DevOps credentials are valid (if set)"""
    print_header("5. Azure DevOps Connectivity Check")
    
    org_url = os.getenv('AZURE_DEVOPS_ORG_URL')
    pat = os.getenv('AZURE_DEVOPS_PAT')
    project = os.getenv('AZURE_DEVOPS_PROJECT')
    
    if not all([org_url, pat, project]):
        print("⊘ Skipped (Azure DevOps credentials not set)")
        return True
    
    try:
        from azure.devops.connection import Connection
        from msrest.authentication import BasicAuthentication
        
        credentials = BasicAuthentication('', pat)
        connection = Connection(base_url=org_url, creds=credentials)
        
        # Try to get work item tracking client
        wit_client = connection.clients.get_work_item_tracking_client()
        
        print(f"✓ Connected to Azure DevOps: {org_url}")
        print(f"✓ Project: {project}")
        return True
        
    except Exception as e:
        print(f"✗ Azure DevOps connectivity check failed: {e}")
        return False

def check_example_file():
    """Check if example files exist"""
    print_header("6. Example Files Check")
    
    example_log = 'examples/sample_build_failure.log'
    example_config = 'examples/config.example'
    
    all_ok = True
    if os.path.exists(example_log):
        print(f"✓ {example_log}")
    else:
        print(f"✗ {example_log} not found")
        all_ok = False
    
    if os.path.exists(example_config):
        print(f"✓ {example_config}")
    else:
        print(f"✗ {example_config} not found")
        all_ok = False
    
    return all_ok

def main():
    """Run all validation checks"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              Build-Fixer Validation Script                   ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    # Run all checks
    results.append(("Python Version", check_python_version()))
    results.append(("Module Imports", check_imports()))
    results.append(("Configuration", check_configuration()))
    results.append(("AWS Connectivity", check_aws_connectivity()))
    results.append(("Azure DevOps Connectivity", check_azure_connectivity()))
    results.append(("Example Files", check_example_file()))
    
    # Summary
    print_header("Validation Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ All checks passed! Build-Fixer is ready to use.")
        print("\nNext steps:")
        print("1. Test with example: python -m build_fixer.main examples/sample_build_failure.log")
        print("2. Integrate into your Azure Pipeline")
        print("3. See SETUP.md for detailed configuration")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please review the errors above.")
        print("\nRefer to:")
        print("- SETUP.md for configuration help")
        print("- FAQ.md for troubleshooting")
        print("- README.md for general information")
        return 1

if __name__ == '__main__':
    sys.exit(main())

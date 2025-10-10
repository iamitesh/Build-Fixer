# Quick Start Guide

Get Build-Fixer running in 5 minutes!

## 1. Install

```bash
git clone https://github.com/iamitesh/Build-Fixer.git
cd Build-Fixer
pip install -r requirements.txt
```

## 2. Set Environment Variables

```bash
# AWS
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export S3_BUCKET_NAME=your-bucket

# Azure DevOps
export AZURE_DEVOPS_ORG_URL=https://dev.azure.com/your-org
export AZURE_DEVOPS_PAT=your_pat_token
export AZURE_DEVOPS_PROJECT=YourProject
```

## 3. Run

```bash
python -m build_fixer.main /path/to/build.log
```

## 4. Check Results

- ✅ Log uploaded to S3
- ✅ AI analysis complete
- ✅ Work item created in Azure DevOps

## Need Help?

See [SETUP.md](SETUP.md) for detailed setup instructions.

## Test with Example

```bash
# Set your environment variables first, then:
python -m build_fixer.main examples/sample_build_failure.log --verbose
```

This will analyze the example build failure and create a work item in your Azure DevOps project.

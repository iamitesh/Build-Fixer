#!/usr/bin/env node

require('dotenv').config();
const BuildFixer = require('./buildFixer');

/**
 * Main entry point for the Build-Fixer CLI
 */
async function main() {
  // Parse command line arguments
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    printUsage();
    process.exit(0);
  }

  // Get configuration from environment variables
  const config = {
    aws: {
      region: process.env.AWS_REGION || 'us-east-1',
      accessKeyId: process.env.AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
      s3BucketName: process.env.AWS_S3_BUCKET_NAME,
      bedrockModelId: process.env.AWS_BEDROCK_MODEL_ID
    },
    azureDevOps: {
      orgUrl: process.env.AZURE_DEVOPS_ORG_URL,
      token: process.env.AZURE_DEVOPS_TOKEN,
      project: process.env.AZURE_DEVOPS_PROJECT
    }
  };

  // Parse arguments
  const logFilePath = getArgValue(args, '--log-file');
  const s3Key = getArgValue(args, '--s3-key');
  const buildId = getArgValue(args, '--build-id') || 'unknown';
  const buildUrl = getArgValue(args, '--build-url') || '';
  const skipS3Upload = args.includes('--skip-s3-upload');

  try {
    const buildFixer = new BuildFixer(config);

    let results;
    if (s3Key) {
      // Process from existing S3 file
      results = await buildFixer.processBuildFailureFromS3({
        s3Key,
        buildId,
        buildUrl
      });
    } else if (logFilePath) {
      // Process from local file
      results = await buildFixer.processBuildFailure({
        logFilePath,
        buildId,
        buildUrl,
        uploadToS3: !skipS3Upload
      });
    } else {
      console.error('Error: Either --log-file or --s3-key must be provided');
      printUsage();
      process.exit(1);
    }

    // Output results as JSON
    console.log('\n📊 Results:');
    console.log(JSON.stringify(results, null, 2));
    
    process.exit(0);
  } catch (error) {
    console.error('\n❌ Fatal error:', error.message);
    process.exit(1);
  }
}

/**
 * Get argument value
 * @param {Array<string>} args - Command line arguments
 * @param {string} argName - Argument name
 * @returns {string|null} - Argument value or null
 */
function getArgValue(args, argName) {
  const index = args.indexOf(argName);
  if (index !== -1 && index + 1 < args.length) {
    return args[index + 1];
  }
  return null;
}

/**
 * Print usage information
 */
function printUsage() {
  console.log(`
Build-Fixer - Automated Build Failure Analyzer for Azure DevOps

USAGE:
  node src/index.js [OPTIONS]

OPTIONS:
  --log-file <path>       Path to the build log file (local)
  --s3-key <key>          S3 key of an existing log file (alternative to --log-file)
  --build-id <id>         Build ID (optional, default: 'unknown')
  --build-url <url>       URL to the failed build (optional)
  --skip-s3-upload        Skip uploading log to S3 (only with --log-file)
  --help, -h              Show this help message

ENVIRONMENT VARIABLES (required):
  AWS_REGION              AWS region (default: us-east-1)
  AWS_ACCESS_KEY_ID       AWS access key ID
  AWS_SECRET_ACCESS_KEY   AWS secret access key
  AWS_S3_BUCKET_NAME      S3 bucket name for log storage
  AWS_BEDROCK_MODEL_ID    Bedrock model ID (optional, default: anthropic.claude-3-sonnet)
  
  AZURE_DEVOPS_ORG_URL    Azure DevOps organization URL
  AZURE_DEVOPS_TOKEN      Azure DevOps personal access token
  AZURE_DEVOPS_PROJECT    Azure DevOps project name

EXAMPLES:
  # Process a local log file
  node src/index.js --log-file ./build.log --build-id 12345 --build-url https://dev.azure.com/...

  # Process an existing S3 log file
  node src/index.js --s3-key build-logs/12345.log --build-id 12345 --build-url https://dev.azure.com/...

  # Process without uploading to S3
  node src/index.js --log-file ./build.log --build-id 12345 --skip-s3-upload

For more information, see the README.md file.
`);
}

// Run main function
if (require.main === module) {
  main().catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
}

module.exports = main;

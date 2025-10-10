const BuildFixer = require('../src/buildFixer');

// Example configuration
const config = {
  aws: {
    region: 'us-east-1',
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    s3BucketName: 'my-build-logs-bucket',
    bedrockModelId: 'anthropic.claude-3-sonnet-20240229-v1:0'
  },
  azureDevOps: {
    orgUrl: 'https://dev.azure.com/my-organization',
    token: process.env.AZURE_DEVOPS_TOKEN,
    project: 'MyProject'
  }
};

// Example 1: Process a local build log file
async function example1() {
  const buildFixer = new BuildFixer(config);
  
  const results = await buildFixer.processBuildFailure({
    logFilePath: './path/to/build.log',
    buildId: '12345',
    buildUrl: 'https://dev.azure.com/org/project/_build/results?buildId=12345',
    uploadToS3: true
  });
  
  console.log('Results:', results);
}

// Example 2: Process a log file already in S3
async function example2() {
  const buildFixer = new BuildFixer(config);
  
  const results = await buildFixer.processBuildFailureFromS3({
    s3Key: 'build-logs/12345-1234567890.log',
    buildId: '12345',
    buildUrl: 'https://dev.azure.com/org/project/_build/results?buildId=12345'
  });
  
  console.log('Results:', results);
}

// Example 3: Process without uploading to S3
async function example3() {
  const buildFixer = new BuildFixer(config);
  
  const results = await buildFixer.processBuildFailure({
    logFilePath: './path/to/build.log',
    buildId: '12345',
    buildUrl: 'https://dev.azure.com/org/project/_build/results?buildId=12345',
    uploadToS3: false
  });
  
  console.log('Results:', results);
}

// Run examples (uncomment the one you want to test)
// example1().catch(console.error);
// example2().catch(console.error);
// example3().catch(console.error);

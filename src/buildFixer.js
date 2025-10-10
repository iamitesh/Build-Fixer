require('dotenv').config();
const S3Service = require('./services/s3Service');
const BedrockService = require('./services/bedrockService');
const AzureDevOpsService = require('./services/azureDevOpsService');
const { readLogFile, validateConfig, truncateLog } = require('./utils/helpers');

class BuildFixer {
  constructor(config) {
    this.validateConfiguration(config);
    
    this.s3Service = new S3Service({
      region: config.aws.region,
      accessKeyId: config.aws.accessKeyId,
      secretAccessKey: config.aws.secretAccessKey,
      bucketName: config.aws.s3BucketName
    });

    this.bedrockService = new BedrockService({
      region: config.aws.region,
      accessKeyId: config.aws.accessKeyId,
      secretAccessKey: config.aws.secretAccessKey,
      modelId: config.aws.bedrockModelId
    });

    this.azureDevOpsService = new AzureDevOpsService({
      orgUrl: config.azureDevOps.orgUrl,
      token: config.azureDevOps.token,
      project: config.azureDevOps.project
    });

    this.config = config;
  }

  /**
   * Validate required configuration
   * @param {Object} config - Configuration object
   */
  validateConfiguration(config) {
    validateConfig(config.aws || {}, ['region', 'accessKeyId', 'secretAccessKey', 's3BucketName']);
    validateConfig(config.azureDevOps || {}, ['orgUrl', 'token', 'project']);
  }

  /**
   * Main workflow to process build failure
   * @param {Object} options - Processing options
   * @param {string} options.logFilePath - Path to the build log file
   * @param {string} options.buildId - Build ID
   * @param {string} options.buildUrl - URL to the failed build
   * @param {boolean} options.uploadToS3 - Whether to upload log to S3 (default: true)
   * @returns {Promise<Object>} - Processing results
   */
  async processBuildFailure(options) {
    const { logFilePath, buildId, buildUrl, uploadToS3 = true } = options;

    console.log(`\n${'='.repeat(60)}`);
    console.log('Build-Fixer: Starting build failure analysis...');
    console.log(`Build ID: ${buildId}`);
    console.log(`${'='.repeat(60)}\n`);

    try {
      // Step 1: Read the build log
      console.log('Step 1: Reading build log file...');
      let logContent = await readLogFile(logFilePath);
      console.log(`Log file read successfully (${logContent.length} characters)\n`);

      // Truncate if too large
      logContent = truncateLog(logContent);

      // Step 2: Upload log to S3 (optional)
      let s3Key = null;
      if (uploadToS3) {
        console.log('Step 2: Uploading log to S3...');
        s3Key = await this.s3Service.uploadLog(logContent, buildId);
        console.log(`Log uploaded to S3: ${s3Key}\n`);
      } else {
        console.log('Step 2: Skipping S3 upload (uploadToS3=false)\n');
      }

      // Step 3: Analyze log with Amazon Bedrock
      console.log('Step 3: Analyzing build log with Amazon Bedrock...');
      const analysis = await this.bedrockService.analyzeLog(logContent);
      console.log('Analysis completed successfully\n');
      console.log('Root Cause Analysis:');
      console.log(analysis.rca);
      console.log('\nRecommended Fixes:');
      console.log(analysis.recommendations);
      console.log();

      // Step 4: Create work item in Azure DevOps
      console.log('Step 4: Creating work item in Azure DevOps...');
      const workItem = await this.azureDevOpsService.createWorkItem(
        buildId,
        analysis.rca,
        analysis.recommendations,
        buildUrl
      );
      console.log(`Work item created: ${workItem.url}\n`);

      // Return results
      const results = {
        success: true,
        buildId,
        s3Key,
        analysis,
        workItem
      };

      console.log(`${'='.repeat(60)}`);
      console.log('Build-Fixer: Process completed successfully!');
      console.log(`${'='.repeat(60)}\n`);

      return results;
    } catch (error) {
      console.error('\n❌ Error processing build failure:', error.message);
      console.error(error.stack);
      throw error;
    }
  }

  /**
   * Process build failure from S3 (when log is already uploaded)
   * @param {Object} options - Processing options
   * @param {string} options.s3Key - S3 key of the log file
   * @param {string} options.buildId - Build ID
   * @param {string} options.buildUrl - URL to the failed build
   * @returns {Promise<Object>} - Processing results
   */
  async processBuildFailureFromS3(options) {
    const { s3Key, buildId, buildUrl } = options;

    console.log(`\n${'='.repeat(60)}`);
    console.log('Build-Fixer: Starting build failure analysis from S3...');
    console.log(`Build ID: ${buildId}`);
    console.log(`S3 Key: ${s3Key}`);
    console.log(`${'='.repeat(60)}\n`);

    try {
      // Step 1: Download log from S3
      console.log('Step 1: Downloading log from S3...');
      let logContent = await this.s3Service.downloadLog(s3Key);
      console.log(`Log downloaded successfully (${logContent.length} characters)\n`);

      // Truncate if too large
      logContent = truncateLog(logContent);

      // Step 2: Analyze log with Amazon Bedrock
      console.log('Step 2: Analyzing build log with Amazon Bedrock...');
      const analysis = await this.bedrockService.analyzeLog(logContent);
      console.log('Analysis completed successfully\n');

      // Step 3: Create work item in Azure DevOps
      console.log('Step 3: Creating work item in Azure DevOps...');
      const workItem = await this.azureDevOpsService.createWorkItem(
        buildId,
        analysis.rca,
        analysis.recommendations,
        buildUrl
      );
      console.log(`Work item created: ${workItem.url}\n`);

      const results = {
        success: true,
        buildId,
        s3Key,
        analysis,
        workItem
      };

      console.log(`${'='.repeat(60)}`);
      console.log('Build-Fixer: Process completed successfully!');
      console.log(`${'='.repeat(60)}\n`);

      return results;
    } catch (error) {
      console.error('\n❌ Error processing build failure:', error.message);
      console.error(error.stack);
      throw error;
    }
  }
}

module.exports = BuildFixer;

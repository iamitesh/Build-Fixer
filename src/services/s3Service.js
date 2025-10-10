const { S3Client, PutObjectCommand, GetObjectCommand } = require('@aws-sdk/client-s3');
const { streamToString } = require('../utils/helpers');

class S3Service {
  constructor(config) {
    this.config = config;
    this.client = new S3Client({
      region: config.region,
      credentials: {
        accessKeyId: config.accessKeyId,
        secretAccessKey: config.secretAccessKey
      }
    });
    this.bucketName = config.bucketName;
  }

  /**
   * Upload build log file to S3
   * @param {string} logContent - The build log content
   * @param {string} buildId - The build ID for naming the file
   * @returns {Promise<string>} - The S3 key of the uploaded file
   */
  async uploadLog(logContent, buildId) {
    const key = `build-logs/${buildId}-${Date.now()}.log`;
    
    const command = new PutObjectCommand({
      Bucket: this.bucketName,
      Key: key,
      Body: logContent,
      ContentType: 'text/plain'
    });

    try {
      await this.client.send(command);
      console.log(`Log uploaded successfully to S3: ${key}`);
      return key;
    } catch (error) {
      console.error('Error uploading log to S3:', error);
      throw new Error(`Failed to upload log to S3: ${error.message}`);
    }
  }

  /**
   * Download build log file from S3
   * @param {string} key - The S3 key of the log file
   * @returns {Promise<string>} - The log content
   */
  async downloadLog(key) {
    const command = new GetObjectCommand({
      Bucket: this.bucketName,
      Key: key
    });

    try {
      const response = await this.client.send(command);
      const logContent = await streamToString(response.Body);
      console.log(`Log downloaded successfully from S3: ${key}`);
      return logContent;
    } catch (error) {
      console.error('Error downloading log from S3:', error);
      throw new Error(`Failed to download log from S3: ${error.message}`);
    }
  }
}

module.exports = S3Service;

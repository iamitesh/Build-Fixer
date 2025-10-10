/**
 * Convert a readable stream to string
 * @param {ReadableStream} stream - The stream to convert
 * @returns {Promise<string>} - The string content
 */
async function streamToString(stream) {
  const chunks = [];
  return new Promise((resolve, reject) => {
    stream.on('data', chunk => chunks.push(Buffer.from(chunk)));
    stream.on('error', reject);
    stream.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
  });
}

/**
 * Read log file from local filesystem
 * @param {string} filePath - Path to the log file
 * @returns {Promise<string>} - The log content
 */
async function readLogFile(filePath) {
  const fs = require('fs').promises;
  try {
    const content = await fs.readFile(filePath, 'utf-8');
    return content;
  } catch (error) {
    throw new Error(`Failed to read log file: ${error.message}`);
  }
}

/**
 * Validate required configuration
 * @param {Object} config - Configuration object
 * @param {Array<string>} requiredFields - Required field names
 * @throws {Error} - If required fields are missing
 */
function validateConfig(config, requiredFields) {
  const missing = requiredFields.filter(field => !config[field]);
  if (missing.length > 0) {
    throw new Error(`Missing required configuration: ${missing.join(', ')}`);
  }
}

/**
 * Truncate log content if too large
 * @param {string} logContent - The log content
 * @param {number} maxLines - Maximum number of lines to keep (default: 1000)
 * @returns {string} - Truncated log content
 */
function truncateLog(logContent, maxLines = 1000) {
  const lines = logContent.split('\n');
  if (lines.length <= maxLines) {
    return logContent;
  }

  // Keep first 200 lines and last 800 lines for context
  const firstLines = lines.slice(0, 200);
  const lastLines = lines.slice(-800);
  
  return [
    ...firstLines,
    `\n... [${lines.length - maxLines} lines truncated] ...\n`,
    ...lastLines
  ].join('\n');
}

module.exports = {
  streamToString,
  readLogFile,
  validateConfig,
  truncateLog
};

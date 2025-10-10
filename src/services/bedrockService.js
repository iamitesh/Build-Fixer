const { BedrockRuntimeClient, InvokeModelCommand } = require('@aws-sdk/client-bedrock-runtime');

class BedrockService {
  constructor(config) {
    this.config = config;
    this.client = new BedrockRuntimeClient({
      region: config.region,
      credentials: {
        accessKeyId: config.accessKeyId,
        secretAccessKey: config.secretAccessKey
      }
    });
    this.modelId = config.modelId || 'anthropic.claude-3-sonnet-20240229-v1:0';
  }

  /**
   * Analyze build log and generate RCA and recommendations
   * @param {string} logContent - The build log content
   * @returns {Promise<{rca: string, recommendations: string}>} - Analysis results
   */
  async analyzeLog(logContent) {
    const prompt = this.createAnalysisPrompt(logContent);

    const payload = {
      anthropic_version: 'bedrock-2023-05-31',
      max_tokens: 4096,
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      temperature: 0.5
    };

    const command = new InvokeModelCommand({
      modelId: this.modelId,
      contentType: 'application/json',
      accept: 'application/json',
      body: JSON.stringify(payload)
    });

    try {
      const response = await this.client.send(command);
      const responseBody = JSON.parse(new TextDecoder().decode(response.body));
      
      console.log('Build log analyzed successfully by Bedrock');
      
      // Parse the response to extract RCA and recommendations
      const analysis = this.parseAnalysisResponse(responseBody.content[0].text);
      return analysis;
    } catch (error) {
      console.error('Error analyzing log with Bedrock:', error);
      throw new Error(`Failed to analyze log with Bedrock: ${error.message}`);
    }
  }

  /**
   * Create analysis prompt for Bedrock
   * @param {string} logContent - The build log content
   * @returns {string} - The prompt
   */
  createAnalysisPrompt(logContent) {
    return `You are an expert DevOps engineer analyzing build failure logs. Please analyze the following build log and provide:

1. **Root Cause Analysis (RCA)**: Identify the primary reason(s) for the build failure
2. **Recommended Fixes**: Provide specific, actionable steps to resolve the issue

Build Log:
\`\`\`
${logContent}
\`\`\`

Please format your response as follows:

## Root Cause Analysis
[Your detailed RCA here]

## Recommended Fixes
[Your recommended fixes here, numbered if multiple fixes]

Be concise but thorough. Focus on the most critical errors and their solutions.`;
  }

  /**
   * Parse the Bedrock response to extract RCA and recommendations
   * @param {string} responseText - The response text from Bedrock
   * @returns {Object} - Parsed RCA and recommendations
   */
  parseAnalysisResponse(responseText) {
    // Split response into RCA and recommendations sections
    const rcaMatch = responseText.match(/##\s*Root Cause Analysis\s*([\s\S]*?)(?=##\s*Recommended Fixes|$)/i);
    const recommendationsMatch = responseText.match(/##\s*Recommended Fixes\s*([\s\S]*?)$/i);

    const rca = rcaMatch ? rcaMatch[1].trim() : responseText;
    const recommendations = recommendationsMatch ? recommendationsMatch[1].trim() : '';

    return {
      rca,
      recommendations,
      fullAnalysis: responseText
    };
  }
}

module.exports = BedrockService;

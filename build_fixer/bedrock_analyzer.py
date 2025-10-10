"""
Bedrock Analyzer - Uses Amazon Bedrock AI to analyze build failure logs
"""
import json
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BedrockAnalyzer:
    """Analyzes build failures using Amazon Bedrock AI"""
    
    def __init__(self, region_name='us-east-1', model_id='anthropic.claude-3-sonnet-20240229-v1:0'):
        """
        Initialize Bedrock Analyzer
        
        Args:
            region_name (str): AWS region name (default: us-east-1)
            model_id (str): Bedrock model ID to use
        """
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        self.model_id = model_id
        logger.info(f"BedrockAnalyzer initialized with model: {model_id}")
    
    def analyze_build_failure(self, log_content, max_tokens=4096):
        """
        Analyze build failure log using Amazon Bedrock
        
        Args:
            log_content (str): Content of the build failure log
            max_tokens (int): Maximum tokens for response
            
        Returns:
            dict: Analysis results with 'rca' and 'recommendations' keys
        """
        # Prepare the prompt for analysis
        prompt = self._create_analysis_prompt(log_content)
        
        try:
            # Call Bedrock API
            response = self._invoke_bedrock(prompt, max_tokens)
            
            # Parse the response
            analysis = self._parse_response(response)
            
            logger.info("Successfully analyzed build failure")
            return analysis
            
        except ClientError as e:
            logger.error(f"Bedrock API call failed: {e}")
            return {
                'rca': 'Failed to analyze: API error',
                'recommendations': 'Please check AWS credentials and Bedrock access'
            }
        except Exception as e:
            logger.error(f"Unexpected error during analysis: {e}")
            return {
                'rca': 'Failed to analyze: Unexpected error',
                'recommendations': str(e)
            }
    
    def _create_analysis_prompt(self, log_content):
        """
        Create a structured prompt for build failure analysis
        
        Args:
            log_content (str): Build log content
            
        Returns:
            str: Formatted prompt
        """
        # Limit log content to prevent token overflow (keep last 10000 chars which are usually most relevant)
        if len(log_content) > 10000:
            log_content = "...[earlier logs truncated]...\n" + log_content[-10000:]
        
        prompt = f"""You are an expert DevOps engineer analyzing a build failure log. 
Please provide a detailed Root Cause Analysis (RCA) and actionable recommendations to fix the issue.

Build Failure Log:
```
{log_content}
```

Please provide your analysis in the following JSON format:
{{
    "rca": "Detailed root cause analysis explaining why the build failed",
    "recommendations": "Step-by-step recommendations to fix the issue"
}}

Focus on:
1. Identifying the exact error or failure point
2. Understanding the root cause (dependencies, configuration, code issues, etc.)
3. Providing clear, actionable steps to resolve the issue
4. Suggesting preventive measures to avoid similar failures

Respond ONLY with valid JSON, no additional text."""
        
        return prompt
    
    def _invoke_bedrock(self, prompt, max_tokens):
        """
        Invoke Bedrock model with the prompt
        
        Args:
            prompt (str): Analysis prompt
            max_tokens (int): Maximum tokens for response
            
        Returns:
            dict: Bedrock API response
        """
        # Prepare request body based on Claude model format
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body
    
    def _parse_response(self, response):
        """
        Parse Bedrock response to extract RCA and recommendations
        
        Args:
            response (dict): Bedrock API response
            
        Returns:
            dict: Parsed analysis with 'rca' and 'recommendations'
        """
        try:
            # Extract content from Claude response
            content = response['content'][0]['text']
            
            # Try to parse as JSON
            try:
                # Remove markdown code blocks if present
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                analysis = json.loads(content)
                
                # Ensure required keys exist
                if 'rca' not in analysis:
                    analysis['rca'] = content
                if 'recommendations' not in analysis:
                    analysis['recommendations'] = 'See RCA for details'
                    
                return analysis
            except json.JSONDecodeError:
                # If not valid JSON, split by common patterns
                logger.warning("Response was not valid JSON, attempting text parsing")
                return self._fallback_parse(content)
                
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected response format: {e}")
            return {
                'rca': 'Unable to parse analysis',
                'recommendations': 'Please review the log manually'
            }
    
    def _fallback_parse(self, content):
        """
        Fallback parsing when JSON parsing fails
        
        Args:
            content (str): Response content
            
        Returns:
            dict: Parsed analysis
        """
        # Try to split by common section headers
        rca = ""
        recommendations = ""
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            lower_line = line.lower()
            if 'root cause' in lower_line or 'rca' in lower_line:
                current_section = 'rca'
                continue
            elif 'recommendation' in lower_line or 'fix' in lower_line or 'solution' in lower_line:
                current_section = 'recommendations'
                continue
            
            if current_section == 'rca':
                rca += line + '\n'
            elif current_section == 'recommendations':
                recommendations += line + '\n'
        
        # If still empty, use entire content as RCA
        if not rca and not recommendations:
            rca = content
            recommendations = "Please review the analysis above for fixing steps"
        
        return {
            'rca': rca.strip() or content,
            'recommendations': recommendations.strip() or "See RCA for details"
        }

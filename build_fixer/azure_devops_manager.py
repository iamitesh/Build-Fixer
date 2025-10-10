"""
Azure DevOps Manager - Handles creation of work items in Azure DevOps
"""
import logging
from azure.devops.connection import Connection
from azure.devops.v7_0.work_item_tracking.models import JsonPatchOperation
from msrest.authentication import BasicAuthentication

logger = logging.getLogger(__name__)


class AzureDevOpsManager:
    """Manages interactions with Azure DevOps for work item creation"""
    
    def __init__(self, organization_url, personal_access_token, project_name):
        """
        Initialize Azure DevOps Manager
        
        Args:
            organization_url (str): Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
            personal_access_token (str): Personal Access Token for authentication
            project_name (str): Name of the Azure DevOps project
        """
        self.organization_url = organization_url
        self.project_name = project_name
        
        # Create connection
        credentials = BasicAuthentication('', personal_access_token)
        self.connection = Connection(base_url=organization_url, creds=credentials)
        
        # Get work item tracking client
        self.wit_client = self.connection.clients.get_work_item_tracking_client()
        
        logger.info(f"AzureDevOpsManager initialized for project: {project_name}")
    
    def create_user_story(self, title, description, rca, recommendations, 
                         tags=None, assigned_to=None, area_path=None, iteration_path=None):
        """
        Create a User Story work item with RCA and recommendations
        
        Args:
            title (str): Title of the user story
            description (str): Description/repro steps
            rca (str): Root Cause Analysis
            recommendations (str): Recommended fixes
            tags (list): List of tags to add (optional)
            assigned_to (str): Email of person to assign to (optional)
            area_path (str): Area path for the work item (optional)
            iteration_path (str): Iteration path for the work item (optional)
            
        Returns:
            int: Work item ID if successful, None otherwise
        """
        # Build the complete description with RCA and recommendations
        full_description = self._format_description(description, rca, recommendations)
        
        # Create JSON patch document for the work item
        document = [
            JsonPatchOperation(
                op="add",
                path="/fields/System.Title",
                value=title
            ),
            JsonPatchOperation(
                op="add",
                path="/fields/System.Description",
                value=full_description
            )
        ]
        
        # Add optional fields
        if tags:
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/System.Tags",
                value="; ".join(tags)
            ))
        
        if assigned_to:
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/System.AssignedTo",
                value=assigned_to
            ))
        
        if area_path:
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/System.AreaPath",
                value=area_path
            ))
        
        if iteration_path:
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/System.IterationPath",
                value=iteration_path
            ))
        
        try:
            # Create the work item
            work_item = self.wit_client.create_work_item(
                document=document,
                project=self.project_name,
                type="User Story"
            )
            
            work_item_id = work_item.id
            logger.info(f"Successfully created User Story #{work_item_id}")
            
            return work_item_id
            
        except Exception as e:
            logger.error(f"Failed to create User Story: {e}")
            return None
    
    def _format_description(self, description, rca, recommendations):
        """
        Format the work item description with RCA and recommendations
        
        Args:
            description (str): Base description
            rca (str): Root Cause Analysis
            recommendations (str): Recommendations
            
        Returns:
            str: Formatted HTML description
        """
        html_description = f"""
<div>
<h2>Description</h2>
<p>{description}</p>

<h2>Root Cause Analysis (RCA)</h2>
<div style="background-color: #f8f8f8; padding: 10px; border-left: 4px solid #e74c3c;">
{self._text_to_html(rca)}
</div>

<h2>Recommended Fixes</h2>
<div style="background-color: #f8f8f8; padding: 10px; border-left: 4px solid #2ecc71;">
{self._text_to_html(recommendations)}
</div>

<p><i>This User Story was automatically created by Build-Fixer tool.</i></p>
</div>
"""
        return html_description
    
    def _text_to_html(self, text):
        """
        Convert plain text to HTML with basic formatting
        
        Args:
            text (str): Plain text
            
        Returns:
            str: HTML formatted text
        """
        # Replace newlines with <br> and wrap in paragraphs
        lines = text.split('\n')
        html_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Check if line is a numbered or bulleted list item
                if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '-', '*', '•')):
                    html_lines.append(f"<li>{line[2:].strip() if line[1] == '.' else line[1:].strip()}</li>")
                else:
                    html_lines.append(f"<p>{line}</p>")
        
        return '\n'.join(html_lines)
    
    def create_bug(self, title, description, rca, recommendations, 
                   severity=None, priority=None, tags=None, assigned_to=None):
        """
        Create a Bug work item with RCA and recommendations
        
        Args:
            title (str): Title of the bug
            description (str): Bug description
            rca (str): Root Cause Analysis
            recommendations (str): Recommended fixes
            severity (str): Bug severity (1-4 or Critical/High/Medium/Low)
            priority (int): Bug priority (1-4)
            tags (list): List of tags to add (optional)
            assigned_to (str): Email of person to assign to (optional)
            
        Returns:
            int: Work item ID if successful, None otherwise
        """
        full_description = self._format_description(description, rca, recommendations)
        
        document = [
            JsonPatchOperation(
                op="add",
                path="/fields/System.Title",
                value=title
            ),
            JsonPatchOperation(
                op="add",
                path="/fields/Microsoft.VSTS.TCM.ReproSteps",
                value=full_description
            )
        ]
        
        if severity:
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/Microsoft.VSTS.Common.Severity",
                value=str(severity)
            ))
        
        if priority:
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/Microsoft.VSTS.Common.Priority",
                value=priority
            ))
        
        if tags:
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/System.Tags",
                value="; ".join(tags)
            ))
        
        if assigned_to:
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/System.AssignedTo",
                value=assigned_to
            ))
        
        try:
            work_item = self.wit_client.create_work_item(
                document=document,
                project=self.project_name,
                type="Bug"
            )
            
            work_item_id = work_item.id
            logger.info(f"Successfully created Bug #{work_item_id}")
            
            return work_item_id
            
        except Exception as e:
            logger.error(f"Failed to create Bug: {e}")
            return None

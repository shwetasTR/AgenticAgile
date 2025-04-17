import json
import logging
import requests
import base64
import os

class ADOExporter:
    """
    Exporter for sending data to Azure DevOps.
    """
    
    def __init__(self, organization, project, personal_access_token=None):
        """
        Initialize the ADO exporter with organization and project information.
        
        Args:
            organization (str): The Azure DevOps organization name
            project (str): The Azure DevOps project name
            personal_access_token (str, optional): The personal access token for authentication.
                If not provided, it will try to get it from the environment variable ADO_PAT.
        """
        self.organization = organization
        self.project = project
        self.personal_access_token = personal_access_token or os.environ.get("ADO_PAT")
        self.logger = self._setup_logger()
        
        # Base URL for Azure DevOps API
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        
    def _setup_logger(self):
        """Set up a logger for the ADO exporter."""
        logger = logging.getLogger("ADOExporter")
        logger.setLevel(logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        return logger
    
    def _get_auth_header(self):
        """
        Get the authorization header for Azure DevOps API.
        
        Returns:
            dict: The authorization header
        """
        if not self.personal_access_token:
            raise ValueError("Personal access token is required for Azure DevOps API")
        
        # Create basic auth header with empty username and PAT as password
        auth_str = f":{self.personal_access_token}"
        auth_bytes = auth_str.encode("ascii")
        base64_bytes = base64.b64encode(auth_bytes)
        base64_auth = base64_bytes.decode("ascii")
        
        return {
            "Authorization": f"Basic {base64_auth}",
            "Content-Type": "application/json"
        }
    
    def export(self, feature_data, user_stories, acceptance_criteria, test_cases):
        """
        Export data to Azure DevOps.
        
        Args:
            feature_data (dict): The feature data
            user_stories (list): The user stories
            acceptance_criteria (list): The acceptance criteria
            test_cases (list): The test cases
            
        Returns:
            dict: A summary of the export results
        """
        self.logger.info(f"Exporting data to Azure DevOps: {self.organization}/{self.project}")
        
        if not self.personal_access_token:
            self.logger.error("Personal access token is required for Azure DevOps API")
            return {"error": "Personal access token is required"}
        
        try:
            # Create a feature work item
            feature_id = self._create_feature(feature_data)
            
            # Create user story work items
            user_story_ids = {}
            for story in user_stories:
                story_id = self._create_user_story(story, feature_id)
                user_story_ids[story["id"]] = story_id
            
            # Create test case work items
            test_case_ids = {}
            for test_case in test_cases:
                # Get the user story ID from the references
                user_story_ref = test_case.get("references", {}).get("user_story_id")
                parent_id = user_story_ids.get(user_story_ref) if user_story_ref else None
                
                test_case_id = self._create_test_case(test_case, parent_id)
                test_case_ids[test_case["id"]] = test_case_id
            
            return {
                "feature_id": feature_id,
                "user_story_ids": user_story_ids,
                "test_case_ids": test_case_ids,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting to Azure DevOps: {str(e)}")
            return {"error": str(e)}
    
    def _create_feature(self, feature_data):
        """
        Create a feature work item in Azure DevOps.
        
        Args:
            feature_data (dict): The feature data
            
        Returns:
            int: The ID of the created feature work item
        """
        self.logger.info(f"Creating feature: {feature_data.get('name')}")
        
        # Prepare the work item fields
        fields = {
            "System.Title": feature_data.get("name", "Unnamed Feature"),
            "System.Description": feature_data.get("description", ""),
            "System.WorkItemType": "Feature",
            "System.State": "New",
            "System.AreaPath": self.project,
            "System.IterationPath": self.project
        }
        
        # Create the work item
        return self._create_work_item(fields)
    
    def _create_user_story(self, user_story, parent_id=None):
        """
        Create a user story work item in Azure DevOps.
        
        Args:
            user_story (dict): The user story data
            parent_id (int, optional): The ID of the parent work item
            
        Returns:
            int: The ID of the created user story work item
        """
        # Format the title as "As a [user_type], I want to [action] so that [benefit]"
        title = f"As a {user_story.get('user_type', '')}, I want to {user_story.get('action', '')} so that {user_story.get('benefit', '')}"
        
        self.logger.info(f"Creating user story: {title[:50]}...")
        
        # Prepare the work item fields
        fields = {
            "System.Title": title,
            "System.Description": f"ID: {user_story.get('id', '')}\n\nUser Type: {user_story.get('user_type', '')}\nAction: {user_story.get('action', '')}\nBenefit: {user_story.get('benefit', '')}",
            "System.WorkItemType": "User Story",
            "System.State": "New",
            "System.AreaPath": self.project,
            "System.IterationPath": self.project
        }
        
        # Create the work item
        user_story_id = self._create_work_item(fields)
        
        # If parent ID is provided, create a link to the parent
        if parent_id:
            self._create_work_item_link(user_story_id, parent_id, "Child")
        
        return user_story_id
    
    def _create_test_case(self, test_case, parent_id=None):
        """
        Create a test case work item in Azure DevOps.
        
        Args:
            test_case (dict): The test case data
            parent_id (int, optional): The ID of the parent work item
            
        Returns:
            int: The ID of the created test case work item
        """
        self.logger.info(f"Creating test case: {test_case.get('title', 'Unnamed Test Case')}")
        
        # Format the steps as HTML
        steps_html = "<steps>"
        for step in test_case.get("steps", []):
            steps_html += f"""
            <step id="{step.get('Step Number', '')}">
                <parameterizedString isformatted="true">{step.get('Step Action', '')}</parameterizedString>
                <parameterizedString isformatted="true">{step.get('Step Expected', '')}</parameterizedString>
            </step>
            """
        steps_html += "</steps>"
        
        # Prepare the work item fields
        fields = {
            "System.Title": test_case.get("title", "Unnamed Test Case"),
            "System.Description": f"ID: {test_case.get('id', '')}\n\nReferences: {json.dumps(test_case.get('references', {}), indent=2)}",
            "System.WorkItemType": "Test Case",
            "System.State": test_case.get("state", "Design"),
            "System.AreaPath": self.project,
            "System.IterationPath": self.project,
            "Microsoft.VSTS.Common.Priority": test_case.get("priority", "2"),
            "Microsoft.VSTS.TCM.Steps": steps_html
        }
        
        # Create the work item
        test_case_id = self._create_work_item(fields)
        
        # If parent ID is provided, create a link to the parent
        if parent_id:
            self._create_work_item_link(test_case_id, parent_id, "Tests")
        
        return test_case_id
    
    def _create_work_item(self, fields):
        """
        Create a work item in Azure DevOps.
        
        Args:
            fields (dict): The fields for the work item
            
        Returns:
            int: The ID of the created work item
        """
        url = f"{self.base_url}/wit/workitems/${fields['System.WorkItemType']}?api-version=6.0"
        
        # Prepare the document
        document = []
        for field, value in fields.items():
            document.append({
                "op": "add",
                "path": f"/fields/{field}",
                "value": value
            })
        
        # Send the request
        response = requests.post(
            url,
            headers=self._get_auth_header(),
            json=document
        )
        
        # Check for errors
        response.raise_for_status()
        
        # Return the work item ID
        return response.json()["id"]
    
    def _create_work_item_link(self, source_id, target_id, link_type):
        """
        Create a link between two work items in Azure DevOps.
        
        Args:
            source_id (int): The ID of the source work item
            target_id (int): The ID of the target work item
            link_type (str): The type of link to create
            
        Returns:
            bool: True if the link was created successfully
        """
        url = f"{self.base_url}/wit/workitems/{source_id}?api-version=6.0"
        
        # Prepare the document
        document = [{
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": f"System.LinkTypes.{link_type}",
                "url": f"{self.base_url}/wit/workitems/{target_id}"
            }
        }]
        
        # Send the request
        response = requests.patch(
            url,
            headers=self._get_auth_header(),
            json=document
        )
        
        # Check for errors
        response.raise_for_status()
        
        return True

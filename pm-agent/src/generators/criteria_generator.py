import json
import logging

class CriteriaGenerator:
    """
    Generator for creating acceptance criteria from user stories using the Gemini model.
    """
    
    def __init__(self, gemini_client):
        """
        Initialize the criteria generator with a Gemini client.
        
        Args:
            gemini_client: An instance of GeminiClient for text generation
        """
        self.gemini_client = gemini_client
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Set up a logger for the criteria generator."""
        logger = logging.getLogger("CriteriaGenerator")
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
    
    def generate(self, user_stories):
        """
        Generate acceptance criteria from user stories.
        
        Args:
            user_stories (list): A list of user stories
            
        Returns:
            list: A list of user stories with acceptance criteria in the format:
                [
                    {
                        "user_story": {
                            "id": "US-001",
                            "user_type": "User role",
                            "action": "What the user wants to do",
                            "benefit": "Why the user wants to do this"
                        },
                        "acceptance_criteria": [
                            {
                                "id": "AC-001-01",
                                "given": "Context",
                                "when": "Action",
                                "then": "Expected result"
                            },
                            ...
                        ]
                    },
                    ...
                ]
        """
        self.logger.info(f"Generating acceptance criteria for {len(user_stories)} user stories")
        
        try:
            # Use the Gemini client to generate acceptance criteria
            criteria_data = self.gemini_client.generate_acceptance_criteria(user_stories)
            
            # Ensure each acceptance criterion has an ID
            for story_data in criteria_data:
                user_story_id = story_data.get("user_story", {}).get("id", "US-UNK")
                
                for i, criterion in enumerate(story_data.get("acceptance_criteria", [])):
                    if "id" not in criterion or not criterion["id"]:
                        # Format: AC-[user story number]-[criterion number]
                        # Example: AC-001-01
                        story_num = user_story_id.split("-")[1] if len(user_story_id.split("-")) > 1 else "UNK"
                        criterion["id"] = f"AC-{story_num}-{(i+1):02d}"
            
            total_criteria = sum(len(story.get("acceptance_criteria", [])) for story in criteria_data)
            self.logger.info(f"Generated {total_criteria} acceptance criteria for {len(criteria_data)} user stories")
            
            return criteria_data
            
        except Exception as e:
            self.logger.error(f"Error generating acceptance criteria: {str(e)}")
            # Return a minimal error response
            return [{
                "user_story": user_stories[0] if user_stories else {"id": "US-ERR"},
                "acceptance_criteria": [{"id": "AC-ERR-01", "error": str(e)}]
            }]

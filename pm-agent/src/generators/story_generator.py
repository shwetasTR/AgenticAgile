import json
import logging

class StoryGenerator:
    """
    Generator for creating user stories from feature data using the Gemini model.
    """
    
    def __init__(self, gemini_client):
        """
        Initialize the story generator with a Gemini client.
        
        Args:
            gemini_client: An instance of GeminiClient for text generation
        """
        self.gemini_client = gemini_client
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Set up a logger for the story generator."""
        logger = logging.getLogger("StoryGenerator")
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
    
    def generate(self, feature_data):
        """
        Generate user stories from feature data.
        
        Args:
            feature_data (dict): The feature data containing information about the feature
            
        Returns:
            list: A list of user stories in the format:
                [
                    {
                        "id": "US-001",
                        "user_type": "User role",
                        "action": "What the user wants to do",
                        "benefit": "Why the user wants to do this"
                    },
                    ...
                ]
        """
        self.logger.info(f"Generating user stories for feature: {feature_data.get('name', 'Unknown')}")
        
        try:
            # Use the Gemini client to generate user stories
            user_stories = self.gemini_client.generate_user_stories(feature_data)
            
            # Ensure each user story has an ID
            for i, story in enumerate(user_stories):
                if "id" not in story or not story["id"]:
                    story["id"] = f"US-{(i+1):03d}"
            
            self.logger.info(f"Generated {len(user_stories)} user stories")
            return user_stories
            
        except Exception as e:
            self.logger.error(f"Error generating user stories: {str(e)}")
            # Return a minimal error response
            return [{"id": "US-ERR", "error": str(e)}]

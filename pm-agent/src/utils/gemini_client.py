import os
import json
import requests
import logging
from typing import Dict
from google.oauth2.credentials import Credentials as OAuth2Credentials
from datetime import datetime
import vertexai
from vertexai.generative_models import GenerativeModel
import re

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class GeminiClient:
    def __init__(self, workspace_id: str = "GTMSageMakerKWAk", model_name: str = "gemini-2.5-pro-preview-03-25"):
        """Initialize GeminiClient with workspace ID and model name."""
        logger.info(f"Initializing GeminiClient with workspace_id: {workspace_id}, model: {model_name}")
        self.workspace_id = workspace_id
        self.model_name = model_name
        self.credentials = self._fetch_credentials()
        self._initialize_vertexai()
        self.model = GenerativeModel(model_name)

    def _fetch_credentials(self) -> Dict:
        """Fetch credentials from Thomson Reuters endpoint."""
        logger.info("Fetching credentials from TR endpoint...")
        payload = {
            "workspace_id": self.workspace_id,
            "model_name": self.model_name,
        }

        url = "https://aiplatform.gcs.int.thomsonreuters.com/v1/gemini/token"

        try:
            # Add timeout and headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30  # 30 seconds timeout
            )

            # Check response immediately
            resp.raise_for_status()

            credentials = resp.json()
            if not credentials or "token" not in credentials or "project_id" not in credentials:
                logger.error("Invalid response format or missing token/project_id")
                raise ValueError("Invalid response format or missing token/project_id")

            logger.info("Successfully fetched credentials")
            return credentials

        except requests.exceptions.Timeout:
            logger.error("Request timed out while fetching credentials")
            raise TimeoutError("Request timed out while fetching credentials")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch credentials: {str(e)}")
            raise ValueError(f"Failed to fetch credentials: {str(e)}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {str(e)}")
            raise ValueError(f"Failed to parse response: {str(e)}")

    def _initialize_vertexai(self):
        """Initialize Vertex AI with fetched credentials."""
        logger.info("Initializing Vertex AI...")
        temp_creds = OAuth2Credentials(self.credentials["token"])
        vertexai.init(
            project=self.credentials["project_id"],
            location=self.credentials["region"],
            credentials=temp_creds
        )
        logger.info(f"Gemini Credentials are fetched and are valid till {self.credentials['expires_on']}")

    def generate_text(self, prompt: str, max_tokens: int = 4096, temperature: float = 0.7) -> str:
        """Generate text using the Gemini model."""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise

    def extract_features_from_text(self, text: str) -> dict:
        """
        Extract features from text using the Gemini model.
        """
        try:
            # Get response from model
            response = self.generate_text(text)
            logger.debug(f"Raw response received: {response[:200]}...")

            # Find JSON object using a simpler regex pattern
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.finditer(json_pattern, response)
            
            for match in matches:
                try:
                    potential_json = match.group()
                    features = json.loads(potential_json)
                    
                    # Validate required fields
                    required_fields = ["title", "description", "user_roles", "functionality", "benefits"]
                    if all(field in features for field in required_fields):
                        logger.info("Successfully extracted valid JSON features")
                        return features
                except json.JSONDecodeError:
                    continue
            
            # If no valid JSON found, try extracting between curly braces
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                try:
                    json_str = response[json_start:json_end]
                    features = json.loads(json_str)
                    
                    if all(field in features for field in required_fields):
                        logger.info("Successfully extracted valid JSON features")
                        return features
                except json.JSONDecodeError:
                    pass
            
            # If we get here, no valid JSON was found
            logger.error("No valid JSON object found in response")
            return {
                "error": "Could not extract valid JSON features",
                "raw_response_preview": response[:500]  # First 500 chars for debugging
            }
            
        except Exception as e:
            logger.error(f"Error in feature extraction: {str(e)}")
            return {"error": str(e)}
    
    def generate_user_stories(self, feature_data: dict) -> dict:
        """
        Generate user stories from feature data using the Gemini model.
        
        Args:
            feature_data (dict): The extracted features
        Returns:
            dict: Generated user stories in structured format
        """
        try:
            prompt = f"""
            Generate user stories based on these features. Return a valid JSON object only.

            Feature Data:
            {json.dumps(feature_data, indent=2)}

            Format the response exactly like this, ensuring valid JSON:
            {{
                "feature_title": string,
                "user_stories": [
                    {{
                        "id": "US-001",
                        "user_role": string,
                        "action": string,
                        "benefit": string,
                        "priority": "High|Medium|Low",
                        "related_functionality": [string]
                    }}
                ]
            }}

            Requirements:
            - Use proper JSON syntax
            - Include all fields
            - Ensure arrays have proper comma separation
            - No trailing commas
            - Escape special characters in strings
            """

            response = self.generate_text(prompt)
            logger.debug(f"Raw response: {response[:200]}...")

            try:
                # First attempt: direct JSON parsing
                user_stories = json.loads(response)
            except json.JSONDecodeError:
                # Second attempt: Extract JSON between curly braces
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    try:
                        json_str = response[json_start:json_end]
                        user_stories = json.loads(json_str)
                    except json.JSONDecodeError as je:
                        logger.error(f"JSON parsing error: {str(je)}")
                        logger.debug(f"Attempted to parse: {json_str}")
                        return {"error": f"Failed to parse JSON: {str(je)}"}
                else:
                    return {"error": "No JSON object found in response"}

            # Validate response structure
            required_fields = ["feature_title", "user_stories"]
            if all(field in user_stories for field in required_fields):
                logger.info(f"Generated {len(user_stories['user_stories'])} user stories")
                return user_stories

            return {
                "error": "Invalid user stories format",
                "details": "Response missing required fields"
            }

        except Exception as e:
            logger.error(f"Error generating user stories: {str(e)}")
            return {"error": str(e)}
    
    def generate_acceptance_criteria(self, user_stories):
        """
        Generate acceptance criteria from user stories using the Gemini model.
        
        Args:
            user_stories (list): The user stories
            
        Returns:
            list: The generated acceptance criteria
        """
        prompt = f"""
        Generate acceptance criteria for each of the following user stories. Each acceptance criterion 
        should follow the format "Given [context], When [action], Then [expected result]".
        
        User Stories:
        {json.dumps(user_stories, indent=2)}
        
        Output the acceptance criteria in the following JSON format:
        [
            {{
                "user_story": {{
                    "id": "US-001",
                    "user_type": "User role",
                    "action": "What the user wants to do",
                    "benefit": "Why the user wants to do this"
                }},
                "acceptance_criteria": [
                    {{
                        "id": "AC-001-01",
                        "given": "Context",
                        "when": "Action",
                        "then": "Expected result"
                    }},
                    ...
                ]
            }},
            ...
        ]
        """
        
        try:
            response = self.generate_text(prompt)
            # Extract JSON from the response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                logger.error("Could not extract JSON from response")
                return [{"error": "Could not generate acceptance criteria"}]
        except Exception as e:
            logger.error(f"Error generating acceptance criteria: {str(e)}")
            return [{"error": str(e)}]
    
    def _clean_json_response(self, response: str) -> str:
        """
        Clean and validate JSON response from model.
        
        Args:
            response (str): Raw response from model
        Returns:
            str: Cleaned JSON string
        """
        # Find JSON content
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start < 0 or json_end <= json_start:
            raise ValueError("No JSON object found in response")
            
        json_str = response[json_start:json_end]
        
        # Common JSON formatting fixes
        replacements = [
            (r'},\s*}', '}}'),  # Fix trailing comma before closing brace
            (r'},\s*]', '}]'),  # Fix trailing comma in arrays
            (r'\s+', ' '),      # Normalize whitespace
            (r',\s*([}\]])', r'\1')  # Remove trailing commas
        ]
        
        for pattern, replacement in replacements:
            json_str = re.sub(pattern, replacement, json_str)
            
        return json_str

    def generate_test_cases(self, user_stories: dict) -> dict:
        """
        Generate test cases for user stories in a properly nested structure.
        """
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Process each user story individually to avoid complex JSON
        result = {
            "feature_title": user_stories.get("feature_title", "AES Shipment Filing"),
            "user_stories": []
        }
        
        for idx, story in enumerate(user_stories.get("user_stories", [])):
            story_id = story.get("id", f"US-{idx+1:03d}")
            
            prompt = f"""
            Generate 1-2 test cases for this specific user story. Follow the EXACT format shown below.
            
            USER STORY:
            {json.dumps(story, indent=2)}
            
            FORMAT:
            {{
              "id": "{story_id}",
              "user_role": "{story.get('user_role', 'User')}",
              "action": "{story.get('action', 'action')}",
              "benefit": "{story.get('benefit', 'benefit')}",
              "priority": "{story.get('priority', 'High')}",
              "test_cases": [
                {{
                  "id": "TC-{story_id}-01",
                  "title": "Clear descriptive title based on the user story",
                  "priority": "High|Medium|Low",
                  "test_steps": [
                    {{
                      "step_number": 1,
                      "action": "First action to take",
                      "expected_result": "Expected outcome"
                    }},
                    {{
                      "step_number": 2,
                      "action": "Second action to take",
                      "expected_result": "Expected outcome"
                    }}
                  ]
                }}
              ]
            }}
            
            IMPORTANT:
            1. Each test case should have 3-5 practical, detailed steps
            2. Steps should be specific, not general
            3. Expected results should be verifiable
            4. Test case IDs should follow format TC-{story_id}-##
            5. Return ONLY the JSON with NO explanations or markdown
            """
            
            try:
                # Get test cases for this story
                response = self.generate_text(prompt)
                
                # Clean and extract JSON
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    story_with_tests = json.loads(json_str)
                    result["user_stories"].append(story_with_tests)
                    logger.info(f"Generated test cases for user story {story_id}")
                else:
                    # If extraction fails, keep original story with empty test cases
                    story_copy = story.copy()
                    story_copy["test_cases"] = []
                    story_copy["error"] = "Failed to generate test cases"
                    result["user_stories"].append(story_copy)
                    logger.warning(f"Failed to extract test cases for story {story_id}")
            
            except Exception as e:
                logger.error(f"Error generating test cases for story {story_id}: {str(e)}")
                # Add the story without test cases
                story_copy = story.copy()
                story_copy["test_cases"] = []
                story_copy["error"] = str(e)
                result["user_stories"].append(story_copy)
        
        # Save the complete result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(output_dir, f'test_cases_{timestamp}.json')
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        return result

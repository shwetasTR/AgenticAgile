import os
import json
import requests
import logging
from typing import Dict
from google.oauth2.credentials import Credentials as OAuth2Credentials
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
        Generate test cases from user stories with improved error handling.
        """
        try:
            prompt = f"""
            Generate test cases for these user stories. Return ONLY valid JSON.
            
            User Stories:
            {json.dumps(user_stories, indent=2)}
            
            Format response EXACTLY as:
            {{
                "feature_title": string,
                "test_cases": [
                    {{
                        "id": "TC-001",
                        "title": string,
                        "priority": "High|Medium|Low",
                        "test_steps": [
                            {{
                                "step_number": number,
                                "action": string,
                                "expected_result": string
                            }}
                        ]
                    }}
                ]
            }}
            
            Rules:
            1. Use valid JSON syntax
            2. No trailing commas
            3. No comments
            4. Double quotes for strings
            5. Keep response focused and concise
            """
            
            response = self.generate_text(prompt)
            logger.debug(f"Raw response: {response[:200]}...")
            
            try:
                # Clean and parse JSON
                json_str = self._clean_json_response(response)
                test_cases = json.loads(json_str)
                
                # Validate structure
                if not isinstance(test_cases, dict):
                    raise ValueError("Response is not a JSON object")
                    
                required_fields = ["feature_title", "test_cases"]
                if not all(field in test_cases for field in required_fields):
                    raise ValueError(f"Missing required fields: {required_fields}")
                    
                logger.info(f"Successfully generated {len(test_cases['test_cases'])} test cases")
                return test_cases
                
            except json.JSONDecodeError as je:
                logger.error(f"JSON parsing error: {str(je)}")
                logger.debug(f"Attempted to parse:\n{json_str}")
                return {
                    "error": f"Failed to parse JSON: {str(je)}",
                    "response_preview": response[:500]
                }
                
        except Exception as e:
            logger.error(f"Error generating test cases: {str(e)}")
            return {"error": str(e)}

import json
import logging

class TestCaseGenerator:
    """
    Generator for creating test cases from acceptance criteria using the Gemini model.
    """
    
    def __init__(self, gemini_client):
        """
        Initialize the test case generator with a Gemini client.
        
        Args:
            gemini_client: An instance of GeminiClient for text generation
        """
        self.gemini_client = gemini_client
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Set up a logger for the test case generator."""
        logger = logging.getLogger("TestCaseGenerator")
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
    
    def _clean_and_parse_json(self, response: str) -> dict:
        """
        Clean and parse JSON from model response.
        
        Args:
            response (str): Raw response from model
            
        Returns:
            dict: Parsed JSON or error dict
        """
        try:
            # First try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.debug("Direct JSON parsing failed, attempting cleanup")
            
            try:
                # Find the first { and last }
                start = response.find('{')
                end = response.rfind('}') + 1
                
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    # Clean up common JSON issues
                    json_str = json_str.replace('}\n}', '}}')
                    json_str = json_str.replace(',\n}', '}')
                    json_str = json_str.replace(',}', '}')
                    
                    self.logger.debug(f"Cleaned JSON string: {json_str[:200]}...")
                    return json.loads(json_str)
                else:
                    raise ValueError("No JSON object found in response")
                    
            except Exception as e:
                self.logger.error(f"JSON cleaning failed: {str(e)}")
                return {"error": f"Failed to parse JSON: {str(e)}"}

    def generate(self, acceptance_criteria_data):
        """
        Generate test cases from acceptance criteria.
        
        Args:
            acceptance_criteria_data (list): A list of user stories with acceptance criteria
            
        Returns:
            list: A list of test cases in the format:
                [
                    {
                        "id": "TC001",
                        "work_item_type": "Test Case",
                        "title": "Test case title",
                        "priority": "1",
                        "state": "Design",
                        "tags": "P1",
                        "steps": [
                            {
                                "Step Number": "1",
                                "Step Action": "Action to perform",
                                "Step Expected": "Expected result"
                            },
                            ...
                        ],
                        "references": {
                            "user_story_id": "US-001",
                            "related_acceptance_criteria": [
                                "AC-001-01",
                                ...
                            ]
                        }
                    },
                    ...
                ]
        """
        self.logger.info(f"Generating test cases for {len(acceptance_criteria_data)} user stories")
        
        try:
            # Get raw response from Gemini
            raw_response = self.gemini_client.generate_test_cases(acceptance_criteria_data)
            
            # Parse and clean JSON response
            test_cases = self._clean_and_parse_json(raw_response)
            
            if "error" in test_cases:
                self.logger.error(f"Error in test case generation: {test_cases['error']}")
                return test_cases
                
            # Validate and process test cases
            for i, test_case in enumerate(test_cases):
                if "id" not in test_case or not test_case["id"]:
                    test_case["id"] = f"TC{(i+1):03d}"
                
                # Ensure work item type is set
                if "work_item_type" not in test_case:
                    test_case["work_item_type"] = "Test Case"
                
                # Ensure state is set
                if "state" not in test_case:
                    test_case["state"] = "Design"
                
                # Ensure priority is set (default to 2 if not specified)
                if "priority" not in test_case:
                    test_case["priority"] = "2"
                
                # Ensure tags are set based on priority
                if "tags" not in test_case:
                    priority = test_case.get("priority", "2")
                    test_case["tags"] = f"P{priority}"
                
                # Ensure steps is an array
                if "steps" not in test_case:
                    test_case["steps"] = []
                
                # Ensure references is an object
                if "references" not in test_case:
                    test_case["references"] = {
                        "user_story_id": "",
                        "related_acceptance_criteria": []
                    }
            
            self.logger.info(f"Generated {len(test_cases)} test cases")
            return test_cases
            
        except Exception as e:
            self.logger.error(f"Error generating test cases: {str(e)}")
            return {"error": str(e)}

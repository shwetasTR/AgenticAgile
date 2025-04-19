import json
import logging
import os
from typing import List, Dict
from analyzers.file_analyzer import FileAnalyzer

class FeatureGenerator:
    """
    Generator for extracting features from input text using the Gemini model.
    """
    
    def __init__(self, gemini_client):
        """
        Initialize the feature generator with a Gemini client.
        
        Args:
            gemini_client: An instance of GeminiClient for text generation
        """
        self.gemini_client = gemini_client
        self.file_analyzer = FileAnalyzer()
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Set up a logger for the feature generator."""
        logger = logging.getLogger("FeatureGenerator")
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

    def _create_feature_prompt(self, text: str) -> str:
        """Create a detailed prompt for feature extraction."""
        return f"""
        As a Product Manager, analyze the following requirements and extract key features.
        
        Requirements Text:
        {text}
        
        Guidelines for Feature Extraction:
        - Identify distinct functional capabilities
        - Focus on business value and user needs
        - Consider different user roles and their requirements
        - Break down complex functionality into manageable features
        - Include both functional and non-functional requirements
        
        Format the output as a JSON object with the following structure:
        {{
            "title": "Clear, concise feature title",
            "description": "Detailed description including purpose and scope",
            "user_roles": ["Primary users", "Secondary users"],
            "functionality": [
                "Key function 1",
                "Key function 2"
            ],
            "benefits": [
                "Business/user benefit 1",
                "Business/user benefit 2"
            ]
        }}
        """

    def generate(self, text: str, output_path: str = None) -> dict:
        """
        Extract features from input text and optionally save to JSON.
        
        Args:
            text (str): The input text to process
            output_path (str, optional): Path to save the JSON output
            
        Returns:
            dict: Extracted features
        """
        self.logger.info("Starting feature generation process")
        
        if not text or not text.strip():
            self.logger.warning("Empty or invalid input text received")
            return {
                "title": "No Features Found",
                "description": "Input text was empty or invalid",
                "user_roles": [],
                "functionality": [],
                "benefits": []
            }

        self.logger.info(f"Processing text input of length: {len(text)}")
        
        try:
            # Create and log the prompt
            prompt = self._create_feature_prompt(text)
            self.logger.info("Generated feature extraction prompt")
            self.logger.debug(f"Prompt content: {prompt}")
            
            # Get raw response from Gemini
            raw_response = self.gemini_client.extract_features_from_text(prompt)
            self.logger.debug(f"Raw response from Gemini: {raw_response}")
            
            # ... existing JSON parsing and validation code ...
            
            # Save features if output path is provided
            if output_path and isinstance(raw_response, dict):
                self.save_features_to_json(raw_response, output_path)
            
            return raw_response
            
        except Exception as e:
            self.logger.error(f"Feature generation failed: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "stage": "feature_generation",
                "details": "Check logs for more information"
            }

    def generate_from_files(self, files: List[str], requirements_text: str) -> Dict:
        """Generate features using multiple input files and requirements."""
        try:
            # Analyze all input files
            system_context = self.file_analyzer.analyze_files(files)
            
            prompt = self._create_context_aware_prompt(system_context, requirements_text)
            features = self.gemini_client.extract_features_from_text(prompt)
            
            return features
        except Exception as e:
            self.logger.error(f"Error generating features: {str(e)}")
            return {"error": str(e)}

    def _create_context_aware_prompt(self, system_context: Dict, requirements_text: str) -> str:
        return f"""
        Analyze these requirements in the context of the existing system:

        System Context:
        {json.dumps(system_context, indent=2)}

        Requirements:
        {requirements_text}

        Consider:
        1. Existing Components: {len(system_context['code_components'])} components found
        2. API Endpoints: {len(system_context['api_endpoints'])} endpoints identified
        3. Data Models: {len(system_context['data_models'])} models present
        4. Business Rules: {len(system_context['business_rules'])} rules identified

        Generate features that align with:
        - Existing architectural patterns
        - Current API design
        - Data model structure
        - Business rule constraints
        """

    def save_features_to_json(self, features: dict, output_path: str) -> bool:
        """
        Save extracted features to a JSON file.
        
        Args:
            features (dict): The features to save
            output_path (str): Path where to save the JSON file
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(features, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Features saved successfully to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save features to {output_path}: {str(e)}")
            return False
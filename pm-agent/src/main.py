import sys
import os
import json
import logging
import argparse
from datetime import datetime

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from src.utils.gemini_client import GeminiClient
from src.generators.feature_generator import FeatureGenerator
from src.parsers.pdf_parser import PdfParser
from parsers.notes_parser import NotesParser
from parsers.url_parser import UrlParser

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--requirements", required=True, help="Requirements file (PDF)")
    parser.add_argument("-f", "--reference", help="Reference system file (PDF)")
    args = parser.parse_args()

    # Initialize clients and parsers
    gemini_client = GeminiClient()
    feature_generator = FeatureGenerator(gemini_client)
    pdf_parser = PdfParser()

    try:
        # Parse requirements PDF
        logger.info(f"Parsing requirements file: {args.requirements}")
        requirements_text = pdf_parser.parse(args.requirements)
        
        if not requirements_text:
            logger.error("No text could be extracted from requirements PDF")
            return

        # Parse reference PDF if provided
        reference_text = ""
        if args.reference:
            logger.info(f"Parsing reference file: {args.reference}")
            reference_text = pdf_parser.parse(args.reference)
            if reference_text:
                # Combine the texts with clear separation
                combined_text = f"REQUIREMENTS DOCUMENT:\n{requirements_text}\n\nREFERENCE DOCUMENT:\n{reference_text}"
            else:
                logger.warning("No text extracted from reference PDF. Using only requirements.")
                combined_text = requirements_text
        else:
            combined_text = requirements_text

        # Generate features using the combined text
        features = feature_generator.generate(combined_text)
        print("\nExtracted Features:", json.dumps(features, indent=2))

        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), 'output')
        os.makedirs(output_dir, exist_ok=True)

        # Save features with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        features_path = os.path.join(output_dir, f'features_{timestamp}.json')
        
        with open(features_path, 'w', encoding='utf-8') as f:
            json.dump(features, f, indent=2, ensure_ascii=False)
        print(f"\nFeatures saved to: {features_path}")

        # Continue with user stories and test cases if features were extracted successfully
        if "error" not in features:
            # Generate user stories from features
            logger.info("Generating user stories from features...")
            user_stories = gemini_client.generate_user_stories(features)
            print("\nGenerated User Stories:", json.dumps(user_stories, indent=2))

            # Save user stories to output
            stories_path = os.path.join(output_dir, f'user_stories_{timestamp}.json')
            with open(stories_path, 'w', encoding='utf-8') as f:
                json.dump(user_stories, f, indent=2, ensure_ascii=False)
            print(f"\nUser stories saved to: {stories_path}")

            # Generate test cases from user stories if they were successfully generated
            if "error" not in user_stories:
                logger.info("Generating test cases from user stories...")
                test_cases = gemini_client.generate_test_cases(user_stories)
                print("\nGenerated Test Cases:", json.dumps(test_cases, indent=2))

                # Save test cases to output
                test_cases_path = os.path.join(output_dir, f'test_cases_{timestamp}.json')
                with open(test_cases_path, 'w', encoding='utf-8') as f:
                    json.dump(test_cases, f, indent=2, ensure_ascii=False)
                print(f"\nTest cases saved to: {test_cases_path}")
                
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}", exc_info=True)
        return

if __name__ == "__main__":
    main()
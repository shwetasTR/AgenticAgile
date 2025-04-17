import sys
import os
import json
import logging
from datetime import datetime

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.gemini_client import GeminiClient
from src.generators.feature_generator import FeatureGenerator
from src.parsers.pdf_parser import PdfParser
from src.parsers.notes_parser import NotesParser
from src.parsers.url_parser import UrlParser

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <source_type> <source>")
        print("source_type: pdf, xml, notes, url")
        return

    source_type = sys.argv[1]
    source = sys.argv[2]

    # Initialize clients
    gemini_client = GeminiClient()
    feature_generator = FeatureGenerator(gemini_client)

    # Parse the input based on its type
    if source_type == "pdf":
        parser = PdfParser()
    elif source_type == "notes":
        parser = NotesParser()
    elif source_type == "url":
        parser = UrlParser()
    else:
        print("Invalid source type. Please use pdf, notes, or url")
        return

    # Extract text from source
    text = parser.parse(source)
    if not text:
        print("No text could be extracted from the source")
        return

    try:
        # Generate features
        features = feature_generator.generate(text)
        print("\nExtracted Features:", json.dumps(features, indent=2))

        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), 'output')
        os.makedirs(output_dir, exist_ok=True)

        # Save features
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        features_path = os.path.join(output_dir, f'features_{timestamp}.json')
        with open(features_path, 'w', encoding='utf-8') as f:
            json.dump(features, f, indent=2, ensure_ascii=False)
        print(f"\nFeatures saved to: {features_path}")

        # Generate user stories if features were successfully extracted
        if "error" not in features:
            user_stories = gemini_client.generate_user_stories(features)
            print("\nGenerated User Stories:", json.dumps(user_stories, indent=2))

            # Save user stories
            stories_path = os.path.join(output_dir, f'user_stories_{timestamp}.json')
            with open(stories_path, 'w', encoding='utf-8') as f:
                json.dump(user_stories, f, indent=2, ensure_ascii=False)
            print(f"\nUser stories saved to: {stories_path}")

            # Generate test cases if user stories were successfully generated
            if "error" not in user_stories:
                test_cases = gemini_client.generate_test_cases(user_stories)
                print("\nGenerated Test Cases:", json.dumps(test_cases, indent=2))

                # Save test cases
                test_cases_path = os.path.join(output_dir, f'test_cases_{timestamp}.json')
                with open(test_cases_path, 'w', encoding='utf-8') as f:
                    json.dump(test_cases, f, indent=2, ensure_ascii=False)
                print(f"\nTest cases saved to: {test_cases_path}")

    except Exception as e:
        print(f"\nError during processing: {str(e)}")
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        return

if __name__ == "__main__":
    main()
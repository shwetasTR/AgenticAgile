# PM Agent

## Overview
The PM Agent is a versatile tool designed to extract features from various input sources, including PDF files, XML documents, notes, and URLs. It utilizes dedicated parsers for each input type to ensure accurate and efficient feature extraction.

## Project Structure
```
pm-agent
├── src
│   ├── main.py                # Entry point of the application
│   ├── parsers                # Contains parsers for different input types
│   │   ├── pdf_parser.py      # PDF parser
│   │   ├── xml_parser.py      # XML parser
│   │   ├── notes_parser.py    # Notes parser
│   │   └── url_parser.py      # URL parser
│   ├── features               # Contains feature extraction logic
│   │   └── feature_extractor.py # Feature extractor
│   └── utils                  # Utility functions
│       └── helpers.py         # Helper functions
├── requirements.txt           # Project dependencies
├── README.md                  # Project documentation
└── .gitignore                 # Files to ignore in version control
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd pm-agent
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the PM Agent, execute the following command:
```
python src/main.py
```

## Features
- **PDF Parsing**: Extracts features from PDF files using the `PdfParser`.
- **XML Parsing**: Extracts features from XML files using the `XmlParser`.
- **Notes Parsing**: Extracts features from notes using the `NotesParser`.
- **URL Parsing**: Extracts features from URLs using the `UrlParser`.
- **Feature Aggregation**: Combines features from different sources using the `FeatureExtractor`.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.
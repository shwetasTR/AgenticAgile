# AI Agents Requirements Processor

This project implements an agentic AI approach using three distinct agents to process requirements documents and generate structured output including user stories, acceptance criteria, and test cases.

## Agents

1. **PM Agent**: Reads PDF requirements and creates user stories
2. **BA Agent**: Creates acceptance criteria for each user story
3. **QA Agent**: Generates test cases based on user stories and acceptance criteria

## Prerequisites

- Python 3.8+
- Google Cloud Platform account with Gemini API access
- GCP credentials JSON file

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your Google Cloud credentials:
   - Place your GCP credentials JSON file in a secure location
   - Update the path in `main()` function of `agents.py`

4. Prepare your input files:
   - Place your requirements PDF file in the project directory
   - Update the file paths in `main()` function of `agents.py`

## Usage

1. Run the main script:
   ```bash
   python agents.py
   ```

2. The script will:
   - Process the PDF requirements
   - Generate user stories
   - Create acceptance criteria
   - Generate test cases
   - Output results to `output.json`

## Output Format

The output JSON will have the following structure:

```json
[
  {
    "user_story": {
      "user_type": "string",
      "action": "string",
      "benefit": "string"
    },
    "acceptance_criteria": [
      {
        "given": "string",
        "when": "string",
        "then": "string"
      }
    ],
    "test_cases": [
      {
        "test_id": "string",
        "description": "string",
        "preconditions": "string",
        "steps": ["string"],
        "expected_result": "string",
        "type": "string",
        "priority": "string",
        "status": "string"
      }
    ]
  }
]
```

## Configuration

- Modify `test_case_template.csv` to adjust the test case structure
- Update the Gemini model version in agent initialization if needed

## Note

Make sure to handle your GCP credentials securely and never commit them to version control. 
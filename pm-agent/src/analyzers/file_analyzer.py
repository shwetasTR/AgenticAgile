import os
import json
import yaml
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

class FileAnalyzer:
    def __init__(self):
        self.supported_extensions = {
            '.py': self._analyze_python,
            '.json': self._analyze_json,
            '.yaml': self._analyze_yaml,
            '.yml': self._analyze_yaml,
            '.md': self._analyze_markdown,
            '.feature': self._analyze_gherkin,
            '.sql': self._analyze_sql
        }

    def analyze_files(self, file_paths: List[str]) -> Dict:
        """Analyze multiple files and combine their information."""
        analysis_results = {
            "code_components": [],
            "api_endpoints": [],
            "data_models": [],
            "business_rules": [],
            "technical_requirements": [],
            "existing_features": []
        }

        for file_path in file_paths:
            try:
                ext = Path(file_path).suffix.lower()
                if ext in self.supported_extensions:
                    logger.info(f"Analyzing file: {file_path}")
                    result = self.supported_extensions[ext](file_path)
                    self._merge_results(analysis_results, result)
                else:
                    logger.warning(f"Unsupported file type: {ext}")
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {str(e)}")

        return analysis_results

    def _merge_results(self, main_results: Dict, new_results: Dict):
        """Merge new analysis results into main results."""
        for key in main_results:
            if key in new_results:
                if isinstance(main_results[key], list):
                    main_results[key].extend(new_results[key])
                elif isinstance(main_results[key], dict):
                    main_results[key].update(new_results[key])

    def _analyze_python(self, file_path: str) -> Dict:
        """Extract information from Python files."""
        # Implementation for Python file analysis
        pass

    def _analyze_json(self, file_path: str) -> Dict:
        """Extract information from JSON files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return self._extract_structure(data)

    def _analyze_yaml(self, file_path: str) -> Dict:
        """Extract information from YAML files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return self._extract_structure(data)

    def _analyze_markdown(self, file_path: str) -> Dict:
        """Extract information from Markdown files."""
        # Implementation for Markdown analysis
        pass

    def _analyze_gherkin(self, file_path: str) -> Dict:
        """Extract information from Gherkin feature files."""
        # Implementation for Gherkin feature files
        pass

    def _analyze_sql(self, file_path: str) -> Dict:
        """Extract information from SQL files."""
        # Implementation for SQL files
        pass
class NotesParser:
    def parse(self, file_path):
        """
        Extract text from a plain text notes file.

        Args:
            file_path (str): Path to the notes file

        Returns:
            str: Extracted text
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            return text if text else ""  # Return empty string if no text
        except Exception as e:
            print(f"Error parsing notes file: {e}")
            return ""  # Return empty string in case of error
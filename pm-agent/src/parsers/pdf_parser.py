from PyPDF2 import PdfReader

class PdfParser:
    def parse(self, file_path):
        """
        Extract text from a PDF file.

        Args:
            file_path (str): Path to the PDF file

        Returns:
            str: Extracted text
        """
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text if text else ""  # Return empty string if no text
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return ""  # Return empty string in case of error
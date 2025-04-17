import requests
from bs4 import BeautifulSoup

class UrlParser:
    def parse(self, url):
        """
        Extract text from a webpage.

        Args:
            url (str): The URL of the webpage

        Returns:
            str: Extracted text
        """
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            return text if text else ""  # Return empty string if no text
        except Exception as e:
            print(f"Error parsing URL: {e}")
            return ""  # Return empty string in case of error
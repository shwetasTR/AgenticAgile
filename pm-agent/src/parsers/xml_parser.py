import xml.etree.ElementTree as ET

class XmlParser:
    def parse(self, file_path):
        """
        Extract text from an XML file.

        Args:
            file_path (str): Path to the XML file

        Returns:
            str: Extracted text
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            text = ET.tostring(root, encoding='unicode', method='text')
            return text if text else ""  # Return empty string if no text
        except Exception as e:
            print(f"Error parsing XML: {e}")
            return ""  # Return empty string in case of error
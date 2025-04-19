import logging
from typing import Optional
import os
import PyPDF2
import tempfile
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import shutil

logger = logging.getLogger(__name__)

class PdfParser:
    def __init__(self):
        # Configure pytesseract path to your specific installation location
        pytesseract.pytesseract.tesseract_cmd = r'C:\Users\6111839\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
        
        # Verify if tesseract is actually available at this path
        if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
            logger.warning(f"Tesseract not found at {pytesseract.pytesseract.tesseract_cmd}")
            logger.warning("OCR functionality may not work properly")
            
        # Test if OCR is functioning
        try:
            # Simple test to make sure tesseract is working
            Image.new('RGB', (1, 1)).save('test.png')
            pytesseract.image_to_string('test.png')
            if os.path.exists('test.png'):
                os.remove('test.png')
            logger.info("Tesseract OCR is working correctly")
        except Exception as e:
            logger.error(f"Tesseract OCR test failed: {str(e)}")
            logger.error("Please verify your Tesseract installation")
        
    def parse(self, file_path: str) -> Optional[str]:
        """Parse text from a PDF file with OCR support."""
        if not os.path.exists(file_path):
            logger.error(f"PDF file not found: {file_path}")
            return None

        # First try standard text extraction with PyPDF2
        text = self._extract_with_pypdf2(file_path)
        if text:
            return text
            
        # If that fails, try PyMuPDF (fitz)
        text = self._extract_with_pymupdf(file_path)
        if text:
            return text
            
        # If all else fails, try OCR
        logger.info(f"No text found with direct extraction. Trying OCR on {file_path}")
        return self._extract_with_ocr(file_path)

    def _extract_with_pypdf2(self, file_path: str) -> Optional[str]:
        """Extract text using PyPDF2."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = []
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text.append(page_text)
                        
                if text:
                    extracted_text = "\n".join(text)
                    logger.info(f"Successfully extracted {len(extracted_text)} characters with PyPDF2")
                    return extracted_text
                return None
                
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {str(e)}")
            return None

    def _extract_with_pymupdf(self, file_path: str) -> Optional[str]:
        """Extract text using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
            text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                if page_text and page_text.strip():
                    text.append(page_text)
                    
            if text:
                extracted_text = "\n".join(text)
                logger.info(f"Successfully extracted {len(extracted_text)} characters with PyMuPDF")
                return extracted_text
            return None
            
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {str(e)}")
            return None

    def _extract_with_ocr(self, file_path: str) -> Optional[str]:
        """Extract text using OCR."""
        try:
            # Create temp directory for images
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Convert PDF to images using PyMuPDF
                doc = fitz.open(file_path)
                text = []
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # 2x resolution for better OCR
                    img_path = os.path.join(temp_dir, f"page_{page_num+1}.png")
                    pix.save(img_path)
                    
                    # Perform OCR on the image
                    image = Image.open(img_path)
                    page_text = pytesseract.image_to_string(image)
                    
                    if page_text and page_text.strip():
                        text.append(page_text)
                        
                if text:
                    extracted_text = "\n".join(text)
                    logger.info(f"Successfully extracted {len(extracted_text)} characters with OCR")
                    return extracted_text
                
                logger.error(f"OCR extraction failed to find any text in {file_path}")
                return None
                
            finally:
                # Clean up temp files
                shutil.rmtree(temp_dir)
                
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}", exc_info=True)
            return None
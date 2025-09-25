"""
OCR utilities for image preprocessing and text extraction.
Implements the OCR pipeline as described in the requirements.
"""
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from pdf2image import convert_from_path
import os
import tempfile
import logging

import re
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

# Configure Tesseract path for Linux/Codespaces
TESSERACT_PATHS = [
    '/usr/bin/tesseract',  # Common Linux path
    '/usr/local/bin/tesseract',  # Alternative Linux path
    'tesseract',  # System PATH
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',  # Windows fallback
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',  # Windows fallback
]

def configure_tesseract():
    """Configure Tesseract path for current environment."""
    # Try to use tesseract from system PATH first (Linux/Codespaces)
    import shutil
    tesseract_cmd = shutil.which('tesseract')
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        logger.info(f"Tesseract configured at: {tesseract_cmd}")
        return True
    
    # Fall back to checking explicit paths
    for path in TESSERACT_PATHS:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            logger.info(f"Tesseract found at: {path}")
            return True
    
    logger.warning("Tesseract not found in common paths. Please install tesseract-ocr package.")
    return False

# Try to configure Tesseract on import
configure_tesseract()


class ImageProcessor:
    """Handles image preprocessing for better OCR accuracy"""
    
    @staticmethod
    def preprocess_image(image_path, output_path=None):
        """
        Enhanced preprocessing for better OCR accuracy:
        - Resize image for better recognition
        - Convert to grayscale
        - Apply advanced denoising
        - Enhance contrast
        - Multiple binarization techniques
        - Morphological operations
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Resize image if too small (OCR works better on larger images)
            height, width = img.shape[:2]
            if height < 300 or width < 300:
                scale_factor = max(300/height, 300/width, 2.0)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(blurred)
            
            # Apply multiple binarization techniques and choose the best
            # Method 1: Otsu's thresholding
            _, binary_otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Method 2: Adaptive thresholding
            binary_adaptive = cv2.adaptiveThreshold(
                enhanced, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 15, 3
            )
            
            # Use Otsu's method as it generally works better for product labels
            binary = binary_otsu
            
            # Apply morphological operations to clean up the image
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # Optional: Deskew the image
            binary = ImageProcessor._deskew_image(binary)
            
            # Save preprocessed image if output path provided
            if output_path:
                cv2.imwrite(output_path, binary)
            
            return binary
            
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {str(e)}")
            raise
    
    @staticmethod
    def _deskew_image(image):
        """
        Detect and correct text skew in the image
        """
        try:
            # Find all contours
            contours, _ = cv2.findContours(
                image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Get the largest contour (assumed to be text)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Get minimum area rectangle
                rect = cv2.minAreaRect(largest_contour)
                angle = rect[2]
                
                # Correct the angle
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle
                
                # Only apply correction if significant skew is detected
                if abs(angle) > 0.5:
                    # Get image dimensions
                    (h, w) = image.shape[:2]
                    center = (w // 2, h // 2)
                    
                    # Get rotation matrix and apply rotation
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    rotated = cv2.warpAffine(
                        image, M, (w, h), 
                        flags=cv2.INTER_CUBIC, 
                        borderMode=cv2.BORDER_REPLICATE
                    )
                    return rotated
            
            return image
            
        except Exception as e:
            logger.warning(f"Deskewing failed: {str(e)}")
            return image


class OCREngine:
    """Handles OCR operations using Tesseract"""
    
    def __init__(self, lang='eng'):
        self.lang = lang
        # Configure Tesseract for better accuracy
        # PSM 6: Assume a single uniform block of text
        # OEM 3: Use both legacy and LSTM OCR engines
        self.config = '--oem 3 --psm 6'
    
    def extract_text_from_image(self, image_path, preprocess=True):
        """
        Extract text from image using multiple OCR configurations for best results
        """
        temp_file_path = None
        try:
            # Try multiple OCR configurations
            configs = [
                '--oem 3 --psm 6',  # Single uniform block
                '--oem 3 --psm 4',  # Single text column
                '--oem 3 --psm 8',  # Single word
                '--oem 3 --psm 7',  # Single text line
                '--oem 3 --psm 11', # Sparse text
            ]
            
            best_text = ""
            best_confidence = 0
            
            for config in configs:
                try:
                    if preprocess:
                        # Preprocess image for better OCR
                        if not temp_file_path:
                            temp_file_path = tempfile.mktemp(suffix='.png')
                            processed_img = ImageProcessor.preprocess_image(image_path, temp_file_path)
                        
                        # Extract text with current config
                        text = pytesseract.image_to_string(
                            temp_file_path, lang=self.lang, config=config
                        )
                        
                        # Get confidence score
                        try:
                            data = pytesseract.image_to_data(temp_file_path, config=config, output_type=pytesseract.Output.DICT)
                            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                        except:
                            avg_confidence = len(text.strip())  # Fallback to text length
                            
                    else:
                        # Use original image
                        text = pytesseract.image_to_string(
                            image_path, lang=self.lang, config=config
                        )
                        try:
                            data = pytesseract.image_to_data(image_path, config=config, output_type=pytesseract.Output.DICT)
                            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                        except:
                            avg_confidence = len(text.strip())
                    
                    # Keep the best result
                    if avg_confidence > best_confidence and text.strip():
                        best_text = text
                        best_confidence = avg_confidence
                        
                except Exception as e:
                    logger.debug(f"OCR config {config} failed: {str(e)}")
                    continue
            
            # If no good result, try without preprocessing as fallback
            if not best_text.strip() and preprocess:
                logger.info("Trying OCR without preprocessing as fallback")
                return self.extract_text_from_image(image_path, preprocess=False)
            
            # Clean up the extracted text
            cleaned_text = self._clean_text(best_text)
            logger.info(f"Best OCR result with confidence {best_confidence}: {cleaned_text[:100]}...")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {str(e)}")
            raise
        finally:
            # Ensure temp file cleanup happens even if there's an error
            if temp_file_path:
                safe_temp_file_cleanup(temp_file_path)
    
    def extract_text_from_pdf(self, pdf_path, dpi=300):
        """
        Convert PDF pages to images and extract text using OCR
        """
        temp_files = []
        try:
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=dpi)
            
            full_text = ""
            for i, page in enumerate(pages):
                # Save page as temporary image with better temp file handling
                temp_file_path = tempfile.mktemp(suffix=f'_page_{i+1}.png')
                temp_files.append(temp_file_path)
                
                page.save(temp_file_path, 'PNG')
                
                # Small delay to ensure file is fully written
                import time
                time.sleep(0.1)
                
                # Extract text from page
                page_text = self.extract_text_from_image(temp_file_path, preprocess=False)
                full_text += f"\n--- Page {i+1} ---\n{page_text}\n"
            
            return self._clean_text(full_text)
            
        except Exception as e:
            logger.error(f"PDF OCR failed for {pdf_path}: {str(e)}")
            raise
        finally:
            # Clean up all temp files with safe cleanup
            for temp_file in temp_files:
                safe_temp_file_cleanup(temp_file)
    
    @staticmethod
    def _clean_text(text):
        """
        Enhanced cleaning and normalization of OCR output
        """
        if not text:
            return ""
        
        import re
        
        # First pass: basic cleaning
        # Replace common OCR mistakes
        text = text.replace('|', 'I')  # Common misreading
        text = text.replace('0', 'O')  # In some contexts
        text = text.replace('§', 'S')  # Special characters
        text = text.replace('¢', 'C')
        
        # Fix common character confusions
        text = re.sub(r'(\d)[oO](\d)', r'\1\2', text)  # Remove O between digits
        text = re.sub(r'(\d)[lI](\d)', r'\1\2', text)  # Remove I/l between digits
        
        # Split into lines and process each
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Strip whitespace
            line = line.strip()
            
            # Skip very short lines or lines with only special characters
            if len(line) < 2 or re.match(r'^[^\w\d]*$', line):
                continue
                
            # Remove isolated special characters at start/end
            line = re.sub(r'^[^\w\d]+|[^\w\d]+$', '', line)
            
            # Keep lines that have meaningful content
            if len(line) > 1 and any(c.isalnum() for c in line):
                cleaned_lines.append(line)
        
        # Join lines and final cleanup
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Normalize whitespace
        cleaned_text = re.sub(r' +', ' ', cleaned_text)
        cleaned_text = re.sub(r'\n+', '\n', cleaned_text)
        
        return cleaned_text.strip()


class ComplianceTextProcessor:
    """Process extracted text to find compliance-related information"""
    
    # Enhanced patterns for Indian packaging compliance with better accuracy
    PATTERNS = {
        'mrp': [
            # More comprehensive MRP patterns
            r'(?:MRP|M\.R\.P\.?|Maximum Retail Price|Max\.?\s*Retail\s*Price)[:\s]*₹?\s*Rs\.?\s*(\d{1,4}(?:\.\d{2})?)',
            r'₹\s*(\d{1,4}(?:\.\d{2})?)\s*(?:only|/-)?',
            r'Rs\.?\s*(\d{1,4}(?:\.\d{2})?)\s*(?:only|/-)?',
            r'Price[:\s]*₹?\s*Rs\.?\s*(\d{1,4}(?:\.\d{2})?)',
            r'MRP\s*[:\-]?\s*₹?\s*Rs\.?\s*(\d{1,4}(?:\.\d{2})?)',
            # Pattern for prices in parentheses
            r'\(₹?\s*Rs\.?\s*(\d{1,4}(?:\.\d{2})?)\)',
        ],
        'net_quantity': [
            # Enhanced quantity patterns with more units and variations
            r'(?:Net\s*Qty\.?|Net\s*Quantity|Net\s*Wt\.?|Net\s*Weight|Contents?|Qty\.?)[:\s]*(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|grams|kg|kilogram|ml|millilitre|l|litre|ltr|pieces?|pcs|nos?|units?)',
            r'(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|grams|kg|kilogram|ml|millilitre|l|litre|ltr|pieces?|pcs|nos?|units?)(?:\s|$|\.)',
            r'Quantity[:\s]*(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|grams|kg|kilogram|ml|millilitre|l|litre|ltr|pieces?|pcs|nos?|units?)',
            r'Weight[:\s]*(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|grams|kg|kilogram)',
            # Pattern for weight/quantity at end of product name
            r'(\d+(?:\.\d+)?)\s*(g|gm|gms|kg|ml|l|ltr)\s*(?:pack|packet|bottle|can|jar)?$'
        ],
        'manufacturer': [
            # Enhanced manufacturer patterns
            r'(?:Manufactured\s*by|Mfd\.?\s*by|Producer|Made\s*by|Manufacturer)[:\s]*((?:[A-Za-z][A-Za-z0-9\s\.,&\-\']{5,50}))',
            r'(?:Mfr\.?|Manufacturer)[:\s]*((?:[A-Za-z][A-Za-z0-9\s\.,&\-\']{5,50}))',
            r'(?:Packed\s*by|Packaged\s*by|Packer)[:\s]*((?:[A-Za-z][A-Za-z0-9\s\.,&\-\']{5,50}))',
            r'(?:Marketed\s*by|Marketer)[:\s]*((?:[A-Za-z][A-Za-z0-9\s\.,&\-\']{5,50}))'
        ],
        'country_origin': [
            # Enhanced country patterns
            r'(?:Country\s*of\s*Origin|Made\s*in|Origin)[:\s]*((?:[A-Za-z\s]{3,20}))',
            r'(?:Imported\s*from|Product\s*of)[:\s]*((?:[A-Za-z\s]{3,20}))',
            r'Made\s*in[:\s]*((?:[A-Za-z\s]{3,20}))',
            # Common countries
            r'\b(India|China|USA|UK|Germany|Japan|South\s*Korea|Thailand|Malaysia|Singapore)\b'
        ],
        'manufacturing_date': [
            # Enhanced date patterns with more formats
            r'(?:Mfg\.?\s*Date|Manufacturing\s*Date|Manufactured\s*on|Date\s*of\s*Mfg\.?|DOM)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?:Mfg\.?\s*Date|Manufacturing\s*Date)[:\s]*(\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{2,4})',
            # Month name formats
            r'(?:Mfg\.?\s*Date|Manufacturing\s*Date)[:\s]*(\d{1,2}\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{2,4})',
            # Standalone date patterns (more restrictive)
            r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})\b'
        ],
        'expiry_date': [
            # Enhanced expiry patterns
            r'(?:Best\s*Before|Expiry\s*Date|Exp\.?\s*Date|Use\s*by|Use\s*before)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?:Expires\s*on|Valid\s*till|Valid\s*until)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?:Best\s*Before|Exp\.?\s*Date)[:\s]*(\d{1,2}\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{2,4})',
            # BB format
            r'BB[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
        ],
        'batch_number': [
            # Batch/Lot number patterns
            r'(?:Batch\s*No\.?|Lot\s*No\.?|Batch)[:\s]*([A-Za-z0-9\-\/]{3,15})',
            r'(?:Lot|L\.)[:\s]*([A-Za-z0-9\-\/]{3,15})',
            r'Batch[:\s]*([A-Za-z0-9\-\/]{3,15})'
        ],
        'fssai_license': [
            # FSSAI license patterns
            r'(?:FSSAI\s*Lic\.?\s*No\.?|FSSAI\s*License)[:\s]*(\d{14})',
            r'FSSAI[:\s]*(\d{14})',
            r'Lic\.?\s*No\.?[:\s]*(\d{14})'
        ]
    }
    
    def __init__(self):
        import re
        self.re = re
    
    def extract_compliance_fields(self, text):
        """
        Extract compliance-related fields from OCR text with enhanced accuracy
        """
        results = {}
        
        for field_name, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    if field_name in ['manufacturer', 'country_origin']:
                        # For text fields, clean up the captured group
                        value = match.group(1).strip()
                        # Remove common OCR artifacts and clean text
                        value = re.sub(r'[^\w\s\.,&\-\']', ' ', value)
                        value = ' '.join(value.split())  # Normalize whitespace
                        if len(value) > 3 and not value.isdigit():  # Only accept meaningful text
                            results[field_name] = value
                            break
                    elif field_name in ['net_quantity']:
                        # Combine number and unit for quantity
                        if len(match.groups()) >= 2:
                            number = match.group(1).strip()
                            unit = match.group(2).strip().lower()
                            # Normalize common unit variations
                            unit_map = {
                                'gm': 'g', 'gms': 'g', 'gram': 'g', 'grams': 'g',
                                'kilogram': 'kg', 'millilitre': 'ml', 'litre': 'l', 
                                'ltr': 'l', 'pieces': 'pcs', 'nos': 'pcs', 'units': 'pcs'
                            }
                            unit = unit_map.get(unit, unit)
                            results[field_name] = f"{number} {unit}"
                        else:
                            results[field_name] = match.group(1)
                        break
                    elif field_name in ['mrp']:
                        # Clean up price values
                        price = match.group(1).strip()
                        # Ensure it's a valid number
                        try:
                            float(price)
                            results[field_name] = f"₹{price}"
                        except ValueError:
                            continue
                        break
                    elif field_name in ['manufacturing_date', 'expiry_date']:
                        # Validate and normalize date format
                        date_str = match.group(1).strip()
                        # Basic date validation
                        if self._validate_date_format(date_str):
                            results[field_name] = date_str
                            break
                    else:
                        # For other fields (batch_number, fssai_license, etc.)
                        value = match.group(1).strip()
                        if len(value) > 2:
                            results[field_name] = value
                            break
        
        return results
    
    def _validate_date_format(self, date_str):
        """
        Basic validation for date format
        """
        # Check if it matches basic date patterns
        date_patterns = [
            r'^\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}$',
            r'^\d{1,2}\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{2,4}$'
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, date_str, re.IGNORECASE):
                return True
        return False
    
    def calculate_compliance_score(self, extracted_fields, required_fields):
        """
        Calculate compliance score based on detected vs required fields
        """
        if not required_fields:
            return 0
        
        detected_count = len([field for field in required_fields if field in extracted_fields])
        total_required = len(required_fields)
        
        return int((detected_count / total_required) * 100)


class PDFProcessor:
    """Handles PDF to image conversion and OCR processing."""
    
    def __init__(self):
        self.ocr_engine = OCREngine()
        self.text_processor = ComplianceTextProcessor()
    
    def convert_pdf_to_images(self, pdf_path: str, output_dir: str = None, dpi: int = 300) -> List[str]:
        """
        Convert PDF pages to high-resolution images.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save images (optional)
            dpi: Resolution for conversion (default 300 DPI)
            
        Returns:
            List of image file paths
        """
        try:
            from pdf2image import convert_from_path
            import tempfile
            
            # Create output directory if not provided
            if output_dir is None:
                output_dir = tempfile.mkdtemp()
            
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=dpi)
            image_paths = []
            
            for i, page in enumerate(pages):
                image_path = os.path.join(output_dir, f'page_{i+1}.png')
                page.save(image_path, 'PNG')
                image_paths.append(image_path)
                logger.info(f"Converted page {i+1} to {image_path}")
            
            return image_paths
            
        except ImportError:
            logger.error("pdf2image not available. Please install: pip install pdf2image")
            raise
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: str, preprocess: bool = True) -> str:
        """
        Extract text from all pages of a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            preprocess: Whether to preprocess images before OCR
            
        Returns:
            Combined text from all pages
        """
        image_paths = []
        try:
            # Convert PDF to images
            image_paths = self.convert_pdf_to_images(pdf_path)
            
            full_text = ""
            
            # Process each page
            for i, image_path in enumerate(image_paths):
                try:
                    page_text = self.ocr_engine.extract_text_from_image(image_path, preprocess=preprocess)
                    full_text += f"\n\n--- Page {i+1} ---\n{page_text}"
                except Exception as page_error:
                    logger.warning(f"Failed to process page {i+1}: {page_error}")
                    full_text += f"\n\n--- Page {i+1} ---\n[ERROR: Could not process page]"
            
            return full_text.strip()
            
        except Exception as e:
            logger.error(f"PDF text extraction failed: {str(e)}")
            return ""
        finally:
            # Clean up all temporary images with safe cleanup
            for image_path in image_paths:
                safe_temp_file_cleanup(image_path)
    
    def process_legal_document(self, pdf_path: str) -> dict:
        """
        Process a legal document PDF and extract structured information.
        
        Args:
            pdf_path: Path to the legal document PDF
            
        Returns:
            Dictionary with extracted information
        """
        try:
            # Extract text from PDF
            full_text = self.extract_text_from_pdf(pdf_path)
            
            # Basic legal document processing
            sections = self._split_into_sections(full_text)
            rules = self._extract_rules(full_text)
            
            return {
                'full_text': full_text,
                'sections': sections,
                'rules': rules,
                'total_pages': len(self.convert_pdf_to_images(pdf_path)),
                'processed_at': __import__('time').strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Legal document processing failed: {str(e)}")
            return {
                'full_text': '',
                'sections': [],
                'rules': [],
                'total_pages': 0,
                'error': str(e)
            }
    
    def _split_into_sections(self, text: str) -> List[dict]:
        """Split document into sections based on common patterns."""
        sections = []
        
        # Common section patterns
        section_patterns = [
            r'(Rule\s+\d+[.\s]*[^\n]+)',
            r'(Chapter\s+\d+[.\s]*[^\n]+)',
            r'(Section\s+\d+[.\s]*[^\n]+)',
            r'(\d+\.\s+[A-Z][^\n]+)',
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                sections.append({
                    'title': match.group(1).strip(),
                    'start_pos': match.start(),
                    'type': 'rule' if 'Rule' in match.group(1) else 'section'
                })
        
        # Sort by position
        sections.sort(key=lambda x: x['start_pos'])
        
        return sections
    
    def _extract_rules(self, text: str) -> List[dict]:
        """Extract specific rules and their content."""
        rules = []
        
        # Pattern for rules with content
        rule_pattern = r'(Rule\s+(\d+)[.\s]*([^\n]+))\n((?:(?!Rule\s+\d+)[\s\S])*?)(?=Rule\s+\d+|\Z)'
        
        matches = re.finditer(rule_pattern, text, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            rule_number = match.group(2)
            rule_title = match.group(3).strip()
            rule_content = match.group(4).strip()
            
            rules.append({
                'number': rule_number,
                'title': rule_title,
                'content': rule_content[:500] + '...' if len(rule_content) > 500 else rule_content,
                'full_content': rule_content
            })
        
        return rules


# Utility functions
def safe_temp_file_cleanup(file_path: str, max_retries: int = 3) -> bool:
    """
    Safely clean up temporary files with retries for Windows file locking issues.
    
    Args:
        file_path: Path to the temporary file to delete
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if file was successfully deleted, False otherwise
    """
    if not os.path.exists(file_path):
        return True
    
    import time
    
    for attempt in range(max_retries):
        try:
            os.unlink(file_path)
            return True
        except (OSError, PermissionError) as e:
            if attempt < max_retries - 1:
                # Wait a bit before retrying
                time.sleep(0.1 * (attempt + 1))
                logger.debug(f"Retry {attempt + 1} for cleaning up {file_path}")
            else:
                logger.warning(f"Could not clean up temp file {file_path} after {max_retries} attempts: {e}")
                return False
    
    return False


def _calculate_field_confidence(fields: dict) -> dict:
    """
    Calculate confidence scores for extracted fields based on pattern matching quality.
    
    Args:
        fields: Dictionary of extracted fields
        
    Returns:
        Dictionary with confidence scores for each field
    """
    confidence_scores = {}
    
    for field_name, value in fields.items():
        if field_name in ['mrp']:
            # Numeric fields - check if properly formatted
            try:
                float_val = float(value.replace('₹', '').replace('Rs.', '').strip())
                confidence_scores[field_name] = 0.9 if float_val > 0 else 0.3
            except:
                confidence_scores[field_name] = 0.3
                
        elif field_name in ['net_quantity']:
            # Quantity fields - check if has valid unit
            units = ['g', 'kg', 'ml', 'l', 'gm', 'gms', 'ltr', 'litre', 'pieces', 'pcs']
            has_valid_unit = any(unit in value.lower() for unit in units)
            has_number = any(char.isdigit() for char in value)
            confidence_scores[field_name] = 0.8 if (has_valid_unit and has_number) else 0.4
            
        elif field_name in ['manufacturing_date', 'expiry_date']:
            # Date fields - check if follows date format
            date_pattern = r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}'
            confidence_scores[field_name] = 0.9 if re.match(date_pattern, value) else 0.5
            
        elif field_name in ['manufacturer', 'country_origin']:
            # Text fields - check length and content quality
            if len(value) > 10 and not value.isupper():
                confidence_scores[field_name] = 0.7
            elif len(value) > 5:
                confidence_scores[field_name] = 0.5
            else:
                confidence_scores[field_name] = 0.3
        else:
            confidence_scores[field_name] = 0.6  # Default confidence
    
    return confidence_scores


def get_tesseract_version() -> str:
    """
    Get the version of installed Tesseract OCR.
    
    Returns:
        Version string or error message
    """
    try:
        return pytesseract.get_tesseract_version()
    except Exception as e:
        return f"Error getting version: {str(e)}"


def validate_image_for_ocr(image_path: str) -> dict:
    """
    Validate if an image is suitable for OCR processing.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with validation results
    """
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            return {'valid': False, 'error': 'File does not exist'}
        
        # Try to read the image
        img = cv2.imread(image_path)
        if img is None:
            return {'valid': False, 'error': 'Cannot read image file'}
        
        # Check image dimensions
        height, width = img.shape[:2]
        if height < 50 or width < 50:
            return {'valid': False, 'error': 'Image too small for OCR'}
        
        # Check file size (should be reasonable)
        file_size = os.path.getsize(image_path)
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            return {'valid': False, 'error': 'Image file too large'}
        
        return {
            'valid': True,
            'dimensions': f"{width}x{height}",
            'file_size': f"{file_size // 1024} KB",
            'channels': len(img.shape) if len(img.shape) > 2 else 1
        }
        
    except Exception as e:
        return {'valid': False, 'error': f"Validation error: {str(e)}"}


def quick_compliance_check(image_path: str, required_fields: List[str] = None) -> dict:
    """
    Perform a quick compliance check on an image without full processing.
    
    Args:
        image_path: Path to the image file
        required_fields: List of required compliance fields
        
    Returns:
        Dictionary with quick compliance results
    """
    if required_fields is None:
        required_fields = ['mrp', 'net_quantity', 'manufacturer']
    
    try:
        # Validate image first
        validation = validate_image_for_ocr(image_path)
        if not validation['valid']:
            return {
                'status': 'error',
                'error': validation['error'],
                'fields_found': {},
                'score': 0
            }
        
        # Quick OCR with minimal preprocessing and better error handling
        ocr_engine = OCREngine()
        
        # Try OCR with fallback mechanism
        text = ""
        try:
            # First try without preprocessing to avoid temp file issues
            text = ocr_engine.extract_text_from_image(image_path, preprocess=False)
        except Exception as ocr_error:
            logger.warning(f"OCR without preprocessing failed: {ocr_error}")
            try:
                # Fallback: try with preprocessing but with more robust temp file handling
                text = ocr_engine.extract_text_from_image(image_path, preprocess=True)
            except Exception as fallback_error:
                logger.error(f"OCR with preprocessing also failed: {fallback_error}")
                return {
                    'status': 'error',
                    'error': f"OCR failed: {str(fallback_error)}",
                    'fields_found': {},
                    'score': 0
                }
        
        # Quick field extraction
        text_processor = ComplianceTextProcessor()
        fields = text_processor.extract_compliance_fields(text)
        
        # Calculate basic score
        found_fields = [field for field in required_fields if field in fields]
        score = int((len(found_fields) / len(required_fields)) * 100) if required_fields else 0
        
        return {
            'status': 'success',
            'fields_found': {field: fields[field] for field in found_fields},
            'score': score,
            'total_fields_required': len(required_fields),
            'fields_detected': len(found_fields),
            'image_info': validation,
            'extracted_text_length': len(text)
        }
        
    except Exception as e:
        logger.error(f"Quick compliance check failed: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'fields_found': {},
            'score': 0
        }


# Convenience functions
def process_pdf_document(pdf_path: str) -> dict:
    """
    Process a PDF document with OCR.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Dictionary with extracted information
    """
    processor = PDFProcessor()
    return processor.process_legal_document(pdf_path)


def extract_compliance_from_image(image_path: str) -> dict:
    """
    Complete compliance checking pipeline for a single image.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary with compliance results
    """
    ocr_engine = OCREngine()
    text_processor = ComplianceTextProcessor()
    
    # Extract text
    text = ocr_engine.extract_text_from_image(image_path, preprocess=True)
    
    # Detect fields
    fields = text_processor.extract_compliance_fields(text)
    
    # Define required fields for scoring
    required_fields = ['mrp', 'net_quantity', 'manufacturer', 'country_origin']
    
    # Calculate score
    score = text_processor.calculate_compliance_score(fields, required_fields)
    
    # Determine status
    if score >= 80:
        status = 'pass'
    elif score >= 50:
        status = 'partial'
    else:
        status = 'fail'
    
    return {
        'extracted_text': text,
        'fields': fields,
        'score': score,
        'status': status,
        'confidence': _calculate_field_confidence(fields)
    }
# mistral_ocr.py
import os
import base64
import logging
from mistralai import Mistral

logger = logging.getLogger(__name__)


def encode_image(image_path):
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        logger.error(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:
        logger.error(f"Error encoding image: {e}")
        return None


class MistralOCR:
    def __init__(self):
        # Get API key from environment variable
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY not set in environment variables")
        
        self.client = Mistral(api_key=self.api_key)

    def extract_compliance_fields(self, image_path, active_fields):
        """
        Extract text from image using Mistral OCR API and detect compliance fields.
        Always returns a dict in the format expected by your serializers.
        """
        try:
            logger.debug(f"Starting OCR extraction for image: {image_path}")
            
            # Encode image to base64
            base64_image = encode_image(image_path)
            if not base64_image:
                return {"success": False, "error": "Failed to encode image"}
            
            logger.debug(f"Image encoded successfully, length: {len(base64_image)}")
            
            # Use Mistral OCR API
            logger.debug("Making Mistral OCR API call...")
            
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}" 
                },
                include_image_base64=True
            )
            
            logger.debug("Mistral OCR API call successful")
            logger.debug(f"OCR Response: {ocr_response}")
            
            # Extract the text from OCR response
            # The response structure may vary, so we'll check different possible fields
            extracted_text = ""
            if hasattr(ocr_response, 'text'):
                extracted_text = ocr_response.text
            elif hasattr(ocr_response, 'content'):
                extracted_text = ocr_response.content
            elif isinstance(ocr_response, dict):
                extracted_text = ocr_response.get('text', '') or ocr_response.get('content', '') or str(ocr_response)
            else:
                extracted_text = str(ocr_response)
            
            logger.debug(f"Extracted text: {extracted_text}")
            
            # Process fields detection
            detected_fields_data = []
            for field in active_fields:
                detected, value, confidence = self._find_field_in_text(extracted_text, field)
                detected_fields_data.append({
                    'field': field.name,
                    'detected': detected,
                    'value': value,
                    'confidence': confidence
                })
            
            return {
                "success": True,
                "raw_text": extracted_text,
                "detected_fields": detected_fields_data
            }

        except Exception as e:
            logger.error(f"Error in extract_compliance_fields: {str(e)}")
            return {"success": False, "error": f"OCR processing failed: {str(e)}"}

    def _find_field_in_text(self, text, field):
        """
        Search for a specific compliance field in the extracted text.
        Returns (detected: bool, value: str, confidence: float)
        """
        import re
        
        # Create keyword variations based on field name
        field_keywords = self._get_field_keywords(field.name)
        
        # Search for field patterns in text
        for keyword in field_keywords:
            # Case-insensitive search for the keyword
            pattern = rf'{re.escape(keyword)}\s*[:\-=]?\s*([^\n\r,;]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            
            if match:
                value = match.group(1).strip()
                confidence = 0.8  # Base confidence for pattern match
                return True, value, confidence
        
        return False, "", 0.0

    def _get_field_keywords(self, field_name):
        """
        Generate keyword variations for field detection based on field name.
        """
        keywords = [field_name.lower()]
        
        # Add common variations based on field name
        field_mapping = {
            'mrp': ['mrp', 'maximum retail price', 'max retail price', 'price', 'cost'],
            'net_quantity': ['net quantity', 'net weight', 'net content', 'quantity', 'weight', 'contents'],
            'manufacturer': ['manufacturer', 'manufactured by', 'mfg by', 'made by', 'producer'],
            'manufacturing_date': ['manufacturing date', 'mfg date', 'manufactured on', 'production date', 'made on'],
            'expiry_date': ['expiry date', 'exp date', 'expires on', 'best before', 'use before', 'use by'],
            'batch_number': ['batch number', 'batch no', 'lot number', 'lot no'],
            'country_origin': ['country of origin', 'made in', 'origin', 'country'],
            'ingredients': ['ingredients', 'contains', 'composition'],
        }
        
        # Check if field name matches any predefined mappings
        for key, values in field_mapping.items():
            if field_name.lower() in key or key in field_name.lower():
                keywords.extend(values)
                break
        
        return list(set(keywords))  # Remove duplicates

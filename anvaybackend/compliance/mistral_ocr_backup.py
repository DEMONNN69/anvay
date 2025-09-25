"""
Mistral AI OCR implementation for image text extraction.
Uses Mistral's vision model to extract text from product compliance images.
"""
import base64
import os
from mistralai import Mistral
import logging

logger = logging.getLogger(__name__)

class MistralOCR:
    """OCR implementation using Mistral AI's vision capabilities"""
    
    def __init__(self):
        """Initialize Mistral OCR with API key from environment."""
        self.api_key = os.environ.get("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable not set")
        
        # Specify model
        self.model = "pixtral-12b-2409"
        
        # Initialize the Mistral client
        self.client = Mistral(api_key=self.api_key)
    
def encode_image(image_path):
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        logger.error(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    
    def extract_text_from_image(self, image_path):
        """
        Extract text from image using Mistral AI vision model.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            str: Extracted text from the image
        """
        try:
            # Getting the base64 string
            base64_image = encode_image(image_path)
            
            if not base64_image:
                raise ValueError("Failed to encode image to base64")
            
            # Define the messages for the chat
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this product label image. Focus on product details like MRP, net content, batch number, manufacturing date, expiry date, manufacturer details, and any other text visible on the label. Provide only the extracted text content."
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{base64_image}" 
                        }
                    ]
                }
            ]
            
            # Get the chat response
            chat_response = self.client.chat.complete(
                model=self.model,
                messages=messages
            )
            
            # Extract the content of the response
            extracted_text = chat_response.choices[0].message.content
            logger.info(f"Mistral OCR extracted text: {extracted_text[:100]}...")
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error in Mistral OCR: {str(e)}")
            raise Exception(f"Mistral OCR failed: {str(e)}")

    def extract_compliance_fields(self, image_path, compliance_fields):
        """
        Extract compliance fields from image using Mistral OCR.
        
        Args:
            image_path (str): Path to the image file
            compliance_fields (QuerySet): Django queryset of ComplianceField objects
        
        Returns:
            tuple: (extracted_text, detected_fields_data)
        """
        try:
            # Extract text using Mistral OCR
            extracted_text = self.extract_text_from_image(image_path)
            
            # Process the fields to find matches
            detected_fields_data = []
            
            for field in compliance_fields:
                detected, value, confidence = self._find_field_in_text(extracted_text, field)
                detected_fields_data.append({
                    'field': field,
                    'detected': detected,
                    'value': value,
                    'confidence': confidence
                })
            
            return extracted_text, detected_fields_data
            
        except Exception as e:
            logger.error(f"Error in extract_compliance_fields: {e}")
            raise
    
    def _find_field_in_text(self, text, field):
        """
        Find a specific compliance field in the extracted text.
        
        Args:
            text (str): Extracted text from OCR
            field (ComplianceField): The field to search for
        
        Returns:
            tuple: (detected, value, confidence)
        """
        import re
        
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        field_name_lower = field.name.lower()
        
        # Define patterns for common compliance fields
        patterns = {
            'mrp': [
                r'(?:mrp|m\.r\.p|maximum retail price)[:\s]*[₹rs\.]*\s*(\d+(?:\.\d{2})?)',
                r'price[:\s]*[₹rs\.]*\s*(\d+(?:\.\d{2})?)',
            ],
            'net quantity': [
                r'(?:net\s*(?:quantity|content|wt|weight))[:\s]*(\d+(?:\.\d+)?\s*(?:ml|g|kg|l|gm))',
                r'(?:quantity|content)[:\s]*(\d+(?:\.\d+)?\s*(?:ml|g|kg|l|gm))',
            ],
            'manufacturer': [
                r'(?:manufactured\s*by|mfg\s*by|produced\s*by)[:\s]*([a-zA-Z\s&\.]+?)(?:\n|,|$)',
                r'(?:manufacturer)[:\s]*([a-zA-Z\s&\.]+?)(?:\n|,|$)',
            ],
            'country of origin': [
                r'(?:country\s*of\s*origin|made\s*in|origin)[:\s]*([a-zA-Z\s]+?)(?:\n|,|$)',
            ],
            'manufacturing date': [
                r'(?:mfg\s*date|manufacturing\s*date|date)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'(?:date)[:\s]*(\d{1,2}[\/\-\.]\d{4})',
            ],
            'expiry date': [
                r'(?:exp\s*date|expiry\s*date|use\s*before)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            ],
            'batch number': [
                r'(?:batch\s*no|lot\s*no|batch)[:\s]*([a-zA-Z0-9\/\-\.]+)',
            ]
        }
        
        # Get patterns for this field
        field_patterns = []
        for key, pattern_list in patterns.items():
            if key in field_name_lower:
                field_patterns.extend(pattern_list)
        
        # If no specific patterns, use a general search
        if not field_patterns:
            # General pattern to find text after field name
            field_patterns = [
                rf'(?:{re.escape(field_name_lower)})[:\s]*([^\n,]+)',
            ]
        
        # Search for patterns
        for pattern in field_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value = match.group(1).strip()
                if value and len(value) > 1:  # Valid value found
                    confidence = 0.8  # High confidence for pattern match
                    return True, value, confidence
        
        # If no pattern match, check for simple keyword presence
        if field_name_lower in text_lower:
            # Extract text around the field name
            index = text_lower.find(field_name_lower)
            if index != -1:
                # Get text after the field name (next 50 characters)
                start = index + len(field_name_lower)
                end = min(start + 50, len(text))
                surrounding_text = text[start:end].strip()
                
                # Clean up the extracted text
                value = re.sub(r'^[:\s\-]+', '', surrounding_text)  # Remove leading punctuation
                value = re.split(r'[\n,]', value)[0].strip()  # Take first line/segment
                
                if value and len(value) > 0:
                    confidence = 0.6  # Medium confidence for keyword match
                    return True, value, confidence
        
        # Field not found
        return False, "", 0.0

# Example usage
if __name__ == "__main__":
    try:
        ocr = MistralOCR()
        # You would replace this with an actual image path
        # result = ocr.extract_text_from_image("/path/to/your/image.jpg")
        # print(result)
    except Exception as e:
        print(f"Error: {e}")


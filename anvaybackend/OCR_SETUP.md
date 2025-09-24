# OCR Setup Instructions

## Installation Steps

### 1. Install Python Dependencies
```bash
# In your activated virtual environment
pip install -r requirements.txt
```

### 2. Install Tesseract OCR

**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\Program Files\Tesseract-OCR\`
3. The system will auto-detect the installation

**Alternative Windows locations:**
- `C:\Program Files (x86)\Tesseract-OCR\`
- `C:\Users\{username}\AppData\Local\Programs\Tesseract-OCR\`

### 3. Install Poppler (for PDF processing)
1. Download from: http://blog.alivate.com.au/poppler-windows/
2. Extract to `C:\poppler\`
3. Add `C:\poppler\bin` to system PATH

### 4. Test Installation
```bash
python manage.py test_ocr
```

## Features Now Available

### Image OCR Processing
- Advanced image preprocessing (grayscale, blur, thresholding, skew correction)
- Tesseract OCR integration
- Confidence scoring
- Automatic field detection for compliance checking

### PDF Document Processing
- Convert PDF to high-resolution images (300 DPI)
- Extract text from legal documents
- Split documents into sections and rules
- Process Legal Metrology documents

### Compliance Field Detection
- MRP (Maximum Retail Price)
- Net Quantity
- Manufacturer details
- Country of Origin
- Manufacturing Date

## Usage

### Basic Image OCR
```python
from compliance.ocr_utils import extract_compliance_from_image

result = extract_compliance_from_image('path/to/image.jpg')
# Returns: {'extracted_text': '...', 'fields': {...}, 'score': 85, 'status': 'pass'}
```

### PDF Processing
```python
from compliance.ocr_utils import process_pdf_document

result = process_pdf_document('legal_document.pdf')
# Returns: {'full_text': '...', 'sections': [...], 'rules': [...]}
```

## Fallback Behavior

If OCR libraries are not installed, the system will:
1. Use mock data for demonstrations
2. Log warnings about missing dependencies
3. Continue functioning with sample compliance results

This ensures your app works even without OCR setup for development/testing purposes.
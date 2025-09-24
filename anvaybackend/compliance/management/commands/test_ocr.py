"""
Instructions for installing Tesseract OCR on Windows

STEP 1: Download Tesseract OCR for Windows
=========================================

1. Go to: https://github.com/UB-Mannheim/tesseract/wiki
2. Download the latest Windows installer (tesseract-ocr-w64-setup-v5.3.3.20231005.exe or similar)
3. Run the installer as Administrator
4. Install to one of these locations:
   - C:\Program Files\Tesseract-OCR\
   - C:\Program Files (x86)\Tesseract-OCR\

STEP 2: Install Python Dependencies
==================================

Run the following command in your virtual environment:

pip install -r requirements.txt

This will install:
- pytesseract==0.3.10
- opencv-python==4.8.1.78
- pdf2image==1.16.3
- numpy==1.24.3
- scipy==1.11.4

STEP 3: Install Poppler (for PDF processing)
===========================================

1. Download Poppler for Windows from: http://blog.alivate.com.au/poppler-windows/
2. Extract to C:\poppler-xx.xx.x\
3. Add C:\poppler-xx.xx.x\bin to your system PATH

STEP 4: Test Installation
========================

After installation, test OCR by running:

python manage.py test_ocr

STEP 5: Configure Tesseract Path (if needed)
==========================================

If Tesseract is installed in a custom location, update the path in:
compliance/ocr_utils.py

Set the correct path in the TESSERACT_PATHS list or set:
pytesseract.pytesseract.tesseract_cmd = r'C:\your\custom\path\tesseract.exe'

TROUBLESHOOTING
==============

1. If you get "tesseract is not installed" error:
   - Verify Tesseract is installed and in PATH
   - Check the path in ocr_utils.py

2. If you get "poppler not found" error:
   - Install Poppler and add to PATH
   - Or set POPPLER_PATH in settings.py

3. If OpenCV installation fails:
   - Try: pip install opencv-python-headless

4. For best OCR results:
   - Use high-resolution images (300 DPI or higher)
   - Ensure good contrast and lighting
   - Images should be straight (not skewed)
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test Tesseract OCR installation and configuration'
    
    def handle(self, *args, **options):
        self.stdout.write("Testing Tesseract OCR installation...")
        
        try:
            import pytesseract
            from PIL import Image
            import cv2
            import numpy as np
            
            self.stdout.write(self.style.SUCCESS("✓ All required packages imported successfully"))
            
            # Test Tesseract installation
            try:
                version = pytesseract.get_tesseract_version()
                self.stdout.write(self.style.SUCCESS(f"✓ Tesseract version: {version}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Tesseract not found: {e}"))
                self.stdout.write("Please install Tesseract OCR following the instructions above.")
                return
            
            # Test OCR with a simple image
            try:
                from compliance.ocr_utils import OCRProcessor, ComplianceFieldDetector
                
                # Create a simple test image with text
                img = np.zeros((100, 400, 3), dtype=np.uint8)
                img.fill(255)  # White background
                
                # Convert to PIL and save temporarily
                pil_img = Image.fromarray(img)
                test_path = '/tmp/test_ocr.png' if os.name != 'nt' else 'test_ocr.png'
                pil_img.save(test_path)
                
                # Test OCR
                ocr = OCRProcessor()
                text = ocr.extract_text(test_path, preprocess=False)
                
                self.stdout.write(self.style.SUCCESS("✓ OCR processing test completed"))
                
                # Test field detection
                detector = ComplianceFieldDetector()
                test_text = "MRP: Rs. 150\nNet Quantity: 500g\nManufactured by: ABC Foods\nMade in India\nMfg Date: 01/2024"
                fields = detector.detect_fields(test_text)
                
                detected_count = sum(1 for field in fields.values() if field['detected'])
                self.stdout.write(self.style.SUCCESS(f"✓ Field detection test: {detected_count}/5 fields detected"))
                
                # Clean up
                if os.path.exists(test_path):
                    os.remove(test_path)
                
            except ImportError as e:
                self.stdout.write(self.style.WARNING(f"⚠ OCR modules not available: {e}"))
                self.stdout.write("The app will use fallback mock processing.")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ OCR test failed: {e}"))
            
            self.stdout.write("\n" + "="*50)
            self.stdout.write("OCR INSTALLATION SUMMARY")
            self.stdout.write("="*50)
            self.stdout.write("If all tests passed, your OCR setup is ready!")
            self.stdout.write("If tests failed, please follow the installation instructions.")
            self.stdout.write("The app will work with mock data even without OCR.")
            
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"✗ Required packages not installed: {e}"))
            self.stdout.write("Please run: pip install -r requirements.txt")
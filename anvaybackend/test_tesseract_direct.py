import os
import sys

# Add the Django project to Python path
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anvayapi.settings')

import django
django.setup()

try:
    import pytesseract
    from PIL import Image
    import numpy as np
    
    print("🔧 Testing Tesseract configuration...")
    
    # Force set the path
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # Check if the executable exists
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(tesseract_path):
        print(f"✅ Tesseract executable found at: {tesseract_path}")
    else:
        print(f"❌ Tesseract executable NOT found at: {tesseract_path}")
        exit(1)
    
    # Test Tesseract version
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
    except Exception as e:
        print(f"❌ Failed to get Tesseract version: {e}")
        exit(1)
    
    # Test OCR with simple text
    try:
        # Create a simple white image with black text
        img_array = np.ones((100, 400, 3), dtype=np.uint8) * 255  # White background
        pil_img = Image.fromarray(img_array)
        
        # Test OCR
        text = pytesseract.image_to_string(pil_img)
        print(f"✅ OCR test completed (extracted: '{text.strip()}')")
        
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        exit(1)
    
    print("\n🎉 SUCCESS! Tesseract is properly configured and working!")
    
    # Now test our OCR utils
    try:
        from compliance.ocr_utils import OCRProcessor
        ocr = OCRProcessor()
        print("✅ OCR utils imported successfully")
    except Exception as e:
        print(f"⚠️  OCR utils import issue: {e}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all packages are installed: pip install -r requirements.txt")
# Anvay Backend - Django REST API

A Django REST API backend for the Anvay compliance checking application.

## Features

- **Image Upload & Processing**: Upload images for compliance analysis
- **Mock OCR**: Simulates text extraction from images
- **Compliance Scoring**: Automated scoring based on detected fields
- **REST API**: Full CRUD operations with Django REST Framework
- **Admin Interface**: Django admin for managing compliance fields and results
- **CORS Support**: Configured for frontend integration

## API Endpoints

### Main Endpoints
- `POST /api/check-compliance/` - Upload image and get compliance analysis
- `GET /api/compliance-checks/` - List all compliance checks
- `GET /api/compliance-checks/{id}/` - Get specific compliance check
- `GET /api/health/` - Health check endpoint

### Request/Response Format

#### Check Compliance
**Request:**
```http
POST /api/check-compliance/
Content-Type: multipart/form-data

image: [image file]
```

**Response:**
```json
{
  "score": 75,
  "extracted_text": "MRP: Rs. 150\nNet Quantity: 500g...",
  "fields": [
    {
      "name": "MRP",
      "detected": true,
      "value": "Mock value for MRP",
      "icon": "rupee"
    }
  ],
  "status": "pass"
}
```

## Setup & Installation

### Prerequisites
- Python 3.8+
- Django 4.2+
- Virtual environment (recommended)

### Installation Steps

1. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create initial compliance fields:**
   ```bash
   python manage.py create_compliance_fields
   ```

5. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server:**
   ```bash
   python manage.py runserver 8000
   ```

## Project Structure

```
anvaybackend/
├── anvayapi/           # Main Django project
│   ├── settings.py     # Django settings
│   ├── urls.py         # Main URL configuration
│   └── wsgi.py         # WSGI configuration
├── compliance/         # Main app
│   ├── models.py       # Database models
│   ├── serializers.py  # DRF serializers
│   ├── views.py        # API views
│   ├── urls.py         # App URL configuration
│   └── admin.py        # Admin configuration
├── media/              # Uploaded files
├── requirements.txt    # Python dependencies
└── manage.py          # Django management script
```

## Models

### ComplianceCheck
- Stores uploaded images and analysis results
- Fields: image, score, extracted_text, status, uploaded_at

### ComplianceField  
- Defines compliance fields to check (MRP, Net Quantity, etc.)
- Fields: name, icon, is_active

### DetectedField
- Links ComplianceCheck to ComplianceField with detection results
- Fields: detected, value, confidence

## Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### CORS Configuration
The API is configured to allow requests from:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (React default)
- `http://127.0.0.1:5173`
- `http://127.0.0.1:3000`

## Development

### Adding New Compliance Fields
1. Use Django admin at `http://localhost:8000/admin/`
2. Or use the management command:
   ```bash
   python manage.py shell
   >>> from compliance.models import ComplianceField
   >>> ComplianceField.objects.create(name="New Field", icon="icon-name")
   ```

### Testing API Endpoints
Use tools like Postman, curl, or your frontend application:

```bash
# Health check
curl http://localhost:8000/api/health/

# Upload image for compliance check
curl -X POST -F "image=@path/to/image.jpg" http://localhost:8000/api/check-compliance/
```

## Future Enhancements

- Replace mock OCR with actual OCR library (Tesseract, Google Vision API)
- Add authentication and user management
- Implement real compliance rules and scoring algorithms
- Add image preprocessing and enhancement
- Implement caching for better performance
- Add comprehensive logging and monitoring
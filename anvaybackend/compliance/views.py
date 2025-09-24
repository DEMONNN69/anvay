from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import ComplianceCheck, ComplianceField
from .serializers import (
    ComplianceCheckCreateSerializer, 
    ComplianceCheckSerializer,
    ComplianceResultSerializer
)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def check_compliance(request):
    """
    Handle image upload and compliance checking.
    Expects a file upload with key 'image'.
    """
    if 'image' not in request.FILES:
        return Response(
            {'error': 'No image file provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = ComplianceCheckCreateSerializer(data=request.data)
    if serializer.is_valid():
        compliance_check = serializer.save()
        
        # Transform the response to match frontend expectations
        detected_fields = compliance_check.detected_fields.all()
        fields_data = []
        
        for detected_field in detected_fields:
            fields_data.append({
                'name': detected_field.field.name,
                'detected': detected_field.detected,
                'value': detected_field.value,
                'icon': detected_field.field.icon
            })
        
        response_data = {
            'score': compliance_check.score,
            'extracted_text': compliance_check.extracted_text,
            'fields': fields_data,
            'status': compliance_check.status
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_compliance_check(request, pk):
    """
    Retrieve a specific compliance check by ID.
    """
    compliance_check = get_object_or_404(ComplianceCheck, pk=pk)
    serializer = ComplianceCheckSerializer(compliance_check)
    return Response(serializer.data)


@api_view(['GET'])
def list_compliance_checks(request):
    """
    List all compliance checks with pagination.
    """
    compliance_checks = ComplianceCheck.objects.all()
    serializer = ComplianceCheckSerializer(compliance_checks, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def health_check(request):
    """
    Simple health check endpoint.
    """
    return Response({'status': 'healthy', 'message': 'Compliance API is running'})

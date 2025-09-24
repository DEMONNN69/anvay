from rest_framework import serializers
from .models import ComplianceCheck, ComplianceField, DetectedField


class ComplianceFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceField
        fields = ['id', 'name', 'icon', 'is_active']


class DetectedFieldSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='field.name', read_only=True)
    icon = serializers.CharField(source='field.icon', read_only=True)
    
    class Meta:
        model = DetectedField
        fields = ['name', 'icon', 'detected', 'value', 'confidence']


class ComplianceCheckSerializer(serializers.ModelSerializer):
    detected_fields = DetectedFieldSerializer(many=True, read_only=True)
    
    class Meta:
        model = ComplianceCheck
        fields = [
            'id', 'image', 'uploaded_at', 'score', 
            'extracted_text', 'status', 'detected_fields'
        ]
        read_only_fields = ['uploaded_at']


class ComplianceCheckCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceCheck
        fields = ['image']
    
    def create(self, validated_data):
        # Create the compliance check
        compliance_check = ComplianceCheck.objects.create(**validated_data)
        
        # Mock OCR and compliance analysis - in production, this would be replaced
        # with actual image processing and compliance checking logic
        self._process_image(compliance_check)
        
        return compliance_check
    
    def _process_image(self, compliance_check):
        """
        Mock function to simulate image processing and compliance checking.
        In production, this would use OCR libraries and actual compliance rules.
        """
        import random
        
        # Mock extracted text
        mock_texts = [
            "MRP: Rs. 150\nNet Quantity: 500g\nManufactured by: ABC Foods Pvt Ltd\nCountry of Origin: India\nMfg Date: 01/2024",
            "Maximum Retail Price: ₹250\nNet Wt: 1kg\nProduced by: XYZ Industries\nMade in India\nManufacturing Date: March 2024",
            "Price: Rs. 99\nQuantity: 250ml\nManufacturer: Sample Company\nOrigin: India\nDate: 15/03/2024"
        ]
        
        compliance_check.extracted_text = random.choice(mock_texts)
        
        # Get all active compliance fields
        active_fields = ComplianceField.objects.filter(is_active=True)
        
        # Create detected fields with mock data
        total_fields = active_fields.count()
        detected_count = 0
        
        for field in active_fields:
            # Mock detection logic - randomly detect fields with higher probability for some
            detection_probability = {
                'MRP': 0.8,
                'Net Quantity': 0.7,
                'Manufacturer': 0.6,
                'Country of Origin': 0.5,
                'Manufacturing Date': 0.4,
            }.get(field.name, 0.5)
            
            detected = random.random() < detection_probability
            if detected:
                detected_count += 1
            
            DetectedField.objects.create(
                compliance_check=compliance_check,
                field=field,
                detected=detected,
                value=f"Mock value for {field.name}" if detected else None,
                confidence=random.uniform(0.6, 0.95) if detected else 0.0
            )
        
        # Calculate compliance score based on detected fields
        if total_fields > 0:
            compliance_check.score = int((detected_count / total_fields) * 100)
        else:
            compliance_check.score = 0
        
        # Determine status based on score
        if compliance_check.score >= 60:
            compliance_check.status = 'pass'
        elif compliance_check.score >= 40:
            compliance_check.status = 'partial'
        else:
            compliance_check.status = 'fail'
        
        compliance_check.save()


class ComplianceResultSerializer(serializers.Serializer):
    """
    Serializer that matches the frontend's expected response format
    """
    score = serializers.IntegerField()
    extracted_text = serializers.CharField()
    fields = serializers.ListSerializer(child=serializers.DictField())
    status = serializers.CharField()
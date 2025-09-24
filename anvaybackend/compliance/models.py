from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class ComplianceCheck(models.Model):
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('partial', 'Partial'),
        ('fail', 'Fail'),
    ]
    
    image = models.ImageField(upload_to='compliance_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    extracted_text = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='fail')
    fields_data = models.JSONField(default=dict)  # Store detected fields as JSON
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Compliance Check {self.id} - {self.status.title()} ({self.score}%)"


class ComplianceField(models.Model):
    ICON_CHOICES = [
        ('rupee', 'Rupee'),
        ('package', 'Package'),
        ('building', 'Building'),
        ('globe', 'Globe'),
        ('calendar', 'Calendar'),
    ]
    
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=20, choices=ICON_CHOICES)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class DetectedField(models.Model):
    compliance_check = models.ForeignKey(
        ComplianceCheck, 
        on_delete=models.CASCADE, 
        related_name='detected_fields'
    )
    field = models.ForeignKey(ComplianceField, on_delete=models.CASCADE)
    detected = models.BooleanField(default=False)
    value = models.TextField(blank=True, null=True)
    confidence = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ['compliance_check', 'field']
    
    def __str__(self):
        return f"{self.field.name} - {'Detected' if self.detected else 'Not Detected'}"

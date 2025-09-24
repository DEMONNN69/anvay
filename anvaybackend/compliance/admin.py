from django.contrib import admin
from .models import ComplianceCheck, ComplianceField, DetectedField


@admin.register(ComplianceField)
class ComplianceFieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'is_active']
    list_filter = ['is_active', 'icon']
    search_fields = ['name']


class DetectedFieldInline(admin.TabularInline):
    model = DetectedField
    extra = 0
    readonly_fields = ['confidence']


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ['id', 'uploaded_at', 'score', 'status']
    list_filter = ['status', 'uploaded_at']
    search_fields = ['extracted_text']
    readonly_fields = ['uploaded_at', 'extracted_text', 'score', 'status']
    inlines = [DetectedFieldInline]
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation through admin


@admin.register(DetectedField)
class DetectedFieldAdmin(admin.ModelAdmin):
    list_display = ['compliance_check', 'field', 'detected', 'confidence']
    list_filter = ['detected', 'field']
    readonly_fields = ['confidence']

from django.urls import path
from . import views

app_name = 'compliance'

urlpatterns = [
    path('check-compliance/', views.check_compliance, name='check_compliance'),
    path('compliance-checks/', views.list_compliance_checks, name='list_compliance_checks'),
    path('compliance-checks/<int:pk>/', views.get_compliance_check, name='get_compliance_check'),
    path('health/', views.health_check, name='health_check'),
]
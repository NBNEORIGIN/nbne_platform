"""
Tenant branding endpoint alias — serves /api/tenant/branding/
Returns config in the format the NBNE-style frontend expects.
"""
from django.urls import path
from .tenant_views import tenant_branding_view

urlpatterns = [
    path('', tenant_branding_view, name='tenant-branding'),
]

"""
Tenant settings endpoint alias — serves /api/tenant/
Returns config in the format the NBNE-style frontend expects.
"""
from django.urls import path
from .tenant_views import tenant_settings_view

urlpatterns = [
    path('', tenant_settings_view, name='tenant-settings'),
]

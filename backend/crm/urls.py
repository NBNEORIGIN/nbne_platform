from django.urls import path
from . import views

urlpatterns = [
    path('leads/', views.list_leads, name='crm-leads'),
    path('leads/create/', views.create_lead, name='crm-lead-create'),
    path('leads/<int:lead_id>/status/', views.update_lead_status, name='crm-lead-status'),
    path('leads/export/', views.export_leads_csv, name='crm-leads-export'),
    path('sync/', views.sync_from_bookings, name='crm-sync'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('leads/', views.list_leads, name='crm-leads'),
    path('leads/create/', views.create_lead, name='crm-lead-create'),
    path('leads/quick-add/', views.quick_add, name='crm-quick-add'),
    path('leads/export/', views.export_leads_csv, name='crm-leads-export'),
    path('leads/<int:lead_id>/update/', views.update_lead, name='crm-lead-update'),
    path('leads/<int:lead_id>/status/', views.update_lead, name='crm-lead-status'),
    path('leads/<int:lead_id>/contact/', views.action_contact, name='crm-lead-contact'),
    path('leads/<int:lead_id>/convert/', views.action_convert, name='crm-lead-convert'),
    path('leads/<int:lead_id>/followup-done/', views.action_followup_done, name='crm-lead-followup-done'),
    path('leads/<int:lead_id>/notes/', views.lead_notes, name='crm-lead-notes'),
    path('leads/<int:lead_id>/history/', views.lead_history, name='crm-lead-history'),
    path('sync/', views.sync_from_bookings, name='crm-sync'),
]

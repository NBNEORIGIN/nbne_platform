from django.contrib import admin
from core.admin_tenant import TenantAdminMixin
from .models import StaffProfile, Shift, LeaveRequest, TrainingRecord, AbsenceRecord


@admin.register(StaffProfile)
class StaffProfileAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['display_name', 'user', 'phone', 'is_active', 'hire_date']
    list_filter = ['is_active']
    search_fields = ['display_name', 'user__email']


@admin.register(Shift)
class ShiftAdmin(TenantAdminMixin, admin.ModelAdmin):
    tenant_field = 'staff__tenant'
    list_display = ['staff', 'date', 'start_time', 'end_time', 'location', 'is_published']
    list_filter = ['is_published', 'date']
    date_hierarchy = 'date'


@admin.register(LeaveRequest)
class LeaveRequestAdmin(TenantAdminMixin, admin.ModelAdmin):
    tenant_field = 'staff__tenant'
    list_display = ['staff', 'leave_type', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'leave_type']


@admin.register(TrainingRecord)
class TrainingRecordAdmin(TenantAdminMixin, admin.ModelAdmin):
    tenant_field = 'staff__tenant'
    list_display = ['staff', 'title', 'provider', 'completed_date', 'expiry_date']
    search_fields = ['title']


@admin.register(AbsenceRecord)
class AbsenceRecordAdmin(TenantAdminMixin, admin.ModelAdmin):
    tenant_field = 'staff__tenant'
    list_display = ['staff', 'record_type', 'date', 'is_authorised']
    list_filter = ['record_type', 'is_authorised']

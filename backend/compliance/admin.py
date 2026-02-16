from django.contrib import admin
from core.admin_tenant import TenantAdminMixin
from .models import (
    IncidentReport, IncidentPhoto, SignOff, RAMSDocument,
    RiskAssessment, HazardFinding, Equipment, EquipmentInspection, ComplianceCategory,
    ComplianceItem, PeaceOfMindScore, ScoreAuditLog,
)


# --- Inlines ---

class IncidentPhotoInline(admin.TabularInline):
    model = IncidentPhoto
    extra = 0


class SignOffInline(admin.TabularInline):
    model = SignOff
    extra = 0
    readonly_fields = ['signed_at']


class HazardFindingInline(admin.TabularInline):
    model = HazardFinding
    extra = 0
    fields = ['category', 'description', 'severity', 'status', 'regulatory_ref', 'due_date']


class EquipmentInspectionInline(admin.TabularInline):
    model = EquipmentInspection
    extra = 0
    readonly_fields = ['created_at']


# --- Incidents ---

@admin.register(IncidentReport)
class IncidentReportAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'severity', 'status', 'location', 'incident_date', 'reported_by']
    list_filter = ['severity', 'status']
    search_fields = ['title', 'description']
    date_hierarchy = 'incident_date'
    inlines = [IncidentPhotoInline, SignOffInline]


@admin.register(IncidentPhoto)
class IncidentPhotoAdmin(admin.ModelAdmin):
    list_display = ['incident', 'caption', 'uploaded_at']


@admin.register(SignOff)
class SignOffAdmin(admin.ModelAdmin):
    list_display = ['incident', 'signed_by', 'role', 'signed_at']


# --- Risk Assessments & Findings ---

@admin.register(RiskAssessment)
class RiskAssessmentAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'site_area', 'assessor', 'assessment_date', 'review_date', 'findings_count_display', 'high_risk_display', 'status']
    list_filter = ['status', 'assessment_date']
    search_fields = ['title', 'site_area', 'description']
    date_hierarchy = 'assessment_date'
    inlines = [HazardFindingInline]

    def findings_count_display(self, obj):
        return obj.findings_count
    findings_count_display.short_description = 'Findings'

    def high_risk_display(self, obj):
        count = obj.high_risk_count
        if count > 0:
            return f'{count} ⚠️'
        return '0'
    high_risk_display.short_description = 'High Risk'


@admin.register(HazardFinding)
class HazardFindingAdmin(admin.ModelAdmin):
    list_display = ['category', 'short_description', 'severity', 'status', 'assessment', 'regulatory_ref', 'due_date']
    list_filter = ['severity', 'status', 'category']
    search_fields = ['category', 'description', 'regulatory_ref']

    def short_description(self, obj):
        return obj.description[:80] + '...' if len(obj.description) > 80 else obj.description
    short_description.short_description = 'Description'


# --- Equipment ---

@admin.register(Equipment)
class EquipmentAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'location', 'category', 'last_inspection', 'next_inspection', 'status', 'is_overdue_display']
    list_filter = ['status', 'category']
    search_fields = ['name', 'location', 'serial_number']
    inlines = [EquipmentInspectionInline]

    def is_overdue_display(self, obj):
        return obj.is_overdue
    is_overdue_display.boolean = True
    is_overdue_display.short_description = 'Overdue?'


@admin.register(EquipmentInspection)
class EquipmentInspectionAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'inspection_date', 'inspector', 'result', 'next_due']
    list_filter = ['result', 'inspection_date']
    date_hierarchy = 'inspection_date'


# --- Compliance Scoring ---

class ComplianceItemInline(admin.TabularInline):
    model = ComplianceItem
    extra = 0
    fields = ['title', 'item_type', 'status', 'due_date', 'regulatory_ref']


@admin.register(ComplianceCategory)
class ComplianceCategoryAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'current_score', 'max_score', 'percentage_display', 'order']
    list_editable = ['current_score', 'max_score', 'order']
    ordering = ['order']
    inlines = [ComplianceItemInline]

    def percentage_display(self, obj):
        pct = obj.percentage
        if pct >= 80:
            return f'{pct}% ✅'
        elif pct >= 60:
            return f'{pct}% ⚠️'
        return f'{pct}% ❌'
    percentage_display.short_description = 'Score %'


@admin.register(ComplianceItem)
class ComplianceItemAdmin(TenantAdminMixin, admin.ModelAdmin):
    tenant_field = 'category__tenant'
    list_display = ['title', 'category', 'item_type', 'status', 'weight_display', 'due_date', 'regulatory_ref']
    list_filter = ['item_type', 'status', 'category']
    search_fields = ['title', 'description', 'regulatory_ref']
    list_editable = ['status']
    actions = ['mark_compliant', 'mark_due_soon', 'mark_overdue']

    def weight_display(self, obj):
        return f'{obj.weight}x'
    weight_display.short_description = 'Weight'

    def mark_compliant(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='COMPLIANT', completed_at=timezone.now())
        from .models import PeaceOfMindScore
        PeaceOfMindScore.recalculate()
        self.message_user(request, f'{queryset.count()} item(s) marked compliant. Score recalculated.')
    mark_compliant.short_description = 'Mark selected as Compliant'

    def mark_due_soon(self, request, queryset):
        queryset.update(status='DUE_SOON')
        from .models import PeaceOfMindScore
        PeaceOfMindScore.recalculate()
        self.message_user(request, f'{queryset.count()} item(s) marked due soon. Score recalculated.')
    mark_due_soon.short_description = 'Mark selected as Due Soon'

    def mark_overdue(self, request, queryset):
        queryset.update(status='OVERDUE')
        from .models import PeaceOfMindScore
        PeaceOfMindScore.recalculate()
        self.message_user(request, f'{queryset.count()} item(s) marked overdue. Score recalculated.')
    mark_overdue.short_description = 'Mark selected as Overdue'


@admin.register(PeaceOfMindScore)
class PeaceOfMindScoreAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['score_display', 'colour', 'interpretation', 'total_items', 'compliant_count', 'due_soon_count', 'overdue_count', 'last_calculated_at']
    readonly_fields = ['score', 'previous_score', 'total_items', 'compliant_count', 'due_soon_count', 'overdue_count', 'legal_items', 'best_practice_items', 'last_calculated_at']

    def score_display(self, obj):
        return f'{obj.score}%'
    score_display.short_description = 'Peace of Mind Score'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ScoreAuditLog)
class ScoreAuditLogAdmin(admin.ModelAdmin):
    list_display = ['calculated_at', 'score', 'previous_score', 'change_display', 'trigger', 'total_items', 'compliant_count', 'overdue_count']
    list_filter = ['trigger', 'calculated_at']
    readonly_fields = ['score', 'previous_score', 'total_items', 'compliant_count', 'due_soon_count', 'overdue_count', 'trigger', 'calculated_at']
    date_hierarchy = 'calculated_at'

    def change_display(self, obj):
        change = obj.score - obj.previous_score
        if change > 0:
            return f'+{change}%'
        elif change < 0:
            return f'{change}%'
        return '0%'
    change_display.short_description = 'Change'

    def has_add_permission(self, request):
        return False


# --- RAMS ---

@admin.register(RAMSDocument)
class RAMSDocumentAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'reference_number', 'status', 'issue_date', 'expiry_date', 'is_expired_display']
    list_filter = ['status']
    search_fields = ['title', 'reference_number']

    def is_expired_display(self, obj):
        return obj.is_expired
    is_expired_display.boolean = True
    is_expired_display.short_description = 'Expired?'

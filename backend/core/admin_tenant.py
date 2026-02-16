"""
TenantAdminMixin — restricts Django admin querysets to the current user's tenant.

Usage:
    class MyModelAdmin(TenantAdminMixin, admin.ModelAdmin):
        ...

For models where tenant is accessed via a relation (e.g. ComplianceItem → category__tenant),
override `tenant_field` on the admin class:
    tenant_field = 'category__tenant'
"""


class TenantAdminMixin:
    """Restrict admin querysets to the logged-in user's tenant."""
    tenant_field = 'tenant'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        tenant = getattr(request.user, 'tenant', None)
        if tenant:
            return qs.filter(**{self.tenant_field: tenant})
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, 'tenant') and not obj.tenant_id:
            obj.tenant = getattr(request.user, 'tenant', None)
        super().save_model(request, obj, form, change)

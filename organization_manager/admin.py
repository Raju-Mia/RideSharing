from django.contrib import admin

# Register your models here.
from organization_manager.models import (
    Organization,
    OrganizationBankAccount,
    OrganizationAccount,
    OrganizationTransaction,
    )


admin.site.register(Organization)
admin.site.register(OrganizationBankAccount)
admin.site.register(OrganizationAccount)
admin.site.register(OrganizationTransaction)

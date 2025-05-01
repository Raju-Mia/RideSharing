from django.contrib import admin

# Register your models here.
from third_party_org_manager.models import OrganizationCustomer, ConciageTripInvoice, ConciageTripSummaryInvoice


admin.site.register(OrganizationCustomer)
admin.site.register(ConciageTripInvoice)
admin.site.register(ConciageTripSummaryInvoice)
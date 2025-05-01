from django.contrib import admin
from payment.models import ClientWallet, DriverWallet, OrganizationWallet, Transaction


admin.site.register(ClientWallet)
admin.site.register(DriverWallet)
admin.site.register(OrganizationWallet)
admin.site.register(Transaction)



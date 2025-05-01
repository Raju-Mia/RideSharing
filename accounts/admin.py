from django.contrib import admin
from django.contrib.auth import get_user_model
from driver_app.models import Driver
from accounts.models import (
    Admin,
    CustomUser,
    UserProfile,
    VerificationOTP,
    VerificationTokens,
    PhoneEmailChangeState,
    SavedPlace,

)


User = get_user_model()
from uc_admin.models import OperatorPermission


class OperatorPermissionInline(admin.TabularInline):
    model = OperatorPermission


class CustomUserAdmin(admin.ModelAdmin):
    inlines = [OperatorPermissionInline]

    list_display = (
        "is_driver",
        "id",
        "is_online",
        "email",
        "phone",
        "email_is_verified",
        "phone_is_verified",
        "service",
    )
    def is_driver(self, obj):
        return Driver.objects.filter(user=obj).exists()
    is_driver.boolean = True  # Display as a boolean icon in the admin panel
    is_driver.short_description = "Driver"



admin.site.register(Admin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserProfile)
admin.site.register(VerificationOTP)
admin.site.register(VerificationTokens)
admin.site.register(PhoneEmailChangeState)
admin.site.register(SavedPlace)

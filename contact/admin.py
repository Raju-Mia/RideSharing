from django.contrib import admin
from .models import Contact, Newsletter, ComplaintBox

# Register your models here.

# contact admin
admin.site.register(Contact)

# newsletter admin
admin.site.register(Newsletter)


# complain box admin
@admin.register(ComplaintBox)
class ComplaintBoxAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "trip", "title", "status", "created_at", "created_by"]
    list_filter = ["id", "title", "status", "created_at"]
    search_fields = ["id", "user__email", "trip__id", "title", "status"]

    ordering = ["-created_at"]

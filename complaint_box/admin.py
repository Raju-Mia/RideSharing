from django.contrib import admin
from complaint_box.models import ComplaintBox, Remark, ComplaintPicture
# Register your models here.


@admin.register(ComplaintBox)
class ComplaintBoxAdmin(admin.ModelAdmin):
    list_display = ('id', 'case_id')  
    list_filter = ('id', 'case_id')  
    search_fields = ('id', 'case_id')  


@admin.register(ComplaintPicture)
class ComplaintPictureAdmin(admin.ModelAdmin):
    list_display = ('id', 'complaint')  
    list_filter = ('id', 'complaint')  
    search_fields = ('id', 'complaint__id')  


@admin.register(Remark)
class RemarkAdmin(admin.ModelAdmin):
    list_display = ('id', 'complaint')  
    list_filter = ('id', 'complaint')  
    search_fields = ('id', 'complaint__id')  

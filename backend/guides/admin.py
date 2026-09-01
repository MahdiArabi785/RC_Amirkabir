# guides/admin.py
from django.contrib import admin

from .models import Guide


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    # قبلاً admin.py کاملاً خالی بود - Guide اصلاً در پنل ادمین قابل
    # مدیریت نبود.
    list_display = ['title', 'filename', 'is_active', 'download_count', 'uploaded_at']
    list_editable = ['is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'description']
    readonly_fields = ['download_count', 'uploaded_at', 'updated_at']
    date_hierarchy = 'uploaded_at'
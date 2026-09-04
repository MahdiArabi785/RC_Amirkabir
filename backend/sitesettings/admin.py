# sitesettings/admin.py
from django.contrib import admin

from .models import Banner, SiteSettings, Supporter


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    # singleton: هیچ‌وقت اجازه‌ی افزودن رکورد دوم یا حذف رکورد موجود
    # داده نمی‌شود - پنل فقط برای ویرایش همان یک رکورد است.
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'subtitle']


@admin.register(Supporter)
class SupporterAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
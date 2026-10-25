# events/admin.py
from django.contrib import admin
from django.utils import timezone

from .models import Call, Event, News


class PublishAtOnSaveMixin:
    """وقتی is_published=True و published_at خالی است، ست می‌کند.
    رفع باگ list_editable = ['is_published'] که published_at را ست نمی‌کرد."""

    def save_model(self, request, obj, form, change):
        if obj.is_published and not obj.published_at:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(News)
class NewsAdmin(PublishAtOnSaveMixin, admin.ModelAdmin):
    list_display = ['title', 'is_published', 'is_active', 'published_at', 'view_count']
    list_editable = ['is_published']
    list_filter = ['is_published', 'is_active']
    search_fields = ['title', 'summary']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    date_hierarchy = 'published_at'


@admin.register(Event)
class EventAdmin(PublishAtOnSaveMixin, admin.ModelAdmin):
    list_display = [
        'title', 'event_type', 'start_date', 'end_date',
        'is_published', 'is_active', 'view_count',
    ]
    list_editable = ['is_published']
    list_filter = ['event_type', 'is_published', 'is_active']
    search_fields = ['title', 'location']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(Call)
class CallAdmin(PublishAtOnSaveMixin, admin.ModelAdmin):
    list_display = [
        'title', 'call_type', 'deadline',
        'is_published', 'is_active', 'view_count',
    ]
    list_editable = ['is_published']
    list_filter = ['call_type', 'is_published', 'is_active']
    search_fields = ['title', 'contact_email']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    date_hierarchy = 'deadline'
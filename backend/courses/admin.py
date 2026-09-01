# courses/admin.py
from django.contrib import admin

from .models import Course, Video


class VideoInline(admin.TabularInline):
    model = Video
    extra = 1
    fields = ['title', 'video_file', 'thumbnail', 'order', 'duration']
    ordering = ['order']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_active', 'created_at']
    list_editable = ['is_active']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'description']
    list_filter = ['is_active', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [VideoInline]


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'duration', 'created_at']
    list_filter = ['course']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']
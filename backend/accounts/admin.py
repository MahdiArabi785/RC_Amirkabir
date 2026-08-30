# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Article, Course, CustomUser, ResearchProject


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'phone', 'full_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'phone', 'password')}),
        ('اطلاعات شخصی', {
            'fields': ('first_name', 'last_name', 'full_name', 'avatar',
                       'bio', 'organization', 'field_of_study'),
        }),
        ('لینک‌ها', {'fields': ('website', 'linkedin', 'google_scholar')}),
        ('دسترسی‌ها', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'role',
                       'groups', 'user_permissions'),
        }),
        ('تاریخ‌های مهم', {'fields': ('last_login', 'date_joined')}),
        ('تأیید هویت', {'fields': ('is_verified',)}),
    )
    # کدهای otp_code/otp_expiry عمداً از پنل ادمین حذف شده‌اند: نمایش کد
    # ورود فعال یک کاربر به هر کاربر staff، حتی برای پشتیبانی، ریسک امنیتی
    # غیرضروری است.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'password1', 'password2', 'role'),
        }),
    )
    readonly_fields = ('last_login', 'date_joined')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'abstract')
    autocomplete_fields = ('authors', 'created_by')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active',)
    search_fields = ('title',)
    autocomplete_fields = ('teacher', 'students')


@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'lead', 'status', 'start_date', 'end_date')
    list_filter = ('status',)
    search_fields = ('title',)
    autocomplete_fields = ('lead', 'team_members')
# sitesettings/permissions.py
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """خواندن (لوگو/بنرها برای صفحه‌ی اصلی) برای همه آزاد است. نوشتن
    فقط برای ادمین - همان معیار is_admin استفاده‌شده در بقیه‌ی اپ‌های
    پروژه (accounts/events/guides/courses)."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return getattr(user, 'is_admin', user.is_staff)
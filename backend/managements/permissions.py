# =============================================================================
# managements/permissions.py
# مجوزهای دسترسی برای پنل مدیریت
# =============================================================================

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """دسترسی کامل فقط برای ادمین‌ها (role='admin' یا is_superuser)"""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'is_admin', False)
        )


class IsAdminOrReadOnly(BasePermission):
    """خواندن برای همه، نوشتن فقط برای ادمین"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return IsAdmin().has_permission(request, view)


class IsSuperUser(BasePermission):
    """فقط سوپرادمین"""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )


class IsAuthenticatedOrReadOnly(BasePermission):
    """خواندن برای همه، نوشتن برای کاربران لاگین‌شده"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)
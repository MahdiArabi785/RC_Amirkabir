# core/permissions.py
"""
مجوزها و helperهای مشترک — از تکرار در events/guides/sitesettings/managements
جلوگیری می‌کند.

تنها منبع تصمیم‌گیری برای «ادمین بودن» همین `is_admin_user` است.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_admin_user(user) -> bool:
    """آیا این کاربر ادمین است؟ (شامل role='admin' و is_superuser)"""
    return bool(
        user
        and user.is_authenticated
        and getattr(user, 'is_admin', False)
    )


class IsAdmin(BasePermission):
    """فقط ادمین‌ها."""
    message = 'این عملیات فقط برای ادمین‌ها مجاز است.'

    def has_permission(self, request, view):
        return is_admin_user(request.user)


class IsAdminOrReadOnly(BasePermission):
    """خواندن برای همه، نوشتن فقط برای ادمین."""
    message = 'فقط ادمین می‌تواند این عملیات را انجام دهد.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return is_admin_user(request.user)


class IsSuperUser(BasePermission):
    """فقط سوپریوزرها (برای عملیات حساس مثل حذف ادمین)."""
    message = 'این عملیات فقط برای سوپریوزرها مجاز است.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsOwnerOrAdmin(BasePermission):
    """صاحب شیء یا ادمین — برای endpointهای پروفایل."""
    def has_object_permission(self, request, view, obj):
        if is_admin_user(request.user):
            return True
        # اگر obj.user دارد
        owner = getattr(obj, 'user', None) or getattr(obj, 'created_by', None)
        return owner == request.user
# core/permissions.py
"""تنها منبع تصمیم‌گیری برای «ادمین بودن»."""
from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_admin_user(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and getattr(user, 'is_admin', False)
    )


class IsAdmin(BasePermission):
    message = 'این عملیات فقط برای ادمین‌ها مجاز است.'

    def has_permission(self, request, view):
        return is_admin_user(request.user)


class IsAdminOrReadOnly(BasePermission):
    message = 'فقط ادمین می‌تواند این عملیات را انجام دهد.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return is_admin_user(request.user)


class IsSuperUser(BasePermission):
    message = 'این عملیات فقط برای سوپریوزرها مجاز است.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if is_admin_user(request.user):
            return True
        owner = getattr(obj, 'user', None) or getattr(obj, 'created_by', None)
        return owner == request.user

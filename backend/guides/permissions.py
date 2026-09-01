# guides/permissions.py
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """اجازه‌ی تغییر (POST/PUT/PATCH/DELETE) فقط به ادمین‌ها داده می‌شود.

    قبلاً فقط user.is_staff بررسی می‌شد؛ برای هماهنگی با معیار دسترسی
    استفاده‌شده در accounts/events (CustomUser.is_admin)، همین‌جا هم به
    آن سوییچ شده - با fallback امن به is_staff اگر مدل کاربر is_admin
    نداشته باشد.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return getattr(user, 'is_admin', user.is_staff)
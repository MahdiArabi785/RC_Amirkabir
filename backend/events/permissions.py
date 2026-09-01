# events/permissions.py
from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """خواندن (GET/HEAD/OPTIONS) برای همه آزاد است. نوشتن (POST/PUT/PATCH/
    DELETE) فقط برای ادمین‌ها.

    قبلاً این‌جا فقط user.is_staff بررسی می‌شد، در حالی‌که اپ accounts
    مفهوم گسترده‌تر CustomUser.is_admin (role == 'admin' یا is_superuser)
    را برای همین منظور در کل پروژه استفاده می‌کند. اینجا هم به همان
    معیار سوییچ شده تا سیاست دسترسی در همه‌ی اپ‌ها یکسان بماند؛ اگر
    مدل کاربر به هر دلیلی is_admin نداشت (مثلاً در تست‌ها با یک User
    استاندارد جنگو)، به‌صورت امن به is_staff برمی‌گردد.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return getattr(user, 'is_admin', user.is_staff)
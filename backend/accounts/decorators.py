# accounts/decorators.py
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def admin_required(view_func):
    """اجازه‌ی دسترسی فقط به ادمین‌های لاگین‌شده.

    قبلاً کاربر ناشناس (anonymous) هم مستقیماً 403 می‌گرفت که تجربه‌ی
    کاربری بدی است (باید به صفحه‌ی ورود هدایت شود، نه پیام «دسترسی
    غیرمجاز»). همچنین شرط تشخیص ادمین قبلاً فقط role == 'admin' بود در
    حالی‌که SuperuserRequiredMixin در views.py علاوه‌بر آن is_superuser
    را هم می‌پذیرفت؛ این ناهماهنگی با استفاده از CustomUser.is_admin
    برطرف شده تا هر دو مسیر یک قانون واحد داشته باشند.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_admin:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("دسترسی غیرمجاز")
    return _wrapped_view
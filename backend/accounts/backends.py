# accounts/backends.py
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class EmailOrPhoneBackend(ModelBackend):
    """احراز هویت با ایمیل یا شماره موبایل به‌جای username.

    نکته امنیتی: در صورت نبودن کاربر، عمداً set_password روی یک نمونه‌ی
    خالی از مدل فراخوانی می‌شود تا زمان پاسخ‌دهی صرف‌نظر از وجود یا عدم
    وجود کاربر تقریباً یکسان بماند (جلوگیری از حمله‌ی user enumeration
    مبتنی بر timing). این رفتار حفظ شده است.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None

        lookup_kwargs = {'email__iexact': username} if '@' in username else {'phone': username}

        try:
            user = UserModel.objects.get(**lookup_kwargs)
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None

    def get_user(self, user_id):
        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None
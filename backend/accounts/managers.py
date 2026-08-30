# accounts/managers.py
import secrets

from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager for CustomUser.

    این تنها Manager معتبر مدل CustomUser است. قبلاً یک نسخه دیگر (و
    ناسازگار) از همین کلاس داخل models.py هم تعریف شده بود که باعث می‌شد
    منطق واقعی create_superuser/create_user هیچ‌وقت اجرا نشود. حالا فقط
    همین‌جا تعریف می‌شود و models.py آن را import می‌کند.
    """

    use_in_migrations = True

    def _create_user(self, email, phone=None, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        # رشته خالی را به None تبدیل می‌کنیم تا با unique=True روی phone تداخل نکند
        # (چند کاربر با phone='' باعث خطای IntegrityError در unique constraint می‌شوند)
        phone = phone or None
        user = self.model(email=email, phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('role', 'user')
        return self._create_user(email, phone, password, **extra_fields)

    def create_superuser(self, email, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self._create_user(email, phone, password, **extra_fields)

    @staticmethod
    def generate_otp_code() -> str:
        """کد ۶ رقمی امن (رمزنگارانه) برای OTP - جایگزین random.randint که
        قابل پیش‌بینی و نامناسب برای مقاصد امنیتی است."""
        return f"{secrets.randbelow(1_000_000):06d}"
# accounts/managers.py
import secrets

from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, email, phone=None, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
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
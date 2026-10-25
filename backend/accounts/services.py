# accounts/services.py
from datetime import timedelta

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .managers import UserManager
from .models import CustomUser

logger = logging.getLogger(__name__)

OTP_VALIDITY = timedelta(minutes=2)
OTP_RESEND_COOLDOWN = timedelta(seconds=60)
MAX_OTP_ATTEMPTS = 5


class OTPService:
    @staticmethod
    def send_otp(email_or_phone: str) -> CustomUser | None:
        """
        ارسال OTP برای ورود. فقط برای کاربران موجود — کاربر جدید نمی‌سازد.

        دلیل: CustomUser.email دارای unique=True است. اگر برای شناسه‌ی
        ناشناخته کاربر جدید می‌ساختیم، اولین کاربر phone-only با
        email='' ذخیره می‌شد و دومین کاربر phone-only با
        IntegrityError (UNIQUE constraint failed) کرش می‌کرد.
        مسیر ثبت‌نام رسمی از SignupAPIView با ایمیل اجباری است.

        بازگشت:
          - CustomUser اگر کاربر موجود باشد (کد ارسال شده یا در cooldown)
          - None اگر کاربری با این شناسه وجود نداشته باشد
        """
        is_email = '@' in email_or_phone
        lookup = {'email': email_or_phone} if is_email else {'phone': email_or_phone}

        user = CustomUser.objects.filter(**lookup).first()

        # کاربر مسدود: پاسخ می‌دهیم ولی کد نمی‌فرستیم (جلوگیری از enumeration)
        if user is not None and not user.is_active:
            logger.info('OTP requested for inactive user id=%s', user.pk)
            return user

        # کاربر موجود در cooldown: کد جدید نمی‌فرستیم
        if user and user.otp_sent_at and \
                (timezone.now() - user.otp_sent_at) < OTP_RESEND_COOLDOWN:
            return user

        # کاربر جدید — نمی‌سازیم
        if user is None:
            logger.info(
                'OTP requested for unregistered identifier type=%s',
                'email' if is_email else 'phone',
            )
            return None

        code = UserManager.generate_otp_code()
        user.otp_code = code
        user.otp_expiry = timezone.now() + OTP_VALIDITY
        user.otp_sent_at = timezone.now()
        user.otp_attempts = 0
        user.save(update_fields=[
            'otp_code', 'otp_expiry', 'otp_sent_at', 'otp_attempts',
        ])

        if is_email:
            try:
                send_mail(
                    'کد ورود', f'کد: {code}',
                    settings.DEFAULT_FROM_EMAIL, [email_or_phone],
                )
            except Exception:
                logger.exception('send_otp email failed')
        else:
            # TODO: اتصال به Kavenegar در production
            logger.info('SMS OTP for phone=%s code=%s', email_or_phone, code)
        return user

    @staticmethod
    def verify_otp(user: CustomUser, code: str) -> bool:
        if not code or not user.otp_code or not user.otp_expiry:
            return False

        if not user.is_active:
            return False

        if user.otp_attempts >= MAX_OTP_ATTEMPTS:
            return False

        import secrets as _s
        if not _s.compare_digest(user.otp_code, code):
            user.otp_attempts = (user.otp_attempts or 0) + 1
            user.save(update_fields=['otp_attempts'])
            return False

        if user.otp_expiry <= timezone.now():
            return False

        user.is_verified = True
        user.otp_code = None
        user.otp_expiry = None
        user.otp_sent_at = None
        user.otp_attempts = 0
        user.save(update_fields=[
            'is_verified', 'otp_code', 'otp_expiry',
            'otp_sent_at', 'otp_attempts',
        ])
        return True
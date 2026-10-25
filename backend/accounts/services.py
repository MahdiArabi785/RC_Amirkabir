# accounts/services.py
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .managers import UserManager
from .models import CustomUser

OTP_VALIDITY = timedelta(minutes=2)
OTP_RESEND_COOLDOWN = timedelta(seconds=60)
MAX_OTP_ATTEMPTS = 5


class OTPService:
    @staticmethod
    def send_otp(email_or_phone: str) -> CustomUser:
        is_email = '@' in email_or_phone
        lookup = {'email': email_or_phone} if is_email else {'phone': email_or_phone}

        user = CustomUser.objects.filter(**lookup).first()
        if user is None:
            user = CustomUser(**lookup)
            user.set_unusable_password()
        elif user.otp_sent_at and \
                (timezone.now() - user.otp_sent_at) < OTP_RESEND_COOLDOWN:
            # در cooldown — کد جدید نفرست، ولی خطا نده
            return user

        code = UserManager.generate_otp_code()
        user.otp_code = code
        user.otp_expiry = timezone.now() + OTP_VALIDITY
        user.otp_sent_at = timezone.now()
        user.otp_attempts = 0
        user.save()

        if is_email:
            send_mail('کد ورود', f'کد: {code}', settings.DEFAULT_FROM_EMAIL, [email_or_phone])
        else:
            # TODO: با Kavenegar در production جایگزین شود
            print(f"SMS to {email_or_phone}: {code}")
        return user

    @staticmethod
    def verify_otp(user: CustomUser, code: str) -> bool:
        if not code or not user.otp_code or not user.otp_expiry:
            return False

        # بررسی is_active برای جلوگیری از ورود کاربر مسدود
        if not user.is_active:
            return False

        # Rate limit
        if user.otp_attempts >= MAX_OTP_ATTEMPTS:
            return False

        # مقایسه‌ی امن
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
            'is_verified', 'otp_code', 'otp_expiry', 'otp_sent_at', 'otp_attempts',
        ])
        return True
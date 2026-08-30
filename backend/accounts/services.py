# accounts/services.py
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .managers import UserManager
from .models import CustomUser

OTP_VALIDITY = timedelta(minutes=2)
OTP_RESEND_COOLDOWN = timedelta(seconds=60)


class OTPService:
    @staticmethod
    def send_otp(email_or_phone: str) -> CustomUser:
        is_email = '@' in email_or_phone
        lookup = {'email': email_or_phone} if is_email else {'phone': email_or_phone}

        user = CustomUser.objects.filter(**lookup).first()
        if user is None:
            # کاربر تازه: چون هیچ رمزی تعیین نشده، ورود او فقط از طریق OTP
            # ممکن است. set_unusable_password صراحتاً این را ثبت می‌کند
            # (قبلاً get_or_create با رمز خالی این کار را به‌طور ضمنی و
            # مبهم انجام می‌داد).
            user = CustomUser(**lookup)
            user.set_unusable_password()
        elif user.otp_expiry and (OTP_VALIDITY - (user.otp_expiry - timezone.now())) < OTP_RESEND_COOLDOWN:
            # جلوگیری از اسپم شدن ایمیل/پیامک با درخواست‌های پی‌درپی روی
            # همان ایمیل/موبایل
            return user

        code = UserManager.generate_otp_code()
        user.otp_code = code
        user.otp_expiry = timezone.now() + OTP_VALIDITY
        user.save()

        if is_email:
            send_mail('کد ورود', f'کد: {code}', settings.DEFAULT_FROM_EMAIL, [email_or_phone])
        else:
            # TODO: اتصال سرویس واقعی پیامک
            print(f"SMS to {email_or_phone}: {code}")
        return user

    @staticmethod
    def verify_otp(user: CustomUser, code: str) -> bool:
        if not code or not user.otp_code or not user.otp_expiry:
            return False
        if user.otp_code == code and user.otp_expiry > timezone.now():
            user.is_verified = True
            user.otp_code = None
            user.otp_expiry = None
            user.save(update_fields=['is_verified', 'otp_code', 'otp_expiry'])
            return True
        return False
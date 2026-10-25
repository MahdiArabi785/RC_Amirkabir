# accounts/api_views.py
"""
API views برای accounts.

شامل:
- احراز هویت (signup, login, OTP, password reset, logout)
- پروفایل کاربر
- داشبورد و مدیریت ادمین
- CRUD مقالات/دوره‌ها/پروژه‌ها (از طریق ViewSet)
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .api_serializers import (
    AdminUserSerializer,
    ArticleSerializer,
    ChangePasswordSerializer,
    CourseSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ResearchProjectSerializer,
    ResendCodeSerializer,
    SendOTPSerializer,
    SignupSerializer,
    UserSerializer,
    VerifyEmailSerializer,
    VerifyOTPSerializer,
)
from .managers import UserManager
from .models import Article, Course, CustomUser, ResearchProject
from .services import OTPService

logger = logging.getLogger(__name__)

EMAIL_CODE_EXPIRY = timedelta(minutes=15)


# =============================================================================
# Throttle classes
# =============================================================================
class OTPAnonThrottle(AnonRateThrottle):
    """
    Rate limit مخصوص OTP.

    چرا `scope` در کلاس (نه attribute روی view): `AnonRateThrottle` فقط
    `scope` را از کلاس خودش می‌خواند. `ScopedRateThrottle` از
    `view.throttle_scope` می‌خواند ولی در `@action` قابل تنظیم نیست
    (TypeError). پس subclass تمیزترین راه است.
    """
    scope = 'otp'


# =============================================================================
# Permission classes
# =============================================================================
class IsAdmin(permissions.BasePermission):
    """معادل SuperuserRequiredMixin — از CustomUser.is_admin استفاده می‌کند."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_admin
        )


# =============================================================================
# Helpers
# =============================================================================
def _tokens_for(user):
    """تولید access/refresh token برای کاربر."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def _can_manage_target(actor, target) -> bool:
    """
    قوانین مدیریت هدف:
    - کاربر نمی‌تواند خودش را مدیریت کند (جلوگیری از خود-قفل‌کردن).
    - فقط سوپریوزر می‌تواند سوپریوزر را تغییر دهد.
    """
    if actor.pk == target.pk:
        return False
    if target.is_superuser and not actor.is_superuser:
        return False
    return True


def _safe_send_mail(subject, message, recipient_list):
    """ارسال ایمیل با مدیریت خطا (بدون 500)."""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    except Exception:
        logger.exception(
            'ارسال ایمیل ناموفق بود — subject=%r recipients=%r',
            subject, recipient_list,
        )


# =============================================================================
# احراز هویت
# =============================================================================
class SendOTPAPIView(APIView):
    """ارسال کد OTP برای ورود با ایمیل/موبایل."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPAnonThrottle]
    serializer_class = SendOTPSerializer

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = OTPService.send_otp(serializer.validated_data['email_or_phone'])
        return Response({'user_id': user.id}, status=status.HTTP_200_OK)


class VerifyOTPAPIView(APIView):
    """تأیید کد OTP و صدور توکن."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = CustomUser.objects.filter(
            id=serializer.validated_data['user_id']
        ).first()
        if user is None:
            return Response(
                {'detail': 'کاربر یافت نشد.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # بررسی قبل از مصرف OTP — جلوگیری از ورود کاربر مسدود/غیرفعال
        if not user.is_active:
            return Response(
                {'detail': 'حساب شما غیرفعال شده است.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if OTPService.verify_otp(user, serializer.validated_data['code']):
            return Response({
                **_tokens_for(user),
                'user': UserSerializer(user).data,
            })

        return Response(
            {'detail': 'کد نامعتبر یا منقضی شده است.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class SignupAPIView(generics.CreateAPIView):
    """ثبت‌نام — پس از ثبت، ایمیل تأیید ارسال می‌شود."""
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        user.otp_code = UserManager.generate_otp_code()
        user.otp_expiry = timezone.now() + EMAIL_CODE_EXPIRY
        user.otp_sent_at = timezone.now()
        user.otp_attempts = 0
        user.save()

        _safe_send_mail(
            'کد تأیید ایمیل',
            f'کد شما: {user.otp_code}',
            [user.email],
        )

        return Response(
            {'user_id': user.id, 'email': user.email},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailAPIView(APIView):
    """تأیید ایمیل پس از ثبت‌نام."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]
    serializer_class = VerifyEmailSerializer

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = CustomUser.objects.filter(
            email=data['email'],
            otp_code=data['code'],
            is_verified=False,
        ).first()

        if user is None or user.otp_expiry is None or user.otp_expiry < timezone.now():
            return Response(
                {'detail': 'کد نامعتبر یا منقضی شده است.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_verified = True
        user.is_active = True
        user.otp_code = None
        user.otp_expiry = None
        user.otp_sent_at = None
        user.otp_attempts = 0
        user.save()

        return Response({
            **_tokens_for(user),
            'user': UserSerializer(user).data,
        })


class ResendCodeAPIView(APIView):
    """ارسال مجدد کد تأیید ایمیل."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPAnonThrottle]
    serializer_class = ResendCodeSerializer

    def post(self, request):
        serializer = ResendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = CustomUser.objects.filter(email=email).first()
        if user is None:
            return Response(
                {'detail': 'کاربری با این ایمیل یافت نشد.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if user.is_verified:
            return Response(
                {'detail': 'حساب قبلاً تأیید شده است.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = UserManager.generate_otp_code()
        user.otp_code = code
        user.otp_expiry = timezone.now() + EMAIL_CODE_EXPIRY
        user.otp_sent_at = timezone.now()
        user.otp_attempts = 0
        user.save()

        _safe_send_mail('کد تأیید', f'کد شما: {code}', [email])

        return Response({'detail': 'کد جدید ارسال شد.'})


class LoginAPIView(APIView):
    """ورود با ایمیل یا موبایل + رمز عبور."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response({
            **_tokens_for(user),
            'user': UserSerializer(user).data,
        })


class LogoutAPIView(APIView):
    """
    خروج با blacklist کردن refresh token.

    نیازمند فعال بودن 'rest_framework_simplejwt.token_blacklist' در
    INSTALLED_APPS و اجرای migrate. اگر blacklist کار نکند، فقط 205
    برمی‌گرداند و فرانت باید توکن‌ها را از localStorage پاک کند.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {'refresh': {'type': 'string'}},
                'required': ['refresh'],
            },
        },
        responses={205: OpenApiResponse(description='Refresh token blacklisted')},
    )
    def post(self, request):
        refresh = request.data.get('refresh')
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except Exception:
                logger.warning(
                    'blacklist failed برای refresh token',
                    exc_info=True,
                )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class PasswordResetRequestAPIView(APIView):
    """
    درخواست بازیابی رمز.

    پیام یکسان صرف‌نظر از وجود کاربر — جلوگیری از user enumeration.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPAnonThrottle]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = CustomUser.objects.filter(email=email).first()
        if user is not None:
            code = UserManager.generate_otp_code()
            user.otp_code = code
            user.otp_expiry = timezone.now() + EMAIL_CODE_EXPIRY
            user.otp_sent_at = timezone.now()
            user.otp_attempts = 0
            user.save()

            _safe_send_mail('بازیابی رمز عبور', f'کد شما: {code}', [email])

        return Response({
            'detail': 'در صورت وجود حساب با این ایمیل، کد بازیابی ارسال شد.'
        })


class PasswordResetConfirmAPIView(APIView):
    """تأیید کد + تنظیم رمز جدید (بدون session)."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = CustomUser.objects.filter(
            email=data['email'],
            otp_code=data['code'],
        ).first()

        if user is None or user.otp_expiry is None or user.otp_expiry < timezone.now():
            return Response(
                {'detail': 'کد نامعتبر یا منقضی شده است.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(data['new_password'])
        user.otp_code = None
        user.otp_expiry = None
        user.otp_sent_at = None
        user.otp_attempts = 0
        user.save()

        return Response({'detail': 'رمز عبور با موفقیت تغییر کرد.'})


# =============================================================================
# پروفایل
# =============================================================================
class ProfileAPIView(generics.RetrieveUpdateAPIView):
    """
    GET: دریافت پروفایل، PATCH: ویرایش.

    توجه: email/phone در UserSerializer read-only هستند — تغییرشان نیاز
    به flow جداگانه با verification دارد (در آینده اضافه کنید).
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordAPIView(APIView):
    """تغییر رمز برای کاربر لاگین‌شده + blacklist همه refresh tokenها."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        # باطل کردن همه refresh tokenهای قبلی (اگر blacklist فعال است)
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken,
            )
            for token in OutstandingToken.objects.filter(user=request.user):
                BlacklistedToken.objects.get_or_create(token=token)
        except ImportError:
            pass
        except Exception:
            logger.warning('blacklist همه توکن‌ها ناموفق', exc_info=True)

        return Response({'detail': 'رمز عبور با موفقیت تغییر کرد.'})


# =============================================================================
# داشبورد و مدیریت ادمین
# =============================================================================
class DashboardStatsAPIView(APIView):
    """آمار داشبورد — فقط ادمین."""
    permission_classes = [IsAdmin]

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        seven_days_ago = timezone.now() - timedelta(days=7)
        return Response({
            'users_count': CustomUser.objects.count(),
            'blocked_users_count': CustomUser.objects.filter(is_active=False).count(),
            'new_users_count': CustomUser.objects.filter(
                date_joined__gte=seven_days_ago,
            ).count(),
            'articles_count': Article.objects.count(),
            'courses_count': Course.objects.count(),
            'projects_count': ResearchProject.objects.count(),
        })


class UserListAPIView(generics.ListAPIView):
    """لیست کاربران با جستجو — فقط ادمین."""
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = CustomUser.objects.all().order_by('-date_joined')
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(phone__icontains=search)
                | Q(full_name__icontains=search)
            )
        return qs


class UserBlockToggleAPIView(APIView):
    """مسدود/رفع مسدودیت — با حفاظت سوپریوزر."""
    permission_classes = [IsAdmin]
    serializer_class = AdminUserSerializer

    def post(self, request, pk):
        user = CustomUser.objects.filter(pk=pk).first()
        if user is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not _can_manage_target(request.user, user):
            return Response(
                {'detail': 'اجازه‌ی تغییر این کاربر را ندارید.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        return Response(AdminUserSerializer(user).data)


class UserDeleteAPIView(generics.DestroyAPIView):
    """حذف کاربر — با حفاظت سوپریوزر."""
    queryset = CustomUser.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()

        if not _can_manage_target(request.user, user):
            return Response(
                {'detail': 'اجازه‌ی حذف این کاربر را ندارید.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)


class UserPromoteAPIView(APIView):
    """
    ارتقا/تنزل دسترسی ادمین — با حفاظت سوپریوزر.

    توجه: فقط role/is_staff تغییر می‌کند. is_superuser دست‌نخورده می‌ماند؛
    برای ارتقا به سوپریوزر باید از shell یا admin Django استفاده شود.
    """
    permission_classes = [IsAdmin]
    serializer_class = AdminUserSerializer

    def post(self, request, pk):
        user = CustomUser.objects.filter(pk=pk).first()
        if user is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not _can_manage_target(request.user, user):
            return Response(
                {'detail': 'اجازه‌ی تغییر سطح این کاربر را ندارید.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.role == 'admin':
            user.role = 'user'
            user.is_staff = False
        else:
            user.role = 'admin'
            user.is_staff = True
        user.save(update_fields=['role', 'is_staff'])

        return Response(AdminUserSerializer(user).data)


# =============================================================================
# محتوا: مقالات / دوره‌ها / پروژه‌ها
# =============================================================================
class ArticleViewSet(viewsets.ModelViewSet):
    """CRUD مقالات — فقط ادمین."""
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CourseViewSet(viewsets.ModelViewSet):
    """CRUD دوره‌ها (accounts.Course) — فقط ادمین."""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdmin]


class ResearchProjectViewSet(viewsets.ModelViewSet):
    """CRUD پروژه‌های تحقیقاتی — فقط ادمین."""
    queryset = ResearchProject.objects.all()
    serializer_class = ResearchProjectSerializer
    permission_classes = [IsAdmin]
# accounts/api_views.py
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .api_serializers import (
    AdminUserSerializer, ArticleSerializer, ChangePasswordSerializer,
    CourseSerializer, LoginSerializer, PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer, ResearchProjectSerializer,
    ResendCodeSerializer, SendOTPSerializer, SignupSerializer, UserSerializer,
    VerifyEmailSerializer, VerifyOTPSerializer,
)
from .managers import UserManager
from .models import Article, Course, CustomUser, ResearchProject
from .services import OTPService

MAX_OTP_ATTEMPTS = 5
EMAIL_CODE_EXPIRY = timedelta(minutes=15)


class IsAdmin(permissions.BasePermission):
    """معادل SuperuserRequiredMixin نسخه‌ی session-based - همان
    CustomUser.is_admin (role == 'admin' یا is_superuser)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


# ------------------------------------------------------------------
# احراز هویت
# ------------------------------------------------------------------
class SendOTPAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = OTPService.send_otp(serializer.validated_data['email_or_phone'])
        return Response({'user_id': user.id}, status=status.HTTP_200_OK)


class VerifyOTPAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = CustomUser.objects.filter(id=serializer.validated_data['user_id']).first()
        if user is None:
            return Response({'detail': 'کاربر یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

        if OTPService.verify_otp(user, serializer.validated_data['code']):
            return Response({**_tokens_for(user), 'user': UserSerializer(user).data})
        return Response({'detail': 'کد نامعتبر یا منقضی شده است.'}, status=status.HTTP_400_BAD_REQUEST)


class SignupAPIView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.otp_code = UserManager.generate_otp_code()
        user.otp_expiry = timezone.now() + EMAIL_CODE_EXPIRY
        user.save()
        send_mail('کد تأیید ایمیل', f'کد شما: {user.otp_code}',
                   settings.DEFAULT_FROM_EMAIL, [user.email])
        return Response({'user_id': user.id, 'email': user.email}, status=status.HTTP_201_CREATED)


class VerifyEmailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = CustomUser.objects.filter(email=data['email'], otp_code=data['code'], is_verified=False).first()
        if user is None or user.otp_expiry is None or user.otp_expiry < timezone.now():
            return Response({'detail': 'کد نامعتبر یا منقضی شده است.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_verified = True
        user.is_active = True
        user.otp_code = None
        user.otp_expiry = None
        user.save()
        return Response({**_tokens_for(user), 'user': UserSerializer(user).data})


class ResendCodeAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = CustomUser.objects.filter(email=email).first()
        if user is None:
            return Response({'detail': 'کاربری با این ایمیل یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)
        if user.is_verified:
            return Response({'detail': 'حساب قبلاً تأیید شده است.'}, status=status.HTTP_400_BAD_REQUEST)
        code = UserManager.generate_otp_code()
        user.otp_code = code
        user.otp_expiry = timezone.now() + EMAIL_CODE_EXPIRY
        user.save()
        send_mail('کد تأیید', f'کد شما: {code}', settings.DEFAULT_FROM_EMAIL, [email])
        return Response({'detail': 'کد جدید ارسال شد.'})


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response({**_tokens_for(user), 'user': UserSerializer(user).data})


class LogoutAPIView(APIView):
    """با JWT چیزی به‌اسم session وجود ندارد، پس logout یعنی باطل‌کردن
    (blacklist) توکن refresh فعلی. نیازمند فعال بودن
    'rest_framework_simplejwt.token_blacklist' در INSTALLED_APPS و
    migrate آن است؛ در غیر این‌صورت این endpoint فقط 205 برمی‌گرداند و
    فرانت باید توکن‌ها را خودش از localStorage پاک کند (که در هر صورت
    باید این کار را بکند)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = request.data.get('refresh')
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except Exception:
                pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


class PasswordResetRequestAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = CustomUser.objects.filter(email=email).first()
        if user is not None:
            code = UserManager.generate_otp_code()
            user.otp_code = code
            user.otp_expiry = timezone.now() + EMAIL_CODE_EXPIRY
            user.save()
            send_mail('بازیابی رمز عبور', f'کد شما: {code}', settings.DEFAULT_FROM_EMAIL, [email])
        # پیام یکسان صرف‌نظر از وجود کاربر، برای جلوگیری از user enumeration
        return Response({'detail': 'در صورت وجود حساب با این ایمیل، کد بازیابی ارسال شد.'})


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = CustomUser.objects.filter(email=data['email'], otp_code=data['code']).first()
        if user is None or user.otp_expiry is None or user.otp_expiry < timezone.now():
            return Response({'detail': 'کد نامعتبر یا منقضی شده است.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(data['new_password'])
        user.otp_code = None
        user.otp_expiry = None
        user.save()
        return Response({'detail': 'رمز عبور با موفقیت تغییر کرد.'})


# ------------------------------------------------------------------
# پروفایل
# ------------------------------------------------------------------
class ProfileAPIView(generics.RetrieveUpdateAPIView):
    """GET برای گرفتن پروفایل، PATCH برای ویرایش هر زیرمجموعه‌ای از
    فیلدهای UserSerializer - شامل activity_logs_enabled هم می‌شود، پس
    endpoint جدای تنظیمات لازم نیست."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'رمز عبور با موفقیت تغییر کرد.'})


# ------------------------------------------------------------------
# داشبورد و مدیریت ادمین
# ------------------------------------------------------------------
class DashboardStatsAPIView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        seven_days_ago = timezone.now() - timedelta(days=7)
        return Response({
            'users_count': CustomUser.objects.count(),
            'blocked_users_count': CustomUser.objects.filter(is_active=False).count(),
            'new_users_count': CustomUser.objects.filter(date_joined__gte=seven_days_ago).count(),
            'articles_count': Article.objects.count(),
            'courses_count': Course.objects.count(),
            'projects_count': ResearchProject.objects.count(),
        })


class UserListAPIView(generics.ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = CustomUser.objects.all().order_by('-date_joined')
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(phone__icontains=search) | Q(full_name__icontains=search)
            )
        return queryset


class UserBlockToggleAPIView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        user = CustomUser.objects.filter(pk=pk).first()
        if user is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if user.pk == request.user.pk:
            return Response({'detail': 'نمی‌توانید حساب خودتان را مسدود کنید.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = not user.is_active
        user.save()
        return Response(AdminUserSerializer(user).data)


class UserDeleteAPIView(generics.DestroyAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [IsAdmin]

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.pk == request.user.pk:
            return Response({'detail': 'نمی‌توانید حساب خودتان را حذف کنید.'}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)


class UserPromoteAPIView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        user = CustomUser.objects.filter(pk=pk).first()
        if user is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if user.pk == request.user.pk:
            return Response({'detail': 'نمی‌توانید سطح دسترسی خودتان را تغییر دهید.'}, status=status.HTTP_400_BAD_REQUEST)
        if user.role == 'admin':
            user.role = 'user'
            user.is_staff = False
        else:
            user.role = 'admin'
            user.is_staff = True
        user.save()
        return Response(AdminUserSerializer(user).data)


# ------------------------------------------------------------------
# محتوا: مقالات / دوره‌ها / پروژه‌ها
# ------------------------------------------------------------------
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdmin]


class ResearchProjectViewSet(viewsets.ModelViewSet):
    queryset = ResearchProject.objects.all()
    serializer_class = ResearchProjectSerializer
    permission_classes = [IsAdmin]
# accounts/api_urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import api_views

app_name = 'accounts_api'

router = DefaultRouter()
router.register('articles', api_views.ArticleViewSet, basename='article')
router.register('courses', api_views.CourseViewSet, basename='course')
router.register('projects', api_views.ResearchProjectViewSet, basename='project')

urlpatterns = [
    # احراز هویت
    path('signup/', api_views.SignupAPIView.as_view(), name='signup'),
    path('login/', api_views.LoginAPIView.as_view(), name='login'),
    path('logout/', api_views.LogoutAPIView.as_view(), name='logout'),
    path('send-otp/', api_views.SendOTPAPIView.as_view(), name='send_otp'),
    path('verify-otp/', api_views.VerifyOTPAPIView.as_view(), name='verify_otp'),
    path('verify-email/', api_views.VerifyEmailAPIView.as_view(), name='verify_email'),
    path('resend-code/', api_views.ResendCodeAPIView.as_view(), name='resend_code'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('password-reset/request/', api_views.PasswordResetRequestAPIView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', api_views.PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm'),

    # پروفایل
    path('profile/', api_views.ProfileAPIView.as_view(), name='profile'),
    path('change-password/', api_views.ChangePasswordAPIView.as_view(), name='change_password'),

    # داشبورد و مدیریت ادمین
    path('dashboard/stats/', api_views.DashboardStatsAPIView.as_view(), name='dashboard_stats'),
    path('users/', api_views.UserListAPIView.as_view(), name='user_list'),
    path('users/<int:pk>/block/', api_views.UserBlockToggleAPIView.as_view(), name='user_block'),
    path('users/<int:pk>/delete/', api_views.UserDeleteAPIView.as_view(), name='user_delete'),
    path('users/<int:pk>/promote/', api_views.UserPromoteAPIView.as_view(), name='user_promote'),

    # مقالات / دوره‌ها / پروژه‌ها (CRUD کامل از طریق DefaultRouter)
    path('', include(router.urls)),
]
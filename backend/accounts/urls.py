# accounts/urls.py
from django.urls import path

from . import views

# قبلاً app_name تعریف نشده بود، در حالی‌که همه‌جای views.py با
# reverse('accounts:...') / redirect('accounts:...') به این namespace
# ارجاع داده می‌شود. بدون این خط (و بدون namespace='accounts' هنگام
# include شدن در urls.py اصلی پروژه) این reverse ها با NoReverseMatch
# خطا می‌دادند.
app_name = 'accounts'

urlpatterns = [
    # احراز هویت
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('send-otp/', views.SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-code/', views.ResendCodeView.as_view(), name='resend_code'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/verify/', views.PasswordResetVerifyView.as_view(), name='password_reset_verify'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # پروفایل
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/activity-logs/', views.ActivityLogsSettingsView.as_view(), name='activity_logs_settings'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # داشبورد ادمین
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('users/', views.UserManagementView.as_view(), name='user_management'),
    path('users/<int:pk>/block/', views.UserBlockView.as_view(), name='user_block'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('users/promote/', views.UserPromoteView.as_view(), name='user_promote'),
    path('block-list/', views.BlockListManagementView.as_view(), name='block_list'),

    # مقالات
    path('articles/create/', views.ArticleCreateView.as_view(), name='article_create'),
    path('articles/<int:pk>/edit/', views.ArticleUpdateView.as_view(), name='article_edit'),
    path('articles/<int:pk>/delete/', views.ArticleDeleteView.as_view(), name='article_delete'),

    # دوره‌ها
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),

    # پروژه‌های تحقیقاتی
    path('projects/create/', views.ResearchProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/edit/', views.ResearchProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<int:pk>/delete/', views.ResearchProjectDeleteView.as_view(), name='project_delete'),
]
# accounts/views.py
import random
import string
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .forms import (
    AccountPasswordChangeForm, AccountSetPasswordForm, ActivityLogsForm,
    ArticleForm, CourseForm, CustomUserCreationForm, ProfileForm,
    ResearchProjectForm, SendOTPForm, UserBlockForm,
)
from .managers import UserManager
from .models import Article, Course, CustomUser, ResearchProject
from .services import OTPService

# قبلاً این رشته در چند view مختلف تکرار شده بود. یک بار تعریف می‌شود تا
# تغییر مسیر backend در آینده فقط یک‌جا نیاز به ویرایش داشته باشد.
AUTH_BACKEND = 'accounts.backends.EmailOrPhoneBackend'

MAX_OTP_ATTEMPTS = 5
MAX_EMAIL_VERIFY_ATTEMPTS = 3
MAX_RESENDS = 3
RESEND_COOLDOWN = timedelta(minutes=1)
EMAIL_CODE_EXPIRY = timedelta(minutes=15)


def _login_user(request, user):
    login(request, user, backend=AUTH_BACKEND)


def _post_login_redirect(user):
    return redirect('accounts:dashboard') if user.is_admin else redirect('home')


def _generate_numeric_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


# ------------------------------------------------------------------
# Mixin برای دسترسی ادمین
# ------------------------------------------------------------------
class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return HttpResponseForbidden("شما مجوز دسترسی به این صفحه را ندارید.")


# ------------------------------------------------------------------
# احراز هویت
# ------------------------------------------------------------------
class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        identifier = request.POST.get("identifier", "").strip()
        password = request.POST.get("password", "")

        if not identifier or not password:
            messages.error(request, "لطفاً ایمیل/موبایل و رمز عبور را وارد کنید.")
            return render(request, self.template_name)

        if '@' in identifier:
            user = authenticate(request, email=identifier, password=password)
        else:
            user = authenticate(request, phone=identifier, password=password)

        if user is None:
            messages.error(request, "اطلاعات وارد شده صحیح نیست.")
            return render(request, self.template_name)

        if not user.is_active:
            messages.error(request, "حساب شما غیرفعال شده است. با پشتیبانی تماس بگیرید.")
            return render(request, self.template_name)

        _login_user(request, user)
        messages.success(request, "ورود موفقیت‌آمیز بود!")
        return _post_login_redirect(user)


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        messages.success(request, "با موفقیت خارج شدید.")
        return redirect('home')


class SendOTPView(View):
    template_name = "accounts/send_otp.html"

    def get(self, request):
        return render(request, self.template_name, {'form': SendOTPForm()})

    def post(self, request):
        form = SendOTPForm(request.POST)
        if form.is_valid():
            input_value = form.cleaned_data['email_or_phone']
            user = OTPService.send_otp(input_value)
            request.session['otp_user_id'] = user.id
            request.session['otp_method'] = 'email' if '@' in input_value else 'phone'
            request.session['otp_attempts'] = 0
            messages.success(request, "کد تأیید ارسال شد.")
            return redirect('accounts:verify_otp')
        return render(request, self.template_name, {'form': form})


class VerifyOTPView(View):
    """قبلاً هیچ محدودیتی روی تعداد تلاش برای حدس زدن کد OTP وجود نداشت
    (یک کد ۶ رقمی فقط ۱ میلیون حالت دارد و بدون rate limit قابل brute-
    force است). حالا بعد از MAX_OTP_ATTEMPTS تلاش ناموفق، نشست OTP باطل
    می‌شود و کاربر باید دوباره کد بگیرد."""
    template_name = "accounts/verify_otp.html"

    def get(self, request):
        if not request.session.get('otp_user_id'):
            return redirect('accounts:send_otp')
        return render(request, self.template_name)

    def post(self, request):
        user_id = request.session.get('otp_user_id')
        if not user_id:
            return redirect('accounts:send_otp')

        attempts = request.session.get('otp_attempts', 0)
        if attempts >= MAX_OTP_ATTEMPTS:
            for key in ('otp_user_id', 'otp_method', 'otp_attempts'):
                request.session.pop(key, None)
            messages.error(request, "تعداد تلاش‌های مجاز به پایان رسید. دوباره کد بگیرید.")
            return redirect('accounts:send_otp')

        code = request.POST.get('code', '').strip()
        # قبلاً CustomUser.objects.get(...) بدون try/except بود که در
        # صورت نامعتبر شدن نشست (مثلاً کاربر حذف شده) خطای 500 می‌داد.
        user = CustomUser.objects.filter(id=user_id).first()
        if user is None:
            return redirect('accounts:send_otp')

        if OTPService.verify_otp(user, code):
            request.session.pop('otp_attempts', None)
            _login_user(request, user)
            messages.success(request, "ورود موفقیت‌آمیز بود!")
            return _post_login_redirect(user)

        request.session['otp_attempts'] = attempts + 1
        messages.error(request, "کد نامعتبر یا منقضی شده است.")
        return render(request, self.template_name)


class SignupView(View):
    template_name = "accounts/signup.html"
    form_class = CustomUserCreationForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.otp_code = UserManager.generate_otp_code()
            user.otp_expiry = timezone.now() + EMAIL_CODE_EXPIRY
            user.save()
            send_mail('کد تأیید ایمیل', f'کد شما: {user.otp_code}',
                       settings.DEFAULT_FROM_EMAIL, [user.email])
            messages.success(request, "لطفاً ایمیل خود را تأیید کنید.")
            return HttpResponseRedirect(f"{reverse('accounts:verify_email')}?email={user.email}")
        return render(request, self.template_name, {'form': form})


class VerifyEmailView(View):
    template_name = "accounts/verify_email.html"

    def get(self, request):
        email = request.GET.get('email', '')
        return render(request, self.template_name, {'email': email})

    def post(self, request):
        code = request.POST.get("verification_code", "").strip()
        email = request.POST.get("email", "").strip()
        user = CustomUser.objects.filter(email=email, otp_code=code, is_verified=False).first()

        if user is None:
            attempts = request.session.get('verify_attempts', 0) + 1
            request.session['verify_attempts'] = attempts
            if attempts >= MAX_EMAIL_VERIFY_ATTEMPTS:
                messages.error(request, "تعداد تلاش‌ها بیش از حد مجاز است.")
                return HttpResponseRedirect(f"{reverse('accounts:resend_code')}?email={email}")
            messages.error(request, "کد تأیید نامعتبر است.")
            return render(request, self.template_name, {'email': email})

        if user.otp_expiry is None or user.otp_expiry < timezone.now():
            messages.error(request, "کد تأیید منقضی شده است.")
            return HttpResponseRedirect(f"{reverse('accounts:resend_code')}?email={email}")

        request.session.pop('verify_attempts', None)
        user.is_verified = True
        user.is_active = True
        user.otp_code = None
        user.otp_expiry = None
        user.save()
        _login_user(request, user)
        messages.success(request, "حساب شما با موفقیت فعال شد!")
        return redirect('home')


class ResendCodeView(View):
    def get(self, request):
        return self.process_request(request, request.GET.get('email', ''))

    def post(self, request):
        return self.process_request(request, request.POST.get('email', ''))

    def process_request(self, request, email):
        user = CustomUser.objects.filter(email=email).first()
        if user is None:
            messages.error(request, "کاربری با این ایمیل یافت نشد.")
            return redirect('accounts:signup')

        if user.is_verified:
            messages.info(request, "حساب قبلاً تأیید شده است.")
            return redirect('accounts:login')

        last_sent = user.otp_expiry
        if last_sent and (timezone.now() - last_sent).total_seconds() < RESEND_COOLDOWN.total_seconds():
            remaining = int(RESEND_COOLDOWN.total_seconds() - (timezone.now() - last_sent).total_seconds())
            messages.warning(request, f"لطفاً {remaining} ثانیه دیگر تلاش کنید.")
            return HttpResponseRedirect(f"{reverse('accounts:verify_email')}?email={email}")

        resends = request.session.get(f'resends_{email}', 0)
        if resends >= MAX_RESENDS:
            messages.error(request, "تعداد درخواست‌ها بیش از حد مجاز است.")
            return redirect('home')

        code = _generate_numeric_code()
        user.otp_code = code
        user.otp_expiry = timezone.now() + EMAIL_CODE_EXPIRY
        user.save()
        send_mail('کد تأیید', f'کد شما: {code}', settings.DEFAULT_FROM_EMAIL, [email])
        request.session[f'resends_{email}'] = resends + 1
        messages.success(request, "کد جدید ارسال شد.")
        return HttpResponseRedirect(f"{reverse('accounts:verify_email')}?email={email}")


class PasswordResetRequestView(View):
    template_name = "accounts/password_reset_request.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email", "").strip()
        if not email:
            messages.error(request, "لطفاً ایمیل خود را وارد کنید.")
            return render(request, self.template_name)

        user = CustomUser.objects.filter(email=email).first()
        # پیام موفقیت همیشه یکسان نمایش داده می‌شود، چه کاربر وجود داشته
        # باشد چه نه، تا آدرس‌های ایمیل ثبت‌شده در سیستم قابل حدس زدن
        # (user enumeration) نباشند.
        if user is not None:
            code = _generate_numeric_code()
            user.otp_code = code
            user.otp_expiry = timezone.now() + EMAIL_CODE_EXPIRY
            user.save()
            send_mail('بازیابی رمز عبور', f'کد شما: {code}', settings.DEFAULT_FROM_EMAIL, [email])
        messages.success(request, "در صورت وجود حساب با این ایمیل، کد بازیابی ارسال شد.")
        return HttpResponseRedirect(f"{reverse('accounts:password_reset_verify')}?email={email}")


class PasswordResetVerifyView(View):
    template_name = "accounts/password_reset_verify.html"

    def get(self, request):
        email = request.GET.get('email', '')
        return render(request, self.template_name, {'email': email})

    def post(self, request):
        code = request.POST.get("verification_code", "").strip()
        email = request.POST.get("email", "").strip()
        user = CustomUser.objects.filter(email=email, otp_code=code).first()

        if user is None:
            messages.error(request, "کد نامعتبر است.")
            return render(request, self.template_name, {'email': email})

        if user.otp_expiry is None or user.otp_expiry < timezone.now():
            messages.error(request, "کد منقضی شده است.")
            return HttpResponseRedirect(f"{reverse('accounts:password_reset_request')}?email={email}")

        request.session['reset_email'] = email
        request.session['reset_verified'] = True
        messages.success(request, "کد صحیح است. لطفاً رمز جدید وارد کنید.")
        return redirect('accounts:password_reset_confirm')


class PasswordResetConfirmView(View):
    """قبلاً رمز جدید اصلاً از نظر طول/قدرت بررسی نمی‌شد. حالا از
    AccountSetPasswordForm (بر پایه‌ی SetPasswordForm جنگو) استفاده
    می‌شود تا AUTH_PASSWORD_VALIDATORS تنظیم‌شده در settings به‌طور
    خودکار اعمال شود."""
    template_name = "accounts/password_reset_confirm.html"

    def get(self, request):
        if not request.session.get('reset_verified'):
            messages.error(request, "ابتدا ایمیل را تأیید کنید.")
            return redirect('accounts:password_reset_request')
        user = self._get_reset_user(request)
        form = AccountSetPasswordForm(user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if not request.session.get('reset_verified'):
            messages.error(request, "ابتدا ایمیل را تأیید کنید.")
            return redirect('accounts:password_reset_request')

        user = self._get_reset_user(request)
        if user is None:
            messages.error(request, "کاربر یافت نشد.")
            return redirect('accounts:password_reset_request')

        form = AccountSetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            user.otp_code = None
            user.otp_expiry = None
            user.save(update_fields=['otp_code', 'otp_expiry'])
            del request.session['reset_email']
            del request.session['reset_verified']
            messages.success(request, "رمز عبور با موفقیت تغییر کرد. لطفاً وارد شوید.")
            return redirect('accounts:login')
        return render(request, self.template_name, {'form': form})

    @staticmethod
    def _get_reset_user(request):
        email = request.session.get('reset_email')
        return CustomUser.objects.filter(email=email).first() if email else None


# ------------------------------------------------------------------
# پروفایل و تنظیمات کاربر
# ------------------------------------------------------------------
class ProfileView(LoginRequiredMixin, View):
    template_name = "accounts/profile.html"

    def get(self, request):
        form = ProfileForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "پروفایل به‌روزرسانی شد.")
        else:
            messages.error(request, "خطا در فرم پروفایل.")
        return redirect('accounts:profile')


class ActivityLogsSettingsView(LoginRequiredMixin, View):
    template_name = "accounts/activity_logs_settings.html"

    def get(self, request):
        form = ActivityLogsForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ActivityLogsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "تنظیمات ذخیره شد.")
            return redirect('accounts:profile')
        return render(request, self.template_name, {'form': form})


class ChangePasswordView(LoginRequiredMixin, View):
    """قبلاً رمز جدید با شرط دستی len(...) < 8 بررسی می‌شد و از همه مهم‌تر
    update_session_auth_hash صدا زده نمی‌شد؛ نتیجه‌اش این بود که کاربر
    بلافاصله بعد از تغییر موفق رمز، از نشست (session) فعلی خودش خارج
    می‌شد چون هش نشست جنگو با تغییر رمز عوض می‌شود."""
    template_name = "accounts/change_password.html"

    def get(self, request):
        form = AccountPasswordChangeForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AccountPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "رمز عبور با موفقیت تغییر کرد.")
            return redirect('accounts:profile')
        return render(request, self.template_name, {'form': form})


# ------------------------------------------------------------------
# داشبورد ادمین
# ------------------------------------------------------------------
class DashboardView(SuperuserRequiredMixin, TemplateView):
    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seven_days_ago = timezone.now() - timedelta(days=7)
        context.update({
            'users_count': CustomUser.objects.count(),
            'blocked_users_count': CustomUser.objects.filter(is_active=False).count(),
            'new_users_count': CustomUser.objects.filter(date_joined__gte=seven_days_ago).count(),
            'articles_count': Article.objects.count(),
            'courses_count': Course.objects.count(),
            'projects_count': ResearchProject.objects.count(),
            'recent_users': CustomUser.objects.order_by('-date_joined')[:10],
            'recent_articles': Article.objects.order_by('-created_at')[:10],
            'recent_courses': Course.objects.order_by('-created_at')[:10],
            'recent_projects': ResearchProject.objects.order_by('-created_at')[:10],
        })
        return context


class UserManagementView(SuperuserRequiredMixin, ListView):
    model = CustomUser
    template_name = "accounts/user_management.html"
    context_object_name = "users"
    ordering = '-date_joined'

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(full_name__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search_query': self.request.GET.get('search', ''),
            'blocked_count': CustomUser.objects.filter(is_active=False).count(),
        })
        return context


class UserBlockView(SuperuserRequiredMixin, UpdateView):
    """قبلاً is_active از طریق یک HiddenInput در فرم toggle می‌شد که با
    resubmit شدن فرم (مثلاً با دکمه‌ی Back مرورگر) می‌توانست رفتار
    غیرمنتظره داشته باشد. حالا وضعیت مستقیم و صریح در خود view عوض
    می‌شود."""
    model = CustomUser
    form_class = UserBlockForm
    template_name = "accounts/user_block.html"
    context_object_name = 'target_user'
    success_url = reverse_lazy('accounts:user_management')

    def form_valid(self, form):
        user = form.save(commit=False)
        if user.pk == self.request.user.pk:
            messages.error(self.request, "نمی‌توانید حساب خودتان را مسدود کنید.")
            return redirect(self.success_url)
        user.is_active = not user.is_active
        user.save()
        action = "رفع مسدودیت" if user.is_active else "مسدود"
        messages.success(self.request, f"کاربر {user.email} {action} شد.")
        return redirect(self.success_url)


class UserDeleteView(SuperuserRequiredMixin, DeleteView):
    model = CustomUser
    template_name = "accounts/user_confirm_delete.html"
    context_object_name = 'target_user'
    success_url = reverse_lazy('accounts:user_management')

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user.pk == request.user.pk:
            messages.error(request, "نمی‌توانید حساب خودتان را حذف کنید.")
            return redirect(self.success_url)
        messages.success(request, f"کاربر {user.email} حذف شد.")
        return super().delete(request, *args, **kwargs)


class UserPromoteView(SuperuserRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user_id = request.POST.get('user_id')
        if not user_id or not user_id.isdigit():
            messages.error(request, "شناسه نامعتبر است.")
            return redirect('accounts:user_management')

        user = CustomUser.objects.filter(id=user_id).first()
        if user is None:
            messages.error(request, "کاربر یافت نشد.")
            return redirect('accounts:user_management')

        if user.pk == request.user.pk:
            messages.error(request, "نمی‌توانید سطح دسترسی خودتان را تغییر دهید.")
            return redirect('accounts:user_management')

        if user.role == 'admin':
            user.role = 'user'
            user.is_staff = False
            messages.success(request, "دسترسی ادمین گرفته شد.")
        else:
            user.role = 'admin'
            user.is_staff = True
            messages.success(request, "کاربر به ادمین ارتقا یافت.")
        user.save()
        return redirect('accounts:user_management')


class BlockListManagementView(SuperuserRequiredMixin, ListView):
    model = CustomUser
    template_name = "accounts/block_list.html"
    context_object_name = "blocked_users"
    ordering = '-date_joined'

    def get_queryset(self):
        return super().get_queryset().filter(is_active=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "لیست کاربران مسدود شده"
        return context


# ------------------------------------------------------------------
# مدیریت مقالات
# ------------------------------------------------------------------
class ArticleCreateView(SuperuserRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = "accounts/article_form.html"
    success_url = reverse_lazy('accounts:dashboard')

    def form_valid(self, form):
        # قبلاً این خط باعث AttributeError می‌شد چون مدل Article فیلد
        # created_by نداشت. حالا فیلد به models.py اضافه شده است.
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ArticleUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = "accounts/article_form.html"
    success_url = reverse_lazy('accounts:dashboard')


class ArticleDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Article
    template_name = "accounts/article_confirm_delete.html"
    success_url = reverse_lazy('accounts:dashboard')


# ------------------------------------------------------------------
# مدیریت دوره‌ها
# ------------------------------------------------------------------
class CourseCreateView(SuperuserRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = "accounts/course_form.html"
    success_url = reverse_lazy('accounts:dashboard')


class CourseUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = "accounts/course_form.html"
    success_url = reverse_lazy('accounts:dashboard')


class CourseDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Course
    template_name = "accounts/course_confirm_delete.html"
    success_url = reverse_lazy('accounts:dashboard')


# ------------------------------------------------------------------
# مدیریت پروژه‌های تحقیقاتی
# ------------------------------------------------------------------
class ResearchProjectCreateView(SuperuserRequiredMixin, CreateView):
    model = ResearchProject
    form_class = ResearchProjectForm
    template_name = "accounts/project_form.html"
    success_url = reverse_lazy('accounts:dashboard')


class ResearchProjectUpdateView(SuperuserRequiredMixin, UpdateView):
    model = ResearchProject
    form_class = ResearchProjectForm
    template_name = "accounts/project_form.html"
    success_url = reverse_lazy('accounts:dashboard')


class ResearchProjectDeleteView(SuperuserRequiredMixin, DeleteView):
    model = ResearchProject
    template_name = "accounts/project_confirm_delete.html"
    success_url = reverse_lazy('accounts:dashboard')
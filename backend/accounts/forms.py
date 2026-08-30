# accounts/forms.py
from django import forms
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm, UserCreationForm
from django.core.validators import validate_email

from .models import Article, Course, CustomUser, ResearchProject


class SendOTPForm(forms.Form):
    email_or_phone = forms.CharField(label='ایمیل یا شماره موبایل')

    def clean_email_or_phone(self):
        value = self.cleaned_data['email_or_phone'].strip()
        if not value:
            raise forms.ValidationError('این فیلد الزامی است.')
        return value


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, validators=[validate_email])
    phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = CustomUser
        fields = ('email', 'phone', 'password1', 'password2')

    def clean_phone(self):
        # رشته‌ی خالی را به None تبدیل می‌کنیم تا با unique=True روی phone
        # تداخل نکند (چند کاربر بدون موبایل نباید IntegrityError بدهند)
        return self.cleaned_data.get('phone') or None


class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'phone', 'full_name', 'avatar', 'role', 'is_active']

    def clean_phone(self):
        return self.cleaned_data.get('phone') or None


class UserBlockForm(forms.ModelForm):
    """این فرم دیگر is_active را کنترل نمی‌کند (آن مقدار قبلاً به‌صورت
    HiddenInput ارسال می‌شد که با بازکردن صفحه از دو تب یا زدن دکمه‌ی
    Back مرورگر می‌توانست مقدار قدیمی/نادرست را دوباره submit کند). تغییر
    وضعیت is_active مستقیماً در UserBlockView انجام می‌شود؛ این فرم فقط
    برای ثبت دلیل مسدودیت است."""
    reason = forms.CharField(
        label='دلیل مسدودیت', widget=forms.Textarea(attrs={'rows': 3}), required=False,
    )

    class Meta:
        model = CustomUser
        fields = ()


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['avatar', 'first_name', 'last_name', 'bio', 'organization',
                  'field_of_study', 'website', 'linkedin', 'google_scholar']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }


class ActivityLogsForm(forms.ModelForm):
    """تنظیم فعال/غیرفعال بودن ذخیره‌ی تاریخچه‌ی فعالیت. قبلاً این تنظیم و
    فیلدهای تغییر رمز عبور در یک فرم واحد (PrivacySecurityForm) مخلوط شده
    بودند بدون اینکه هیچ view واقعاً از آن استفاده کند."""
    class Meta:
        model = CustomUser
        fields = ['activity_logs_enabled']
        widgets = {'activity_logs_enabled': forms.CheckboxInput()}


class AccountPasswordChangeForm(PasswordChangeForm):
    """تغییر رمز برای کاربر لاگین‌شده. با استفاده از فرم استاندارد جنگو،
    AUTH_PASSWORD_VALIDATORS تنظیم‌شده در settings به‌طور خودکار اعمال
    می‌شود (قبلاً این بررسی به‌صورت دستی و فقط با شرط len(...) < 8 در
    ChangePasswordView انجام می‌شد)."""


class AccountSetPasswordForm(SetPasswordForm):
    """تنظیم رمز جدید در جریان بازیابی رمز عبور (بدون نیاز به رمز فعلی)."""


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'abstract', 'content', 'authors', 'status']
        widgets = {
            'authors': forms.SelectMultiple(),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'teacher', 'start_date', 'end_date', 'is_active']


class ResearchProjectForm(forms.ModelForm):
    class Meta:
        model = ResearchProject
        fields = ['title', 'description', 'lead', 'team_members', 'status',
                  'budget', 'start_date', 'end_date']
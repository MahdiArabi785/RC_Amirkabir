# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'ادمین'),
        ('user', 'کاربر عادی'),
    ]

    username = None
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    # اطلاعات پروفایل
    bio = models.TextField(blank=True, verbose_name='بیوگرافی')
    organization = models.CharField(max_length=100, blank=True, verbose_name='سازمان/دانشگاه')
    field_of_study = models.CharField(max_length=100, blank=True, verbose_name='زمینه تحقیقاتی')
    website = models.URLField(blank=True, verbose_name='وبسایت')
    linkedin = models.URLField(blank=True, verbose_name='لینکدین')
    google_scholar = models.URLField(blank=True, verbose_name='گوگل اسکالر')
    activity_logs_enabled = models.BooleanField(default=True, verbose_name='فعال بودن ذخیره تاریخچه فعالیت‌ها')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    objects = UserManager()

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return self.email or self.phone or self.full_name or f"user #{self.pk}"

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.full_name

    @property
    def is_admin(self):
        """تنها منبع تصمیم‌گیری برای 'ادمین بودن' - هم مسیر مدیریتی (role)
        و هم superuser جنگویی را پوشش می‌دهد. جای اینکه هرجا این شرط را
        دوباره‌نویسی کنیم (که قبلاً باعث ناهماهنگی بین decorators.py و
        views.py شده بود)، همه جا از همین property استفاده می‌شود."""
        return self.is_superuser or self.role == 'admin'


class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('under_review', 'در حال بررسی'),
        ('published', 'منتشر شده'),
        ('rejected', 'رد شده'),
    ]
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    content = models.TextField(blank=True)
    authors = models.ManyToManyField(CustomUser, related_name='articles', blank=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_articles', verbose_name='ایجادکننده',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'مقاله'
        verbose_name_plural = 'مقالات'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='courses')
    students = models.ManyToManyField(CustomUser, related_name='enrolled_courses', blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'دوره آموزشی'
        verbose_name_plural = 'دوره‌های آموزشی'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ResearchProject(models.Model):
    STATUS_CHOICES = [
        ('idea', 'ایده'),
        ('in_progress', 'در حال اجرا'),
        ('completed', 'تکمیل شده'),
        ('suspended', 'متوقف'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    lead = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='led_projects')
    team_members = models.ManyToManyField(CustomUser, related_name='research_projects', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idea')
    budget = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'پروژه تحقیقاتی'
        verbose_name_plural = 'پروژه‌های تحقیقاتی'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class OTPCode(models.Model):
    """توجه: این مدل در حال حاضر توسط services.py استفاده نمی‌شود (کد OTP
    مستقیماً روی خود CustomUser ذخیره می‌شود). اگر قصد دارید تاریخچه‌ی
    کدهای ارسالی را برای audit نگه دارید، باید OTPService را طوری اصلاح
    کنید که به‌جای/علاوه‌بر فیلدهای otp_code/otp_expiry روی CustomUser،
    رکورد این مدل را هم بسازد. در غیر این صورت بهتر است این مدل حذف شود
    تا کد مرده در پروژه نماند."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    method = models.CharField(max_length=10, choices=[('email', 'ایمیل'), ('phone', 'پیامک')])
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.code}"
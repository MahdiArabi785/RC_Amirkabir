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
    email = models.EmailField(unique=True)  # blank/null حذف شد
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    otp_sent_at = models.DateTimeField(blank=True, null=True)   # ← جدید
    otp_attempts = models.PositiveSmallIntegerField(default=0)   # ← جدید
    is_verified = models.BooleanField(default=False)

    bio = models.TextField(blank=True, verbose_name='بیوگرافی')
    organization = models.CharField(max_length=100, blank=True, verbose_name='سازمان/دانشگاه')
    field_of_study = models.CharField(max_length=100, blank=True, verbose_name='زمینه تحقیقاتی')
    website = models.URLField(blank=True, verbose_name='وبسایت')
    linkedin = models.URLField(blank=True, verbose_name='لینکدین')
    google_scholar = models.URLField(blank=True, verbose_name='گوگل اسکالر')
    activity_logs_enabled = models.BooleanField(
        default=True, verbose_name='فعال بودن ذخیره تاریخچه فعالیت‌ها'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return self.email or self.phone or self.full_name or f"user #{self.pk}"

    def get_full_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.full_name

    @property
    def is_admin(self):
        return self.is_superuser or self.role == 'admin'


# مدل OTPCode (اگر استفاده نمی‌شود، حذف شود - اینجا حذف شد)
# اگر روزی برای audit لازم شد، با روشن شدن OTPService اضافه کنید.


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
    """Course قدیمی accounts — اگر courses.models.Course جدید استفاده می‌شود،
    این کلاس حذف شود (co-existence خطرناک است). در صورت حفظ، teacher/lead
    باید PROTECT باشند نه CASCADE."""
    title = models.CharField(max_length=255)
    description = models.TextField()
    teacher = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT, related_name='courses'
    )
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
    lead = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT, related_name='led_projects'
    )
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
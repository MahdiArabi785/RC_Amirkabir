# =============================================================================
# managements/models.py
# مدل‌های کمکی برای لاگ فعالیت‌ها و تنظیمات پنل مدیریت
# =============================================================================

from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import JSONField, Index

User = get_user_model()


class ActivityLog(models.Model):
    """
    ثبت تمام فعالیت‌های مدیریتی در پنل.
    شامل عملیات CRUD، انتشار، مسدودیت، و سایر رویدادها.
    """
    ACTION_CHOICES = (
        ('create', 'ایجاد'),
        ('update', 'ویرایش'),
        ('delete', 'حذف'),
        ('bulk_delete', 'حذف گروهی'),
        ('publish', 'انتشار'),
        ('unpublish', 'عدم انتشار'),
        ('block', 'مسدودیت'),
        ('unblock', 'رفع مسدودیت'),
        ('promote', 'ارتقا سطح'),
        ('login', 'ورود'),
        ('logout', 'خروج'),
        ('download', 'دانلود'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='management_logs',
        verbose_name="کاربر"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True,
        verbose_name="عملیات"
    )
    model_name = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="نام مدل"
    )
    object_id = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="شناسه شیء"
    )
    object_repr = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="عنوان شیء"
    )
    changes = JSONField(
        default=dict,
        blank=True,
        verbose_name="تغییرات"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="آی‌پی"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="مرورگر"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="زمان"
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "لاگ فعالیت"
        verbose_name_plural = "لاگ‌های فعالیت"
        indexes = [
            Index(fields=['model_name', 'object_id']),
            Index(fields=['timestamp']),
            Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.object_repr}"


class ManagementSetting(models.Model):
    """
    تنظیمات پنل مدیریت (تعداد آیتم در صفحه، تم، و غیره)
    """
    key = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="کلید"
    )
    value = models.CharField(
        max_length=500,
        verbose_name="مقدار"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="توضیح"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:
        verbose_name = "تنظیمات مدیریت"
        verbose_name_plural = "تنظیمات مدیریت"

    def __str__(self):
        return f"{self.key}: {self.value}"
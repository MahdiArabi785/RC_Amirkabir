# guides/models.py
import os

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import F

ALLOWED_GUIDE_EXTENSIONS = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'zip']
MAX_GUIDE_FILE_SIZE_MB = 25


def validate_guide_file_size(file):
    # قبلاً هیچ محدودیتی روی حجم فایل آپلودی وجود نداشت - یک فایل چندگیگابایتی
    # هم بدون خطا پذیرفته می‌شد (ریسک پر شدن دیسک سرور).
    limit_bytes = MAX_GUIDE_FILE_SIZE_MB * 1024 * 1024
    if file.size > limit_bytes:
        raise ValidationError(f'حجم فایل نباید بیشتر از {MAX_GUIDE_FILE_SIZE_MB} مگابایت باشد.')


class Guide(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    file = models.FileField(
        upload_to='guides/%Y/%m/%d/',
        verbose_name="فایل",
        # قبلاً هیچ محدودیتی روی نوع فایل نبود - هر پسوندی (حتی .exe یا
        # .php) قابل آپلود بود. چون این validator روی خود فیلد مدل است،
        # DRF هم به‌صورت خودکار همین اعتبارسنجی را در سریالایزر اعمال
        # می‌کند (نیازی به تکرارش در serializers.py نیست).
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_GUIDE_EXTENSIONS),
            validate_guide_file_size,
        ],
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    download_count = models.PositiveIntegerField(default=0, verbose_name="تعداد دانلود")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ آپلود")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "راهنما"
        verbose_name_plural = "راهنماها"

    def __str__(self):
        return self.title

    def filename(self):
        # os.path.basename به‌جای split('/')[-1] - رفتار یکسان ولی
        # استانداردتر و مقاوم‌تر در برابر نام‌های مسیر غیرمعمول.
        return os.path.basename(self.file.name) if self.file else ''

    def increase_download(self):
        # افزایش اتمیک در سطح دیتابیس (نه read-then-write) تا زیر بار
        # دانلود همزمان چندین کاربر، هیچ افزایشی گم نشود.
        type(self).objects.filter(pk=self.pk).update(download_count=F('download_count') + 1)
        self.refresh_from_db(fields=['download_count'])
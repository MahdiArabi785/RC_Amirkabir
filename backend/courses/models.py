# courses/models.py
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify


class Course(models.Model):
    title = models.CharField('عنوان', max_length=200)
    slug = models.SlugField('اسلاگ', max_length=200, unique=True, blank=True)
    description = models.TextField('توضیحات', blank=True)
    thumbnail = models.ImageField(
        'تصویر بند‌انگشتی',
        upload_to='courses/thumbnails/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ بروزرسانی', auto_now=True)
    is_active = models.BooleanField('فعال', default=True)

    class Meta:
        verbose_name = 'دوره'
        verbose_name_plural = 'دوره‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # قبلاً اگر دو دوره عنوان یکسان داشتند (مثلاً هردو "مقدماتی")،
        # slugify هر دو مقدار یکسانی تولید می‌کرد و چون slug یکتا
        # (unique=True) است، ذخیره‌ی دومی با IntegrityError کرش می‌کرد.
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True)
            slug_candidate = base_slug
            counter = 1
            while Course.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
                counter += 1
                slug_candidate = f'{base_slug}-{counter}'
            self.slug = slug_candidate
        super().save(*args, **kwargs)


class Video(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='videos',
        verbose_name='دوره'
    )
    title = models.CharField('عنوان', max_length=200)
    description = models.TextField('توضیحات', blank=True)
    video_file = models.FileField(
        'فایل ویدیو',
        upload_to='courses/videos/',
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'webm', 'ogg'])],
        help_text='فرمت‌های مجاز: mp4, webm, ogg'
    )
    thumbnail = models.ImageField(
        'تصویر بند‌انگشتی (اختیاری)',
        upload_to='courses/thumbnails/',
        blank=True,
        null=True
    )
    order = models.PositiveIntegerField(
        'ترتیب', default=0,
        help_text='اگر صفر بماند، خودکار بعد از آخرین ویدیوی دوره قرار می‌گیرد.'
    )
    duration = models.PositiveIntegerField('مدت زمان (ثانیه)', default=0, help_text='در صورت تمایل وارد کنید')
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'ویدیو'
        verbose_name_plural = 'ویدیوها'
        # قبلاً اینجا `unique_together = [['course', 'order']]` بود.
        # چون order مقدار پیش‌فرض 0 دارد، افزودن دومین ویدیوی یک دوره
        # بدون تعیین دستی ترتیب - چه از inline پنل ادمین (که برای هر
        # ردیف خالی همان 0 پیش‌فرض را نشان می‌دهد)، چه از API - بلافاصله
        # با خطای یکتایی رد می‌شد؛ در پنل ادمین این خطا حتی قبل از رسیدن
        # به save() (در اعتبارسنجی فرم) رخ می‌داد، پس اصلاح فقط در
        # save() کافی نبود. ترتیب نمایش صرفاً یک مقدار راهنماست نه یک
        # محدودیت یکپارچگی داده، برای همین این قید حذف شد؛ تساوی order
        # با created_at به‌عنوان tie-breaker در Meta.ordering مدیریت
        # می‌شود.
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def save(self, *args, **kwargs):
        # اگر ویدیوی جدید بدون تعیین دستی ترتیب ثبت شود (order هنوز
        # همان مقدار پیش‌فرض 0 است)، به‌جای برخورد با ویدیوهای قبلی
        # همان دوره، خودکار بعد از آخرین ویدیوی موجود قرار می‌گیرد.
        if self._state.adding and self.order == 0:
            last_order = Video.objects.filter(course=self.course).aggregate(
                models.Max('order')
            )['order__max']
            if last_order is not None:
                self.order = last_order + 1
        super().save(*args, **kwargs)
# sitesettings/models.py
from django.db import models


class SiteSettings(models.Model):
    """تنظیمات کلی سایت. این مدل singleton است - همیشه باید فقط یک
    رکورد از آن وجود داشته باشد (لوگو/نام سایت چیزی نیست که چند نمونه
    از آن معنا داشته باشد)."""
    site_name = models.CharField('نام سایت', max_length=100, blank=True)
    tagline = models.CharField('شعار/توضیح کوتاه', max_length=255, blank=True)
    logo = models.ImageField('لوگو', upload_to='site/logo/', blank=True, null=True)
    favicon = models.ImageField('فاوآیکون', upload_to='site/favicon/', blank=True, null=True)
    updated_at = models.DateTimeField('آخرین بروزرسانی', auto_now=True)

    class Meta:
        verbose_name = 'تنظیمات سایت'
        verbose_name_plural = 'تنظیمات سایت'

    def __str__(self):
        return self.site_name or 'تنظیمات سایت'

    def save(self, *args, **kwargs):
        # الگوی singleton: pk همیشه 1 اجباری می‌شود تا حتی اگر کسی
        # مستقیم از شل یا اسکریپت تلاش کند رکورد دوم بسازد، همان رکورد
        # اول بازنویسی شود نه اینکه رکورد جدیدی اضافه شود.
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # حذف تنظیمات سایت معنا ندارد - همیشه باید یک رکورد وجود داشته باشد.
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Banner(models.Model):
    """اسلایدهای بنر صفحه‌ی اصلی."""
    title = models.CharField('عنوان', max_length=200, blank=True)
    subtitle = models.CharField('زیرعنوان', max_length=300, blank=True)
    image = models.ImageField('تصویر', upload_to='site/banners/')
    link_url = models.URLField('لینک مقصد', blank=True)
    order = models.PositiveIntegerField('ترتیب', default=0)
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'بنر'
        verbose_name_plural = 'بنرها'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title or f'بنر #{self.pk}'

    def save(self, *args, **kwargs):
        # همان الگوی order خودکار که در اپ courses استفاده شد - اگر
        # کسی ترتیب را دستی مشخص نکند (order=0 پیش‌فرض بماند)، بنر
        # خودکار بعد از آخرین بنر موجود قرار می‌گیرد.
        if self._state.adding and self.order == 0:
            last_order = Banner.objects.aggregate(models.Max('order'))['order__max']
            if last_order is not None:
                self.order = last_order + 1
        super().save(*args, **kwargs)


class Supporter(models.Model):
    """لوگوی سازمان‌ها/نهادهایی که از ما حمایت می‌کنند - عمداً یک مدل
    کاملاً جدا از SiteSettings.logo (لوگوی خود سایت). این دو مفهوم
    متفاوتی هستند: یکی هویت بصری خود سایت است (تک‌مورد)، دیگری فهرستی
    از حامیان بیرونی است (چندمورد، هرکدام با نام/لینک مخصوص به خودش)."""
    name = models.CharField('نام حامی', max_length=150)
    logo = models.ImageField('لوگو', upload_to='site/supporters/')
    website_url = models.URLField('لینک وبسایت', blank=True)
    order = models.PositiveIntegerField('ترتیب', default=0)
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'حامی'
        verbose_name_plural = 'حامیان'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self._state.adding and self.order == 0:
            last_order = Supporter.objects.aggregate(models.Max('order'))['order__max']
            if last_order is not None:
                self.order = last_order + 1
        super().save(*args, **kwargs)
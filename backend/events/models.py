# events/models.py
from django.db import models
from django.db.models import F
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    is_active = models.BooleanField(default=True, verbose_name="فعال", db_index=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=['is_active'])


class PublishMixin(models.Model):
    is_published = models.BooleanField(default=False, verbose_name="منتشر شده", db_index=True)
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان انتشار")

    class Meta:
        abstract = True

    def publish(self):
        self.is_published = True
        if not self.published_at:
            self.published_at = timezone.now()
        self.save(update_fields=['is_published', 'published_at'])

    def unpublish(self):
        self.is_published = False
        self.save(update_fields=['is_published'])


class SlugMixin(models.Model):
    slug = models.SlugField(max_length=255, unique=True, verbose_name="نامک", allow_unicode=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # حتی اگر slug داده شده باشد (مثلاً prepopulated_fields در admin)،
        # اگر تکراری باشد خودکار suffix می‌زند.
        base_slug = (self.slug or '').strip()
        if not base_slug and hasattr(self, 'title'):
            base_slug = slugify(self.title, allow_unicode=True) or 'item'

        slug_candidate = base_slug
        counter = 1
        model_class = type(self)
        while model_class.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
            counter += 1
            slug_candidate = f'{base_slug}-{counter}'
        self.slug = slug_candidate
        super().save(*args, **kwargs)


class ViewCountMixin(models.Model):
    view_count = models.PositiveIntegerField(default=0, verbose_name="تعداد بازدید")

    class Meta:
        abstract = True

    def increase_view(self):
        updated = type(self).objects.filter(pk=self.pk).update(
            view_count=F('view_count') + 1
        )
        if updated:
            try:
                self.refresh_from_db(fields=['view_count'])
            except type(self).DoesNotExist:
                pass


class News(BaseModel, PublishMixin, SlugMixin, ViewCountMixin):
    title = models.CharField(max_length=200, verbose_name="عنوان")
    summary = models.TextField(max_length=500, verbose_name="خلاصه", null=True, blank=True)
    content = models.TextField(verbose_name="متن کامل")
    cover_image = models.ImageField(
        upload_to='events/news/covers/', null=True, blank=True, verbose_name="تصویر شاخص",
    )
    source = models.URLField(max_length=255, null=True, blank=True, verbose_name="منبع")

    class Meta:
        verbose_name = "خبر"
        verbose_name_plural = "اخبار"
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class Event(BaseModel, PublishMixin, SlugMixin, ViewCountMixin):
    class EventType(models.TextChoices):
        IN_PERSON = 'in_person', _('حضوری')
        ONLINE = 'online', _('آنلاین')
        HYBRID = 'hybrid', _('ترکیبی')

    title = models.CharField(max_length=200, verbose_name="عنوان")
    summary = models.TextField(max_length=500, verbose_name="خلاصه", null=True, blank=True)
    content = models.TextField(verbose_name="توضیحات کامل")
    event_type = models.CharField(
        max_length=20, choices=EventType.choices,
        default=EventType.IN_PERSON, verbose_name="نوع برگزاری", db_index=True,
    )
    start_date = models.DateTimeField(verbose_name="تاریخ شروع", db_index=True)
    end_date = models.DateTimeField(verbose_name="تاریخ پایان", db_index=True)
    location = models.CharField(max_length=255, verbose_name="مکان", null=True, blank=True)
    cover_image = models.ImageField(
        upload_to='events/events/covers/', null=True, blank=True, verbose_name="تصویر شاخص",
    )
    capacity = models.PositiveIntegerField(null=True, blank=True, verbose_name="ظرفیت")
    registration_deadline = models.DateTimeField(
        null=True, blank=True, verbose_name="مهلت ثبت‌نام",
    )

    class Meta:
        verbose_name = "رویداد"
        verbose_name_plural = "رویدادها"
        ordering = ['start_date']

    def __str__(self):
        return self.title

    def is_upcoming(self):
        return self.start_date >= timezone.now()


class Call(BaseModel, PublishMixin, SlugMixin, ViewCountMixin):
    class CallType(models.TextChoices):
        RESEARCH = 'research', _('فراخوان مقاله')
        GRANT = 'grant', _('فراخوان گرنت')
        JOB = 'job', _('فراخوان استخدام')
        OTHER = 'other', _('سایر')

    title = models.CharField(max_length=200, verbose_name="عنوان")
    summary = models.TextField(max_length=500, verbose_name="خلاصه", null=True, blank=True)
    content = models.TextField(verbose_name="متن کامل فراخوان")
    call_type = models.CharField(
        max_length=20, choices=CallType.choices,
        default=CallType.RESEARCH, verbose_name="نوع فراخوان", db_index=True,
    )
    deadline = models.DateTimeField(verbose_name="مهلت ارسال", db_index=True)
    contact_email = models.EmailField(verbose_name="ایمیل تماس", null=True, blank=True)
    contact_phone = models.CharField(max_length=20, verbose_name="تلفن تماس", null=True, blank=True)
    document = models.FileField(
        upload_to='events/calls/documents/', null=True, blank=True, verbose_name="فایل پیوست",
    )

    class Meta:
        verbose_name = "فراخوان"
        verbose_name_plural = "فراخوان‌ها"
        ordering = ['deadline']

    def __str__(self):
        return self.title

    def is_expired(self):
        return self.deadline < timezone.now()
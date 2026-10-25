# managements/signals.py
"""
سیگنال‌ها برای ثبت خودکار فعالیت‌های پرخطر.
توجه: فقط فعالیت‌هایی که در Mixin ثبت نمی‌شوند اینجا مدیریت می‌شوند.
"""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ActivityLog

User = get_user_model()


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """فقط ثبت ایجاد اولیه — block/promote در Mixin انجام می‌شود."""
    if created:
        ActivityLog.objects.create(
            action='create',
            model_name='user',
            object_id=str(instance.pk),
            object_repr=instance.email or str(instance.pk),
        )


# توجه: اگر LoggingMixin روی ArticleViewSet active است، اینجا تکرار نکنید.
# برای جلوگیری از duplicate، از یک flag یا signal-level deduplication استفاده کنید.
# در این نسخه، فقط log_action در Mixin انجام می‌شود و این سیگنال حذف شد.
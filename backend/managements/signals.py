# =============================================================================
# managements/signals.py
# سیگنال‌ها برای ثبت خودکار رویدادها (اختیاری)
# =============================================================================

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from accounts.models import Article, Course
from events.models import Event, Call, News
from guides.models import Guide
from sitesettings.models import Banner
from .models import ActivityLog

User = get_user_model()


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance,
            action='create',
            model_name='User',
            object_id=str(instance.id),
            object_repr=instance.email
        )


@receiver(post_delete, sender=Article)
def article_post_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        action='delete',
        model_name='Article',
        object_id=str(instance.id),
        object_repr=instance.title
    )
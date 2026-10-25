# core/mixins.py
"""
Mixinهای مشترک برای مدل‌ها و viewها.
"""
import logging

from django.db import transaction
from django.db.models import F, Max

logger = logging.getLogger(__name__)


class IncreaseCounterMixin:
    """
    برای مدل‌هایی که counter دارند (download_count/view_count).
    افزایش اتمیک + refresh امن.

    استفاده:
        class Guide(IncreaseCounterMixin, models.Model):
            counter_field = 'download_count'
            download_count = models.PositiveIntegerField(default=0)

        guide.increase_counter()  # به‌جای increase_download
    """
    counter_field = None

    def increase_counter(self):
        if not self.counter_field:
            raise NotImplementedError(
                f"{type(self).__name__}.counter_field تعریف نشده است."
            )
        updated = type(self).objects.filter(pk=self.pk).update(
            **{self.counter_field: F(self.counter_field) + 1}
        )
        if updated:
            try:
                self.refresh_from_db(fields=[self.counter_field])
            except type(self).DoesNotExist:
                pass


class AutoOrderMixin:
    """
    برای مدل‌هایی که فیلد `order` دارند و اگر 0 بود، خودکار بعد از آخرین
    رکورد قرار می‌گیرد. race-safe با transaction + select_for_update.

    استفاده:
        class Banner(AutoOrderMixin, models.Model):
            order_field = 'order'
            order = models.PositiveIntegerField(default=0)
    """
    order_field = 'order'

    def _assign_order_if_needed(self):
        if not self._state.adding:
            return
        if getattr(self, self.order_field, 0) != 0:
            return

        # برای race safety
        with transaction.atomic():
            last = (
                type(self).objects
                .select_for_update()
                .aggregate(Max(self.order_field))[f'{self.order_field}__max']
            )
            setattr(self, self.order_field, (last or 0) + 1)

    def save(self, *args, **kwargs):
        self._assign_order_if_needed()
        super().save(*args, **kwargs)
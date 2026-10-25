# core/mixins.py
"""Mixinهای مشترک برای مدل‌ها."""
import logging

from django.db import IntegrityError, transaction
from django.db.models import F

logger = logging.getLogger(__name__)


class IncreaseCounterMixin:
    """افزایش اتمیک counter_field."""
    counter_field = None

    def increase_counter(self):
        if not self.counter_field:
            raise NotImplementedError(
                f"{type(self).__name__}.counter_field تعریف نشده است."
            )
        if self.pk is None:
            raise ValueError(
                f'{type(self).__name__} باید قبل از increase_counter ذخیره شود.'
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
    اگر فیلد order صفر بود، خودکار بعد از آخرین رکورد قرار می‌گیرد.
    پیش‌نیاز: مدل باید UniqueConstraint(fields=['order']) داشته باشد.
    """
    order_field = 'order'
    order_max_retries = 3

    def _next_order_value(self) -> int:
        last = (
            type(self).objects
            .order_by(f'-{self.order_field}')
            .values_list(self.order_field, flat=True)
            .first()
        )
        return (last or 0) + 1

    def _assign_order_if_needed(self):
        if not self._state.adding:
            return
        if getattr(self, self.order_field, 0) != 0:
            return
        setattr(self, self.order_field, self._next_order_value())

    def save(self, *args, **kwargs):
        if not self._state.adding or getattr(self, self.order_field, 0) != 0:
            return super().save(*args, **kwargs)

        last_exc = None
        for attempt in range(self.order_max_retries):
            self._assign_order_if_needed()
            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError as exc:
                last_exc = exc
                logger.warning(
                    'AutoOrderMixin: order conflict on %s (attempt %d/%d)',
                    type(self).__name__, attempt + 1, self.order_max_retries,
                )
                setattr(self, self.order_field, 0)
        if last_exc is not None:
            raise last_exc

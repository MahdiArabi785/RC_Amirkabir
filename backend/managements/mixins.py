# managements/mixins.py
import logging

from rest_framework import status
from rest_framework.response import Response

from .models import ActivityLog

logger = logging.getLogger(__name__)


class LoggingMixin:
    """لاگ فعالیت‌ها — حالا واقعاً در DB ذخیره می‌شود."""

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return self.request.META.get('REMOTE_ADDR')

    def log_action(self, action, instance=None, changes=None):
        user = getattr(self.request, 'user', None)
        if not (user and user.is_authenticated):
            return
        try:
            ActivityLog.objects.create(
                user=user,
                action=action,
                model_name=instance._meta.model_name if instance else '',
                object_id=str(instance.pk) if instance else None,
                object_repr=str(instance) if instance else '',
                changes=changes or {},
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:2000],
            )
        except Exception:
            # اگر لاگ fail شد، نباید کل درخواست را بشکند
            logger.exception('ActivityLog create failed')


class ApiResponseMixin:
    def get_serializer_errors(self, serializer):
        return {
            field: [str(e) for e in errors]
            for field, errors in serializer.errors.items()
        }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                'success': True,
                'message': 'با موفقیت ایجاد شد',
                'data': serializer.data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': self.get_serializer_errors(serializer),
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                'success': True,
                'message': 'با موفقیت بروزرسانی شد',
                'data': serializer.data,
            })
        return Response({
            'success': False,
            'errors': self.get_serializer_errors(serializer),
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': 'با موفقیت حذف شد',
        }, status=status.HTTP_200_OK)
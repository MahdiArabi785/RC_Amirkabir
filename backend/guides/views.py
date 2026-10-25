# guides/views.py
import logging
import os

from django.http import FileResponse, Http404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.throttling import AnonRateThrottle

from .models import Guide
from .permissions import IsAdminOrReadOnly
from .serializers import GuideSerializer

logger = logging.getLogger(__name__)


# =============================================================================
# Throttle classes — بدون استفاده از throttle_scope در @action
# =============================================================================
class DownloadRateThrottle(AnonRateThrottle):
    """
    throttle مخصوص دانلود.

    چرا `AnonRateThrottle` (نه `UserRateThrottle`): endpoint دانلود عمومی
    است و کاربر ناشناس هم می‌تواند دانلود کند. `UserRateThrottle` فقط
    کاربران authenticated را throttle می‌کند.

    scope='download' در settings.DEFAULT_THROTTLE_RATES تعریف شده
    (پیش‌فرض: 60/hour).
    """
    scope = 'download'


# =============================================================================
# Helper
# =============================================================================
def _can_see_inactive(user) -> bool:
    """آیا این کاربر می‌تواند راهنماهای غیرفعال را ببیند؟ (ادمین‌ها)"""
    return bool(
        user
        and user.is_authenticated
        and getattr(user, 'is_admin', False)
    )


# =============================================================================
# ViewSet
# =============================================================================
class GuideViewSet(viewsets.ModelViewSet):
    """
    CRUD راهنماها.

    - خواندن (GET): برای همه آزاد است (فقط راهنماهای فعال).
    - نوشتن (POST/PUT/PATCH/DELETE): فقط ادمین‌ها.
    - دانلود: عمومی، ولی با rate limit.

    نکته: filter_backends باید **کلاس** باشد (نه رشته). در settings
    می‌شود رشته گذاشت ولی روی view نمی‌شود — TypeError می‌دهد.
    """
    serializer_class = GuideSerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at', 'download_count', 'title']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        if _can_see_inactive(self.request.user):
            return Guide.objects.all()
        return Guide.objects.filter(is_active=True)

    @action(
        detail=True,
        methods=['get'],
        url_path='download',
        throttle_classes=[DownloadRateThrottle],
    )
    def download(self, request, pk=None):
        """
        دانلود فایل راهنما.

        - فایل با filename زیبا (بدون suffix تصادفی storage) برمی‌گردد.
        - download_count به‌صورت اتمیک زیاد می‌شود.
        - Cache-Control ست می‌شود تا مرورگر کش کند.
        - اگر بین open و return خطایی رخ دهد، file_handle بسته می‌شود
          (جلوگیری از leak فایل‌دسکریپتور).
        """
        guide = self.get_object()

        if not guide.file:
            raise Http404("فایلی برای این راهنما ثبت نشده است.")

        try:
            file_handle = guide.file.open('rb')
        except (FileNotFoundError, OSError):
            raise Http404("فایل مورد نظر یافت نشد.")

        # filename زیبا: title اصلی + پسوند فایل
        ext = os.path.splitext(guide.file.name)[1].lower()
        safe_title = (
            (guide.title or 'guide')
            .replace('"', '')
            .replace('\n', ' ')
            .strip()
        )
        filename = f'{safe_title}{ext}'

        try:
            guide.increase_download()
            response = FileResponse(
                file_handle,
                as_attachment=True,
                filename=filename,
            )
            response['Cache-Control'] = 'public, max-age=86400'
            return response
        except Exception:
            file_handle.close()
            logger.exception('guide download failed pk=%s', guide.pk)
            raise
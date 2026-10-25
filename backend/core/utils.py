# core/utils.py
"""helperهای کوچک که در چند اپ تکرار می‌شوند."""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def get_client_ip(request) -> str:
    """
    IP کاربر با پشتیبانی از reverse proxy.

    هشدار امنیتی: X-Forwarded-For توسط کلاینت قابل جعل است. فقط زمانی که
    پشت یک load balancer مطمئن هستید (که XFF را overwrite می‌کند) از این
    استفاده کنید. TRUSTED_PROXIES در settings باید ست شود.
    """
    if not request:
        return ''

    remote_addr = request.META.get('REMOTE_ADDR', '')
    trusted_proxies = getattr(settings, 'TRUSTED_PROXIES', [])

    if trusted_proxies and remote_addr in trusted_proxies:
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[-1].strip()

    return remote_addr


def build_absolute_url(request, field) -> str | None:
    """URL مطلق برای ImageField/FileField."""
    if not field:
        return None
    try:
        if request:
            return request.build_absolute_uri(field.url)
        return field.url
    except (ValueError, OSError) as exc:
        logger.warning('build_absolute_url failed: %s', exc)
        return None

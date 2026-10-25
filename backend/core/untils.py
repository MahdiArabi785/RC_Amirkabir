# core/utils.py
"""helperهای کوچک که در چند اپ تکرار می‌شوند."""

def get_client_ip(request) -> str:
    """IP کاربر با پشتیبانی از proxy."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def build_absolute_url(request, field) -> str | None:
    """URL مطلق برای ImageField/FileField (جلوگیری از تکرار در serializers)."""
    if not field:
        return None
    if request:
        return request.build_absolute_uri(field.url)
    return field.url  # fallback نسبی
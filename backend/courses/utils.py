# courses/utils.py
import os
import re

from django.http import StreamingHttpResponse
from django.utils.http import http_date

CHUNK_SIZE = 8192


class VideoStreamer:
    """کلاس مدیریت استریم ویدیو با پشتیبانی از HTTP Range."""

    CONTENT_TYPES = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.ogg': 'video/ogg',
    }

    def __init__(self, file_path, range_header=None):
        self.file_path = file_path
        self.range_header = range_header
        self.file_size = os.path.getsize(file_path)

    def get_content_type(self):
        """تشخیص نوع MIME بر اساس پسوند فایل"""
        ext = os.path.splitext(self.file_path)[1].lower()
        return self.CONTENT_TYPES.get(ext, 'application/octet-stream')

    def parse_range(self):
        """پردازش هدر Range طبق RFC 7233. سه حالت برمی‌گرداند:
        - (None, None, False): بدون Range یا نامفهوم -> کل فایل با 200
        - (start, end, False): بازه‌ی معتبر -> 206
        - (None, None, True): بازه‌ی خارج از محدوده‌ی فایل -> باید 416 برگردد

        قبلاً وقتی end از اندازه‌ی فایل بزرگ‌تر بود یا start نامعتبر
        بود، به‌جای رفتار درست (محدودکردن end به آخر فایل، یا برگرداندن
        416)، کل درخواست به‌سکوت به یک پاسخ کامل 200 تبدیل می‌شد که طبق
        استاندارد نادرست است و می‌تواند پخش‌کننده‌های ویدیو را گیج کند.
        """
        if not self.range_header:
            return None, None, False

        # علاوه بر 'bytes=START-END' و 'bytes=START-'، حالت
        # 'bytes=-SUFFIX' (یعنی SUFFIX بایت آخر فایل) هم پشتیبانی
        # می‌شود که قبلاً اصلاً مدیریت نمی‌شد.
        range_match = re.match(r'bytes=(\d*)-(\d*)', self.range_header)
        if not range_match:
            return None, None, False

        start_str, end_str = range_match.groups()
        if not start_str and not end_str:
            return None, None, False

        if not start_str:
            suffix_length = int(end_str)
            if suffix_length <= 0:
                return None, None, False
            start = max(self.file_size - suffix_length, 0)
            end = self.file_size - 1
        else:
            start = int(start_str)
            end = int(end_str) if end_str else self.file_size - 1
            end = min(end, self.file_size - 1)

        if start >= self.file_size or start > end:
            return None, None, True

        return start, end, False

    def stream_response(self):
        """ایجاد پاسخ استریم با رعایت Range"""
        content_type = self.get_content_type()
        start, end, unsatisfiable = self.parse_range()

        if unsatisfiable:
            response = StreamingHttpResponse(iter(()), status=416, content_type=content_type)
            response['Content-Range'] = f'bytes */{self.file_size}'
            return response

        if start is None:
            # کل فایل
            response = StreamingHttpResponse(
                self.file_iterator(0, self.file_size - 1),
                content_type=content_type,
            )
            response['Content-Length'] = self.file_size
        else:
            # پاسخ بخشی (Partial Content)
            content_length = end - start + 1
            response = StreamingHttpResponse(
                self.file_iterator(start, end),
                content_type=content_type,
                status=206,
            )
            response['Content-Range'] = f'bytes {start}-{end}/{self.file_size}'
            response['Content-Length'] = content_length

        response['Accept-Ranges'] = 'bytes'
        # قبلاً import های HttpResponse/HttpResponseNotModified/unquote/
        # settings همه بدون استفاده در فایل مانده بودند - نشانه‌ای از
        # اینکه پشتیبانی caching قرار بوده اضافه شود ولی هیچ‌وقت پیاده
        # نشد. Last-Modified اضافه شد تا مرورگر/پخش‌کننده بتواند فایل را
        # کش کند.
        response['Last-Modified'] = http_date(os.path.getmtime(self.file_path))
        return response

    def file_iterator(self, start, end):
        """ژنراتور برای خواندن بخش مورد نظر از فایل"""
        with open(self.file_path, 'rb') as f:
            f.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                read_size = min(CHUNK_SIZE, remaining)
                data = f.read(read_size)
                if not data:
                    break
                remaining -= len(data)
                yield data
# quizes/validators.py
"""
اعتبارسنجی فایل‌های آپلودی (پاسخ + صورت سؤال).

چرا magic bytes: پسوند و content_type ارسالی کاربر قابل جعل هستند.
فقط خواندن بایت‌های ابتدای فایل می‌تواند تضمین کند فایل واقعاً همان
فرمتی است که ادعا می‌شود. بدون این بررسی، کاربر می‌تواند مثلاً یک
اجرایی exe را با نام answer.pdf آپلود کند و اگر بعداً آن را با
پسوند اصلی خودش سرو کنیم، خطر امنیتی جدی ایجاد می‌شود.

نکته: این validator جایگزین آنتی‌ویروس نیست. در production، توصیه
می‌شود از ClamAV یا سرویس مشابه استفاده کنید.
"""
import os

from django.core.exceptions import ValidationError


# --- MIME signatures ---
PDF_MAGIC = b'%PDF'
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'
JPEG_MAGIC = b'\xff\xd8\xff'
WEBP_RIFF = b'RIFF'
WEBP_MARK = b'WEBP'
ZIP_MAGIC = b'PK\x03\x04'   # DOCX هم ZIP است
OLE_MAGIC = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'  # DOC قدیمی


ALLOWED_ANSWER_EXTS = {'pdf', 'jpg', 'jpeg', 'png'}
ALLOWED_QUESTION_IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'webp'}
ALLOWED_QUESTION_DOC_EXTS = {'pdf', 'docx', 'doc'}


def _read_head(file_obj, n: int = 16) -> bytes:
    """
    خواندن n بایت اول بدون مصرف کردن استریم.

    اگر فایل seek/read را پشتیبانی نکند (نادر)، bytes خالی برمی‌گرداند.
    """
    try:
        if hasattr(file_obj, 'seek') and hasattr(file_obj, 'tell'):
            pos = file_obj.tell()
            try:
                file_obj.seek(0)
                return file_obj.read(n)
            finally:
                file_obj.seek(pos)
    except (OSError, ValueError, AttributeError):
        pass
    return b''


def _ext(file_obj) -> str:
    """پسوند فایل به‌صورت lowercase بدون نقطه."""
    name = getattr(file_obj, 'name', '') or ''
    return os.path.splitext(name)[1].lower().lstrip('.')


def validate_pdf_magic(file_obj) -> None:
    if not _read_head(file_obj, len(PDF_MAGIC)).startswith(PDF_MAGIC):
        raise ValidationError('فایل PDF نامعتبر است.')


def validate_image_magic(file_obj) -> None:
    ext = _ext(file_obj)
    head = _read_head(file_obj, 16)
    if ext in ('jpg', 'jpeg'):
        if not head.startswith(JPEG_MAGIC):
            raise ValidationError('فایل JPEG نامعتبر است.')
    elif ext == 'png':
        if not head.startswith(PNG_MAGIC):
            raise ValidationError('فایل PNG نامعتبر است.')
    elif ext == 'webp':
        if not (head.startswith(WEBP_RIFF) and head[8:12] == WEBP_MARK):
            raise ValidationError('فایل WEBP نامعتبر است.')
    else:
        raise ValidationError(f'پسوند {ext} برای تصویر مجاز نیست.')


def validate_docx_magic(file_obj) -> None:
    """DOCX یک فایل ZIP است که باید با PK\x03\x04 شروع شود."""
    if not _read_head(file_obj, len(ZIP_MAGIC)).startswith(ZIP_MAGIC):
        raise ValidationError('فایل DOCX نامعتبر است.')


def validate_doc_magic(file_obj) -> None:
    """DOC قدیمی با امضای OLE مشخص می‌شود."""
    if not _read_head(file_obj, len(OLE_MAGIC)).startswith(OLE_MAGIC):
        raise ValidationError('فایل DOC نامعتبر است.')


def validate_size(file_obj, max_mb: int) -> None:
    if file_obj.size > max_mb * 1024 * 1024:
        raise ValidationError(
            f'حجم فایل «{os.path.basename(file_obj.name)}» نباید بیشتر از '
            f'{max_mb} مگابایت باشد.'
        )


def validate_answer_file(file_obj, max_size_mb: int) -> None:
    """
    اعتبارسنجی کامل فایل پاسخ تشریحی:
      - حجم
      - پسوند در {pdf, jpg, jpeg, png}
      - magic bytes منطبق با پسوند
    """
    validate_size(file_obj, max_size_mb)
    ext = _ext(file_obj)
    if ext not in ALLOWED_ANSWER_EXTS:
        raise ValidationError(
            f'پسوند «{ext}» برای پاسخ مجاز نیست. '
            f'مجاز: {sorted(ALLOWED_ANSWER_EXTS)}'
        )
    if ext == 'pdf':
        validate_pdf_magic(file_obj)
    else:
        validate_image_magic(file_obj)


def validate_question_image(file_obj, max_size_mb: int = 10) -> None:
    validate_size(file_obj, max_size_mb)
    ext = _ext(file_obj)
    if ext not in ALLOWED_QUESTION_IMAGE_EXTS:
        raise ValidationError(
            f'پسوند «{ext}» برای تصویر سؤال مجاز نیست.'
        )
    validate_image_magic(file_obj)


def validate_question_document(file_obj, max_size_mb: int = 20) -> None:
    validate_size(file_obj, max_size_mb)
    ext = _ext(file_obj)
    if ext not in ALLOWED_QUESTION_DOC_EXTS:
        raise ValidationError(
            f'پسوند «{ext}» برای سند سؤال مجاز نیست. '
            f'مجاز: {sorted(ALLOWED_QUESTION_DOC_EXTS)}'
        )
    if ext == 'pdf':
        validate_pdf_magic(file_obj)
    elif ext == 'docx':
        validate_docx_magic(file_obj)
    elif ext == 'doc':
        validate_doc_magic(file_obj)
// src/utils/format.ts

/**
 * فرمت تاریخ ISO به تاریخ شمسی (مثلاً "۱۵ مهر ۱۴۰۵")
 */
export function formatPersianDate(isoDate: string | null | undefined): string {
  if (!isoDate) return '—';
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) return '—';

  return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
}

/**
 * فرمت حجم بایت به رشته خوانا (مثلاً "۲.۴ مگابایت")
 */
export function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null || bytes <= 0) return 'نامشخص';
  if (bytes < 1024) return `${bytes.toLocaleString('fa-IR')} بایت`;
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toLocaleString('fa-IR', {
      maximumFractionDigits: 1,
    })} کیلوبایت`;
  }
  return `${(bytes / (1024 * 1024)).toLocaleString('fa-IR', {
    maximumFractionDigits: 1,
  })} مگابایت`;
}

/**
 * تخمین زمان مطالعه بر اساس تعداد کلمات (۲۰۰ کلمه در دقیقه)
 */
export function estimateReadingTime(content: string | null | undefined): number {
  if (!content) return 1;
  const words = content.trim().split(/\s+/).length;
  return Math.max(1, Math.ceil(words / 200));
}

/**
 * نرمال‌سازی متن فارسی برای جستجو
 */
export function normalizePersian(value: string): string {
  return value
    .trim()
    .toLocaleLowerCase('fa-IR')
    .replace(/ي/g, 'ی')
    .replace(/ى/g, 'ی')
    .replace(/ك/g, 'ک')
    .replace(/\u200c/g, ' ')
    .replace(/\s+/g, ' ');
}

/**
 * استخراج پسوند فایل از نام (بدون نقطه)
 */
export function getFileExtension(fileName: string): string {
  const parts = fileName.split('.');
  if (parts.length < 2) return '';
  return (parts.pop() || '').toUpperCase();
}

/**
 * جایگزین تصویر خالی با placeholder
 */
export const PLACEHOLDER_IMAGE =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
      <rect fill="#f1f5f9" width="400" height="300"/>
      <text x="50%" y="50%" text-anchor="middle" fill="#cbd5e1"
            font-family="sans-serif" font-size="16" dy=".3em">
        بدون تصویر
      </text>
    </svg>`,
  );
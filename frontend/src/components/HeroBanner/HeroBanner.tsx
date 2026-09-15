import type { CSSProperties, MouseEventHandler } from 'react';
import './HeroBanner.css';

type HorizontalPosition = 'left' | 'center' | 'right';
type VerticalPosition = 'top' | 'center' | 'bottom';

type BannerAlignment =
  | 'top-left'
  | 'top-center'
  | 'top-right'
  | 'center-left'
  | 'center'
  | 'center-right'
  | 'bottom-left'
  | 'bottom-center'
  | 'bottom-right';

interface HeroBannerButton {
  label: string;
  href?: string;
  variant?: string;
  className?: string;
  target?: '_self' | '_blank';
  rel?: string;
  onClick?: MouseEventHandler<HTMLAnchorElement>;
}

interface HeroBannerProps {
  /**
   * آدرس تصویر پس‌زمینه
   */
  backgroundImage: string;

  /**
   * عنوان اصلی بنر
   */
  title: string;

  /**
   * توضیح اختیاری
   */
  description?: string;

  /**
   * دکمه‌های بنر
   */
  buttons?: HeroBannerButton[];

  /**
   * یکی از ۹ موقعیت آماده
   * در صورت ارسال این prop، اولویت با آن است.
   */
  alignment?: BannerAlignment;

  /**
   * موقعیت افقی محتوا
   */
  horizontalPosition?: HorizontalPosition;

  /**
   * موقعیت عمودی محتوا
   */
  verticalPosition?: VerticalPosition;

  /**
   * نسبت طول به عرض بنر
   *
   * نمونه:
   * 16 / 7
   * 16 / 9
   * 4 / 3
   * 1 / 1
   */
  aspectRatio?: string;

  /**
   * موقعیت تصویر پس‌زمینه
   *
   * نمونه:
   * center
   * center right
   * top center
   * 70% center
   */
  backgroundPosition?: string;

  /**
   * نحوه قرارگیری تصویر
   */
  backgroundSize?: 'cover' | 'contain' | 'auto';

  /**
   * رنگ متن
   */
  textColor?: 'light' | 'dark' | 'white' | 'black';

  /**
   * کلاس اضافه برای شخصی‌سازی بیرونی
   */
  className?: string;

  /**
   * متن جایگزین برای دسترسی‌پذیری
   */
  imageAlt?: string;

  /**
   * جهت متن
   */
  dir?: 'rtl' | 'ltr';
}

const alignmentMap: Record<
  BannerAlignment,
  {
    horizontal: HorizontalPosition;
    vertical: VerticalPosition;
  }
> = {
  'top-left': {
    horizontal: 'left',
    vertical: 'top',
  },
  'top-center': {
    horizontal: 'center',
    vertical: 'top',
  },
  'top-right': {
    horizontal: 'right',
    vertical: 'top',
  },
  'center-left': {
    horizontal: 'left',
    vertical: 'center',
  },
  center: {
    horizontal: 'center',
    vertical: 'center',
  },
  'center-right': {
    horizontal: 'right',
    vertical: 'center',
  },
  'bottom-left': {
    horizontal: 'left',
    vertical: 'bottom',
  },
  'bottom-center': {
    horizontal: 'center',
    vertical: 'bottom',
  },
  'bottom-right': {
    horizontal: 'right',
    vertical: 'bottom',
  },
};

function getAlignment(
  alignment?: BannerAlignment,
  horizontalPosition: HorizontalPosition = 'right',
  verticalPosition: VerticalPosition = 'center',
) {
  if (alignment) {
    return alignmentMap[alignment];
  }

  return {
    horizontal: horizontalPosition,
    vertical: verticalPosition,
  };
}

function getButtonClassName(button: HeroBannerButton) {
  const variant = button.variant || 'primary';

  return [
    'btn',
    `btn-${variant}`,
    button.className || '',
  ]
    .filter(Boolean)
    .join(' ');
}

export default function HeroBanner({
  backgroundImage,
  title,
  description,
  buttons = [],
  alignment,
  horizontalPosition = 'right',
  verticalPosition = 'center',
  aspectRatio = '16 / 7',
  backgroundPosition = 'center',
  backgroundSize = 'cover',
  textColor = 'light',
  className = '',
  imageAlt = '',
  dir = 'rtl',
}: HeroBannerProps) {
  const selectedAlignment = getAlignment(
    alignment,
    horizontalPosition,
    verticalPosition,
  );

  const bannerStyle = {
    '--hero-banner-background-image': `url("${backgroundImage}")`,
    '--hero-banner-aspect-ratio': aspectRatio,
    '--hero-banner-background-position': backgroundPosition,
    '--hero-banner-background-size': backgroundSize,
  } as CSSProperties;

  const bannerClassName = [
    'hero-banner',
    `hero-banner-horizontal-${selectedAlignment.horizontal}`,
    `hero-banner-vertical-${selectedAlignment.vertical}`,
    `hero-banner-text-${textColor}`,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <section
      className={bannerClassName}
      style={bannerStyle}
      dir={dir}
      aria-label={title}
    >
      {/* این تصویر فقط برای دسترسی‌پذیری و SEO در DOM قرار دارد */}
      {imageAlt && (
        <img
          className="hero-banner-accessible-image"
          src={backgroundImage}
          alt={imageAlt}
        />
      )}

      <div className="hero-banner-content">
        <div className="hero-banner-content-inner">
          <h1 className="hero-banner-title">{title}</h1>

          {description && (
            <p className="hero-banner-description">{description}</p>
          )}

          {buttons.length > 0 && (
            <div className="hero-banner-actions">
              {buttons.map((button, index) => {
                const isExternalBlank =
                  button.target === '_blank' && !button.rel;

                return (
                  <a
                    key={`${button.label}-${index}`}
                    href={button.href || '#'}
                    className={getButtonClassName(button)}
                    target={button.target}
                    rel={
                      button.rel ||
                      (isExternalBlank ? 'noopener noreferrer' : undefined)
                    }
                    onClick={button.onClick}
                  >
                    {button.label}
                  </a>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

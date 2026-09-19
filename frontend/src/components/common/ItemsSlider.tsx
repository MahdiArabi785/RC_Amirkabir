import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Swiper, SwiperSlide } from 'swiper/react';
import { A11y, Keyboard, Pagination } from 'swiper/modules';
import type { Swiper as SwiperClass } from 'swiper';
import { FiChevronRight, FiChevronLeft, FiPlay, FiPause } from 'react-icons/fi';

import 'swiper/css';
import 'swiper/css/pagination';

export type SliderCardItem = {
  id: string | number;
  image?: string;
  video?: string;
  mediaType?: 'image' | 'video';
  title: string;
  description: string;
  to: string;
  alt?: string;
};

export type ItemsSliderProps = {
  items: SliderCardItem[];
  title?: string;
  subtitle?: string;
  slidesPerView?: number;
  slidesPerViewDesktop?: number;
  spaceBetween?: number;
  showNavigation?: boolean;
  showPagination?: boolean;
  className?: string;
};


// کامپوننت اختصاصی مدیا ویدیو با قابلیت کلیک برای پخش/توقف
function VideoMediaItem({ videoSrc, posterSrc }: { videoSrc: string; posterSrc?: string }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const togglePlay = (e: React.MouseEvent) => {
    e.preventDefault(); // جلوگیری از رفتن به صفحه لینک
    e.stopPropagation(); // جلوگیری از فعال شدن رویدادهای والد

    if (!videoRef.current) return;

    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  return (
    <div className="slider-video-container" onClick={togglePlay}>
      <video
        ref={videoRef}
        src={videoSrc}
        poster={posterSrc}
        className="slider-card-image"
        playsInline
        onEnded={() => setIsPlaying(false)}
        onPause={() => setIsPlaying(false)}
        onPlay={() => setIsPlaying(true)}
      />
      {/* دکمه Play / Pause روی ویدیو */}
      <button
        type="button"
        className={`slider-video-play-btn ${isPlaying ? 'playing' : ''}`}
        aria-label={isPlaying ? 'توقف ویدیو' : 'پخش ویدیو'}
      >
        {isPlaying ? <FiPause size={24} /> : <FiPlay size={24} style={{ marginRight: '-2px' }} />}
      </button>
    </div>
  );
}


function ItemsSlider({
  items,
  title,
  subtitle,
  slidesPerView = 2,
  slidesPerViewDesktop = 4,
  spaceBetween = 16,
  showNavigation = true,
  showPagination = true,
  className,
}: ItemsSliderProps) {
  const swiperRef = useRef<SwiperClass | null>(null);

  if (items.length === 0) return null;

  return (
    <div className={`items-slider-wrapper ${className ?? ''}`}>
      {/* بخش هدر اسلایدر: شامل عنوان و دکمه‌های کنترل خارج از اسلایدر */}
      {(title || showNavigation) && (
        <div className="slider-header d-flex align-items-center justify-content-between mb-3">
          <div>
            {title && <h2 className="slider-title h4 fw-bold mb-1">{title}</h2>}
            {subtitle && <p className="slider-subtitle text-muted small mb-0">{subtitle}</p>}
          </div>

          {showNavigation && (
            <div className="slider-navigation-btns d-flex gap-2">
              {/* در RTL: دکمه راست یعنی قبلی (به سمت راست) و چپ یعنی بعدی */}
              <button
                type="button"
                className="slider-nav-btn prev-btn"
                onClick={() => swiperRef.current?.slidePrev()}
                aria-label="اسلاید قبلی"
              >
                <FiChevronRight size={20} />
              </button>
              <button
                type="button"
                className="slider-nav-btn next-btn"
                onClick={() => swiperRef.current?.slideNext()}
                aria-label="اسلاید بعدی"
              >
                <FiChevronLeft size={20} />
              </button>
            </div>
          )}
        </div>
      )}

      {/* اسلایدر اصلی */}
      <Swiper
        className="items-slider"
        modules={[Pagination, Keyboard, A11y]}
        dir="rtl"
        onBeforeInit={(swiper) => {
          swiperRef.current = swiper;
        }}
        slidesPerView={slidesPerView}
        spaceBetween={spaceBetween}
        breakpoints={{
          992: {
            slidesPerView: slidesPerViewDesktop,
            spaceBetween,
          },
        }}
        loop={false}
        grabCursor
        pagination={
          showPagination
            ? {
                clickable: true,
                el: '.custom-swiper-pagination', // رندر نقاط در باکس خارج از اسلایدر
              }
            : false
        }
        keyboard={{ enabled: true, onlyInViewport: true }}
      >
        {items.map((item, index) => (
          <SwiperSlide key={item.id}>
            <Link to={item.to} className="slider-card-link" title={item.title}>
              <article className="slider-card">
                <div className="slider-card-image-wrapper">
                    {item.video ? (
                      <VideoMediaItem videoSrc={item.video} posterSrc={item.image} />
                    ) : (
                        <img
                        src={item.image}
                        alt={item.alt ?? item.title}
                        className="slider-card-image"
                        loading={index < slidesPerViewDesktop ? 'eager' : 'lazy'}
                        draggable={false}
                        />
                    )}
                    </div>

                <div className="slider-card-body">
                  <h3 className="slider-card-title">{item.title}</h3>
                  <p className="slider-card-description">{item.description}</p>
                </div>
              </article>
            </Link>
          </SwiperSlide>
        ))}
      </Swiper>

      {/* نقاط پیمایش که کاملاً زیر اسلایدر رندر می‌شوند */}
      {showPagination && <div className="custom-swiper-pagination text-center mt-3" />}
    </div>
  );
}

export default ItemsSlider;

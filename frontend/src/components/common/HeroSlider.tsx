import Carousel from "react-bootstrap/Carousel";
import { Link } from "react-router-dom";

export type SliderCta = {
  label: string;
  to: string;          // مسیر داخلی
  variant?: string;    // کلاس‌های بوت‌استرپ مثل: "btn-primary" / "btn-outline-light"
};

export type SliderItem = {
  src: string;         // مثل: "/images/slide-1.jpg" (از public)
  alt: string;
  title?: string;
  subtitle?: string;
  cta?: SliderCta;     // اختیاری: فقط بعضی اسلایدها دکمه دارند
};

type HeroSliderProps = {
  items: SliderItem[];
  height?: string;     // ارتفاع ثابت برای یکدستی در مانیتورها
  intervalMs?: number; // پیش‌فرض 3000
};

export default function HeroSlider({
  items,
  height = 'auto',
  intervalMs = 5000,
}: HeroSliderProps) {
  return (
    <Carousel
      interval={intervalMs}
      controls
      indicators
      slide
      touch
      pause="hover"
    >
      {items.map((item, idx) => (
        <Carousel.Item key={idx}>
          {/* تصویر */}
          <img
            className="d-block w-100 hero-slider__img"
            src={item.src}
            alt={item.alt}
            style={{ 
              height, 
              width: "100%",
              objectFit: "contain",
              objectPosition: "center"
            }}
            loading={idx === 0 ? "eager" : "lazy"}
          />

          {/* کپشن اختیاری (اگر title/subtitle/cta داشتیم) */}
          {(item.title || item.subtitle || item.cta) && (
            <Carousel.Caption className="hero-slider__caption text-end">
              {item.title && <h3 className="fw-bold">{item.title}</h3>}
              {item.subtitle && <p className="mb-3">{item.subtitle}</p>}

              {item.cta && (
                <Link
                  to={item.cta.to}
                  className={`btn ${item.cta.variant ?? "btn-primary"} px-4`}
                >
                  {item.cta.label}
                </Link>
              )}
            </Carousel.Caption>
          )}
        </Carousel.Item>
      ))}
    </Carousel>
  );
}

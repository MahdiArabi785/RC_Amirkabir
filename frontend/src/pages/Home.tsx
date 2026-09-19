import HeroSlider, { type SliderItem } from "../components/common/HeroSlider";
import { Swiper, SwiperSlide } from 'swiper/react';
import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/pagination';
import { Navigation, Pagination } from 'swiper/modules';
import { Container } from 'react-bootstrap';
import ItemsSlider from '../components/common/ItemsSlider';
import type { SliderCardItem } from '../components/common/ItemsSlider';
import FAQSection from '../components/FAQSection';
import TrustedCompanies from '../components/TrustedCompanies';
import HeroBanner from '../components/HeroBanner/HeroBanner';


const sliderItems2: SliderCardItem[] = [
  {
    id: 1,
    image: '/images/item-1.jpg',
    alt: 'تصویر خدمات طراحی وب',
    title: 'طراحی وب‌سایت مدرن',
    description:
      'طراحی رابط کاربری زیبا، سریع و واکنش‌گرا برای کسب‌وکارهای مدرن.',
    to: '/services/web-design',
  },
  {
    id: 2,
    image: '/images/item-2.jpg',
    alt: 'تصویر توسعه نرم‌افزار',
    title: 'توسعه نرم‌افزار',
    description:
      'پیاده‌سازی پروژه‌های مقیاس‌پذیر با استفاده از React و TypeScript.',
    to: '/services/software-development',
  },
  {
    id: 3,
    image: '/images/item-3.jpg',
    alt: 'تصویر طراحی رابط کاربری',
    title: 'طراحی رابط کاربری',
    description: 'ساخت تجربه‌ای ساده و حرفه‌ای برای افزایش رضایت کاربران.',
    to: '/services/ui-ux',
  },
  {
    id: 4,
    image: '/images/item-4.jpg',
    alt: 'تصویر سئو',
    title: 'بهینه‌سازی و سئو',
    description: 'بهبود ساختار سایت و افزایش شانس دیده‌شدن در موتورهای جست‌وجو.',
    to: '/services/seo',
  },
  {
    id: 5,
    image: '/images/item-5.jpg',
    alt: 'تصویر پشتیبانی فنی',
    title: 'پشتیبانی فنی',
    description: 'همراهی مداوم برای رفع مشکلات و توسعه امکانات جدید پروژه.',
    to: '/services/support',
  },
];
const sliderItems3: SliderCardItem[] = [
  {
    id: 1,
    video: '/images/video-1.mp4',
    alt: 'ویدئو خدمات طراحی وب',
    title: 'طراحی وب‌سایت مدرن',
    description:
      'طراحی رابط کاربری زیبا، سریع و واکنش‌گرا برای کسب‌وکارهای مدرن.',
    to: '/services/web-design',
  },
  {
    id: 2,
    video: '/images/video-1.mp4',
    alt: 'ویدئو خدمات طراحی وب',
    title: 'توسعه نرم‌افزار',
    description:
      'پیاده‌سازی پروژه‌های مقیاس‌پذیر با استفاده از React و TypeScript.',
    to: '/services/software-development',
  },
  {
    id: 3,
    video: '/images/video-1.mp4',
    alt: 'ویدئو خدمات طراحی وب',
    title: 'طراحی رابط کاربری',
    description: 'ساخت تجربه‌ای ساده و حرفه‌ای برای افزایش رضایت کاربران.',
    to: '/services/ui-ux',
  },
  {
    id: 4,
    video: '/images/video-1.mp4',
    alt: 'ویدئو خدمات طراحی وب',
    title: 'بهینه‌سازی و سئو',
    description: 'بهبود ساختار سایت و افزایش شانس دیده‌شدن در موتورهای جست‌وجو.',
    to: '/services/seo',
  },
  {
    id: 5,
    video: '/images/video-1.mp4',
    alt: 'ویدئو خدمات طراحی وب',
    title: 'پشتیبانی فنی',
    description: 'همراهی مداوم برای رفع مشکلات و توسعه امکانات جدید پروژه.',
    to: '/services/support',
  },
];


const sliderItems: SliderItem[] = [
  {
    src: "/images/slide-1.png",
    alt: "اسلاید ۱",
    // title: "به پلتفرم ما خوش آمدید",
    // subtitle: "سریع، مدرن و مقیاس‌پذیر",
    // cta: { label: "شروع کنید", to: "/register", variant: "btn-primary" },
  },
  {
    src: "/images/slide-2.png",
    alt: "اسلاید ۲",
    // title: "تجربه کاربری یکدست",
    // subtitle: "ریسپانسیو + RTL",
  },
  {
    src: "/images/slide-4.png",
    alt: "اسلاید ۳",
    // title: "پشتیبانی و توسعه‌پذیری",
    // cta: { label: "اطلاعات بیشتر", to: "/about", variant: "btn-outline-light" },
  },
  {
    src: "/images/slide-5.png",
    alt: "اسلاید ۳",
    // title: "پشتیبانی و توسعه‌پذیری",
    // cta: { label: "اطلاعات بیشتر", to: "/about", variant: "btn-outline-light" },
  },
];

function Home() {
  return (
    <div className="home-page">
      <HeroSlider items={sliderItems} height={'auto'} intervalMs={5000} />
      
      <HeroBanner
        backgroundImage="/images/step-1.png"
        imageAlt="خدمات طراحی و توسعه نرم‌افزار"
        title="راهکارهای هوشمند برای رشد کسب‌وکار شما"
        description="از ایده تا اجرای کامل، در کنار شما هستیم تا محصولات دیجیتال حرفه‌ای و مقیاس‌پذیر بسازید."
        horizontalPosition="right"
        verticalPosition="center"
        aspectRatio="16 / 7"
        backgroundPosition="center"
        textColor="dark"
        buttons={[
          {
            label: 'مشاهده خدمات',
            href: '/services',
            variant: 'primary',
          },
          {
            label: 'تماس با ما',
            href: '/contact',
            variant: 'outline-primary',
          },
        ]}
      />
      <HeroBanner
        backgroundImage="/images/step-2.png"
        imageAlt="خدمات طراحی و توسعه نرم‌افزار"
        title="راهکارهای هوشمند برای رشد کسب‌وکار شما"
        description="از ایده تا اجرای کامل، در کنار شما هستیم تا محصولات دیجیتال حرفه‌ای و مقیاس‌پذیر بسازید."
        horizontalPosition="left"
        verticalPosition="center"
        aspectRatio="16 / 7"
        backgroundPosition="center"
        textColor="dark"
        buttons={[
          {
            label: 'مشاهده خدمات',
            href: '/services',
            variant: 'primary',
          },
          {
            label: 'تماس با ما',
            href: '/contact',
            variant: 'outline-primary',
          },
        ]}
      />
      <HeroBanner
        backgroundImage="/images/step-3.png"
        imageAlt="خدمات طراحی و توسعه نرم‌افزار"
        title="راهکارهای هوشمند برای رشد کسب‌وکار شما"
        description="از ایده تا اجرای کامل، در کنار شما هستیم تا محصولات دیجیتال حرفه‌ای و مقیاس‌پذیر بسازید."
        horizontalPosition="right"
        verticalPosition="center"
        aspectRatio="16 / 7"
        backgroundPosition="center"
        textColor="dark"
        buttons={[
          {
            label: 'مشاهده خدمات',
            href: '/services',
            variant: 'primary',
          },
          {
            label: 'تماس با ما',
            href: '/contact',
            variant: 'outline-primary',
          },
        ]}
      />

      <section className="py-5 bg-light row_section_1">
        <Container>
          <div className="text-center mb-2">
            <h2 className="fw-bold mb-2 row_section_1_title">دستاورد های ما</h2>
            <p className="text-muted mb-0">
              نتایج تلاش‌ها و همکاری‌های ما در مسیر نوآوری و توسعه
            </p>
          </div>
          <ItemsSlider items={sliderItems2} />
        </Container>
      </section>

      <section className="py-5 bg-light row_section_2">
        <Container>
          <div className="text-center mb-2">
            <h2 className="fw-bold mb-2 row_section_2_title">آنچه دیگران درباره ما میگویند</h2>
            <p className="text-muted mb-0">
              مصاحبه با کارآفرینان و همکاران موفق
            </p>
          </div>
          <ItemsSlider items={sliderItems3} />
        </Container>
      </section>
      
      <TrustedCompanies />
      
      <FAQSection />

    </div>
  );
}

export default Home;

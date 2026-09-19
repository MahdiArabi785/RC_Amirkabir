import MarqueeModule from 'react-fast-marquee';
import './TrustedCompanies.css'
const Marquee = (MarqueeModule as any).default ?? MarqueeModule;

interface CompanyLogo {
  id: number;
  name: string;
  logo: string;
}

// دیتای نمونه: ۷ لوگو برای ردیف اول
const rowOneLogos: CompanyLogo[] = [
  { id: 1, name: 'پارک علم و فناوری همدان', logo: 'https://hstp.ir/wp-content/uploads/elementor/thumbs/Untitled-2-3-r9nrz5lp4m4o47beipjuofxes2xhonhool42giigrg.jpg' },
  { id: 2, name: 'خدمات واقعیت افزوده ارس', logo: 'https://mr-vr.ir/wp-content/uploads/2025/09/3d-logo-scaled.webp#32655' },
  { id: 3, name: 'جهاد کشاورزی', logo: 'https://parsflag.com/wp-content/uploads/2023/11/%D9%88%D8%B2%D8%A7%D8%B1%D8%AA-%D8%AC%D9%87%D8%A7%D8%AF-%DA%A9%D8%B4%D8%A7%D9%88%D8%B1%D8%B2%DB%8C.png' },
  { id: 4, name: 'دانشگاه صنعتی اراک', logo: 'https://www.clipartmax.com/png/middle/337-3370388_file-arak-ut-svg-%D8%A2%D8%B1%D9%85-%D8%AF%D8%A7%D9%86%D8%B4%DA%AF%D8%A7%D9%87-%D8%B5%D9%86%D8%B9%D8%AA%DB%8C-%D8%A7%D8%B1%D8%A7%DA%A9.png' },
  { id: 5, name: 'دانشگاه آزاد اسلامی واحد اراک', logo: 'https://www.uniref.ir/media/lo/1158.webp' },
  { id: 6, name: 'مرکز آموزش عالی محلات', logo: 'https://www.uniref.ir/media/lo/2262.webp' },
  { id: 7, name: 'پارک علم و فناور مرکزی', logo: 'https://eitaa.com/download_0f89b9a7467c21ce2a0ea12de0cc218c?token=78da01b80047ff10000000107ee31dc87c2be4d87f1138d891cfe1fb8c8a99f6c8926c8be6c3a1d454a165c328236b67874e667a2d05bbfa91f3aa6fdb9e46779760e96b8dcd8a0380297934366fbecec28af0a1ddd1607688a25b74628b7bdc36118d1c87d069f76f7ea7349f8f2731916b81ba5bad73b59abe41796d072d66db054c9ed730d7786d604a124cb2091d1a4b1b45ea5198e337da55816e4267e6f79b7281ef879accb06836b858f300c2577c74ea41df6563369bf6896db31666d05c0e' },
  { id: 8, name: 'ماشین سازی اراک', logo: 'https://msa.ir/wp-content/uploads/2025/08/msa-mainlogo-1024x900.png' },
];

// دیتای نمونه: ۷ لوگو برای ردیف دوم
const rowTwoLogos: CompanyLogo[] = [
  { id: 9, name: 'پارک علم و فناوری همدان', logo: 'https://hstp.ir/wp-content/uploads/elementor/thumbs/Untitled-2-3-r9nrz5lp4m4o47beipjuofxes2xhonhool42giigrg.jpg' },
  { id: 10, name: 'خدمات واقعیت افزوده ارس', logo: 'https://mr-vr.ir/wp-content/uploads/2025/09/3d-logo-scaled.webp#32655' },
  { id: 11, name: 'جهاد کشاورزی', logo: 'https://parsflag.com/wp-content/uploads/2023/11/%D9%88%D8%B2%D8%A7%D8%B1%D8%AA-%D8%AC%D9%87%D8%A7%D8%AF-%DA%A9%D8%B4%D8%A7%D9%88%D8%B1%D8%B2%DB%8C.png' },
  { id: 12, name: 'دانشگاه صنعتی اراک', logo: 'https://www.clipartmax.com/png/middle/337-3370388_file-arak-ut-svg-%D8%A2%D8%B1%D9%85-%D8%AF%D8%A7%D9%86%D8%B4%DA%AF%D8%A7%D9%87-%D8%B5%D9%86%D8%B9%D8%AA%DB%8C-%D8%A7%D8%B1%D8%A7%DA%A9.png' },
  { id: 13, name: 'دانشگاه آزاد اسلامی واحد اراک', logo: 'https://www.uniref.ir/media/lo/1158.webp' },
  { id: 14, name: 'مرکز آموزش عالی محلات', logo: 'https://www.uniref.ir/media/lo/2262.webp' },
  { id: 15, name: 'پارک علم و فناور مرکزی', logo: 'https://eitaa.com/download_0f89b9a7467c21ce2a0ea12de0cc218c?token=78da01b80047ff10000000107ee31dc87c2be4d87f1138d891cfe1fb8c8a99f6c8926c8be6c3a1d454a165c328236b67874e667a2d05bbfa91f3aa6fdb9e46779760e96b8dcd8a0380297934366fbecec28af0a1ddd1607688a25b74628b7bdc36118d1c87d069f76f7ea7349f8f2731916b81ba5bad73b59abe41796d072d66db054c9ed730d7786d604a124cb2091d1a4b1b45ea5198e337da55816e4267e6f79b7281ef879accb06836b858f300c2577c74ea41df6563369bf6896db31666d05c0e' },
  { id: 16, name: 'ماشین سازی اراک', logo: 'https://msa.ir/wp-content/uploads/2025/08/msa-mainlogo-1024x900.png' },
];

interface TrustedCompaniesProps {
  title?: string;
  subtitle?: string;
  className?: string;
}

export default function TrustedCompanies({
  title = 'مورد اعتماد سازمان‌ها و شرکت‌های پیشرو',
  subtitle = 'افتخار همکاری با بیش از ۷ مجموعه معتبر در سراسر کشور',
  className = '',
}: TrustedCompaniesProps) {
  return (
    <section className={`trusted-companies-section py-5 ${className}`}>
      <div className="container text-center mb-4">
        {title && <h2 className="fw-bold fs-3 mb-2">{title}</h2>}
        {subtitle && <p className="text-muted fs-6 mb-0">{subtitle}</p>}
      </div>

      <div className="marquee-container d-flex flex-column">
        {/* ردیف اول: حرکت به چپ */}
        <Marquee
          direction="left"
          speed={40}
          autoFill={true}
          pauseOnHover={true}
          gradient={true}
          gradientColor="#ffffff"
          gradientWidth={100}
          scrolldelay='5'
        >
          {rowOneLogos.map((item) => (
            <div key={item.id} className="marquee-logo-card">
              <img src={item.logo} alt={item.name} title={item.name} loading="lazy" />
            </div>
          ))}
        </Marquee>

        {/* ردیف دوم: حرکت به راست */}
        <Marquee
          direction="right"
          speed={40}
          autoFill={true}
          pauseOnHover={true}
          gradient={true}
          gradientColor="#ffffff"
          gradientWidth={100}
        >
          {rowTwoLogos.map((item) => (
            <div key={item.id} className="marquee-logo-card">
              <img src={item.logo} alt={item.name} title={item.name} loading="lazy" />
            </div>
          ))}
        </Marquee>
      </div>
    </section>
  );
}

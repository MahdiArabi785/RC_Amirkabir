import Accordion from 'react-bootstrap/Accordion';
import { FiHelpCircle } from 'react-icons/fi';

type FAQItem = {
  question: string;
  answer: string;
};

const faqItems: FAQItem[] = [
  {
    question: 'چگونه می‌توانم در سایت ثبت‌نام کنم؟',
    answer:
      'برای ثبت‌نام، از منوی اصلی روی گزینه ثبت‌نام کلیک کنید و اطلاعات موردنیاز را وارد نمایید.',
  },
  {
    question: 'آیا امکان پیگیری درخواست وجود دارد؟',
    answer:
      'بله، پس از ورود به حساب کاربری می‌توانید وضعیت درخواست‌ها و سفارش‌های خود را مشاهده و پیگیری کنید.',
  },
  {
    question: 'چگونه با پشتیبانی تماس بگیرم؟',
    answer:
      'می‌توانید از طریق فرم تماس با ما یا شماره‌های درج‌شده در صفحه تماس، با تیم پشتیبانی ارتباط برقرار کنید.',
  },
  {
    question: 'آیا اطلاعات کاربران محفوظ می‌ماند؟',
    answer:
      'بله، اطلاعات کاربران مطابق با سیاست حفظ حریم خصوصی سایت نگهداری و محافظت می‌شود.',
  },
];

function FAQSection() {
  return (
    <section className="faq-section py-5" aria-labelledby="faq-title">
      <div className="container">
        <div className="row align-items-center g-5">
          {/* تصویر؛ در موبایل بالای سوالات قرار می‌گیرد */}
          <div className="col-12 col-lg-5 order-1 order-lg-2">
            <img
              src="/images/question_mark.png"
              alt="سوالات پرتکرار"
              className="faq-image img-fluid"
            />
          </div>

          {/* سوالات */}
          <div className="col-12 col-lg-7 order-2 order-lg-1">
            <div className="faq-content">
              <span className="faq-subtitle">راهنمای کاربران</span>

              <h2 id="faq-title" className="faq-title">
                سوالات پرتکرار
              </h2>

              <p className="faq-intro">
                پاسخ سوالات متداول کاربران را در این بخش مشاهده کنید.
              </p>

              <Accordion defaultActiveKey="0">
                {faqItems.map((item, index) => (
                  <Accordion.Item eventKey={String(index)} key={item.question}>
                    <Accordion.Header>{item.question}</Accordion.Header>

                    <Accordion.Body>{item.answer}</Accordion.Body>
                  </Accordion.Item>
                ))}
              </Accordion>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default FAQSection;

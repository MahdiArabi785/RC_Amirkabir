import { Container, Row, Col, Form, Button } from 'react-bootstrap';
import {
  FaInstagram,
  FaTelegram,
  FaLinkedin,
  FaTwitter,
} from 'react-icons/fa';

function Footer() {
  return (
    <footer className="site-footer bg-dark text-light mt-5">
      <Container>
        <Row className="py-5 g-4">
          {/* معرفی */}
          <Col lg={4} md={6}>
            <h5 className="fw-bold mb-3">مرکز تحقیقات امیرکبیر</h5>

            <p className="text-light-emphasis">
              ارائه‌دهنده خدمات حرفه‌ای با هدف ایجاد تجربه‌ای ساده،
              سریع و قابل اعتماد برای کاربران.
            </p>

            <div className="d-flex gap-3 mt-4">
              <a href="#" className="social-link" aria-label="Instagram">
                <FaInstagram />
              </a>

              <a href="#" className="social-link" aria-label="Telegram">
                <FaTelegram />
              </a>

              <a href="#" className="social-link" aria-label="LinkedIn">
                <FaLinkedin />
              </a>

              <a href="#" className="social-link" aria-label="Twitter">
                <FaTwitter />
              </a>
            </div>
          </Col>

          {/* لینک‌های سریع */}
          <Col lg={2} md={6}>
            <h6 className="fw-bold mb-3">دسترسی سریع</h6>

            <ul className="list-unstyled footer-links">
              <li>
                <a href="/">خانه</a>
              </li>

              <li>
                <a href="/about">درباره ما</a>
              </li>

              <li>
                <a href="/services">خدمات</a>
              </li>

              <li>
                <a href="/contact">تماس با ما</a>
              </li>
            </ul>
          </Col>

          {/* پشتیبانی */}
          <Col lg={2} md={6}>
            <h6 className="fw-bold mb-3">پشتیبانی</h6>

            <ul className="list-unstyled footer-links">
              <li>
                <a href="/faq">سوالات متداول</a>
              </li>

              <li>
                <a href="/terms">قوانین و مقررات</a>
              </li>

              <li>
                <a href="/privacy">حریم خصوصی</a>
              </li>

              <li>
                <a href="/support">پشتیبانی</a>
              </li>
            </ul>
          </Col>

          {/* خبرنامه */}
          <Col lg={4} md={6}>
            <h6 className="fw-bold mb-3">عضویت در خبرنامه</h6>

            <p className="text-light-emphasis">
              برای دریافت جدیدترین اخبار، ایمیل خود را وارد کنید.
            </p>

            <Form className="d-flex gap-2">
              <Form.Control
                type="email"
                placeholder="ایمیل شما"
                aria-label="ایمیل شما"
              />

              <Button variant="primary" type="submit">
                عضویت
              </Button>
            </Form>
          </Col>
        </Row>

        <hr className="border-secondary" />

        <div className="d-flex flex-column flex-md-row justify-content-between align-items-center py-3 gap-2">
          <small className="text-light-emphasis">
            © ۱۴۰۵ تمامی حقوق محفوظ است.
          </small>

          <small className="text-light-emphasis">
            طراحی و توسعه با React و TypeScript
          </small>
        </div>
      </Container>
    </footer>
  );
}

export default Footer;

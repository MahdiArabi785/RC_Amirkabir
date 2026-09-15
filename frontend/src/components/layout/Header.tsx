import { Container, Nav, Navbar, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';

function Header() {
  return (
    <Navbar
      expand="lg"
      bg="white"
      className="site-header shadow-sm"
      sticky="top"
    >
      <Container>
        {/* لوگو */}
        <Navbar.Brand as={Link} to="/" className="fw-bold text-primary">
          <img src='images/logo_small.png' width={120}></img>
        </Navbar.Brand>

        {/* دکمه منوی موبایل */}
        <Navbar.Toggle aria-controls="main-navbar" />

        <Navbar.Collapse id="main-navbar">
          {/* منوی ساده */}
          <Nav className="mx-auto my-3 my-lg-2 fw-bold gap-4">
            <Nav.Link as={Link} to="/">
              خانه
            </Nav.Link>

            <Nav.Link as={Link} to="/tutorials">
              آموزش ها
            </Nav.Link>

            <Nav.Link as={Link} to="/documents">
              مستندات
            </Nav.Link>

            <Nav.Link as={Link} to="/news">
             اخبار و فراخوان‌ها
            </Nav.Link>

            <Nav.Link as={Link} to="/about">
              درباره ما
            </Nav.Link>
          </Nav>

          {/* دکمه‌های ورود و ثبت‌نام */}
          <div className="d-flex gap-2">
            <Link
              to="/login"
              className="btn btn-outline-primary"
            >
              ورود
            </Link>

            <Link
              to="/register"
              className="btn btn-primary"
            >
              ثبت‌نام
            </Link>
          </div>
          
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default Header;

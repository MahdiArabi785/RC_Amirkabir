import { Routes, Route } from 'react-router-dom';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import Home from './pages/Home';
import TutorialsPage from './pages/Tutorials/TutorialsPage';
import DocumentsPage from "./pages/Documents/DocumentsPage";
import NewsPage from "./pages/News/NewsPage";
import NewsDetailsPage from "./pages/News/NewsDetailsPage";


function App() {
  return (
    <div className="d-flex flex-column min-vh-100 bg-light">
      {/* سربرگ */}
      <Header />

      {/* محتوای اصلی */}
      <main className="flex-grow-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<div className="container py-5">صفحه درباره ما</div>} />
          <Route path="/tutorials" element={<TutorialsPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/news" element={<NewsPage />} />
          <Route path="/news/:slug" element={<NewsDetailsPage />} />
          <Route path="/services" element={<div className="container py-5">صفحه خدمات</div>} />
          <Route path="/contact" element={
            <div className="container py-5">
              صفحه تماس با ما
            </div>
          } />
          <Route path="/login" element={<div className="container py-5">صفحه ورود</div>} />
          <Route path="/register" element={<div className="container py-5">صفحه ثبت‌نام</div>} />
        </Routes>
      </main>

      {/* پاورقی */}
      <Footer />
    </div>
  );
}

export default App;

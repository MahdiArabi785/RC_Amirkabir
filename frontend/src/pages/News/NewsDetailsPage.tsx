// src/pages/News/NewsDetailsPage.tsx

import { Link, useParams } from "react-router-dom";
import { news } from "../../data/News";
import "./NewsDetailsPage.css";

const categoryLabels = {
  news: "خبر",
  event: "رویداد",
  announcement: "اطلاعیه",
  product: "محصول و خدمات",
  education: "آموزش",
  report: "گزارش",
} as const;

const formatPersianDate = (date: string): string => {
  return new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(`${date}T00:00:00`));
};

const NewsDetailsPage = () => {
  const { slug } = useParams<{ slug: string }>();

  const currentNews = news.find((item) => item.slug === slug);

  if (!currentNews) {
    return (
      <main className="news-details-page" dir="rtl">
        <div className="container">
          <section className="news-details-not-found">
            <h1>خبر پیدا نشد</h1>

            <p>
              خبر موردنظر وجود ندارد یا ممکن است حذف شده باشد.
            </p>

            <Link to="/news" className="btn btn-primary">
              بازگشت به اخبار
            </Link>
          </section>
        </div>
      </main>
    );
  }

  return (
    <main className="news-details-page" dir="rtl">
      <div className="container">
        <article className="news-details-article">
          <Link to="/news" className="news-details-back-link">
            ← بازگشت به اخبار و رویدادها
          </Link>

          <div className="news-details-header">
            <span className="news-details-category">
              {categoryLabels[currentNews.category]}
            </span>

            <h1 className="news-details-title">
              {currentNews.title}
            </h1>

            <div className="news-details-meta">
              <span>
                تاریخ انتشار:{" "}
                {formatPersianDate(currentNews.publishDate)}
              </span>

              {currentNews.author && (
                <span>منتشرکننده: {currentNews.author}</span>
              )}

              {currentNews.readingTime && (
                <span>
                  زمان مطالعه: {currentNews.readingTime} دقیقه
                </span>
              )}
            </div>
          </div>

          <img
            src={currentNews.imageUrl}
            alt={currentNews.imageAlt || currentNews.title}
            className="news-details-image"
          />

          <div className="news-details-content">
            {currentNews.content
              .split("\n")
              .map((paragraph, index) => (
                <p key={index}>{paragraph}</p>
              ))}
          </div>

          {currentNews.tags && currentNews.tags.length > 0 && (
            <div className="news-details-tags">
              <strong>برچسب‌ها:</strong>

              {currentNews.tags.map((tag) => (
                <span key={tag} className="news-details-tag">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </article>
      </div>
    </main>
  );
};

export default NewsDetailsPage;

// src/pages/News/NewsPage.tsx

import {
  useEffect,
  useMemo,
  useState,
  type ChangeEvent,
} from "react";
import { Link } from "react-router-dom";

import { news } from "../../data/News";
import type {
  NewsCategory,
  NewsItem,
} from "../../types/News";

import "./NewsPage.css";

const ITEMS_PER_PAGE = 6;

type DateFilter = "all" | "week" | "month" | "year";

const categoryLabels: Record<NewsCategory, string> = {
  all: "همه انواع",
  news: "خبر",
  event: "رویداد",
  announcement: "اطلاعیه",
  product: "محصول و خدمات",
  education: "آموزش",
  report: "گزارش",
};

const dateFilterLabels: Record<DateFilter, string> = {
  all: "همه تاریخ‌ها",
  week: "هفته اخیر",
  month: "ماه اخیر",
  year: "سال اخیر",
};

/**
 * نرمال‌سازی متن فارسی برای جستجوی بهتر
 *
 * مواردی مانند:
 * ي -> ی
 * ى -> ی
 * ك -> ک
 * نیم‌فاصله -> فاصله معمولی
 */
const normalizePersian = (value: string): string => {
  return value
    .trim()
    .toLocaleLowerCase("fa-IR")
    .replace(/ي/g, "ی")
    .replace(/ى/g, "ی")
    .replace(/ك/g, "ک")
    .replace(/\u200c/g, " ")
    .replace(/\s+/g, " ");
};

/**
 * تبدیل تاریخ میلادی به تاریخ فارسی قابل نمایش
 */
const formatPersianDate = (date: string): string => {
  const parsedDate = new Date(`${date}T00:00:00`);

  if (Number.isNaN(parsedDate.getTime())) {
    return date;
  }

  return new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(parsedDate);
};

/**
 * محاسبه تاریخ شروع بازه فیلتر
 */
const getDateLimit = (filter: DateFilter): Date | null => {
  if (filter === "all") {
    return null;
  }

  const limitDate = new Date();

  switch (filter) {
    case "week":
      limitDate.setDate(limitDate.getDate() - 7);
      break;

    case "month":
      limitDate.setMonth(limitDate.getMonth() - 1);
      break;

    case "year":
      limitDate.setFullYear(limitDate.getFullYear() - 1);
      break;
  }

  limitDate.setHours(0, 0, 0, 0);

  return limitDate;
};

/**
 * بررسی قرار داشتن خبر در بازه زمانی انتخاب‌شده
 */
const isDateInRange = (
  publishDate: string,
  selectedDateFilter: DateFilter
): boolean => {
  const dateLimit = getDateLimit(selectedDateFilter);

  if (!dateLimit) {
    return true;
  }

  const itemDate = new Date(`${publishDate}T00:00:00`);

  if (Number.isNaN(itemDate.getTime())) {
    return false;
  }

  itemDate.setHours(0, 0, 0, 0);

  return itemDate >= dateLimit;
};

interface NewsListItemProps {
  item: NewsItem;
}

const NewsListItem = ({ item }: NewsListItemProps) => {
  return (
    <article className="news-list-item">
      <Link
        to={`/news/${item.slug}`}
        className="news-list-item-link"
        aria-label={`مشاهده خبر ${item.title}`}
      >
        {/* در حالت RTL تصویر در سمت راست نمایش داده می‌شود */}
        <div className="news-list-item-image-wrapper">
          <img
            src={item.imageUrl}
            alt={item.imageAlt || item.title}
            className="news-list-item-image"
            loading="lazy"
          />
        </div>

        <div className="news-list-item-content">
          <div className="news-list-item-meta">
            <span className="news-list-item-category">
              {categoryLabels[item.category]}
            </span>

            <span className="news-list-item-date">
              {formatPersianDate(item.publishDate)}
            </span>

            {item.readingTime && (
              <span className="news-list-item-reading-time">
                {item.readingTime.toLocaleString("fa-IR")} دقیقه مطالعه
              </span>
            )}
          </div>

          <h2 className="news-list-item-title">
            {item.title}
          </h2>

          <p className="news-list-item-summary">
            {item.summary}
          </p>

          <span className="news-list-item-more">
            مشاهده جزئیات
            <span aria-hidden="true">←</span>
          </span>
        </div>
      </Link>
    </article>
  );
};

const NewsPage = () => {
  const [searchTerm, setSearchTerm] = useState("");

  const [selectedCategory, setSelectedCategory] =
    useState<NewsCategory>("all");

  const [selectedDateFilter, setSelectedDateFilter] =
    useState<DateFilter>("all");

  const [currentPage, setCurrentPage] = useState(1);

  /**
   * فیلتر و مرتب‌سازی اخبار
   */
  const filteredNews = useMemo(() => {
    const normalizedSearchTerm = normalizePersian(searchTerm);

    return [...news]
      .filter((item) => {
        const matchesCategory =
          selectedCategory === "all" ||
          item.category === selectedCategory;

        const searchableText = normalizePersian(
          [
            item.title,
            item.summary,
            item.content,
            categoryLabels[item.category],
            ...(item.tags || []),
          ].join(" ")
        );

        const matchesSearch =
          normalizedSearchTerm.length === 0 ||
          searchableText.includes(normalizedSearchTerm);

        const matchesDate = isDateInRange(
          item.publishDate,
          selectedDateFilter
        );

        return (
          matchesCategory &&
          matchesSearch &&
          matchesDate
        );
      })
      .sort((firstItem, secondItem) => {
        const firstDate = new Date(
          `${firstItem.publishDate}T00:00:00`
        ).getTime();

        const secondDate = new Date(
          `${secondItem.publishDate}T00:00:00`
        ).getTime();

        return secondDate - firstDate;
      });
  }, [
    searchTerm,
    selectedCategory,
    selectedDateFilter,
  ]);

  /**
   * تعداد کل صفحات
   */
  const totalPages = Math.max(
    1,
    Math.ceil(filteredNews.length / ITEMS_PER_PAGE)
  );

  /**
   * اخبار مربوط به صفحه فعلی
   */
  const paginatedNews = useMemo(() => {
    const startIndex =
      (currentPage - 1) * ITEMS_PER_PAGE;

    return filteredNews.slice(
      startIndex,
      startIndex + ITEMS_PER_PAGE
    );
  }, [filteredNews, currentPage]);

  /**
   * هنگام تغییر هر فیلتر، کاربر به صفحه اول برمی‌گردد
   */
  useEffect(() => {
    setCurrentPage(1);
  }, [
    searchTerm,
    selectedCategory,
    selectedDateFilter,
  ]);

  /**
   * اگر بعد از فیلتر تعداد صفحات کمتر شود،
   * شماره صفحه فعلی اصلاح می‌شود.
   */
  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  /**
   * حذف تمام فیلترها
   */
  const resetFilters = () => {
    setSearchTerm("");
    setSelectedCategory("all");
    setSelectedDateFilter("all");
    setCurrentPage(1);
  };

  /**
   * تغییر عبارت جستجو
   */
  const handleSearchChange = (
    event: ChangeEvent<HTMLInputElement>
  ) => {
    setSearchTerm(event.target.value);
  };

  /**
   * تغییر دسته‌بندی
   */
  const handleCategoryChange = (
    event: ChangeEvent<HTMLSelectElement>
  ) => {
    setSelectedCategory(
      event.target.value as NewsCategory
    );
  };

  /**
   * تغییر بازه زمانی
   */
  const handleDateFilterChange = (
    event: ChangeEvent<HTMLSelectElement>
  ) => {
    setSelectedDateFilter(
      event.target.value as DateFilter
    );
  };

  const hasActiveFilters =
    searchTerm.trim().length > 0 ||
    selectedCategory !== "all" ||
    selectedDateFilter !== "all";

  const firstDisplayedItem =
    filteredNews.length === 0
      ? 0
      : (currentPage - 1) * ITEMS_PER_PAGE + 1;

  const lastDisplayedItem =
    Math.min(
      currentPage * ITEMS_PER_PAGE,
      filteredNews.length
    );

  return (
    <main className="news-page" dir="rtl">
      <div className="container">
        {/* عنوان صفحه */}
        <header className="news-page-header">
          <h1 className="news-page-title">
            اخبار و رویدادها
          </h1>

          <p className="news-page-subtitle">
            آخرین اخبار، اطلاعیه‌ها و رویدادهای شرکت اطلاعیه‌ها و رویدادهای شرکت
          </p>
        </header>

        {/* فیلترها */}
        <section
          className="news-filters"
          aria-label="فیلتر اخبار و رویدادها"
        >
          <div className="row g-3">
            {/* جستجو */}
            <div className="col-12 col-lg-6">
              <label
                htmlFor="news-search"
                className="news-filter-label"
              >
                جستجو در اخبار
              </label>

              <div className="news-search-wrapper">
                <span
                  className="news-search-icon"
                  aria-hidden="true"
                >
                  ⌕
                </span>

                <input
                  id="news-search"
                  type="search"
                  className="news-search-input"
                  placeholder="عنوان، توضیحات یا برچسب خبر را جستجو کنید..."
                  value={searchTerm}
                  onChange={handleSearchChange}
                />
              </div>
            </div>

            {/* فیلتر نوع محتوا */}
            <div className="col-12 col-md-6 col-lg-3">
              <label
                htmlFor="news-category"
                className="news-filter-label"
              >
                نوع محتوا
              </label>

              <select
                id="news-category"
                className="form-select news-category-select"
                value={selectedCategory}
                onChange={handleCategoryChange}
              >
                {Object.entries(categoryLabels).map(
                  ([value, label]) => (
                    <option
                      key={value}
                      value={value}
                    >
                      {label}
                    </option>
                  )
                )}
              </select>
            </div>

            {/* فیلتر تاریخ */}
            <div className="col-12 col-md-6 col-lg-3">
              <label
                htmlFor="news-date"
                className="news-filter-label"
              >
                بازه زمانی
              </label>

              <select
                id="news-date"
                className="form-select news-date-select"
                value={selectedDateFilter}
                onChange={handleDateFilterChange}
              >
                {Object.entries(dateFilterLabels).map(
                  ([value, label]) => (
                    <option
                      key={value}
                      value={value}
                    >
                      {label}
                    </option>
                  )
                )}
              </select>
            </div>
          </div>
        </section>

        {/* اطلاعات نتایج */}
        <div className="news-results-info">
          <span>
            نمایش{" "}
            {firstDisplayedItem.toLocaleString("fa-IR")} تا{" "}
            {lastDisplayedItem.toLocaleString("fa-IR")} از{" "}
            {filteredNews.length.toLocaleString("fa-IR")} خبر
          </span>

          {totalPages > 1 && (
            <span>
              صفحه{" "}
              {currentPage.toLocaleString("fa-IR")} از{" "}
              {totalPages.toLocaleString("fa-IR")}
            </span>
          )}

          {hasActiveFilters && (
            <button
              type="button"
              className="news-reset-button"
              onClick={resetFilters}
            >
              حذف فیلترها
            </button>
          )}
        </div>

        {/* فهرست اخبار */}
        {paginatedNews.length > 0 ? (
          <section
            className="news-list"
            aria-label="فهرست اخبار"
          >
            {paginatedNews.map((item) => (
              <NewsListItem
                key={item.id}
                item={item}
              />
            ))}
          </section>
        ) : (
          <section className="news-empty-state">
            <div
              className="news-empty-icon"
              aria-hidden="true"
            >
              📰
            </div>

            <h2>خبری پیدا نشد</h2>

            <p>
              با عبارت جستجو یا فیلترهای انتخاب‌شده
              نتیجه‌ای پیدا نشد.
            </p>

            <button
              type="button"
              className="btn btn-primary"
              onClick={resetFilters}
            >
              نمایش همه اخبار
            </button>
          </section>
        )}

        {/* صفحه‌بندی */}
        {totalPages > 1 && (
          <nav
            className="news-pagination"
            aria-label="صفحه‌بندی اخبار"
          >
            {/* صفحه قبلی */}
            <button
              type="button"
              className="news-pagination-button"
              disabled={currentPage === 1}
              aria-label="رفتن به صفحه قبلی"
              onClick={() => {
                setCurrentPage((page) =>
                  Math.max(1, page - 1)
                );
              }}
            >
              قبلی
            </button>

            {/* شماره صفحات */}
            <div className="news-pagination-pages">
              {Array.from(
                { length: totalPages },
                (_, index) => index + 1
              ).map((page) => (
                <button
                  key={page}
                  type="button"
                  className={`news-pagination-page ${
                    currentPage === page
                      ? "active"
                      : ""
                  }`}
                  aria-label={`رفتن به صفحه ${page}`}
                  aria-current={
                    currentPage === page
                      ? "page"
                      : undefined
                  }
                  onClick={() => {
                    setCurrentPage(page);
                  }}
                >
                  {page.toLocaleString("fa-IR")}
                </button>
              ))}
            </div>

            {/* صفحه بعدی */}
            <button
              type="button"
              className="news-pagination-button"
              disabled={currentPage === totalPages}
              aria-label="رفتن به صفحه بعدی"
              onClick={() => {
                setCurrentPage((page) =>
                  Math.min(totalPages, page + 1)
                );
              }}
            >
              بعدی
            </button>
          </nav>
        )}
      </div>
    </main>
  );
};

export default NewsPage;

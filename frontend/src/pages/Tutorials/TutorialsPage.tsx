import React, { useEffect, useMemo, useState } from 'react';

import TutorialCard from '../../components/TutorialCard/TutorialCard';
import { tutorials } from '../../data/tutorials';
import type { Tutorial } from '../../types/tutorial';

import './TutorialsPage.css';

const ITEMS_PER_PAGE = 8;

export default function TutorialsPage() {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [selectedTutorial, setSelectedTutorial] = useState<Tutorial | null>(null);

  /**
   * استخراج دسته‌بندی‌های یکتا برای منوی کشویی فیلتر
   */
  const tutorialTypes = useMemo(() => {
    return Array.from(new Set(tutorials.map((tutorial) => tutorial.type)));
  }, []);

  /**
   * فیلتر آموزش‌ها بر اساس عنوان، توضیحات و دسته‌بندی
   */
  const filteredTutorials = useMemo(() => {
    const normalizedSearchTerm = searchTerm.trim().toLowerCase();

    return tutorials.filter((tutorial) => {
      const title = tutorial.title.toLowerCase();
      const description = tutorial.description.toLowerCase();

      const matchesSearch =
        normalizedSearchTerm === '' ||
        title.includes(normalizedSearchTerm) ||
        description.includes(normalizedSearchTerm);

      const matchesType =
        selectedType === 'all' || tutorial.type === selectedType;

      return matchesSearch && matchesType;
    });
  }, [searchTerm, selectedType]);

  /**
   * محاسبه کل صفحات بر اساس دیتای فیلتر شده
   */
  const totalPages = Math.ceil(filteredTutorials.length / ITEMS_PER_PAGE) || 1;

  // اطمینان از اینکه شماره صفحه در بازه مجاز قرار دارد
  const safeCurrentPage = Math.min(Math.max(currentPage, 1), totalPages);

  /**
   * آموزش‌های صفحه‌ی فعلی
   */
  const paginatedTutorials = useMemo(() => {
    const startIndex = (safeCurrentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;

    return filteredTutorials.slice(startIndex, endIndex);
  }, [filteredTutorials, safeCurrentPage]);

  /**
   * بستن Modal با کلید Escape
   */
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSelectedTutorial(null);
      }
    };

    if (selectedTutorial) {
      document.addEventListener('keydown', handleEscape);
      document.body.classList.add('tutorial-modal-open');
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.classList.remove('tutorial-modal-open');
    };
  }, [selectedTutorial]);

  /**
   * ساخت لیست شماره صفحات
   */
  const pageNumbers = useMemo(() => {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }, [totalPages]);

  /**
   * تغییر صفحه و اسکرول نرم به بالای صفحه
   */
  const handlePageChange = (page: number) => {
    if (page < 1 || page > totalPages || page === safeCurrentPage) {
      return;
    }

    setCurrentPage(page);

    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  };

  /**
   * هندلرهای تغییر جستجو و فیلتر همراه با ریست صفحه به 1
   */
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setCurrentPage(1);
  };

  const handleTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedType(event.target.value);
    setCurrentPage(1);
  };

  /**
   * پاک کردن جستجو و فیلترها
   */
  const handleResetFilters = () => {
    setSearchTerm('');
    setSelectedType('all');
    setCurrentPage(1);
  };

  /**
   * بستن Modal
   */
  const handleCloseModal = () => {
    setSelectedTutorial(null);
  };

  /**
   * جلوگیری از انتشار رویداد کلیک داخل پنجره مدال به لایه پس‌زمینه
   */
  const handleModalContentClick = (event: React.MouseEvent<HTMLDivElement>) => {
    event.stopPropagation();
  };

  return (
    <main className="tutorials-page" dir="rtl">
      <div className="container">
        {/* Header صفحه */}
        <header className="tutorials-page-header">
          <h1 className="tutorials-page-title">آموزش‌ها</h1>
          <p className="tutorials-page-subtitle">
            مجموعه‌ای از آموزش‌های کاربردی برای یادگیری و توسعه مهارت‌های شما
          </p>
        </header>

        {/* بخش جستجو و فیلتر */}
        <section
          className="tutorials-filters"
          aria-label="جستجو و فیلتر آموزش‌ها"
        >
          <div className="row g-3 align-items-end">
            <div className="col-12 col-md-7">
              <label
                htmlFor="tutorial-search"
                className="form-label tutorials-filter-label"
              >
                جستجوی آموزش
              </label>

              <div className="tutorial-search-wrapper">
                <span className="tutorial-search-icon" aria-hidden="true">
                  🔍
                </span>

                <input
                  id="tutorial-search"
                  type="search"
                  className="form-control tutorial-search-input"
                  placeholder="عنوان یا توضیح آموزش را جستجو کنید..."
                  value={searchTerm}
                  onChange={handleSearchChange}
                />
              </div>
            </div>

            <div className="col-12 col-md-5">
              <label
                htmlFor="tutorial-type"
                className="form-label tutorials-filter-label"
              >
                نوع آموزش
              </label>

              <select
                id="tutorial-type"
                className="form-select"
                value={selectedType}
                onChange={handleTypeChange}
              >
                <option value="all">همه آموزش‌ها</option>
                {tutorialTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </section>

        {/* اطلاعات نتایج */}
        <div className="tutorials-results-info">
          <span>
            {filteredTutorials.length === 0
              ? 'نتیجه‌ای پیدا نشد'
              : `${filteredTutorials.length} آموزش پیدا شد`}
          </span>

          {(searchTerm.trim() !== '' || selectedType !== 'all') && (
            <button
              type="button"
              className="tutorials-reset-button"
              onClick={handleResetFilters}
            >
              حذف فیلترها
            </button>
          )}
        </div>

        {/* لیست آموزش‌ها */}
        {paginatedTutorials.length > 0 ? (
          <section className="tutorials-list" aria-label="فهرست آموزش‌ها">
            <div className="row g-4">
              {paginatedTutorials.map((tutorial) => (
                <div className="col-6 col-lg-3" key={tutorial.id}>
                  <TutorialCard
                    tutorial={tutorial}
                    onVideoClick={setSelectedTutorial}
                  />
                </div>
              ))}
            </div>
          </section>
        ) : (
          <section className="tutorials-empty-state">
            <div className="tutorials-empty-icon" aria-hidden="true">
              🔎
            </div>
            <h2>آموزشی پیدا نشد</h2>
            <p>عبارت جستجو یا فیلتر انتخاب‌شده نتیجه‌ای نداشت.</p>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleResetFilters}
            >
              نمایش همه آموزش‌ها
            </button>
          </section>
        )}

        {/* صفحه‌بندی */}
        {totalPages > 1 && (
          <nav
            className="tutorials-pagination"
            aria-label="صفحه‌بندی آموزش‌ها"
          >
            <button
              type="button"
              className="tutorial-pagination-button"
              disabled={safeCurrentPage === 1}
              onClick={() => handlePageChange(safeCurrentPage - 1)}
              aria-label="صفحه قبلی"
            >
              قبلی
            </button>

            <div className="tutorial-pagination-pages">
              {pageNumbers.map((page) => (
                <button
                  type="button"
                  key={page}
                  className={`tutorial-pagination-page ${
                    safeCurrentPage === page ? 'active' : ''
                  }`}
                  onClick={() => handlePageChange(page)}
                  aria-current={safeCurrentPage === page ? 'page' : undefined}
                >
                  {page}
                </button>
              ))}
            </div>

            <button
              type="button"
              className="tutorial-pagination-button"
              disabled={safeCurrentPage === totalPages}
              onClick={() => handlePageChange(safeCurrentPage + 1)}
              aria-label="صفحه بعدی"
            >
              بعدی
            </button>
          </nav>
        )}
      </div>

      {/* Modal ویدئو */}
      {selectedTutorial && (
        <div
          className="tutorial-video-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="tutorial-modal-title"
          onClick={handleCloseModal}
        >
          <div
            className="tutorial-video-modal-content"
            onClick={handleModalContentClick}
          >
            <div className="tutorial-video-modal-header">
              <h2
                id="tutorial-modal-title"
                className="tutorial-video-modal-title"
              >
                {selectedTutorial.title}
              </h2>

              <button
                type="button"
                className="tutorial-video-modal-close"
                onClick={handleCloseModal}
                aria-label="بستن ویدئو"
              >
                ×
              </button>
            </div>

            <div className="tutorial-video-wrapper">
              <iframe
                src={selectedTutorial.aparatUrl}
                title={selectedTutorial.title}
                frameBorder="0"
                allow="autoplay; fullscreen"
                allowFullScreen
              />
            </div>

            <div className="tutorial-video-modal-description">
              <span className="tutorial-card-type">
                {selectedTutorial.type}
              </span>
              <p>{selectedTutorial.description}</p>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

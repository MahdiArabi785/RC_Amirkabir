import { useEffect, useMemo, useState } from "react";
import { documents } from "../../data/documents";
import type {
  DocumentCategory,
  DocumentItem,
} from "../../types/document";
import "./DocumentsPage.css";

const ITEMS_PER_PAGE = 8;

const categoryLabels: Record<DocumentCategory | "all", string> = {
  all: "همه دسته‌ها",
  guide: "راهنمای کاربری",
  catalog: "کاتالوگ",
  form: "فرم",
  standard: "استاندارد",
  report: "گزارش",
  other: "سایر",
};

const formatIcons: Record<string, string> = {
  PDF: "PDF",
  DOC: "DOC",
  DOCX: "DOCX",
  XLS: "XLS",
  XLSX: "XLSX",
  ZIP: "ZIP",
  RAR: "RAR",
  PPT: "PPT",
  PPTX: "PPTX",
};

const getFileExtension = (file: DocumentItem): string => {
  const extension = file.fileFormat?.toUpperCase();

  if (extension && formatIcons[extension]) {
    return formatIcons[extension];
  }

  return extension || "FILE";
};

const formatDownloadCount = (downloads?: number): string => {
  if (!downloads) {
    return "۰ دانلود";
  }

  return `${downloads.toLocaleString("fa-IR")} دانلود`;
};

interface DocumentIconProps {
  format: string;
}

const DocumentIcon = ({ format }: DocumentIconProps) => {
  const iconClass = [
    "document-file-icon",
    `document-file-icon-${format.toLowerCase()}`,
  ].join(" ");

  return (
    <div className={iconClass} aria-label={`فایل ${format}`}>
      <span>{format}</span>
      <i aria-hidden="true" />
    </div>
  );
};

const DocumentsPage = () => {
  const [searchTerm, setSearchTerm] = useState("");

  const [selectedCategory, setSelectedCategory] = useState<
    DocumentCategory | "all"
  >("all");

  const [currentPage, setCurrentPage] = useState(1);

  const filteredDocuments = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLocaleLowerCase("fa-IR");

    return documents.filter((document) => {
      const matchesCategory =
        selectedCategory === "all" ||
        document.category === selectedCategory;

      const searchableText = [
        document.title,
        document.description,
        document.type,
        document.fileFormat,
        document.fileName,
      ]

      const matchesSearch =
        normalizedSearch.length === 0 ||
        searchableText.includes(normalizedSearch);

      return matchesCategory && matchesSearch;
    });
  }, [searchTerm, selectedCategory]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredDocuments.length / ITEMS_PER_PAGE)
  );

  const paginatedDocuments = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;

    return filteredDocuments.slice(
      startIndex,
      startIndex + ITEMS_PER_PAGE
    );
  }, [currentPage, filteredDocuments]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedCategory]);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const resetFilters = () => {
    setSearchTerm("");
    setSelectedCategory("all");
    setCurrentPage(1);
  };

  return (
    <main className="documents-page" dir="rtl">
      <div className="container">
        <header className="documents-page-header">
          <h1 className="documents-page-title">مستندات</h1>

          <p className="documents-page-subtitle">
            فایل‌ها، راهنماها، کاتالوگ‌ها و مستندات مورد نیاز خود را دریافت
            کنید.
          </p>
        </header>

        <section
          className="documents-filters"
          aria-label="فیلتر مستندات"
        >
          <div className="row g-3">
            <div className="col-12 col-md-7">
              <label
                htmlFor="document-search"
                className="documents-filter-label"
              >
                جستجو در مستندات
              </label>

              <div className="document-search-wrapper">
                <span
                  className="document-search-icon"
                  aria-hidden="true"
                >
                  ⌕
                </span>

                <input
                  id="document-search"
                  type="search"
                  className="document-search-input"
                  placeholder="عنوان، توضیح یا فرمت فایل را جستجو کنید..."
                  value={searchTerm}
                  onChange={(event) => {
                    setSearchTerm(event.target.value);
                  }}
                />
              </div>
            </div>

            <div className="col-12 col-md-5">
              <label
                htmlFor="document-category"
                className="documents-filter-label"
              >
                دسته‌بندی
              </label>

              <select
                id="document-category"
                className="form-select document-category-select"
                value={selectedCategory}
                onChange={(event) => {
                  setSelectedCategory(
                    event.target.value as DocumentCategory | "all"
                  );
                }}
              >
                {Object.entries(categoryLabels).map(
                  ([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  )
                )}
              </select>
            </div>
          </div>
        </section>

        <div className="documents-results-info">
          <span>
            نمایش{" "}
            {paginatedDocuments.length.toLocaleString("fa-IR")} مورد از{" "}
            {filteredDocuments.length.toLocaleString("fa-IR")} مستند
          </span>

          {(searchTerm || selectedCategory !== "all") && (
            <button
              type="button"
              className="documents-reset-button"
              onClick={resetFilters}
            >
              حذف فیلترها
            </button>
          )}
        </div>

        {paginatedDocuments.length > 0 ? (
          <section className="documents-grid">
            {paginatedDocuments.map((document) => {
              const format = getFileExtension(document);

              return (
                <article
                  className="document-card"
                  key={document.id}
                >
                  <div className="document-card-top">
                    <DocumentIcon format={format} />

                    <span className="document-card-format">
                      {document.fileFormat || format}
                    </span>
                  </div>

                  <div className="document-card-body">
                    <span className="document-card-type">
                      {document.type}
                    </span>

                    <h2 className="document-card-title">
                      {document.title}
                    </h2>

                    <p className="document-card-description">
                      {document.description}
                    </p>

                    <div className="document-card-meta">
                      <span>
                        <strong>حجم:</strong> {document.fileSize}
                      </span>

                      {document.version && (
                        <span>
                          <strong>نسخه:</strong> {document.version}
                        </span>
                      )}

                      {document.publishDate && (
                        <span>
                          <strong>انتشار:</strong>{" "}
                          {document.publishDate}
                        </span>
                      )}

                      <span>
                        <strong>دریافت:</strong>{" "}
                        {formatDownloadCount(document.downloads)}
                      </span>
                    </div>
                  </div>

                  <div className="document-card-footer">
                    <a
                      href={document.fileUrl}
                      download={document.fileName}
                      className="document-download-button"
                    >
                      <span aria-hidden="true">↓</span>
                      دانلود فایل
                    </a>
                  </div>
                </article>
              );
            })}
          </section>
        ) : (
          <section className="documents-empty-state">
            <div
              className="documents-empty-icon"
              aria-hidden="true"
            >
              📁
            </div>

            <h2>مستندی پیدا نشد</h2>

            <p>
              عبارت جستجو یا دسته‌بندی انتخاب‌شده نتیجه‌ای نداشت.
            </p>

            <button
              type="button"
              className="btn btn-primary"
              onClick={resetFilters}
            >
              نمایش همه مستندات
            </button>
          </section>
        )}

        {totalPages > 1 && (
          <nav
            className="documents-pagination"
            aria-label="صفحه‌بندی مستندات"
          >
            <button
              type="button"
              className="documents-pagination-button"
              disabled={currentPage === 1}
              onClick={() => {
                setCurrentPage((page) => Math.max(1, page - 1));
              }}
            >
              قبلی
            </button>

            <div className="documents-pagination-pages">
             {Array.from(
                { length: totalPages },
                (_, index) => index + 1
              ).map((page) => (
                <button
                  type="button"
                  key={page}
                  className={`documents-pagination-page ${
                    currentPage === page ? "active" : ""
                  }`}
                  aria-current={
                    currentPage === page ? "page" : undefined
                  }
                  onClick={() => {
                    setCurrentPage(page);
                  }}
                >
                  {page.toLocaleString("fa-IR")}
                </button>
              ))}
            </div>

            <button
              type="button"
              className="documents-pagination-button"
              disabled={currentPage === totalPages}
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

export default DocumentsPage;

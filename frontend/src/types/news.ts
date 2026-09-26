export type NewsCategory =
  | "all"
  | "news"
  | "event"
  | "announcement"
  | "product"
  | "report";

export interface NewsItem {
  id: string;
  slug: string;
  title: string;
  summary: string;
  content: string;
  imageUrl: string;
  imageAlt?: string;
  category: Exclude<NewsCategory, "all">;
  publishDate: string;
  author?: string;
  readingTime?: number;
  tags?: string[];
  isFeatured?: boolean;
}

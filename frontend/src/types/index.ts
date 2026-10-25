// src/types/index.ts

// =============================================================================
// Navigation
// =============================================================================
export interface NavItem {
  label: string;
  href: string;
  badge?: string;
}

export interface FooterLinkGroup {
  title: string;
  links: NavItem[];
}

// =============================================================================
// Pagination (DRF)
// =============================================================================
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// =============================================================================
// User
// =============================================================================
export interface User {
  id: number;
  email: string;
  phone: string | null;
  full_name: string;
  first_name: string;
  last_name: string;
  avatar: string | null;
  role: 'admin' | 'user';
  is_admin: boolean;
  is_verified: boolean;
  bio: string;
  organization: string;
  field_of_study: string;
  website: string;
  linkedin: string;
  google_scholar: string;
  activity_logs_enabled: boolean;
}

export interface LoginPayload {
  identifier: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface SignupPayload {
  email: string;
  phone?: string | null;
  password: string;
}

// =============================================================================
// News / Event / Call — نمای یکپارچه
// =============================================================================
export type ContentCategory =
  | 'all'
  | 'news'
  | 'event'
  | 'announcement'
  | 'product'
  | 'report';

export interface ContentItem {
  id: string;
  slug: string;
  title: string;
  summary: string;
  content: string;
  imageUrl: string;
  category: Exclude<ContentCategory, 'all'>;
  publishDate: string; // ISO
  viewCount: number;
  author?: string;
  readingTime?: number;
  tags?: string[];
  isFeatured?: boolean;
}

// =============================================================================
// Guides (Documents)
// =============================================================================
export interface Guide {
  id: number;
  title: string;
  description: string;
  fileUrl: string;
  fileName: string;
  fileFormat: string;
  fileSize: number; // بایت
  downloadCount: number;
  uploadedAt: string; // ISO
  isActive: boolean;
}

// =============================================================================
// Courses / Videos (Tutorials)
// =============================================================================
export interface CourseListItem {
  id: number;
  title: string;
  slug: string;
  description: string;
  thumbnailUrl: string | null;
  isActive: boolean;
  createdAt: string;
}

export interface Video {
  id: number;
  title: string;
  description: string;
  videoUrl: string | null;
  thumbnailUrl: string | null;
  order: number;
  duration: number;
  createdAt: string;
}

export interface CourseDetail extends CourseListItem {
  videos: Video[];
  updatedAt: string;
}

export interface Tutorial {
  id: number;
  title: string;
  description: string;
  type: string;
  thumbnail: string;
  videoUrl: string;
}

// =============================================================================
// SiteSettings
// =============================================================================
export interface SiteSettings {
  site_name: string;
  tagline: string;
  logo_url: string | null;
  favicon_url: string | null;
  updated_at: string;
}

export interface Banner {
  id: number;
  title: string;
  subtitle: string;
  imageUrl: string;
  linkUrl: string;
  order: number;
  isActive: boolean;
}

export interface Supporter {
  id: number;
  name: string;
  logoUrl: string;
  websiteUrl: string;
  order: number;
  isActive: boolean;
}
// src/services/content.ts
import api, { stripHost } from './api';
import { estimateReadingTime, getFileExtension } from '../utils/format';
import type {
  ContentItem,
  CourseDetail,
  CourseListItem,
  Guide,
  Paginated,
  Tutorial,
  Video,
} from '../types';

// =============================================================================
// helper — دریافت همه‌ی آیتم‌ها با دنبال کردن next
// =============================================================================
async function fetchAllPages<T>(endpoint: string): Promise<T[]> {
  const all: T[] = [];
  let url: string | null = endpoint;

  while (url) {
    const { data } = await api.get<Paginated<T> | T[]>(url);

    if (Array.isArray(data)) {
      all.push(...data);
      break;
    }

    all.push(...data.results);
    url = data.next ? stripHost(data.next) : null;
  }

  return all;
}

// =============================================================================
// News/Event/Call adapters
// =============================================================================
function buildContent(
  raw: Record<string, any>,
  category: ContentItem['category'],
): ContentItem {
  return {
    id: String(raw.id),
    slug: raw.slug,
    title: raw.title,
    summary: raw.summary ?? '',
    content: raw.content ?? '',
    imageUrl: raw.cover_image_url ?? '',
    category,
    publishDate: raw.published_at ?? raw.created_at ?? '',
    viewCount: raw.view_count ?? 0,
    readingTime: estimateReadingTime(raw.content),
  };
}

// =============================================================================
// Content (News + Events + Calls)
// =============================================================================
export const contentService = {
  async fetchAll(): Promise<ContentItem[]> {
    const [news, events, calls] = await Promise.all([
      fetchAllPages<Record<string, any>>('/events/news/').catch(() => []),
      fetchAllPages<Record<string, any>>('/events/events/').catch(() => []),
      fetchAllPages<Record<string, any>>('/events/calls/').catch(() => []),
    ]);

    const items: ContentItem[] = [
      ...news.map((r) => buildContent(r, 'news')),
      ...events.map((r) => buildContent(r, 'event')),
      ...calls.map((r) => buildContent(r, 'announcement')),
    ];

    return items.sort((a, b) => {
      const aTime = a.publishDate ? new Date(a.publishDate).getTime() : 0;
      const bTime = b.publishDate ? new Date(b.publishDate).getTime() : 0;
      return bTime - aTime;
    });
  },

  async fetchBySlug(slug: string): Promise<ContentItem | null> {
    const endpoints: Array<[string, ContentItem['category']]> = [
      ['/events/news/', 'news'],
      ['/events/events/', 'event'],
      ['/events/calls/', 'announcement'],
    ];

    for (const [endpoint, category] of endpoints) {
      try {
        const { data } = await api.get<Record<string, any>>(`${endpoint}${slug}/`);
        return buildContent(data, category);
      } catch {
        // 404 → try next
      }
    }

    return null;
  },
};

// =============================================================================
// Guides (Documents)
// =============================================================================
function adaptGuide(raw: Record<string, any>): Guide {
  const fileName = raw.file_url
    ? decodeURIComponent(raw.file_url.split('/').pop() || '')
    : '';
  return {
    id: raw.id,
    title: raw.title,
    description: raw.description ?? '',
    fileUrl: raw.file_url ?? '',
    fileName,
    fileFormat: getFileExtension(fileName),
    fileSize: raw.file_size ?? 0,
    downloadCount: raw.download_count ?? 0,
    uploadedAt: raw.uploaded_at ?? '',
    isActive: raw.is_active ?? true,
  };
}

export const guideService = {
  async fetchAll(): Promise<Guide[]> {
    const raw = await fetchAllPages<Record<string, any>>('/guides/');
    return raw.map(adaptGuide);
  },
};

// =============================================================================
// Courses → Tutorials (flatten videos)
// =============================================================================
function adaptVideo(video: Record<string, any>, course: CourseDetail): Tutorial {
  return {
    id: video.id,
    title: video.title,
    description: video.description || course.description || '',
    type: course.title,
    thumbnail: video.thumbnail_url || course.thumbnailUrl || '',
    videoUrl: video.video_url || '',
  };
}

function adaptCourseList(raw: Record<string, any>): CourseListItem {
  return {
    id: raw.id,
    title: raw.title,
    slug: raw.slug,
    description: raw.description ?? '',
    thumbnailUrl: raw.thumbnail_url ?? null,
    isActive: raw.is_active ?? true,
    createdAt: raw.created_at ?? '',
  };
}

function adaptCourseDetail(raw: Record<string, any>): CourseDetail {
  return {
    ...adaptCourseList(raw),
    updatedAt: raw.updated_at ?? '',
    videos: (raw.videos ?? []).map((v: Record<string, any>) => ({
      id: v.id,
      title: v.title,
      description: v.description ?? '',
      videoUrl: v.video_url ?? null,
      thumbnailUrl: v.thumbnail_url ?? null,
      order: v.order ?? 0,
      duration: v.duration ?? 0,
      createdAt: v.created_at ?? '',
    })) as Video[],
  };
}

export const courseService = {
  async fetchAll(): Promise<CourseListItem[]> {
    const raw = await fetchAllPages<Record<string, any>>('/courses/');
    return raw.map(adaptCourseList);
  },

  async fetchDetail(slug: string): Promise<CourseDetail> {
    const { data } = await api.get<Record<string, any>>(`/courses/${slug}/`);
    return adaptCourseDetail(data);
  },

  /**
   * دریافت همه‌ی آموزش‌ها — هر ویدیو از هر دوره یک Tutorial
   */
  async fetchAllTutorials(): Promise<Tutorial[]> {
    const courses = await this.fetchAll();

    const details = await Promise.all(
      courses.map((c) =>
        this.fetchDetail(c.slug).catch(() => null),
      ),
    );

    const tutorials: Tutorial[] = [];
    for (const detail of details) {
      if (!detail) continue;
      for (const video of detail.videos) {
        tutorials.push(adaptVideo(video, detail));
      }
    }

    return tutorials;
  },
};
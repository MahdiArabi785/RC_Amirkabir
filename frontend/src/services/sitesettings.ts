// src/services/sitesettings.ts
import api, { stripHost } from './api';
import type { Banner, Paginated, SiteSettings, Supporter } from '../types';

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

function adaptBanner(raw: Record<string, any>): Banner {
  return {
    id: raw.id,
    title: raw.title ?? '',
    subtitle: raw.subtitle ?? '',
    imageUrl: raw.image_url ?? '',
    linkUrl: raw.link_url ?? '',
    order: raw.order ?? 0,
    isActive: raw.is_active ?? true,
  };
}

function adaptSupporter(raw: Record<string, any>): Supporter {
  return {
    id: raw.id,
    name: raw.name ?? '',
    logoUrl: raw.logo_url ?? '',
    websiteUrl: raw.website_url ?? '',
    order: raw.order ?? 0,
    isActive: raw.is_active ?? true,
  };
}

export const siteSettingsService = {
  async fetchSettings(): Promise<SiteSettings> {
    const { data } = await api.get<SiteSettings>('/settings/');
    return data;
  },

  async fetchBanners(): Promise<Banner[]> {
    const raw = await fetchAllPages<Record<string, any>>('/banners/');
    return raw.map(adaptBanner);
  },

  async fetchSupporters(): Promise<Supporter[]> {
    const raw = await fetchAllPages<Record<string, any>>('/supporters/');
    return raw.map(adaptSupporter);
  },
};
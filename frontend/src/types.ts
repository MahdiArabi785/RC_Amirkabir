// types.ts
export interface NavItem {
  label: string;
  href: string;
  badge?: string;
}

export interface FooterLinkGroup {
  title: string;
  links: NavItem[];
}

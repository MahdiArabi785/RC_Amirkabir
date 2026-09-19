export type DocumentCategory =
  | "guide"
  | "catalog"
  | "form"
  | "standard"
  | "report"
  | "other";

export interface DocumentItem {
  id: number;
  title: string;
  description: string;
  type: string;
  category: DocumentCategory;
  fileUrl: string;
  fileName: string;
  fileFormat: string;
  fileSize: string;
  version?: string;
  publishDate?: string;
  downloads?: number;
}

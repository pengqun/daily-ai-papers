export interface Author {
  id: number;
  name: string;
  affiliation: string | null;
}

export interface PaperListItem {
  id: number;
  source: string;
  source_id: string;
  title: string;
  abstract: string | null;
  published_at: string | null;
  categories: string[] | null;
  keywords: string[] | null;
  status: string;
  authors: Author[];
}

export interface PaperDetail extends PaperListItem {
  summary: string | null;
  summary_zh: string | null;
  contributions: string[] | null;
  pdf_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubmitPaperRequest {
  source: "arxiv" | "semantic_scholar";
  paper_ids: string[];
}

export interface SubmitPaperResult {
  source_id: string;
  status: string;
  paper_id: number | null;
  message: string;
}

export interface SubmitPaperResponse {
  total: number;
  results: SubmitPaperResult[];
}

export interface ChatRequest {
  question: string;
  paper_ids?: number[];
}

export interface ChatResponse {
  answer: string;
  source_papers: number[];
  source_chunks: string[];
}

export type PaperStatus =
  | "pending"
  | "crawled"
  | "downloading"
  | "parsed"
  | "analyzed"
  | "embedded"
  | "ready";

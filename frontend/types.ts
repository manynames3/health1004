export type LanguageCode = "ko" | "en" | "mixed" | "unknown";

export interface Citation {
  document_id: string;
  chunk_id: string;
  title: string;
  filename: string;
  detected_date?: string | null;
  page_start: number;
  page_end: number;
  page_numbers: number[];
  page_quotes: Array<{ page_number: number; quote: string }>;
  section_title?: string | null;
  quote: string;
  pdf_url?: string | null;
}

export interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  title: string;
  filename: string;
  detected_date?: string | null;
  page_start: number;
  page_end: number;
  page_numbers: number[];
  page_spans: Array<{ page_number: number; text: string; token_count?: number }>;
  section_title?: string | null;
  language: LanguageCode;
  text: string;
  score: number;
  source_s3_key?: string | null;
  pdf_s3_key?: string | null;
  extraction_method?: string | null;
  token_count?: number | null;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  retrieved_chunks: RetrievedChunk[];
  language: LanguageCode;
  warning_notes: string[];
  request_id: string;
}

export interface DocumentSummary {
  document_id: string;
  title: string;
  filename: string;
  detected_date?: string | null;
  language: LanguageCode;
  page_count: number;
  chunk_count: number;
  extraction_method?: string | null;
  pdf_s3_key?: string | null;
  pdf_url?: string | null;
  checksum?: string | null;
}

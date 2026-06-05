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

export interface AdminStatus {
  admin_configured: boolean;
  aws_region_configured: boolean;
  s3_configured: boolean;
  s3_bucket?: string | null;
  metadata_key: string;
  vector_bundle_key: string;
  upload_limit_bytes: number;
}

export interface AdminIngestResponse {
  status: "completed";
  run_id: string;
  total_pdfs: number;
  successful_pdfs: number;
  failed_pdfs: number;
  skipped_pdfs: number;
  pages_processed: number;
  chunks_created: number;
  vector_bundle: {
    s3_key?: string;
    record_count?: number;
    bytes_gzipped?: number;
  };
  files: Array<{
    filename: string;
    document_id?: string;
    status: string;
    reason?: string;
    page_count?: number;
    chunk_count?: number;
    vector_records?: number;
    extraction_method?: string;
    error?: string;
  }>;
  errors: Array<{ filename: string; status: string; error: string }>;
}

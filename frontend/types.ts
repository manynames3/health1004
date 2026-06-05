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
  series?: string | null;
  volume?: string | null;
  lesson_number?: string | null;
  source_page_image_s3_key?: string | null;
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
  article_id?: string | null;
  source_s3_key?: string | null;
  pdf_s3_key?: string | null;
  source_pdf_s3_key?: string | null;
  source_text_s3_key?: string | null;
  source_page_image_s3_key?: string | null;
  extraction_method?: string | null;
  token_count?: number | null;
  original_korean_text?: string | null;
  english_summary_optional?: string | null;
  body_system_tags: string[];
  symptom_tags: string[];
  condition_tags: string[];
  food_tags: string[];
  substance_tags: string[];
  habit_tags: string[];
  body_system_slugs: string[];
  symptom_slugs: string[];
  condition_slugs: string[];
  food_slugs: string[];
  substance_slugs: string[];
  habit_slugs: string[];
  avoid_tags: string[];
  recommended_food_tags: string[];
  topic_slugs: string[];
  confidence_score?: number | null;
  needs_human_review: boolean;
  embedding_id?: string | null;
}

export interface ResolvedQuery {
  original_query: string;
  detected_language: LanguageCode;
  matched_topics: string[];
  matched_topic_slugs: string[];
  matched_body_systems: string[];
  matched_body_system_slugs: string[];
  expanded_aliases: string[];
  retrieval_filters: Record<string, string[]>;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  retrieved_chunks: RetrievedChunk[];
  language: LanguageCode;
  warning_notes: string[];
  request_id: string;
  resolved_query?: ResolvedQuery | null;
  related_topics: Array<{ slug: string; title: string; category?: string }>;
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
  series?: string | null;
  volume?: string | null;
  lesson_number?: string | null;
  pdf_s3_key?: string | null;
  pdf_url?: string | null;
  checksum?: string | null;
}

export interface DocumentListResponse {
  documents: DocumentSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface TopicSummary {
  slug: string;
  title: string;
  english_title?: string | null;
  category: string;
  aliases: string[];
  body_system_slugs: string[];
  related_slugs: string[];
  source_count: number;
}

export interface TaxonomyResponse {
  categories: Record<string, TopicSummary[]>;
  topic_count: number;
  alias_count: number;
}

export interface TopicListResponse {
  topics: TopicSummary[];
}

export interface TopicDetail extends TopicSummary {
  related_topics: TopicSummary[];
  source_passages: RetrievedChunk[];
  related_documents: DocumentSummary[];
  safety_disclaimer: string;
}

export interface PassageListResponse {
  passages: RetrievedChunk[];
  total: number;
}

export interface PassageSearchResponse {
  query: string;
  category?: string | null;
  matched_topics: string[];
  matched_topic_slugs: string[];
  expanded_aliases: string[];
  filters_used: Record<string, string[]>;
  fallback_used: boolean;
  passages: RetrievedChunk[];
  total: number;
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

export interface AdminReviewTagResponse {
  status: "updated" | "not_configured";
  chunk_id: string;
}

export interface AdminAliasSuggestionResponse {
  status: "saved";
  suggestion_count: number;
  key: string;
}

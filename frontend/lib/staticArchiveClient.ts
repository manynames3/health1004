import { DocumentListResponse, DocumentSummary, TopicDetail, TopicListResponse } from "../types";

const STATIC_ARCHIVE_BASE = "/static-data/archive";

export async function fetchStaticTopics(path = "/topics"): Promise<TopicListResponse | null> {
  return fetchStaticJson<TopicListResponse>(`${STATIC_ARCHIVE_BASE}/categories/${categoryCacheName(path)}.json`);
}

export async function fetchStaticTopic(slug: string): Promise<TopicDetail | null> {
  return fetchStaticJson<TopicDetail>(`${STATIC_ARCHIVE_BASE}/topics/${encodeURIComponent(slug)}.json`);
}

export async function fetchStaticDocuments({
  query = "",
  limit = 25,
  offset = 0
}: {
  query?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<DocumentListResponse | null> {
  const payload = await fetchStaticJson<DocumentListResponse>(`${STATIC_ARCHIVE_BASE}/documents/all.json`);
  if (!payload) return null;
  return paginateDocuments(payload.documents || [], query, limit, offset);
}

async function fetchStaticJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(path, { cache: "force-cache" });
    if (response.status === 404) return null;
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function paginateDocuments(
  documents: DocumentSummary[],
  query: string,
  limit: number,
  offset: number
): DocumentListResponse {
  const needle = query.trim().toLowerCase();
  const matched = needle ? documents.filter((document) => documentMatches(document, needle)) : documents;
  return {
    documents: matched.slice(offset, offset + limit),
    total: matched.length,
    limit,
    offset
  };
}

function documentMatches(document: DocumentSummary, needle: string): boolean {
  return [document.title, document.filename, document.detected_date, document.series, document.volume, document.lesson_number]
    .filter(Boolean)
    .join(" ")
    .toLowerCase()
    .includes(needle);
}

function categoryCacheName(path: string): string {
  const normalized = path.replace(/^\/+|\/+$/g, "") || "topics";
  return normalized === "topics" ? "topics" : normalized;
}

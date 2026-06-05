import { TopicDetail, TopicListResponse } from "../types";

const STATIC_ARCHIVE_BASE = "/static-data/archive";

export async function fetchStaticTopics(path = "/topics"): Promise<TopicListResponse | null> {
  return fetchStaticJson<TopicListResponse>(`${STATIC_ARCHIVE_BASE}/categories/${categoryCacheName(path)}.json`);
}

export async function fetchStaticTopic(slug: string): Promise<TopicDetail | null> {
  return fetchStaticJson<TopicDetail>(`${STATIC_ARCHIVE_BASE}/topics/${encodeURIComponent(slug)}.json`);
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

function categoryCacheName(path: string): string {
  const normalized = path.replace(/^\/+|\/+$/g, "") || "topics";
  return normalized === "topics" ? "topics" : normalized;
}

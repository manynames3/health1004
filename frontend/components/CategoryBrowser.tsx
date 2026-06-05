"use client";

import Link from "next/link";
import { Loader2, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchTopics } from "../lib/api";
import { TopicListResponse, TopicSummary } from "../types";

const CATEGORY_CACHE_VERSION = "v1";
const CATEGORY_CACHE_MAX_AGE_MS = 24 * 60 * 60 * 1000;

export function CategoryBrowser({
  endpoint,
  emptyText = "표시할 주제가 없습니다."
}: {
  endpoint: string;
  emptyText?: string;
}) {
  const [topics, setTopics] = useState<TopicSummary[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;
    const cached = readCachedTopics(endpoint);
    if (cached) {
      setTopics(cached.topics);
      setLoading(false);
    }

    fetchTopics(endpoint)
      .then((payload) => {
        if (ignore) return;
        setTopics(payload.topics);
        setError("");
        writeCachedTopics(endpoint, payload);
      })
      .catch((err: Error) => {
        if (!ignore && !cached) setError(formatError(err));
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, [endpoint]);

  const filtered = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    if (!needle) return topics;
    return topics.filter((topic) => `${topic.title} ${topic.english_title || ""} ${topic.aliases.join(" ")}`.toLowerCase().includes(needle));
  }, [topics, filter]);
  const trimmedFilter = filter.trim();
  const scopeLabel = endpointLabel(endpoint);
  const topicCountLabel =
    loading && topics.length === 0 ? "주제 목록 불러오는 중" : `등록된 ${scopeLabel} 주제 ${topics.length.toLocaleString()}개`;

  return (
    <section className="browse-panel">
      <label className="input-with-icon">
        <Search size={18} aria-hidden="true" />
        <input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder={`${scopeLabel} 주제, 별칭 검색`} />
      </label>
      <div className="category-search-meta">
        <span>{topicCountLabel}</span>
        {trimmedFilter && (
          <Link href={`/ask/?q=${encodeURIComponent(trimmedFilter)}`}>원문 전체에서 질문하기</Link>
        )}
      </div>
      {loading && (
        <div className="empty-state">
          <Loader2 className="spin" size={18} aria-hidden="true" />
          주제 목록을 불러오는 중입니다.
        </div>
      )}
      {error && <div className="error-box">{error}</div>}
      {!loading && !error && filtered.length === 0 && (
        <div className="category-empty-state">
          <p>{trimmedFilter ? `등록된 ${scopeLabel} 주제 중 일치 항목이 없습니다.` : emptyText}</p>
          {trimmedFilter && (
            <div className="category-empty-actions">
              <Link href={`/ask/?q=${encodeURIComponent(trimmedFilter)}`}>원문 전체에서 질문하기</Link>
              {endpoint !== "/topics" && <Link href="/topics/">전체 주제에서 찾기</Link>}
            </div>
          )}
        </div>
      )}
      <div className="archive-topic-grid">
        {filtered.map((topic) => (
          <Link className="archive-topic-card" href={`/topics/${topic.slug}/`} key={topic.slug}>
            <span>{categoryLabel(topic.category)}</span>
            <h2>{topic.title}</h2>
            {topic.english_title && <p>{topic.english_title}</p>}
            <small>{topic.aliases.slice(0, 5).join(", ")}</small>
            <strong>원문 조각 {topic.source_count.toLocaleString()}개</strong>
          </Link>
        ))}
      </div>
    </section>
  );
}

function categoryLabel(category: string): string {
  return (
    {
      body_systems: "관심군",
      symptoms: "증상/고민",
      conditions: "질환",
      foods: "음식",
      substances: "첨가물/물질",
      habits: "생활습관"
    }[category] || category
  );
}

function endpointLabel(endpoint: string): string {
  return (
    {
      "/topics": "전체",
      "/symptoms": "증상/고민",
      "/foods": "음식/식재료",
      "/conditions": "질환",
      "/substances": "첨가물/물질",
      "/habits": "생활습관"
    }[endpoint] || "현재 분류"
  );
}

function formatError(error: Error): string {
  if (error.message === "Failed to fetch") {
    return "API 서버에 연결할 수 없습니다. 잠시 후 새로고침하거나 배포된 Pages 주소에서 다시 시도하세요.";
  }
  return error.message;
}

function cacheKey(endpoint: string): string {
  return `health1004-category:${CATEGORY_CACHE_VERSION}:${endpoint}`;
}

function readCachedTopics(endpoint: string): TopicListResponse | null {
  try {
    const raw = window.localStorage.getItem(cacheKey(endpoint));
    if (!raw) return null;
    const cached = JSON.parse(raw) as { savedAt: number; payload: TopicListResponse };
    if (!cached.savedAt || Date.now() - cached.savedAt > CATEGORY_CACHE_MAX_AGE_MS) return null;
    if (!cached.payload?.topics?.length) return null;
    return cached.payload;
  } catch {
    return null;
  }
}

function writeCachedTopics(endpoint: string, payload: TopicListResponse): void {
  try {
    window.localStorage.setItem(cacheKey(endpoint), JSON.stringify({ savedAt: Date.now(), payload }));
  } catch {
    // Browsers can reject localStorage in private mode or when storage is full.
  }
}

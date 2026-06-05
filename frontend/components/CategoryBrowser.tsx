"use client";

import Link from "next/link";
import { Loader2, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchTopics, searchPassages } from "../lib/api";
import { PassageSearchResponse, RetrievedChunk, TopicListResponse, TopicSummary } from "../types";

const CATEGORY_CACHE_VERSION = "v2";
const CATEGORY_CACHE_MAX_AGE_MS = 24 * 60 * 60 * 1000;

export function CategoryBrowser({
  endpoint,
  emptyText = "표시할 주제가 없습니다.",
  initialTopics
}: {
  endpoint: string;
  emptyText?: string;
  initialTopics?: TopicListResponse | null;
}) {
  const [topics, setTopics] = useState<TopicSummary[]>(initialTopics?.topics ?? []);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(!initialTopics);
  const [error, setError] = useState("");
  const [sourceSearch, setSourceSearch] = useState<PassageSearchResponse | null>(null);
  const [sourceLoading, setSourceLoading] = useState(false);
  const [sourceError, setSourceError] = useState("");

  useEffect(() => {
    let ignore = false;
    if (initialTopics) {
      setTopics(initialTopics.topics);
      setLoading(false);
      setError("");
      writeCachedTopics(endpoint, initialTopics);
      return () => {
        ignore = true;
      };
    }

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
  }, [endpoint, initialTopics]);

  useEffect(() => {
    const query = filter.trim();
    if (query.length < 2) {
      setSourceSearch(null);
      setSourceError("");
      setSourceLoading(false);
      return;
    }
    let ignore = false;
    setSourceLoading(true);
    setSourceError("");
    const timer = window.setTimeout(() => {
      searchPassages({ query, category: endpointCategory(endpoint), limit: 6 })
        .then((payload) => {
          if (ignore) return;
          setSourceSearch(payload);
        })
        .catch((err: Error) => {
          if (!ignore) {
            setSourceSearch(null);
            setSourceError(formatError(err));
          }
        })
        .finally(() => {
          if (!ignore) setSourceLoading(false);
        });
    }, 250);
    return () => {
      ignore = true;
      window.clearTimeout(timer);
    };
  }, [filter, endpoint]);

  const topicsWithSources = useMemo(() => topics.filter((topic) => topic.source_count > 0), [topics]);
  const filtered = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    if (!needle) return topicsWithSources;
    return topics.filter((topic) => `${topic.title} ${topic.english_title || ""} ${topic.aliases.join(" ")}`.toLowerCase().includes(needle));
  }, [topics, topicsWithSources, filter]);
  const trimmedFilter = filter.trim();
  const scopeLabel = endpointLabel(endpoint);
  const topicCountLabel =
    loading && topics.length === 0
      ? "주제 목록 불러오는 중"
      : `관련 원문이 있는 ${scopeLabel} 주제 ${topicsWithSources.length.toLocaleString()}개`;

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
            <strong>관련 원문 {topic.source_count.toLocaleString()}건</strong>
          </Link>
        ))}
      </div>

      {trimmedFilter.length >= 2 && (
        <section className="source-search-section" aria-label="Original archive results">
          <div className="source-search-heading">
            <div>
              <p className="eyebrow">원문 결과</p>
              <h2>PDF 안에서 찾은 관련 원문</h2>
            </div>
            <Link href={`/admin/?alias=${encodeURIComponent(trimmedFilter)}&category=${encodeURIComponent(endpointCategory(endpoint) || "topics")}`}>
              새 별칭으로 제안
            </Link>
          </div>

          {sourceLoading && (
            <div className="empty-state">
              <Loader2 className="spin" size={18} aria-hidden="true" />
              관련 원문을 찾는 중입니다.
            </div>
          )}
          {sourceError && <div className="error-box">{sourceError}</div>}
          {!sourceLoading && !sourceError && sourceSearch && (
            <>
              <div className="source-search-summary">
                <span>
                  관련 원문 {sourceSearch.total.toLocaleString()}건
                  {sourceSearch.fallback_used ? " · 전체 원문까지 확장 검색" : ""}
                </span>
                {sourceSearch.matched_topics.length > 0 && (
                  <small>연결된 주제: {sourceSearch.matched_topics.slice(0, 5).join(", ")}</small>
                )}
                {sourceSearch.expanded_aliases.length > 0 && (
                  <small>확장어: {sourceSearch.expanded_aliases.slice(0, 6).join(", ")}</small>
                )}
              </div>

              {sourceSearch.passages.length === 0 ? (
                <div className="empty-state">원문에서도 일치하는 내용을 찾지 못했습니다.</div>
              ) : (
                <div className="source-result-list">
                  {sourceSearch.passages.map((passage) => (
                    <article className="source-result-card" key={passage.chunk_id}>
                      <h3>{passage.section_title || passage.title}</h3>
                      <p>
                        {passage.filename} · p.{formatPages(passage)}
                      </p>
                      <blockquote>{excerpt(passage.text)}</blockquote>
                      <footer>
                        <Link href={`/documents/document/?id=${encodeURIComponent(passage.document_id)}`}>문서 보기</Link>
                        <Link href={`/ask/?q=${encodeURIComponent(trimmedFilter)}`}>원문 기반으로 질문하기</Link>
                      </footer>
                    </article>
                  ))}
                </div>
              )}
            </>
          )}
        </section>
      )}
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

function endpointCategory(endpoint: string): string | undefined {
  return (
    {
      "/symptoms": "symptoms",
      "/foods": "foods",
      "/conditions": "conditions",
      "/substances": "substances",
      "/habits": "habits"
    }[endpoint]
  );
}

function formatPages(passage: RetrievedChunk): string {
  if (passage.page_numbers?.length) {
    const pages = [...new Set(passage.page_numbers)].sort((a, b) => a - b);
    return pages.length === 1 ? String(pages[0]) : `${pages[0]}-${pages[pages.length - 1]}`;
  }
  return passage.page_start === passage.page_end ? String(passage.page_start) : `${passage.page_start}-${passage.page_end}`;
}

function excerpt(text: string, maxChars = 220): string {
  const compact = (text || "").replace(/\s+/g, " ").trim();
  if (compact.length <= maxChars) return compact;
  return `${compact.slice(0, maxChars - 1).trim()}...`;
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

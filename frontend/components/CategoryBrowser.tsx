"use client";

import Link from "next/link";
import { Loader2, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchTopics } from "../lib/api";
import { TopicSummary } from "../types";

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
    fetchTopics(endpoint)
      .then((payload) => setTopics(payload.topics))
      .catch((err: Error) => setError(formatError(err)))
      .finally(() => setLoading(false));
  }, [endpoint]);

  const filtered = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    if (!needle) return topics;
    return topics.filter((topic) => `${topic.title} ${topic.english_title || ""} ${topic.aliases.join(" ")}`.toLowerCase().includes(needle));
  }, [topics, filter]);

  return (
    <section className="browse-panel">
      <label className="input-with-icon">
        <Search size={18} aria-hidden="true" />
        <input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="주제, 별칭, 영어명 검색" />
      </label>
      {loading && (
        <div className="empty-state">
          <Loader2 className="spin" size={18} aria-hidden="true" />
          주제 목록을 불러오는 중입니다.
        </div>
      )}
      {error && <div className="error-box">{error}</div>}
      {!loading && !error && filtered.length === 0 && <div className="empty-state">{emptyText}</div>}
      <div className="archive-topic-grid">
        {filtered.map((topic) => (
          <Link className="archive-topic-card" href={`/topics/${topic.slug}/`} key={topic.slug}>
            <span>{categoryLabel(topic.category)}</span>
            <h2>{topic.title}</h2>
            {topic.english_title && <p>{topic.english_title}</p>}
            <small>{topic.aliases.slice(0, 5).join(", ")}</small>
            <strong>{topic.source_count.toLocaleString()} sources</strong>
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

function formatError(error: Error): string {
  if (error.message === "Failed to fetch") {
    return "API 서버에 연결할 수 없습니다. FastAPI 백엔드와 NEXT_PUBLIC_API_BASE_URL을 확인하세요.";
  }
  return error.message;
}

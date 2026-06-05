"use client";

import Link from "next/link";
import { Loader2, Search } from "lucide-react";
import { FormEvent, useState } from "react";
import { resolveArchiveQuery } from "../lib/api";
import { ResolvedQuery } from "../types";

export function ResolveSearchPanel() {
  const [query, setQuery] = useState("");
  const [resolved, setResolved] = useState<ResolvedQuery | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      setResolved(await resolveArchiveQuery(query.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "검색어를 해석할 수 없습니다.");
      setResolved(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="resolver-panel" aria-labelledby="resolver-title">
      <form onSubmit={onSubmit}>
        <label htmlFor="archive-query" id="resolver-title">
          건강 고민, 음식, 첨가물, 질환을 입력하세요
        </label>
        <div>
          <Search size={20} aria-hidden="true" />
          <input
            id="archive-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="예: 속이 안 좋고 소화가 안돼요"
          />
          <button type="submit" disabled={loading || !query.trim()}>
            {loading ? <Loader2 className="spin" size={18} /> : "찾기"}
          </button>
        </div>
      </form>

      {error && <div className="error-box">{error}</div>}

      {resolved && (
        <div className="resolver-results">
          <div>
            <span>일치한 주제</span>
            <strong>{resolved.matched_topics.length ? resolved.matched_topics.join(", ") : "일치 항목 없음"}</strong>
          </div>
          <div>
            <span>관련 표현</span>
            <strong>{resolved.expanded_aliases.slice(0, 10).join(", ") || "별칭 없음"}</strong>
          </div>
          <div>
            <span>추천 분류</span>
            <strong>{resolved.matched_body_systems.join(", ") || "전체 아카이브"}</strong>
          </div>
          <div className="resolver-actions">
            {resolved.matched_topic_slugs[0] && (
              <Link href={`/topics/${resolved.matched_topic_slugs[0]}/`}>이 주제로 보기</Link>
            )}
            <Link href={`/ask/?q=${encodeURIComponent(resolved.original_query)}`}>원문 기반으로 질문하기</Link>
          </div>
        </div>
      )}
    </section>
  );
}

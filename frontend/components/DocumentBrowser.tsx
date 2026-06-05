"use client";

import { FileText, Loader2, Search } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { fetchDocuments } from "../lib/api";
import { DocumentListResponse, DocumentSummary } from "../types";

const PAGE_SIZE = 25;

export function DocumentBrowser({ initialDocuments = null }: { initialDocuments?: DocumentListResponse | null }) {
  const [allDocuments, setAllDocuments] = useState<DocumentSummary[]>(initialDocuments?.documents ?? []);
  const [liveDocuments, setLiveDocuments] = useState<DocumentSummary[]>([]);
  const [filter, setFilter] = useState("");
  const [submittedFilter, setSubmittedFilter] = useState("");
  const [liveTotal, setLiveTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const usingStaticDocuments = Boolean(initialDocuments?.documents?.length);
  const [loading, setLoading] = useState(!usingStaticDocuments);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;
    if (usingStaticDocuments) {
      setAllDocuments(initialDocuments?.documents ?? []);
      setLoading(false);
      setError("");
      return () => {
        ignore = true;
      };
    }

    setLoading(true);
    fetchDocuments({ query: submittedFilter, limit: PAGE_SIZE, offset })
      .then((payload) => {
        if (ignore) return;
        setLiveDocuments(payload.documents);
        setLiveTotal(payload.total);
        setError("");
      })
      .catch((err: Error) => setError(formatConnectionError(err)))
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [submittedFilter, offset, initialDocuments, usingStaticDocuments]);

  function submitSearch(event: FormEvent) {
    event.preventDefault();
    setError("");
    setOffset(0);
    setSubmittedFilter(filter.trim());
  }

  const filteredStaticDocuments = useMemo(() => {
    if (!usingStaticDocuments) return [];
    const needle = submittedFilter.trim().toLowerCase();
    if (!needle) return allDocuments;
    return allDocuments.filter((doc) => documentMatches(doc, needle));
  }, [allDocuments, submittedFilter, usingStaticDocuments]);
  const documents = usingStaticDocuments ? filteredStaticDocuments.slice(offset, offset + PAGE_SIZE) : liveDocuments;
  const total = usingStaticDocuments ? filteredStaticDocuments.length : liveTotal;
  const currentStart = total === 0 ? 0 : offset + 1;
  const currentEnd = Math.min(offset + documents.length, total);
  const hasPrevious = offset > 0;
  const hasNext = offset + PAGE_SIZE < total;

  return (
    <section className="panel document-panel" aria-labelledby="documents-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">문서</p>
          <h2 id="documents-title">PDF 브라우저</h2>
        </div>
        <span className="count-pill">총 {total.toLocaleString()}개</span>
      </div>

      <form className="document-search-form" onSubmit={submitSearch}>
        <label className="input-with-icon">
          <Search size={18} aria-hidden="true" />
          <input
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder="제목 검색"
          />
        </label>
        <button type="submit">검색</button>
      </form>

      {loading && (
        <div className="empty-state">
          <Loader2 className="spin" size={18} aria-hidden="true" />
          문서 목록을 불러오는 중입니다.
        </div>
      )}

      {error && <div className="error-box">{error}</div>}

      {!loading && !error && documents.length === 0 && (
        <div className="empty-state">일치하는 문서를 찾지 못했습니다.</div>
      )}

      {!loading && !error && documents.length > 0 && (
        <div className="document-range">
          {currentStart.toLocaleString()}-{currentEnd.toLocaleString()}번째 원문
          {submittedFilter && <span> · "{submittedFilter}" 검색 결과</span>}
        </div>
      )}

      <div className="document-list">
        {documents.map((doc) => (
          <article className="document-row" key={doc.document_id}>
            <FileText size={19} aria-hidden="true" />
            <div className="document-main">
              <h3>
                <Link href={`/documents/document/?id=${encodeURIComponent(doc.document_id)}`}>{doc.title}</Link>
              </h3>
            </div>
          </article>
        ))}
      </div>

      {!loading && !error && total > PAGE_SIZE && (
        <div className="document-pager">
          <button type="button" disabled={!hasPrevious} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
            이전
          </button>
          <span>
            {Math.floor(offset / PAGE_SIZE) + 1} / {Math.ceil(total / PAGE_SIZE)}
          </span>
          <button type="button" disabled={!hasNext} onClick={() => setOffset(offset + PAGE_SIZE)}>
            다음
          </button>
        </div>
      )}
    </section>
  );
}

function documentMatches(document: DocumentSummary, needle: string): boolean {
  return [document.title, document.filename, document.detected_date, document.series, document.volume, document.lesson_number]
    .filter(Boolean)
    .join(" ")
    .toLowerCase()
    .includes(needle);
}

function formatConnectionError(error: Error): string {
  if (error.message === "Failed to fetch") {
    return "API 서버에 연결할 수 없습니다. 잠시 후 새로고침하거나 배포된 API 주소를 확인하세요.";
  }
  return error.message;
}

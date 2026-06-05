"use client";

import { ExternalLink, FileText, Loader2, Search } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { fetchDocuments } from "../lib/api";
import { DocumentSummary } from "../types";

const PAGE_SIZE = 25;

export function DocumentBrowser() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [filter, setFilter] = useState("");
  const [submittedFilter, setSubmittedFilter] = useState("");
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    fetchDocuments({ query: submittedFilter, limit: PAGE_SIZE, offset })
      .then((payload) => {
        if (ignore) return;
        setDocuments(payload.documents);
        setTotal(payload.total);
        setError("");
      })
      .catch((err: Error) => setError(formatConnectionError(err)))
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [submittedFilter, offset]);

  function submitSearch(event: FormEvent) {
    event.preventDefault();
    setError("");
    setOffset(0);
    setSubmittedFilter(filter.trim());
  }

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
            placeholder="제목, 파일명 검색"
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
              <p>
                {doc.lesson_number ? `#${doc.lesson_number} · ` : ""}
                {doc.page_count}쪽 · 원문 조각 {doc.chunk_count}개
              </p>
              <span>{doc.filename}</span>
            </div>
            {doc.pdf_url && (
              <a className="icon-link" href={doc.pdf_url} target="_blank" rel="noreferrer" aria-label="PDF 열기">
                <ExternalLink size={18} />
              </a>
            )}
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

function formatConnectionError(error: Error): string {
  if (error.message === "Failed to fetch") {
    return "API 서버에 연결할 수 없습니다. 잠시 후 새로고침하거나 배포된 API 주소를 확인하세요.";
  }
  return error.message;
}

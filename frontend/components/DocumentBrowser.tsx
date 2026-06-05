"use client";

import { ExternalLink, FileText, Loader2, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchDocuments } from "../lib/api";
import { DocumentSummary } from "../types";

export function DocumentBrowser() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchDocuments()
      .then(setDocuments)
      .catch((err: Error) => setError(formatConnectionError(err)))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    if (!needle) return documents;
    return documents.filter((doc) => {
      const haystack = `${doc.title} ${doc.filename} ${doc.detected_date || ""}`.toLowerCase();
      return haystack.includes(needle);
    });
  }, [documents, filter]);

  return (
    <section className="panel document-panel" aria-labelledby="documents-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">문서</p>
          <h2 id="documents-title">PDF 브라우저</h2>
        </div>
        <span className="count-pill">{documents.length.toLocaleString()} files</span>
      </div>

      <label className="input-with-icon">
        <Search size={18} aria-hidden="true" />
        <input
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          placeholder="연도, 날짜, 제목, 파일명 검색"
        />
      </label>

      {loading && (
        <div className="empty-state">
          <Loader2 className="spin" size={18} aria-hidden="true" />
          문서 목록을 불러오는 중입니다.
        </div>
      )}

      {error && <div className="error-box">{error}</div>}

      {!loading && !error && filtered.length === 0 && (
        <div className="empty-state">일치하는 문서를 찾지 못했습니다.</div>
      )}

      <div className="document-list">
        {filtered.map((doc) => (
          <article className="document-row" key={doc.document_id}>
            <FileText size={19} aria-hidden="true" />
            <div className="document-main">
              <h3>{doc.title}</h3>
              <p>
                {doc.detected_date || "날짜 미상"} · {doc.page_count} pages · {doc.chunk_count} chunks
              </p>
              <span>{doc.filename}</span>
            </div>
            {doc.pdf_url && (
              <a className="icon-link" href={doc.pdf_url} target="_blank" rel="noreferrer" aria-label="Open PDF">
                <ExternalLink size={18} />
              </a>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

function formatConnectionError(error: Error): string {
  if (error.message === "Failed to fetch") {
    return "API 서버에 연결할 수 없습니다. FastAPI 백엔드를 localhost:8000에서 실행하면 문서 목록이 표시됩니다.";
  }
  return error.message;
}

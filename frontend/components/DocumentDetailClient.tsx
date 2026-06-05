"use client";

import { ExternalLink, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchDocument } from "../lib/api";
import { DocumentSummary } from "../types";

export function DocumentDetailClient({ documentId }: { documentId: string }) {
  const [document, setDocument] = useState<DocumentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const resolvedDocumentId =
      documentId === "document" ? new URLSearchParams(window.location.search).get("id") || "" : documentId;
    if (!resolvedDocumentId) {
      setError("문서 ID가 없습니다.");
      setLoading(false);
      return;
    }
    fetchDocument(resolvedDocumentId)
      .then(setDocument)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [documentId]);

  if (loading) {
    return (
      <div className="empty-state">
        <Loader2 className="spin" size={18} />
        문서 정보를 불러오는 중입니다.
      </div>
    );
  }
  if (error || !document) return <div className="error-box">{error || "문서를 찾지 못했습니다."}</div>;

  return (
    <section className="document-detail-card">
      <p className="eyebrow">원문 PDF</p>
      <h2>{document.title}</h2>
      <dl>
        <div>
          <dt>파일명</dt>
          <dd>{document.filename}</dd>
        </div>
        <div>
          <dt>날짜</dt>
          <dd>{document.detected_date || "날짜 미상"}</dd>
        </div>
        <div>
          <dt>페이지 / 조각</dt>
          <dd>
            {document.page_count}쪽 · 원문 조각 {document.chunk_count}개
          </dd>
        </div>
        <div>
          <dt>추출 방식</dt>
          <dd>{document.extraction_method || "미상"}</dd>
        </div>
      </dl>
      {document.pdf_url && (
        <a className="primary-link dark" href={document.pdf_url} target="_blank" rel="noreferrer">
          <ExternalLink size={18} />
          원문 PDF 열기
        </a>
      )}
    </section>
  );
}

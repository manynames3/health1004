"use client";

import { Loader2 } from "lucide-react";
import { FormEvent, useState } from "react";
import { fetchLowConfidencePassages, reviewTag } from "../lib/api";
import { RetrievedChunk } from "../types";

export function AdminReviewPanel() {
  const [password, setPassword] = useState("");
  const [passages, setPassages] = useState<RetrievedChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [hasSubmittedPassword, setHasSubmittedPassword] = useState(false);

  async function loadQueue(adminPassword: string) {
    const trimmed = adminPassword.trim();
    if (!trimmed) {
      setError("");
      setPassages([]);
      setHasSubmittedPassword(false);
      return;
    }
    setHasSubmittedPassword(true);
    setLoading(true);
    setError("");
    try {
      const payload = await fetchLowConfidencePassages(trimmed);
      setPassages(payload.passages);
    } catch (err) {
      setError(err instanceof Error ? formatReviewError(err.message) : "검토 대기열을 불러올 수 없습니다.");
    } finally {
      setLoading(false);
    }
  }

  async function onPasswordSubmit(event: FormEvent) {
    event.preventDefault();
    await loadQueue(password);
  }

  async function markReviewed(passage: RetrievedChunk) {
    setSaved("");
    await reviewTag({
      adminPassword: password.trim(),
      chunkId: passage.chunk_id,
      topicSlugs: passage.topic_slugs,
      confidenceScore: 0.9,
      needsHumanReview: false
    });
    setSaved(`${passage.chunk_id} 검토 완료`);
    setPassages((current) => current.filter((item) => item.chunk_id !== passage.chunk_id));
  }

  return (
    <section className="review-panel">
      <form onSubmit={onPasswordSubmit} className="review-password-row">
        <input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="관리자 비밀번호" type="password" />
        <button type="submit">검토 목록 불러오기</button>
      </form>
      {!hasSubmittedPassword && !loading && !error && (
        <div className="empty-state">관리자 비밀번호를 입력하면 태그 검토 목록을 불러옵니다.</div>
      )}
      {loading && (
        <div className="empty-state">
          <Loader2 className="spin" size={18} />
          검토 항목을 불러오는 중입니다.
        </div>
      )}
      {error && <div className="error-box">{error}</div>}
      {saved && <div className="success-box">{saved}</div>}
      {hasSubmittedPassword && !loading && !error && passages.length === 0 && (
        <div className="empty-state">검토가 필요한 태그 항목이 없습니다.</div>
      )}
      <div className="passage-list">
        {passages.map((passage) => (
          <article className="passage-card" key={passage.chunk_id}>
            <h2>{passage.section_title || passage.title}</h2>
            <p>
              {passage.filename} · p.{passage.page_start}-{passage.page_end} · 신뢰도{" "}
              {passage.confidence_score?.toFixed(2) || "0.00"}
            </p>
            <blockquote>{passage.text}</blockquote>
            <small>{passage.topic_slugs.join(", ") || "태그 없음"}</small>
            <button type="button" onClick={() => markReviewed(passage)}>
              검토 완료
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

function formatReviewError(message: string): string {
  if (message === "Invalid admin password") {
    return "관리자 비밀번호가 올바르지 않습니다.";
  }
  return message;
}

"use client";

import { Loader2 } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { fetchLowConfidencePassages, reviewTag } from "../lib/api";
import { RetrievedChunk } from "../types";

export function AdminReviewPanel() {
  const [password, setPassword] = useState("");
  const [passages, setPassages] = useState<RetrievedChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");

  useEffect(() => {
    loadQueue("");
  }, []);

  async function loadQueue(adminPassword: string) {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchLowConfidencePassages(adminPassword);
      setPassages(payload.passages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "검토 대기열을 불러올 수 없습니다.");
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
      adminPassword: password,
      chunkId: passage.chunk_id,
      topicSlugs: passage.topic_slugs,
      confidenceScore: 0.9,
      needsHumanReview: false
    });
    setSaved(`${passage.chunk_id} updated`);
    setPassages((current) => current.filter((item) => item.chunk_id !== passage.chunk_id));
  }

  return (
    <section className="review-panel">
      <form onSubmit={onPasswordSubmit} className="review-password-row">
        <input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="ADMIN_PASSWORD" type="password" />
        <button type="submit">Load queue</button>
      </form>
      {loading && (
        <div className="empty-state">
          <Loader2 className="spin" size={18} />
          검토 항목을 불러오는 중입니다.
        </div>
      )}
      {error && <div className="error-box">{error}</div>}
      {saved && <div className="success-box">{saved}</div>}
      <div className="passage-list">
        {passages.map((passage) => (
          <article className="passage-card" key={passage.chunk_id}>
            <h2>{passage.section_title || passage.title}</h2>
            <p>
              {passage.filename} · p.{passage.page_start}-{passage.page_end} · confidence{" "}
              {passage.confidence_score?.toFixed(2) || "0.00"}
            </p>
            <blockquote>{passage.text}</blockquote>
            <small>{passage.topic_slugs.join(", ") || "untagged"}</small>
            <button type="button" onClick={() => markReviewed(passage)}>
              Mark reviewed
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

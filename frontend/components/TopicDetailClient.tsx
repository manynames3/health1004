"use client";

import Link from "next/link";
import { ExternalLink, Loader2, MessageSquareText } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchTopic } from "../lib/api";
import { TopicDetail } from "../types";

export function TopicDetailClient({ slug, initialTopic = null }: { slug: string; initialTopic?: TopicDetail | null }) {
  const [topic, setTopic] = useState<TopicDetail | null>(initialTopic);
  const [loading, setLoading] = useState(!initialTopic);
  const [error, setError] = useState("");

  useEffect(() => {
    if (initialTopic?.slug === slug) {
      setTopic(initialTopic);
      setLoading(false);
      setError("");
      return;
    }

    setLoading(true);
    setError("");
    fetchTopic(slug)
      .then(setTopic)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [slug, initialTopic]);

  if (loading) {
    return (
      <div className="empty-state">
        <Loader2 className="spin" size={18} />
        주제 자료를 불러오는 중입니다.
      </div>
    );
  }
  if (error || !topic) return <div className="error-box">{error || "주제를 찾지 못했습니다."}</div>;

  return (
    <div className="topic-detail-layout">
      <section className="topic-main-panel">
        <div className="topic-title-row">
          <div>
            <p className="eyebrow">{topic.category}</p>
            <h1>{topic.title}</h1>
            {topic.english_title && <p>{topic.english_title}</p>}
          </div>
          <Link className="primary-link dark" href={`/ask/?topic=${topic.slug}`}>
            <MessageSquareText size={18} />
            이 주제로 질문하기
          </Link>
        </div>

        <div className="alias-cloud">
          {topic.aliases.map((alias) => (
            <span key={alias}>{alias}</span>
          ))}
        </div>

        <section>
          <h2>주요 원문 발췌</h2>
          <div className="passage-list">
            {topic.source_passages.length === 0 && <div className="empty-state">아직 연결된 원문 발췌가 없습니다.</div>}
            {topic.source_passages.map((passage) => (
              <article className="passage-card" key={passage.chunk_id}>
                <div>
                  <h3>{passage.section_title || passage.title}</h3>
                  <p>
                    {passage.filename} · p.
                    {passage.page_start === passage.page_end ? passage.page_start : `${passage.page_start}-${passage.page_end}`}
                  </p>
                </div>
                <blockquote>{passage.original_korean_text || passage.text}</blockquote>
                <footer>
                  <Link href={`/documents/document/?id=${encodeURIComponent(passage.document_id)}`}>문서 보기</Link>
                  <span>p.{passage.page_start === passage.page_end ? passage.page_start : `${passage.page_start}-${passage.page_end}`}</span>
                </footer>
              </article>
            ))}
          </div>
        </section>
      </section>

      <aside className="topic-side-panel">
        <section>
          <h2>관련 주제</h2>
          {topic.related_topics.length === 0 && <p>관련 주제는 태깅 후 표시됩니다.</p>}
          {topic.related_topics.map((related) => (
            <Link href={`/topics/${related.slug}/`} key={related.slug}>
              {related.title}
              <small>관련 원문 {related.source_count}건</small>
            </Link>
          ))}
        </section>
        <section>
          <h2>관련 원문 PDF</h2>
          {topic.related_documents.length === 0 && <p>관련 문서는 태깅 후 표시됩니다.</p>}
          {topic.related_documents.map((doc) => (
            <article key={doc.document_id}>
              <strong>{doc.title}</strong>
              <span>{doc.filename}</span>
              <Link href={`/documents/document/?id=${encodeURIComponent(doc.document_id)}`}>문서 보기</Link>
              {doc.pdf_url && (
                <a href={doc.pdf_url} target="_blank" rel="noreferrer">
                  <ExternalLink size={15} />
                  PDF
                </a>
              )}
            </article>
          ))}
        </section>
        <p className="safety-note">{topic.safety_disclaimer}</p>
      </aside>
    </div>
  );
}

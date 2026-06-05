"use client";

import { AlertTriangle, BookOpen, ChevronDown, ExternalLink, Loader2, Send, ShieldCheck } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { askQuestion } from "../lib/api";
import { QueryResponse, RetrievedChunk } from "../types";

const EXAMPLE_QUESTIONS = [
  "우유와 골다공증에 대해 뭐라고 하나요?",
  "대장암과 고기 섭취의 관계를 찾아줘.",
  "방부제에 대해 나온 자료를 정리해줘."
];

export function QueryWorkspace() {
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(8);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    const topic = params.get("topic");
    if (q) setQuestion(q);
    if (topic) setQuestion(`이 자료에서는 ${topic} 주제를 어떻게 설명하나요?`);
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;
    setLoading(true);
    setError("");
    try {
      setResponse(await askQuestion(trimmed, topK));
    } catch (err) {
      setError(err instanceof Error ? formatConnectionError(err) : "알 수 없는 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  const citationCount = response?.citations.length ?? 0;

  return (
    <section className="workspace" aria-label="Question answer workspace">
      <form className="query-panel" onSubmit={onSubmit}>
        <div className="query-heading">
          <div>
            <p className="eyebrow">원문 질문</p>
            <h2>원문 기반 요약</h2>
          </div>
          <div className="model-note">
            <ShieldCheck size={16} aria-hidden="true" />
            출처 필수
          </div>
        </div>

        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="원문 자료에 대해 질문하세요. 예: 속이 안 좋고 소화가 안돼요"
          rows={5}
        />

        <div className="query-actions">
          <label>
            참고할 원문
            <select value={topK} onChange={(event) => setTopK(Number(event.target.value))}>
              {[4, 6, 8, 10, 12, 16].map((value) => (
                <option value={value} key={value}>
                  최대 {value}개
                </option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
            질문하기
          </button>
        </div>

        <div className="example-row" aria-label="Example questions">
          {EXAMPLE_QUESTIONS.map((example) => (
            <button type="button" key={example} onClick={() => setQuestion(example)}>
              {example}
            </button>
          ))}
        </div>
      </form>

      <div className="disclaimer">
        <AlertTriangle size={18} aria-hidden="true" />
        <p>
          이 기능은 업로드된 원문을 요약해 보여주는 교육용 아카이브입니다. 진단, 처방, 치료 계획이
          필요하거나 증상이 급한 경우에는 자격을 갖춘 의료 전문가와 상담하세요.
        </p>
      </div>

      {error && <div className="error-box">{error}</div>}

      <section className="answer-panel" aria-labelledby="answer-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">답변</p>
            <h2 id="answer-title">근거 기반 요약</h2>
          </div>
          <span className="count-pill">인용 {citationCount}개</span>
        </div>

        {!response && !loading && (
          <div className="empty-answer">
            <BookOpen size={24} aria-hidden="true" />
            질문을 입력하면 답변, 인용, 검색된 원문 근거가 여기에 표시됩니다.
          </div>
        )}

        {loading && (
          <div className="empty-answer">
            <Loader2 className="spin" size={24} aria-hidden="true" />
            관련 원문과 인용 가능한 출처를 확인하는 중입니다.
          </div>
        )}

        {response && (
          <>
            {response.warning_notes.length > 0 && (
              <div className="warning-list">
                {response.warning_notes.map((note) => (
                  <p key={note}>{note}</p>
                ))}
              </div>
            )}
            {response.resolved_query && (
              <div className="resolved-strip">
                <span>해석된 주제</span>
                <strong>{response.resolved_query.matched_topics.join(", ") || "전체 아카이브"}</strong>
              </div>
            )}
            <div className="answer-text">{response.answer}</div>
            <CitationList response={response} />
            <RetrievedSources chunks={response.retrieved_chunks} />
          </>
        )}
      </section>
    </section>
  );
}

function formatConnectionError(error: Error): string {
  if (error.message === "Failed to fetch") {
    return "API 서버에 연결할 수 없습니다. FastAPI 백엔드를 localhost:8000에서 실행하거나 NEXT_PUBLIC_API_BASE_URL을 확인하세요.";
  }
  return error.message;
}

function CitationList({ response }: { response: QueryResponse }) {
  if (response.citations.length === 0) return null;

  return (
    <section className="citation-section" aria-labelledby="citations-title">
      <h3 id="citations-title">인용</h3>
      <div className="citation-list">
        {response.citations.map((citation) => (
          <article className="citation-card" key={`${citation.chunk_id}-${citation.page_start}`}>
            <div>
              <h4>{citation.section_title || citation.title}</h4>
              <p>
                {citation.filename} · {citation.detected_date || "날짜 미상"} · p.
                {citation.page_start === citation.page_end
                  ? citation.page_start
                  : `${citation.page_start}-${citation.page_end}`}
              </p>
            </div>
            <blockquote>
              {citation.page_quotes?.length
                ? citation.page_quotes.map((item) => `p. ${item.page_number}: ${item.quote}`).join(" ")
                : citation.quote}
            </blockquote>
            <div className="citation-footer">
              <code>{citation.chunk_id}</code>
              {citation.pdf_url && (
                <a href={citation.pdf_url} target="_blank" rel="noreferrer">
                  <ExternalLink size={16} aria-hidden="true" />
                  PDF
                </a>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function RetrievedSources({ chunks }: { chunks: RetrievedChunk[] }) {
  const sorted = useMemo(() => [...chunks].sort((a, b) => b.score - a.score), [chunks]);
  if (sorted.length === 0) return null;

  return (
    <section className="source-section" aria-labelledby="sources-title">
      <h3 id="sources-title">검색된 원문 근거</h3>
      <div className="source-list">
        {sorted.map((chunk) => (
          <details key={chunk.chunk_id} className="source-detail">
            <summary>
              <span>
                {chunk.title}
                <small>
                  {chunk.section_title ? `${chunk.section_title} · ` : ""}
                  {chunk.filename} · p.
                  {chunk.page_start === chunk.page_end ? chunk.page_start : `${chunk.page_start}-${chunk.page_end}`} ·{" "}
                  관련도 {chunk.score.toFixed(3)}
                </small>
              </span>
              <ChevronDown size={18} aria-hidden="true" />
            </summary>
            <p>{chunk.text}</p>
            <code>{chunk.chunk_id}</code>
          </details>
        ))}
      </div>
    </section>
  );
}

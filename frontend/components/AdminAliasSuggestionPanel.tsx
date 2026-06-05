"use client";

import { FormEvent, useEffect, useState } from "react";
import { suggestAlias } from "../lib/api";

export function AdminAliasSuggestionPanel() {
  const [password, setPassword] = useState("");
  const [query, setQuery] = useState("");
  const [suggestedAlias, setSuggestedAlias] = useState("");
  const [category, setCategory] = useState("substances");
  const [canonicalSlug, setCanonicalSlug] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const alias = params.get("alias") || "";
    const queryParam = params.get("q") || alias;
    const categoryParam = params.get("category") || "substances";
    if (alias) setSuggestedAlias(alias);
    if (queryParam) setQuery(queryParam);
    if (categoryParam) setCategory(categoryParam);
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSaved("");
    if (!password.trim()) {
      setError("관리자 비밀번호를 입력하세요.");
      return;
    }
    const alias = suggestedAlias.trim();
    if (!alias) {
      setError("제안할 별칭을 입력하세요.");
      return;
    }
    setSaving(true);
    try {
      const response = await suggestAlias({
        adminPassword: password.trim(),
        query: query.trim() || alias,
        category,
        suggestedAlias: alias,
        canonicalSlug: canonicalSlug.trim() || undefined,
        notes: notes.trim() || undefined
      });
      setSaved(`별칭 제안이 저장되었습니다. 총 ${response.suggestion_count.toLocaleString()}개 대기 중입니다.`);
    } catch (err) {
      setError(err instanceof Error ? formatAliasError(err.message) : "별칭 제안을 저장할 수 없습니다.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="review-panel">
      <form className="alias-suggestion-form" onSubmit={onSubmit}>
        <label>
          관리자 비밀번호
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
        </label>
        <label>
          검색어
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="예: 카라멜색소" />
        </label>
        <label>
          새 별칭
          <input value={suggestedAlias} onChange={(event) => setSuggestedAlias(event.target.value)} placeholder="예: 카라멜색소" />
        </label>
        <label>
          분류
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="substances">첨가물/물질</option>
            <option value="foods">음식/식재료</option>
            <option value="conditions">질환</option>
            <option value="symptoms">증상/고민</option>
            <option value="habits">생활습관</option>
            <option value="topics">전체 주제</option>
          </select>
        </label>
        <label>
          연결할 기존 slug
          <input value={canonicalSlug} onChange={(event) => setCanonicalSlug(event.target.value)} placeholder="예: colorant" />
        </label>
        <label>
          메모
          <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} placeholder="반복 검색어, 연결하고 싶은 주제, 확인한 원문 등을 남겨주세요." />
        </label>
        <button type="submit" disabled={saving}>{saving ? "저장 중..." : "별칭 제안 저장"}</button>
      </form>
      {error && <div className="error-box">{error}</div>}
      {saved && <div className="success-box">{saved}</div>}
    </section>
  );
}

function formatAliasError(message: string): string {
  if (message === "Invalid admin password") {
    return "관리자 비밀번호가 올바르지 않습니다.";
  }
  return message;
}

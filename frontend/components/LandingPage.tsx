import {
  ArrowRight,
  BadgeCheck,
  BookOpenCheck,
  Database,
  FileSearch,
  Leaf,
  LineChart,
  SearchCheck,
  ShieldCheck
} from "lucide-react";
import { AdminIngestPanel } from "./AdminIngestPanel";
import { DocumentBrowser } from "./DocumentBrowser";
import { QueryWorkspace } from "./QueryWorkspace";

const topicFamilies = [
  { name: "식원성 질환 / 먹거리", count: 67, detail: "고기, 음료, 식품첨가물, 식습관", tone: "green" },
  { name: "혈관 / 심장 / 당뇨", count: 67, detail: "혈관오염, 심장질환, 혈당, 대사", tone: "blue" },
  { name: "암 예방과 치유", count: 62, detail: "발암물질, 영양소, 주요 암 주제", tone: "coral" },
  { name: "약물복용", count: 50, detail: "진통제, 스테로이드, 수면제, 항우울제", tone: "slate" },
  { name: "생활독소 / 환경독소", count: 44, detail: "전자파, 수은, 설탕, 환경호르몬", tone: "amber" },
  { name: "영양소 / 보충", count: 39, detail: "비타민 B/C/D, 코큐10, 오메가-3", tone: "gold" },
  { name: "장 건강", count: 37, detail: "장내세균, 유익균, 글루텐, 프로바이오틱스", tone: "olive" },
  { name: "스트레스 / 면역", count: 28, detail: "면역계, 조절계, 스트레스와 질환", tone: "teal" }
];

const proofPoints = [
  { label: "PDF corpus", value: "365", note: "건강미인 3탄 파일명 기준" },
  { label: "Topic families", value: "8", note: "식습관부터 약물복용까지" },
  { label: "Retrieval style", value: "S3", note: "저비용 벡터 묶음 검색" },
  { label: "Citation mode", value: "Page", note: "페이지 단위 근거 확인" }
];

const workflow = [
  {
    icon: FileSearch,
    title: "Korean PDF ingestion",
    body: "Embedded text and OCR diagnostics preserve Korean source quality before retrieval."
  },
  {
    icon: SearchCheck,
    title: "Evidence-first search",
    body: "Questions retrieve ranked passages with source pages before answer generation."
  },
  {
    icon: Database,
    title: "Low-cost archive",
    body: "The vector bundle lives in S3, avoiding always-on managed search infrastructure."
  }
];

export function LandingPage() {
  return (
    <main className="site-shell">
      <section className="hero-section" aria-labelledby="hero-title">
        <nav className="top-nav" aria-label="Primary">
          <a className="brand-mark" href="#top" aria-label="Health1004 home">
            <span>H</span>
            Health1004
          </a>
          <div className="nav-links">
            <a href="#topics">Topics</a>
            <a href="#workflow">Workflow</a>
            <a href="#workspace">Workspace</a>
            <a href="#admin">Admin</a>
          </div>
        </nav>

        <div className="hero-content" id="top">
          <p className="hero-kicker">
            <Leaf size={18} aria-hidden="true" />
            Korean natural-health PDF intelligence
          </p>
          <h1 id="hero-title">Health1004</h1>
          <p className="hero-copy">
            A citation-first knowledge base for the 건강미인 3탄 archive, spanning food-origin illness, lifestyle
            toxins, gut health, nutrition, cancer prevention, vascular health, stress, immunity, and medication topics.
          </p>
          <div className="hero-actions">
            <a className="primary-link" href="#workspace">
              Open workspace
              <ArrowRight size={18} aria-hidden="true" />
            </a>
            <a className="secondary-link" href="#topics">Explore corpus</a>
          </div>
        </div>
      </section>

      <section className="proof-band" aria-label="Corpus summary">
        <div className="proof-grid">
          {proofPoints.map((point) => (
            <article className="proof-item" key={point.label}>
              <p>{point.label}</p>
              <strong>{point.value}</strong>
              <span>{point.note}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-section topic-section" id="topics" aria-labelledby="topics-title">
        <div className="section-heading">
          <p className="eyebrow">파일명 분석</p>
          <h2 id="topics-title">What this database is about</h2>
          <p>
            The filenames describe a Korean health education archive centered on how food, toxins, stress, gut health,
            medications, nutrients, and chronic disease patterns connect.
          </p>
        </div>
        <div className="topic-grid">
          {topicFamilies.map((topic) => (
            <article className={`topic-card ${topic.tone}`} key={topic.name}>
              <div>
                <span>{topic.count}</span>
                <small>PDFs</small>
              </div>
              <h3>{topic.name}</h3>
              <p>{topic.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-section workflow-section" id="workflow" aria-labelledby="workflow-title">
        <div className="section-heading compact">
          <p className="eyebrow">운영 모델</p>
          <h2 id="workflow-title">A quiet SaaS layer for a long-lived archive</h2>
          <p>
            The site is shaped for low-volume maintenance: static frontend, S3 corpus storage, on-demand model calls,
            and visible source traceability.
          </p>
        </div>
        <div className="workflow-grid">
          {workflow.map((item) => {
            const Icon = item.icon;
            return (
              <article className="workflow-card" key={item.title}>
                <Icon size={22} aria-hidden="true" />
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="landing-section trust-section" aria-label="Trust cues">
        <div className="trust-row">
          <div>
            <BadgeCheck size={22} aria-hidden="true" />
            <span>OCR diagnostics</span>
          </div>
          <div>
            <BookOpenCheck size={22} aria-hidden="true" />
            <span>Page-accurate citations</span>
          </div>
          <div>
            <LineChart size={22} aria-hidden="true" />
            <span>Retrieved chunks before answers</span>
          </div>
          <div>
            <ShieldCheck size={22} aria-hidden="true" />
            <span>Education, not medical advice</span>
          </div>
        </div>
      </section>

      <section className="landing-section product-section" id="workspace" aria-labelledby="workspace-title">
        <div className="section-heading">
          <p className="eyebrow">PRODUCT SURFACE</p>
          <h2 id="workspace-title">Search the archive with source-grounded answers</h2>
          <p>
            Ask in Korean or English, inspect the retrieved chunks, and follow citations back to the PDF page context.
          </p>
        </div>
        <div className="product-grid">
          <QueryWorkspace />
          <DocumentBrowser />
        </div>
      </section>

      <section className="landing-section admin-section" id="admin" aria-labelledby="admin-title">
        <AdminIngestPanel />
      </section>
    </main>
  );
}

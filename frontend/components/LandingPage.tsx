import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  FlaskConical,
  Leaf,
  MessageSquareText,
  Salad,
  SearchCheck,
  ShieldCheck,
  Stethoscope,
  UploadCloud
} from "lucide-react";
import { CATEGORY_ROUTES } from "../lib/staticTaxonomy";
import { ResolveSearchPanel } from "./ResolveSearchPanel";
import { SiteHeader } from "./SiteChrome";

const homeCards = [
  { href: "/symptoms/", title: "내 증상/고민으로 찾기", icon: SearchCheck },
  { href: "/foods/", title: "음식/식재료로 찾기", icon: Salad },
  { href: "/substances/", title: "피해야 할 첨가물 찾기", icon: FlaskConical },
  { href: "/conditions/", title: "질환별 자료 보기", icon: Stethoscope },
  { href: "/archive/", title: "원문 PDF 읽기", icon: BookOpen },
  { href: "/ask/", title: "AI에게 질문하기", icon: MessageSquareText }
];

const adminCards = [
  { href: "/admin/ingest/", title: "PDF 업로드", detail: "AWS S3 ingestion", icon: UploadCloud },
  { href: "/admin/review/", title: "태그 검토", detail: "Low-confidence review", icon: ShieldCheck }
];

export function LandingPage() {
  return (
    <main className="archive-shell home">
      <SiteHeader />
      <section className="taxonomy-hero">
        <div>
          <p className="hero-kicker">
            <Leaf size={18} aria-hidden="true" />
            원문 기반 건강 아카이브
          </p>
          <h1>건강미인 지식서재</h1>
          <p>
            증상, 음식, 질환, 식품첨가물, 생활습관으로 찾아보는 원문 기반 건강 아카이브입니다.
            검색보다 먼저 분류와 출처를 따라 읽을 수 있게 구성했습니다.
          </p>
        </div>
      </section>

      <section className="author-section" id="author" aria-labelledby="author-title">
        <div className="author-intro">
          <p className="eyebrow">저자 / Author</p>
          <h2 id="author-title">정현수</h2>
          <p className="author-role">천문학자</p>
          <p>
            연세대학교에서 천문기상학을 전공하고, 일본 도쿄대학에서 천문학 박사학위를 취득했습니다.
            일본 노베야마우주전파관측소 객원연구원을 거쳐 한국천문연구원에서 전파망원경을 인공전파의
            간섭으로부터 보호하기 위한 정책 마련에 힘써 왔습니다.
          </p>
          <p>
            우주를 관측하는 일은 보이지 않는 신호를 붙잡아 진실에 가까워지는 일입니다. 이 아카이브는
            그런 연구자의 태도가 건강과 삶의 문제로 이어진 기록입니다. 유행이나 단정이 아니라 원문,
            맥락, 출처를 남겨 독자가 스스로 확인할 수 있게 하는 것, 그것이 이 지식서재가 지키려는
            건강과 진실의 방향입니다.
          </p>
        </div>
        <dl className="author-profile">
          <div>
            <dt>학력</dt>
            <dd>도쿄대학 천문학 박사학위</dd>
            <dd>연세대학교 천문기상학 전공</dd>
          </div>
          <div>
            <dt>경력</dt>
            <dd>일본 노베야마우주전파관측소 객원연구원</dd>
            <dd>한국천문연구원 근무</dd>
            <dd>국제전기통신연합(ITU) 과학연구반(SG7) 부의장</dd>
          </div>
          <div>
            <dt>출생지</dt>
            <dd>대한민국</dd>
          </div>
          <div>
            <dt>옮긴 책</dt>
            <dd>밀리미터파 공학, 초신성 1987A와 별의 성장, 전파로 본 우주, 암흑우주 등</dd>
          </div>
        </dl>
      </section>

      <section className="home-card-grid" aria-label="Main archive paths">
        {homeCards.map((card) => {
          const Icon = card.icon;
          return (
            <Link className="home-path-card" href={card.href} key={card.href}>
              <Icon size={24} aria-hidden="true" />
              <strong>{card.title}</strong>
              <ArrowRight size={18} aria-hidden="true" />
            </Link>
          );
        })}
      </section>

      <section className="admin-access-panel" aria-labelledby="admin-access-title">
        <div>
          <p className="eyebrow">관리자</p>
          <h2 id="admin-access-title">아카이브 관리</h2>
        </div>
        <div className="admin-access-actions">
          {adminCards.map((card) => {
            const Icon = card.icon;
            return (
              <Link href={card.href} key={card.href}>
                <Icon size={20} aria-hidden="true" />
                <span>
                  <strong>{card.title}</strong>
                  <small>{card.detail}</small>
                </span>
                <ArrowRight size={17} aria-hidden="true" />
              </Link>
            );
          })}
        </div>
      </section>

      <ResolveSearchPanel />

      <section className="archive-section">
        <div className="section-heading compact">
          <p className="eyebrow">분류로 읽기</p>
          <h2>RAG보다 먼저, 원문을 찾는 길</h2>
          <p>질문 하나에 의존하지 않고 주제, 별칭, 원문 조각, PDF 출처를 함께 확인합니다.</p>
        </div>
        <div className="category-overview-grid">
          {CATEGORY_ROUTES.slice(0, 5).map((route) => (
            <Link href={route.href} key={route.href}>
              <span>{route.label}</span>
              <p>{route.description}</p>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}

import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  FlaskConical,
  Leaf,
  MessageSquareText,
  Salad,
  SearchCheck,
  Stethoscope
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
          <h1>건강 자료를 원문 기준으로 찾아보기</h1>
          <p>
            증상, 음식, 질환, 식품첨가물, 생활습관으로 찾아보는 원문 기반 건강 아카이브입니다.
            검색보다 먼저 분류와 출처를 따라 읽을 수 있게 구성했습니다.
          </p>
        </div>
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

      <ResolveSearchPanel />

      <section className="archive-section">
        <div className="section-heading compact">
          <p className="eyebrow">분류로 읽기</p>
          <h2>주제와 출처로 원문 읽기</h2>
          <p>증상, 음식, 질환, 첨가물별로 관련 문장을 찾고 PDF 출처까지 함께 확인합니다.</p>
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

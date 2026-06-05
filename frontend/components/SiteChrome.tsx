import Link from "next/link";
import { BookOpenCheck } from "lucide-react";

export function SiteHeader() {
  return (
    <header className="archive-header">
      <Link className="archive-brand" href="/">
        건강1004 지식서재
      </Link>
      <nav aria-label="Primary archive navigation">
        <Link href="/symptoms/">증상/고민</Link>
        <Link href="/foods/">음식</Link>
        <Link href="/substances/">첨가물</Link>
        <Link href="/conditions/">질환</Link>
        <Link href="/archive/">원문 PDF</Link>
        <Link href="/ask/">AI 질문</Link>
        <Link className="admin-nav-link" href="/admin/">
          관리자
        </Link>
      </nav>
    </header>
  );
}

export function PageShell({
  eyebrow,
  title,
  subtitle,
  children
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <main className="archive-shell">
      <SiteHeader />
      <section className="archive-page-hero">
        <p className="eyebrow">{eyebrow || "원문 기반 아카이브"}</p>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </section>
      {children}
      <ArchiveDisclaimer />
    </main>
  );
}

export function ArchiveDisclaimer() {
  return (
    <section className="archive-disclaimer">
      <BookOpenCheck size={19} aria-hidden="true" />
      <p>이 사이트는 역사적/교육적 원문 아카이브이며 의학적 진단, 처방, 치료 계획을 제공하지 않습니다.</p>
    </section>
  );
}

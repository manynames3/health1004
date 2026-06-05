import { DocumentDetailClient } from "../../../components/DocumentDetailClient";
import { PageShell } from "../../../components/SiteChrome";

export function generateStaticParams() {
  return [{ id: "document" }];
}

export default async function DocumentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <PageShell eyebrow="원문 PDF" title="문서 상세" subtitle="PDF 파일명과 원문 링크를 확인합니다.">
      <DocumentDetailClient documentId={id} />
    </PageShell>
  );
}

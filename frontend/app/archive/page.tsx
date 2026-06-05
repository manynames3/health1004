import type { Metadata } from "next";
import { DocumentBrowser } from "../../components/DocumentBrowser";
import { PageShell } from "../../components/SiteChrome";
import { readStaticDocumentList } from "../../lib/staticArchiveServer";

export const metadata: Metadata = {
  title: "원문 PDF"
};

export default function ArchivePage() {
  const initialDocuments = readStaticDocumentList();
  return (
    <PageShell
      eyebrow="파일명으로 출처 확인"
      title="원문 PDF 읽기"
      subtitle="원문 제목을 순서대로 살펴보고 필요한 자료로 이동합니다."
    >
      <DocumentBrowser initialDocuments={initialDocuments} />
    </PageShell>
  );
}

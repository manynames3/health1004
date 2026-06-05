import { DocumentBrowser } from "../../components/DocumentBrowser";
import { PageShell } from "../../components/SiteChrome";

export default function ArchivePage() {
  return (
    <PageShell
      eyebrow="원문 PDF"
      title="원문 PDF 읽기"
      subtitle="문서 제목, 파일명, PDF 링크를 기준으로 원래 자료를 확인합니다."
    >
      <DocumentBrowser />
    </PageShell>
  );
}

import { AdminIngestPanel } from "../../../components/AdminIngestPanel";
import { PageShell } from "../../../components/SiteChrome";

export default function AdminIngestPage() {
  return (
    <PageShell eyebrow="ADMIN" title="PDF ingestion" subtitle="PDF를 AWS S3에 업로드하고 원문 추출, 청킹, 임베딩, 태깅을 실행합니다.">
      <AdminIngestPanel />
    </PageShell>
  );
}

import { AdminDashboard } from "../../../components/AdminDashboard";
import { PageShell } from "../../../components/SiteChrome";

export default function AdminIngestPage() {
  return (
    <PageShell eyebrow="업로드와 검토 도구" title="관리자" subtitle="PDF 업로드와 태그 검토를 한 곳에서 관리합니다.">
      <AdminDashboard />
    </PageShell>
  );
}

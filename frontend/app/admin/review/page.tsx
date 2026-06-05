import { AdminDashboard } from "../../../components/AdminDashboard";
import { PageShell } from "../../../components/SiteChrome";

export default function AdminReviewPage() {
  return (
    <PageShell eyebrow="ADMIN" title="관리자" subtitle="PDF 업로드와 태그 검토를 한 곳에서 관리합니다.">
      <AdminDashboard />
    </PageShell>
  );
}

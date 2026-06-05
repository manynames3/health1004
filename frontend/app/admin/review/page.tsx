import { AdminReviewPanel } from "../../../components/AdminReviewPanel";
import { PageShell } from "../../../components/SiteChrome";

export default function AdminReviewPage() {
  return (
    <PageShell
      eyebrow="ADMIN"
      title="Low-confidence tagging review"
      subtitle="자동 태깅 신뢰도가 낮은 원문 조각을 검토합니다."
    >
      <AdminReviewPanel />
    </PageShell>
  );
}

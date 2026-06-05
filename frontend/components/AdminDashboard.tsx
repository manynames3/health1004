import { AdminIngestPanel } from "./AdminIngestPanel";
import { AdminReviewPanel } from "./AdminReviewPanel";

export function AdminDashboard() {
  return (
    <div className="admin-dashboard">
      <nav className="admin-dashboard-nav" aria-label="Admin tools">
        <a href="#pdf-ingest">PDF 업로드</a>
        <a href="#tag-review">태그 검토</a>
      </nav>

      <div className="admin-dashboard-section" id="pdf-ingest">
        <AdminIngestPanel />
      </div>

      <div className="admin-dashboard-section" id="tag-review">
        <div className="admin-section-heading">
          <p className="eyebrow">검토 대기</p>
          <h2>태그 검토</h2>
          <p>자동 태깅 신뢰도가 낮은 원문 조각을 검토합니다.</p>
        </div>
        <AdminReviewPanel />
      </div>
    </div>
  );
}

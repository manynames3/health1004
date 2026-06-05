import { AdminAliasSuggestionPanel } from "./AdminAliasSuggestionPanel";
import { AdminIngestPanel } from "./AdminIngestPanel";
import { AdminReviewPanel } from "./AdminReviewPanel";

export function AdminDashboard() {
  return (
    <div className="admin-dashboard">
      <nav className="admin-dashboard-nav" aria-label="Admin tools">
        <a href="#pdf-ingest">PDF 업로드</a>
        <a href="#tag-review">태그 검토</a>
        <a href="#alias-suggestions">별칭 제안</a>
      </nav>

      <div className="admin-dashboard-section" id="pdf-ingest">
        <AdminIngestPanel />
      </div>

      <div className="admin-dashboard-section" id="tag-review">
        <div className="admin-section-heading">
          <p className="eyebrow">검토 대기</p>
          <h2>태그 검토</h2>
          <p>자동 태깅 신뢰도가 낮은 원문 발췌를 검토합니다.</p>
        </div>
        <AdminReviewPanel />
      </div>

      <div className="admin-dashboard-section" id="alias-suggestions">
        <div className="admin-section-heading">
          <p className="eyebrow">검색어 보강</p>
          <h2>새 별칭 제안</h2>
          <p>원문에는 나오지만 분류 목록에 없는 검색어를 taxonomy 후보로 저장합니다.</p>
        </div>
        <AdminAliasSuggestionPanel />
      </div>
    </div>
  );
}

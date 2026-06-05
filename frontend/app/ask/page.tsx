import { QueryWorkspace } from "../../components/QueryWorkspace";
import { PageShell } from "../../components/SiteChrome";

export default function AskPage() {
  return (
    <PageShell
      eyebrow="AI에게 질문하기"
      title="이 자료에서는 어떻게 설명하나요?"
      subtitle="태그로 좁힌 원문 조각과 페이지 인용을 바탕으로 답변합니다."
    >
      <QueryWorkspace />
    </PageShell>
  );
}

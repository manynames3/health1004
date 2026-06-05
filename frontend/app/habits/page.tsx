import { CategoryBrowser } from "../../components/CategoryBrowser";
import { PageShell } from "../../components/SiteChrome";

export default function HabitsPage() {
  return (
    <PageShell
      eyebrow="생활 속 단서로 탐색"
      title="생활습관별 자료 보기"
      subtitle="수면, 운동, 스트레스, 식습관, 자연치유처럼 생활의 맥락으로 원문을 읽습니다."
    >
      <CategoryBrowser endpoint="/habits" />
    </PageShell>
  );
}

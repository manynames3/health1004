import { CategoryBrowser } from "../../components/CategoryBrowser";
import { PageShell } from "../../components/SiteChrome";
import { readStaticTopicList } from "../../lib/staticArchiveServer";

export default function TopicsPage() {
  const initialTopics = readStaticTopicList("/topics");
  return (
    <PageShell
      eyebrow="분류 전체를 한눈에"
      title="모든 분류 주제"
      subtitle="증상, 음식, 질환, 첨가물, 생활습관을 하나의 통제된 한국어 taxonomy로 탐색합니다."
    >
      <CategoryBrowser endpoint="/topics" initialTopics={initialTopics} />
    </PageShell>
  );
}

import { CategoryBrowser } from "../../components/CategoryBrowser";
import { PageShell } from "../../components/SiteChrome";
import { readStaticTopicList } from "../../lib/staticArchiveServer";

export default function FoodsPage() {
  const initialTopics = readStaticTopicList("/foods");
  return (
    <PageShell
      eyebrow="식재료 이름으로 탐색"
      title="음식/식재료로 찾기"
      subtitle="마늘, 양파, 우유, 고기, 탄산음료처럼 원문에서 반복되는 음식 주제를 살펴봅니다."
    >
      <CategoryBrowser endpoint="/foods" initialTopics={initialTopics} />
    </PageShell>
  );
}

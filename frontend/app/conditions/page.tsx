import type { Metadata } from "next";
import { CategoryBrowser } from "../../components/CategoryBrowser";
import { PageShell } from "../../components/SiteChrome";
import { readStaticTopicList } from "../../lib/staticArchiveServer";

export const metadata: Metadata = {
  title: "질환"
};

export default function ConditionsPage() {
  const initialTopics = readStaticTopicList("/conditions");
  return (
    <PageShell
      eyebrow="질환명에서 원문으로"
      title="질환별 자료 보기"
      subtitle="암, 심장질환, 당뇨병, 고혈압 등 질환명으로 관련 원문을 찾아봅니다."
    >
      <CategoryBrowser endpoint="/conditions" initialTopics={initialTopics} />
    </PageShell>
  );
}

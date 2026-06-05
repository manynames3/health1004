import { CategoryBrowser } from "../../components/CategoryBrowser";
import { PageShell } from "../../components/SiteChrome";
import { readStaticTopicList } from "../../lib/staticArchiveServer";

export default function SymptomsPage() {
  const initialTopics = readStaticTopicList("/symptoms");
  return (
    <PageShell
      eyebrow="증상 표현에서 시작"
      title="내 증상/건강 고민으로 찾기"
      subtitle="진단명이 아니어도 소화, 피로, 피부, 혈압 같은 표현에서 관련 원문 주제로 이동합니다."
    >
      <CategoryBrowser endpoint="/symptoms" initialTopics={initialTopics} />
    </PageShell>
  );
}

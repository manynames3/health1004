import { PageShell } from "../../../components/SiteChrome";
import { TopicDetailClient } from "../../../components/TopicDetailClient";
import { readStaticTopicDetail } from "../../../lib/staticArchiveServer";
import { TOPIC_SLUGS } from "../../../lib/staticTaxonomy";

export function generateStaticParams() {
  return TOPIC_SLUGS.map((slug) => ({ slug }));
}

export default async function TopicPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const initialTopic = readStaticTopicDetail(slug);
  return (
    <PageShell
      eyebrow="주제 상세"
      title="관련 원문 찾아보기"
      subtitle="주제별 별칭, 원문 발췌, PDF 출처, 관련 문서를 함께 확인합니다."
    >
      <TopicDetailClient slug={slug} initialTopic={initialTopic} />
    </PageShell>
  );
}

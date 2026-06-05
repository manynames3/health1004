import { CategoryBrowser } from "../../components/CategoryBrowser";
import { PageShell } from "../../components/SiteChrome";

export default function ConditionsPage() {
  return (
    <PageShell
      eyebrow="질환명에서 원문으로"
      title="질환별 자료 보기"
      subtitle="암, 심장질환, 당뇨병, 고혈압 등 질환명으로 관련 원문을 찾아봅니다."
    >
      <CategoryBrowser endpoint="/conditions" />
    </PageShell>
  );
}

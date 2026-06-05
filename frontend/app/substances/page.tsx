import { CategoryBrowser } from "../../components/CategoryBrowser";
import { PageShell } from "../../components/SiteChrome";

export default function SubstancesPage() {
  return (
    <PageShell
      eyebrow="성분명과 별칭으로 추적"
      title="피해야 할 첨가물/화학물질 찾기"
      subtitle="방부제, 안식향산나트륨, 착색료, MSG, 농약, 공장식 축산처럼 회피 주제를 정리합니다."
    >
      <CategoryBrowser endpoint="/substances" />
    </PageShell>
  );
}

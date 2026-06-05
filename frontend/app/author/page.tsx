import { ArchiveDisclaimer, SiteHeader } from "../../components/SiteChrome";

export default function AuthorPage() {
  return (
    <main className="archive-shell">
      <SiteHeader />
      <section className="author-page-layout author-unified-section">
        <article className="author-bio-copy">
          <h1>About 건강1004</h1>
          <p className="author-subheader">정현수</p>
          <p>안녕하세요, 저는 평생 보이지 않는 신호를 붙잡으려 애써온 사람입니다.</p>
          <p>
            연세대학교에서 천문기상학을 공부하고, 일본 도쿄대학교에서 천문학 박사학위를 받았습니다.
            이후 노베야마우주전파관측소와 한국천문연구원에서 전파망원경이 조금 더 맑은 귀를 가질 수
            있도록 돕는 일을 했습니다.
          </p>
          <p>그 오랜 시간이 저에게 하나를 가르쳐 줬습니다.</p>
          <p>
            진실은 언제나 그 자리에 있습니다. 다만 제대로 볼 줄 알아야 할 뿐이에요.
          </p>
          <p>
            그 마음이 이 아카이브의 시작이었습니다. 15년간 지인들과 건강 정보를 나누면서, 유행보다는
            근거를, 빠른 답보다는 출처와 맥락을 먼저 전하려고 노력해 왔습니다. 건강1004는 그 기록들을
            증상과 음식, 질환, 첨가물, 생활습관이라는 길을 따라 다시 읽을 수 있게 정리한 공간입니다.
          </p>
          <p>
            증상이 걱정될 때, 질환에 대해 더 알고 싶을 때, 혹은 그냥 조금 더 건강하게 살고 싶을 때,
            이곳이 작은 도움이 되었으면 합니다.
          </p>
          <p>
            건강한 결정엔 좋은 정보가 필요하니까요. 그 길을 함께 찾아가고 싶습니다. 💚
          </p>
        </article>

        <aside className="author-side-column" aria-label="정현수 저자 프로필">
          <figure className="author-photo-card">
            <img src="/author-hs.jpg" alt="자연 속에서 미소 짓는 정현수 저자" />
            <figcaption>정현수 · 건강천사</figcaption>
          </figure>

          <dl className="author-profile-list">
            <div>
              <dt>학력</dt>
              <dd>도쿄대학 천문학 박사학위</dd>
              <dd>연세대학교 천문기상학 전공</dd>
            </div>
            <div>
              <dt>경력</dt>
              <dd>일본 노베야마우주전파관측소 객원연구원</dd>
              <dd>한국천문연구원 근무</dd>
              <dd>국제전기통신연합(ITU) 과학연구반(SG7) 부의장</dd>
            </div>
            <div>
              <dt>출생지</dt>
              <dd>대한민국</dd>
            </div>
            <div>
              <dt>옮긴 책</dt>
              <dd>밀리미터파 공학, 초신성 1987A와 별의 성장, 전파로 본 우주, 암흑우주 등</dd>
            </div>
          </dl>
        </aside>
      </section>
      <ArchiveDisclaimer />
    </main>
  );
}

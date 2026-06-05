import { PageShell } from "../../components/SiteChrome";

export default function AuthorPage() {
  return (
    <PageShell
      eyebrow="ABOUT"
      title="About 건강1004"
      subtitle="15년 동안의 정성으로 만들어 지인들에게 나눈 이메일들을 모아 만든 지식서재입니다."
    >
      <section className="author-archive-note">
        <p className="eyebrow">건강1004 지식서재</p>
        <h2>원문과 마음을 함께 보존하는 건강 아카이브</h2>
        <p>
          건강1004는 오랜 시간 꾸준히 나눈 건강 글과 원문 자료를 한곳에 모아, 증상과 음식, 질환,
          첨가물, 생활습관이라는 길을 따라 다시 읽을 수 있게 정리한 지식서재입니다. 빠른 답보다
          출처와 맥락을 먼저 보여주는 것을 목표로 합니다.
        </p>
      </section>

      <section className="author-page-layout">
        <article className="author-bio-copy">
          <p className="eyebrow">Bio</p>
          <h2>정현수</h2>
          <p className="author-role">건강천사</p>
          <p>
            연세대학교에서 천문기상학을 전공하고, 일본 도쿄대학에서 천문학 박사학위를 취득했습니다.
            일본 노베야마우주전파관측소 객원연구원을 거쳐 한국천문연구원에서 전파망원경을 인공전파의
            간섭으로부터 보호하기 위한 정책 마련에 힘써 왔습니다.
          </p>
          <p>
            우주를 관측하는 일은 보이지 않는 신호를 붙잡아 진실에 가까워지는 일입니다. 이 아카이브는
            그런 연구자의 태도가 건강과 삶의 문제로 이어진 기록입니다. 유행이나 단정이 아니라 원문,
            맥락, 출처를 남겨 독자가 스스로 확인할 수 있게 하는 것, 그것이 이 지식서재가 지키려는
            건강과 진실의 방향입니다.
          </p>
        </article>

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
      </section>
    </PageShell>
  );
}

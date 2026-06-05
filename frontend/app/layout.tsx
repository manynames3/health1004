import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "건강1004 지식서재",
  description: "증상, 음식, 질환, 식품첨가물, 생활습관으로 찾아보는 Korean natural health archive"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>
        {children}
        <footer className="site-footer">©2026 SUPREME AI VENTURES LLC</footer>
      </body>
    </html>
  );
}

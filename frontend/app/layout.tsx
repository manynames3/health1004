import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Korean PDF RAG Search",
  description: "Grounded Korean/English search over manually ingested PDF newsletters"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}

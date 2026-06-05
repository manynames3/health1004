import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Health1004 | Korean Natural Health PDF Intelligence",
  description: "Citation-first search over the Korean Health1004 natural-health PDF archive"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}

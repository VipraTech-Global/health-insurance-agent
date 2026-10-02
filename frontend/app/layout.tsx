import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "CoverGuide — cited policy comparisons",
  description: "Local health insurance comparison demo",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}


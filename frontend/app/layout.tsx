import type { Metadata } from "next";
import "./styles.css";
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: "CoverGuide — evidence-first insurance advice",
  description: "Local health insurance advisory pilot",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}


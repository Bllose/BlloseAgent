import type { Metadata } from "next";
import { ChatProvider } from "@/context/ChatContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "BlloseAgent",
  description: "AI Agent Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        <ChatProvider>{children}</ChatProvider>
      </body>
    </html>
  );
}

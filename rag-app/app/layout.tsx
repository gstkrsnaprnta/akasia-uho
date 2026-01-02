import type { Metadata } from "next";
import { Inter, Roboto_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/ui/sidebar";

const fontSans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const fontMono = Roboto_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "AKASIA v1.0 - Asisten Akademik UHO",
  description: "Asisten Akademik Berbasis AI untuk Universitas Halu Oleo",
};

import { ChatProvider } from "@/components/chat-provider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${fontSans.variable} ${fontMono.variable} antialiased aurora-bg min-h-screen`} suppressHydrationWarning>
        <ChatProvider>
          <Sidebar />
          <main className="md:pl-64 min-h-screen relative z-10">
            {children}
          </main>
        </ChatProvider>
      </body>
    </html>
  );
}

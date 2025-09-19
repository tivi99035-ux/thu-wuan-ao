import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Seed-VC CPU - Hệ Thống Chuyển Đổi Giọng Nói",
  description: "Hệ thống chuyển đổi giọng nói tối ưu CPU cho xử lý âm thanh thời gian thực",
  keywords: ["chuyển đổi giọng nói", "xử lý âm thanh", "AI", "máy học", "tối ưu CPU"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
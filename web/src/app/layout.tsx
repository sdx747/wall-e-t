import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { QueryProvider } from "@/providers/query-provider";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Wall-E-T | Trading Dashboard",
  description: "Algorithmic trading dashboard for Wall-E-T",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <QueryProvider>
          <Sidebar />
          <div className="lg:pl-60">
            <Header />
            <main className="min-h-[calc(100vh-3.5rem)] p-6 lg:p-8">
              {children}
            </main>
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}

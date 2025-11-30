import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "./contexts/AuthContext";
import { ViewLimitProvider } from "./contexts/ViewLimitContext";
import LayoutWrapper from "./components/LayoutWrapper";
import DonationModal from "./components/DonationModal";

export const metadata: Metadata = {
  title: "아작 (주식 한입)",
  description: "AI가 분석하는 주식 투자 도우미",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className="bg-gray-50">
        <AuthProvider>
          <ViewLimitProvider>
            <LayoutWrapper>{children}</LayoutWrapper>
            <DonationModal />
          </ViewLimitProvider>
        </AuthProvider>
      </body>
    </html>
  );
}

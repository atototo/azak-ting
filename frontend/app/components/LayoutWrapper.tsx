"use client";

import { usePathname } from "next/navigation";
import { useAuth } from "@/app/contexts/AuthContext";
import Navigation from "./Navigation";
import BetaNoticeBanner from "./BetaNoticeBanner";
import PredictionStatusBanner from "./PredictionStatusBanner";
import ViewLimitBanner from "./ViewLimitBanner";
import Footer from "./Footer";

/**
 * 레이아웃 래퍼 컴포넌트
 *
 * 인증 상태와 현재 경로에 따라 네비게이션과 배너를 조건부로 렌더링합니다.
 * 퍼블릭 페이지(대시보드, 종목)에서는 비로그인 사용자도 네비게이션을 볼 수 있습니다.
 */
export default function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { loading, isAuthenticated } = useAuth();

  // 로그인 페이지와 프리뷰 페이지에서는 네비게이션과 배너를 숨김
  const isLoginPage = pathname === "/login";
  const isPreviewPage = pathname.startsWith("/preview/");

  // 퍼블릭 페이지 (로그인 없이도 접근 가능)
  const isPublicPage =
    pathname === "/" ||
    pathname === "/stocks" ||
    pathname.startsWith("/stocks/");

  // 네비게이션 표시 조건: 로그인 페이지/프리뷰 페이지가 아니고, (로그인됨 OR 퍼블릭 페이지)
  const shouldShowNavigation = !isLoginPage && !isPreviewPage && (isAuthenticated || isPublicPage);

  // 로딩 중에는 스피너 표시
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
          <p className="mt-4 text-gray-400">로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {shouldShowNavigation && (
        <>
          <Navigation />
          <BetaNoticeBanner />
          <PredictionStatusBanner />
          <ViewLimitBanner />
        </>
      )}
      {children}
      <Footer />
    </>
  );
}

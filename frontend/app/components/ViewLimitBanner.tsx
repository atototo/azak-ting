"use client";

import { useViewLimit } from "../contexts/ViewLimitContext";
import { useAuth } from "../contexts/AuthContext";
import { Coffee, Eye } from "lucide-react";
import Link from "next/link";

/**
 * 조회 제한 안내 배너
 *
 * 비로그인 사용자에게 남은 무료 조회 횟수를 표시합니다.
 */
export default function ViewLimitBanner() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { remainingViews, viewedCount, dailyLimit, isLimitReached } = useViewLimit();

  // 로딩 중이거나 로그인한 사용자는 배너 표시 안 함
  if (authLoading || isAuthenticated) return null;

  // 제한에 도달한 경우
  if (isLimitReached) {
    return (
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Coffee className="w-5 h-5" />
              <span className="font-medium">
                오늘의 무료 조회를 모두 사용했습니다
              </span>
            </div>
            <div className="flex items-center gap-3">
              <a
                href="https://buymeacoffee.com/atototo"
                target="_blank"
                rel="noopener noreferrer"
                className="bg-white text-amber-600 hover:bg-amber-50 px-4 py-1.5 rounded-full text-sm font-bold transition"
              >
                후원하기
              </a>
              <Link
                href="/login"
                className="text-white/90 hover:text-white text-sm underline"
              >
                로그인
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 남은 조회 횟수 표시
  return (
    <div className="bg-amber-50 border-b border-amber-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2 text-amber-800">
            <Eye className="w-4 h-4" />
            <span className="text-sm">
              무료 종목 상세 조회{" "}
              <strong>{remainingViews}건</strong> 남음
              <span className="text-amber-600 ml-1">
                ({viewedCount}/{dailyLimit})
              </span>
            </span>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="https://buymeacoffee.com/atototo"
              target="_blank"
              rel="noopener noreferrer"
              className="text-amber-700 hover:text-amber-900 text-sm font-medium flex items-center gap-1"
            >
              <Coffee className="w-4 h-4" />
              후원하면 무제한
            </a>
            <Link
              href="/login"
              className="text-amber-600 hover:text-amber-800 text-sm"
            >
              로그인
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

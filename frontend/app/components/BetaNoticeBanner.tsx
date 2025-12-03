"use client";

import { useState, useEffect } from "react";
import { X, FlaskConical } from "lucide-react";

/**
 * 베타 서비스 안내 배너
 *
 * 개인 프로젝트로 서버가 불안정할 수 있다는 양해를 구하는 배너입니다.
 * 닫기 버튼으로 숨길 수 있으며, 세션 동안 유지됩니다.
 */
export default function BetaNoticeBanner() {
  const [dismissed, setDismissed] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // sessionStorage에서 닫기 상태 확인 (새로고침해도 유지, 탭 닫으면 초기화)
    const isDismissed = sessionStorage.getItem("betaNoticeDismissed");
    if (isDismissed === "true") {
      setDismissed(true);
    }
  }, []);

  const handleDismiss = () => {
    setDismissed(true);
    sessionStorage.setItem("betaNoticeDismissed", "true");
  };

  // SSR에서는 렌더링하지 않음
  if (!mounted || dismissed) return null;

  return (
    <div className="bg-blue-50 border-b border-blue-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-blue-700">
            <FlaskConical className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm">
              <strong>실험적 프로젝트</strong> · 개인이 운영하는 사이드 프로젝트입니다. 서버가 불안정할 수 있으니 양해 부탁드립니다 🙏
            </span>
          </div>
          <button
            onClick={handleDismiss}
            className="text-blue-500 hover:text-blue-700 p-1 flex-shrink-0"
            aria-label="닫기"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

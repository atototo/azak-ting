"use client";

import { useViewLimit } from "../contexts/ViewLimitContext";
import { X, Coffee, Lock, Cookie } from "lucide-react";
import Link from "next/link";

/**
 * Buy Me a Coffee 링크
 */
const BUYMEACOFFEE_URL = "https://buymeacoffee.com/atototo";

/**
 * 후원 안내 모달 컴포넌트
 *
 * 비로그인 사용자가 하루 무료 조회 제한에 도달했을 때 표시됩니다.
 * 친근한 톤으로 서비스를 소개하고 후원을 유도합니다.
 */
export default function DonationModal() {
  const { showDonationModal, closeDonationModal, viewedCount, dailyLimit } = useViewLimit();

  if (!showDonationModal) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 배경 오버레이 */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={closeDonationModal}
      />

      {/* 모달 컨텐츠 */}
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 overflow-hidden">
        {/* 헤더 */}
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-8 text-white text-center">
          <div className="flex justify-center mb-3">
            <div className="bg-white/20 rounded-full p-3">
              <Lock className="w-8 h-8" />
            </div>
          </div>
          <h2 className="text-xl font-bold mb-2">
            오늘의 무료 조회를 모두 사용했습니다
          </h2>
          <p className="text-amber-100 text-sm">
            {viewedCount}/{dailyLimit}건 조회 완료
          </p>
        </div>

        {/* 닫기 버튼 */}
        <button
          onClick={closeDonationModal}
          className="absolute top-4 right-4 text-white/80 hover:text-white transition"
        >
          <X className="w-6 h-6" />
        </button>

        {/* 본문 */}
        <div className="px-6 py-6">
          {/* 서비스 소개 */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <Cookie className="w-5 h-5 text-amber-600" />
              <h3 className="font-bold text-gray-900">아작(Azak) 소개</h3>
            </div>
            <p className="text-gray-600 text-sm leading-relaxed">
              10분마다 시장 동향을 파악하고, 여러 AI 모델이 종목을 분석합니다.
              같은 데이터를 보고도 AI마다 다른 판단을 내리는 게 흥미롭습니다.
            </p>
            <p className="text-gray-500 text-sm mt-2">
              거창한 스타트업이 아니라 실험용 프로젝트입니다.
              회사 일 끝나고 짬날 때마다 붙여보는 사이드 실험 수준입니다.
            </p>
          </div>

          {/* 후원 안내 */}
          <div className="bg-amber-50 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 mb-2">
              <Coffee className="w-5 h-5 text-amber-700" />
              <h3 className="font-bold text-amber-900">커피 한 잔의 응원</h3>
            </div>
            <p className="text-amber-800 text-sm leading-relaxed mb-3">
              이 서비스가 도움이 됐다면 커피 한 잔 사주시면 감사하겠습니다.
              진짜 엄청난 동기부여가 됩니다.
            </p>
            <p className="text-amber-700 text-sm">
              감사의 의미로 <strong>체험용 계정 코드</strong>를 이메일로 제공해드립니다.
              서버비랑 데이터 구매비로만 조용히 잘 쓰겠습니다.
            </p>
          </div>

          {/* 버튼들 */}
          <div className="space-y-3">
            <a
              href={BUYMEACOFFEE_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 w-full bg-amber-500 hover:bg-amber-600 text-white font-bold py-3 px-4 rounded-lg transition"
            >
              <Coffee className="w-5 h-5" />
              Buy Me a Coffee
            </a>

            <div className="flex gap-3">
              <Link
                href="/login"
                className="flex-1 text-center bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2.5 px-4 rounded-lg transition text-sm"
              >
                로그인
              </Link>
              <button
                onClick={closeDonationModal}
                className="flex-1 text-center bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2.5 px-4 rounded-lg transition text-sm"
              >
                나중에
              </button>
            </div>
          </div>
        </div>

        {/* 푸터 */}
        <div className="bg-gray-50 px-6 py-4 text-center">
          <p className="text-xs text-gray-500">
            내일이 되면 무료 조회가 다시 충전됩니다
          </p>
        </div>
      </div>
    </div>
  );
}

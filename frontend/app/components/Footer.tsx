"use client";

export default function Footer() {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* 면책 조항 */}
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 rounded-r-lg">
            <h3 className="text-lg font-bold text-gray-900 mb-3">⚠️ 투자 유의사항</h3>
            <div className="space-y-3 text-sm text-gray-700">
              <p className="leading-relaxed">
                아작이 제공하는 모든 정보는 <strong>투자 참고용으로만 제공</strong>되며
                특정 주식 매매를 추천하거나 투자 결정의 유일한 근거로 사용되어서는 안 됩니다.
              </p>
              <p className="leading-relaxed">
                모든 투자에는 <strong>원금 손실 위험</strong>이 따르므로 투자 전 개인의
                투자목표와 위험성향을 신중히 고려하여 본인 판단에 따라 투자하시기 바라며,
                당사는 제공된 정보로 인한 투자 결과에 대해 <strong>법적 책임을 지지 않습니다</strong>.
              </p>
              <p className="text-xs text-gray-600 pt-2 border-t border-yellow-200">
                AI 분석은 과거 데이터와 패턴을 기반으로 하며, 미래 수익을 보장하지 않습니다.
                투자의 최종 결정은 반드시 투자자 본인의 판단과 책임하에 이루어져야 합니다.
              </p>
            </div>
          </div>

          {/* 데이터 출처 */}
          <div className="text-center text-sm text-gray-600">
            <p className="font-medium mb-1">📊 Data Powered by</p>
            <p>한국거래소(KRX), 금융감독원 전자공시시스템(DART), 한국투자증권 API</p>
          </div>

          {/* 저작권 정보 */}
          <div className="pt-6 border-t border-gray-300 text-center">
            <p className="text-sm text-gray-600">
              © {new Date().getFullYear()} 아작 (주식 한입). All rights reserved.
            </p>
            <p className="text-xs text-gray-500 mt-2">
              본 서비스는 정보 제공 목적으로만 운영되며, 금융투자업 라이선스를 보유하지 않습니다.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}

"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import StockChart from "./StockChart";
import NewsImpact from "./NewsImpact";

// Types
interface StockDetailData {
  stock: {
    code: string;
    name: string;
  };
  current_price: {
    price: number;
    change_amount: number;
    change_rate: number;
    open?: number;
    high?: number;
    low?: number;
    date?: string;
  } | null;
  analysis_summary: {
    ab_test_enabled?: boolean;
    model_a?: AnalysisSummary;
    model_b?: AnalysisSummary;
    confidence_level?: 'high' | 'medium' | 'low';
    data_sources_used?: string[];
    limitations?: string[];
    overall_summary?: string;
    short_term_scenario?: string;
    medium_term_scenario?: string;
    long_term_scenario?: string;
    risk_factors?: string[];
    opportunity_factors?: string[];
    recommendation?: string;
    meta?: {
      based_on_prediction_count: number;
      last_updated: string;
    };
  } | null;
  statistics: {
    total_news: number;
    total_notifications: number;
  };
  recent_news: RecentNews[];
}

interface AnalysisSummary {
  confidence_level?: 'high' | 'medium' | 'low';
  data_sources_used?: string[];
  limitations?: string[];
  overall_summary?: string;
  short_term_scenario?: string;
  medium_term_scenario?: string;
  long_term_scenario?: string;
  risk_factors?: string[];
  opportunity_factors?: string[];
  recommendation?: string;
}

interface RecentNews {
  id: number;
  source: string;
  published_at: string;
  notified_at?: string;
  prediction?: {
    sentiment_direction?: 'positive' | 'negative' | 'neutral';
    impact_score?: number;
    reasoning?: string;
  };
}

interface ABTestConfig {
  model_a: { name: string };
  model_b: { name: string };
}

interface StockDetailViewProps {
  data: StockDetailData;
  abConfig?: ABTestConfig | null;
  showBackButton?: boolean;
  showForceUpdate?: boolean;
  onForceUpdate?: () => void;
  updating?: boolean;
  updateMessage?: { type: 'success' | 'error'; text: string } | null;
}

// Data Source Badges Component
function DataSourceBadges({ dataSources }: { dataSources: string[] }) {
  const sourceLabels: Record<string, string> = {
    'stock_prices': '주가·거래량',
    'investor_flow': '투자자 수급',
    'financial_metrics': '재무 지표',
    'company_info': '기업 정보',
    'technical_indicators': '기술적 지표',
    'market_trends': '시장 동향',
  };

  return (
    <div className="flex flex-wrap gap-2">
      {Object.keys(sourceLabels).map((key) => {
        const isUsed = dataSources.includes(key);
        return (
          <span
            key={key}
            className={`px-3 py-1 rounded-full text-xs font-medium border ${
              isUsed
                ? 'bg-blue-100 text-blue-700 border-blue-300'
                : 'bg-gray-100 text-gray-400 border-gray-300'
            }`}
          >
            {isUsed ? '✅' : '❌'} {sourceLabels[key]}
          </span>
        );
      })}
    </div>
  );
}

export default function StockDetailView({
  data,
  abConfig,
  showBackButton = false,
  showForceUpdate = false,
  onForceUpdate,
  updating = false,
  updateMessage = null,
}: StockDetailViewProps) {
  const [isMounted, setIsMounted] = useState(false);
  const [showConfidenceInfo, setShowConfidenceInfo] = useState(false);

  const { stock, current_price, analysis_summary, statistics, recent_news } = data;

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Helper function to render model summary (for A/B test)
  const renderModelSummary = (
    summary: AnalysisSummary,
    modelName: string,
    bgClass: string,
    borderClass: string
  ) => (
    <div className={`flex-1 p-6 rounded-xl border-2 ${bgClass} ${borderClass}`}>
      <h3 className="text-lg font-bold mb-4 text-gray-800">{modelName}</h3>

      {/* 신뢰도 */}
      {summary.confidence_level && (
        <div className="mb-4">
          <span className="text-sm font-medium text-gray-700">신뢰도: </span>
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium ${
              summary.confidence_level === 'high'
                ? 'bg-green-100 text-green-700'
                : summary.confidence_level === 'medium'
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {summary.confidence_level === 'high' && '높음 🟢'}
            {summary.confidence_level === 'medium' && '중간 🟡'}
            {summary.confidence_level === 'low' && '낮음 🔴'}
          </span>
        </div>
      )}

      {/* 데이터 소스 배지 */}
      {summary.data_sources_used && (
        <div className="mb-4">
          <h4 className="text-xs font-bold text-gray-700 mb-2">사용된 데이터:</h4>
          <DataSourceBadges dataSources={summary.data_sources_used} />
        </div>
      )}

      {/* 제한사항 */}
      {summary.limitations && summary.limitations.length > 0 && (
        <div className="mb-4 bg-yellow-50 border-l-2 border-yellow-400 p-3 rounded">
          <h4 className="text-xs font-bold text-yellow-800 mb-2 flex items-center">
            <span className="mr-1">⚠️</span> 제한사항
          </h4>
          <ul className="space-y-1">
            {summary.limitations.map((limitation, idx) => (
              <li key={idx} className="text-xs text-yellow-700 flex items-start">
                <span className="mr-1">•</span>
                <span>{limitation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 종합 의견 */}
      {summary.overall_summary && (
        <div className="mb-4">
          <h4 className="text-sm font-bold text-gray-700 mb-2">📋 종합 의견</h4>
          <div className="bg-white rounded p-3 border-l-4 border-indigo-400">
            <p className="text-sm text-gray-700 leading-relaxed">{summary.overall_summary}</p>
          </div>
        </div>
      )}

      {/* 기간별 투자 전략 */}
      {(summary.short_term_scenario || summary.medium_term_scenario || summary.long_term_scenario) && (
        <div className="mb-4">
          <h4 className="text-sm font-bold text-gray-700 mb-2">📅 기간별 전략</h4>
          <div className="space-y-2">
            {summary.short_term_scenario && (
              <div className="bg-white rounded p-2 border-l-2 border-red-400">
                <h5 className="text-xs font-bold text-red-700 mb-1">🔹 단기</h5>
                <p className="text-xs text-gray-700 leading-relaxed">{summary.short_term_scenario}</p>
              </div>
            )}
            {summary.medium_term_scenario && (
              <div className="bg-white rounded p-2 border-l-2 border-yellow-400">
                <h5 className="text-xs font-bold text-yellow-700 mb-1">🔸 중기</h5>
                <p className="text-xs text-gray-700 leading-relaxed">{summary.medium_term_scenario}</p>
              </div>
            )}
            {summary.long_term_scenario && (
              <div className="bg-white rounded p-2 border-l-2 border-green-400">
                <h5 className="text-xs font-bold text-green-700 mb-1">🔶 장기</h5>
                <p className="text-xs text-gray-700 leading-relaxed">{summary.long_term_scenario}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 리스크 및 기회 요인 */}
      {((summary.risk_factors && summary.risk_factors.length > 0) ||
        (summary.opportunity_factors && summary.opportunity_factors.length > 0)) && (
        <div className="mb-4">
          <h4 className="text-sm font-bold text-gray-700 mb-2">⚖️ 리스크 & 기회</h4>
          <div className="space-y-2">
            {summary.risk_factors && summary.risk_factors.length > 0 && (
              <div className="bg-white rounded p-2 border-l-2 border-orange-400">
                <h5 className="text-xs font-bold text-orange-700 mb-1">⚠️ 리스크</h5>
                <ul className="space-y-1">
                  {summary.risk_factors.map((risk, index) => (
                    <li key={index} className="text-xs text-gray-700 flex items-start">
                      <span className="mr-1 text-orange-500">•</span>
                      <span>{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {summary.opportunity_factors && summary.opportunity_factors.length > 0 && (
              <div className="bg-white rounded p-2 border-l-2 border-teal-400">
                <h5 className="text-xs font-bold text-teal-700 mb-1">💡 기회</h5>
                <ul className="space-y-1">
                  {summary.opportunity_factors.map((opportunity, index) => (
                    <li key={index} className="text-xs text-gray-700 flex items-start">
                      <span className="mr-1 text-teal-500">•</span>
                      <span>{opportunity}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 최종 추천 */}
      {summary.recommendation && (
        <div className="mb-2">
          <h4 className="text-sm font-bold text-gray-700 mb-2">🎯 최종 추천</h4>
          <div className="bg-white rounded p-3 border-l-4 border-purple-400">
            <p className="text-sm text-gray-700 font-medium leading-relaxed">{summary.recommendation}</p>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          {showBackButton && (
            <Link href="/stocks" className="text-blue-600 hover:underline mb-2 inline-block">
              ← 종목 목록
            </Link>
          )}
          <h1 className="text-3xl font-bold text-gray-900">
            {stock.name} ({stock.code})
          </h1>
        </div>

        {/* Current Price Section */}
        {current_price && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">현재가 정보</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <p className="text-sm text-gray-600">현재가</p>
                <p className="text-3xl font-bold text-gray-900">
                  {current_price.price.toLocaleString()}원
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">등락</p>
                <p
                  className={`text-xl font-semibold ${
                    current_price.change_rate >= 0 ? "text-red-600" : "text-blue-600"
                  }`}
                >
                  {current_price.change_rate >= 0 ? "▲" : "▼"}{" "}
                  {Math.abs(current_price.change_rate)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">시가</p>
                <p className="text-xl font-semibold text-gray-700">
                  {current_price.open ? current_price.open.toLocaleString() : '-'}원
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">고가</p>
                <p className="text-xl font-semibold text-red-600">
                  {current_price.high ? current_price.high.toLocaleString() : '-'}원
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">저가</p>
                <p className="text-xl font-semibold text-blue-600">
                  {current_price.low ? current_price.low.toLocaleString() : '-'}원
                </p>
              </div>
            </div>
            {isMounted && current_price.date && (
              <p className="text-sm text-gray-500 mt-4">
                기준일: {new Date(current_price.date).toLocaleDateString("ko-KR")}
              </p>
            )}
          </div>
        )}

        {/* Stock Price Chart */}
        <StockChart stockCode={stock.code} />

        {/* LLM-Generated Investment Summary - A/B Test Support */}
        {analysis_summary && (
          <div className="bg-gradient-to-br from-slate-50 to-blue-50 rounded-2xl shadow-2xl p-8 mb-6 border border-indigo-100">
            {/* 헤더 */}
            <div className="mb-8 pb-6 border-b-2 border-indigo-200">
              <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-blue-600 bg-clip-text text-transparent flex items-center">
                  <span className="mr-3 text-3xl">🤖</span> AI 종합 투자 리포트
                  {analysis_summary.ab_test_enabled && (
                    <span className="ml-4 text-sm font-normal text-purple-600 bg-purple-100 px-3 py-1 rounded-full">
                      A/B Testing
                    </span>
                  )}
                </h2>
                {showForceUpdate && onForceUpdate && (
                  <button
                    onClick={onForceUpdate}
                    disabled={updating}
                    className={`px-4 py-2 rounded-md font-medium text-sm transition-colors ${
                      updating
                        ? "bg-gray-400 cursor-not-allowed text-white"
                        : "bg-indigo-600 hover:bg-indigo-700 text-white shadow-md"
                    }`}
                  >
                    {updating ? "업데이트 중..." : "🔄 리포트 업데이트"}
                  </button>
                )}
              </div>

              {/* 업데이트 메시지 */}
              {updateMessage && (
                <div className={`mt-4 p-3 rounded-md ${
                  updateMessage.type === 'success'
                    ? 'bg-green-50 border border-green-200 text-green-800'
                    : 'bg-red-50 border border-red-200 text-red-800'
                }`}>
                  <p className="text-sm font-medium">{updateMessage.text}</p>
                </div>
              )}
            </div>

            {/* A/B Test Mode: Side-by-side comparison */}
            {analysis_summary.ab_test_enabled && analysis_summary.model_a && analysis_summary.model_b ? (
              <div className="flex flex-col md:flex-row gap-6">
                {/* Model A */}
                {renderModelSummary(
                  analysis_summary.model_a,
                  abConfig ? `Model A (${abConfig.model_a.name})` : "Model A",
                  "bg-blue-50",
                  "border-blue-200"
                )}

                {/* Model B */}
                {renderModelSummary(
                  analysis_summary.model_b,
                  abConfig ? `Model B (${abConfig.model_b.name})` : "Model B",
                  "bg-green-50",
                  "border-green-200"
                )}
              </div>
            ) : (
              // Single Model Mode
              <div>
                {/* 신뢰도 배지 */}
                {analysis_summary.confidence_level && (
                  <div className="mb-6">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-base font-medium text-gray-700">분석 신뢰도:</span>
                      <span className={`px-4 py-2 rounded-full text-sm font-medium border ${
                        analysis_summary.confidence_level === 'high'
                          ? 'bg-green-100 text-green-700 border-green-300'
                          : analysis_summary.confidence_level === 'medium'
                          ? 'bg-yellow-100 text-yellow-700 border-yellow-300'
                          : 'bg-red-100 text-red-700 border-red-300'
                      }`}>
                        {analysis_summary.confidence_level === 'high' && '높음 🟢'}
                        {analysis_summary.confidence_level === 'medium' && '중간 🟡'}
                        {analysis_summary.confidence_level === 'low' && '낮음 🔴'}
                      </span>
                      <button
                        onClick={() => setShowConfidenceInfo(!showConfidenceInfo)}
                        className="text-gray-500 hover:text-gray-700 transition-colors"
                        title="신뢰도 기준 보기"
                      >
                        <span className="text-base font-bold">ⓘ</span>
                      </button>
                    </div>

                    {/* 신뢰도 기준 설명 */}
                    {showConfidenceInfo && (
                      <div className="mt-2 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-gray-700">
                        <p className="font-semibold mb-2">📊 신뢰도 평가 기준 (AI 모델이 자동 판단)</p>
                        <p className="mb-2 text-sm text-gray-600">
                          AI 모델이 6가지 데이터 소스의 <strong>품질과 완전도</strong>를 종합 평가합니다:
                        </p>
                        <ul className="space-y-1 ml-4">
                          <li>• <strong className="text-green-700">높음 🟢</strong>: 모든 데이터가 충분한 양과 우수한 품질로 확보됨</li>
                          <li>• <strong className="text-yellow-700">중간 🟡</strong>: 데이터가 있으나 일부 부족하거나 품질이 제한적임</li>
                          <li>• <strong className="text-red-700">낮음 🔴</strong>: 필수 데이터가 많이 부족하여 분석의 한계가 있음</li>
                        </ul>
                        <div className="mt-3 pt-3 border-t border-blue-300">
                          <p className="text-sm text-gray-600">
                            💡 <strong>데이터 소스 ✅ 표시</strong>는 존재 여부만 나타내며, 신뢰도는 AI가 품질까지 평가합니다
                          </p>
                          <p className="mt-2 text-xs text-gray-500">
                            * 6가지 데이터 소스: 주가·거래량, 투자자 수급, 재무 지표, 기업 정보, 기술적 지표, 시장 동향
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 데이터 소스 배지 */}
                {analysis_summary.data_sources_used && (
                  <div className="mb-6">
                    <h4 className="text-base font-bold text-gray-700 mb-2">사용된 데이터 소스:</h4>
                    <DataSourceBadges dataSources={analysis_summary.data_sources_used} />
                  </div>
                )}

                {/* 제한사항 섹션 */}
                {analysis_summary.limitations && analysis_summary.limitations.length > 0 && (
                  <div className="mb-6 bg-yellow-50 border-l-4 border-yellow-400 p-5 rounded-lg">
                    <h4 className="text-base font-bold text-yellow-800 mb-3 flex items-center">
                      <span className="mr-2">⚠️</span> 분석 제한사항
                    </h4>
                    <ul className="space-y-2">
                      {analysis_summary.limitations.map((limitation, idx) => (
                        <li key={idx} className="text-sm text-yellow-700 flex items-start">
                          <span className="mr-2">•</span>
                          <span>{limitation}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Section 1: 종합 의견 */}
                {analysis_summary.overall_summary && (
                  <div className="mb-10">
                    <div className="mb-4">
                      <h3 className="text-xl font-bold text-gray-900 flex items-center">
                        <span className="mr-3 text-2xl">📋</span> 종합 의견
                      </h3>
                    </div>
                    <div className="p-6 bg-white rounded-xl shadow-lg border-l-4 border-indigo-500">
                      <p className="text-gray-700 leading-relaxed text-base">{analysis_summary.overall_summary}</p>
                    </div>
                  </div>
                )}

                {/* Section 2: 기간별 투자 전략 */}
                {(analysis_summary.short_term_scenario || analysis_summary.medium_term_scenario || analysis_summary.long_term_scenario) && (
                  <div className="mb-10">
                    <div className="mb-4">
                      <h3 className="text-xl font-bold text-gray-900 flex items-center">
                        <span className="mr-3 text-2xl">📅</span> 기간별 투자 전략
                      </h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                      {/* Short-term */}
                      {analysis_summary.short_term_scenario && (
                        <div className="bg-white rounded-xl p-5 shadow-md hover:shadow-xl transition-shadow border-l-4 border-red-400">
                          <div className="flex items-center mb-3">
                            <span className="text-2xl mr-2">🔹</span>
                            <h4 className="text-base font-bold text-red-700">단기 (1일~1주)</h4>
                          </div>
                          <p className="text-sm text-gray-700 leading-relaxed">
                            {analysis_summary.short_term_scenario}
                          </p>
                        </div>
                      )}

                      {/* Medium-term */}
                      {analysis_summary.medium_term_scenario && (
                        <div className="bg-white rounded-xl p-5 shadow-md hover:shadow-xl transition-shadow border-l-4 border-yellow-400">
                          <div className="flex items-center mb-3">
                            <span className="text-2xl mr-2">🔸</span>
                            <h4 className="text-base font-bold text-yellow-700">중기 (1주~1개월)</h4>
                          </div>
                          <p className="text-sm text-gray-700 leading-relaxed">
                            {analysis_summary.medium_term_scenario}
                          </p>
                        </div>
                      )}

                      {/* Long-term */}
                      {analysis_summary.long_term_scenario && (
                        <div className="bg-white rounded-xl p-5 shadow-md hover:shadow-xl transition-shadow border-l-4 border-green-400">
                          <div className="flex items-center mb-3">
                            <span className="text-2xl mr-2">🔶</span>
                            <h4 className="text-base font-bold text-green-700">장기 (1개월 이상)</h4>
                          </div>
                          <p className="text-sm text-gray-700 leading-relaxed">
                            {analysis_summary.long_term_scenario}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Section 3: 리스크 및 기회 요인 */}
                {((analysis_summary.risk_factors && analysis_summary.risk_factors.length > 0) ||
                  (analysis_summary.opportunity_factors && analysis_summary.opportunity_factors.length > 0)) && (
                  <div className="mb-10">
                    <div className="mb-4">
                      <h3 className="text-xl font-bold text-gray-900 flex items-center">
                        <span className="mr-3 text-2xl">⚖️</span> 리스크 및 기회 요인
                      </h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                      {/* Risk Factors */}
                      {analysis_summary.risk_factors && analysis_summary.risk_factors.length > 0 && (
                        <div className="bg-white rounded-xl p-5 shadow-md border-l-4 border-orange-400">
                          <h4 className="text-lg font-bold text-orange-700 mb-4 flex items-center">
                            <span className="mr-2 text-xl">⚠️</span> 리스크 요인
                          </h4>
                          <ul className="space-y-3">
                            {analysis_summary.risk_factors.map((risk, index) => (
                              <li key={index} className="text-sm text-gray-700 flex items-start">
                                <span className="mr-2 text-orange-500 flex-shrink-0 font-bold">•</span>
                                <span className="leading-relaxed">{risk}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Opportunity Factors */}
                      {analysis_summary.opportunity_factors && analysis_summary.opportunity_factors.length > 0 && (
                        <div className="bg-white rounded-xl p-5 shadow-md border-l-4 border-teal-400">
                          <h4 className="text-lg font-bold text-teal-700 mb-4 flex items-center">
                            <span className="mr-2 text-xl">💡</span> 기회 요인
                          </h4>
                          <ul className="space-y-3">
                            {analysis_summary.opportunity_factors.map((opportunity, index) => (
                              <li key={index} className="text-sm text-gray-700 flex items-start">
                                <span className="mr-2 text-teal-500 flex-shrink-0 font-bold">•</span>
                                <span className="leading-relaxed">{opportunity}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Section 4: 최종 추천 */}
                {analysis_summary.recommendation && (
                  <div className="mb-6">
                    <div className="mb-4">
                      <h3 className="text-xl font-bold text-gray-900 flex items-center">
                        <span className="mr-3 text-2xl">🎯</span> 최종 추천
                      </h3>
                    </div>
                    <div className="bg-white rounded-xl p-6 shadow-xl border-2 border-indigo-200">
                      <p className="text-gray-700 font-medium leading-relaxed text-base">
                        {analysis_summary.recommendation}
                      </p>
                    </div>
                  </div>
                )}

                {/* Meta Info */}
                {analysis_summary.meta && (
                  <div className="mt-6 pt-5 border-t border-gray-300">
                    <div className="flex items-center justify-center text-sm text-gray-500">
                      <span className="mr-2">📊</span>
                      <span className="font-medium">분석 기준: {analysis_summary.meta.based_on_prediction_count}건의 예측</span>
                      {isMounted && analysis_summary.meta.last_updated && (() => {
                        const lastUpdated = new Date(analysis_summary.meta.last_updated);
                        const now = new Date();
                        const diffMs = now.getTime() - lastUpdated.getTime();
                        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                        const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

                        let timeAgo = '';
                        if (diffHours > 0) {
                          timeAgo = `${diffHours}시간 ${diffMinutes}분 전`;
                        } else {
                          timeAgo = `${diffMinutes}분 전`;
                        }

                        const isStale = diffHours >= 5;

                        return (
                          <>
                            <span className="mx-2">|</span>
                            <span className={isStale ? "font-bold text-orange-600" : ""}>
                              🕐 리포트 생성: {lastUpdated.toLocaleString("ko-KR")} ({timeAgo})
                            </span>
                          </>
                        );
                      })()}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Common Meta Info Footer for A/B Test */}
            {analysis_summary.ab_test_enabled && analysis_summary.meta && (
              <div className="mt-6 pt-5 border-t border-gray-300">
                <div className="flex items-center justify-center text-sm text-gray-500">
                  <span className="mr-2">📊</span>
                  <span className="font-medium">분석 기준: {analysis_summary.meta.based_on_prediction_count}건의 예측</span>
                  {isMounted && analysis_summary.meta.last_updated && (() => {
                    const lastUpdated = new Date(analysis_summary.meta.last_updated);
                    const now = new Date();
                    const diffMs = now.getTime() - lastUpdated.getTime();
                    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

                    let timeAgo = '';
                    if (diffHours > 0) {
                      timeAgo = `${diffHours}시간 ${diffMinutes}분 전`;
                    } else {
                      timeAgo = `${diffMinutes}분 전`;
                    }

                    const isStale = diffHours >= 5;

                    return (
                      <>
                        <span className="mx-2">|</span>
                        <span className={isStale ? "font-bold text-orange-600" : ""}>
                          🕐 리포트 생성: {lastUpdated.toLocaleString("ko-KR")} ({timeAgo})
                        </span>
                      </>
                    );
                  })()}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Statistics Section */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">📊 시장 동향 통계</h2>
          <div className="grid grid-cols-2 gap-6">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-3xl font-bold text-green-600">
                {statistics.total_news}
              </div>
              <div className="text-sm text-gray-600 mt-1">분석 건수</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-3xl font-bold text-purple-600">
                {statistics.total_notifications}
              </div>
              <div className="text-sm text-gray-600 mt-1">알림 전송</div>
            </div>
          </div>
        </div>

        {/* Recent Market Analysis Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">📊 최근 시장 동향 & AI 분석</h2>
          {recent_news.length > 0 ? (
            <div className="space-y-4">
              {recent_news.map((news) => (
                <div
                  key={news.id}
                  className="border border-gray-200 rounded-lg overflow-hidden"
                >
                  <div className="p-4 bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          {news.prediction?.sentiment_direction === 'positive' && (
                            <span className="text-lg">📈</span>
                          )}
                          {news.prediction?.sentiment_direction === 'negative' && (
                            <span className="text-lg">📉</span>
                          )}
                          {news.prediction?.sentiment_direction === 'neutral' && (
                            <span className="text-lg">➡️</span>
                          )}
                          {!news.prediction?.sentiment_direction && (
                            <span className="text-lg">📊</span>
                          )}
                          <h3 className="font-medium text-gray-900">
                            {news.prediction?.sentiment_direction === 'positive' && '긍정적 시장 시그널'}
                            {news.prediction?.sentiment_direction === 'negative' && '부정적 시장 시그널'}
                            {news.prediction?.sentiment_direction === 'neutral' && '중립적 시장 시그널'}
                            {!news.prediction?.sentiment_direction && '시장 정보'}
                          </h3>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-600">
                          <span>
                            📰 {
                              news.source.includes('DART') || news.source.includes('금융감독')
                                ? '공식공시'
                                : news.source.includes('증권') || news.source.includes('리서치')
                                ? '증권리포트'
                                : '시장 정보'
                            }
                          </span>
                          {isMounted && news.published_at && (
                            <span>
                              🕐 {new Date(news.published_at).toLocaleString("ko-KR")}
                            </span>
                          )}
                        </div>
                      </div>
                      {news.notified_at && (
                        <span className="ml-4 px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                          알림 전송
                        </span>
                      )}
                    </div>

                    {news.prediction && (
                      <div className="mt-4">
                        <NewsImpact prediction={news.prediction} />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>시장 동향 분석이 없습니다</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

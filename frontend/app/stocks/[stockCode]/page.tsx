"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import toast, { Toaster } from 'react-hot-toast';
import StockDetailView from "../../components/StockDetailView";
import { useViewLimit } from "../../contexts/ViewLimitContext";

interface StockPrice {
  close: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  change_rate: number;
  date: string | null;
}

interface ConfidenceBreakdown {
  similar_news_quality?: number | null;
  pattern_consistency?: number | null;
  disclosure_impact?: number | null;
  explanation?: string | null;
}

interface PatternAnalysis {
  avg_1d?: number | null;
  avg_2d?: number | null;
  avg_3d?: number | null;
  avg_5d?: number | null;
  avg_10d?: number | null;
  avg_20d?: number | null;
  max_1d?: number | null;
  min_1d?: number | null;
  count?: number | null;
}

interface RecentNews {
  id: number;
  title: string;
  source: string;
  published_at: string | null;
  notified_at: string | null;
  prediction?: {
    // Epic 3: New impact analysis fields
    sentiment_direction?: string | null;
    sentiment_score?: number | null;
    impact_level?: string | null;
    relevance_score?: number | null;
    urgency_level?: string | null;
    impact_analysis?: string | null;
    reasoning?: string | null;
    // Deprecated fields (backward compatibility)
    direction?: string;
    confidence?: number;
    short_term?: string;
    medium_term?: string;
    long_term?: string;
    confidence_breakdown?: ConfidenceBreakdown;
    pattern_analysis?: PatternAnalysis;
  };
}

interface DirectionDistribution {
  up: number;
  down: number;
  hold: number;
}

interface DataSources {
  market_data: boolean;
  investor_trading: boolean;
  financial_ratios: boolean;
  product_info: boolean;
  technical_indicators: boolean;
  news: boolean;
}

interface SingleModelSummary {
  overall_summary: string;
  short_term_scenario?: string | null;
  medium_term_scenario?: string | null;
  long_term_scenario?: string | null;
  risk_factors: string[];
  opportunity_factors: string[];
  recommendation?: string | null;
  // US-004 메타데이터
  data_sources_used?: DataSources;
  limitations?: string[];
  confidence_level?: 'high' | 'medium' | 'low';
  data_completeness_score?: number;
}

interface ABTestSummary {
  ab_test_enabled: true;
  model_a: SingleModelSummary;
  model_b: SingleModelSummary;
  comparison?: {
    recommendation_match: boolean;
    risk_overlap: string[];
    opportunity_overlap: string[];
  };
}

interface AnalysisSummary {
  // Single model fields (backward compatibility)
  overall_summary?: string;
  short_term_scenario?: string | null;
  medium_term_scenario?: string | null;
  long_term_scenario?: string | null;
  risk_factors?: string[];
  opportunity_factors?: string[];
  recommendation?: string | null;
  statistics?: {
    total_predictions: number;
    up_count: number;
    down_count: number;
    hold_count: number;
    avg_confidence: number | null;
  };
  meta?: {
    last_updated: string | null;
    based_on_prediction_count: number;
  };
  // US-004 메타데이터
  data_sources_used?: DataSources;
  limitations?: string[];
  confidence_level?: 'high' | 'medium' | 'low';
  data_completeness_score?: number;
  // A/B test fields
  ab_test_enabled?: boolean;
  model_a?: SingleModelSummary;
  model_b?: SingleModelSummary;
  comparison?: {
    recommendation_match: boolean;
    risk_overlap: string[];
    opportunity_overlap: string[];
  };
}

interface StockDetail {
  stock_code: string;
  stock_name: string;
  statistics: {
    total_news: number;
    total_notifications: number;
    avg_confidence: number | null;
    direction_distribution: DirectionDistribution | null;
    investment_opinion: string | null;
    opinion_confidence: number | null;
    // Phase 2: 종합 통계
    confidence_breakdown_avg?: ConfidenceBreakdown;
    pattern_analysis_avg?: PatternAnalysis;
  };
  // Phase 2: LLM 기반 AI 투자 분석 요약
  analysis_summary?: AnalysisSummary;
  current_price: StockPrice | null;
  recent_news: RecentNews[];
}

export default function StockDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const stockCode = params.stockCode as string;
  const isPublicPreview = searchParams.get('isPublicPreview') === 'true';

  // 조회 제한 훅
  const { canViewStock, recordView, openDonationModal, remainingViews } = useViewLimit();

  const [stock, setStock] = useState<StockDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);
  const [abConfig, setAbConfig] = useState<{model_a: {name: string}, model_b: {name: string}} | null>(null);
  const [updating, setUpdating] = useState(false);
  const [updateMessage, setUpdateMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [viewRecorded, setViewRecorded] = useState(false);

  // 리포트 완료 알림 추적 (이미 알림 표시한 종목 코드)
  // localStorage에서 이전 알림 기록 불러오기 (새로고침 시에도 유지)
  const notifiedReports = useRef<Set<string>>(
    typeof window !== 'undefined'
      ? new Set(JSON.parse(localStorage.getItem('notifiedReports') || '[]'))
      : new Set()
  );

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // 조회 제한 체크 및 기록
  useEffect(() => {
    if (!stockCode || viewRecorded) return;

    // 조회 가능 여부 체크
    if (!canViewStock(stockCode)) {
      // 제한 도달 - 모달 표시
      openDonationModal();
      setViewRecorded(true);
      return;
    }

    // 조회 기록
    const success = recordView(stockCode);
    setViewRecorded(true);

    if (!success) {
      // 이번 조회로 제한 도달 - 모달은 recordView에서 표시됨
    }
  }, [stockCode, canViewStock, recordView, openDonationModal, viewRecorded]);

  // A/B 설정 가져오기
  useEffect(() => {
    fetch("/api/ab-test/config")
      .then((res) => res.json())
      .then((data) => {
        if (data.model_a && data.model_b) {
          setAbConfig({
            model_a: { name: data.model_a.name },
            model_b: { name: data.model_b.name }
          });
        }
      })
      .catch((err) => {
        console.error("Failed to fetch A/B config:", err);
      });
  }, []);

  // 리포트 생성 상태 폴링 (5초마다)
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch('/api/ab-test/prediction-status');
        const data = await res.json();

        const reportStatus = data.report_status || {};

        // 완료된 리포트 확인
        Object.entries(reportStatus).forEach(([code, info]: [string, any]) => {
          if (info.status === 'completed' && !notifiedReports.current.has(code)) {
            // 아직 알림 표시하지 않은 완료된 리포트

            if (code === stockCode) {
              // 현재 페이지 종목 - 데이터 리페치 + 화면 메시지
              fetchStockData();
              setUpdateMessage({
                type: 'success',
                text: `리포트가 생성되었습니다! (${info.model_count}개 모델)`
              });

              // 5초 후 메시지 제거
              setTimeout(() => {
                setUpdateMessage(null);
              }, 5000);

              toast.success(`${info.stock_name} 리포트 생성 완료!`, {
                duration: 4000,
                position: 'top-right',
              });
            } else {
              // 다른 종목 - toast 알림만
              toast.success(`${info.stock_name} 리포트가 생성되었습니다`, {
                duration: 4000,
                position: 'top-right',
              });
            }

            // 알림 표시 완료 기록 (localStorage에도 저장)
            notifiedReports.current.add(code);
            if (typeof window !== 'undefined') {
              localStorage.setItem(
                'notifiedReports',
                JSON.stringify(Array.from(notifiedReports.current))
              );
            }
          }
        });
      } catch (error) {
        console.error("Failed to fetch report status:", error);
      }
    }, 5000); // 5초마다 폴링

    return () => clearInterval(interval);
  }, [stockCode]);

  useEffect(() => {
    if (!stockCode) return;

    fetch(`/api/stocks/${stockCode}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error("종목을 찾을 수 없습니다");
        }
        return res.json();
      })
      .then((data) => {
        setStock(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch stock detail:", err);
        setError(err.message);
        setLoading(false);
      });
  }, [stockCode]);

  // 종목 데이터 리페치 함수
  const fetchStockData = async () => {
    if (!stockCode) return;

    try {
      const response = await fetch(`/api/stocks/${stockCode}`);
      if (response.ok) {
        const data = await response.json();
        setStock(data);
      }
    } catch (error) {
      console.error("Failed to fetch stock data:", error);
    }
  };

  // 리포트 강제 업데이트 핸들러 (비동기 - 즉시 리턴)
  const handleForceUpdate = async () => {
    if (!stockCode) return;

    setUpdating(true);
    setUpdateMessage(null);

    try {
      const response = await fetch(`/api/reports/force-update/${stockCode}`, {
        method: "POST",
        cache: 'no-store',
      });

      const result = await response.json();

      if (result.success && result.status === 'processing') {
        // 백그라운드 작업 시작 성공
        let message = `${result.stock_name || '종목'} 리포트 생성 중... 완료되면 자동으로 알림을 표시합니다.`;

        // 할당량 정보가 있으면 추가
        if (result.quota_info) {
          message += ` (남은 할당량: ${result.quota_info.remaining}/${result.quota_info.total})`;
        }

        setUpdateMessage({
          type: 'success',
          text: message
        });

        // 5초 후 메시지 제거
        setTimeout(() => {
          setUpdateMessage(null);
        }, 5000);
      } else {
        // 에러 케이스 처리
        let errorMessage = result.message || '리포트 업데이트 요청 실패';

        // 할당량 초과 시 특별 처리
        if (result.error === 'quota_exceeded' && result.quota_info) {
          errorMessage = `리포트 업데이트 할당량을 모두 사용했습니다. (${result.quota_info.used}/${result.quota_info.total}) 관리자에게 문의하세요.`;
        } else if (result.error === 'permission_denied') {
          errorMessage = '리포트 업데이트 권한이 없습니다. 관리자에게 문의하세요.';
        }

        setUpdateMessage({
          type: 'error',
          text: errorMessage
        });

        // 에러 메시지는 10초 후 제거
        setTimeout(() => {
          setUpdateMessage(null);
        }, 10000);
      }
    } catch (error) {
      console.error("Failed to update report:", error);
      setUpdateMessage({
        type: 'error',
        text: "리포트 업데이트 중 오류가 발생했습니다."
      });
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (error || !stock) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl text-red-600 mb-4">{error || "종목을 찾을 수 없습니다"}</p>
          <Link href="/stocks" className="text-blue-600 hover:underline">
            ← 종목 목록으로 돌아가기
          </Link>
        </div>
      </div>
    );
  }

  // Transform stock data to match StockDetailView prop type
  const stockDetailData = {
    stock: {
      code: stock.stock_code,
      name: stock.stock_name,
    },
    current_price: stock.current_price ? {
      price: stock.current_price.close,
      change_amount: 0, // Not provided in old format
      change_rate: stock.current_price.change_rate,
      open: stock.current_price.open,
      high: stock.current_price.high,
      low: stock.current_price.low,
      date: stock.current_price.date,
    } : null,
    analysis_summary: stock.analysis_summary ? {
      ab_test_enabled: stock.analysis_summary.ab_test_enabled,
      model_a: stock.analysis_summary.model_a,
      model_b: stock.analysis_summary.model_b,
      confidence_level: stock.analysis_summary.confidence_level,
      data_sources_used: stock.analysis_summary.data_sources_used ?
        Object.entries(stock.analysis_summary.data_sources_used)
          .filter(([_, value]) => value)
          .map(([key, _]) => key)
        : undefined,
      limitations: stock.analysis_summary.limitations,
      overall_summary: stock.analysis_summary.overall_summary,
      short_term_scenario: stock.analysis_summary.short_term_scenario,
      medium_term_scenario: stock.analysis_summary.medium_term_scenario,
      long_term_scenario: stock.analysis_summary.long_term_scenario,
      risk_factors: stock.analysis_summary.risk_factors,
      opportunity_factors: stock.analysis_summary.opportunity_factors,
      recommendation: stock.analysis_summary.recommendation,
      meta: stock.analysis_summary.meta,
    } : null,
    statistics: {
      total_news: stock.statistics.total_news,
      total_notifications: stock.statistics.total_notifications,
    },
    recent_news: stock.recent_news,
  };

  return (
    <>
      {/* Toast 알림 컴포넌트 */}
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            zIndex: 9999,
          },
        }}
      />

      <StockDetailView
        data={stockDetailData}
        abConfig={abConfig}
        showBackButton={!isPublicPreview}
        showForceUpdate={true}
        onForceUpdate={handleForceUpdate}
        updating={updating}
        updateMessage={updateMessage}
      />
    </>
  );
}


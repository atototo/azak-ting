"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import StockDetailView from "../../components/StockDetailView";

// Types (simplified from StockDetailPage)
interface StockPrice {
  close: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  change_rate: number;
  date: string | null;
}

interface RecentNews {
  id: number;
  title: string;
  source: string;
  published_at: string | null;
  notified_at: string | null;
  prediction?: {
    sentiment_direction?: string | null;
    sentiment_score?: number | null;
    impact_level?: string | null;
    relevance_score?: number | null;
    urgency_level?: string | null;
    impact_analysis?: string | null;
    reasoning?: string | null;
  };
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
  data_sources_used?: DataSources;
  limitations?: string[];
  confidence_level?: 'high' | 'medium' | 'low';
  data_completeness_score?: number;
}

interface AnalysisSummary {
  overall_summary?: string;
  short_term_scenario?: string | null;
  medium_term_scenario?: string | null;
  long_term_scenario?: string | null;
  risk_factors?: string[];
  opportunity_factors?: string[];
  recommendation?: string | null;
  meta?: {
    last_updated: string | null;
    based_on_prediction_count: number;
  };
  data_sources_used?: DataSources;
  limitations?: string[];
  confidence_level?: 'high' | 'medium' | 'low';
  data_completeness_score?: number;
  ab_test_enabled?: boolean;
  model_a?: SingleModelSummary;
  model_b?: SingleModelSummary;
}

interface StockDetail {
  stock_code: string;
  stock_name: string;
  statistics: {
    total_news: number;
    total_notifications: number;
  };
  analysis_summary?: AnalysisSummary;
  current_price: StockPrice | null;
  recent_news: RecentNews[];
}

export default function PublicPreviewPage() {
  const params = useParams();
  const linkId = params.linkId as string;

  const [stockCode, setStockCode] = useState<string | null>(null);
  const [stock, setStock] = useState<StockDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [abConfig, setAbConfig] = useState<{model_a: {name: string}, model_b: {name: string}} | null>(null);

  // 1단계: linkId로 stock_code 조회
  useEffect(() => {
    if (!linkId) return;

    fetch(`/api/public-preview/${linkId}`)
      .then((res) => {
        if (!res.ok) {
          if (res.status === 410) {
            throw new Error("이 링크는 만료되었습니다");
          }
          throw new Error("유효하지 않은 링크입니다");
        }
        return res.json();
      })
      .then((data) => {
        setStockCode(data.stock_code);
      })
      .catch((err) => {
        console.error("Failed to resolve preview link:", err);
        setError(err.message);
        setLoading(false);
      });
  }, [linkId]);

  // 2단계: stock_code로 종목 상세 정보 조회
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
          <p className="text-gray-600">이 공개 프리뷰 링크를 생성한 관리자에게 문의하세요</p>
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
    <StockDetailView
      data={stockDetailData}
      abConfig={abConfig}
      showBackButton={false}
      showForceUpdate={false}
    />
  );
}

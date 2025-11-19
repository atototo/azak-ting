"use client";

import { useState, useEffect } from "react";
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceDot,
  ReferenceLine,
} from "recharts";

interface PriceData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface AnalysisReport {
  id: number;
  model_id: number | null;
  model_name: string;
  generated_at: string | null;
  sentiment_direction: string;
  overall_summary: string | null;
  recommendation: string | null;
  short_term_scenario: string | null;
  medium_term_scenario: string | null;
  long_term_scenario: string | null;
  risk_factors: string[];
  opportunity_factors: string[];
  confidence_level: string | null;
  data_completeness_score: number | null;
  short_term_target_price: number | null;
  medium_term_target_price: number | null;
  long_term_target_price: number | null;
  base_price: number | null;
}

interface ModelInfo {
  id: number;
  name: string;
  description: string | null;
}

interface StockChartProps {
  stockCode: string;
}

type PeriodType = "1W" | "1M" | "3M" | "6M" | "1Y";

const PERIOD_DAYS: Record<PeriodType, number> = {
  "1W": 7,
  "1M": 30,
  "3M": 90,
  "6M": 180,
  "1Y": 365,
};

// 모델별 색상 팔레트
const MODEL_COLORS = [
  "#3b82f6", // 파란색 (Model 1)
  "#10b981", // 초록색 (Model 2)
  "#f59e0b", // 주황색
  "#8b5cf6", // 보라색
  "#ec4899", // 핑크색
];

export default function StockChart({ stockCode }: StockChartProps) {
  const [data, setData] = useState<PriceData[]>([]);
  const [reports, setReports] = useState<AnalysisReport[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<PeriodType>("1M");
  const [selectedReport, setSelectedReport] = useState<AnalysisReport | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const days = PERIOD_DAYS[period];

        // 주가 데이터
        const priceResponse = await fetch(`/api/stocks/${stockCode}/prices?days=${days}`);
        if (!priceResponse.ok) {
          throw new Error("주가 데이터를 불러올 수 없습니다");
        }
        const prices: PriceData[] = await priceResponse.json();
        setData(prices);

        // AI 리포트 데이터
        const startDate = prices.length > 0 ? prices[0].date.split('T')[0] : null;
        const endDate = prices.length > 0 ? prices[prices.length - 1].date.split('T')[0] : null;

        if (startDate && endDate) {
          const reportsResponse = await fetch(
            `/api/stocks/${stockCode}/analysis-reports?start_date=${startDate}&end_date=${endDate}`
          );
          if (reportsResponse.ok) {
            const reportsData = await reportsResponse.json();
            setReports(reportsData.reports || []);
            setModels(reportsData.models || []);
          }
        }
      } catch (err) {
        console.error("Failed to fetch data:", err);
        setError(err instanceof Error ? err.message : "데이터 로딩 실패");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [stockCode, period]);

  // 가격 포맷팅
  const formatPrice = (value: number) => {
    return value.toLocaleString() + "원";
  };

  // 거래량 포맷팅 (천 단위)
  const formatVolume = (value: number) => {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(1) + "M";
    } else if (value >= 1000) {
      return (value / 1000).toFixed(0) + "K";
    }
    return value.toString();
  };

  // 날짜 포맷팅
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  // sentiment에 따른 이모지
  const getSentimentEmoji = (sentiment: string | null) => {
    if (sentiment === 'positive') return '📈';
    if (sentiment === 'negative') return '📉';
    return '➡️';
  };

  // 모델명 약어 생성
  const getModelShortName = (modelName: string) => {
    if (modelName.includes('GPT')) return 'G';
    if (modelName.includes('DeepSeek')) return 'D';
    if (modelName.includes('Qwen3')) return 'Q3';
    if (modelName.includes('Qwen')) return 'Q2';
    return modelName[0];
  };

  // 추천 기반 아이콘 생성 (첫 단어 기준)
  const getRecommendationIcon = (recommendation: string | null) => {
    if (!recommendation) return '−';

    // 첫 단어 추출 (공백, 하이픈, 쉼표 등으로 구분)
    const firstWord = recommendation.trim().toLowerCase().split(/[\s\-,\.]/)[0];

    // 첫 단어 기준으로 판단
    if (firstWord === '매수' || firstWord === 'buy' || firstWord.includes('적극')) return '↑';
    if (firstWord === '매도' || firstWord === 'sell') return '↓';
    if (firstWord === '관망' || firstWord === '보유' || firstWord === 'hold' || firstWord === '중립') return '−';

    return '−'; // 기본값 (관망)
  };

  // 추천 라벨 생성
  const getRecommendationLabel = (report: AnalysisReport) => {
    const modelShort = getModelShortName(report.model_name);
    const icon = getRecommendationIcon(report.recommendation);
    return `${modelShort} ${icon}`;
  };

  // confidence_level에 따른 크기 (더 크게)
  const getConfidenceSize = (confidence: string | null) => {
    if (confidence === 'high') return 14;
    if (confidence === 'medium') return 12;
    return 10;
  };

  // 모델 색상 가져오기
  const getModelColor = (modelId: number | null) => {
    if (modelId === null) return MODEL_COLORS[0];
    const index = models.findIndex(m => m.id === modelId);
    return MODEL_COLORS[index % MODEL_COLORS.length];
  };

  // Custom Tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const date = new Date(data.date);

      return (
        <div className="bg-white p-4 border border-gray-300 rounded-lg shadow-lg max-w-xs">
          <p className="font-semibold text-gray-900 mb-2">
            {date.toLocaleDateString("ko-KR")}
          </p>
          <div className="space-y-1 text-sm">
            <p className="text-gray-700">
              <span className="font-medium">시가:</span> {data.open.toLocaleString()}원
            </p>
            <p className="text-gray-700">
              <span className="font-medium">고가:</span> {data.high.toLocaleString()}원
            </p>
            <p className="text-gray-700">
              <span className="font-medium">저가:</span> {data.low.toLocaleString()}원
            </p>
            <p className="text-gray-700 font-semibold">
              <span className="font-medium">종가:</span> {data.close.toLocaleString()}원
            </p>
            <p className="text-gray-700 pt-2 border-t border-gray-200">
              <span className="font-medium">거래량:</span> {data.volume.toLocaleString()}
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center justify-center h-96">
          <div className="text-gray-500">차트 로딩 중...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center justify-center h-96">
          <div className="text-red-600">{error}</div>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center justify-center h-96">
          <div className="text-gray-500">주가 데이터가 없습니다</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">
          📈 주가 차트 {reports.length > 0 && <span className="text-sm font-normal text-gray-600">with AI 리포트 ({reports.length}건)</span>}
        </h2>

        {/* 기간 선택 버튼 */}
        <div className="flex gap-2">
          {(Object.keys(PERIOD_DAYS) as PeriodType[]).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                period === p
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* 모델 범례 */}
      {models.length > 0 && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm font-medium text-gray-700 mb-2">AI 모델 범례:</p>
          <div className="flex flex-wrap gap-3">
            {models.map((model) => (
              <div key={model.id} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getModelColor(model.id) }}
                />
                <span className="text-sm text-gray-600">{model.name}</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-2">
            💡 차트의 점을 클릭하면 AI 리포트 상세 정보를 볼 수 있습니다
          </p>
        </div>
      )}

      <ResponsiveContainer width="100%" height={450}>
        <ComposedChart
          data={data}
          margin={{ top: 20, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />

          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
          />

          {/* 주가 Y축 (왼쪽) */}
          <YAxis
            yAxisId="price"
            tickFormatter={formatPrice}
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
            domain={["auto", "auto"]}
          />

          {/* 거래량 Y축 (오른쪽) */}
          <YAxis
            yAxisId="volume"
            orientation="right"
            tickFormatter={formatVolume}
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
          />

          <Tooltip content={<CustomTooltip />} />

          <Legend
            wrapperStyle={{ paddingTop: "20px" }}
            iconType="line"
          />

          {/* 거래량 바 차트 (하단) */}
          <Bar
            yAxisId="volume"
            dataKey="volume"
            fill="url(#colorVolume)"
            name="거래량"
            opacity={0.3}
          />

          {/* 고가 라인 */}
          <Line
            yAxisId="price"
            type="monotone"
            dataKey="high"
            stroke="#ef4444"
            strokeWidth={1}
            dot={false}
            name="고가"
            opacity={0.5}
          />

          {/* 저가 라인 */}
          <Line
            yAxisId="price"
            type="monotone"
            dataKey="low"
            stroke="#3b82f6"
            strokeWidth={1}
            dot={false}
            name="저가"
            opacity={0.5}
          />

          {/* 종가 라인 (메인) */}
          <Line
            yAxisId="price"
            type="monotone"
            dataKey="close"
            stroke="#10b981"
            strokeWidth={2}
            dot={false}
            name="종가"
          />

          {/* 선택된 리포트의 목표가 수평선 */}
          {selectedReport && selectedReport.short_term_target_price && (
            <ReferenceLine
              yAxisId="price"
              y={selectedReport.short_term_target_price}
              stroke={getModelColor(selectedReport.model_id)}
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{
                value: `단기 목표: ${selectedReport.short_term_target_price.toLocaleString()}원`,
                position: 'insideTopRight',
                fill: getModelColor(selectedReport.model_id),
                fontSize: 11,
                fontWeight: 'bold',
              }}
            />
          )}

          {selectedReport && selectedReport.medium_term_target_price && (
            <ReferenceLine
              yAxisId="price"
              y={selectedReport.medium_term_target_price}
              stroke={getModelColor(selectedReport.model_id)}
              strokeDasharray="3 3"
              strokeWidth={1.5}
              opacity={0.7}
              label={{
                value: `중기 목표: ${selectedReport.medium_term_target_price.toLocaleString()}원`,
                position: 'insideBottomRight',
                fill: getModelColor(selectedReport.model_id),
                fontSize: 10,
              }}
            />
          )}

          {/* AI 리포트 마커 (모델별) */}
          {reports.map((report, idx) => {
            if (!report.generated_at) {
              return null;
            }

            const reportDate = new Date(report.generated_at).toISOString().split('T')[0];
            const priceData = data.find(d => d.date.startsWith(reportDate));

            if (!priceData) {
              return null;
            }

            // 마커 Y축 위치 계산 (같은 날짜의 마커들을 세로로 배치)
            const sameDateReports = reports.filter(r =>
              r.generated_at && new Date(r.generated_at).toISOString().split('T')[0] === reportDate
            );
            const sameDateIndex = sameDateReports.findIndex(r => r.id === report.id);
            // 간격을 더 넓게 (0.02 → 0.03)
            const yPosition = priceData.high * (1.04 + (sameDateIndex * 0.03));

            return (
              <ReferenceDot
                key={report.id}
                yAxisId="price"
                x={priceData.date}
                y={yPosition}
                r={6}  // 작은 점 (클릭 영역)
                fill={getModelColor(report.model_id)}
                fillOpacity={0.3}  // 반투명
                stroke={getModelColor(report.model_id)}
                strokeWidth={2}
                onClick={() => setSelectedReport(report)}
                style={{ cursor: 'pointer' }}
                label={{
                  value: getRecommendationLabel(report),
                  position: 'right',
                  fontSize: 13,
                  fontWeight: 'bold',
                  fill: getModelColor(report.model_id),
                  stroke: '#fff',
                  strokeWidth: 4,
                  paintOrder: 'stroke',
                  style: { cursor: 'pointer' },
                }}
              />
            );
          })}
        </ComposedChart>
      </ResponsiveContainer>

      {/* 선택된 리포트 상세 정보 */}
      {selectedReport && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex justify-between items-start mb-3">
            <div>
              <h3 className="font-semibold text-gray-900 text-lg">
                🤖 {selectedReport.model_name} AI 투자 리포트
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                생성일: {selectedReport.generated_at && new Date(selectedReport.generated_at).toLocaleString("ko-KR")}
              </p>
            </div>
            <button
              onClick={() => setSelectedReport(null)}
              className="text-gray-500 hover:text-gray-700 text-xl"
            >
              ✕
            </button>
          </div>

          <div className="space-y-3">
            {/* 종합 의견 */}
            {selectedReport.overall_summary && (
              <div className="p-3 bg-white rounded border-l-4" style={{ borderLeftColor: getModelColor(selectedReport.model_id) }}>
                <p className="font-medium text-gray-900 mb-1 text-sm">📋 종합 의견</p>
                <p className="text-sm text-gray-700">{selectedReport.overall_summary}</p>
              </div>
            )}

            {/* 최종 추천 */}
            {selectedReport.recommendation && (
              <div className="p-3 bg-white rounded border-l-4 border-indigo-400">
                <p className="font-medium text-gray-900 mb-1 text-sm">🎯 최종 추천</p>
                <p className="text-sm text-gray-700 font-medium">{selectedReport.recommendation}</p>
              </div>
            )}

            {/* 투자 전략 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {selectedReport.short_term_scenario && (
                <div className="p-2 bg-white rounded border border-red-200">
                  <p className="text-xs font-medium text-red-700 mb-1">단기 (1일~1주)</p>
                  <p className="text-xs text-gray-600">{selectedReport.short_term_scenario}</p>
                  {selectedReport.short_term_target_price && (
                    <p className="text-xs text-red-600 mt-1 font-medium">
                      목표: {selectedReport.short_term_target_price.toLocaleString()}원
                    </p>
                  )}
                </div>
              )}

              {selectedReport.medium_term_scenario && (
                <div className="p-2 bg-white rounded border border-yellow-200">
                  <p className="text-xs font-medium text-yellow-700 mb-1">중기 (1주~1개월)</p>
                  <p className="text-xs text-gray-600">{selectedReport.medium_term_scenario}</p>
                  {selectedReport.medium_term_target_price && (
                    <p className="text-xs text-yellow-600 mt-1 font-medium">
                      목표: {selectedReport.medium_term_target_price.toLocaleString()}원
                    </p>
                  )}
                </div>
              )}

              {selectedReport.long_term_scenario && (
                <div className="p-2 bg-white rounded border border-green-200">
                  <p className="text-xs font-medium text-green-700 mb-1">장기 (1개월 이상)</p>
                  <p className="text-xs text-gray-600">{selectedReport.long_term_scenario}</p>
                  {selectedReport.long_term_target_price && (
                    <p className="text-xs text-green-600 mt-1 font-medium">
                      목표: {selectedReport.long_term_target_price.toLocaleString()}원
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* 리스크 & 기회 요인 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Array.isArray(selectedReport.risk_factors) && selectedReport.risk_factors.length > 0 && (
                <div className="p-3 bg-white rounded">
                  <p className="font-medium text-orange-700 mb-2 text-sm flex items-center">
                    <span className="mr-1">⚠️</span> 리스크 요인
                  </p>
                  <ul className="space-y-1">
                    {selectedReport.risk_factors.slice(0, 3).map((risk, idx) => (
                      <li key={idx} className="text-xs text-gray-600 flex items-start">
                        <span className="mr-1">•</span>
                        <span>{risk}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {Array.isArray(selectedReport.opportunity_factors) && selectedReport.opportunity_factors.length > 0 && (
                <div className="p-3 bg-white rounded">
                  <p className="font-medium text-teal-700 mb-2 text-sm flex items-center">
                    <span className="mr-1">💡</span> 기회 요인
                  </p>
                  <ul className="space-y-1">
                    {selectedReport.opportunity_factors.slice(0, 3).map((opp, idx) => (
                      <li key={idx} className="text-xs text-gray-600 flex items-start">
                        <span className="mr-1">•</span>
                        <span>{opp}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* 신뢰도 정보 */}
            <div className="flex items-center gap-3 text-xs text-gray-600">
              <span>
                신뢰도: <span className="font-medium">{selectedReport.confidence_level || '-'}</span>
              </span>
              {selectedReport.data_completeness_score !== null && (
                <span>
                  데이터 완전도: <span className="font-medium">{(selectedReport.data_completeness_score * 100).toFixed(0)}%</span>
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 차트 통계 */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="text-center">
            <p className="text-gray-600">데이터 포인트</p>
            <p className="font-semibold text-gray-900">{data.length}일</p>
          </div>
          <div className="text-center">
            <p className="text-gray-600">최고가</p>
            <p className="font-semibold text-red-600">
              {Math.max(...data.map((d) => d.high)).toLocaleString()}원
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-600">최저가</p>
            <p className="font-semibold text-blue-600">
              {Math.min(...data.map((d) => d.low)).toLocaleString()}원
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-600">AI 리포트</p>
            <p className="font-semibold text-indigo-600">{reports.length}건</p>
          </div>
        </div>
      </div>
    </div>
  );
}

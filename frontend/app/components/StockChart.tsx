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
  ReferenceArea,
  Scatter,
  Label,
  Customized,
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

// Helper to get model color
const getModelColor = (modelId: number) => {
  return MODEL_COLORS[(modelId - 1) % MODEL_COLORS.length];
};

// Custom component to render labels with collision detection
const PredictionLabels = (props: any) => {
  const { models, extendedData, yAxis, xAxis } = props;

  if (!yAxis || !xAxis || !models || !extendedData) return null;

  // 1. Collect all label positions
  const labels: any[] = [];

  models.forEach((model: any) => {
    let lastPoint = null;
    let predictionValue = null;

    for (let i = extendedData.length - 1; i >= 0; i--) {
      if (extendedData[i][`prediction_${model.id}`] !== undefined && extendedData[i][`prediction_${model.id}`] !== null) {
        lastPoint = extendedData[i];
        predictionValue = extendedData[i][`prediction_${model.id}`];
        break;
      }
    }

    if (lastPoint && predictionValue) {
      const x = xAxis.scale(lastPoint.date);
      const y = yAxis.scale(predictionValue);
      labels.push({
        model,
        x,
        y, // Original Y (for the dot)
        labelY: y, // Adjusted Y (for the label)
        height: 24 // Height of label + padding
      });
    }
  });

  // 2. Sort by Y position (ascending - top to bottom)
  labels.sort((a, b) => a.y - b.y);

  // 3. Resolve collisions
  // Simple greedy approach: iterate and push down if overlapping
  for (let i = 1; i < labels.length; i++) {
    const prev = labels[i - 1];
    const curr = labels[i];

    if (curr.labelY < prev.labelY + prev.height) {
      curr.labelY = prev.labelY + prev.height;
    }
  }

  return (
    <g>
      {labels.map((item) => {
        const { model, x, y, labelY } = item;
        const width = model.name.length * 8 + 16;
        const height = 20;

        return (
          <g key={`label-${model.id}`}>
            {/* Dot at the original position */}
            <circle cx={x} cy={y} r={4} fill={getModelColor(model.id)} />

            {/* Connecting line if label moved significantly */}
            {Math.abs(labelY - y) > 10 && (
              <line
                x1={x} y1={y}
                x2={x + 8} y2={labelY}
                stroke={getModelColor(model.id)}
                strokeWidth={1}
                opacity={0.5}
              />
            )}

            {/* Label at adjusted position */}
            <rect
              x={x + 8}
              y={labelY - height / 2}
              width={width}
              height={height}
              fill={getModelColor(model.id)}
              rx={4}
              ry={4}
            />
            <text
              x={x + 8 + width / 2}
              y={labelY}
              dy={4}
              fill="#fff"
              fontSize={11}
              fontWeight="bold"
              textAnchor="middle"
            >
              {model.name}
            </text>
          </g>
        );
      })}
    </g>
  );
};

export default function StockChart({ stockCode }: StockChartProps) {
  const [data, setData] = useState<PriceData[]>([]);
  const [extendedData, setExtendedData] = useState<any[]>([]); // Future data included
  const [futureStartIndex, setFutureStartIndex] = useState<number>(-1);

  const [reports, setReports] = useState<AnalysisReport[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<PeriodType>("3M");
  const [showMarkers, setShowMarkers] = useState(true);
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

        let fetchedReports: AnalysisReport[] = [];

        if (startDate) {
          const reportsResponse = await fetch(
            `/api/stocks/${stockCode}/analysis-reports?start_date=${startDate}`
          );
          if (reportsResponse.ok) {
            const reportsData = await reportsResponse.json();
            const activeModels = reportsData.models || [];
            const activeModelIds = new Set(activeModels.map((m: ModelInfo) => m.id));

            // Filter reports: Only include reports from active models
            fetchedReports = (reportsData.reports || []).filter((r: AnalysisReport) =>
              r.model_id && activeModelIds.has(r.model_id)
            );

            // Define lastDate and lastClose for calculations
            const lastDate = new Date(prices[prices.length - 1].date);
            const lastDateStr = lastDate.toISOString().split('T')[0];
            const lastClose = prices[prices.length - 1].close;

            // 1. Filter reports: Show latest report per model per date
            // Group by date, then for each date keep only the latest report per model
            const reportsByDate = new Map<string, Map<number, AnalysisReport>>();

            fetchedReports.forEach(report => {
              if (!report.generated_at || !report.model_id) return;

              // Extract date directly from string to avoid timezone conversion
              const reportDate = report.generated_at.split('T')[0];

              if (!reportsByDate.has(reportDate)) {
                reportsByDate.set(reportDate, new Map());
              }

              const dateMap = reportsByDate.get(reportDate)!;
              const existing = dateMap.get(report.model_id);

              // Keep the latest report for this model on this date
              if (!existing || new Date(report.generated_at) > new Date(existing.generated_at!)) {
                dateMap.set(report.model_id, report);
              }
            });

            // Flatten back to array
            const filteredReports: AnalysisReport[] = [];
            reportsByDate.forEach(dateMap => {
              dateMap.forEach(report => filteredReports.push(report));
            });

            setReports(filteredReports);
            setModels(reportsData.models || []); // Keep all models for legend

            // 2. Calculate Consensus Targets from the MOST RECENT reports (latest date)
            // Find the latest date among all reports
            const latestReports: AnalysisReport[] = [];
            if (filteredReports.length > 0) {
              const dates = filteredReports
                .map(r => {
                  if (!r.generated_at) return 0;
                  // Extract date string directly (already in local timezone from backend)
                  return new Date(r.generated_at).getTime();
                })
                .filter(t => t > 0);

              if (dates.length > 0) {
                const maxTimestamp = Math.max(...dates);
                // Use the original string format to avoid timezone issues
                const maxDateStr = filteredReports
                  .find(r => r.generated_at && new Date(r.generated_at).getTime() === maxTimestamp)
                  ?.generated_at?.split('T')[0] || '';

                latestReports.push(...filteredReports.filter(r =>
                  r.generated_at && r.generated_at.startsWith(maxDateStr)
                ));
              }
            }

            // 2. Calculate Per-Model Prediction Paths
            // We no longer calculate a single consensus. Instead, we prepare data for each model.
            // latestReports already contains the latest report for each model from the most recent date.

            // 3. Extend Data for Future Area
            const futureDays = 35; // Extend by ~35 days to cover medium term (30d)

            // Initialize with historical data
            const newExtendedData: any[] = prices.map(p => ({
              ...p,
            }));

            // Determine the prediction start date (latest report date or last price date)
            let predictionStartDate = lastDateStr;
            let predictionStartPrice = lastClose;

            if (latestReports.length > 0) {
              const latestReportDate = new Date(Math.max(...latestReports
                .map(r => r.generated_at ? new Date(r.generated_at).getTime() : 0)
              ));
              const latestReportDateStr = latestReportDate.toISOString().split('T')[0];

              // If latest report is newer than last price data, add a point for the report date
              if (latestReportDateStr > lastDateStr) {
                predictionStartDate = latestReportDateStr;
                predictionStartPrice = lastClose; // Use last known price

                // Add intermediate point if needed
                newExtendedData.push({
                  date: predictionStartDate,
                  open: null,
                  high: null,
                  low: null,
                  close: lastClose, // Show current price
                  volume: null,
                });
              }
            }

            // Add the prediction start point for all models
            if (newExtendedData.length > 0) {
              const startPoint = newExtendedData[newExtendedData.length - 1];
              latestReports.forEach(report => {
                if (report.model_id) {
                  startPoint[`prediction_${report.model_id}`] = predictionStartPrice;
                }
              });
            }

            for (let i = 1; i <= futureDays; i++) {
              const futureDate = new Date(predictionStartDate);
              futureDate.setDate(futureDate.getDate() + i);
              const dateStr = futureDate.toISOString().split('T')[0];

              const point: any = {
                date: dateStr,
                open: null, high: null, low: null, close: null, volume: null,
              };

              // Calculate prediction for each model
              latestReports.forEach(report => {
                if (!report.model_id) return;

                const modelId = report.model_id;
                const shortTarget = report.short_term_target_price;
                const mediumTarget = report.medium_term_target_price;

                // Short Term: Day 0 -> Day 7
                if (i <= 7 && shortTarget) {
                  const slope = (shortTarget - predictionStartPrice) / 7;
                  point[`prediction_${modelId}`] = predictionStartPrice + (slope * i);
                }

                // Medium Term: Day 7 -> Day 30
                if (i > 7 && i <= 30 && shortTarget && mediumTarget) {
                  const slope = (mediumTarget - shortTarget) / (30 - 7);
                  point[`prediction_${modelId}`] = shortTarget + (slope * (i - 7));
                }
              });

              newExtendedData.push(point);
            }


            setExtendedData(newExtendedData);
            // Future starts after the prediction start point (could be price data end or report date)
            const futureIndex = predictionStartDate > lastDateStr ? prices.length + 1 : prices.length;
            setFutureStartIndex(futureIndex);
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

  // X축 틱 계산 (너무 빽빽하지 않게)
  const getXAxisTicks = () => {
    if (extendedData.length === 0) return [];
    const ticks = [];
    const step = Math.ceil(extendedData.length / 6); // Show ~6 ticks
    for (let i = 0; i < extendedData.length; i += step) {
      ticks.push(extendedData[i].date);
    }
    return ticks;
  };

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

      // Historical data exists
      if (data.open !== null) {
        return (
          <div className="bg-white p-4 border border-gray-300 rounded-lg shadow-lg max-w-xs" style={{ pointerEvents: 'none' }}>
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

      // Future data (Consensus targets)
      // Future data (Model predictions)
      const hasPrediction = models.some(m => data[`prediction_${m.id}`] !== undefined);

      if (hasPrediction) {
        return (
          <div className="bg-white p-4 border border-gray-300 rounded-lg shadow-lg max-w-xs" style={{ pointerEvents: 'none' }}>
            <p className="font-semibold text-gray-900 mb-2">
              {date.toLocaleDateString("ko-KR")} (예측)
            </p>
            <div className="space-y-1 text-sm">
              {models.map(model => {
                const pred = data[`prediction_${model.id}`];
                if (pred === undefined || pred === null) return null;
                return (
                  <p key={model.id} className="font-medium" style={{ color: getModelColor(model.id) }}>
                    {model.name}: {Math.round(pred).toLocaleString()}원
                  </p>
                );
              })}
            </div>
          </div>
        );
      }
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
        <div className="flex gap-2 items-center">
          <button
            onClick={() => setShowMarkers(!showMarkers)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors border ${showMarkers
              ? "bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100"
              : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
              }`}
          >
            {showMarkers ? "마커 숨기기" : "마커 보이기"}
          </button>
          <div className="h-4 w-px bg-gray-300 mx-1" />
          {(Object.keys(PERIOD_DAYS) as PeriodType[]).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${period === p
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

      <div style={{ width: "100%", height: 450 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            key={extendedData.length}
            data={extendedData.length > 0 ? extendedData : data}
            margin={{ top: 20, right: 100, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1} />
              </linearGradient>
            </defs>

            {/* 미래 영역 배경 (가장 뒤에 그려짐) */}
            {futureStartIndex > -1 && extendedData.length > futureStartIndex + 7 && (
              <ReferenceArea
                yAxisId="price"
                x1={extendedData[futureStartIndex].date}
                x2={extendedData[futureStartIndex + 7].date}
                fill="#8b5cf6"
                fillOpacity={0.1}
                label={{
                  value: "단기 예측",
                  position: "insideTop",
                  fill: "#8b5cf6",
                  fontSize: 12,
                  fontWeight: "bold"
                }}
              />
            )}

            {futureStartIndex > -1 && extendedData.length > futureStartIndex + 7 && (
              <ReferenceArea
                yAxisId="price"
                x1={extendedData[futureStartIndex + 7].date}
                x2={extendedData[extendedData.length - 1].date}
                fill="#f59e0b"
                fillOpacity={0.1}
                label={{
                  value: "중기 예측",
                  position: "insideTop",
                  fill: "#f59e0b",
                  fontSize: 12,
                  fontWeight: "bold"
                }}
              />
            )}

            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />

            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="#6b7280"
              style={{ fontSize: "12px" }}
              ticks={getXAxisTicks()}
            />

            {/* 주가 Y축 (왼쪽) */}
            <YAxis
              yAxisId="price"
              tickFormatter={formatPrice}
              stroke="#6b7280"
              style={{ fontSize: "12px" }}
              width={80}
              domain={['auto', (dataMax: number) => Math.round(dataMax * 1.15)]}
            />

            {/* 거래량 Y축 (오른쪽) */}
            <YAxis
              yAxisId="volume"
              orientation="right"
              tickFormatter={formatVolume}
              stroke="#6b7280"
              style={{ fontSize: "12px" }}
              label={{ value: '거래량', angle: 90, position: 'insideRight', offset: 10, style: { fill: '#6b7280', fontSize: '12px' } }}
            />

            <Tooltip
              content={<CustomTooltip />}
              wrapperStyle={{ pointerEvents: 'none' }}
            />

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
              connectNulls
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
              connectNulls
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
              connectNulls
            />

            {/* Per-Model Prediction Lines */}
            {models.map((model, index) => {
              // Different dash patterns for each model
              const dashPatterns = ["5 5", "10 5", "5 10", "3 3"];

              return (
                <Line
                  key={model.id}
                  yAxisId="price"
                  type="linear"
                  dataKey={`prediction_${model.id}`}
                  stroke={getModelColor(model.id)}
                  strokeWidth={3 - (index * 0.5)} // Vary width: 3, 2.5, 2, 1.5
                  strokeDasharray={dashPatterns[index % dashPatterns.length]}
                  dot={false}
                  name={`${model.name} 예측`}
                  connectNulls
                />
              );
            })} {/* Model Labels at the end of prediction lines */}
            {models.map((model) => {
              // Find the last point that actually has a prediction value for this model
              let lastPoint = null;
              let predictionValue = null;

              for (let i = extendedData.length - 1; i >= 0; i--) {
                if (extendedData[i][`prediction_${model.id}`] !== undefined && extendedData[i][`prediction_${model.id}`] !== null) {
                  lastPoint = extendedData[i];
                  predictionValue = extendedData[i][`prediction_${model.id}`];
                  break;
                }
              }

              if (!lastPoint || !predictionValue) {
                return null;
              }

              return (
                <ReferenceDot
                  key={`label-${model.id}-${lastPoint.date}`}
                  yAxisId="price"
                  x={lastPoint.date}
                  y={predictionValue}
                  isFront={true}
                  shape={(props: any) => {
                    const { cx, cy } = props;
                    if (!cx || !cy) return <g />;

                    const width = model.name.length * 8 + 16;
                    const height = 20;

                    return (
                      <g className="prediction-label" style={{ cursor: 'pointer' }}>
                        {/* Dot at prediction endpoint */}
                        <circle
                          cx={cx}
                          cy={cy}
                          r={4}
                          fill={getModelColor(model.id)}
                          stroke="#fff"
                          strokeWidth={1}
                        />

                        {/* Label background with slight transparency */}
                        <rect
                          x={cx + 8}
                          y={cy - height / 2}
                          width={width}
                          height={height}
                          fill={getModelColor(model.id)}
                          fillOpacity={0.95}
                          stroke="#fff"
                          strokeWidth={1}
                          rx={4}
                          ry={4}
                        />

                        {/* Label text */}
                        <text
                          x={cx + 8 + width / 2}
                          y={cy}
                          dy={4}
                          fill="#fff"
                          fontSize={11}
                          fontWeight="bold"
                          textAnchor="middle"
                        >
                          {model.name}
                        </text>
                      </g>
                    );
                  }}
                />
              );
            })}

            {/* AI 리포트 마커 (ReferenceDot으로 복귀 및 개선) */}
            {showMarkers && reports.map((report, idx) => {
              if (!report.generated_at) {
                return null;
              }

              // Extract date directly from string to avoid timezone conversion
              const reportDate = report.generated_at.split('T')[0];
              // extendedData에서 리포트 날짜에 해당하는 데이터 포인트 찾기
              const chartData = extendedData.find(d => d.date.startsWith(reportDate));

              if (!chartData) {
                return null;
              }

              // Y축 위치: high 값이 있으면 사용, 없으면 close 값 사용
              const basePrice = chartData.high || chartData.close || 0;

              if (basePrice === 0) {
                return null;
              }

              // 마커 Y축 위치 계산 (같은 날짜의 마커들을 세로로 배치)
              const sameDateReports = reports.filter(r =>
                r.generated_at && r.generated_at.split('T')[0] === reportDate
              );
              const sameDateIndex = sameDateReports.findIndex(r => r.id === report.id);
              // 간격을 좁힘 (0.03 -> 0.02) 및 시작점 조정 (1.04 -> 1.02)
              const yPosition = basePrice * (1.02 + (sameDateIndex * 0.02));

              return (
                <ReferenceDot
                  key={report.id}
                  yAxisId="price"
                  x={chartData.date}
                  y={yPosition}
                  r={4}
                  fill={getModelColor(report.model_id)}
                  fillOpacity={0.8}
                  stroke={getModelColor(report.model_id)}
                  strokeWidth={1}
                  isFront={true}
                  onClick={(e) => {

                    setSelectedReport(report);
                  }}
                  style={{ cursor: 'pointer' }}
                />
              );
            })}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* 선택된 리포트 상세 정보 */}
      {showMarkers && selectedReport && (
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

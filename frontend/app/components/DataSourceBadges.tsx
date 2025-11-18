interface DataSources {
  market_data: boolean;
  investor_trading: boolean;
  financial_ratios: boolean;
  product_info: boolean;
  technical_indicators: boolean;
  news: boolean;
}

interface DataSourceBadgesProps {
  dataSources: DataSources;
}

const DATA_SOURCE_LABELS: Record<keyof DataSources, string> = {
  market_data: '주가·거래량',
  investor_trading: '투자자 수급',
  financial_ratios: '재무 지표',
  product_info: '기업 정보',
  technical_indicators: '기술적 지표',
  news: '시장 동향',
};

const DATA_SOURCE_TOOLTIPS: Record<keyof DataSources, string> = {
  market_data: '주가, 거래량, 호가 등 가격 정보',
  investor_trading: '외국인/기관/개인 순매수 동향',
  financial_ratios: 'ROE, PER, EPS, 부채비율 등',
  product_info: '업종, 위험등급 등 기업 기본정보',
  technical_indicators: '이동평균, RSI, 볼린저밴드 등',
  news: 'AI 기반 시장 동향 분석',
};

export const DataSourceBadges: React.FC<DataSourceBadgesProps> = ({ dataSources }) => {
  return (
    <div className="flex flex-wrap gap-2">
      {Object.entries(dataSources).map(([key, available]) => {
        const label = DATA_SOURCE_LABELS[key as keyof DataSources];
        const tooltip = DATA_SOURCE_TOOLTIPS[key as keyof DataSources];

        return (
          <div
            key={key}
            title={tooltip}
            className={`px-3 py-1 rounded-full text-xs font-medium ${
              available
                ? 'bg-green-100 text-green-700 border border-green-300'
                : 'bg-gray-100 text-gray-500 border border-gray-300'
            }`}
          >
            {available ? '✅' : '❌'} {label}
          </div>
        );
      })}
    </div>
  );
};

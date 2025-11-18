"""
기술적 지표 계산 유틸리티
MA, RSI, MACD, Bollinger Bands, 거래량 분석, 모멘텀 등을 계산합니다.
"""
from typing import Dict, Any, Optional
import logging
from sqlalchemy.orm import Session
from backend.db.models.stock import StockPrice

logger = logging.getLogger(__name__)


def calculate_technical_indicators(stock_code: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    기술적 지표를 계산합니다.

    Args:
        stock_code: 종목 코드
        db: 데이터베이스 세션

    Returns:
        기술적 지표 딕셔너리 또는 None
        {
            "moving_averages": {
                "ma5": float,
                "ma20": float,
                "ma60": float,
                "current_vs_ma5": float,  # 현재가 대비 %
                "current_vs_ma20": float,
                "current_vs_ma60": float,
                "trend": str  # "강세", "중립", "약세"
            },
            "volume_analysis": {
                "current_volume": int,
                "avg_volume_20d": float,
                "volume_ratio": float,  # 평균 대비 %
                "trend": str  # "급증", "보통", "저조"
            },
            "price_momentum": {
                "change_1d": float,  # %
                "change_5d": float,
                "change_20d": float,
                "trend": str  # "상승세", "보합", "하락세"
            },
            "rsi": {
                "value": float,
                "signal": str  # "과매수", "중립", "과매도"
            },
            "bollinger_bands": {
                "upper": float,
                "middle": float,
                "lower": float,
                "position": str  # "상단돌파", "상단근접", "중립", "하단근접", "하단돌파"
            },
            "macd": {
                "macd_line": float,
                "signal_line": float,
                "histogram": float,
                "trend": str  # "매수신호", "중립", "매도신호"
            }
        }
    """
    try:
        # 최근 60일치 데이터 조회 (MA60 계산용)
        recent_prices = (
            db.query(StockPrice)
            .filter(StockPrice.stock_code == stock_code)
            .order_by(StockPrice.date.desc())
            .limit(60)
            .all()
        )

        if len(recent_prices) < 5:
            logger.warning(f"기술적 지표 계산 불가: {stock_code} - 데이터 부족 ({len(recent_prices)}일)")
            return None

        # 최신 데이터가 먼저 오므로 역순 정렬
        recent_prices.reverse()

        current_price = recent_prices[-1].close
        current_volume = recent_prices[-1].volume or 0

        # 1. 이동평균선 계산
        ma5 = sum(p.close for p in recent_prices[-5:]) / 5 if len(recent_prices) >= 5 else None
        ma20 = sum(p.close for p in recent_prices[-20:]) / 20 if len(recent_prices) >= 20 else None
        ma60 = sum(p.close for p in recent_prices[-60:]) / 60 if len(recent_prices) >= 60 else None

        # 현재가 vs 이동평균 비율
        ma5_diff = ((current_price - ma5) / ma5 * 100) if ma5 else None
        ma20_diff = ((current_price - ma20) / ma20 * 100) if ma20 else None
        ma60_diff = ((current_price - ma60) / ma60 * 100) if ma60 else None

        # 추세 판단 (정배열: 강세, 역배열: 약세)
        ma_trend = "중립"
        if ma5 and ma20 and ma60:
            if ma5 > ma20 > ma60 and current_price > ma5:
                ma_trend = "강세"
            elif ma5 < ma20 < ma60 and current_price < ma5:
                ma_trend = "약세"

        # 2. 거래량 분석
        volumes = [p.volume for p in recent_prices[-20:] if p.volume]
        avg_volume_20d = sum(volumes) / len(volumes) if volumes else 0
        volume_ratio = ((current_volume - avg_volume_20d) / avg_volume_20d * 100) if avg_volume_20d > 0 else 0

        volume_trend = "보통"
        if volume_ratio > 50:
            volume_trend = "급증"
        elif volume_ratio < -30:
            volume_trend = "저조"

        # 3. 가격 모멘텀
        change_1d = 0.0
        change_5d = 0.0
        change_20d = 0.0

        if len(recent_prices) >= 2:
            change_1d = ((current_price - recent_prices[-2].close) / recent_prices[-2].close * 100)

        if len(recent_prices) >= 6:
            change_5d = ((current_price - recent_prices[-6].close) / recent_prices[-6].close * 100)

        if len(recent_prices) >= 21:
            change_20d = ((current_price - recent_prices[-21].close) / recent_prices[-21].close * 100)

        # 모멘텀 추세 판단
        momentum_trend = "보합"
        if change_1d > 0 and change_5d > 0 and change_20d > 0:
            momentum_trend = "상승세"
        elif change_1d < 0 and change_5d < 0 and change_20d < 0:
            momentum_trend = "하락세"

        # 4. RSI (14일 기준)
        rsi = None
        rsi_signal = "중립"
        if len(recent_prices) >= 15:
            # RSI 계산: 14일간의 상승/하락 평균
            gains = []
            losses = []
            for i in range(-14, 0):
                change = recent_prices[i].close - recent_prices[i-1].close
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))

            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            # RSI 신호 판단
            if rsi >= 70:
                rsi_signal = "과매수"
            elif rsi <= 30:
                rsi_signal = "과매도"

        # 5. 볼린저 밴드 (20일 기준, 2 표준편차)
        bb_upper = None
        bb_middle = None
        bb_lower = None
        bb_position = "중립"
        if len(recent_prices) >= 20 and ma20:
            # 표준편차 계산
            prices_20d = [p.close for p in recent_prices[-20:]]
            variance = sum((p - ma20) ** 2 for p in prices_20d) / 20
            std_dev = variance ** 0.5

            bb_upper = ma20 + (2 * std_dev)
            bb_middle = ma20
            bb_lower = ma20 - (2 * std_dev)

            # 현재가 위치 판단
            if current_price >= bb_upper:
                bb_position = "상단돌파"
            elif current_price <= bb_lower:
                bb_position = "하단돌파"
            elif current_price > bb_middle:
                bb_position = "상단근접"
            else:
                bb_position = "하단근접"

        # 6. MACD (12일, 26일, 9일 신호선)
        macd_line = None
        macd_signal = None
        macd_histogram = None
        macd_trend = "중립"
        if len(recent_prices) >= 26:
            # EMA 계산 헬퍼 함수
            def calculate_ema(prices, period):
                multiplier = 2 / (period + 1)
                ema = prices[0]
                for price in prices[1:]:
                    ema = (price - ema) * multiplier + ema
                return ema

            prices = [p.close for p in recent_prices]

            # 12일 EMA
            ema12 = calculate_ema(prices[-26:], 12)

            # 26일 EMA
            ema26 = calculate_ema(prices[-26:], 26)

            # MACD Line
            macd_line = ema12 - ema26

            # Signal Line (MACD의 9일 EMA)
            if len(recent_prices) >= 35:
                macd_values = []
                for i in range(-35, 0):
                    prices_segment = [p.close for p in recent_prices[max(0, i-25):i+1]]
                    if len(prices_segment) >= 26:
                        e12 = calculate_ema(prices_segment[-26:], 12)
                        e26 = calculate_ema(prices_segment[-26:], 26)
                        macd_values.append(e12 - e26)

                if len(macd_values) >= 9:
                    macd_signal = calculate_ema(macd_values[-9:], 9)
                    macd_histogram = macd_line - macd_signal

                    # MACD 신호 판단
                    if macd_histogram > 0:
                        macd_trend = "매수신호"
                    elif macd_histogram < 0:
                        macd_trend = "매도신호"

        return {
            "moving_averages": {
                "ma5": round(ma5, 2) if ma5 else None,
                "ma20": round(ma20, 2) if ma20 else None,
                "ma60": round(ma60, 2) if ma60 else None,
                "current_vs_ma5": round(ma5_diff, 2) if ma5_diff else None,
                "current_vs_ma20": round(ma20_diff, 2) if ma20_diff else None,
                "current_vs_ma60": round(ma60_diff, 2) if ma60_diff else None,
                "trend": ma_trend,
            },
            "volume_analysis": {
                "current_volume": current_volume,
                "avg_volume_20d": round(avg_volume_20d, 0) if avg_volume_20d else 0,
                "volume_ratio": round(volume_ratio, 2),
                "trend": volume_trend,
            },
            "price_momentum": {
                "change_1d": round(change_1d, 2),
                "change_5d": round(change_5d, 2),
                "change_20d": round(change_20d, 2),
                "trend": momentum_trend,
            },
            "rsi": {
                "value": round(rsi, 2) if rsi else None,
                "signal": rsi_signal,
            },
            "bollinger_bands": {
                "upper": round(bb_upper, 2) if bb_upper else None,
                "middle": round(bb_middle, 2) if bb_middle else None,
                "lower": round(bb_lower, 2) if bb_lower else None,
                "position": bb_position,
            },
            "macd": {
                "macd_line": round(macd_line, 2) if macd_line else None,
                "signal_line": round(macd_signal, 2) if macd_signal else None,
                "histogram": round(macd_histogram, 2) if macd_histogram else None,
                "trend": macd_trend,
            }
        }

    except Exception as e:
        logger.error(f"기술적 지표 계산 실패 (종목코드: {stock_code}): {e}")
        return None

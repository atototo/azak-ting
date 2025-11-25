"""
종목 API

종목별 통계 및 주가 정보를 제공합니다.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db.session import SessionLocal
from backend.db.models.news import NewsArticle
from backend.db.models.stock import StockPrice
from backend.db.models.prediction import Prediction
from backend.utils.stock_mapping import get_stock_mapper
from backend.services.stock_analysis_service import (
    get_stock_analysis_summary,
)
from backend.services.price_service import get_current_price, get_market_status


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stocks")


def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _generate_investment_summary(
    total_predictions: int,
    direction_distribution: dict,
    avg_confidence: float,
    confidence_breakdown_avg: dict,
    pattern_analysis_avg: dict,
    investment_opinion: str,
) -> dict:
    """
    AI 투자 분석 요약 생성

    투자 전문가처럼 종합적인 인사이트를 제공합니다.
    """
    if total_predictions == 0:
        return {
            "overall_summary": "아직 분석된 뉴스가 없습니다.",
            "short_term_outlook": None,
            "medium_term_outlook": None,
            "long_term_outlook": None,
            "risk_factors": [],
            "opportunity_factors": [],
            "recommendation": None,
        }

    up_count = direction_distribution["up"]
    down_count = direction_distribution["down"]
    hold_count = direction_distribution["hold"]

    # 1. 전체 요약
    up_ratio = up_count / total_predictions * 100
    down_ratio = down_count / total_predictions * 100

    if investment_opinion == "buy":
        opinion_text = "**매수 추천**"
        trend = "강한 상승세"
    elif investment_opinion == "hold_positive":
        opinion_text = "**긍정적 관망**"
        trend = "상승 가능성"
    elif investment_opinion == "sell":
        opinion_text = "**매도 고려**"
        trend = "하락 우려"
    elif investment_opinion == "hold_negative":
        opinion_text = "**부정적 관망**"
        trend = "하락 가능성"
    else:
        opinion_text = "**중립 관망**"
        trend = "보합세"

    confidence_text = "높은" if avg_confidence and avg_confidence >= 70 else "중간" if avg_confidence and avg_confidence >= 50 else "낮은"

    overall_summary = (
        f"최근 {total_predictions}건의 뉴스를 분석한 결과, "
        f"AI는 {up_count}건 상승, {down_count}건 하락, {hold_count}건 보합으로 예측했습니다. "
        f"평균 신뢰도 {round(avg_confidence, 1) if avg_confidence else 0}%로 {confidence_text} 편이며, "
        f"현재 {opinion_text} 의견입니다. {trend}가 감지되고 있습니다."
    )

    # 2. 기간별 전망
    short_term_outlook = None
    medium_term_outlook = None
    long_term_outlook = None

    if pattern_analysis_avg:
        avg_1d = pattern_analysis_avg.get("avg_1d")
        avg_3d = pattern_analysis_avg.get("avg_3d")
        avg_5d = pattern_analysis_avg.get("avg_5d")
        avg_10d = pattern_analysis_avg.get("avg_10d")
        avg_20d = pattern_analysis_avg.get("avg_20d")

        # 단기 (T+1~3일)
        if avg_1d is not None and avg_3d is not None:
            short_avg = (avg_1d + avg_3d) / 2
            if short_avg > 2:
                short_term_outlook = f"단기 반등 가능성 높음 (평균 +{short_avg:.1f}%)"
            elif short_avg > 0:
                short_term_outlook = f"단기 완만한 상승 예상 (평균 +{short_avg:.1f}%)"
            elif short_avg > -2:
                short_term_outlook = f"단기 소폭 하락 우려 (평균 {short_avg:.1f}%)"
            else:
                short_term_outlook = f"단기 조정 가능성 (평균 {short_avg:.1f}%)"

        # 중기 (T+5~10일)
        if avg_5d is not None and avg_10d is not None:
            mid_avg = (avg_5d + avg_10d) / 2
            if mid_avg > 5:
                medium_term_outlook = f"중기 강한 상승 추세 (평균 +{mid_avg:.1f}%)"
            elif mid_avg > 0:
                medium_term_outlook = f"중기 점진적 상승 (평균 +{mid_avg:.1f}%)"
            elif mid_avg > -5:
                medium_term_outlook = f"중기 하락 압력 (평균 {mid_avg:.1f}%)"
            else:
                medium_term_outlook = f"중기 큰 조정 예상 (평균 {mid_avg:.1f}%)"

        # 장기 (T+20일)
        if avg_20d is not None:
            if avg_20d > 10:
                long_term_outlook = f"장기 우상향 전망 (평균 +{avg_20d:.1f}%)"
            elif avg_20d > 0:
                long_term_outlook = f"장기 완만한 상승 (평균 +{avg_20d:.1f}%)"
            elif avg_20d > -10:
                long_term_outlook = f"장기 하락 리스크 (평균 {avg_20d:.1f}%)"
            else:
                long_term_outlook = f"장기 큰 변동성 (평균 {avg_20d:.1f}%)"

    # 3. 리스크 요인
    risk_factors = []

    if down_ratio > 40:
        risk_factors.append(f"하락 예측 비중 높음 ({down_ratio:.0f}%)")

    if avg_confidence and avg_confidence < 60:
        risk_factors.append(f"예측 신뢰도 낮음 ({avg_confidence:.0f}%)")

    if confidence_breakdown_avg:
        if confidence_breakdown_avg.get("similar_news_quality") and confidence_breakdown_avg["similar_news_quality"] < 60:
            risk_factors.append("유사 뉴스 품질 부족")
        if confidence_breakdown_avg.get("pattern_consistency") and confidence_breakdown_avg["pattern_consistency"] < 60:
            risk_factors.append("과거 패턴 일관성 낮음")

    if total_predictions < 5:
        risk_factors.append("분석 데이터 부족")

    # 4. 기회 요인
    opportunity_factors = []

    if up_ratio > 60:
        opportunity_factors.append(f"강한 상승 신호 ({up_ratio:.0f}%)")

    if avg_confidence and avg_confidence >= 70:
        opportunity_factors.append(f"높은 예측 신뢰도 ({avg_confidence:.0f}%)")

    if confidence_breakdown_avg:
        if confidence_breakdown_avg.get("pattern_consistency") and confidence_breakdown_avg["pattern_consistency"] >= 70:
            opportunity_factors.append("일관된 상승 패턴")
        if confidence_breakdown_avg.get("disclosure_impact") and confidence_breakdown_avg["disclosure_impact"] >= 70:
            opportunity_factors.append("긍정적 공시 영향")

    if pattern_analysis_avg:
        if pattern_analysis_avg.get("avg_5d") and pattern_analysis_avg["avg_5d"] > 5:
            opportunity_factors.append(f"중기 강한 상승 모멘텀 (+{pattern_analysis_avg['avg_5d']:.1f}%)")

    # 5. 투자 추천
    recommendation = None

    if investment_opinion == "buy":
        if avg_confidence and avg_confidence >= 70:
            recommendation = "**적극 매수**: 단기 반등 기회 포착 권장"
        else:
            recommendation = "**매수 고려**: 분할 매수 전략 추천"
    elif investment_opinion == "hold_positive":
        recommendation = "**관망 후 매수**: 추가 상승 신호 확인 후 진입"
    elif investment_opinion == "sell":
        if avg_confidence and avg_confidence >= 70:
            recommendation = "**손절 고려**: 추가 하락 전 청산 검토"
        else:
            recommendation = "**비중 축소**: 점진적 매도 전략"
    elif investment_opinion == "hold_negative":
        recommendation = "**신규 진입 비추천**: 반등 신호까지 대기"
    else:
        recommendation = "**중립**: 명확한 방향성 확인 필요"

    return {
        "overall_summary": overall_summary,
        "short_term_outlook": short_term_outlook,
        "medium_term_outlook": medium_term_outlook,
        "long_term_outlook": long_term_outlook,
        "risk_factors": risk_factors,
        "opportunity_factors": opportunity_factors,
        "recommendation": recommendation,
    }


@router.get("/summary")
async def get_stocks_summary(db: Session = Depends(get_db)):
    """
    종목별 요약 통계

    모든 활성 종목의 뉴스 건수, 알림 건수 등을 반환합니다.
    US-004: 뉴스가 없는 종목도 표시 (Placeholder 리포트 포함)
    """
    try:
        from backend.db.models.stock import Stock

        # Stock 테이블 기준으로 LEFT JOIN (뉴스 없는 종목도 포함)
        stock_stats = db.query(
            Stock.code.label("stock_code"),
            Stock.name.label("stock_name"),
            func.coalesce(func.count(NewsArticle.id), 0).label("news_count"),
            func.coalesce(func.count(NewsArticle.notified_at), 0).label("notification_count"),
            func.max(NewsArticle.published_at).label("latest_news_date")
        ).outerjoin(
            NewsArticle, Stock.code == NewsArticle.stock_code
        ).filter(
            Stock.is_active == True  # 활성 종목만
        ).group_by(
            Stock.code, Stock.name
        ).all()

        result = []
        for stock_code, stock_name, news_count, notification_count, latest_news_date in stock_stats:
            result.append({
                "stock_code": stock_code,
                "stock_name": stock_name or stock_code,
                "news_count": news_count,
                "notification_count": notification_count,
                "latest_news_date": latest_news_date.isoformat() if latest_news_date else None,
            })

        # 뉴스 건수 많은 순으로 정렬 (뉴스 0건은 마지막)
        result.sort(key=lambda x: x["news_count"], reverse=True)

        return result

    except Exception as e:
        logger.error(f"종목 요약 조회 실패: {e}", exc_info=True)
        raise


@router.get("/{stock_code}")
async def get_stock_detail(
    stock_code: str,
    db: Session = Depends(get_db)
):
    """
    종목 상세 정보

    특정 종목의 상세 통계 및 최신 주가를 반환합니다.
    """
    try:
        # 종목명 조회 (DB에서 직접 조회)
        from backend.db.models.stock import Stock
        stock = db.query(Stock).filter(Stock.code == stock_code).first()

        if not stock:
            raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다")

        stock_name = stock.name

        # 뉴스 통계
        total_news = db.query(func.count(NewsArticle.id)).filter(
            NewsArticle.stock_code == stock_code
        ).scalar() or 0

        total_notifications = db.query(func.count(NewsArticle.id)).filter(
            NewsArticle.stock_code == stock_code,
            NewsArticle.notified_at.isnot(None)
        ).scalar() or 0

        # 예측 통계 (신 스키마 사용: sentiment_direction)
        # sentiment_score는 -1.0~1.0이므로 평균을 0~1로 정규화
        avg_sentiment = db.query(func.avg(Prediction.sentiment_score)).filter(
            Prediction.stock_code == stock_code,
            Prediction.sentiment_score.isnot(None)
        ).scalar()

        # 0~1 범위로 정규화 (-1~1 → 0~1)
        avg_confidence = ((avg_sentiment + 1) / 2) if avg_sentiment is not None else None

        # 방향 분포 (sentiment_direction 사용: positive/negative/neutral → up/down/hold 매핑)
        direction_counts = db.query(
            Prediction.sentiment_direction,
            func.count(Prediction.id)
        ).filter(
            Prediction.stock_code == stock_code,
            Prediction.sentiment_direction.isnot(None)
        ).group_by(Prediction.sentiment_direction).all()

        direction_distribution = {
            "up": 0,
            "down": 0,
            "hold": 0
        }
        # sentiment_direction을 direction으로 매핑
        sentiment_to_direction = {
            "positive": "up",
            "negative": "down",
            "neutral": "hold"
        }
        for sentiment, count in direction_counts:
            direction = sentiment_to_direction.get(sentiment)
            if direction and direction in direction_distribution:
                direction_distribution[direction] = count

        # Phase 2: 전체 예측의 종합 통계 계산
        all_predictions = db.query(Prediction).filter(
            Prediction.stock_code == stock_code
        ).all()

        # 신뢰도 breakdown 평균 계산
        confidence_breakdown_avg = {
            "similar_news_quality": None,
            "pattern_consistency": None,
            "disclosure_impact": None,
        }

        breakdown_counts = {"similar_news_quality": 0, "pattern_consistency": 0, "disclosure_impact": 0}
        breakdown_sums = {"similar_news_quality": 0.0, "pattern_consistency": 0.0, "disclosure_impact": 0.0}

        for pred in all_predictions:
            if pred.confidence_breakdown:
                for key in ["similar_news_quality", "pattern_consistency", "disclosure_impact"]:
                    val = pred.confidence_breakdown.get(key)
                    if val is not None:
                        try:
                            # 문자열로 저장된 경우를 대비해 float로 변환
                            val_float = float(val)
                            breakdown_sums[key] += val_float
                            breakdown_counts[key] += 1
                        except (ValueError, TypeError):
                            # 변환 실패 시 건너뛰기
                            continue

        for key in ["similar_news_quality", "pattern_consistency", "disclosure_impact"]:
            if breakdown_counts[key] > 0:
                confidence_breakdown_avg[key] = round(breakdown_sums[key] / breakdown_counts[key], 1)

        # 패턴 분석 평균 계산
        pattern_analysis_avg = {
            "avg_1d": None,
            "avg_2d": None,
            "avg_3d": None,
            "avg_5d": None,
            "avg_10d": None,
            "avg_20d": None,
        }

        pattern_counts = {"avg_1d": 0, "avg_2d": 0, "avg_3d": 0, "avg_5d": 0, "avg_10d": 0, "avg_20d": 0}
        pattern_sums = {"avg_1d": 0.0, "avg_2d": 0.0, "avg_3d": 0.0, "avg_5d": 0.0, "avg_10d": 0.0, "avg_20d": 0.0}

        for pred in all_predictions:
            if pred.pattern_analysis:
                for key in ["avg_1d", "avg_2d", "avg_3d", "avg_5d", "avg_10d", "avg_20d"]:
                    val = pred.pattern_analysis.get(key)
                    if val is not None and val != 0.0:  # 0.0은 제외 (의미 없는 데이터)
                        try:
                            # 문자열로 저장된 경우를 대비해 float로 변환
                            val_float = float(val)
                            if val_float != 0.0:
                                pattern_sums[key] += val_float
                                pattern_counts[key] += 1
                        except (ValueError, TypeError):
                            # 변환 실패 시 건너뛰기
                            continue

        for key in ["avg_1d", "avg_2d", "avg_3d", "avg_5d", "avg_10d", "avg_20d"]:
            if pattern_counts[key] > 0:
                pattern_analysis_avg[key] = round(pattern_sums[key] / pattern_counts[key], 2)

        # AI 투자 의견 계산
        total_predictions = direction_distribution["up"] + direction_distribution["down"] + direction_distribution["hold"]
        investment_opinion = None
        opinion_confidence = None

        if total_predictions > 0:
            up_ratio = direction_distribution["up"] / total_predictions
            down_ratio = direction_distribution["down"] / total_predictions

            # 상승/하락 비율 기반 의견 생성
            if up_ratio >= 0.6:
                investment_opinion = "buy"  # 매수 추천
                opinion_confidence = up_ratio
            elif up_ratio >= 0.4:
                investment_opinion = "hold_positive"  # 긍정적 관망
                opinion_confidence = up_ratio
            elif down_ratio >= 0.6:
                investment_opinion = "sell"  # 매도 고려
                opinion_confidence = down_ratio
            elif down_ratio >= 0.4:
                investment_opinion = "hold_negative"  # 부정적 관망
                opinion_confidence = down_ratio
            else:
                investment_opinion = "hold"  # 중립 관망
                opinion_confidence = max(up_ratio, down_ratio)

        # Phase 2: LLM 기반 AI 투자 분석 요약 조회
        # 캐시된 분석 요약이 있으면 사용, 없으면 fallback 메시지만 표시 (자동 생성 제거)
        analysis_summary = get_stock_analysis_summary(stock_code, db)

        if not analysis_summary:
            # 자동 생성하지 않고 기본 메시지만 표시
            logger.info(f"종목 {stock_code}의 분석 요약이 없습니다. 리포트 업데이트 버튼을 눌러주세요.")

            # 기본 규칙 기반 요약 사용 (fallback)
            analysis_summary = _generate_investment_summary(
                total_predictions=total_predictions,
                direction_distribution=direction_distribution,
                avg_confidence=avg_confidence,
                confidence_breakdown_avg=confidence_breakdown_avg,
                pattern_analysis_avg=pattern_analysis_avg,
                investment_opinion=investment_opinion,
            )
            # 규칙 기반 요약을 LLM 형식에 맞게 변환
            analysis_summary = {
                "overall_summary": analysis_summary.get("overall_summary"),
                "short_term_scenario": analysis_summary.get("short_term_outlook"),
                "medium_term_scenario": analysis_summary.get("medium_term_outlook"),
                "long_term_scenario": analysis_summary.get("long_term_outlook"),
                "risk_factors": analysis_summary.get("risk_factors", []),
                "opportunity_factors": analysis_summary.get("opportunity_factors", []),
                "recommendation": analysis_summary.get("recommendation"),
                "statistics": {
                    "total_predictions": total_predictions,
                    "up_count": direction_distribution["up"],
                    "down_count": direction_distribution["down"],
                    "hold_count": direction_distribution["hold"],
                    "avg_confidence": round(avg_confidence * 100, 1) if avg_confidence else None,
                },
                "meta": {
                    "last_updated": None,
                    "based_on_prediction_count": total_predictions,
                }
            }

        # 시간대별 현재가 조회
        current_price = await get_current_price(stock_code, db)

        # 시장 상태 추가
        market_status = get_market_status()
        if current_price:
            current_price["market_status"] = market_status

        # 최근 뉴스 (5건) + 예측 정보
        recent_news = db.query(NewsArticle).filter(
            NewsArticle.stock_code == stock_code
        ).order_by(NewsArticle.created_at.desc()).limit(5).all()

        recent_news_list = []
        for news in recent_news:
            # 해당 뉴스의 예측 정보 조회
            prediction = db.query(Prediction).filter(
                Prediction.news_id == news.id
            ).first()

            news_data = {
                "id": news.id,
                "title": news.title,
                "source": news.source,
                "published_at": news.published_at.isoformat() if news.published_at else None,
                "notified_at": news.notified_at.isoformat() if news.notified_at else None,
            }

            # 예측 정보가 있으면 추가 (Epic 3: 영향도 분석 필드 추가)
            if prediction:
                news_data["prediction"] = {
                    # Epic 3: 새로운 영향도 분석 필드
                    "sentiment_direction": prediction.sentiment_direction,
                    "sentiment_score": prediction.sentiment_score,
                    "impact_level": prediction.impact_level,
                    "relevance_score": prediction.relevance_score,
                    "urgency_level": prediction.urgency_level,
                    "impact_analysis": prediction.impact_analysis,
                    "reasoning": prediction.reasoning,
                    # Deprecated 필드 (하위 호환성)
                    "direction": prediction.direction,
                    "confidence": prediction.confidence,
                    "short_term": prediction.short_term,
                    "medium_term": prediction.medium_term,
                    "long_term": prediction.long_term,
                    "confidence_breakdown": prediction.confidence_breakdown,
                    "pattern_analysis": prediction.pattern_analysis,
                }

            recent_news_list.append(news_data)

        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "statistics": {
                "total_news": total_news,
                "total_notifications": total_notifications,
                "avg_confidence": round(avg_confidence, 2) if avg_confidence else None,
                "direction_distribution": direction_distribution,
                "investment_opinion": investment_opinion,
                "opinion_confidence": round(opinion_confidence, 2) if opinion_confidence else None,
                # Phase 2: 종합 통계
                "confidence_breakdown_avg": confidence_breakdown_avg,
                "pattern_analysis_avg": pattern_analysis_avg,
            },
            # Phase 2: LLM 기반 AI 투자 분석 요약 (별도 필드로 분리)
            "analysis_summary": analysis_summary,
            "current_price": current_price,
            "recent_news": recent_news_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"종목 상세 조회 실패: {e}", exc_info=True)
        raise


@router.get("/{stock_code}/prices")
async def get_stock_prices(
    stock_code: str,
    days: int = Query(30, ge=1, le=365, description="조회할 일수"),
    db: Session = Depends(get_db)
):
    """
    종목 주가 히스토리

    특정 종목의 주가 데이터를 반환합니다.
    오늘 일봉 데이터가 없으면 현재가를 포함합니다.
    """
    try:
        # 날짜 범위 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 주가 조회 (일봉)
        prices = db.query(StockPrice).filter(
            StockPrice.stock_code == stock_code,
            StockPrice.date >= start_date,
            StockPrice.date <= end_date
        ).order_by(StockPrice.date.asc()).all()

        result = [{
            "date": price.date.isoformat() if price.date else None,
            "open": price.open,
            "high": price.high,
            "low": price.low,
            "close": price.close,
            "volume": price.volume,
        } for price in prices]

        # 오늘 일봉 데이터가 없으면 현재가를 추가
        today = datetime.now().date()
        has_today = any(
            datetime.fromisoformat(p["date"]).date() == today for p in result if p["date"]
        )

        if not has_today:
            from sqlalchemy import text
            current_price_row = db.execute(text("""
                SELECT stck_prpr, acml_vol, datetime
                FROM stock_current_price
                WHERE stock_code = :stock_code
                AND datetime::date = :today
                ORDER BY datetime DESC
                LIMIT 1
            """), {"stock_code": stock_code, "today": today}).fetchone()

            if current_price_row:
                current_price = current_price_row[0]
                volume = current_price_row[1] or 0
                price_datetime = current_price_row[2]

                # 현재가를 임시 OHLC로 사용
                result.append({
                    "date": price_datetime.replace(hour=0, minute=0, second=0).isoformat(),
                    "open": current_price,
                    "high": current_price,
                    "low": current_price,
                    "close": current_price,
                    "volume": volume,
                })

        return result

    except Exception as e:
        logger.error(f"주가 히스토리 조회 실패: {e}", exc_info=True)
        raise


@router.get("/{stock_code}/predictions")
async def get_stock_predictions(
    stock_code: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    종목별 예측 목록

    특정 종목에 대한 예측(알림) 기록을 반환합니다.
    """
    try:
        # 알림이 발송된 뉴스만 조회
        query = db.query(NewsArticle).filter(
            NewsArticle.stock_code == stock_code,
            NewsArticle.notified_at.isnot(None)
        ).order_by(NewsArticle.notified_at.desc())

        total_count = query.count()

        offset = (page - 1) * limit
        news_list = query.offset(offset).limit(limit).all()

        result = [{
            "id": news.id,
            "title": news.title,
            "source": news.source,
            "published_at": news.published_at.isoformat() if news.published_at else None,
            "notified_at": news.notified_at.isoformat() if news.notified_at else None,
        } for news in news_list]

        total_pages = (total_count + limit - 1) // limit

        return {
            "items": result,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": total_pages,
            }
        }

    except Exception as e:
        logger.error(f"종목별 예측 조회 실패: {e}", exc_info=True)
        raise


@router.get("/{stock_code}/analysis-reports")
async def get_analysis_reports(
    stock_code: str,
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    차트용 AI 리포트 데이터

    특정 종목의 모델별 AI 투자 리포트를 반환합니다.
    """
    try:
        from backend.db.models.model import Model
        from backend.db.models.stock_analysis import StockAnalysisSummary

        # 리포트 쿼리
        query = db.query(StockAnalysisSummary).filter(
            StockAnalysisSummary.stock_code == stock_code
        )

        # 날짜 범위 필터
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(StockAnalysisSummary.last_updated >= start_dt)

        # end_date 필터는 사용하지 않음
        # 이유: 차트 조회 시 주가 데이터의 마지막 날짜를 end_date로 전달하는데,
        # 오늘 생성된 리포트는 아직 주가 일봉 데이터가 없어서 제외될 수 있음
        # 대신 start_date 이후의 모든 리포트를 반환하여 최신 리포트를 포함

        reports = query.order_by(StockAnalysisSummary.last_updated.asc()).all()

        # 모든 활성 모델 정보 조회
        models = db.query(Model).filter(Model.is_active == True).all()
        model_info = {
            model.id: {
                "id": model.id,
                "name": model.name,
                "description": model.description
            }
            for model in models
        }

        # 리포트 데이터 변환
        result = []
        for report in reports:
            # 투자 방향 결정 (up/down/hold 카운트 기반)
            total = report.total_predictions or 0
            direction = "hold"
            if total > 0:
                up_ratio = (report.up_count or 0) / total
                down_ratio = (report.down_count or 0) / total
                if up_ratio > 0.6:
                    direction = "positive"
                elif down_ratio > 0.6:
                    direction = "negative"

            result.append({
                "id": report.id,
                "model_id": report.model_id,
                "model_name": model_info.get(report.model_id, {}).get("name", f"Model {report.model_id}") if report.model_id else "Unknown",
                "generated_at": report.last_updated.isoformat() if report.last_updated else None,
                "sentiment_direction": direction,
                "overall_summary": report.overall_summary,
                "recommendation": report.recommendation,
                "short_term_scenario": report.short_term_scenario,
                "medium_term_scenario": report.medium_term_scenario,
                "long_term_scenario": report.long_term_scenario,
                "risk_factors": report.risk_factors or [],
                "opportunity_factors": report.opportunity_factors or [],
                "confidence_level": report.confidence_level,
                "data_completeness_score": report.data_completeness_score,
                # 가격 목표
                "short_term_target_price": report.short_term_target_price,
                "medium_term_target_price": report.medium_term_target_price,
                "long_term_target_price": report.long_term_target_price,
                "base_price": report.base_price,
            })

        return {
            "reports": result,
            "models": list(model_info.values())
        }

    except Exception as e:
        logger.error(f"AI 리포트 조회 실패: {e}", exc_info=True)
        raise

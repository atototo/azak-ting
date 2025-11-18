"""
Stock Analysis Service

예측 생성 시 자동으로 종합 투자 리포트를 업데이트하는 서비스
"""
import logging
import json
import re
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.models.prediction import Prediction
from backend.db.models.stock_analysis import StockAnalysisSummary
from backend.db.models.stock import StockPrice, Stock
from backend.db.models.model import Model
from backend.db.models.ab_test_config import ABTestConfig
from backend.db.models.market_data import StockCurrentPrice, InvestorTrading
from backend.db.models.financial import FinancialRatio, ProductInfo
from backend.db.models.news import NewsArticle
from backend.llm.investment_report import get_report_generator
from backend.utils.stock_mapping import get_stock_mapper
from backend.utils.market_time import (
    get_market_phase,
    get_ttl_hours,
    get_price_threshold,
    get_direction_threshold
)
from backend.crawlers.kis_client import KISClient
from backend.services.kis_data_service import save_product_info, save_financial_ratios


logger = logging.getLogger(__name__)


async def trigger_initial_analysis(stock_code: str, db: Session):
    """
    신규 종목 등록 시 즉시 분석 실행

    1. KIS API로 초기 데이터 수집 (1회만)
    2. DB에 저장
    3. 초기 리포트 생성

    Args:
        stock_code: 종목코드
        db: DB 세션

    Raises:
        Exception: 치명적 오류 시 (로그만 기록, re-raise 안 함)
    """
    logger.info(f"🚀 Triggering initial analysis for {stock_code}")

    try:
        client = KISClient()

        # KIS API 호출 (초기 1회만)
        tasks = [
            client.get_current_price(stock_code),
            client.get_product_info(stock_code),
            client.get_financial_ratios(stock_code, div_cls_code="0")
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        current_price_data = results[0] if not isinstance(results[0], Exception) else None
        product_info_data = results[1] if not isinstance(results[1], Exception) else None
        financial_ratios_data = results[2] if not isinstance(results[2], Exception) else None

        # DB 저장 (우아한 실패 처리)
        if product_info_data:
            save_product_info(db, stock_code, product_info_data)
            logger.info(f"✅ Saved product info for {stock_code}")

        if financial_ratios_data:
            save_financial_ratios(db, stock_code, financial_ratios_data)
            logger.info(f"✅ Saved financial ratios for {stock_code}")

        # 초기 리포트 생성 (US-004: DB 기반, 전체 모델)
        reports = await generate_stock_report(stock_code, db)

        if reports:
            logger.info(f"✅ Initial DB-based reports generated for {stock_code} ({len(reports)} models)")
        else:
            # DB 데이터도 없어서 리포트 생성 실패 - Placeholder 생성
            logger.warning(f"⚠️ No data available for {stock_code}, creating placeholder report")
            await create_placeholder_report(
                stock_code, db,
                error_msg="초기 데이터 수집 대기 중 - KIS API 데이터 수집 후 재시도 예정"
            )

    except Exception as e:
        logger.error(f"❌ Initial analysis failed for {stock_code}: {e}")
        # Placeholder 리포트 생성 시도
        try:
            await create_placeholder_report(stock_code, db, error_msg=str(e))
        except Exception as e2:
            logger.error(f"❌ Placeholder report failed for {stock_code}: {e2}")


async def generate_stock_report(
    stock_code: str,
    db: Session,
    force_update: bool = False
) -> List[StockAnalysisSummary]:
    """
    종목 리포트 생성 - DB 기반, 전체 모델 지원 (US-004 통합 버전)

    프로세스:
    1. DB에서 컨텍스트 구축 (현재가, 투자자수급, 재무비율, 상품정보, 뉴스)
    2. 데이터 가용성 확인
    3. 적응형 프롬프트 생성
    4. 모든 활성 모델에 대해 리포트 생성
    5. 메타데이터 포함 (data_sources_used, limitations, confidence_level)

    Args:
        stock_code: 종목코드
        db: DB 세션
        force_update: 강제 업데이트 (기본값: False)

    Returns:
        생성된 StockAnalysisSummary 리스트 (각 모델별 1개씩)
    """
    logger.info(f"📊 Generating stock report for {stock_code}")

    try:
        # 1. DB에서 컨텍스트 구축
        context = await build_analysis_context_from_db(stock_code, db)

        # 2. 데이터 가용성 확인
        data_sources = context.get("data_sources", {})
        available_count = sum(1 for v in data_sources.values() if v)

        if available_count == 0:
            logger.warning(f"No data available for {stock_code}")
            return []

        # 3. 적응형 프롬프트 생성
        from backend.llm.investment_report import build_adaptive_analysis_prompt
        prompt = build_adaptive_analysis_prompt(context)

        # 4. 모든 활성 모델 조회
        active_models: List[Model] = db.query(Model).filter(Model.is_active == True).all()

        if not active_models:
            logger.error("No active LLM model found")
            return []

        logger.info(f"📋 Generating reports for {len(active_models)} active models")

        # 5. 각 모델별로 리포트 생성
        from backend.llm.investment_report import get_report_generator
        generator = get_report_generator()

        created_summaries: List[StockAnalysisSummary] = []
        failed_models = []

        for model in active_models:
            try:
                logger.info(f"  🔄 Generating report with {model.name} ({model.provider})")

                # LLM 클라이언트 생성
                client = generator._create_client(model.provider)

                messages = [
                    {
                        "role": "system",
                        "content": "당신은 한국 주식 시장의 베테랑 애널리스트입니다. DB 데이터 기반으로 명확하고 실용적인 투자 리포트를 작성합니다.",
                    },
                    {"role": "user", "content": prompt},
                ]

                kwargs = {
                    "model": model.model_identifier,
                    "messages": messages,
                    "temperature": 0.4,
                    "max_tokens": 1000,
                }

                if model.provider != "openrouter":
                    kwargs["response_format"] = {"type": "json_object"}

                response = client.chat.completions.create(**kwargs)
                result_text = response.choices[0].message.content

                # OpenRouter JSON 추출
                if model.provider == "openrouter":
                    result_text = _extract_openrouter_json(result_text)

                # JSON 파싱
                report_data = json.loads(result_text)

                # DB에 저장
                summary = StockAnalysisSummary(
                    stock_code=stock_code,
                    model_id=model.id,
                    overall_summary=report_data.get("overall_summary"),
                    short_term_scenario=report_data.get("short_term_scenario"),
                    medium_term_scenario=report_data.get("medium_term_scenario"),
                    long_term_scenario=report_data.get("long_term_scenario"),
                    risk_factors=json.dumps(report_data.get("risk_factors", [])) if isinstance(report_data.get("risk_factors"), list) else report_data.get("risk_factors"),
                    opportunity_factors=json.dumps(report_data.get("opportunity_factors", [])) if isinstance(report_data.get("opportunity_factors"), list) else report_data.get("opportunity_factors"),
                    recommendation=report_data.get("recommendation"),
                    confidence_level=report_data.get("confidence_level", "medium"),
                    data_sources_used=data_sources,
                    limitations=report_data.get("limitations", []),
                    data_completeness_score=available_count / 6.0,  # 6개 데이터 소스
                    total_predictions=0,  # DB 기반 리포트는 예측 아님
                    based_on_prediction_count=0,
                    # 가격 목표치 (있으면 포함)
                    base_price=report_data.get("price_targets", {}).get("base_price"),
                    short_term_target_price=report_data.get("price_targets", {}).get("short_term_target"),
                    short_term_support_price=report_data.get("price_targets", {}).get("short_term_support"),
                    medium_term_target_price=report_data.get("price_targets", {}).get("medium_term_target"),
                    medium_term_support_price=report_data.get("price_targets", {}).get("medium_term_support"),
                    long_term_target_price=report_data.get("price_targets", {}).get("long_term_target"),
                )

                db.add(summary)
                created_summaries.append(summary)
                logger.info(f"  ✅ {model.name} report created (confidence={summary.confidence_level})")

            except Exception as model_error:
                logger.error(
                    f"  ❌ {model.name} report generation failed: {model_error}",
                    exc_info=True
                )
                failed_models.append(model.name)
                continue

        # 모든 모델 실패 시
        if not created_summaries:
            logger.error(f"❌ All models failed for {stock_code} (failed: {', '.join(failed_models)})")
            return []

        # DB 커밋
        db.commit()
        for summary in created_summaries:
            db.refresh(summary)

        logger.info(f"✅ Stock report completed: {len(created_summaries)}/{len(active_models)} models succeeded")
        if failed_models:
            logger.warning(f"⚠️  Failed models: {', '.join(failed_models)}")

        return created_summaries

    except Exception as e:
        logger.error(f"Failed to generate stock report for {stock_code}: {e}", exc_info=True)
        db.rollback()
        return []


async def generate_db_based_report(stock_code: str, db: Session) -> Optional[StockAnalysisSummary]:
    """
    [DEPRECATED] 하위 호환성을 위해 유지
    generate_stock_report() 사용 권장
    """
    reports = await generate_stock_report(stock_code, db)
    return reports[0] if reports else None


async def create_placeholder_report(stock_code: str, db: Session, error_msg: str):
    """
    오류 발생 시 placeholder 리포트 생성

    데이터 없이도 종목이 "추적 중" 목록에 나타나도록 함
    """
    summary = StockAnalysisSummary(
        stock_code=stock_code,
        overall_summary="데이터 수집 중입니다. 잠시 후 다시 확인해주세요.",
        recommendation="보류",
        confidence_level="low",
        data_sources_used={
            "market_data": False,
            "investor_trading": False,
            "financial_ratios": False,
            "product_info": False,
            "news": False
        },
        limitations=[f"초기 데이터 수집 실패: {error_msg}"]
    )

    db.add(summary)
    db.commit()
    logger.info(f"📝 Placeholder report created for {stock_code}")


async def build_analysis_context_from_db(stock_code: str, db: Session) -> Dict[str, Any]:
    """
    DB 쿼리만으로 분석 컨텍스트 생성 (KIS API 호출 0회)

    Returns:
        {
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "current_price": {...},
            "investor_trading": [...],
            "financial_ratios": [...],
            "product_info": {...},
            "technical_indicators": {...},
            "news": [...],
            "data_sources": {
                "market_data": True,
                "investor_trading": True,
                "financial_ratios": True,
                "product_info": True,
                "technical_indicators": False,
                "news": True
            }
        }
    """
    logger.debug(f"Building analysis context from DB for {stock_code}")

    context = {
        "stock_code": stock_code,
        "data_sources": {}
    }

    # Stock 기본 정보
    stock = db.query(Stock).filter(Stock.code == stock_code).first()
    if stock:
        context["stock_name"] = stock.name

    # Tier 1: DB 쿼리 (API 호출 없음)

    # 1. 현재가
    current_price = db.query(StockCurrentPrice).filter(
        StockCurrentPrice.stock_code == stock_code
    ).order_by(StockCurrentPrice.created_at.desc()).first()

    if current_price:
        context["current_price"] = {
            "current_price": current_price.stck_prpr,
            "change_rate": current_price.prdy_ctrt,
            "volume": current_price.acml_vol,
            "per": current_price.per,
            "pbr": current_price.pbr,
            "eps": current_price.eps,
            "bps": current_price.bps,
            "market_cap": current_price.hts_avls,
        }
    else:
        context["current_price"] = None
    context["data_sources"]["market_data"] = bool(current_price)

    # 2. 투자자 수급 (최근 5일)
    investor_trading = db.query(InvestorTrading).filter(
        InvestorTrading.stock_code == stock_code
    ).order_by(InvestorTrading.date.desc()).limit(5).all()

    if investor_trading:
        context["investor_trading"] = [{
            "date": it.date.isoformat() if it.date else None,
            "foreigner_net": it.frgn_ntby_qty,
            "institution_net": it.orgn_ntby_qty,
            "individual_net": it.prsn_ntby_qty,
        } for it in investor_trading]
    else:
        context["investor_trading"] = []
    context["data_sources"]["investor_trading"] = bool(investor_trading)

    # 3. 재무비율 (최근 3년)
    financial_ratios = db.query(FinancialRatio).filter(
        FinancialRatio.stock_code == stock_code
    ).order_by(FinancialRatio.stac_yymm.desc()).limit(3).all()

    if financial_ratios:
        context["financial_ratios"] = [{
            "stac_yymm": fr.stac_yymm,
            "roe_val": fr.roe_val,
            "eps": fr.eps,
            "bps": fr.bps,
            "lblt_rate": fr.lblt_rate,
        } for fr in financial_ratios]
    else:
        context["financial_ratios"] = []
    context["data_sources"]["financial_ratios"] = bool(financial_ratios)

    # 4. 상품정보
    product_info = db.query(ProductInfo).filter(
        ProductInfo.stock_code == stock_code
    ).first()

    if product_info:
        context["product_info"] = {
            "prdt_name": product_info.prdt_name,
            "prdt_clsf_name": product_info.prdt_clsf_name,
            "prdt_risk_grad_cd": product_info.prdt_risk_grad_cd,
        }
    else:
        context["product_info"] = None
    context["data_sources"]["product_info"] = bool(product_info)

    # Tier 2: 계산 (DB 데이터 기반)
    # 기술적 지표는 일봉 데이터가 있을 때만 계산
    technical_indicators = None
    try:
        from backend.utils.technical_indicators import calculate_technical_indicators
        technical_indicators = calculate_technical_indicators(stock_code, db)
    except Exception as e:
        logger.debug(f"Technical indicators unavailable for {stock_code}: {e}")

    context["technical_indicators"] = technical_indicators
    context["data_sources"]["technical_indicators"] = bool(technical_indicators)

    # Tier 3: 선택 (뉴스)
    news = db.query(NewsArticle).filter(
        NewsArticle.stock_code == stock_code
    ).order_by(NewsArticle.published_at.desc()).limit(10).all()

    if news:
        context["news"] = [{
            "title": n.title,
            "content": n.content,
            "published_at": n.published_at.isoformat() if n.published_at else None,
            "source": n.source,
            "url": n.url,
        } for n in news]
    else:
        context["news"] = []
    context["data_sources"]["news"] = bool(news)

    logger.debug(f"Context built: {context['data_sources']}")
    return context


async def should_update_report(
    stock_code: str,
    db: Session,
    existing_summary: Optional[StockAnalysisSummary],
    predictions: list,
    current_price: Optional[Dict[str, Any]],
    force_update: bool
) -> tuple[bool, str]:
    """
    리포트 업데이트 필요 여부 판단 (시장 시간 기반)

    Args:
        stock_code: 종목 코드
        db: Database session
        existing_summary: 기존 요약 (None이면 신규 생성)
        predictions: 최근 예측 리스트
        current_price: 현재 주가 정보
        force_update: 강제 업데이트 여부

    Returns:
        (업데이트 필요 여부, 사유)
    """
    if force_update or not existing_summary:
        return True, "강제 업데이트 또는 리포트 없음"

    market_phase = get_market_phase()
    staleness_hours = (datetime.now() - existing_summary.last_updated).total_seconds() / 3600

    # 트리거 1: 예측 개수 증가
    total_prediction_count = (
        db.query(func.count(Prediction.id))
        .filter(Prediction.stock_code == stock_code)
        .scalar()
    )

    if existing_summary.based_on_prediction_count < total_prediction_count:
        return True, (
            f"새 예측 추가 (기존: {existing_summary.based_on_prediction_count}, "
            f"현재: {total_prediction_count}, 시장: {market_phase})"
        )

    # 트리거 2: 시장 시간 기반 TTL 초과
    ttl_hours = get_ttl_hours(market_phase)
    if staleness_hours >= ttl_hours:
        return True, (
            f"시장 단계별 TTL 초과 ({market_phase}: {staleness_hours:.1f}h > {ttl_hours}h)"
        )

    # 트리거 3: 주가 급변 (장중만)
    if market_phase in ["market_open", "trading", "market_close"] and current_price:
        price_threshold = get_price_threshold(market_phase)
        price_change_rate = abs(current_price.get("change_rate", 0))

        if price_change_rate >= price_threshold:
            return True, (
                f"주가 급변 ({price_change_rate:.1f}%, 임계값: {price_threshold}%, "
                f"시장: {market_phase})"
            )

    # 트리거 4: 예측 방향 변화
    if predictions:
        current_up_ratio = sum(1 for p in predictions if p.direction == "up") / len(predictions)
        report_up_ratio = existing_summary.up_count / existing_summary.total_predictions if existing_summary.total_predictions > 0 else 0

        direction_threshold = get_direction_threshold(market_phase)
        direction_change = abs(current_up_ratio - report_up_ratio)

        if direction_change >= direction_threshold:
            return True, (
                f"예측 방향 급변 (상승 비율: {report_up_ratio:.1%} → {current_up_ratio:.1%}, "
                f"변화: {direction_change:.1%}, 임계값: {direction_threshold:.1%}, 시장: {market_phase})"
            )

    return False, f"업데이트 불필요 (시장: {market_phase}, 경과: {staleness_hours:.1f}h/{ttl_hours}h)"


async def update_stock_analysis_summary(
    stock_code: str,
    db: Session,
    force_update: bool = False
) -> Optional[StockAnalysisSummary]:
    """
    종목 투자 분석 요약 업데이트 (LLM 기반)

    Args:
        stock_code: 종목 코드
        db: Database session
        force_update: 강제 업데이트 여부 (기본값: False)

    Returns:
        StockAnalysisSummary 인스턴스 또는 None (실패 시)
    """
    try:
        # 1. 최근 30일 예측 데이터 조회 (최대 20건)
        predictions = (
            db.query(Prediction)
            .filter(Prediction.stock_code == stock_code)
            .order_by(Prediction.created_at.desc())
            .limit(20)
            .all()
        )

        if not predictions:
            logger.warning(f"종목 {stock_code}에 대한 예측 데이터가 없습니다.")
            return None

        # 2. 현재가 정보 조회
        current_price_obj = (
            db.query(StockPrice)
            .filter(StockPrice.stock_code == stock_code)
            .order_by(StockPrice.date.desc())
            .first()
        )

        current_price = None
        if current_price_obj:
            # 전일 대비 변동률 계산
            previous_price_obj = (
                db.query(StockPrice)
                .filter(
                    StockPrice.stock_code == stock_code,
                    StockPrice.date < current_price_obj.date
                )
                .order_by(StockPrice.date.desc())
                .first()
            )

            change_rate = 0.0
            if previous_price_obj and previous_price_obj.close > 0:
                change_rate = ((current_price_obj.close - previous_price_obj.close) / previous_price_obj.close) * 100

            current_price = {
                "close": current_price_obj.close,
                "change_rate": round(change_rate, 2),
            }

        # 3. 기존 요약 조회
        existing_summary = (
            db.query(StockAnalysisSummary)
            .filter(StockAnalysisSummary.stock_code == stock_code)
            .order_by(StockAnalysisSummary.last_updated.desc())
            .first()
        )

        # 4. 업데이트 필요 여부 확인 (시장 시간 기반 다중 트리거)
        should_update, reason = await should_update_report(
            stock_code, db, existing_summary, predictions, current_price, force_update
        )

        if not should_update:
            logger.info(f"종목 {stock_code}의 분석 요약이 최신 상태입니다. ({reason})")
            return existing_summary

        logger.info(f"종목 {stock_code} 업데이트 시작: {reason}")

        # 5. LLM 리포트 생성 (모든 활성 모델 대상)
        active_models: List[Model] = (
            db.query(Model).filter(Model.is_active == True).all()
        )

        if not active_models:
            logger.error("활성화된 LLM 모델이 없습니다. 리포트 생성을 중단합니다.")
            return None

        generator = get_report_generator()
        report_data = generator._prepare_report_data(
            stock_code, predictions, current_price
        )
        prompt = generator._build_prompt(report_data)

        total_predictions = len(predictions)
        up_count = sum(1 for p in predictions if p.direction == "up")
        down_count = sum(1 for p in predictions if p.direction == "down")
        hold_count = sum(1 for p in predictions if p.direction == "hold")
        confidences = [p.confidence for p in predictions if p.confidence]
        avg_confidence = sum(confidences) / len(confidences) if confidences else None

        created_summaries: List[StockAnalysisSummary] = []
        failed_models = []

        for model in active_models:
            try:
                logger.info(
                    f"모델 {model.name} ({model.provider}/{model.model_identifier}) 리포트 생성 시작"
                )
                report_payload = _generate_report_for_model(
                    generator=generator,
                    model=model,
                    prompt=prompt,
                )

                if not report_payload:
                    logger.warning(
                        f"⚠️ 모델 {model.name} 리포트 생성 실패 (빈 응답): {stock_code}"
                    )
                    failed_models.append(model.name)
                    continue

                summary = _build_summary_from_payload(
                    stock_code=stock_code,
                    model=model,
                    report_payload=report_payload,
                    total_predictions=total_predictions,
                    up_count=up_count,
                    down_count=down_count,
                    hold_count=hold_count,
                    avg_confidence=avg_confidence,
                )
                db.add(summary)
                created_summaries.append(summary)
                logger.info(
                    f"  ✅ 모델 {model.name} 리포트 생성 완료 (stock={stock_code})"
                )
            except Exception as model_error:
                logger.error(
                    f"❌ 모델 {model.name} 리포트 생성 중 예외 발생: {model_error}",
                    exc_info=True
                )
                failed_models.append(model.name)
                continue

        # 모든 모델 실패 시 기존 리포트 유지 (롤백하지 않음)
        if not created_summaries:
            logger.error(
                f"❌ 모든 모델 리포트 생성 실패: {stock_code} "
                f"(실패 모델: {', '.join(failed_models)})"
            )
            # 기존 리포트가 있으면 유지하기 위해 롤백하지 않음
            db.rollback()
            # 기존 리포트 반환 (있으면)
            if existing_summary:
                logger.warning(
                    f"⚠️ 기존 리포트 유지: {stock_code} "
                    f"(마지막 업데이트: {existing_summary.last_updated})"
                )
                return existing_summary
            return None

        # DB 커밋 시도 (재시도 로직 포함)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.commit()
                for summary in created_summaries:
                    db.refresh(summary)

                # 일부 모델 실패 시 경고 로그
                if failed_models:
                    logger.warning(
                        f"⚠️ 일부 모델 실패 (성공: {len(created_summaries)}/{len(active_models)}): "
                        f"{stock_code} (실패 모델: {', '.join(failed_models)})"
                    )
                else:
                    logger.info(
                        f"✅ 모든 모델 리포트 생성 성공 ({len(created_summaries)}/{len(active_models)}): {stock_code}"
                    )

                return created_summaries[0]
            except Exception as commit_error:
                db.rollback()
                if attempt < max_retries - 1:
                    logger.warning(
                        f"⚠️ DB 커밋 실패 (재시도 {attempt + 1}/{max_retries}): {commit_error}"
                    )
                    # 짧은 대기 후 재시도
                    import time
                    time.sleep(0.1 * (attempt + 1))
                else:
                    logger.error(
                        f"❌ DB 커밋 최종 실패 ({max_retries}회 시도): {commit_error}",
                        exc_info=True
                    )
                    # 기존 리포트 반환
                    if existing_summary:
                        logger.warning(
                            f"⚠️ 커밋 실패로 기존 리포트 유지: {stock_code}"
                        )
                        return existing_summary
                    return None

    except Exception as e:
        logger.error(f"종목 {stock_code}의 분석 요약 업데이트 실패: {e}", exc_info=True)
        db.rollback()
        return None


def get_stock_analysis_summary(
    stock_code: str,
    db: Session
) -> Optional[Dict[str, Any]]:
    """
    종목 투자 분석 요약 조회

    Args:
        stock_code: 종목 코드
        db: Database session

    Returns:
        분석 요약 딕셔너리 또는 None
    """
    try:
        from backend.config import settings

        model_map = {
            model.id: model for model in db.query(Model).all()
        }

        ab_config: Optional[ABTestConfig] = None
        if settings.AB_TEST_ENABLED:
            ab_config = (
                db.query(ABTestConfig)
                .filter(ABTestConfig.is_active == True)
                .first()
            )

        if ab_config:
            report_a = _fetch_latest_summary(
                db, stock_code, model_id=ab_config.model_a_id
            )
            report_b = _fetch_latest_summary(
                db, stock_code, model_id=ab_config.model_b_id
            )

            if report_a and report_b:
                formatted_a = _format_summary_output(report_a, model_map)
                formatted_b = _format_summary_output(report_b, model_map)
                comparison = _build_comparison(formatted_a, formatted_b)
                meta_last_updated = max(
                    report_a.last_updated or datetime.min,
                    report_b.last_updated or datetime.min,
                )
                meta_prediction_count = max(
                    report_a.based_on_prediction_count or 0,
                    report_b.based_on_prediction_count or 0,
                )

                return {
                    "ab_test_enabled": True,
                    "model_a": formatted_a,
                    "model_b": formatted_b,
                    "comparison": comparison,
                    "meta": {
                        "last_updated": meta_last_updated.isoformat()
                        if meta_last_updated
                        else None,
                        "based_on_prediction_count": meta_prediction_count,
                    },
                }

        # A/B 비활성화 또는 모델 리포트 미존재 시 최신 리포트 1건 반환
        summary = _fetch_latest_summary(db, stock_code)

        if not summary:
            return None

        return _format_summary_output(summary, model_map)

    except Exception as e:
        logger.error(f"종목 {stock_code}의 분석 요약 조회 실패: {e}", exc_info=True)
        return None


def _generate_report_for_model(
    generator,
    model: Model,
    prompt: str,
) -> Optional[Dict[str, Any]]:
    """주어진 모델로 LLM 리포트를 생성."""
    try:
        client = generator._create_client(model.provider)
        messages = [
            {
                "role": "system",
                "content": "당신은 한국 주식 시장의 베테랑 애널리스트입니다. 데이터 기반으로 명확하고 실용적인 투자 리포트를 작성합니다.",
            },
            {"role": "user", "content": prompt},
        ]

        kwargs = {
            "model": model.model_identifier,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 1000,
        }

        if model.provider != "openrouter":
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)
        result_text = response.choices[0].message.content

        if model.provider == "openrouter":
            result_text = _extract_openrouter_json(result_text)

        return json.loads(result_text)
    except Exception as e:
        logger.error(
            f"모델 {model.name} ({model.provider}) 리포트 생성 실패: {e}",
            exc_info=True,
        )
        return None


def _build_summary_from_payload(
    stock_code: str,
    model: Model,
    report_payload: Dict[str, Any],
    total_predictions: int,
    up_count: int,
    down_count: int,
    hold_count: int,
    avg_confidence: Optional[float],
) -> StockAnalysisSummary:
    """LLM 응답을 StockAnalysisSummary 엔티티로 변환."""
    price_targets = report_payload.get("price_targets") or {}
    now = datetime.now()

    # JSON 필드는 직렬화된 문자열로 저장
    risk_factors = report_payload.get("risk_factors", [])
    opportunity_factors = report_payload.get("opportunity_factors", [])

    return StockAnalysisSummary(
        stock_code=stock_code,
        model_id=model.id,
        overall_summary=report_payload.get("overall_summary"),
        short_term_scenario=report_payload.get("short_term_scenario"),
        medium_term_scenario=report_payload.get("medium_term_scenario"),
        long_term_scenario=report_payload.get("long_term_scenario"),
        risk_factors=json.dumps(risk_factors) if isinstance(risk_factors, list) else risk_factors,
        opportunity_factors=json.dumps(opportunity_factors) if isinstance(opportunity_factors, list) else opportunity_factors,
        recommendation=report_payload.get("recommendation"),
        custom_data=json.dumps({
            "model_id": model.id,
            "model_name": model.name,
            "raw_report": report_payload,
        }),
        total_predictions=total_predictions,
        up_count=up_count,
        down_count=down_count,
        hold_count=hold_count,
        avg_confidence=avg_confidence,
        base_price=price_targets.get("base_price"),
        short_term_target_price=price_targets.get("short_term_target"),
        short_term_support_price=price_targets.get("short_term_support"),
        medium_term_target_price=price_targets.get("medium_term_target"),
        medium_term_support_price=price_targets.get("medium_term_support"),
        long_term_target_price=price_targets.get("long_term_target"),
        last_updated=now,
        based_on_prediction_count=total_predictions,
    )


def _extract_openrouter_json(text: str) -> str:
    """OpenRouter 응답에서 JSON 부분만 추출."""
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        return json_match.group(1)

    json_match = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        return json_match.group(1)

    json_match = re.search(r"(\{[^{]*\"overall_summary\".*\})\s*$", text, re.DOTALL)
    if json_match:
        return json_match.group(1)

    return text


def _fetch_latest_summary(
    db: Session,
    stock_code: str,
    model_id: Optional[int] = None,
) -> Optional[StockAnalysisSummary]:
    """특정 종목(+모델)의 최신 리포트 조회."""
    query = db.query(StockAnalysisSummary).filter(
        StockAnalysisSummary.stock_code == stock_code
    )
    if model_id is not None:
        query = query.filter(StockAnalysisSummary.model_id == model_id)

    return query.order_by(StockAnalysisSummary.last_updated.desc()).first()


def _format_summary_output(
    summary: StockAnalysisSummary,
    model_map: Dict[int, Model],
) -> Dict[str, Any]:
    """StockAnalysisSummary 엔티티를 API 응답 형태로 변환."""
    model_info = model_map.get(summary.model_id) if summary.model_id else None
    statistics = {
        "total_predictions": summary.total_predictions,
        "up_count": summary.up_count,
        "down_count": summary.down_count,
        "hold_count": summary.hold_count,
        "avg_confidence": round(summary.avg_confidence * 100, 1)
        if summary.avg_confidence
        else None,
    }
    price_targets = {
        "base_price": summary.base_price,
        "short_term_target": summary.short_term_target_price,
        "short_term_support": summary.short_term_support_price,
        "medium_term_target": summary.medium_term_target_price,
        "medium_term_support": summary.medium_term_support_price,
        "long_term_target": summary.long_term_target_price,
    }

    # JSON 문자열 파싱
    risk_factors = summary.risk_factors
    if isinstance(risk_factors, str):
        try:
            risk_factors = json.loads(risk_factors)
        except:
            risk_factors = []
    elif risk_factors is None:
        risk_factors = []

    opportunity_factors = summary.opportunity_factors
    if isinstance(opportunity_factors, str):
        try:
            opportunity_factors = json.loads(opportunity_factors)
        except:
            opportunity_factors = []
    elif opportunity_factors is None:
        opportunity_factors = []

    return {
        "model_id": summary.model_id,
        "model_name": model_info.name if model_info else None,
        "overall_summary": summary.overall_summary,
        "short_term_scenario": summary.short_term_scenario,
        "medium_term_scenario": summary.medium_term_scenario,
        "long_term_scenario": summary.long_term_scenario,
        "risk_factors": risk_factors,
        "opportunity_factors": opportunity_factors,
        "recommendation": summary.recommendation,
        "price_targets": price_targets,
        "statistics": statistics,
        "meta": {
            "last_updated": summary.last_updated.isoformat()
            if summary.last_updated
            else None,
            "based_on_prediction_count": summary.based_on_prediction_count,
        },
    }


def _build_comparison(
    report_a: Dict[str, Any],
    report_b: Dict[str, Any],
) -> Dict[str, Any]:
    """두 리포트를 비교하여 공통점 도출."""
    rec_a = (report_a.get("recommendation") or "").lower()
    rec_b = (report_b.get("recommendation") or "").lower()

    recommendation_match = False
    if ("매수" in rec_a and "매수" in rec_b) or \
       ("매도" in rec_a and "매도" in rec_b) or \
       ("관망" in rec_a and "관망" in rec_b) or \
       ("보유" in rec_a and "보유" in rec_b):
        recommendation_match = True

    risks_a = set(report_a.get("risk_factors") or [])
    risks_b = set(report_b.get("risk_factors") or [])
    opps_a = set(report_a.get("opportunity_factors") or [])
    opps_b = set(report_b.get("opportunity_factors") or [])

    return {
        "recommendation_match": recommendation_match,
        "risk_overlap": list(risks_a & risks_b),
        "opportunity_overlap": list(opps_a & opps_b),
    }

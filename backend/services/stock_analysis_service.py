"""
Stock Analysis Service

예측 생성 시 자동으로 종합 투자 리포트를 업데이트하는 서비스
"""
import logging
import json
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.models.prediction import Prediction
from backend.db.models.stock_analysis import StockAnalysisSummary
from backend.db.models.stock import StockPrice
from backend.db.models.model import Model
from backend.db.models.ab_test_config import ABTestConfig
from backend.llm.investment_report import get_report_generator
from backend.utils.stock_mapping import get_stock_mapper
from backend.utils.market_time import (
    get_market_phase,
    get_ttl_hours,
    get_price_threshold,
    get_direction_threshold
)


logger = logging.getLogger(__name__)


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

    return StockAnalysisSummary(
        stock_code=stock_code,
        model_id=model.id,
        overall_summary=report_payload.get("overall_summary"),
        short_term_scenario=report_payload.get("short_term_scenario"),
        medium_term_scenario=report_payload.get("medium_term_scenario"),
        long_term_scenario=report_payload.get("long_term_scenario"),
        risk_factors=report_payload.get("risk_factors", []),
        opportunity_factors=report_payload.get("opportunity_factors", []),
        recommendation=report_payload.get("recommendation"),
        custom_data={
            "model_id": model.id,
            "model_name": model.name,
            "raw_report": report_payload,
        },
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

    return {
        "model_id": summary.model_id,
        "model_name": model_info.name if model_info else None,
        "overall_summary": summary.overall_summary,
        "short_term_scenario": summary.short_term_scenario,
        "medium_term_scenario": summary.medium_term_scenario,
        "long_term_scenario": summary.long_term_scenario,
        "risk_factors": summary.risk_factors or [],
        "opportunity_factors": summary.opportunity_factors or [],
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

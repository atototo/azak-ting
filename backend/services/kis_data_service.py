"""
KIS Data Service - 재무비율 및 상품정보 저장 서비스

KIS API에서 조회한 데이터를 DB에 저장하는 함수들을 제공합니다.
"""
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from backend.db.models.financial import ProductInfo, FinancialRatio
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def save_product_info(db: Session, stock_code: str, api_data: Dict[str, Any]) -> ProductInfo:
    """
    상품정보 저장 (UPSERT)

    Args:
        db: DB 세션
        stock_code: 종목코드
        api_data: KIS API 응답 데이터

    Returns:
        저장된 ProductInfo 객체

    Raises:
        Exception: DB 저장 실패 시
    """
    output = api_data.get("output", {})

    try:
        # UPSERT (PostgreSQL)
        stmt = insert(ProductInfo).values(
            stock_code=stock_code,
            prdt_name=output.get("prdt_name"),
            prdt_clsf_name=output.get("prdt_clsf_name"),
            ivst_prdt_type_cd_name=output.get("ivst_prdt_type_cd_name"),
            prdt_risk_grad_cd=output.get("prdt_risk_grad_cd"),
            frst_erlm_dt=output.get("frst_erlm_dt")
        ).on_conflict_do_update(
            index_elements=['stock_code'],
            set_={
                'prdt_name': output.get("prdt_name"),
                'prdt_clsf_name': output.get("prdt_clsf_name"),
                'ivst_prdt_type_cd_name': output.get("ivst_prdt_type_cd_name"),
                'prdt_risk_grad_cd': output.get("prdt_risk_grad_cd"),
                'frst_erlm_dt': output.get("frst_erlm_dt")
            }
        )

        db.execute(stmt)
        db.commit()

        # 저장된 객체 반환
        product_info = db.query(ProductInfo).filter(ProductInfo.stock_code == stock_code).first()
        logger.info(f"✅ 상품정보 저장 완료: {stock_code} - {output.get('prdt_name')}")
        return product_info

    except Exception as e:
        db.rollback()
        logger.error(f"❌ 상품정보 저장 실패: {stock_code}, {e}")
        raise


def save_financial_ratios(db: Session, stock_code: str, api_data: Dict[str, Any]) -> List[FinancialRatio]:
    """
    재무비율 저장 (중복 방지)

    Args:
        db: DB 세션
        stock_code: 종목코드
        api_data: KIS API 응답 데이터

    Returns:
        저장된 FinancialRatio 객체 리스트

    Raises:
        Exception: DB 저장 실패 시
    """
    output_list = api_data.get("output", [])
    saved_ratios = []

    try:
        for ratio_data in output_list:
            stac_yymm = ratio_data.get("stac_yymm")
            div_cls_code = ratio_data.get("div_cls_code", "0")

            # 중복 체크
            existing = db.query(FinancialRatio).filter(
                FinancialRatio.stock_code == stock_code,
                FinancialRatio.stac_yymm == stac_yymm,
                FinancialRatio.div_cls_code == div_cls_code
            ).first()

            if existing:
                logger.debug(f"재무비율 이미 존재: {stock_code} {stac_yymm} (div: {div_cls_code})")
                continue

            # 신규 삽입
            ratio = FinancialRatio(
                stock_code=stock_code,
                stac_yymm=stac_yymm,
                div_cls_code=div_cls_code,
                grs=float(ratio_data.get("grs", 0)) if ratio_data.get("grs") else None,
                bsop_prfi_inrt=float(ratio_data.get("bsop_prfi_inrt", 0)) if ratio_data.get("bsop_prfi_inrt") else None,
                ntin_inrt=float(ratio_data.get("ntin_inrt", 0)) if ratio_data.get("ntin_inrt") else None,
                roe_val=float(ratio_data.get("roe_val", 0)) if ratio_data.get("roe_val") else None,
                eps=float(ratio_data.get("eps", 0)) if ratio_data.get("eps") else None,
                bps=float(ratio_data.get("bps", 0)) if ratio_data.get("bps") else None,
                lblt_rate=float(ratio_data.get("lblt_rate", 0)) if ratio_data.get("lblt_rate") else None,
                rsrv_rate=float(ratio_data.get("rsrv_rate", 0)) if ratio_data.get("rsrv_rate") else None
            )

            db.add(ratio)
            saved_ratios.append(ratio)
            logger.debug(f"재무비율 추가: {stock_code} {stac_yymm} (div: {div_cls_code})")

        db.commit()
        logger.info(f"✅ 재무비율 저장 완료: {stock_code} - {len(saved_ratios)}건")
        return saved_ratios

    except Exception as e:
        db.rollback()
        logger.error(f"❌ 재무비율 저장 실패: {stock_code}, {e}")
        raise

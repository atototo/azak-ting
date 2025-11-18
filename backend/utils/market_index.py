"""
시장 지수 조회 유틸리티
KOSPI/KOSDAQ 지수 데이터를 조회합니다.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.db.models.market_data import SectorIndex


def get_market_indices(db: Session, hours: int = 24) -> Dict[str, Any]:
    """
    KOSPI/KOSDAQ 시장 지수 조회

    Args:
        db: 데이터베이스 세션
        hours: 조회할 시간 범위 (기본 24시간)

    Returns:
        {
            "kospi": {"index": float, "change_rate": float, "datetime": str} or None,
            "kosdaq": {"index": float, "change_rate": float, "datetime": str} or None,
        }
    """
    since = datetime.now() - timedelta(hours=hours)
    result = {}

    # KOSPI 지수 (0001)
    kospi = db.query(SectorIndex).filter(
        SectorIndex.sector_code == '0001',
        SectorIndex.datetime >= since
    ).order_by(SectorIndex.datetime.desc()).first()

    if kospi:
        result["kospi"] = {
            "index": kospi.bstp_nmix_prpr or 0.0,
            "change_rate": kospi.bstp_nmix_prdy_ctrt or 0.0,
            "datetime": kospi.datetime.strftime("%Y-%m-%d %H:%M:%S") if kospi.datetime else None,
        }
    else:
        result["kospi"] = None

    # KOSDAQ 지수 (1001)
    kosdaq = db.query(SectorIndex).filter(
        SectorIndex.sector_code == '1001',
        SectorIndex.datetime >= since
    ).order_by(SectorIndex.datetime.desc()).first()

    if kosdaq:
        result["kosdaq"] = {
            "index": kosdaq.bstp_nmix_prpr or 0.0,
            "change_rate": kosdaq.bstp_nmix_prdy_ctrt or 0.0,
            "datetime": kosdaq.datetime.strftime("%Y-%m-%d %H:%M:%S") if kosdaq.datetime else None,
        }
    else:
        result["kosdaq"] = None

    return result


def format_market_indices(indices: Dict[str, Any]) -> str:
    """
    시장 지수를 프롬프트용 텍스트로 간단하게 포맷팅
    해석은 LLM이 하도록 데이터만 제공

    Args:
        indices: get_market_indices()의 결과

    Returns:
        포맷팅된 텍스트
    """
    if not indices:
        return "시장 지수 데이터 없음"

    lines = []

    kospi = indices.get("kospi")
    if kospi:
        lines.append(f"- KOSPI: {kospi['index']:,.2f} ({kospi['change_rate']:+.2f}%)")

    kosdaq = indices.get("kosdaq")
    if kosdaq:
        lines.append(f"- KOSDAQ: {kosdaq['index']:,.2f} ({kosdaq['change_rate']:+.2f}%)")

    return "\n".join(lines) if lines else "시장 지수 데이터 없음"

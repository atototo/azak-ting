"""
종목 관리 API (Admin)

종목 추가, 수정, 삭제 기능을 제공합니다.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import logging
import re
import asyncio

from backend.db.session import get_db, SessionLocal
from backend.db.models.stock import Stock
from backend.services.stock_analysis_service import trigger_initial_analysis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/stocks", tags=["stock-management"])


# Request/Response Models
class StockCreate(BaseModel):
    """종목 생성 요청"""
    code: str = Field(..., min_length=6, max_length=6, description="종목 코드 (6자리, 숫자 또는 영문 대문자)")
    name: str = Field(..., min_length=1, max_length=100, description="종목명")
    priority: int = Field(default=5, ge=1, le=5, description="우선순위 (1~5)")

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """종목 코드 유효성 검사: 6자리 숫자 또는 영문 대문자"""
        v = v.upper()  # 자동으로 대문자 변환
        if not re.match(r'^[0-9A-Z]{6}$', v):
            raise ValueError('종목 코드는 6자리 숫자 또는 영문 대문자여야 합니다 (예: 005930, 0126Z0)')
        return v


class StockUpdate(BaseModel):
    """종목 수정 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="종목명")
    priority: Optional[int] = Field(None, ge=1, le=5, description="우선순위 (1~5)")
    is_active: Optional[bool] = Field(None, description="활성화 여부")


class StockResponse(BaseModel):
    """종목 응답"""
    id: int
    code: str
    name: str
    priority: int
    is_active: bool

    class Config:
        from_attributes = True


class StockListResponse(BaseModel):
    """종목 목록 응답"""
    total: int
    stocks: List[StockResponse]


# API Endpoints
@router.post("", response_model=StockResponse, status_code=201)
async def create_stock(stock: StockCreate, db: Session = Depends(get_db)):
    """
    새 종목을 추가하고 즉시 분석을 실행합니다.

    - **code**: 종목 코드 (6자리, 예: 005930)
    - **name**: 종목명 (예: 삼성전자)
    - **priority**: 우선순위 1~5 (낮을수록 우선, 기본값: 5, deprecated)
    """
    logger.info(f"📝 Registering stock: {stock.code} ({stock.name})")

    # 중복 체크
    existing = db.query(Stock).filter(Stock.code == stock.code).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"이미 존재하는 종목 코드입니다: {stock.code}"
        )

    # 종목 생성
    new_stock = Stock(
        code=stock.code,
        name=stock.name,
        priority=stock.priority,  # deprecated, 하지만 하위 호환성 유지
        is_active=True
    )

    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)

    logger.info(f"✅ Stock saved: {stock.code}")

    # 백그라운드에서 초기 분석 실행 (비동기, 응답 즉시 반환)
    asyncio.create_task(_run_initial_analysis_background(stock.code))
    logger.info(f"🚀 Initial analysis scheduled for {stock.code}")

    return new_stock


async def _run_initial_analysis_background(stock_code: str):
    """
    백그라운드에서 초기 분석을 실행합니다.

    새로운 DB 세션을 생성하여 안전하게 처리합니다.
    """
    db = SessionLocal()
    try:
        await trigger_initial_analysis(stock_code, db)
        logger.info(f"✅ Background initial analysis completed for {stock_code}")
    except Exception as e:
        logger.error(f"❌ Background initial analysis failed for {stock_code}: {e}", exc_info=True)
    finally:
        db.close()


@router.get("", response_model=StockListResponse)
def get_stocks(
    priority: Optional[int] = Query(None, ge=1, le=5, description="우선순위 필터"),
    is_active: Optional[bool] = Query(None, description="활성화 상태 필터"),
    search: Optional[str] = Query(None, description="종목명 또는 코드 검색"),
    db: Session = Depends(get_db)
):
    """
    종목 목록을 조회합니다.

    - **priority**: 우선순위로 필터링 (1~5)
    - **is_active**: 활성화 상태로 필터링
    - **search**: 종목명 또는 코드로 검색
    """
    query = db.query(Stock)

    # 필터 적용
    if priority is not None:
        query = query.filter(Stock.priority == priority)

    if is_active is not None:
        query = query.filter(Stock.is_active == is_active)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Stock.name.like(search_pattern)) | (Stock.code.like(search_pattern))
        )

    # 정렬: 우선순위 오름차순, 이름 오름차순
    query = query.order_by(Stock.priority, Stock.name)

    stocks = query.all()
    total = len(stocks)

    return StockListResponse(total=total, stocks=stocks)


@router.get("/{stock_code}", response_model=StockResponse)
def get_stock(stock_code: str, db: Session = Depends(get_db)):
    """
    특정 종목 정보를 조회합니다.

    - **stock_code**: 종목 코드 (6자리)
    """
    stock = db.query(Stock).filter(Stock.code == stock_code).first()

    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"종목을 찾을 수 없습니다: {stock_code}"
        )

    return stock


@router.put("/{stock_code}", response_model=StockResponse)
def update_stock(
    stock_code: str,
    stock_update: StockUpdate,
    db: Session = Depends(get_db)
):
    """
    종목 정보를 수정합니다.

    - **stock_code**: 종목 코드 (6자리)
    - **name**: 종목명 (선택)
    - **priority**: 우선순위 (선택)
    - **is_active**: 활성화 여부 (선택)
    """
    stock = db.query(Stock).filter(Stock.code == stock_code).first()

    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"종목을 찾을 수 없습니다: {stock_code}"
        )

    # 업데이트
    update_data = stock_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(stock, field, value)

    db.commit()
    db.refresh(stock)

    return stock


@router.delete("/{stock_code}", status_code=204)
def delete_stock(stock_code: str, db: Session = Depends(get_db)):
    """
    종목을 비활성화합니다 (소프트 삭제).

    - **stock_code**: 종목 코드 (6자리)
    """
    stock = db.query(Stock).filter(Stock.code == stock_code).first()

    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"종목을 찾을 수 없습니다: {stock_code}"
        )

    # 소프트 삭제 (비활성화)
    stock.is_active = False
    db.commit()

    return None

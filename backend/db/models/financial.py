"""
Financial data models for storing product information and financial ratios.

NOTE: 데이터 무결성은 애플리케이션 레벨에서 관리합니다.
      Foreign Key 제약조건을 사용하지 않아 성능을 최적화했습니다.
      stock_code는 반드시 stocks 테이블에 존재하는 값이어야 합니다.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint, Index
from datetime import datetime
from backend.db.base import Base


class ProductInfo(Base):
    """
    상품 정보 테이블 (KIS API에서 수집한 상품 메타데이터).

    stock_info 테이블과의 차이:
    - stock_info: 업종, 시가총액, 상장주식수 등 숫자 중심의 시장 데이터
    - product_info: 상품명, 분류, 위험등급 등 텍스트 중심의 상품 메타데이터

    Attributes:
        id: Primary key
        stock_code: 종목 코드 (stocks.code와 연결, 애플리케이션 레벨에서 무결성 관리)
        prdt_name: 상품명 (예: "삼성전자")
        prdt_clsf_name: 상품분류명 (예: "주권")
        ivst_prdt_type_cd_name: 투자상품유형명 (예: "보통주")
        prdt_risk_grad_cd: 위험등급코드 (예: "3" - 중위험)
        frst_erlm_dt: 최초등록일 (YYYYMMDD 형식)
        created_at: 생성일시
        updated_at: 수정일시

    Note:
        - stock_code는 UNIQUE 제약조건으로 중복 방지
        - 데이터 삽입 전 stocks 테이블에 해당 종목 존재 확인 필수
    """

    __tablename__ = "product_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), unique=True, nullable=False, comment="종목 코드 (stocks.code 참조)")
    prdt_name = Column(String(120), comment="상품명")
    prdt_clsf_name = Column(String(100), comment="상품분류명 (예: 주권)")
    ivst_prdt_type_cd_name = Column(String(100), comment="투자상품유형명 (예: 보통주)")
    prdt_risk_grad_cd = Column(String(10), comment="위험등급코드")
    frst_erlm_dt = Column(String(8), comment="최초등록일 (YYYYMMDD)")
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="수정일시")

    def __repr__(self) -> str:
        return (
            f"<ProductInfo(id={self.id}, stock_code='{self.stock_code}', "
            f"prdt_name='{self.prdt_name}')>"
        )


class FinancialRatio(Base):
    """
    재무비율 테이블 (KIS API에서 수집한 재무 지표).

    뉴스 없이도 펀더멘털 데이터 기반 분석을 가능하게 합니다.
    년도별, 분기별 재무비율 데이터를 저장합니다.

    Attributes:
        id: Primary key
        stock_code: 종목 코드 (stocks.code 참조, 애플리케이션 레벨에서 무결성 관리)
        stac_yymm: 결산년월 (YYYYMM 형식, 예: "202312")
        div_cls_code: 구분코드 (0: 년도, 1: 분기)

        [성장성 지표]
        grs: 매출액증가율 (Growth Rate of Sales, %)
        bsop_prfi_inrt: 영업이익증가율 (Business Operating Profit Increase Rate, %)
        ntin_inrt: 순이익증가율 (Net Income Increase Rate, %)

        [수익성 지표]
        roe_val: 자기자본이익률 (Return on Equity, %)

        [주당 지표]
        eps: 주당순이익 (Earnings Per Share, 원)
        bps: 주당순자산 (Book value Per Share, 원)

        [안정성 지표]
        lblt_rate: 부채비율 (Liability Rate, %)
        rsrv_rate: 유보율 (Reserve Rate, %)

        created_at: 생성일시
        updated_at: 수정일시

    Note:
        - (stock_code, stac_yymm, div_cls_code) 조합으로 UNIQUE 제약
        - 데이터 삽입 전 stocks 테이블에 해당 종목 존재 확인 필수
        - idx_financial_ratios_stock_stac 인덱스로 최신 데이터 조회 최적화
    """

    __tablename__ = "financial_ratios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, comment="종목 코드 (stocks.code 참조)")
    stac_yymm = Column(String(6), nullable=False, comment="결산년월 (YYYYMM)")
    div_cls_code = Column(String(1), default='0', nullable=False, comment="구분코드 (0:년도, 1:분기)")

    # 성장성 지표
    grs = Column(Float, comment="매출액증가율 (%)")
    bsop_prfi_inrt = Column(Float, comment="영업이익증가율 (%)")
    ntin_inrt = Column(Float, comment="순이익증가율 (%)")

    # 수익성 지표
    roe_val = Column(Float, comment="자기자본이익률 ROE (%)")

    # 주당 지표
    eps = Column(Float, comment="주당순이익 EPS (원)")
    bps = Column(Float, comment="주당순자산 BPS (원)")

    # 안정성 지표
    lblt_rate = Column(Float, comment="부채비율 (%)")
    rsrv_rate = Column(Float, comment="유보율 (%)")

    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="수정일시")

    __table_args__ = (
        UniqueConstraint('stock_code', 'stac_yymm', 'div_cls_code', name='uq_financial_ratios'),
        Index('idx_financial_ratios_stock_code', 'stock_code'),
        Index('idx_financial_ratios_stock_stac', 'stock_code', 'stac_yymm'),
    )

    def __repr__(self) -> str:
        return (
            f"<FinancialRatio(id={self.id}, stock_code='{self.stock_code}', "
            f"stac_yymm='{self.stac_yymm}', div_cls_code='{self.div_cls_code}')>"
        )

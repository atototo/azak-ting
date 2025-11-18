"""
Integration tests for KIS API - Financial Ratios and Product Info

These tests require:
1. RUN_INTEGRATION_TESTS=true environment variable
2. Valid KIS_APP_KEY and KIS_APP_SECRET in environment
3. Running database connection

Usage:
    RUN_INTEGRATION_TESTS=true pytest tests/integration/test_kis_api_integration.py -v
"""
import pytest
from backend.crawlers.kis_client import get_kis_client
from backend.db.session import SessionLocal
from backend.services.kis_data_service import save_product_info, save_financial_ratios
import os


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=true to enable"
)
@pytest.mark.asyncio
async def test_real_kis_financial_ratios():
    """
    실전 KIS API 재무비율 조회 테스트

    삼성전자(005930)의 재무비율 데이터를 실제 API로 조회합니다.
    """
    client = await get_kis_client()

    # 삼성전자로 테스트
    result = await client.get_financial_ratios("005930")

    assert result["rt_cd"] == "0", f"API 호출 실패: {result.get('msg1')}"
    assert "output" in result, "output 키가 없습니다"
    assert len(result["output"]) > 0, "output이 비어있습니다"

    # 첫 번째 재무비율 데이터 검증
    first_ratio = result["output"][0]
    assert "stac_yymm" in first_ratio, "stac_yymm 필드가 없습니다"
    assert len(first_ratio["stac_yymm"]) == 6, "stac_yymm은 YYYYMM 형식이어야 합니다"

    print(f"✅ 재무비율 조회 성공: {len(result['output'])}건")
    print(f"   최신 데이터: {first_ratio['stac_yymm']}")


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled"
)
@pytest.mark.asyncio
async def test_real_kis_financial_ratios_with_db_save():
    """
    실전 KIS API 재무비율 조회 및 DB 저장 테스트
    """
    client = await get_kis_client()

    # API 조회
    result = await client.get_financial_ratios("005930")

    assert result["rt_cd"] == "0"
    assert len(result["output"]) > 0

    # DB 저장 테스트
    db = SessionLocal()
    try:
        ratios = save_financial_ratios(db, "005930", result)
        print(f"✅ DB 저장 성공: {len(ratios)}건 신규 삽입")

        # 저장된 데이터 검증
        if len(ratios) > 0:
            assert ratios[0].stock_code == "005930"
            assert ratios[0].stac_yymm is not None
            print(f"   첫 번째 레코드: {ratios[0].stac_yymm}, ROE: {ratios[0].roe_val}")
        else:
            print("   ℹ️  중복 데이터로 신규 삽입 없음")

    finally:
        db.close()


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled"
)
@pytest.mark.asyncio
async def test_real_kis_product_info():
    """
    실전 KIS API 상품정보 조회 테스트

    삼성전자(005930)의 상품정보를 실제 API로 조회합니다.
    """
    client = await get_kis_client()

    result = await client.get_product_info("005930")

    assert result["rt_cd"] == "0", f"API 호출 실패: {result.get('msg1')}"
    assert "output" in result, "output 키가 없습니다"

    output = result["output"]
    assert output.get("prdt_name"), "상품명이 없습니다"
    assert output.get("prdt_clsf_name"), "상품분류명이 없습니다"

    print(f"✅ 상품정보 조회 성공")
    print(f"   상품명: {output.get('prdt_name')}")
    print(f"   분류: {output.get('prdt_clsf_name')}")
    print(f"   위험등급: {output.get('prdt_risk_grad_cd')}")


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled"
)
@pytest.mark.asyncio
async def test_real_kis_product_info_with_db_save():
    """
    실전 KIS API 상품정보 조회 및 DB 저장 테스트 (UPSERT)
    """
    client = await get_kis_client()

    result = await client.get_product_info("005930")

    assert result["rt_cd"] == "0"
    assert result["output"]["prdt_name"]

    # DB 저장 테스트 (UPSERT)
    db = SessionLocal()
    try:
        product_info = save_product_info(db, "005930", result)

        assert product_info is not None
        assert product_info.stock_code == "005930"
        assert product_info.prdt_name == result["output"]["prdt_name"]

        print(f"✅ DB UPSERT 성공")
        print(f"   ID: {product_info.id}")
        print(f"   상품명: {product_info.prdt_name}")
        print(f"   최초등록일: {product_info.frst_erlm_dt}")

    finally:
        db.close()


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled"
)
@pytest.mark.asyncio
async def test_real_kis_financial_ratios_quarterly():
    """
    실전 KIS API 재무비율 조회 - 분기별 데이터
    """
    client = await get_kis_client()

    # 분기별 데이터 조회 (div_cls_code="1")
    result = await client.get_financial_ratios("005930", div_cls_code="1")

    assert result["rt_cd"] == "0"
    assert "output" in result

    if len(result["output"]) > 0:
        first_ratio = result["output"][0]
        print(f"✅ 분기별 재무비율 조회 성공: {len(result['output'])}건")
        print(f"   최신 분기: {first_ratio['stac_yymm']}")
    else:
        print("⚠️  분기별 데이터가 없습니다")


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled"
)
@pytest.mark.asyncio
async def test_real_kis_multiple_stocks():
    """
    실전 KIS API 여러 종목 테스트

    여러 대표 종목의 데이터를 조회하여 API 안정성을 확인합니다.
    """
    client = await get_kis_client()

    test_stocks = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035420", "NAVER")
    ]

    for stock_code, stock_name in test_stocks:
        # 상품정보 조회
        product_result = await client.get_product_info(stock_code)
        assert product_result["rt_cd"] == "0", f"{stock_name} 상품정보 조회 실패"

        # 재무비율 조회
        ratio_result = await client.get_financial_ratios(stock_code)
        assert ratio_result["rt_cd"] == "0", f"{stock_name} 재무비율 조회 실패"

        print(f"✅ {stock_name}({stock_code}) 조회 성공")

    print(f"\n✅ 총 {len(test_stocks)}개 종목 조회 완료")

"""
Unit tests for KIS API Client - get_financial_ratios() and get_product_info()
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.crawlers.kis_client import KISClient


@pytest.fixture
def kis_client():
    """KIS Client fixture for testing"""
    with patch('backend.crawlers.kis_client.settings') as mock_settings:
        mock_settings.KIS_APP_KEY = "test_app_key"
        mock_settings.KIS_APP_SECRET = "test_app_secret"
        mock_settings.KIS_BASE_URL = "https://test.api.com"
        mock_settings.KIS_MOCK_MODE = False
        mock_settings.REDIS_HOST = "localhost"
        mock_settings.REDIS_PORT = 6379
        mock_settings.REDIS_DB = 0

        with patch('backend.crawlers.kis_client.redis.Redis'):
            client = KISClient()
            return client


@pytest.mark.asyncio
async def test_get_financial_ratios_success(kis_client):
    """재무비율 조회 성공 케이스"""
    mock_response = {
        "rt_cd": "0",
        "msg1": "정상처리",
        "output": [
            {
                "stac_yymm": "202312",
                "grs": "12.5",
                "bsop_prfi_inrt": "15.3",
                "ntin_inrt": "18.7",
                "roe_val": "22.3",
                "eps": "5500",
                "bps": "45000",
                "lblt_rate": "35.2",
                "rsrv_rate": "1200.5"
            }
        ]
    }

    # Mock the request method
    kis_client.request = AsyncMock(return_value=mock_response)

    result = await kis_client.get_financial_ratios("005930")

    assert result["rt_cd"] == "0"
    assert len(result["output"]) == 1
    assert result["output"][0]["stac_yymm"] == "202312"
    assert result["output"][0]["grs"] == "12.5"
    assert result["output"][0]["roe_val"] == "22.3"
    assert result["output"][0]["eps"] == "5500"

    # Verify request was called with correct parameters
    kis_client.request.assert_called_once()
    call_args = kis_client.request.call_args
    assert call_args[1]["method"] == "GET"
    assert call_args[1]["tr_id"] == "FHKST66430300"
    assert call_args[1]["params"]["fid_input_iscd"] == "005930"
    assert call_args[1]["params"]["FID_DIV_CLS_CODE"] == "0"


@pytest.mark.asyncio
async def test_get_financial_ratios_with_div_cls_code(kis_client):
    """재무비율 조회 - 분기별 데이터"""
    mock_response = {
        "rt_cd": "0",
        "msg1": "정상처리",
        "output": [{"stac_yymm": "202309", "grs": "10.0"}]
    }

    kis_client.request = AsyncMock(return_value=mock_response)

    result = await kis_client.get_financial_ratios("005930", div_cls_code="1")

    assert result["rt_cd"] == "0"

    # Verify div_cls_code parameter
    call_args = kis_client.request.call_args
    assert call_args[1]["params"]["FID_DIV_CLS_CODE"] == "1"


@pytest.mark.asyncio
async def test_get_financial_ratios_invalid_stock_code(kis_client):
    """재무비율 조회 - 잘못된 종목코드"""
    with pytest.raises(ValueError, match="Invalid stock_code"):
        await kis_client.get_financial_ratios("invalid")

    with pytest.raises(ValueError, match="Invalid stock_code"):
        await kis_client.get_financial_ratios("")

    with pytest.raises(ValueError, match="Invalid stock_code"):
        await kis_client.get_financial_ratios("12345")  # 5자리


@pytest.mark.asyncio
async def test_get_financial_ratios_invalid_div_cls_code(kis_client):
    """재무비율 조회 - 잘못된 분류코드"""
    with pytest.raises(ValueError, match="Invalid div_cls_code"):
        await kis_client.get_financial_ratios("005930", div_cls_code="2")

    with pytest.raises(ValueError, match="Invalid div_cls_code"):
        await kis_client.get_financial_ratios("005930", div_cls_code="invalid")


@pytest.mark.asyncio
async def test_get_financial_ratios_api_error(kis_client):
    """재무비율 조회 - API 에러"""
    # Mock request to raise exception
    kis_client.request = AsyncMock(side_effect=Exception("API Error"))

    with pytest.raises(Exception, match="API Error"):
        await kis_client.get_financial_ratios("005930")


@pytest.mark.asyncio
async def test_get_product_info_success(kis_client):
    """상품정보 조회 성공 케이스"""
    mock_response = {
        "rt_cd": "0",
        "msg1": "정상처리",
        "output": {
            "prdt_name": "삼성전자",
            "prdt_clsf_name": "전기전자",
            "ivst_prdt_type_cd_name": "주권",
            "prdt_risk_grad_cd": "3",
            "frst_erlm_dt": "19750611"
        }
    }

    kis_client.request = AsyncMock(return_value=mock_response)

    result = await kis_client.get_product_info("005930")

    assert result["rt_cd"] == "0"
    assert result["output"]["prdt_name"] == "삼성전자"
    assert result["output"]["prdt_clsf_name"] == "전기전자"
    assert result["output"]["prdt_risk_grad_cd"] == "3"

    # Verify request was called with correct parameters
    kis_client.request.assert_called_once()
    call_args = kis_client.request.call_args
    assert call_args[1]["method"] == "GET"
    assert call_args[1]["tr_id"] == "CTPF1604R"
    assert call_args[1]["params"]["PDNO"] == "005930"
    assert call_args[1]["params"]["PRDT_TYPE_CD"] == "300"


@pytest.mark.asyncio
async def test_get_product_info_invalid_stock_code(kis_client):
    """상품정보 조회 - 잘못된 종목코드"""
    with pytest.raises(ValueError, match="Invalid stock_code"):
        await kis_client.get_product_info("invalid")

    with pytest.raises(ValueError, match="Invalid stock_code"):
        await kis_client.get_product_info("")

    with pytest.raises(ValueError, match="Invalid stock_code"):
        await kis_client.get_product_info("12345")  # 5자리


@pytest.mark.asyncio
async def test_get_product_info_api_error(kis_client):
    """상품정보 조회 - API 에러"""
    kis_client.request = AsyncMock(side_effect=Exception("API Error"))

    with pytest.raises(Exception, match="API Error"):
        await kis_client.get_product_info("005930")


@pytest.mark.asyncio
async def test_get_financial_ratios_empty_output(kis_client):
    """재무비율 조회 - 빈 output"""
    mock_response = {
        "rt_cd": "0",
        "msg1": "정상처리",
        "output": []
    }

    kis_client.request = AsyncMock(return_value=mock_response)

    result = await kis_client.get_financial_ratios("005930")

    assert result["rt_cd"] == "0"
    assert len(result["output"]) == 0

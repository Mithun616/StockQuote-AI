import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import httpx

from main import app
from models import StockRequest
from logic_app_client import send_to_logic_app

client = TestClient(app)

def test_health_endpoint():
    """Verify health endpoint reports correct Azure service configurations."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "StockQuotesAgentUS" in data["foundry_endpoint"]
    assert data["foundry_agent"] == "StockQuoteAgent"
    assert data["azure_table_name"] == "StockQuotes"
    assert data["logic_app_name"] == "stockworkflow616"

def test_symbol_validation_valid():
    """Verify valid ticker symbols are normalized to uppercase."""
    req1 = StockRequest(symbol="msft")
    assert req1.symbol == "MSFT"

    req2 = StockRequest(symbol="aapl")
    assert req2.symbol == "AAPL"

    req3 = StockRequest(symbol="BRK.B")
    assert req3.symbol == "BRK.B"

def test_symbol_validation_invalid():
    """Verify invalid symbols raise validation errors."""
    with pytest.raises(ValueError):
        StockRequest(symbol="")

    with pytest.raises(ValueError):
        StockRequest(symbol="TOOLONGTICKERNAME")

    with pytest.raises(ValueError):
        StockRequest(symbol="MS FT")  # spaces invalid

    with pytest.raises(ValueError):
        StockRequest(symbol="AAPL$$")  # special symbols invalid

def test_post_stock_valid_symbol():
    """Test full /api/stock flow with valid symbol MSFT."""
    with patch("main.settings.ALLOW_MOCK_FALLBACK", True):
        response = client.post("/api/stock", json={"symbol": "MSFT"})
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "MSFT"
        assert data["price"] > 0
        assert data["currency"] == "USD"
        assert "trading_date" in data
        assert data["azure_table_name"] == "StockQuotes"
        assert data["azure_logic_app"] == "stockworkflow616"

def test_post_stock_invalid_symbol_rejected():
    """Test /api/stock rejects invalid input with 422 Unprocessable Entity."""
    response = client.post("/api/stock", json={"symbol": "INVALID$$$"})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_logic_app_missing_url():
    """When LOGIC_APP_URL is empty, return NOT_CONFIGURED and saved_to_azure=False."""
    with patch("logic_app_client.settings.LOGIC_APP_URL", ""):
        saved, status_str, msg = await send_to_logic_app("MSFT", 524.51)
        assert saved is False
        assert status_str == "NOT_CONFIGURED"
        assert "not configured" in msg.lower()

@pytest.mark.asyncio
async def test_logic_app_success_mock():
    """When Logic App returns 200 OK, saved_to_azure must be True."""
    mock_response = httpx.Response(status_code=200, text="OK")
    with patch("logic_app_client.settings.LOGIC_APP_URL", "https://mock-logic-app.azure.com/invoke"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            saved, status_str, msg = await send_to_logic_app("MSFT", 524.51)
            assert saved is True
            assert status_str == "SUCCESS"
            assert "Successfully saved MSFT ($524.51)" in msg

@pytest.mark.asyncio
async def test_logic_app_failure_mock():
    """When Logic App returns 500 error, saved_to_azure must be False."""
    mock_response = httpx.Response(status_code=500, text="Internal Logic App Server Error")
    with patch("logic_app_client.settings.LOGIC_APP_URL", "https://mock-logic-app.azure.com/invoke"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            saved, status_str, msg = await send_to_logic_app("MSFT", 524.51)
            assert saved is False
            assert status_str == "FAILED"
            assert "rejected request with HTTP 500" in msg

def test_popular_stocks_endpoint():
    """Verify /api/stocks/popular returns key tickers."""
    response = client.get("/api/stocks/popular")
    assert response.status_code == 200
    stocks = response.json()
    symbols = [s["symbol"] for s in stocks]
    assert "MSFT" in symbols
    assert "AAPL" in symbols
    assert "NVDA" in symbols

def test_rate_limiting_trigger():
    """Verify rate limiting rejects excess requests beyond threshold."""
    with patch("main.settings.RATE_LIMIT_PER_MINUTE", 3), patch("main.settings.ALLOW_MOCK_FALLBACK", True):
        # Clear existing timestamps for test client
        from main import _rate_limits
        _rate_limits.clear()
        
        # 3 calls should pass
        for _ in range(3):
            r = client.post("/api/stock", json={"symbol": "MSFT"})
            assert r.status_code == 200
            
        # 4th call should hit rate limit (HTTP 429)
        r = client.post("/api/stock", json={"symbol": "MSFT"})
        assert r.status_code == 429
        assert "Rate limit exceeded" in r.json()["detail"]
        _rate_limits.clear()


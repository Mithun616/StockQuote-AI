"""
Comprehensive Local Test Suite for Alpha Vantage Quota Optimization & Security
Tests:
1. Pre-Foundry Cache Check (Cache Hit skips Foundry & Alpha Vantage)
2. Rejection of unverified / legacy records (provenance_verified=False)
3. Rejection of tampered / forged signatures
4. Concurrent request deduplication / Stampede protection (Double-Checked Lock)
5. Provider Rate Limit (HTTP 429) handling: no automatic retries, clear error message, no fake prices
6. Provider Rate Limit cooldown (prevents pounding exhausted provider)
7. Preservation of distinct trading_date vs. cache timestamp
"""

import asyncio
import hmac
import hashlib
import time
import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from main import app
from models import StockResponse
from table_storage_service import (
    compute_canonical_signature,
    CachedQuoteResult,
    table_cache_service,
)
from config import settings

TEST_SIGNING_KEY = "test-secret-key-32-bytes-long-12345"

@pytest.fixture(autouse=True)
def setup_test_env():
    import main
    main._provider_rate_limited_until = 0.0
    main._provider_rate_limit_msg = ""
    with patch("config.settings.PROVENANCE_SIGNING_KEY", TEST_SIGNING_KEY), \
         patch("main.settings.PROVENANCE_SIGNING_KEY", TEST_SIGNING_KEY), \
         patch("main.settings.ALLOW_MOCK_FALLBACK", False):
        yield

def test_cache_hit_skips_foundry_and_av():
    """Verify that a valid HMAC-verified cached record serves the quote with ZERO Foundry/AV calls."""
    client = TestClient(app)
    symbol = "MSFT"
    price = 524.51
    trading_date = "2026-10-26"
    data_source = "Alpha Vantage TIME_SERIES_DAILY"
    stored_at = "2026-10-27T10:00:00+00:00"

    valid_sig = compute_canonical_signature(
        symbol=symbol,
        price=price,
        trading_date=trading_date,
        data_source=data_source,
        retrieved_at=stored_at,
        signing_key=TEST_SIGNING_KEY,
    )

    cached_result = CachedQuoteResult(
        symbol=symbol,
        price=price,
        trading_date=trading_date,
        stored_at=stored_at,
        cached_at="2026-10-27T12:00:00+00:00",
        age_seconds=7200.0,
        is_fresh=True,
        provenance_verified=True,
        data_source=data_source,
        provenance_signature=valid_sig,
        provenance_note="Cryptographically verified market quote (HMAC-SHA256 verified).",
    )

    with patch.object(table_cache_service, "get_cached_quote", new_callable=AsyncMock) as mock_get_cache, \
         patch("main.agent_service.fetch_stock_quote", new_callable=AsyncMock) as mock_fetch:
        
        mock_get_cache.return_value = cached_result

        response = client.post("/api/stock", json={"symbol": symbol})

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "MSFT"
        assert data["price"] == 524.51
        assert data["trading_date"] == "2026-10-26"
        assert data["is_cached"] is True
        assert data["azure_save_status"] == "CACHED"
        assert data["provenance_verified"] is True
        assert data["provenance_signature"] == valid_sig

        # CRITICAL: Confirm Foundry was NEVER invoked
        mock_fetch.assert_not_called()
        print("\n[PASS] Verified cache hit served in zero Foundry / AV calls.")

def test_legacy_unverified_record_rejected():
    """Verify legacy records lacking provenance/trading_date are rejected from cache."""
    symbol = "MSFT"
    raw_entity = {
        "PartitionKey": "MSFT",
        "RowKey": "old-guid",
        "price": 524.51,
        "Timestamp": "2026-10-25T12:00:00Z",
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"value": [raw_entity]}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = asyncio.run(table_cache_service.get_cached_quote(symbol))

        assert result is not None
        assert result.provenance_verified is False
        assert result.trading_date is None
        assert result.is_fresh is False
        assert "Unverified record" in result.provenance_note
        print("\n[PASS] Legacy unverified record rejected as fresh cache.")

def test_tampered_signature_rejected():
    """Verify an entity with altered price or forged signature is rejected as unverified."""
    symbol = "MSFT"
    raw_entity = {
        "PartitionKey": "MSFT",
        "RowKey": "tampered-guid",
        "price": 999.99,
        "trading_date": "2026-10-26",
        "provenance_verified": True,
        "provenance_signature": "badc0de000000000000000000000000000000000000000000000000000000000",
        "data_source": "Alpha Vantage TIME_SERIES_DAILY",
        "retrieved_at": "2026-10-27T10:00:00Z",
        "Timestamp": "2026-10-27T10:00:00Z",
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"value": [raw_entity]}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = asyncio.run(table_cache_service.get_cached_quote(symbol))

        assert result is not None
        assert result.provenance_verified is False
        assert result.trading_date is None
        assert result.is_fresh is False
        assert "Cryptographic signature mismatch" in result.provenance_note
        print("\n[PASS] Tampered record signature detected and rejected.")

@pytest.mark.asyncio
async def test_concurrent_requests_stampede_protection():
    """Verify simultaneous requests for the same symbol trigger EXACTLY ONE live provider call."""
    symbol = "MSFT"
    live_call_count = 0
    saved_cache = None

    async def mock_fetch(sym):
        nonlocal live_call_count
        live_call_count += 1
        await asyncio.sleep(0.05)  # simulate async network latency
        return StockResponse(
            symbol=sym,
            price=524.51,
            currency="USD",
            trading_date="2026-10-26",
            data_source="Alpha Vantage TIME_SERIES_DAILY",
            retrieved_at="2026-10-27T10:00:00Z",
            is_mock=False,
            saved_to_azure=True,
        )

    async def mock_get_cache(sym):
        return saved_cache

    async def mock_logic_app(**kwargs):
        nonlocal saved_cache
        saved_cache = CachedQuoteResult(
            symbol=kwargs["symbol"],
            price=kwargs["price"],
            trading_date=kwargs["trading_date"],
            stored_at=kwargs["retrieved_at"],
            cached_at="2026-10-27T10:00:05Z",
            age_seconds=1.0,
            is_fresh=True,
            provenance_verified=True,
            data_source=kwargs["data_source"],
            provenance_signature="sig-123",
            provenance_note="Verified",
        )
        return (True, "SUCCESS", "Saved")

    with patch("main.table_cache_service.get_cached_quote", side_effect=mock_get_cache), \
         patch("main.agent_service.fetch_stock_quote", side_effect=mock_fetch), \
         patch("main.send_to_logic_app", side_effect=mock_logic_app):

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # Fire 5 simultaneous requests for MSFT
            tasks = [client.post("/api/stock", json={"symbol": symbol}) for _ in range(5)]
            responses = await asyncio.gather(*tasks)

        assert all(r.status_code == 200 for r in responses)
        # CRITICAL: Verify only 1 live provider call was made
        assert live_call_count == 1
        
        # Verify all 5 received consistent data
        for r in responses:
            body = r.json()
            assert body["symbol"] == "MSFT"
            assert body["price"] == 524.51
            assert body["trading_date"] == "2026-10-26"

        print(f"\n[PASS] Stampede protection verified: 5 concurrent requests -> {live_call_count} live provider call.")

def test_provider_http_429_handling():
    """Verify provider rate limit returns HTTP 429 without retry, fake prices, or unverified bypass."""
    client = TestClient(app)
    symbol = "MSFT"

    with patch.object(table_cache_service, "get_cached_quote", new_callable=AsyncMock) as mock_get_cache, \
         patch("main.agent_service.fetch_stock_quote", new_callable=AsyncMock) as mock_fetch:
        
        # Cache miss
        mock_get_cache.return_value = None

        # Foundry returns rate limit error
        mock_fetch.side_effect = RuntimeError(
            "Alpha Vantage API rate limit reached (standard tier limit is 25 requests per day). Live price is temporarily unavailable."
        )

        response = client.post("/api/stock", json={"symbol": symbol})

        assert response.status_code == 429
        data = response.json()
        assert "25 requests" in data["detail"] or "daily API quota" in data["detail"]
        # Confirm no retries were made
        assert mock_fetch.call_count == 1
        print("\n[PASS] Provider HTTP 429 cleanly handled without retries or fake data.")

def test_provider_rate_limit_cooldown():
    """Verify subsequent requests within cooldown are blocked from pounding the exhausted provider."""
    client = TestClient(app)
    symbol = "MSFT"

    with patch.object(table_cache_service, "get_cached_quote", new_callable=AsyncMock) as mock_get_cache, \
         patch("main.agent_service.fetch_stock_quote", new_callable=AsyncMock) as mock_fetch:
        
        mock_get_cache.return_value = None
        mock_fetch.side_effect = RuntimeError("Alpha Vantage rate limit reached")

        # First request hits rate limit
        r1 = client.post("/api/stock", json={"symbol": symbol})
        assert r1.status_code == 429
        assert mock_fetch.call_count == 1

        # Second request immediately after (within 60s cooldown) should NOT invoke fetch_stock_quote
        r2 = client.post("/api/stock", json={"symbol": symbol})
        assert r2.status_code == 429
        assert mock_fetch.call_count == 1  # Still 1! Provider was not pounded!
        print("\n[PASS] Provider cooldown active: blocked redundant live call while rate-limited.")

def test_trading_date_vs_cache_timestamp_distinction():
    """Verify original trading date is strictly preserved and distinct from cache timestamp."""
    client = TestClient(app)
    symbol = "MSFT"
    original_trading_date = "2026-10-24"
    cache_insertion_time = "2026-10-27T15:30:00+00:00"

    valid_sig = compute_canonical_signature(
        symbol=symbol,
        price=524.51,
        trading_date=original_trading_date,
        data_source="Alpha Vantage TIME_SERIES_DAILY",
        retrieved_at=cache_insertion_time,
        signing_key=TEST_SIGNING_KEY,
    )

    cached_result = CachedQuoteResult(
        symbol=symbol,
        price=524.51,
        trading_date=original_trading_date,
        stored_at=cache_insertion_time,
        cached_at=cache_insertion_time,
        age_seconds=100.0,
        is_fresh=True,
        provenance_verified=True,
        data_source="Alpha Vantage TIME_SERIES_DAILY",
        provenance_signature=valid_sig,
        provenance_note="Verified",
    )

    with patch.object(table_cache_service, "get_cached_quote", new_callable=AsyncMock) as mock_get_cache:
        mock_get_cache.return_value = cached_result

        resp = client.post("/api/stock", json={"symbol": symbol})
        assert resp.status_code == 200
        data = resp.json()
        assert data["trading_date"] == original_trading_date
        assert data["cached_at"] == cache_insertion_time
        assert data["trading_date"] != data["cached_at"]
        print("\n[PASS] trading_date (market session) strictly distinguished from cached_at (storage time).")

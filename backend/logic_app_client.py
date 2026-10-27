import httpx
import logging
from typing import Tuple, Optional
from config import settings

logger = logging.getLogger("stockquote.logic_app")

async def send_to_logic_app(
    symbol: str,
    price: float,
    trading_date: Optional[str] = None,
    data_source: Optional[str] = None,
    retrieved_at: Optional[str] = None,
    provenance_verified: bool = True,
) -> Tuple[bool, str, str]:
    """
    Sends the retrieved stock quote and verified provenance to Azure Logic App `stockworkflow616`.
    Payload format includes symbol, price, and provenance fields:
    {"symbol": "MSFT", "price": 524.51, "trading_date": "2026-10-23", ...}
    
    Returns:
        (saved_to_azure: bool, azure_save_status: str, message: str)
    """
    logic_app_url = settings.LOGIC_APP_URL.strip()
    
    if not logic_app_url:
        logger.warning("LOGIC_APP_URL is not configured. Skipping save to Azure.")
        return (
            False,
            "NOT_CONFIGURED",
            "Logic App URL is not configured in backend environment (.env). Quote was retrieved but not saved to Azure Table Storage."
        )

    # Strictly format payload expected by stockworkflow616
    payload: dict = {
        "symbol": symbol.upper(),
        "price": round(float(price), 2),
    }
    if trading_date:
        payload["trading_date"] = trading_date
    if data_source:
        payload["data_source"] = data_source
    if retrieved_at:
        payload["retrieved_at"] = retrieved_at
    payload["provenance_verified"] = provenance_verified

    # Compute deterministic canonical HMAC signature if signing key is configured
    signing_key = settings.PROVENANCE_SIGNING_KEY.strip()
    if signing_key and trading_date:
        from table_storage_service import compute_canonical_signature
        sig = compute_canonical_signature(
            symbol=symbol,
            price=payload["price"],
            trading_date=trading_date,
            data_source=data_source or "Alpha Vantage TIME_SERIES_DAILY",
            retrieved_at=retrieved_at or "",
            signing_key=signing_key,
        )
        payload["provenance_signature"] = sig

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "StockQuoteAI-Backend/1.0",
    }
    # Attach backend-to-Logic-App authentication token header
    auth_token = settings.BACKEND_LOGIC_APP_AUTH_TOKEN.strip()
    if auth_token:
        headers["x-backend-auth-token"] = auth_token

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(logic_app_url, json=payload, headers=headers)
            
            # Logic Apps typically return HTTP 200 (OK) or HTTP 202 (Accepted)
            if response.status_code in (200, 202):
                logger.info(
                    f"Successfully sent quote for {symbol} (${payload['price']}) to Logic App stockworkflow616. "
                    f"HTTP {response.status_code}"
                )
                return (
                    True,
                    "SUCCESS",
                    f"Successfully saved {symbol} (${payload['price']:.2f}) to Azure Table Storage 'StockQuotes' via Logic App 'stockworkflow616'."
                )
            else:
                error_body = response.text[:200]
                logger.error(
                    f"Logic App returned error {response.status_code}: {error_body}"
                )
                return (
                    False,
                    "FAILED",
                    f"Logic App rejected request with HTTP {response.status_code}: {error_body}"
                )

    except httpx.TimeoutException:
        logger.error("Timeout connecting to Azure Logic App")
        return (
            False,
            "FAILED",
            "Azure Logic App request timed out after 15 seconds."
        )
    except Exception as e:
        logger.error(f"Error calling Azure Logic App: {str(e)}")
        return (
            False,
            "FAILED",
            f"Failed to communicate with Azure Logic App: {str(e)}"
        )

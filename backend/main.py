import time
import asyncio
import logging
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from models import StockRequest, StockResponse, HealthResponse
from agent_service import agent_service
from logic_app_client import send_to_logic_app
from table_storage_service import table_cache_service

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("stockquote.main")

app = FastAPI(
    title="StockQuote AI Backend",
    description="Full-stack Azure AI Foundry + Alpha Vantage MCP + Azure Logic App integration service.",
    version="1.1.0-quota-optimized",
)

# Allowed explicit CORS origins (no wildcards)
allowed_origins = [o.rstrip("/") for o in settings.CORS_ORIGINS if o.strip() and o.strip() != "*"]

# CORS Middleware supporting explicit origins and Azure Static Web Apps regex
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https://[a-zA-Z0-9-]+\.azurestaticapps\.net$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# In-memory sliding window rate limiter
_rate_limits = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Only rate limit /api/stock requests
    if request.url.path.startswith("/api/stock") and request.method == "POST":
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window_seconds = 60.0
        max_requests = settings.RATE_LIMIT_PER_MINUTE

        # Clean old timestamps
        timestamps = [t for t in _rate_limits[client_ip] if now - t < window_seconds]
        if len(timestamps) >= max_requests:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum {max_requests} requests per minute allowed to protect Alpha Vantage and Azure quotas."
                },
            )
        timestamps.append(now)
        _rate_limits[client_ip] = timestamps

    return await call_next(request)

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Checks backend service status, Microsoft Foundry configuration,
    and Azure Logic App readiness.
    """
    return HealthResponse(
        status="HEALTHY",
        version="1.1.0-quota-optimized",
        azure_foundry_configured=bool(settings.AZURE_AI_PROJECT_ENDPOINT and settings.AZURE_AGENT_NAME),
        foundry_endpoint=settings.AZURE_AI_PROJECT_ENDPOINT,
        foundry_agent=settings.AZURE_AGENT_NAME,
        foundry_model=settings.AZURE_MODEL_DEPLOYMENT,
        logic_app_configured=bool(settings.LOGIC_APP_URL.strip()),
        logic_app_name="stockworkflow616",
        azure_table_name="StockQuotes",
        mock_mode_allowed=settings.ALLOW_MOCK_FALLBACK,
    )

# In-memory per-symbol mutex to prevent Cache Stampede / duplicate provider calls
_symbol_locks = defaultdict(asyncio.Lock)
_provider_rate_limited_until: float = 0.0
_provider_rate_limit_msg: str = ""

def _format_cached_response(cached) -> StockResponse:
    return StockResponse(
        symbol=cached.symbol,
        price=cached.price,
        currency="USD",
        trading_date=cached.trading_date,
        saved_to_azure=True,
        azure_save_status="CACHED",
        azure_save_message=f"Verified daily close for trading session {cached.trading_date} served from Azure Table Storage cache.",
        azure_table_name="StockQuotes",
        azure_logic_app="stockworkflow616",
        is_mock=False,
        is_cached=True,
        cached_at=cached.cached_at,
        provenance_verified=True,
        provenance_signature=cached.provenance_signature,
        provenance_note=cached.provenance_note,
        data_source=cached.data_source,
        retrieved_at=cached.stored_at,
        history=[],
        raw_agent_message=f"Served from Azure Table Storage cache. Market trading session: {cached.trading_date}.",
    )

@app.post("/api/stock", response_model=StockResponse)
async def get_and_save_stock_quote(payload: StockRequest):
    """
    Retrieves the latest daily closing stock quote for the requested symbol
    via Microsoft Foundry AI Agent (Alpha Vantage MCP TIME_SERIES_DAILY),
    with an intelligent read-through cache on Azure Table Storage 'StockQuotes'
    and single-flight concurrency lock to prevent duplicate provider queries.
    """
    symbol = payload.symbol.strip().upper()
    logger.info(f"Received request for stock symbol: {symbol}")

    # 1. Fast-Path Read-Through Cache Check: Check Azure Table Storage 'StockQuotes'
    cached = await table_cache_service.get_cached_quote(symbol)
    if cached and cached.is_fresh and cached.provenance_verified:
        logger.info(
            f"Table Storage Cache HIT for {symbol}: Price=${cached.price}, TradingDate={cached.trading_date}, Age={cached.age_seconds:.0f}s. "
            f"Serving verified daily close without consuming Alpha Vantage quota."
        )
        return _format_cached_response(cached)

    # 2. Acquire per-symbol lock to coalesce concurrent requests (prevent stampede)
    async with _symbol_locks[symbol]:
        # Double-check cache inside lock (in case another in-flight request just populated it)
        cached = await table_cache_service.get_cached_quote(symbol)
        if cached and cached.is_fresh and cached.provenance_verified:
            logger.info(
                f"Table Storage Cache HIT (coalesced) for {symbol}: Price=${cached.price}, TradingDate={cached.trading_date}. "
                f"Serving verified daily close without duplicate provider invocation."
            )
            return _format_cached_response(cached)

        # Provider cooldown check: if Alpha Vantage is currently rate-limited, avoid redundant live queries
        global _provider_rate_limited_until, _provider_rate_limit_msg
        if time.time() < _provider_rate_limited_until:
            if cached and cached.provenance_verified and cached.trading_date:
                logger.info(f"Provider cooldown active. Serving verified historical record for {symbol}.")
                return StockResponse(
                    symbol=cached.symbol,
                    price=cached.price,
                    currency="USD",
                    trading_date=cached.trading_date,
                    saved_to_azure=True,
                    azure_save_status="HISTORICAL_FALLBACK",
                    azure_save_message=f"Live Alpha Vantage quota reached. Displaying verified historical close for session {cached.trading_date}.",
                    azure_table_name="StockQuotes",
                    azure_logic_app="stockworkflow616",
                    is_mock=False,
                    is_cached=True,
                    is_historical_fallback=True,
                    cached_at=cached.cached_at,
                    provenance_verified=True,
                    provenance_signature=cached.provenance_signature,
                    provenance_note=cached.provenance_note,
                    data_source=f"Azure Table Storage (Verified Close from Session {cached.trading_date})",
                    retrieved_at=cached.stored_at,
                    history=[],
                    raw_agent_message="Live Alpha Vantage quota reached. Showing verified historical close from Azure Table Storage.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=_provider_rate_limit_msg or f"Alpha Vantage daily API quota exhausted (25 requests/day limit). Live market data is temporarily unavailable for '{symbol}'.",
                )

        # 3. Live Foundry Agent query (Cache Miss or Expired)
        try:
            quote = await agent_service.fetch_stock_quote(symbol)
            quote.provenance_verified = True
        except Exception as e:
            err_str = str(e)
            logger.error(f"Live Foundry Agent execution failed for {symbol}: {err_str}")

            # If live provider hits quota limit but we have a verified record in Table Storage:
            if any(term in err_str.lower() for term in ["rate limit", "rate-limit", "daily request limit", "standard tier limit"]):
                # Set 60-second cooldown so subsequent requests don't waste time or quota
                _provider_rate_limited_until = time.time() + 60.0
                _provider_rate_limit_msg = err_str

                if cached and cached.provenance_verified and cached.trading_date:
                    logger.info(
                        f"Alpha Vantage quota reached. Falling back to verified historical record in Table Storage for {symbol}."
                    )
                    return StockResponse(
                        symbol=cached.symbol,
                        price=cached.price,
                        currency="USD",
                        trading_date=cached.trading_date,
                        saved_to_azure=True,
                        azure_save_status="HISTORICAL_FALLBACK",
                        azure_save_message=f"Live Alpha Vantage quota reached. Displaying verified historical close for session {cached.trading_date}.",
                        azure_table_name="StockQuotes",
                        azure_logic_app="stockworkflow616",
                        is_mock=False,
                        is_cached=True,
                        is_historical_fallback=True,
                        cached_at=cached.cached_at,
                        provenance_verified=True,
                        provenance_signature=cached.provenance_signature,
                        provenance_note=cached.provenance_note,
                        data_source=f"Azure Table Storage (Verified Close from Session {cached.trading_date})",
                        retrieved_at=cached.stored_at,
                        history=[],
                        raw_agent_message="Live Alpha Vantage quota reached. Showing verified historical close from Azure Table Storage.",
                    )
                else:
                    # Rule 7: Do not return unverified legacy prices as successful stock quote responses.
                    logger.warning(
                        f"Table Storage entity found for {symbol} but provenance/trading_date is unverified. Refusing to return unverified quote."
                    )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=(
                            f"Alpha Vantage daily API quota exhausted (25 requests/day limit). Live market data is temporarily "
                            f"unavailable for '{symbol}'. Existing historical record in storage lacks verified market session provenance "
                            f"and cannot be served."
                        ),
                    )

            # No cache fallback available and not a rate limit error: raise clean 502
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Microsoft Foundry Agent error: {err_str}",
            )

        # 4. Live quote succeeded: Save verified quote with full provenance to Azure Table Storage via Logic App
        saved_to_azure, save_status, save_message = await send_to_logic_app(
            symbol=quote.symbol,
            price=quote.price,
            trading_date=quote.trading_date,
            data_source=quote.data_source,
            retrieved_at=quote.retrieved_at,
            provenance_verified=True,
        )

        quote.saved_to_azure = saved_to_azure
        quote.azure_save_status = save_status
        quote.azure_save_message = save_message

        logger.info(
            f"Processed {symbol}: Price=${quote.price}, SavedToAzure={saved_to_azure} ({save_status})"
        )

        return quote

@app.get("/api/stocks/popular")
async def get_popular_stocks():
    """Returns a list of popular symbols and their company names for quick selection."""
    return [
        {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
        {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Consumer Electronics"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Semiconductors"},
        {"symbol": "TSLA", "name": "Tesla, Inc.", "sector": "Automotive / Clean Energy"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
        {"symbol": "AMZN", "name": "Amazon.com, Inc.", "sector": "E-Commerce / Cloud"},
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)

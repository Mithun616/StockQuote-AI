import logging
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass
from zoneinfo import ZoneInfo
import httpx
from config import settings

logger = logging.getLogger("stockquote.table_cache")

def compute_canonical_signature(
    symbol: str,
    price: float,
    trading_date: str,
    data_source: str,
    retrieved_at: str,
    signing_key: str,
) -> str:
    """
    Computes a deterministic canonical HMAC-SHA256 signature for market-data provenance.
    Format: SYMBOL|PRICE_2DEC|TRADING_DATE|DATA_SOURCE|RETRIEVED_AT
    """
    clean_sym = symbol.strip().upper()
    price_str = f"{float(price):.2f}"
    clean_date = str(trading_date).strip()
    clean_source = str(data_source).strip()
    clean_retrieved = str(retrieved_at).strip()

    canonical = f"{clean_sym}|{price_str}|{clean_date}|{clean_source}|{clean_retrieved}"
    return hmac.new(
        signing_key.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

@dataclass
class CachedQuoteResult:
    symbol: str
    price: float
    trading_date: Optional[str]       # Genuine market trading date (YYYY-MM-DD), NEVER storedAt or entity Timestamp
    stored_at: str                    # Database insertion timestamp in Azure Table Storage
    cached_at: str                    # When retrieved or placed into cache
    age_seconds: float
    is_fresh: bool
    provenance_verified: bool         # Strictly True ONLY if explicitly verified in persistent storage entity
    data_source: str
    provenance_signature: Optional[str] = None
    provenance_note: Optional[str] = None

def get_ny_market_status(now_utc: Optional[datetime] = None) -> tuple[bool, str]:
    """
    Evaluates whether the US Stock Market (NYSE/NASDAQ) is currently in open trading session.
    Handles US Daylight Saving Time (EDT/EST) automatically via ZoneInfo('America/New_York').
    Returns:
        (is_market_open: bool, status_reason: str)
    """
    ny_tz = ZoneInfo("America/New_York")
    now_ny = datetime.now(timezone.utc).astimezone(ny_tz) if now_utc is None else now_utc.astimezone(ny_tz)
    
    # Weekends: Always closed
    if now_ny.weekday() == 5:
        return False, f"Market Closed (Saturday - {now_ny.strftime('%Y-%m-%d %H:%M %Z')})"
    if now_ny.weekday() == 6:
        return False, f"Market Closed (Sunday - {now_ny.strftime('%Y-%m-%d %H:%M %Z')})"

    # US Market regular trading hours: 9:30 AM to 4:00 PM Eastern Time
    time_minutes = now_ny.hour * 60 + now_ny.minute
    market_open_minutes = 9 * 60 + 30   # 09:30
    market_close_minutes = 16 * 60     # 16:00

    if time_minutes < market_open_minutes:
        return False, f"Pre-Market (Opens 09:30 AM ET - Current: {now_ny.strftime('%H:%M %Z')})"
    elif time_minutes >= market_close_minutes:
        return False, f"Post-Market (Closed 04:00 PM ET - Current: {now_ny.strftime('%H:%M %Z')})"
    else:
        return True, f"Regular Market Hours Open ({now_ny.strftime('%H:%M %Z')})"

class TableStorageCacheService:
    def __init__(self):
        self.account = settings.TABLE_STORAGE_ACCOUNT
        self.table_name = settings.TABLE_STORAGE_TABLE
        self.base_url = f"https://{self.account}.table.core.windows.net/{self.table_name}()"
        self._credential = None
        self._cached_token = None
        self._token_expires_at = 0

    def _get_bearer_token(self) -> Optional[str]:
        """Obtains AAD bearer token for Azure Storage data plane."""
        import time
        now = time.time()
        if self._cached_token and now < self._token_expires_at - 60:
            return self._cached_token

        try:
            if not self._credential:
                from azure.identity import DefaultAzureCredential
                self._credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
            token_obj = self._credential.get_token("https://storage.azure.com/.default")
            self._cached_token = token_obj.token
            self._token_expires_at = token_obj.expires_on
            return self._cached_token
        except Exception as e:
            logger.debug(f"Could not obtain Azure AD storage token: {e}")
            return None

    async def get_cached_quote(self, symbol: str) -> Optional[CachedQuoteResult]:
        """
        Retrieves the latest stock quote entity from Azure Table Storage 'StockQuotes'.
        Strict Data Integrity & Provenance Rules:
        1. NO reliance on hardcoded stock prices, dates, or in-memory registries.
        2. Set provenance_verified=False by default unless explicitly recorded in persistent storage.
        3. Never substitute storedAt, entity Timestamp, or current date for market trading_date.
        4. If provenance or trading_date is absent, provenance_verified is False.
        5. Isolates PartitionKey strictly by symbol.
        """
        clean_sym = symbol.strip().upper()
        token = self._get_bearer_token()
        sas = getattr(settings, "TABLE_STORAGE_READ_SAS", "").strip().lstrip("?")

        headers = {
            "Accept": "application/json;odata=nometadata",
            "x-ms-version": "2019-02-02",
        }

        # Determine URL and auth headers
        request_attempts = []
        if token:
            h = headers.copy()
            h["Authorization"] = f"Bearer {token}"
            request_attempts.append((f"{self.base_url}?$filter=PartitionKey eq '{clean_sym}'", h))
        if sas:
            request_attempts.append((f"{self.base_url}?$filter=PartitionKey eq '{clean_sym}'&{sas}", headers.copy()))

        if not request_attempts:
            logger.debug("No storage credentials available for Table Storage cache.")
            return None

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = None
                for url, req_headers in request_attempts:
                    try:
                        res = await client.get(url, headers=req_headers)
                        if res.status_code == 200:
                            break
                        logger.debug(f"Cache attempt returned {res.status_code}, trying next auth if available")
                    except Exception as attempt_err:
                        logger.debug(f"Cache connection attempt error: {attempt_err}")

                if not res or res.status_code != 200:
                    logger.debug(f"Table storage returned status {getattr(res, 'status_code', None)}")
                    return None

                data = res.json()
                items = data.get("value", [])
                if not items:
                    return None

                # Find entity with most recent Timestamp or storedAt
                sorted_items = sorted(
                    items,
                    key=lambda x: str(x.get("Timestamp") or x.get("storedAt") or ""),
                    reverse=True
                )
                latest = sorted_items[0]

                raw_price = latest.get("price")
                if not raw_price:
                    return None

                price = round(float(str(raw_price).replace("$", "").replace(",", "").strip()), 2)
                stored_at_str = str(latest.get("storedAt") or latest.get("Timestamp") or "")
                now_utc = datetime.now(timezone.utc)
                cached_at_str = now_utc.isoformat()

                # Calculate storage record age
                age_seconds = 86400.0
                if stored_at_str:
                    try:
                        iso_clean = stored_at_str.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(iso_clean)
                        age_seconds = (now_utc - dt).total_seconds()
                    except Exception:
                        pass

                # Strict Rule 1, 2, 4, 5, 6: Cryptographic HMAC signature & provenance inspection
                # An entity is verified ONLY if:
                # 1. It explicitly possesses non-empty trading_date
                # 2. provenance_verified is True
                # 3. It possesses a valid HMAC-SHA256 signature matching the canonical payload
                entity_trading_date = latest.get("trading_date")
                entity_provenance = latest.get("provenance_verified")
                entity_signature = latest.get("provenance_signature")
                entity_source = str(latest.get("data_source") or "").strip()
                entity_retrieved = str(latest.get("retrieved_at") or "").strip()

                # Normalize boolean representation
                if isinstance(entity_provenance, str):
                    is_prov_true = entity_provenance.lower() in ("true", "1")
                elif isinstance(entity_provenance, bool):
                    is_prov_true = entity_provenance
                else:
                    is_prov_true = False

                # Cryptographic HMAC verification
                has_valid_sig = False
                sig_error_reason = ""
                signing_key = settings.PROVENANCE_SIGNING_KEY.strip()

                if signing_key:
                    if not entity_signature:
                        sig_error_reason = "Missing cryptographic provenance signature"
                    elif not entity_trading_date:
                        sig_error_reason = "Missing market trading date"
                    else:
                        expected_sig = compute_canonical_signature(
                            symbol=clean_sym,
                            price=price,
                            trading_date=str(entity_trading_date).strip(),
                            data_source=entity_source,
                            retrieved_at=entity_retrieved,
                            signing_key=signing_key,
                        )
                        if hmac.compare_digest(str(entity_signature).strip(), expected_sig):
                            has_valid_sig = True
                        else:
                            sig_error_reason = "Cryptographic signature mismatch (tampered or unauthenticated record)"
                else:
                    sig_error_reason = "Backend signing key not configured"

                if entity_trading_date and is_prov_true and has_valid_sig:
                    trading_date = str(entity_trading_date).strip()
                    provenance_verified = True
                    data_source = entity_source or "Azure Table Storage Cache (Verified Provider)"
                    provenance_note = "Cryptographically verified market quote (HMAC-SHA256 verified)."
                else:
                    # Legacy, unsigned, or tampered entity: Never invent or substitute trading date
                    trading_date = None
                    provenance_verified = False
                    data_source = "Azure Table Storage (Unverified Record)"
                    provenance_note = f"Unverified record: {sig_error_reason}" if sig_error_reason else "Legacy entity lacks verified market trading date or provider provenance."

                # Rule 6: TTL calculation based on exact New York market hours
                is_market_open, market_status = get_ny_market_status(now_utc)
                ttl = settings.CACHE_TTL_MARKET_HOURS_SECONDS if is_market_open else settings.CACHE_TTL_OFF_HOURS_SECONDS
                is_fresh = (0 <= age_seconds <= ttl) and provenance_verified

                return CachedQuoteResult(
                    symbol=clean_sym,
                    price=price,
                    trading_date=trading_date,
                    stored_at=stored_at_str,
                    cached_at=cached_at_str,
                    age_seconds=max(0.0, age_seconds),
                    is_fresh=is_fresh,
                    provenance_verified=provenance_verified,
                    data_source=data_source,
                    provenance_signature=str(entity_signature).strip() if entity_signature else None,
                    provenance_note=provenance_note,
                )

        except Exception as e:
            logger.warning(f"Error querying Table Storage cache for {clean_sym}: {e}")
            return None

table_cache_service = TableStorageCacheService()

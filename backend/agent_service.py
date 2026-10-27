import os
import json
import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from config import settings
from models import StockResponse, DailyHistoricalQuote

logger = logging.getLogger("stockquote.agent")

def _safe_float(val: Any) -> Optional[float]:
    """Safely converts a value to float, returning None if None or invalid."""
    if val is None or val == "" or val == "null":
        return None
    try:
        if isinstance(val, str):
            val = val.replace("$", "").replace(",", "").strip()
        f = float(val)
        return f if not (f != f) else None  # Check for NaN
    except (ValueError, TypeError):
        return None

def _safe_int(val: Any) -> Optional[int]:
    """Safely converts a value to int, returning None if None or invalid."""
    if val is None or val == "" or val == "null":
        return None
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return int(float(val))
    except (ValueError, TypeError):
        return None

def _parse_agent_json(raw_text: str, default_symbol: str = "") -> Optional[Dict[str, Any]]:
    """Extract JSON object from agent output text, with robust fallback for bulleted text."""
    if not raw_text:
        return None

    # 1. Try direct JSON parse
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # 2. Extract from markdown code blocks ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    # 3. Find first outer curly braces
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(raw_text[start:end + 1])
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    # 4. Fallback: Parse conversational/bullet-point text format
    parsed: Dict[str, Any] = {"symbol": default_symbol}
    
    # Extract Price: e.g. "Price (most recent): $524.51" or "Close: $524.51"
    price_match = re.search(r"(?:price|close)[^$\d]*\$?\s*([0-9]+\.[0-9]+)", raw_text, re.IGNORECASE)
    if price_match:
        parsed["price"] = _safe_float(price_match.group(1))

    # Extract Trading Date: e.g. "2026-10-23" or "October 23, 2026"
    date_iso_match = re.search(r"(?:date|day)[^0-9]*([0-9]{4}-[0-9]{2}-[0-9]{2})", raw_text, re.IGNORECASE)
    if date_iso_match:
        parsed["trading_date"] = date_iso_match.group(1)
    else:
        date_word_match = re.search(r"([A-Za-z]+ \d{1,2},? \d{4})", raw_text)
        if date_word_match:
            try:
                dt = datetime.strptime(date_word_match.group(1).replace(",", ""), "%B %d %Y")
                parsed["trading_date"] = dt.strftime("%Y-%m-%d")
            except Exception:
                pass

    # Extract Open: e.g. "Open: $517.7450"
    open_match = re.search(r"open[^$\d]*\$?\s*([0-9]+\.[0-9]+)", raw_text, re.IGNORECASE)
    if open_match:
        parsed["open"] = _safe_float(open_match.group(1))

    # Extract High: e.g. "High: $525.77"
    high_match = re.search(r"high[^$\d]*\$?\s*([0-9]+\.[0-9]+)", raw_text, re.IGNORECASE)
    if high_match:
        parsed["high"] = _safe_float(high_match.group(1))

    # Extract Low: e.g. "Low: $515.70"
    low_match = re.search(r"low[^$\d]*\$?\s*([0-9]+\.[0-9]+)", raw_text, re.IGNORECASE)
    if low_match:
        parsed["low"] = _safe_float(low_match.group(1))

    # Extract Volume: e.g. "Volume: 13,681,067"
    vol_match = re.search(r"volume[^0-9]*([0-9,]+)", raw_text, re.IGNORECASE)
    if vol_match:
        parsed["volume"] = _safe_int(vol_match.group(1))

    # Extract Change: e.g. "Change: +$3.43 (+0.6582%)"
    chg_match = re.search(r"change[^0-9+-]*([+-]?\$?[0-9]+\.[0-9]+)(?:[^(]*\(([+-]?[0-9.]+)\%\))?", raw_text, re.IGNORECASE)
    if chg_match:
        parsed["change"] = _safe_float(chg_match.group(1))
        if chg_match.group(2):
            parsed["change_percent"] = _safe_float(chg_match.group(2))

    if parsed.get("price") is not None:
        return parsed

    return None

def _detect_mcp_rate_limit_or_error(response_output: List[Any]) -> Optional[str]:
    """Inspects response output items for Alpha Vantage rate limits or errors."""
    for item in response_output:
        raw_out = getattr(item, "output", None) or getattr(item, "content", None)
        if not raw_out:
            continue
        out_str = str(raw_out)
        
        # Check for Alpha Vantage rate limit message
        if "rate_limit" in out_str.lower() or "25 requests per day" in out_str.lower() or "daily request limit" in out_str.lower():
            return "Alpha Vantage API rate limit reached (standard tier limit is 25 requests per day). Live price is temporarily unavailable. Please retry later."
        if "thank you for using alpha vantage" in out_str.lower() or "higher api call volume" in out_str.lower():
            return "Alpha Vantage API rate limit reached. Please wait a minute and retry."
        if "error" in out_str.lower() and "message" in out_str.lower():
            try:
                err_dict = raw_out if isinstance(raw_out, dict) else json.loads(out_str)
                msg = err_dict.get("error", {}).get("message") if isinstance(err_dict, dict) else None
                if msg:
                    return f"Alpha Vantage error: {msg}"
            except Exception:
                return f"Alpha Vantage error: {out_str[:150]}"
    return None

def _extract_alpha_vantage_history(response_output: List[Any]) -> List[DailyHistoricalQuote]:
    """Extracts real historical OHLCV data from Alpha Vantage MCP McpCall result if present."""
    history = []
    try:
        for item in response_output:
            raw_out = getattr(item, "output", None) or getattr(item, "content", None)
            if not raw_out:
                continue

            ts_data = None
            if isinstance(raw_out, dict):
                ts_data = raw_out
            elif isinstance(raw_out, str) and "Time Series (Daily)" in raw_out:
                try:
                    ts_data = json.loads(raw_out)
                except Exception:
                    pass

            if ts_data and "Time Series (Daily)" in ts_data:
                daily_series = ts_data["Time Series (Daily)"]
                sorted_dates = sorted(daily_series.keys())[-10:]
                for d in sorted_dates:
                    bar = daily_series[d]
                    history.append(DailyHistoricalQuote(
                        date=d,
                        close=_safe_float(bar.get("4. close")) or 0.0,
                        open=_safe_float(bar.get("1. open")),
                        high=_safe_float(bar.get("2. high")),
                        low=_safe_float(bar.get("3. low")),
                        volume=_safe_int(bar.get("5. volume")),
                    ))
                break
    except Exception as e:
        logger.debug(f"Could not parse Alpha Vantage history: {e}")
    return history

class FoundryAgentService:
    def __init__(self):
        self.endpoint = settings.AZURE_AI_PROJECT_ENDPOINT
        self.agent_name = settings.AZURE_AGENT_NAME
        self.model_deployment = settings.AZURE_MODEL_DEPLOYMENT
        self._project_client = None
        self._openai_client = None

    def _init_client(self):
        """Initializes Azure AI Project Client using DefaultAzureCredential."""
        if self._openai_client:
            return

        from azure.identity import DefaultAzureCredential
        from azure.ai.projects import AIProjectClient

        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        
        self._project_client = AIProjectClient(
            endpoint=self.endpoint,
            credential=credential,
            allow_preview=True,
        )
        self._openai_client = self._project_client.get_openai_client(
            agent_name=self.agent_name
        )

    async def fetch_stock_quote(self, symbol: str) -> StockResponse:
        """
        Connects to Microsoft Foundry StockQuoteAgent to retrieve the latest daily closing price
        using the Alpha Vantage MCP Server TIME_SERIES_DAILY tool.
        """
        symbol = symbol.strip().upper()
        retrieved_at = datetime.now(timezone.utc).isoformat()
        
        prompt = (
            f"You are StockQuoteAgent connected to the Alpha Vantage MCP server. "
            f"Retrieve the latest available daily closing price for stock ticker '{symbol}' "
            f"using the Alpha Vantage TIME_SERIES_DAILY tool. "
            f"Do not guess or invent prices. "
            f"Respond STRICTLY with a valid JSON object matching this schema:\n"
            f'{{\n'
            f'  "symbol": "{symbol}",\n'
            f'  "price": <numeric daily close price>,\n'
            f'  "trading_date": "<YYYY-MM-DD>",\n'
            f'  "currency": "USD"\n'
            f'}}'
        )

        try:
            self._init_client()
            
            logger.info(
                f"Querying Microsoft Foundry Agent '{self.agent_name}' ({self.model_deployment}) for symbol '{symbol}'..."
            )
            
            # Use OpenAI responses API supported by Foundry Agent protocol
            response = self._openai_client.responses.create(
                model=self.model_deployment,
                input=prompt,
            )

            # Check if Alpha Vantage MCP call reported rate limits or errors
            mcp_error = _detect_mcp_rate_limit_or_error(getattr(response, "output", []))

            # Extract output text
            raw_text = getattr(response, "output_text", None) or ""
            if not raw_text and hasattr(response, "output"):
                for out_item in getattr(response, "output", []):
                    if getattr(out_item, "type", "") == "message" and hasattr(out_item, "content"):
                        for c in out_item.content:
                            if hasattr(c, "text"):
                                raw_text = c.text
                                break

            logger.info(f"Received raw agent output: {raw_text}")
            parsed = _parse_agent_json(raw_text, default_symbol=symbol)

            # Extract and validate price strictly as float
            raw_price = parsed.get("price") if parsed else None
            price = _safe_float(raw_price)

            if price is None or price <= 0:
                # 1. Check if agent output contained an explicit error field
                agent_err = parsed.get("error") if parsed else None
                if agent_err:
                    logger.warning(f"Agent explicit error payload for {symbol}: {agent_err}")
                    raise RuntimeError(f"Alpha Vantage MCP error: {agent_err}")

                # 2. Check if MCP tool call reported rate limits or other errors
                if mcp_error:
                    logger.warning(f"Alpha Vantage MCP error detected for {symbol}: {mcp_error}")
                    raise RuntimeError(mcp_error)

                # 3. Check if raw agent text reports rate limit notices
                raw_lower = raw_text.lower()
                if any(k in raw_lower for k in ["rate limit", "rate-limit", "daily request limit", "standard api rate limit"]):
                    raise RuntimeError(
                        f"Alpha Vantage API rate limit reached (standard tier limit is 25 requests per day). "
                        f"Live market price for '{symbol}' is temporarily unavailable."
                    )

                # 4. General fallback error
                raise RuntimeError(
                    f"Alpha Vantage MCP did not return a valid market price for '{symbol}'. "
                    f"Agent output: {raw_text[:200]}"
                )

            trading_date = str(parsed.get("trading_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            currency = str(parsed.get("currency") or "USD")

            # Extract real historical time series directly from the MCP McpCall result
            history_list = _extract_alpha_vantage_history(getattr(response, "output", []))

            # Day metrics
            open_price = _safe_float(parsed.get("open"))
            high_price = _safe_float(parsed.get("high"))
            low_price = _safe_float(parsed.get("low"))
            volume = _safe_int(parsed.get("volume"))
            change = _safe_float(parsed.get("change"))
            change_percent = _safe_float(parsed.get("change_percent"))

            if history_list and not open_price:
                latest_bar = history_list[-1]
                open_price = latest_bar.open
                high_price = latest_bar.high
                low_price = latest_bar.low
                volume = latest_bar.volume
                if len(history_list) >= 2 and change is None:
                    prev_close = history_list[-2].close
                    change = round(price - prev_close, 2)
                    change_percent = round((change / prev_close) * 100, 2)

            return StockResponse(
                symbol=symbol,
                price=round(price, 2),
                currency=currency,
                trading_date=trading_date,
                change=change,
                change_percent=change_percent,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                volume=volume,
                saved_to_azure=False,
                azure_save_status="PENDING",
                is_mock=False,
                data_source="Microsoft Foundry StockQuoteAgent (Alpha Vantage MCP TIME_SERIES_DAILY)",
                retrieved_at=retrieved_at,
                history=history_list,
                raw_agent_message=raw_text[:500],
            )

        except Exception as e:
            err_msg = str(e)
            logger.error(f"Live Foundry Agent execution encountered an error: {err_msg}")
            
            # Rule: Never substitute hardcoded/mock prices when mock fallback is disabled
            if not settings.ALLOW_MOCK_FALLBACK:
                logger.error("Mock fallback is disabled. Re-raising real error.")
                raise RuntimeError(err_msg)

            # In dev mock mode only
            logger.warning(f"Generating mock fallback quote for '{symbol}'.")
            return StockResponse(
                symbol=symbol,
                price=100.0,
                currency="USD",
                trading_date="2026-10-23",
                saved_to_azure=False,
                azure_save_status="PENDING",
                is_mock=True,
                data_source="Development Mock / Fallback",
                retrieved_at=retrieved_at,
                history=[],
                raw_agent_message=f"Mock data active: {err_msg}",
            )

agent_service = FoundryAgentService()

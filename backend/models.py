from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re

class StockRequest(BaseModel):
    symbol: str = Field(
        ...,
        description="Stock ticker symbol (e.g. MSFT, AAPL, TSLA, NVDA, GOOGL)",
        min_length=1,
        max_length=10,
    )

    @field_validator("symbol")
    @classmethod
    def validate_and_normalize_symbol(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(r"^[A-Z0-9.]{1,10}$", clean):
            raise ValueError(
                "Invalid ticker symbol. Must contain 1-10 uppercase alphanumeric characters or dots (e.g., 'MSFT', 'BRK.A')."
            )
        return clean

class DailyHistoricalQuote(BaseModel):
    date: str
    close: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None

class StockResponse(BaseModel):
    symbol: str
    price: float
    currency: str = "USD"
    trading_date: str
    change: Optional[float] = None
    change_percent: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    volume: Optional[int] = None
    
    # Azure integration status
    saved_to_azure: bool = False
    azure_save_status: str = "PENDING"  # SUCCESS, FAILED, SKIPPED, NOT_CONFIGURED
    azure_save_message: Optional[str] = None
    azure_table_name: str = "StockQuotes"
    azure_logic_app: str = "stockworkflow616"
    
    # Source metadata
    is_mock: bool = False
    is_cached: bool = False
    cached_at: Optional[str] = None
    is_historical_fallback: bool = False
    provenance_verified: bool = False  # Strict Default: False unless explicitly verified from genuine provider response
    provenance_signature: Optional[str] = None
    provenance_note: Optional[str] = None
    data_source: str = "Microsoft Foundry AI Agent (Alpha Vantage TIME_SERIES_DAILY)"
    retrieved_at: str
    history: List[DailyHistoricalQuote] = []
    raw_agent_message: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str = "StockQuote AI Backend"
    version: str = "1.0.0"
    azure_foundry_configured: bool
    foundry_endpoint: str
    foundry_agent: str
    foundry_model: str
    logic_app_configured: bool
    logic_app_name: str
    azure_table_name: str
    mock_mode_allowed: bool

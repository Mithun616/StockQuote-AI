import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Microsoft Foundry & Azure AI Configuration
    # Resource Group: stock-agent-rg
    # Foundry Resource: stock-foundry-us616
    # Foundry Project: StockQuotesAgentUS
    # Foundry Agent: StockQuoteAgent
    AZURE_AI_PROJECT_ENDPOINT: str = os.getenv(
        "AZURE_AI_PROJECT_ENDPOINT",
        "https://stock-foundry-us616.services.ai.azure.com/api/projects/StockQuotesAgentUS",
    )
    AZURE_AGENT_NAME: str = os.getenv(
        "AZURE_AGENT_NAME",
        "StockQuoteAgent",
    )
    AZURE_MODEL_DEPLOYMENT: str = os.getenv(
        "AZURE_MODEL_DEPLOYMENT",
        "gpt-5-mini",
    )

    # Azure Logic App Configuration
    # Logic App: stockworkflow616
    # Trigger: HTTP POST
    # Table Storage: StockQuotes (storage account: stockagent)
    LOGIC_APP_URL: str = os.getenv("LOGIC_APP_URL", "")

    # Application Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ]

    # Mode: if live credentials are not yet present or Alpha Vantage MCP is unreachable,
    # allow realistic mock fallback clearly labeled as is_mock: True
    ALLOW_MOCK_FALLBACK: bool = os.getenv("ALLOW_MOCK_FALLBACK", "true").lower() in ("true", "1", "yes")

    # Rate limiting: max requests per window
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

    # Azure Table Storage Cache Configuration
    TABLE_STORAGE_ACCOUNT: str = os.getenv("TABLE_STORAGE_ACCOUNT", "stockagent")
    TABLE_STORAGE_TABLE: str = os.getenv("TABLE_STORAGE_TABLE", "StockQuotes")
    CACHE_TTL_MARKET_HOURS_SECONDS: int = int(os.getenv("CACHE_TTL_MARKET_HOURS_SECONDS", "14400"))  # 4 hours
    CACHE_TTL_OFF_HOURS_SECONDS: int = int(os.getenv("CACHE_TTL_OFF_HOURS_SECONDS", "86400"))  # 24 hours
    TABLE_STORAGE_READ_SAS: str = os.getenv("TABLE_STORAGE_READ_SAS", "")

    # Cryptographic Provenance & Backend Authentication
    PROVENANCE_SIGNING_KEY: str = os.getenv("PROVENANCE_SIGNING_KEY", "")
    BACKEND_LOGIC_APP_AUTH_TOKEN: str = os.getenv("BACKEND_LOGIC_APP_AUTH_TOKEN", "")

settings = Settings()

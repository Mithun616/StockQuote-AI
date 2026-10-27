# StockQuote AI Architecture & Provenance Security

## Data Flow Diagram

1. **User Query**: Client searches symbol (e.g. `MSFT`) on Static Web App.
2. **Cache Check**: Backend queries Azure Table Storage via Managed Identity (`PartitionKey eq 'MSFT'`).
   - If entity exists, is fresh (TTL: 4h market hours / 24h off-hours), AND HMAC-SHA256 signature matches canonical payload:
     Returns HTTP 200 CACHED (0 Alpha Vantage calls, ~0.5s latency).
3. **Live Query (Cache Miss / Expired)**:
   - Backend queries Microsoft Foundry Agent (`gpt-5-mini`).
   - Agent invokes Alpha Vantage MCP tool `TIME_SERIES_DAILY`.
   - On success:
     - Backend canonicalizes payload: `SYMBOL|PRICE_2DEC|TRADING_DATE|DATA_SOURCE|RETRIEVED_AT`.
     - Generates HMAC-SHA256 signature using `PROVENANCE_SIGNING_KEY`.
     - Posts to Logic App with `x-backend-auth-token` header.
     - Logic App validates ingress token and saves all 8 fields to Table Storage.
   - On rate limit / error:
     - Checks if Table Storage has verified historical fallback.
     - If entity lacks HMAC signature or verified date, strictly rejects with HTTP 429.
     - Never invents prices (`ALLOW_MOCK_FALLBACK=false`).

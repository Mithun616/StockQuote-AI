# Environment Variables Reference

## Backend (.env & App Service App Settings)

| Name | Type | Description | Example / Default |
| :--- | :--- | :--- | :--- |
| `AZURE_AI_PROJECT_ENDPOINT` | string | Azure AI Foundry Project Endpoint | `https://stock-foundry-us616.services.ai.azure.com/api/projects/StockQuotesAgentUS` |
| `AZURE_AGENT_NAME` | string | Microsoft Foundry Agent Name | `StockQuoteAgent` |
| `AZURE_MODEL_DEPLOYMENT` | string | Model deployment name | `gpt-5-mini` |
| `LOGIC_APP_URL` | string | Azure Logic App HTTP Trigger Callback URL | `https://prod-23.centralindia.logic.azure.com/.../invoke?...` |
| `PROVENANCE_SIGNING_KEY` | string | 256-bit secret key for HMAC-SHA256 signatures | 64-character hexadecimal string |
| `BACKEND_LOGIC_APP_AUTH_TOKEN` | string | Shared secret token for Logic App ingress validation | 64-character hexadecimal string |
| `TABLE_STORAGE_ACCOUNT` | string | Azure Storage Account name | `stockagent` |
| `TABLE_STORAGE_TABLE` | string | Azure Storage Table name | `StockQuotes` |
| `ALLOW_MOCK_FALLBACK` | boolean | Disables all mock data in production | `false` |
| `CORS_ORIGINS` | string | Comma-separated list of allowed origins | `http://localhost:5173,https://<swa-domain>.azurestaticapps.net` |
| `HOST` | string | Host to bind local server | `0.0.0.0` |
| `PORT` | integer | Port to bind local server | `8000` |
| `CACHE_TTL_MARKET_HOURS_SECONDS` | integer | Cache TTL during New York market session | `14400` (4 hours) |
| `CACHE_TTL_OFF_HOURS_SECONDS` | integer | Cache TTL during off-hours & weekends | `86400` (24 hours) |

## Frontend (.env.production & .env.development)

| Name | Description | Example / Default |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Base URL of deployed backend API | `https://stockquote-api-mithun616-d4gefkevgugmh2fp.centralindia-01.azurewebsites.net` (empty in dev for Vite proxy) |

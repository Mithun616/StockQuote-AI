# StockQuote AI Deployment Guide

This guide details how to redeploy all components of StockQuote AI from scratch.

---

## 1. Azure Infrastructure Requirements

- **Resource Group**: `stock-agent-rg` (Region: `centralindia` or `eastus`)
- **Storage Account**: Standard LRS (e.g. `stockagent`), with Table `StockQuotes`.
- **Azure App Service**: Linux Free F1, Python 3.11 (e.g. `stockquote-api-mithun616`).
- **Azure Static Web App**: Free tier (e.g. `stockquote-web-mithun616`).
- **Azure Logic App**: Consumption tier (e.g. `stockworkflow616`).
- **Microsoft Foundry**: Project `StockQuotesAgentUS` with model deployment `gpt-5-mini`.

---

## 2. Logic App Setup

1. Create a Consumption Logic App `stockworkflow616`.
2. Apply the workflow definition from `azure_config/logic_app_workflow.json`.
3. Set parameter `backendAuthSecret` (type: SecureString) to your chosen 256-bit token.
4. Note the HTTP POST Trigger callback URL.

---

## 3. Storage Account Setup

1. Create table `StockQuotes` in the storage account.
2. Under Storage Account -> Access Control (IAM), assign `Storage Table Data Reader` to the App Service Managed Identity.

---

## 4. Backend Deployment

1. Package `backend/` into `backend_deploy.zip` (excluding `.env` and `__pycache__`).
2. Deploy via Azure CLI:
   ```bash
   az webapp deploy --resource-group stock-agent-rg --name stockquote-api-mithun616 --src-path backend_deploy.zip --type zip
   ```
3. Set App Settings:
   ```bash
   az webapp config appsettings set --name stockquote-api-mithun616 --resource-group stock-agent-rg --settings \
       ALLOW_MOCK_FALLBACK=false \
       AZURE_AI_PROJECT_ENDPOINT="https://<foundry-endpoint>" \
       AZURE_AGENT_NAME="StockQuoteAgent" \
       AZURE_MODEL_DEPLOYMENT="gpt-5-mini" \
       LOGIC_APP_URL="<logic-app-trigger-url>" \
       PROVENANCE_SIGNING_KEY="<256-bit-hex-key>" \
       BACKEND_LOGIC_APP_AUTH_TOKEN="<256-bit-hex-token>" \
       CORS_ORIGINS="http://localhost:5173,https://<your-static-web-app>.azurestaticapps.net"
   ```

---

## 5. Frontend Deployment

1. Set `VITE_API_BASE_URL` in `frontend/.env.production` to your App Service URL.
2. Build frontend:
   ```bash
   cd frontend && npm run build
   ```
3. Deploy to Azure Static Web Apps:
   ```bash
   npx @azure/static-web-apps-cli deploy ./dist --deployment-token <TOKEN> --env production
   ```

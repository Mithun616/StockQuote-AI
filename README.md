# StockQuote AI — Full-Stack Azure-Integrated Stock Market Dashboard

A production-oriented stock market dashboard powered by **Microsoft Foundry AI Agent**, **Alpha Vantage MCP Server (`TIME_SERIES_DAILY`)**, and automated **Azure Table Storage** persistence via **Azure Logic App**.

---

## 🏗️ Architecture & Data Flow

```mermaid
flowchart LR
    A["React 19 + Vite UI\n(Tailwind CSS)"] -->|POST /api/stock| B["FastAPI Backend\n(Python 3.11)"]
    B -->|Azure Identity\nDefaultAzureCredential| C["Microsoft Foundry\nStockQuoteAgent\n(gpt-5-mini)"]
    C -->|Tool: TIME_SERIES_DAILY| D["Alpha Vantage MCP\n(Market Data)"]
    D -->|Daily Close JSON| C
    C -->|Structured Quote| B
    B -->|HTTP POST\n{'symbol','price'}| E["Azure Logic App\n(stockworkflow616)"]
    E -->|Insert Entity| F["Azure Table Storage\n(stockagent / StockQuotes)"]
    B -->|JSON Response\n+ Save Status| A
```

### Existing Azure Infrastructure

| Resource | Name / Endpoint | Purpose |
| :--- | :--- | :--- |
| **Resource Group** | `stock-agent-rg` | Resource container |
| **Foundry Resource** | `stock-foundry-us616` | Azure AI Foundry host |
| **Foundry Project** | `StockQuotesAgentUS` | AI Project |
| **Foundry Agent** | `StockQuoteAgent` | Financial quoting agent |
| **Model Deployment** | `gpt-5-mini` | LLM backing the agent |
| **MCP Integration** | Alpha Vantage MCP Server | Method: `TIME_SERIES_DAILY` |
| **Logic App** | `stockworkflow616` | HTTP POST trigger workflow |
| **Storage Account** | `stockagent` | Table Storage account |
| **Storage Table** | `StockQuotes` | Persistence destination |

---

## 🚀 Quick Start (Local Run)

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### 2. Backend Setup
```bash
cd backend

# Install dependencies (already completed in workspace)
pip install -r requirements.txt

# Configure your environment variables
cp .env.example .env
```

Open `backend/.env` and insert your signed Azure Logic App URL:
```ini
AZURE_AI_PROJECT_ENDPOINT=https://stock-foundry-us616.services.ai.azure.com/api/projects/StockQuotesAgentUS
AZURE_AGENT_NAME=StockQuoteAgent
AZURE_MODEL_DEPLOYMENT=gpt-5-mini
LOGIC_APP_URL=https://prod-XX.eastus.logic.azure.com:443/workflows/.../triggers/manual/paths/invoke?...
ALLOW_MOCK_FALLBACK=true
```

Start the FastAPI backend:
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- Swagger API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies (already completed)
npm install

# Start Vite dev server
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

### 4. One-Click Launch Script (Windows)
Run both backend and frontend simultaneously:
```powershell
.\run-all.ps1
```

---

## 🧪 Testing & Verification

### Run Pytest Test Suite
From the `backend` directory:
```bash
cd backend
python -m pytest -v
```
**Test coverage:**
- `test_health_endpoint` — Validates Azure config reporting
- `test_symbol_validation_valid` — Validates uppercase normalization (`msft` -> `MSFT`)
- `test_symbol_validation_invalid` — Rejects invalid ticker formats with HTTP 422
- `test_post_stock_valid_symbol` — Full quote workflow
- `test_logic_app_missing_url` — Verifies missing URL status reporting (`NOT_CONFIGURED`)
- `test_logic_app_success_mock` — Verifies HTTP 200/202 save confirmation contract
- `test_logic_app_failure_mock` — Verifies HTTP 500 error reporting
- `test_popular_stocks_endpoint` — Validates quick-select stocks
- `test_rate_limiting_trigger` — Enforces 30 req/min anti-abuse rate limiting

### Run End-to-End Verification Script
```bash
python backend/test_e2e.py
```

---

## ☁️ Azure Cloud Deployment

The application is pre-configured for deployment to Azure:
- **Backend**: Azure App Service (Linux, Python 3.11) with System-Assigned Managed Identity
- **Frontend**: Azure Static Web Apps (Free tier)

### Proposed Deployment Resources & Costs

| Resource | Service | SKU / Tier | Estimated Monthly Cost |
| :--- | :--- | :--- | :--- |
| **Backend** | Azure App Service (Linux) | Basic B1 | ~$13.00 / month (or Free F1 $0) |
| **Frontend** | Azure Static Web Apps | Free Tier | $0.00 / month |
| **Logic App** | Existing `stockworkflow616` | Consumption | ~$0.000025 per call |
| **Table Storage** | Existing `StockQuotes` | Standard LRS | < $0.05 / month |

### Deployment Command
```powershell
.\deployment\azure-deploy.ps1 -ResourceGroup "stock-agent-rg" -Location "eastus"
```
*Note: The script prompts for explicit confirmation before creating any Azure resources.*

---

## 🔍 How to Verify Saved Quotes in Azure Table Storage

1. Open the [Azure Portal](https://portal.azure.com).
2. Navigate to your storage account: **`stockagent`** in resource group **`stock-agent-rg`**.
3. Under **Storage browser** in the left menu, select **Tables**.
4. Click on the **`StockQuotes`** table.
5. In the table viewer, verify that the recently searched stock (e.g., `MSFT`, `AAPL`) has a new record with:
   - `PartitionKey` or Symbol: `MSFT`
   - `Price`: numeric closing price (e.g. `524.51`)
   - `Timestamp`: exact ingestion time from `stockworkflow616`
6. Alternatively, in the Azure Portal, open the Logic App **`stockworkflow616`** and click **Runs history** to inspect the successful trigger execution and HTTP POST input/output body.

---

## 📋 Azure Role Assignments for Managed Identity

When running in Azure App Service, grant the App Service's Managed Identity access to Microsoft Foundry:
```bash
# Get Web App Principal ID
PRINCIPAL_ID=$(az webapp identity show --name <web-app-name> --resource-group stock-agent-rg --query principalId -o tsv)

# Assign Azure AI Developer role to the web app
az role assignment create \
    --assignee $PRINCIPAL_ID \
    --role "Azure AI Developer" \
    --scope "/subscriptions/<subscription-id>/resourceGroups/stock-agent-rg/providers/Microsoft.CognitiveServices/accounts/stock-foundry-us616"
```

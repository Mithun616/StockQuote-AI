#!/usr/bin/env bash
set -e

RESOURCE_GROUP=${1:-"stock-agent-rg"}
LOCATION=${2:-"eastus"}
LOGIC_APP_URL=${3:-""}

echo "============================================================"
echo " StockQuote AI — Azure Production Deployment Script (Bash)"
echo "============================================================"

# 1. Check Azure CLI
if ! command -v az &> /dev/null; then
    echo "[ERROR] Azure CLI ('az') is not installed. Visit https://aka.ms/installazurecli"
    exit 1
fi

# 2. Check Auth
az account show --output table || az login

# 3. Check Resource Group
if [ "$(az group exists --name "$RESOURCE_GROUP")" != "true" ]; then
    echo "[ERROR] Resource group '$RESOURCE_GROUP' does not exist."
    exit 1
fi

# 4. Display Proposed Actions
echo ""
echo "PROPOSED ACTIONS & COSTS:"
echo "  • Azure App Service (Linux, Python 3.11): Basic B1 (~$13/mo) or Free F1"
echo "  • Azure Static Web Apps: Free Tier ($0/mo)"
echo "  • Preserves existing: stock-foundry-us616, stockworkflow616, stockagent"
echo ""
read -p "Do you approve deploying these resources? (y/N): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "[ABORTED] Deployment cancelled."
    exit 0
fi

# 5. Execute Bicep Deployment
az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file ./bicep/main.bicep \
    --parameters logicAppUrl="$LOGIC_APP_URL" \
    --output table

echo "[DONE] Deployment completed successfully!"

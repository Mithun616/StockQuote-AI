<#
.SYNOPSIS
    Automated Azure Deployment Script for StockQuote AI.
.DESCRIPTION
    Deploys FastAPI backend to Azure App Service and React frontend to Azure Static Web Apps
    within the existing resource group 'stock-agent-rg'.
#>

param(
    [string]$ResourceGroup = "stock-agent-rg",
    [string]$Location = "eastus",
    [string]$LogicAppUrl = ""
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " StockQuote AI — Azure Production Deployment Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check Azure CLI installation
Write-Host "`n[1/5] Checking Azure CLI..." -ForegroundColor Yellow
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Azure CLI ('az') is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Azure CLI from: https://aka.ms/installazurecliwindows" -ForegroundColor Yellow
    exit 1
}
Write-Host "[PASS] Azure CLI found." -ForegroundColor Green

# 2. Check Azure Authentication
Write-Host "`n[2/5] Checking Azure Authentication..." -ForegroundColor Yellow
$account = az account show --output json 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "[WARNING] Not currently authenticated to Azure. Initiating 'az login'..." -ForegroundColor Yellow
    az login --output table
    $account = az account show --output json | ConvertFrom-Json
}
Write-Host "[PASS] Authenticated as: $($account.user.name) (Subscription: $($account.name))" -ForegroundColor Green

# 3. Verify Existing Resource Group
Write-Host "`n[3/5] Verifying Resource Group '$ResourceGroup'..." -ForegroundColor Yellow
$rgExists = az group exists --name $ResourceGroup
if ($rgExists -ne "true") {
    Write-Host "[ERROR] Resource group '$ResourceGroup' does not exist." -ForegroundColor Red
    Write-Host "Please confirm your subscription has access to the existing 'stock-agent-rg' resource group." -ForegroundColor Yellow
    exit 1
}
Write-Host "[PASS] Resource Group '$ResourceGroup' confirmed." -ForegroundColor Green

# 4. Display Proposed Actions and Cost Estimates
Write-Host "`n[4/5] PROPOSED CLOUD ACTIONS & COST ESTIMATES:" -ForegroundColor Cyan
Write-Host "  • Backend Service: Azure App Service (Linux, Python 3.11)" -ForegroundColor White
Write-Host "    - SKU: Basic B1 (~`$13.00/month) or Free F1 (`$0.00/month)" -ForegroundColor White
Write-Host "    - System-Assigned Managed Identity enabled for Azure AI Foundry access" -ForegroundColor White
Write-Host "  • Frontend Service: Azure Static Web Apps (Free Tier: `$0.00/month)" -ForegroundColor White
Write-Host "  • Existing resources preserved untouched:" -ForegroundColor White
Write-Host "    - Microsoft Foundry: stock-foundry-us616 / StockQuotesAgentUS" -ForegroundColor Gray
Write-Host "    - Agent: StockQuoteAgent (gpt-5-mini)" -ForegroundColor Gray
Write-Host "    - Logic App: stockworkflow616" -ForegroundColor Gray
Write-Host "    - Storage Account: stockagent (StockQuotes table)" -ForegroundColor Gray

$confirm = Read-Host "`nDo you approve deploying these resources to '$ResourceGroup'? (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "[ABORTED] Deployment cancelled by user. No resources created or modified." -ForegroundColor Yellow
    exit 0
}

# 5. Deployment Execution
Write-Host "`n[5/5] Deploying Infrastructure via Bicep..." -ForegroundColor Yellow

if (-not $LogicAppUrl) {
    $LogicAppUrl = Read-Host "Enter your Logic App Trigger URL (or leave blank to configure later)"
}

az deployment group create `
    --resource-group $ResourceGroup `
    --template-file ./bicep/main.bicep `
    --parameters logicAppUrl="$LogicAppUrl" `
    --output table

Write-Host "`n[DONE] Azure Infrastructure deployment complete!" -ForegroundColor Green

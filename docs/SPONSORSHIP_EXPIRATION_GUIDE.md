# Azure Sponsorship Expiration & Migration Guide

## What Happens if Azure Sponsorship Credits Expire?

1. **App Service (Free F1 Plan)**:
   - Free F1 tier web apps do not incur compute charges, but if the Azure subscription enters a Disabled state due to expiration of credit, the App Service is stopped.
2. **Azure Static Web App (Free Plan)**:
   - Free Static Web Apps remain hosted, but if the parent subscription is disabled, access to management plane and custom domains may be restricted.
3. **Table Storage (Standard LRS)**:
   - Storage accounts incur nominal storage costs (< $0.05/month). If subscription disables, storage becomes read-only or temporarily inaccessible until reactivated or converted to Pay-As-You-Go.
4. **Microsoft Foundry & OpenAI Models**:
   - Serverless model inference and Foundry agents require an active subscription billing profile.

---

## Safe Migration / Offline Preservation Steps

1. **Local Self-Hosted Execution**:
   - The backup in `backend/` and `frontend/` runs completely standalone.
   - You can run the FastAPI backend locally and connect to free market data providers (e.g. Yahoo Finance via `yfinance`, Finnhub, or Twelve Data) or a local SQLite/PostgreSQL cache.
2. **Converting to Azure Pay-As-You-Go (Zero / Near-Zero Cost)**:
   - If you want to keep the Azure deployment live without sponsorship, converting the subscription to Pay-As-You-Go keeps your App Service (Free F1) and Static Web App (Free) at **$0.00/month**.
   - Storage costs for Table Storage with a few hundred records is **< $0.01/month**.
   - Alpha Vantage Free tier is **$0.00/month**.

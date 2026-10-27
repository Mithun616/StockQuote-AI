@description('Target Azure region (e.g. eastus, eastus2)')
param location string = resourceGroup().location

@description('App name prefix')
param appName string = 'stockquote-ai'

@description('Unique suffix for globally unique resource names')
param uniqueSuffix string = substring(uniqueString(resourceGroup().id), 0, 6)

@description('Azure AI Foundry Project Endpoint')
param azureAiProjectEndpoint string = 'https://stock-foundry-us616.services.ai.azure.com/api/projects/StockQuotesAgentUS'

@description('Azure AI Agent Name')
param azureAgentName string = 'StockQuoteAgent'

@description('Azure Logic App Trigger URL (Signed HTTP POST)')
@secure()
param logicAppUrl string = ''

var appServicePlanName = '${appName}-plan-${uniqueSuffix}'
var webAppName = '${appName}-api-${uniqueSuffix}'
var staticWebAppName = '${appName}-web-${uniqueSuffix}'

// 1. Linux App Service Plan for FastAPI Backend
resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// 2. Linux App Service for FastAPI Backend
resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: webAppName
  location: location
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'gunicorn -c gunicorn_conf.py main:app'
      alwaysOn: true
      cors: {
        allowedOrigins: ['*']
      }
      appSettings: [
        {
          name: 'AZURE_AI_PROJECT_ENDPOINT'
          value: azureAiProjectEndpoint
        }
        {
          name: 'AZURE_AGENT_NAME'
          value: azureAgentName
        }
        {
          name: 'AZURE_MODEL_DEPLOYMENT'
          value: 'gpt-5-mini'
        }
        {
          name: 'LOGIC_APP_URL'
          value: logicAppUrl
        }
        {
          name: 'ALLOW_MOCK_FALLBACK'
          value: 'false'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
      ]
    }
    httpsOnly: true
  }
}

// 3. Azure Static Web App for React Frontend
resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {
  name: staticWebAppName
  location: 'eastus2' // SWA available regions
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {}
}

output backendAppServiceUrl string = 'https://${webApp.properties.defaultHostName}'
output backendPrincipalId string = webApp.identity.principalId
output frontendStaticWebAppUrl string = 'https://${staticWebApp.properties.defaultHostname}'

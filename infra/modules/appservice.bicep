@description('Azure region for App Service resources.')
param location string

@description('App Service Plan name.')
param appServicePlanName string

@description('Web app name.')
param webAppName string

@description('App Service plan SKU name.')
param planSkuName string = 'B1'

@description('Gunicorn startup command. Set by T046 when prod.py and startup.sh are ready.')
param startupCommand string = 'gunicorn --bind=0.0.0.0 --timeout 600 resumetailor.wsgi'

@description('Linux runtime stack, for example PYTHON|3.12.')
param linuxFxVersion string = 'PYTHON|3.12'

@description('Application Insights connection string.')
param appInsightsConnectionString string

@description('Blob endpoint URL.')
param blobEndpoint string

@description('Blob container name used by the app.')
param blobContainerName string

@description('Storage account name used by the app.')
param storageAccountName string

@description('Key Vault URI.')
param keyVaultUri string

@description('Key Vault secret URI for Django secret key.')
param djangoSecretKeySecretUri string

@description('Key Vault secret URI for GitHub Models token.')
param githubModelsTokenSecretUri string

@description('Key Vault secret URI for DATABASE_URL.')
param databaseUrlSecretUri string

@description('GitHub Models endpoint URL.')
param githubModelsEndpoint string

@description('GitHub Models model deployment name.')
param githubModelsModel string

@description('Common tags applied to resources.')
param tags object = {}

// B* → Basic, S* → Standard, contains v3 → PremiumV3, contains v2 → PremiumV2, other P* → PremiumV3
var planTier = contains(toLower(planSkuName), 'v3') ? 'PremiumV3'
             : contains(toLower(planSkuName), 'v2') ? 'PremiumV2'
             : startsWith(toLower(planSkuName), 's') ? 'Standard'
             : startsWith(toLower(planSkuName), 'p') ? 'PremiumV3'
             : 'Basic'

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: {
    name: planSkuName
    tier: planTier
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: webAppName
  location: location
  tags: tags
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    httpsOnly: true
    serverFarmId: appServicePlan.id
    publicNetworkAccess: 'Enabled'
    siteConfig: {
      linuxFxVersion: linuxFxVersion
      ftpsState: 'FtpsOnly'
      minTlsVersion: '1.2'
      http20Enabled: true
      alwaysOn: true
      appCommandLine: startupCommand
      appSettings: [
        {
          name: 'DJANGO_SETTINGS_MODULE'
          value: 'resumetailor.settings.prod'
        }
        {
          name: 'USE_LOCAL_FILE_STORAGE'
          value: 'false'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: '1'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'AZURE_BLOB_ENDPOINT'
          value: blobEndpoint
        }
        {
          name: 'AZURE_STORAGE_ACCOUNT_NAME'
          value: storageAccountName
        }
        {
          name: 'AZURE_STORAGE_CONTAINER_NAME'
          value: blobContainerName
        }
        {
          name: 'KEY_VAULT_URI'
          value: keyVaultUri
        }
        {
          name: 'GITHUB_MODELS_ENDPOINT'
          value: githubModelsEndpoint
        }
        {
          name: 'GITHUB_MODELS_MODEL'
          value: githubModelsModel
        }
        {
          name: 'DJANGO_SECRET_KEY'
          value: '@Microsoft.KeyVault(SecretUri=${djangoSecretKeySecretUri})'
        }
        {
          name: 'GITHUB_MODELS_TOKEN'
          value: '@Microsoft.KeyVault(SecretUri=${githubModelsTokenSecretUri})'
        }
        {
          name: 'DATABASE_URL'
          value: '@Microsoft.KeyVault(SecretUri=${databaseUrlSecretUri})'
        }
      ]
    }
  }
}

output appServicePlanName string = appServicePlan.name
output webAppName string = webApp.name
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output principalId string = webApp.identity.principalId

targetScope = 'resourceGroup'

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Project/application short name used in resource naming.')
@minLength(3)
param projectName string = 'resumetailor'

@description('Deployment environment name, for example dev or prod.')
@minLength(1)
param environmentName string

@description('Common tags applied to all resources.')
param tags object = {}

@description('App Service Plan SKU, for example B1, P1v3.')
param appServicePlanSkuName string = 'B1'

@description('PostgreSQL flexible server SKU name.')
param postgresSkuName string = 'Standard_B1ms'

@description('PostgreSQL storage size in MB.')
param postgresStorageMb int = 32768

@description('PostgreSQL major version.')
param postgresVersion string = '16'

@description('Application database name.')
param postgresDatabaseName string = 'resumetailor'

@description('PostgreSQL administrator login username.')
param postgresAdminLogin string = 'pgadminrt'

@secure()
@description('PostgreSQL administrator password.')
param postgresAdminPassword string

@secure()
@description('Django secret key stored in Key Vault for runtime.')
param djangoSecretKey string

@secure()
@description('GitHub Models token stored in Key Vault for runtime.')
param githubModelsToken string

@description('GitHub Models endpoint URL.')
param githubModelsEndpoint string = 'https://models.inference.ai.azure.com'

@description('GitHub Models model deployment name.')
param githubModelsModel string = 'gpt-4.1-mini'

@description('Storage SKU name.')
param storageSkuName string = 'Standard_LRS'

@description('Storage account name, 3-24 lowercase alphanumeric characters.')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('Blob container used for source uploads and generated artifacts.')
param blobContainerName string = 'resumetailor-artifacts'

@description('App Service Linux runtime stack.')
param linuxFxVersion string = 'PYTHON|3.12'

@description('App Service startup command for Django/Gunicorn.')
param startupCommand string = 'bash startup.sh'

@description('Set to true for production-grade vault purge protection.')
param keyVaultEnablePurgeProtection bool = true

@description('Key Vault name, 3-24 characters.')
@minLength(3)
@maxLength(24)
param keyVaultName string

var baseName = toLower('${projectName}-${environmentName}')
var appServicePlanName = '${baseName}-plan'
var webAppName = take(replace('${baseName}-web', '_', '-'), 60)
var postgresServerName = take(replace('${baseName}-pg', '_', '-'), 63)
var appInsightsName = '${baseName}-appi'

module monitoring './modules/monitoring.bicep' = {
  params: {
    location: location
    appInsightsName: appInsightsName
    tags: tags
  }
}

module postgres './modules/postgres.bicep' = {
  params: {
    location: location
    serverName: postgresServerName
    databaseName: postgresDatabaseName
    adminLogin: postgresAdminLogin
    adminPassword: postgresAdminPassword
    skuName: postgresSkuName
    storageMb: postgresStorageMb
    postgresVersion: postgresVersion
    tags: tags
  }
}

module storage './modules/storage.bicep' = {
  params: {
    location: location
    storageAccountName: storageAccountName
    storageSkuName: storageSkuName
    blobContainerName: blobContainerName
    tags: tags
  }
}

var databaseUrl = 'postgresql://${postgresAdminLogin}:${postgresAdminPassword}@${postgres.outputs.fqdn}:5432/${postgresDatabaseName}?sslmode=require'

module keyVault './modules/keyvault.bicep' = {
  params: {
    location: location
    keyVaultName: keyVaultName
    enablePurgeProtection: keyVaultEnablePurgeProtection
    djangoSecretKey: djangoSecretKey
    githubModelsToken: githubModelsToken
    databaseUrl: databaseUrl
    tags: tags
  }
}

module appService './modules/appservice.bicep' = {
  params: {
    location: location
    appServicePlanName: appServicePlanName
    webAppName: webAppName
    planSkuName: appServicePlanSkuName
    linuxFxVersion: linuxFxVersion
    startupCommand: startupCommand
    appInsightsConnectionString: monitoring.outputs.connectionString
    blobEndpoint: storage.outputs.blobEndpoint
    blobContainerName: storage.outputs.blobContainerName
    storageAccountName: storage.outputs.storageAccountName
    keyVaultUri: keyVault.outputs.vaultUri
    djangoSecretKeySecretUri: keyVault.outputs.djangoSecretKeySecretUri
    githubModelsTokenSecretUri: keyVault.outputs.githubModelsTokenSecretUri
    databaseUrlSecretUri: keyVault.outputs.databaseUrlSecretUri
    githubModelsEndpoint: githubModelsEndpoint
    githubModelsModel: githubModelsModel
    tags: tags
  }
}

var storageBlobDataContributorRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
var keyVaultSecretsUserRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')

resource storageAccountResource 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource keyVaultResource 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource appToStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, webAppName, storageAccountName, 'storage-blob-data-contributor')
  scope: storageAccountResource
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleId
    principalId: appService.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

resource appToKeyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, webAppName, keyVaultName, 'key-vault-secrets-user')
  scope: keyVaultResource
  properties: {
    roleDefinitionId: keyVaultSecretsUserRoleId
    principalId: appService.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

output webAppName string = appService.outputs.webAppName
output webAppUrl string = appService.outputs.webAppUrl
output appServicePlanName string = appService.outputs.appServicePlanName
output storageAccountName string = storage.outputs.storageAccountName
output postgresServerName string = postgres.outputs.serverName
output keyVaultName string = keyVault.outputs.keyVaultName
output applicationInsightsName string = monitoring.outputs.appInsightsName

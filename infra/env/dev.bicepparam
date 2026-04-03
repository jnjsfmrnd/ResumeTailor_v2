using '../main.bicep'

param environmentName = 'dev'
param location = 'eastus'
param projectName = 'resumetailor'

param tags = {
  environment: 'dev'
  workload: 'resumetailor'
  managedBy: 'bicep'
}

param appServicePlanSkuName = 'B1'
param postgresSkuName = 'Standard_B1ms'
param postgresStorageMb = 32768
param postgresVersion = '16'
param postgresDatabaseName = 'resumetailor'
param postgresAdminLogin = 'pgadminrt'
param storageAccountName = 'resumetailordevst'
param storageSkuName = 'Standard_LRS'
param blobContainerName = 'resumetailor-artifacts'
param linuxFxVersion = 'PYTHON|3.12'
param startupCommand = 'bash startup.sh'
param keyVaultEnablePurgeProtection = true
param keyVaultName = 'resumetailordevkv'
param githubModelsEndpoint = 'https://models.inference.ai.azure.com'
param githubModelsModel = 'gpt-4.1-mini'

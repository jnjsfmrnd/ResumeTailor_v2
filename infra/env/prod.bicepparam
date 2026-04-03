using '../main.bicep'

param environmentName = 'prod'
param location = 'eastus'
param projectName = 'resumetailor'

param tags = {
  environment: 'prod'
  workload: 'resumetailor'
  managedBy: 'bicep'
}

param appServicePlanSkuName = 'P1v3'
param postgresSkuName = 'Standard_D2ds_v4'
param postgresStorageMb = 65536
param postgresVersion = '16'
param postgresDatabaseName = 'resumetailor'
param postgresAdminLogin = 'pgadminrt'
param storageAccountName = 'resumetailorprodst'
param storageSkuName = 'Standard_LRS'
param blobContainerName = 'resumetailor-artifacts'
param linuxFxVersion = 'PYTHON|3.12'
param startupCommand = 'bash startup.sh'
param keyVaultEnablePurgeProtection = true
param keyVaultName = 'resumetailorprodkv'
param githubModelsEndpoint = 'https://models.inference.ai.azure.com'
param githubModelsModel = 'gpt-4.1-mini'

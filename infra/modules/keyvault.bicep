@description('Azure region for the Key Vault.')
param location string

@description('Key Vault name, 3-24 characters.')
param keyVaultName string

@description('Enable purge protection for production safety.')
param enablePurgeProtection bool = true

@secure()
@description('Django secret key value to store in Key Vault.')
param djangoSecretKey string

@secure()
@description('GitHub Models token to store in Key Vault.')
param githubModelsToken string

@secure()
@description('Database URL to store in Key Vault.')
param databaseUrl string

@description('Common tags applied to resources.')
param tags object = {}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    enablePurgeProtection: enablePurgeProtection
    publicNetworkAccess: 'Enabled'
    softDeleteRetentionInDays: 90
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

resource djangoSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'django-secret-key'
  properties: {
    value: djangoSecretKey
  }
}

resource githubModelsTokenSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'github-models-token'
  properties: {
    value: githubModelsToken
  }
}

resource databaseUrlSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'database-url'
  properties: {
    value: databaseUrl
  }
}

output keyVaultName string = keyVault.name
output keyVaultId string = keyVault.id
output vaultUri string = keyVault.properties.vaultUri
output djangoSecretKeySecretUri string = djangoSecret.properties.secretUriWithVersion
output githubModelsTokenSecretUri string = githubModelsTokenSecret.properties.secretUriWithVersion
output databaseUrlSecretUri string = databaseUrlSecret.properties.secretUriWithVersion

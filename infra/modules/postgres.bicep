@description('Azure region for PostgreSQL flexible server.')
param location string

@description('PostgreSQL flexible server name.')
param serverName string

@description('Application database name.')
param databaseName string

@description('PostgreSQL admin login username.')
param adminLogin string

@secure()
@description('PostgreSQL admin login password.')
param adminPassword string

@description('Flexible server SKU name.')
param skuName string = 'Standard_B1ms'

@description('Storage size in MB.')
param storageMb int = 32768

@description('PostgreSQL major version.')
param postgresVersion string = '16'

@description('Common tags applied to resources.')
param tags object = {}

// Standard_B* → Burstable, Standard_E* → MemoryOptimized, Standard_D* → GeneralPurpose
var skuTier = contains(toLower(skuName), '_b') ? 'Burstable'
            : contains(toLower(skuName), '_e') ? 'MemoryOptimized'
            : 'GeneralPurpose'

resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: serverName
  location: location
  tags: tags
  sku: {
    name: skuName
    tier: skuTier
  }
  properties: {
    administratorLogin: adminLogin
    administratorLoginPassword: adminPassword
    version: postgresVersion
    storage: {
      storageSizeGB: int(storageMb / 1024)
      autoGrow: 'Enabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
    maintenanceWindow: {
      customWindow: 'Disabled'
      dayOfWeek: 0
      startHour: 0
      startMinute: 0
    }
    dataEncryption: {
      type: 'SystemManaged'
    }
    authConfig: {
      activeDirectoryAuth: 'Disabled'
      passwordAuth: 'Enabled'
    }
  }
}

resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  parent: postgresServer
  name: databaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

resource allowAzureServicesFirewall 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-12-01-preview' = {
  parent: postgresServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

output serverName string = postgresServer.name
output fqdn string = postgresServer.properties.fullyQualifiedDomainName
output databaseName string = postgresDatabase.name
output serverId string = postgresServer.id

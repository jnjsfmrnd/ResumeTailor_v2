@description('Azure region for the Application Insights component.')
param location string

@description('Application Insights name.')
param appInsightsName string

@description('Common tags applied to resources.')
param tags object = {}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    IngestionMode: 'ApplicationInsights'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

output appInsightsName string = appInsights.name
output connectionString string = appInsights.properties.ConnectionString
output instrumentationKey string = appInsights.properties.InstrumentationKey
output appInsightsId string = appInsights.id

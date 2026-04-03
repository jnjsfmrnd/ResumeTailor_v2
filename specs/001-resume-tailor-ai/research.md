# Phase 0 Research

## Decision 1: Use a Django monolith for the full-stack application

- **Decision**: Implement the product as a server-rendered Django 5.x monolith with Django templates and small progressive-enhancement endpoints instead of splitting frontend and backend into separate applications.
- **Rationale**: The user explicitly wants a Django full-stack application. A monolith keeps authentication/session handling, document upload, AI orchestration, review UI, and PDF generation in one deployable unit and is the smallest acceptable design for a greenfield MVP.
- **Alternatives considered**:
  - React SPA plus Django API: rejected because it adds a second build system and deployment target without improving the MVP requirements.
  - Django plus a separate dedicated worker service: rejected for initial delivery because the clarified performance budget can be met first with synchronous orchestration plus careful request sizing and instrumentation.

## Decision 2: Deploy on Azure App Service with PostgreSQL, Blob Storage, Key Vault, and Application Insights

- **Decision**: Target Azure App Service on Linux for the Django web app, Azure Database for PostgreSQL Flexible Server for relational persistence, Azure Blob Storage for uploaded source files and generated artifacts, Azure Key Vault for secrets, and Application Insights for telemetry.
- **Rationale**: Azure’s official Django guidance centers on App Service with PostgreSQL, production Django settings, WhiteNoise, and Key Vault-backed app settings. Blob Storage is required because App Service local storage is not durable for persisted uploads. Key Vault is the right place for the Django secret and GitHub Models PAT.
- **Alternatives considered**:
  - Azure Container Apps: rejected because the application does not require container orchestration or event-driven scale at MVP scope.
  - AKS: rejected because cluster operations would add unnecessary complexity for a single web application.
  - Storing uploaded PDFs inside PostgreSQL: rejected because binary artifacts are better handled in blob storage, with metadata in PostgreSQL.

## Decision 3: Store only the latest uploaded resume as the active source artifact

- **Decision**: Persist one active uploaded resume per workspace/session, keep it in Blob Storage, and expose the active filename and status in the UI.
- **Rationale**: This matches the clarified spec and keeps persistence lightweight while still surviving refreshes and redeploys. Metadata in PostgreSQL plus blob references gives the app a durable pointer to the active source document.
- **Alternatives considered**:
  - No persistence: rejected because the clarified requirement explicitly asks to save the latest upload and show which PDF is in use.
  - Multi-document history library: rejected because the spec explicitly limits v1 to the latest active upload rather than a full document archive.

## Decision 4: Use GitHub Models through a server-side PAT stored in Key Vault

- **Decision**: Integrate AI generation from the Django backend using the GitHub Models API with a GitHub personal access token scoped to `models:read`, stored in Azure Key Vault and surfaced to App Service via Key Vault references.
- **Rationale**: Official GitHub Models documentation states that API access uses a GitHub personal access token with `models:read`. Because GitHub Models is not an Azure resource, managed identity cannot replace the GitHub token; the secure path is to store the PAT in Key Vault and never expose it to the browser or source control.
- **Alternatives considered**:
  - Calling the model directly from the browser: rejected because it would expose the PAT.
  - Embedding the PAT in GitHub Actions only: rejected because the running application still needs a runtime credential.
  - Switching to Azure OpenAI now: rejected because the user specifically wants GitHub Copilot / GitHub model token-based access.

## Decision 5: Use GitHub Actions with Azure OIDC and Bicep-based deployments

- **Decision**: Create separate GitHub Actions workflows for CI and CD. CI will run Ruff, pytest, contract checks, and browser smoke coverage. CD will authenticate to Azure using GitHub OIDC, validate Bicep with `what-if`, deploy infrastructure from `infra/`, then deploy the Django app to App Service.
- **Rationale**: GitHub Actions is the requested CI/CD platform. Azure best practices favor IaC over ad hoc scripts and service-principal/OIDC based deployment credentials over long-lived secrets. Bicep under `infra/` aligns with both Azure guidance and the repository planning rules.
- **Alternatives considered**:
  - Publish profile deployment: rejected because it relies on long-lived secrets and weaker credential hygiene than OIDC.
  - Manual Azure CLI deployment only: rejected because the user explicitly wants GitHub Actions CI/CD.
  - azd-managed deployment: rejected for the initial implementation plan because the user specifically requested Bicep IaC and GitHub Actions as first-class artifacts.

## Decision 6: Use production-safe Django settings for Azure App Service

- **Decision**: Use WhiteNoise for static files, configure `ALLOWED_HOSTS` from `WEBSITE_HOSTNAME`, separate `base/dev/prod` settings, and keep uploads in blob storage instead of local media in production.
- **Rationale**: Azure’s official Django guidance calls out `WEBSITE_HOSTNAME` handling and WhiteNoise as standard production configuration for Django on App Service.
- **Alternatives considered**:
  - Serving all media and static files from App Service disk: rejected because static and uploaded content need reliable production behavior across app restarts and scale-out.
  - Using Django default single-file settings module: rejected because environment separation for Azure deployment, local development, and CI is clearer and safer with split settings.

## Decision 7: Use a minimalist GameCube-inspired design system for the web UI

- **Decision**: Apply a minimalist GameCube-inspired visual system to the interactive web application, using indigo-led branding, spice-orange CTAs, platinum-grey surfaces, geometric display typography, rounded industrial cards, circular vent-inspired patterns, and tactile glossy control feedback.
- **Rationale**: The user supplied a concrete aesthetic direction. Encoding it now prevents the frontend from defaulting to generic dashboard styling and gives implementation a specific visual target for layout, components, and interaction states.
- **Alternatives considered**:
  - Default neutral SaaS styling: rejected because it would lose the project’s intended identity.
  - Applying the same visual styling to exported resumes: rejected because submission artifacts must stay ATS-friendly and plain.

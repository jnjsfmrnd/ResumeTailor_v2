# Quickstart

## Goal

Run the Django full-stack application locally, validate the test suite, provision Azure infrastructure with Bicep, and configure GitHub Actions for CI/CD deployment to Azure App Service.

## 1. Local development prerequisites

- Python 3.12
- PostgreSQL 16 or a compatible local Postgres instance
- Node.js 20+ for Playwright browser automation
- Azure CLI for infrastructure validation and deployment
- A GitHub personal access token with `models:read` for GitHub Models API access

## 2. Local environment setup

1. Create and activate a virtual environment inside `repo/`.
2. Install application and development dependencies from `repo/requirements/dev.txt`.
3. Create `repo/.env` from `repo/.env.example` with at least:
   - `DJANGO_SETTINGS_MODULE=resumetailor.settings.dev`
   - `DJANGO_SECRET_KEY=<local-dev-secret>`
   - `DATABASE_URL=postgresql://...`
   - `GITHUB_MODELS_TOKEN=<pat-with-models-read>`
   - `GITHUB_MODELS_ENDPOINT=https://models.inference.ai.azure.com`
   - `GITHUB_MODELS_MODEL=<selected-model>`
   - `USE_LOCAL_FILE_STORAGE=true`
4. Run database migrations.
5. Start the Django development server from `repo/`.

## 3. Local validation workflow

From `repo/`, run:

1. `ruff check .`
2. `ruff format --check .`
3. `python manage.py check`
4. `pytest`
5. `playwright install --with-deps`
6. `playwright test`

## 4. Azure infrastructure layout

Planned Azure resources in `infra/`:

1. App Service Plan (Linux)
2. Azure App Service for Django
3. Azure Database for PostgreSQL Flexible Server
4. Azure Storage Account with Blob container for uploads/artifacts
5. Azure Key Vault for Django and GitHub Models secrets
6. Application Insights

Production notes:

1. App Service uses Key Vault references for runtime secrets.
2. PostgreSQL connection and Django `SECRET_KEY` are not committed to the repo.
3. Uploaded files and generated outputs are stored in Blob Storage, not on App Service disk.
4. Django production settings should derive `ALLOWED_HOSTS` from `WEBSITE_HOSTNAME` and serve static assets with WhiteNoise.

## 5. Bicep validation and deployment

1. Author resource group-scoped Bicep files under `infra/`.
2. Keep environment-specific values in `infra/env/*.bicepparam`.
3. Validate infrastructure before deployment using `what-if`.
4. Deploy infrastructure from GitHub Actions or locally with Azure CLI after validation.

Suggested validation flow:

1. `az login`
2. `az account set --subscription <subscription-id>`
3. `az deployment group what-if --resource-group <rg> --template-file infra/main.bicep --parameters infra/env/dev.bicepparam`

For secured validation in this project, include secure parameters explicitly:

4. `az deployment group what-if --resource-group <rg> --template-file infra/main.bicep --parameters infra/env/dev.bicepparam --parameters postgresAdminPassword=<...> djangoSecretKey=<...> githubModelsToken=<...>`

## 6. GitHub Actions CI/CD setup

### CI workflow

The CI workflow should run on pull requests and pushes to the main integration branch and must:

1. Set up Python 3.12
2. Install dependencies
3. Run Ruff
4. Run Django checks
5. Run pytest
6. Run Playwright smoke coverage

### Deployment workflow

The deployment workflow should:

1. Authenticate to Azure using GitHub OIDC, not a publish profile
2. Run Bicep validation (`what-if`) before deploy
3. Deploy or update Azure infrastructure
4. Deploy the Django app to App Service
5. Run post-deploy health checks

Required GitHub repository or environment secrets/configuration:

1. `AZURE_CLIENT_ID`
2. `AZURE_TENANT_ID`
3. `AZURE_SUBSCRIPTION_ID`
4. `AZURE_RESOURCE_GROUP`
5. `AZURE_ENVIRONMENT` (`dev` or `prod`)
6. `POSTGRES_ADMIN_PASSWORD`
7. `DJANGO_SECRET_KEY`
8. `GITHUB_MODELS_TOKEN`

The GitHub Models PAT should live in Azure Key Vault for runtime app usage. It should not be duplicated into CI unless a build-time operation explicitly requires it.

The deployment workflow validates Bicep with `what-if`, deploys infra, zips `repo/`, and deploys the app package to App Service. It also sets startup command to `bash startup.sh` via Bicep parameters.

## 6.5 Runtime environment contract

Expected App Service runtime settings:

1. `DJANGO_SETTINGS_MODULE=resumetailor.settings.prod`
2. `USE_LOCAL_FILE_STORAGE=false`
3. `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_STORAGE_CONTAINER_NAME`, `AZURE_BLOB_ENDPOINT`
4. `APPLICATIONINSIGHTS_CONNECTION_STRING`
5. `GITHUB_MODELS_ENDPOINT`, `GITHUB_MODELS_MODEL`
6. `DJANGO_SECRET_KEY`, `DATABASE_URL`, and `GITHUB_MODELS_TOKEN` as Key Vault references

## 7. First production smoke test

After deployment:

1. Open the App Service URL
2. Upload a PDF resume and confirm the UI displays the active source file name
3. Paste a job description and generate a tailored draft
4. Edit the generated content
5. Generate the resume PDF separately
6. Generate the cover letter separately
7. Confirm artifacts are downloadable and the latest upload remains visible as the active source document
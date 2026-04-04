# ResumeTailor

ResumeTailor is a Django monolith for AI-assisted resume tailoring with a GameCube-inspired review interface and ATS-friendly export outputs.

## Local setup

1. Create a Python 3.12 virtual environment in `repo/`.
2. Install dependencies from `requirements/dev.txt`.
3. Copy `.env.example` to `.env` and fill in the required values.
	For local development, you can leave `GITHUB_MODELS_TOKEN` empty and keep
	`GITHUB_MODELS_ENABLE_DEV_FALLBACK=true` to generate a deterministic mock draft.
	Production must still provide a real `GITHUB_MODELS_TOKEN`.
4. Run `python manage.py migrate`.
5. Run `python manage.py runserver`.

## Validation

- `ruff check .`
- `python manage.py check`
- `pytest`
- `npm install`
- `npx playwright install --with-deps chromium`
- `npm run test:e2e`

## Azure deployment

Infrastructure and deployment automation live in `infra/` and `.github/workflows/deploy.yml`.

### Required GitHub secrets

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP`
- `AZURE_ENVIRONMENT` (`dev` or `prod`)
- `POSTGRES_ADMIN_PASSWORD`
- `DJANGO_SECRET_KEY`
- `GITHUB_MODELS_TOKEN`

### Runtime env vars on App Service

The deploy pipeline configures these app settings:

- `DJANGO_SETTINGS_MODULE=resumetailor.settings.prod`
- `USE_LOCAL_FILE_STORAGE=false`
- `AZURE_STORAGE_ACCOUNT_NAME`
- `AZURE_STORAGE_CONTAINER_NAME`
- `AZURE_BLOB_ENDPOINT`
- `GITHUB_MODELS_ENDPOINT`
- `GITHUB_MODELS_MODEL`
- `APPLICATIONINSIGHTS_CONNECTION_STRING`

These three are configured as Key Vault references (not plain text values):

- `DJANGO_SECRET_KEY`
- `DATABASE_URL`
- `GITHUB_MODELS_TOKEN`

### Deployment validation

1. Run `az bicep build --file infra/main.bicep`.
2. Run `az deployment group what-if --resource-group <rg> --template-file infra/main.bicep --parameters infra/env/dev.bicepparam --parameters postgresAdminPassword=<...> djangoSecretKey=<...> githubModelsToken=<...>`.
3. Trigger `.github/workflows/deploy.yml` with `environment=dev`.
4. Verify health endpoint `/` returns 200 from the deployed hostname.
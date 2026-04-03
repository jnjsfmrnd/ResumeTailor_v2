# Implementation Plan: AI Resume Tailoring Workflow

**Branch**: `[001-resume-tailor-ai]` | **Date**: 2026-04-03 | **Spec**: `/specs/001-resume-tailor-ai/spec.md`
**Input**: Feature specification from `/specs/001-resume-tailor-ai/spec.md`

## Summary

Build a greenfield Django full-stack application that lets a user upload a resume, paste a job description, generate truthful AI-tailored resume and cover-letter outputs, review and edit the generated content, and export an ATS-compatible resume PDF. The interactive web experience will follow a minimalist GameCube-inspired design system with indigo-led branding, tactile controls, and industrial rounded geometry. The application will be deployed to Azure App Service on Linux using Bicep IaC under `infra/`, with Azure Database for PostgreSQL Flexible Server for relational data, Azure Blob Storage for persisted source files and generated artifacts, Azure Key Vault for secrets including the GitHub Models PAT, and GitHub Actions for CI/CD using Azure OIDC authentication.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Django 5.x, Gunicorn, psycopg[binary], WhiteNoise, django-storages, azure-storage-blob, httpx, pypdf/python-docx for document parsing, WeasyPrint or reportlab-compatible PDF generation, pytest, pytest-django, Playwright, Ruff  
**Storage**: Azure Database for PostgreSQL Flexible Server for relational data; Azure Blob Storage for latest uploaded resume and generated artifacts; local filesystem fallback for development only  
**Testing**: pytest, pytest-django, Django test client integration tests, API contract validation, Playwright smoke coverage, Ruff lint/format checks, `python manage.py check --deploy` for production configuration validation  
**Target Platform**: Azure App Service Linux (web), Azure Database for PostgreSQL Flexible Server, Azure Blob Storage, Azure Key Vault, GitHub Actions Linux runners  
**Project Type**: Server-rendered full-stack web application with internal JSON endpoints  
**Performance Goals**: First tailored draft available within 90 seconds for 95% of successful runs; resume PDF export within 30 seconds for 95% of successful runs; cover-letter generation completes within the same 90-second draft budget when requested separately  
**Constraints**: No unsupported claims in generated outputs; latest uploaded resume is the active persisted source; resume and cover letter are generated separately; GitHub Models PAT must have `models:read` and be stored as a secret, not committed; App Service local disk is not used for durable uploads; Azure infra must be authored in Bicep under `infra/`; the product UI must follow the approved minimalist GameCube-inspired design guide while exported documents remain plain and ATS-friendly  
**Scale/Scope**: MVP for individual job seekers, single-region Azure deployment, low-hundreds of daily sessions, one active source document per anonymous workspace/session, separate CI and deployment workflows in GitHub Actions

## Constitution Check

*GATE: Passes before Phase 0 research. Re-checked after Phase 1 design and still passes.*

- **Code Quality**: Planned modules are bounded into `repo/apps/intake` for upload and parsing, `repo/apps/tailoring` for orchestration and review state, `repo/apps/ai` for GitHub Models integration and prompt policy, `repo/apps/outputs` for resume/cover-letter/PDF generation, `repo/apps/common` for shared utilities, plus `infra/` for Bicep and `.github/workflows/` for CI/CD. Validation path will use Ruff for lint and formatting checks, `python manage.py check`, and deployment-safe settings separation for local vs production.
- **Testing**: Implementation must add fail-first then pass-after tests for document parsing, truthfulness guards, skill-gap/project recommendation formatting, resume export, cover-letter generation, and the upload-to-review flow. Integration coverage will use pytest-django for server-side flows and contract tests for the JSON endpoints documented in `contracts/`. A Playwright smoke test will exercise the browser flow for upload, draft review, and separate artifact generation.
- **UX Consistency**: Because the repository is greenfield, the plan standardizes on one Django-rendered shell, shared form/error/message components, consistent loading and empty states, and a visible “current source PDF” indicator. The visual system will implement the approved GameCube-inspired guide consistently through indigo primary surfaces, spice-orange CTA emphasis, platinum-grey cards, geometric display typography, rounded industrial shapes, circular vent-inspired background detailing, and tactile glossy button states. No separate SPA is introduced; incremental interactivity stays within the same UI pattern to avoid split UX systems.
- **Performance**: Budgets follow the spec: 90 seconds for initial tailored draft, 30 seconds for resume PDF export. Measurement will use request/job timing logs, integration assertions around generation latency boundaries, and Azure Application Insights after deployment. If the synchronous generation path threatens the budget, the first mitigation is reducing prompt/output size and caching extracted document structure; background worker extraction is explicitly deferred unless measurements justify the added complexity.
- **Decision Evidence**: Simpler alternatives were considered and rejected: storing uploads on App Service disk was rejected because storage is not durable across instances; a React SPA plus API split was rejected because a Django monolith is the smallest acceptable full-stack design; Azure Container Apps or AKS were rejected because App Service is the simpler production fit for Django on Azure; bundling resume and cover-letter generation was rejected because the clarified spec requires separate user-selectable outputs.

## Project Structure

### Documentation (this feature)

```text
specs/001-resume-tailor-ai/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── resume-tailoring-api.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
repo/
├── manage.py
├── pyproject.toml
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── .env.example
├── resumetailor/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── common/
│   ├── intake/
│   ├── tailoring/
│   ├── ai/
│   └── outputs/
├── templates/
├── static/
└── tests/
    ├── contract/
    ├── integration/
    ├── unit/
    └── e2e/

infra/
├── main.bicep
├── modules/
└── env/
    ├── dev.bicepparam
    └── prod.bicepparam

.github/
└── workflows/
    ├── ci.yml
    └── deploy.yml
```

**Structure Decision**: Use a Django monolith rooted in `repo/` with app modules separated by business responsibility, while keeping infrastructure in `infra/` per Azure IaC guidance and deployment automation in `.github/workflows/`. Centralize theme tokens, icon styles, and reusable tactile UI components within the Django app so the GameCube-inspired interface remains coherent across upload, review, and generation surfaces. This is the smallest structure that supports full-stack delivery, Azure deployment, and CI/CD without introducing a second application runtime.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |


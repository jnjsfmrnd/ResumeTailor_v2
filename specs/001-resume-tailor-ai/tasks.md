# Tasks: AI Resume Tailoring Workflow

**Input**: Design documents from `/specs/001-resume-tailor-ai/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/resume-tailoring-api.openapi.yaml, quickstart.md

**Tests**: Automated tests are REQUIRED for each user story and bug fix unless an approved exception is documented with fallback manual validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. Parallelizable tasks are marked `[P]` and are split across lane-owned modules, partial templates, and component styles to minimize file conflicts.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the Django monolith, quality tooling, and baseline project layout.

- [X] T001 Create the Django monolith scaffold and dependency manifests in repo/manage.py, repo/pyproject.toml, repo/requirements/base.txt, repo/requirements/dev.txt, repo/requirements/prod.txt
- [X] T002 [P] Configure Ruff, pytest, and Playwright baseline settings in repo/pyproject.toml, repo/pytest.ini, repo/package.json, repo/playwright.config.ts
- [X] T003 [P] Create environment templates and local bootstrap files in repo/.env.example, repo/.gitignore, repo/README.md
- [X] T004 [P] Create base Django settings and app package structure in repo/resumetailor/settings/base.py, repo/resumetailor/settings/dev.py, repo/resumetailor/settings/prod.py, repo/apps/common/__init__.py, repo/apps/intake/__init__.py, repo/apps/tailoring/__init__.py, repo/apps/ai/__init__.py, repo/apps/outputs/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the smallest shared foundation that all story lanes depend on.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [X] T005 Create shared workspace, source document, job target, and tailoring run models with initial migrations in repo/apps/common/models.py, repo/apps/intake/models.py, repo/apps/tailoring/models.py, repo/apps/common/migrations/, repo/apps/intake/migrations/, repo/apps/tailoring/migrations/
- [X] T006 [P] Implement durable storage abstractions for local development and Azure Blob storage in repo/apps/intake/storage.py, repo/apps/intake/repositories.py, repo/resumetailor/settings/base.py
- [X] T007 [P] Implement resume parsing and normalization services for PDF, DOC, and DOCX in repo/apps/intake/parsers.py, repo/apps/intake/services.py
- [X] T008 [P] Implement the GitHub Models client, prompt policy, and retry/error handling in repo/apps/ai/client.py, repo/apps/ai/prompts.py, repo/apps/ai/services.py
- [X] T009 Implement the shared GameCube-inspired app shell, theme tokens, tactile interaction primitives, and component-style contract layout in repo/templates/base.html, repo/templates/components/layout_shell.html, repo/static/css/theme.css, repo/static/css/components/, repo/static/js/app.js
- [X] T010 Implement shared routing, session bootstrap, current-workspace endpoint, and common error handling in repo/resumetailor/urls.py, repo/apps/common/views.py, repo/apps/common/urls.py, repo/apps/common/forms.py
- [X] T011 [P] Implement shared logging, timing metrics, and performance instrumentation in repo/apps/common/logging.py, repo/apps/common/metrics.py, repo/resumetailor/settings/prod.py
- [X] T012 [P] Implement the baseline CI workflow for lint, checks, unit/integration tests, and browser smoke setup in .github/workflows/ci.yml

**Checkpoint**: Foundation ready. Story lanes can now proceed in parallel.

---

## Phase 3: User Story 1 - Tailor Resume For A Target Role (Priority: P1) 🎯 MVP

**Goal**: Let a user upload a resume, paste a job description, generate a truthful tailored draft, edit it, and see the currently active source document in the UI.

**Independent Test**: Upload a supported resume, paste a job description, generate a reviewable draft, manually edit it, and confirm the active source filename and core UI states are visible without unsupported claims.

### Tests for User Story 1 ⚠️

- [X] T013 [P] [US1] Create contract tests for current workspace and upload endpoints in repo/tests/contract/test_workspace_api.py
- [X] T014 [P] [US1] Create contract tests for job target creation and tailoring start endpoints in repo/tests/contract/test_tailoring_start_api.py
- [X] T015 [P] [US1] Create integration test for the upload-to-review draft flow in repo/tests/integration/test_resume_tailoring_flow.py
- [X] T016 [P] [US1] Create unit tests for document parsing and truthfulness guard behavior in repo/tests/unit/test_document_parsing.py, repo/tests/unit/test_truthfulness_guard.py

### Implementation for User Story 1

- [X] T017 [US1] Implement upload and active-source document forms, views, and templates in repo/apps/intake/forms.py, repo/apps/intake/views.py, repo/templates/intake/upload.html
- [X] T018 [US1] Implement job description capture and current-source UI badge rendering in repo/apps/intake/views.py, repo/templates/intake/job_target.html, repo/templates/components/current_source_badge.html
- [X] T019 [US1] Implement draft orchestration for summary, skills, and experience rewriting in repo/apps/tailoring/draft_service.py, repo/apps/ai/prompts.py
- [X] T020 [US1] Implement source-grounding and unsupported-claim validation in repo/apps/tailoring/validators.py, repo/apps/tailoring/draft_service.py
- [X] T021 [US1] Implement MVP review retrieval and manual-edit save flows in repo/apps/tailoring/review_views.py, repo/apps/tailoring/review_urls.py, repo/templates/tailoring/review.html, repo/templates/tailoring/partials/review_core_panel.html
- [X] T022 [US1] Verify themed loading, empty, error, success, and active-source states plus the 90-second draft budget for the MVP flow in repo/templates/components/loading_disc.html, repo/templates/components/empty_state.html, repo/static/css/components/review_core.css, repo/tests/integration/test_resume_tailoring_flow.py

**Checkpoint**: User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Understand Gaps And Add Relevant Project Experience (Priority: P2)

**Goal**: Show missing requirements, map transferable skills, recommend a gap-closing micro-project, and let the user include or exclude generated project bullets.

**Independent Test**: Starting from a reviewable tailoring run, inspect the skill-gap panel, verify transferable-skill mapping, review generated project bullets, and save inclusion or exclusion choices successfully.

### Tests for User Story 2 ⚠️

- [X] T023 [P] [US2] Create unit tests for skill-gap classification and transferable-skill mapping in repo/tests/unit/test_skill_gap_analysis.py
- [X] T024 [P] [US2] Create unit tests for project recommendation and bullet proposal formatting in repo/tests/unit/test_project_recommendations.py
- [X] T025 [P] [US2] Create contract tests for tailoring detail retrieval and review-update payloads in repo/tests/contract/test_tailoring_review_api.py
- [X] T026 [P] [US2] Create integration test for gap analysis and project inclusion decisions in repo/tests/integration/test_skill_gap_review_flow.py

### Implementation for User Story 2

- [X] T027 [P] [US2] Create skill-gap, project recommendation, and project bullet proposal models with migrations in repo/apps/tailoring/models.py, repo/apps/tailoring/migrations/
- [X] T028 [US2] Implement skill-gap analysis and transferable-skill mapping services in repo/apps/tailoring/gap_analysis.py, repo/apps/tailoring/gap_service.py
- [X] T029 [US2] Implement micro-project recommendation and bullet proposal generation in repo/apps/tailoring/recommendations.py, repo/apps/tailoring/gap_service.py
- [X] T030 [US2] Implement project include/exclude handlers and gap-review composition in repo/apps/tailoring/gap_review_views.py, repo/apps/tailoring/gap_review_urls.py, repo/templates/tailoring/partials/review_gap_panel.html
- [X] T031 [US2] Implement GameCube-styled gap-analysis and project recommendation components in repo/templates/components/gap_panel.html, repo/templates/components/project_card.html, repo/static/css/components/gap_panel.css
- [X] T032 [US2] Verify latency, validation, empty-state, and error-state behavior for gap analysis and project review in repo/apps/common/metrics.py, repo/tests/integration/test_skill_gap_review_flow.py

**Checkpoint**: User Stories 1 and 2 work independently, and US2 adds reviewable gap/project intelligence without breaking US1.

---

## Phase 5: User Story 3 - Generate Separate Application Outputs (Priority: P3)

**Goal**: Generate a resume PDF and a cover letter as separate user-selectable outputs from the approved tailoring run.

**Independent Test**: From a reviewed tailoring run, generate the resume PDF alone, generate the cover letter alone, and confirm each output is downloadable and audited separately.

### Tests for User Story 3 ⚠️

- [X] T033 [P] [US3] Create unit tests for resume PDF composition and cover-letter generation in repo/tests/unit/test_resume_export.py, repo/tests/unit/test_cover_letter_generation.py
- [X] T034 [P] [US3] Create contract tests for resume and cover-letter artifact endpoints in repo/tests/contract/test_artifact_api.py
- [X] T035 [P] [US3] Create integration test for separate artifact generation flows in repo/tests/integration/test_artifact_generation_flow.py
- [X] T036 [P] [US3] Create Playwright smoke coverage for separate resume and cover-letter actions in repo/tests/e2e/test_generation_actions.py

### Implementation for User Story 3

- [X] T037 [P] [US3] Create cover-letter draft and generated-artifact models with migrations in repo/apps/outputs/models.py, repo/apps/outputs/migrations/
- [X] T038 [US3] Implement ATS-safe resume PDF composition and artifact persistence in repo/apps/outputs/resume_service.py, repo/apps/outputs/pdf_templates/, repo/apps/outputs/services.py
- [X] T039 [US3] Implement separate cover-letter generation and templating in repo/apps/outputs/cover_letter_service.py, repo/templates/outputs/cover_letter.html
- [X] T040 [US3] Implement artifact generation endpoints, download views, and separate action controls in repo/apps/outputs/views.py, repo/apps/outputs/urls.py, repo/templates/components/export_actions.html, repo/templates/tailoring/partials/review_export_panel.html
- [X] T041 [US3] Enforce export approval rules and artifact audit metadata in repo/apps/outputs/policies.py, repo/apps/outputs/services.py
- [X] T042 [US3] Verify themed generation, empty-artifact, error, and success states plus the 30-second resume export budget, ATS-safe export behavior, and first-attempt cover-letter success path in repo/static/css/components/export_actions.css, repo/templates/components/loading_disc.html, repo/templates/components/empty_state.html, repo/tests/integration/test_artifact_generation_flow.py
- [X] T043 [US3] Verify cover-letter generation latency stays within the 90-second performance budget for successful runs in repo/apps/common/metrics.py, repo/tests/integration/test_artifact_generation_flow.py

**Checkpoint**: All user stories are independently functional and the user can generate resume and cover-letter outputs separately.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Delivery, infrastructure, and whole-system quality work that spans multiple stories.

- [X] T044 [P] Implement Azure App Service, PostgreSQL, Blob Storage, Key Vault, and Application Insights Bicep modules in infra/main.bicep, infra/modules/appservice.bicep, infra/modules/postgres.bicep, infra/modules/storage.bicep, infra/modules/keyvault.bicep, infra/modules/monitoring.bicep, infra/env/dev.bicepparam, infra/env/prod.bicepparam
- [X] T045 [P] Implement GitHub Actions deployment workflow with Azure OIDC and Bicep what-if validation in .github/workflows/deploy.yml
- [X] T046 [P] Implement production startup and deployment settings for App Service in repo/startup.sh, repo/resumetailor/settings/prod.py, repo/requirements/prod.txt
- [X] T047 Run quickstart validation and update onboarding/deployment instructions in repo/README.md, specs/001-resume-tailor-ai/quickstart.md
- [X] T048 Perform final UX consistency, security, and performance audit across app and deployment surfaces in repo/templates/base.html, repo/static/css/theme.css, repo/tests/e2e/test_generation_actions.py, infra/main.bicep, .github/workflows/ci.yml, .github/workflows/deploy.yml

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all story lanes.
- **User Stories (Phases 3-5)**: Depend on Foundational completion.
- **Polish & Cross-Cutting (Phase 6)**: Depends on the relevant story contracts being stable; T044-T046 can begin once Phase 2 is complete, while T047-T048 should wait until the desired stories are finished.

### User Story Dependencies

- **User Story 1 (P1)**: Starts immediately after Phase 2 and delivers the MVP.
- **User Story 2 (P2)**: Starts after Phase 2 and builds on the shared tailoring run foundation, not on completed US1 implementation.
- **User Story 3 (P3)**: Starts after Phase 2 and depends on approved tailoring-run data structures, not on US2 completion.

### Within Each User Story

- Tests must be written and fail before implementation.
- Shared or story-specific models come before orchestration services.
- Services come before views/endpoints and templates.
- UI state verification and performance checks complete the story.

### Parallel Opportunities

- `T002`, `T003`, and `T004` can run in parallel during setup.
- `T006`, `T007`, `T008`, `T011`, and `T012` can run in parallel once `T005` starts defining the shared data model.
- After Phase 2, story lanes `US1`, `US2`, and `US3` can proceed in parallel because review logic, review partials, and component styles are split into lane-owned modules.
- `T044`, `T045`, and `T046` can run in a dedicated delivery lane in parallel with story work once the app structure and settings contracts from Phase 2 are in place.

---

## Parallel Agent Lanes

### Lane A: Platform Foundation

- T001-T012
- Recommended agent focus: project bootstrap, settings, storage, AI client, base shell, shared routing
- Exit condition: shared models, GitHub Models client, GameCube shell, and workspace bootstrap are all merged

### Lane B: Intake + Tailoring MVP

- T013-T022
- Recommended agent focus: upload, job description entry, tailored draft generation, truthfulness guard, review core panel, empty-state handling
- Minimal blockers: waits only for Phase 2 completion and owns `draft_service.py`, `review_views.py`, and `review_core_panel.html`

### Lane C: Gap Intelligence

- T023-T032
- Recommended agent focus: gap analysis, transferable-skill mapping, project recommendation logic, gap review panel
- Minimal blockers: waits only for Phase 2 completion and owns `gap_service.py`, `gap_review_views.py`, and `review_gap_panel.html`

### Lane D: Output Generation

- T033-T043
- Recommended agent focus: resume PDF, cover-letter generation, artifact persistence, separate output controls
- Minimal blockers: waits only for Phase 2 completion and owns `repo/apps/outputs/*`, `review_export_panel.html`, and export component styles

### Lane E: Delivery + Azure

- T044-T048
- Recommended agent focus: Bicep IaC, GitHub Actions CI/CD, production startup config, quickstart validation
- Minimal blockers: can begin after Phase 2, then sync once runtime env vars and startup commands stabilize

---

## Parallel Example: Multiple Custom Agents

```text
Agent 1: T006, T007, T009, T010
Agent 2: T008, T011, T012
Agent 3: T013-T022 after Phase 2
Agent 4: T023-T032 after Phase 2
Agent 5: T033-T043 after Phase 2
Agent 6: T044-T046 after Phase 2, then T047-T048 near the end
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3.
4. Validate the upload-to-review flow before expanding further.

### Incremental Delivery

1. Ship US1 as the first usable milestone.
2. Add US2 in parallel if you want a second agent lane focused on intelligence and review UX.
3. Add US3 in parallel if you want a third lane focused on export artifacts.
4. Land Azure and CI/CD tasks continuously in the delivery lane once the shared settings contract is stable.

### Minimal-Blocker Rule Set

1. Do not let story lanes edit shared settings, shared routes, or shared theme tokens without an agreed contract owner.
2. Keep draft orchestration, gap intelligence, and output generation in separate lane-owned modules: `repo/apps/tailoring/draft_service.py`, `repo/apps/tailoring/gap_service.py`, and `repo/apps/outputs/services.py`.
3. Keep Azure/Bicep and GitHub Actions work isolated to `infra/` and `.github/workflows/` so delivery agents do not block feature agents.
4. Keep the review page compositional: `review.html` is the shell, while story lanes own `review_core_panel.html`, `review_gap_panel.html`, and `review_export_panel.html` separately.
5. Merge Phase 2 completely before starting story lanes; after that, prefer contract-driven coordination instead of shared-file concurrency.

---

## Notes

- `[P]` means the task can run in parallel without depending on incomplete work in the same phase.
- Story labels map tasks directly back to independently testable user stories.
- The best multi-agent cut is one shared foundation lane plus four parallel lanes: MVP, gap intelligence, outputs, and delivery.
- Exported resume and cover-letter artifacts remain ATS-friendly even though the application UI follows the GameCube-inspired design system.
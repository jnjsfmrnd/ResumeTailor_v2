# Data Model

## WorkspaceSession

- **Purpose**: Represents the active anonymous or lightweight user workspace that holds the latest upload, current job description, and latest tailoring state.
- **Fields**:
  - `id` (UUID)
  - `session_key` (string, unique)
  - `current_source_document_id` (FK to SourceDocument, nullable)
  - `current_job_target_id` (FK to JobTarget, nullable)
  - `created_at` (datetime)
  - `updated_at` (datetime)
  - `expires_at` (datetime)
- **Relationships**:
  - Has many SourceDocuments
  - Has many JobTargets
  - Has many TailoringRuns
- **Validation Rules**:
  - Only one source document may be marked current for a workspace at a time.
  - Expired sessions must not be reused for new write operations.

## SourceDocument

- **Purpose**: Stores metadata about the latest uploaded resume and its extracted text.
- **Fields**:
  - `id` (UUID)
  - `workspace_session_id` (FK)
  - `original_filename` (string)
  - `content_type` (enum: `application/pdf`, `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`)
  - `blob_path` (string)
  - `sha256` (string)
  - `extracted_text` (text)
  - `parse_status` (enum: `uploaded`, `processing`, `ready`, `failed`)
  - `parse_error` (text, nullable)
  - `is_current` (boolean)
  - `uploaded_at` (datetime)
- **Relationships**:
  - Belongs to WorkspaceSession
  - Referenced by TailoringRuns and GeneratedArtifacts
- **Validation Rules**:
  - Only supported file types are accepted.
  - `is_current=true` must be unique per workspace.
  - `extracted_text` is required when `parse_status=ready`.
- **State Transitions**:
  - `uploaded -> processing -> ready`
  - `uploaded -> processing -> failed`

## JobTarget

- **Purpose**: Holds the pasted job description and derived role signals.
- **Fields**:
  - `id` (UUID)
  - `workspace_session_id` (FK)
  - `company_name` (string, nullable)
  - `role_title` (string, nullable)
  - `description_text` (text)
  - `top_keywords` (JSON array)
  - `created_at` (datetime)
- **Relationships**:
  - Belongs to WorkspaceSession
  - Referenced by TailoringRuns and CoverLetterDrafts
- **Validation Rules**:
  - `description_text` cannot be empty.
  - Keyword extraction must preserve the original job description separately from generated summaries.

## TailoringRun

- **Purpose**: Represents a single AI-assisted drafting run for a source resume and job target pair.
- **Fields**:
  - `id` (UUID)
  - `workspace_session_id` (FK)
  - `source_document_id` (FK)
  - `job_target_id` (FK)
  - `status` (enum: `pending`, `processing`, `reviewable`, `failed`)
  - `professional_summary` (text)
  - `tailored_skills` (JSON array)
  - `tailored_experience_sections` (JSON array)
  - `truthfulness_notes` (JSON array)
  - `created_at` (datetime)
  - `updated_at` (datetime)
- **Relationships**:
  - Belongs to WorkspaceSession, SourceDocument, and JobTarget
  - Has one SkillGapAssessment
  - Has many ProjectRecommendations
  - Has many GeneratedArtifacts
- **Validation Rules**:
  - A run cannot become `reviewable` unless summary and section outputs are present.
  - The run must retain enough source references to audit unsupported claims.
- **State Transitions**:
  - `pending -> processing -> reviewable`
  - `pending -> processing -> failed`

## SkillGapAssessment

- **Purpose**: Captures missing requirements, transferable skills, and supporting evidence from the run.
- **Fields**:
  - `id` (UUID)
  - `tailoring_run_id` (FK, unique)
  - `missing_requirements` (JSON array)
  - `transferable_skills` (JSON array)
  - `coverage_summary` (text)
  - `generated_at` (datetime)
- **Relationships**:
  - Belongs to TailoringRun
- **Validation Rules**:
  - Each missing requirement entry must classify whether it is unsupported or partially transferable.

## ProjectRecommendation

- **Purpose**: Describes a suggested micro-project to close the highest-value skill gaps.
- **Fields**:
  - `id` (UUID)
  - `tailoring_run_id` (FK)
  - `title` (string)
  - `goal` (text)
  - `scope_markdown` (text)
  - `targeted_gaps` (JSON array)
  - `is_included` (boolean)
  - `created_at` (datetime)
- **Relationships**:
  - Belongs to TailoringRun
  - Has many ProjectBulletProposals
- **Validation Rules**:
  - At least one targeted gap must be recorded.
  - Inclusion defaults to false until the user approves it.

## ProjectBulletProposal

- **Purpose**: Stores generated resume bullet points for the recommended project, including user edits.
- **Fields**:
  - `id` (UUID)
  - `project_recommendation_id` (FK)
  - `sort_order` (integer)
  - `generated_text` (text)
  - `edited_text` (text, nullable)
  - `is_approved` (boolean)
- **Relationships**:
  - Belongs to ProjectRecommendation
- **Validation Rules**:
  - Export uses `edited_text` when present, otherwise `generated_text`.
  - Unapproved bullets are excluded from final resume export.

## CoverLetterDraft

- **Purpose**: Represents the separately generated cover letter artifact for the selected tailoring run.
- **Fields**:
  - `id` (UUID)
  - `tailoring_run_id` (FK)
  - `job_target_id` (FK)
  - `body_markdown` (text)
  - `status` (enum: `pending`, `processing`, `ready`, `failed`)
  - `created_at` (datetime)
- **Relationships**:
  - Belongs to TailoringRun and JobTarget
- **Validation Rules**:
  - Must only be generated from a `reviewable` tailoring run.
- **State Transitions**:
  - `pending -> processing -> ready`
  - `pending -> processing -> failed`

## GeneratedArtifact

- **Purpose**: Tracks downloadable output files generated by the system.
- **Fields**:
  - `id` (UUID)
  - `tailoring_run_id` (FK)
  - `artifact_type` (enum: `resume_pdf`, `cover_letter_file`)
  - `blob_path` (string)
  - `content_hash` (string)
  - `created_at` (datetime)
- **Relationships**:
  - Belongs to TailoringRun
  - May reference SourceDocument indirectly through the run
- **Validation Rules**:
  - Resume PDF exports must exclude unapproved project bullets.
  - Artifact generation must record the exact run version used for auditability.

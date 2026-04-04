# Feature Specification: AI Resume Tailoring Workflow

**Feature Branch**: `[001-resume-tailor-ai]`  
**Created**: 2026-04-03  
**Status**: Draft  
**Input**: User description: "I want to build a resume tailoring application where I upload a pdf or doc, paste a job description and we run it through AI to create a truthful rewritten resume, that matches keywords with the job description, writes custom summary, highlights skills, whatever we need to maximize chances of getting through an interview. Also have skill gap analysis, if there are requirements missing from the resume, try to highlight current skills that can transfer to the missing skill. Give me a small project to build that will cover all my skill gaps, then generate resume bullet points for that said project and include it in the final pdf. So the final PDF out should have uploaded PDF content, professional summary, experience keywords tailored to job interview, personal projects plus skill gap project, and ATS-compatible formatting."

## Clarifications

### Session 2026-04-03

- Q: What should the final PDF contain relative to the uploaded resume? → A: Final PDF is a newly generated tailored resume only, using approved content from the uploaded resume plus approved project additions.
- Q: How much editing control should the user have during review? → A: User can manually edit generated summary, bullets, and project content before export.
- Q: What persistence should v1 provide for uploaded files? → A: Save the latest uploaded file and show in the UI which PDF is currently being used.
- Q: Should resume and cover-letter generation be bundled or separate? → A: Users can generate the tailored resume and cover letter separately.
- Q: What visual direction should the UI follow? → A: Use a minimalist GameCube-inspired aesthetic with indigo primary branding, spice-orange accents, platinum-grey surfaces, tactile glossy controls, rounded industrial forms, and shape-based iconography.

## Experience Direction

- The interactive product UI MUST follow a minimalist GameCube-inspired visual system rather than a generic SaaS dashboard aesthetic.
- The primary visual palette uses Indigo for brand and active states, Spice Orange for CTAs and highlights, Platinum Grey for neutral surfaces, Jet Black for text and shadows, and Power LED Red only for sparse alert or status indicators.
- Typography should feel tech-forward and early-2000s inspired: geometric or wide display headings, highly legible body copy, and occasional squarish display treatment for major titles.
- Key containers should reference the console's industrial form through rounded rectangular cards, handle-like negative-space motifs, circular vent patterns, beveled edges, and subtle plastic-like depth.
- Interactive controls should feel tactile through clear press states, glossy or reflective button treatment, and deliberate loading cues such as disc-like spinners or pulsing power-light indicators.
- Icons should remain simple, shape-based, and visually consistent with the indigo-plus-orange visual language.
- The exported resume and cover letter remain ATS-friendly and plain where required; the GameCube aesthetic applies to the application interface, not to the submission document formatting.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tailor Resume For A Target Role (Priority: P1)

As a job seeker, I want to use a single workspace page to upload my current resume, paste a target job description, and run generation actions so I can receive a rewritten resume draft that is more relevant to the role without inventing experience I do not have.

**Why this priority**: This is the core value proposition. Without a truthful tailored draft, the feature does not solve the primary hiring workflow.

**Independent Test**: Can be fully tested by opening the home route workspace, uploading a resume, pasting a job description on the same page, and confirming that the system produces a revised resume draft with a custom summary, updated skill emphasis, and role-aligned wording that remains grounded in the original resume content.

**Acceptance Scenarios**:

1. **Given** a user provides a supported resume file and a job description, **When** tailoring is requested, **Then** the system produces a resume draft with a job-targeted professional summary, updated skill emphasis, and revised experience wording based only on supported source content.
2. **Given** the uploaded resume does not support a claimed requirement from the job description, **When** the tailored draft is generated, **Then** the system does not invent that claim and instead either omits it or flags it as a gap.
3. **Given** the resume file cannot be parsed or the job description is missing, **When** the user attempts to generate a draft, **Then** the system shows a clear error and explains how to correct the input.
4. **Given** a user has uploaded a resume, **When** the workspace is refreshed or the workflow is reopened within the supported v1 session model, **Then** the latest uploaded file is shown as the current source document in the UI.
5. **Given** generation or export actions are running, **When** the user is on the one-page workspace, **Then** action buttons are temporarily disabled, a loading indicator is shown, and export actions are re-enabled only after the tailoring run reaches a reviewable state.

---

### User Story 2 - Understand Gaps And Add Relevant Project Experience (Priority: P2)

As a job seeker, I want the system to identify missing requirements, highlight transferable strengths, and recommend a small project that helps cover the most important gaps so I can improve both my application and my real-world portfolio.

**Why this priority**: Gap analysis turns the app from a wording tool into a career-advancement tool. It gives users a realistic path to strengthen future applications rather than only editing existing material.

**Independent Test**: Can be fully tested by providing a resume and job description with obvious missing skills, then verifying that the system identifies direct gaps, maps transferable skills, proposes a small project to address those gaps, and creates resume-ready bullet points for the proposed project.

**Acceptance Scenarios**:

1. **Given** a job description contains requirements that are not clearly present in the resume, **When** analysis completes, **Then** the system lists the missing requirements and pairs each with any relevant transferable experience already shown in the resume.
2. **Given** one or more important gaps are found, **When** recommendations are generated, **Then** the system proposes a small project that addresses those gaps and provides resume-ready bullet points that the user can review.
3. **Given** the user decides not to include the suggested project content, **When** finalizing the resume, **Then** the system excludes the proposed project from the final output while preserving the rest of the tailored resume.

---

### User Story 3 - Generate Separate Application Outputs (Priority: P3)

As a job seeker, I want to approve tailored content and generate the resume and cover letter separately so I can use one or both artifacts depending on the application.

**Why this priority**: Users need submission-ready artifacts, but they do not always need both at the same time. Separate generation keeps the workflow flexible without forcing extra outputs.

**Independent Test**: Can be fully tested by reviewing generated changes, choosing whether to include the proposed gap-coverage project, and generating the resume and cover letter independently to confirm each output is available on its own.

**Acceptance Scenarios**:

1. **Given** a user has a tailored draft and optional project suggestions, **When** the user reviews and manually edits generated summary, bullet, or project text before approval, **Then** those approved edits are reflected in the generated output selected by the user.
2. **Given** the user chooses to generate only the resume, **When** resume export completes, **Then** the system produces a plain ATS-compatible resume document with readable headings, preserved ordering, and no unsupported content.
3. **Given** the user chooses to generate a cover letter, **When** cover-letter generation completes, **Then** the system produces a separate cover-letter output based on the uploaded resume, the job description, and the approved tailored content.

### Edge Cases

- The uploaded file is corrupted, password-protected, or uses an unsupported format.
- The uploaded resume is image-only or too poorly structured to extract reliable text.
- The job description is extremely long, repetitive, or includes contradictory requirements.
- The resume contains too little evidence to support meaningful tailoring for the target role.
- The recommended skill-gap project overlaps with an existing project already listed in the resume.
- The user rejects all generated project bullets and still expects a complete final export.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a one-page intake workspace at the home route where a user can provide an existing resume in PDF or document format and paste a target job description.
- **FR-002**: The system MUST save the latest uploaded resume file for reuse in the current product scope and show in the UI which uploaded file is currently being used as the source document.
- **FR-003**: The system MUST extract and organize the uploaded resume content into recognizable resume sections when sufficient source content is available.
- **FR-004**: The system MUST generate a tailored resume draft that rewrites and reorders content to improve role relevance while remaining truthful to the uploaded resume and any user-approved additions.
- **FR-005**: The system MUST generate a job-specific professional summary for the tailored resume.
- **FR-006**: The system MUST identify important keywords, competencies, and themes from the job description and reflect them in the tailored resume where supported by source evidence.
- **FR-007**: The system MUST distinguish between direct matches in the uploaded resume, missing requirements, and transferable skills that could support the missing requirements.
- **FR-008**: The system MUST provide a skill gap analysis that explains which important requirements are not directly supported by the uploaded resume.
- **FR-009**: The system MUST recommend at least one small project intended to strengthen the user against the most important identified skill gaps.
- **FR-010**: The system MUST generate resume-ready bullet points for the recommended project and present them as proposed additions rather than established experience until the user approves them.
- **FR-011**: The system MUST allow the user to review generated resume changes, manually edit generated summary, bullet, and project text, and decide whether to include or exclude proposed project content before final export.
- **FR-012**: The system MUST preserve the uploaded resume as the primary source of truth and MUST not add unsupported experience, achievements, or credentials to the final resume.
- **FR-013**: The system MUST allow users to generate the tailored resume and the cover letter as separate outputs rather than forcing both to be generated together.
- **FR-014**: The system MUST generate a final PDF resume that contains only the newly generated tailored resume, including approved tailored content, a professional summary, tailored experience and skills wording, existing projects, and any approved gap-coverage project content.
- **FR-015**: The system MUST produce the final resume PDF in an ATS-compatible format intended for applicant tracking systems and recruiter review.
- **FR-016**: The system MUST generate a separate cover-letter output tailored to the target job description and grounded in the uploaded resume and approved additions.
- **FR-017**: The system MUST provide clear user-facing states for loading, success, incomplete input, and failure across upload, analysis, review, resume generation, cover-letter generation, and export steps, including an explicit indication of the currently active uploaded resume file, temporary button blocking during async actions, and gating of export actions until the run is reviewable.

### Quality Requirements *(mandatory)*

- **QR-001**: Automated tests MUST cover the primary workflow from resume upload through separate resume and cover-letter generation, including acceptance and rejection of proposed project content.
- **QR-002**: Automated tests MUST verify truthfulness safeguards by confirming that unsupported claims are excluded or flagged rather than inserted into the tailored resume.
- **QR-003**: The feature MUST define explicit success, loading, empty, and error states for file ingestion, latest-file retrieval, job description analysis, resume generation, cover-letter generation, manual review and editing, skill-gap analysis, and export.
- **QR-004**: The feature MUST implement the approved minimalist GameCube-inspired UI direction consistently across the upload, review, and generation flows, including palette, typography, rounded industrial shapes, and tactile interaction cues.
- **QR-005**: The feature MUST provide deliberate tactile feedback for primary controls and recognizable themed loading states for long-running generation actions.
- **QR-006**: For a typical resume of up to 5 pages and a job description of up to 3,000 words, users MUST receive an initial tailored draft within 90 seconds in at least 95% of successful runs.
- **QR-007**: Final PDF export MUST complete within 30 seconds in at least 95% of successful runs after the user approves content.

### Key Entities *(include if feature involves data)*

- **Resume Source Document**: The latest saved uploaded resume file and its extracted content, which act as the factual baseline for tailoring and export.
- **Job Description**: The target role description used to identify keywords, competencies, responsibilities, and missing requirements.
- **Tailored Resume Draft**: The rewritten resume output that reorganizes and emphasizes supported content for the target role.
- **Skill Gap Assessment**: The analysis that separates direct matches, missing requirements, and transferable skills.
- **Project Recommendation**: A small proposed project intended to address the most important identified skill gaps and improve future candidacy.
- **Project Bullet Proposal**: Resume-ready bullet points derived from the recommended project and awaiting user approval.
- **Cover Letter Draft**: A separately generated job-targeted letter derived from the uploaded resume, job description, and approved tailored content.
- **Final Resume Export**: The ATS-compatible PDF assembled from approved tailored content.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of users can complete the flow from resume upload and job description entry to a first tailored draft in under 5 minutes, excluding time spent manually reviewing content.
- **SC-002**: At least 95% of successful tailoring runs produce an initial tailored draft within 90 seconds.
- **SC-003**: In 100% of reviewed final exports, every included skill, experience claim, and achievement can be traced to the uploaded resume or to user-approved project content.
- **SC-004**: At least 80% of analyzed job descriptions receive explicit coverage or gap commentary for the top 10 role-relevant keywords or competencies identified from the posting.
- **SC-005**: At least 90% of users who reach the review step successfully export an ATS-compatible PDF on their first attempt.
- **SC-006**: At least 90% of users who request a cover letter successfully generate it on their first attempt.

## Assumptions

- The initial release targets individual job seekers rather than recruiters, coaches, or collaborative teams.
- The initial release supports English-language resumes and job descriptions.
- Users provide resumes in PDF, DOC, or DOCX formats, and scanned image-only resumes may require fallback messaging rather than full support.
- The product retains the latest uploaded source resume so the UI can show which file is currently active, but v1 does not require a full multi-document history.
- The final exported PDF contains only the newly generated tailored resume based on uploaded content and approved additions, not a literal merged copy of the originally uploaded file and not an appendix package containing the original upload.
- Resume generation and cover-letter generation are separate user-selectable actions in v1 rather than a mandatory bundled export.
- The recommended skill-gap project represents suggested future or in-progress work and is only included in the final resume after explicit user approval.
- Users can manually edit generated summary, bullet, and project text before export while remaining responsible for approving the truthfulness of final content.
- The GameCube-inspired aesthetic applies to the web application UI, while exported submission documents remain plain and ATS-compatible.
- ATS compatibility and content clarity take priority over forcing the document into a one-page layout.

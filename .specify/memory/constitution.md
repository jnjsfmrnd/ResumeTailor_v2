<!--
Sync Impact Report
Version change: unversioned template -> 1.0.0
Modified principles:
- Template principle slot 1 -> I. Code Quality Is a Product Requirement
- Template principle slot 2 -> II. Tests Define Done
- Template principle slot 3 -> III. Experience Must Stay Cohesive
- Template principle slot 4 -> IV. Performance Budgets Are Explicit
- Template principle slot 5 -> V. Technical Decisions Require Evidence
Added sections:
- Implementation Standards
- Delivery Workflow & Quality Gates
Removed sections:
- None
Templates requiring updates:
- ✅ .specify/templates/plan-template.md
- ✅ .specify/templates/spec-template.md
- ✅ .specify/templates/tasks-template.md
- ✅ No files present under .specify/templates/commands/
Follow-up TODOs:
- None
-->

# ResumeTailor Constitution

## Core Principles

### I. Code Quality Is a Product Requirement
All production code MUST be readable, bounded in scope, and safe to change.
Every change MUST meet the repository's formatting, linting, and static analysis
standards before review. Functions, components, and modules MUST have a single
clear responsibility; duplication, dead code, and speculative abstractions MUST
be removed or justified in writing. When delivery pressure conflicts with code
quality, scope is reduced before maintainability is reduced, because unstable
code slows every subsequent feature.

### II. Tests Define Done
Every behavior change and bug fix MUST include automated tests at the lowest
practical level, plus integration coverage when user flows, contracts, or
system boundaries are affected. A task is not complete until the relevant tests
fail for the intended reason, pass after implementation, and are wired into the
normal validation path. If an automated test is genuinely infeasible, the PR
MUST record why, define the fallback manual validation steps, and identify the
owner responsible for closing that gap.

### III. Experience Must Stay Cohesive
User-facing changes MUST preserve a consistent experience across copy, layout,
interaction patterns, loading states, empty states, and error handling.
Features MUST reuse established components, tokens, and content patterns before
introducing new ones. Any intentional UX deviation MUST document the reason,
the affected surfaces, and the expected user benefit. Consistency is enforced
because fragmented interfaces increase user error, support cost, and rework.

### IV. Performance Budgets Are Explicit
Primary user flows MUST have stated performance expectations before
implementation begins. Each plan MUST define the relevant budget, measurement
method, and fallback strategy for regressions, covering latency, rendering,
throughput, memory, or bundle size as applicable. Changes that risk exceeding a
budget MUST include mitigation work in the same plan or a written exception.
Performance is treated as a product requirement, not a post-release cleanup.

### V. Technical Decisions Require Evidence
Implementation choices MUST follow the simplest design that satisfies current
requirements while honoring the four principles above. New dependencies,
patterns, services, or abstractions MUST be justified with explicit tradeoffs,
operational cost, and a rejected simpler alternative. Team members MAY propose
exceptions, but they MUST include measurable benefit, known risks, owner, and
expiration or review date. Opinion alone is not sufficient when the codebase is
asked to absorb complexity.

## Implementation Standards

- Plans MUST identify affected modules, shared contracts, and rollback surface
	before implementation starts.
- Specifications MUST define functional requirements, UX expectations,
	performance expectations, and measurable success criteria for the primary
	user journeys.
- Shared UI primitives, validation rules, and content conventions MUST be
	reused where they already exist; new patterns require documented rationale.
- Validation commands for linting, type-checking, testing, and performance
	verification MUST be executable by another contributor without hidden steps.
- Temporary workarounds MUST be labeled with owner, removal condition, and a
	tracked follow-up item.

## Delivery Workflow & Quality Gates

- The Constitution Check in each implementation plan MUST confirm how code
	quality, testing, UX consistency, performance budgets, and decision evidence
	are satisfied.
- Pull requests MUST summarize the user impact, changed surfaces, test evidence,
	UX consistency considerations, and performance impact or expected neutrality.
- Reviewers MUST block changes that weaken any principle without an approved and
	documented exception.
- Releases SHOULD prioritize smaller independently verifiable increments so
	regressions can be isolated quickly and reverted safely.
- Post-implementation cleanup is not a substitute for missing quality work in
	the original change unless that cleanup is explicitly approved as a time-boxed
	exception.

## Governance

This constitution overrides ad hoc local practices for planning, implementation,
and review. Amendments MUST be made in the same change set as any required
template or workflow updates, and MUST include a short rationale plus a version
bump determined by semantic intent: MAJOR for incompatible governance changes or
principle removal, MINOR for new principles or materially expanded obligations,
and PATCH for clarifications that do not change enforcement. Every feature plan,
task list, and pull request MUST include a compliance review against this
constitution. Approved exceptions MUST be written, time-boxed, and linked to the
work item they affect. If guidance conflicts, the stricter interpretation that
better protects code quality, testing, UX cohesion, and performance MUST win
until the constitution is amended explicitly.

**Version**: 1.0.0 | **Ratified**: 2026-04-02 | **Last Amended**: 2026-04-02

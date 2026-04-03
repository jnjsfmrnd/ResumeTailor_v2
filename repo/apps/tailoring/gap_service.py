from __future__ import annotations

import re
from collections.abc import Iterable

from apps.tailoring.models import (
    ProjectBulletProposal,
    ProjectRecommendation,
    SkillGapAssessment,
    TailoringRun,
)

_STOP_WORDS = {
    "and",
    "the",
    "for",
    "with",
    "from",
    "need",
    "needs",
    "looking",
    "experience",
    "required",
    "preferred",
    "years",
    "role",
    "work",
    "team",
    "strong",
    "ability",
    "skills",
}

_TARGET_KEYWORDS = {
    "kubernetes",
    "terraform",
    "redis",
    "django",
    "python",
    "graphql",
    "observability",
    "ci",
    "cd",
}

_TRANSFERABLE_HINTS = {
    "terraform": ["infrastructure automation", "iac", "cloudformation"],
    "kubernetes": ["containers", "container orchestration", "docker"],
    "observability": ["monitoring", "logging", "metrics"],
    "redis": ["caching", "cache"],
}


class GapServiceError(Exception):
    """Raised when the gap intelligence pipeline cannot proceed."""


def _normalize_text(text: str) -> str:
    return (text or "").strip().lower()


def _extract_keywords(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+/.-]{1,}", _normalize_text(text))
    return [t for t in tokens if t not in _STOP_WORDS]


def _collect_requirements(job_description: str) -> list[str]:
    tokens = set(_extract_keywords(job_description))
    targeted = sorted(tokens.intersection(_TARGET_KEYWORDS))
    return targeted


def _collect_transferable_mapping(requirement: str, resume_text: str) -> dict | None:
    resume = _normalize_text(resume_text)
    for hint in _TRANSFERABLE_HINTS.get(requirement, []):
        if hint in resume:
            return {
                "target": requirement,
                "source": hint,
                "evidence": f"Resume mentions {hint}.",
            }
    return None


def analyze_skill_gaps(
    *,
    job_description: str,
    resume_text: str,
    tailored_skills: Iterable[str] | None = None,
) -> dict:
    job_description = _normalize_text(job_description)
    resume_text = _normalize_text(resume_text)

    if not job_description or not resume_text:
        return {
            "missing_requirements": [],
            "transferable_skills": [],
            "coverage_summary": "Insufficient data to perform skill-gap analysis.",
        }

    requirements = _collect_requirements(job_description)
    resume_tokens = set(_extract_keywords(resume_text))
    tailored = {s.strip().lower() for s in (tailored_skills or []) if str(s).strip()}

    missing: list[dict] = []
    transferable: list[dict] = []

    for requirement in requirements:
        if requirement in resume_tokens or requirement in tailored:
            continue
        mapping = _collect_transferable_mapping(requirement, resume_text)
        if mapping:
            transferable.append(mapping)
            missing.append(
                {
                    "requirement": requirement,
                    "classification": "partially_transferable",
                    "evidence": mapping["evidence"],
                }
            )
            continue
        missing.append(
            {
                "requirement": requirement,
                "classification": "unsupported",
                "evidence": "No direct or transferable evidence found in source resume.",
            }
        )

    if not missing:
        summary = "Core requirements are covered by the current resume evidence."
    else:
        summary = (
            f"Detected {len(missing)} missing requirement(s); "
            f"{len(transferable)} can be framed as transferable."
        )

    return {
        "missing_requirements": missing,
        "transferable_skills": transferable,
        "coverage_summary": summary,
    }


def build_project_recommendation(
    *,
    role_title: str,
    missing_requirements: list[dict],
    transferable_skills: list[dict],
) -> dict:
    targeted_gaps = [item["requirement"] for item in missing_requirements[:3]]
    role = role_title.strip() if role_title else "target role"

    if targeted_gaps:
        gap_phrase = ", ".join(targeted_gaps)
        title = f"{role}: {targeted_gaps[0].title()} portfolio accelerator"
        goal = (
            f"Build a micro-project that demonstrates measurable capability in {gap_phrase}."
        )
    else:
        title = f"{role}: Portfolio proof project"
        goal = "Build a compact portfolio project that reinforces production-ready impact."

    transfer_lines = [
        f"- Bridge from {item['source']} to {item['target']}" for item in transferable_skills
    ]
    scope_lines = [
        "## Scope",
        "- Ship a small but complete feature with deployment notes.",
        "- Capture tradeoffs and measurable outcomes in README bullets.",
    ]
    scope_lines.extend(transfer_lines)

    primary_gap = targeted_gaps[0] if targeted_gaps else "platform reliability"
    bullets = [
        f"Built a focused micro-project to address {primary_gap} requirements for {role} roles.",
        "Implemented delivery automation, validation checks, and clear runbook documentation.",
        "Measured quality outcomes and translated execution details into ATS-friendly"
        " resume bullets.",
    ]

    return {
        "title": title,
        "goal": goal,
        "scope_markdown": "\n".join(scope_lines),
        "targeted_gaps": targeted_gaps,
        "bullets": bullets,
    }


def refresh_gap_intelligence(run: TailoringRun) -> tuple[SkillGapAssessment, ProjectRecommendation]:
    if run.status != TailoringRun.Status.REVIEWABLE:
        raise GapServiceError("Gap intelligence requires a reviewable tailoring run.")

    gap_result = analyze_skill_gaps(
        job_description=run.job_target.description_text,
        resume_text=run.source_document.extracted_text,
        tailored_skills=run.tailored_skills,
    )

    assessment, _ = SkillGapAssessment.objects.update_or_create(
        tailoring_run=run,
        defaults={
            "missing_requirements": gap_result["missing_requirements"],
            "transferable_skills": gap_result["transferable_skills"],
            "coverage_summary": gap_result["coverage_summary"],
        },
    )

    recommendation_payload = build_project_recommendation(
        role_title=run.job_target.role_title,
        missing_requirements=gap_result["missing_requirements"],
        transferable_skills=gap_result["transferable_skills"],
    )

    recommendation, _ = ProjectRecommendation.objects.update_or_create(
        tailoring_run=run,
        title=recommendation_payload["title"],
        defaults={
            "goal": recommendation_payload["goal"],
            "scope_markdown": recommendation_payload["scope_markdown"],
            "targeted_gaps": recommendation_payload["targeted_gaps"],
        },
    )

    ProjectBulletProposal.objects.filter(project_recommendation=recommendation).delete()
    ProjectBulletProposal.objects.bulk_create(
        [
            ProjectBulletProposal(
                project_recommendation=recommendation,
                sort_order=index + 1,
                generated_text=text,
            )
            for index, text in enumerate(recommendation_payload["bullets"])
        ]
    )
    return assessment, recommendation


def apply_review_updates(run: TailoringRun, project_recommendations: list[dict]) -> None:
    if not isinstance(project_recommendations, list):
        raise GapServiceError("projectRecommendations must be a list.")

    recommendation_ids = [item.get("id") for item in project_recommendations]
    recommendation_map = {
        str(item.id): item
        for item in ProjectRecommendation.objects.filter(
            tailoring_run=run,
            id__in=recommendation_ids,
        ).prefetch_related("bullets")
    }

    for update in project_recommendations:
        recommendation_id = update.get("id")
        if recommendation_id not in recommendation_map:
            raise GapServiceError("Recommendation not found for this tailoring run.")

        recommendation = recommendation_map[recommendation_id]
        if "isIncluded" in update:
            recommendation.is_included = bool(update["isIncluded"])
            recommendation.save(update_fields=["is_included"])

        bullets_update = update.get("bullets", [])
        if bullets_update and not isinstance(bullets_update, list):
            raise GapServiceError("bullets must be a list when provided.")

        bullet_map = {
            str(b.id): b
            for b in ProjectBulletProposal.objects.filter(
                project_recommendation=recommendation
            )
        }
        for bullet_update in bullets_update:
            bullet_id = bullet_update.get("id")
            if bullet_id not in bullet_map:
                raise GapServiceError("Bullet proposal not found for this recommendation.")
            bullet = bullet_map[bullet_id]
            changed = []
            if "editedText" in bullet_update:
                bullet.edited_text = str(bullet_update["editedText"])
                changed.append("edited_text")
            if "isApproved" in bullet_update:
                bullet.is_approved = bool(bullet_update["isApproved"])
                changed.append("is_approved")
            if changed:
                bullet.save(update_fields=changed)


def serialize_gap_review(run: TailoringRun) -> dict:
    assessment = getattr(run, "skill_gap_assessment", None)
    recommendations = ProjectRecommendation.objects.filter(
        tailoring_run=run
    ).prefetch_related("bullets")
    bullet_map: dict[str, list[ProjectBulletProposal]] = {}
    for bullet in ProjectBulletProposal.objects.filter(
        project_recommendation__in=recommendations
    ).order_by("sort_order", "id"):
        key = str(bullet.project_recommendation.id)
        bullet_map.setdefault(key, []).append(bullet)

    return {
        "id": str(run.id),
        "status": run.status,
        "skillGapAssessment": {
            "missingRequirements": assessment.missing_requirements if assessment else [],
            "transferableSkills": assessment.transferable_skills if assessment else [],
            "coverageSummary": assessment.coverage_summary if assessment else "",
        },
        "projectRecommendations": [
            {
                "id": str(item.id),
                "title": item.title,
                "goal": item.goal,
                "scopeMarkdown": item.scope_markdown,
                "targetedGaps": item.targeted_gaps,
                "isIncluded": item.is_included,
                "bullets": [
                    {
                        "id": str(bullet.id),
                        "generatedText": bullet.generated_text,
                        "editedText": bullet.edited_text,
                        "isApproved": bullet.is_approved,
                    }
                    for bullet in bullet_map.get(str(item.id), [])
                ],
            }
            for item in recommendations
        ],
    }
